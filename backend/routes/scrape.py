"""
公众号文章抓取路由
POST /scrape/wechat          — 抓取单篇文章并返回结构化数据
POST /scrape/wechat/save     — 抓取后直接保存为 Analysis 记录
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel, HttpUrl
from typing import Optional
from datetime import datetime

from database import get_db
from wechat_scraper import fetch_article
import models

router = APIRouter(prefix="/scrape", tags=["内容抓取"])


class ScrapeRequest(BaseModel):
    url: str
    ipo_id: Optional[int] = None       # 关联新股 ID（可选）
    blogger_id: Optional[int] = None   # 关联博主 ID（可选）
    recommendation: Optional[str] = None  # 人工填写推荐结论


class ScrapeResponse(BaseModel):
    success: bool
    title: str
    author: str
    published_at: Optional[datetime]
    cover_image_url: str
    summary: str
    content_length: int
    error: str


@router.post("/wechat", response_model=ScrapeResponse, summary="抓取公众号文章")
async def scrape_wechat(req: ScrapeRequest):
    """
    传入公众号文章链接，返回解析后的结构化数据（不入库）。
    可用于预览，确认内容正确后再调用 /scrape/wechat/save。
    """
    article = await fetch_article(req.url)
    return ScrapeResponse(
        success=article.success,
        title=article.title,
        author=article.author,
        published_at=article.published_at,
        cover_image_url=article.cover_image_url,
        summary=article.summary,
        content_length=len(article.content_text),
        error=article.error,
    )


@router.post("/wechat/save", summary="抓取并保存为分析文章")
async def scrape_and_save(req: ScrapeRequest, db: Session = Depends(get_db)):
    """
    抓取公众号文章并保存到 analyses 表。
    需要提供 ipo_id 和 blogger_id。
    """
    if not req.ipo_id or not req.blogger_id:
        raise HTTPException(status_code=400, detail="ipo_id 和 blogger_id 为必填项")

    ipo = db.query(models.IPO).filter(models.IPO.id == req.ipo_id).first()
    if not ipo:
        raise HTTPException(status_code=404, detail="新股不存在")

    blogger = db.query(models.Blogger).filter(models.Blogger.id == req.blogger_id).first()
    if not blogger:
        raise HTTPException(status_code=404, detail="博主不存在")

    article = await fetch_article(req.url)
    if not article.success:
        raise HTTPException(status_code=422, detail=f"文章抓取失败: {article.error}")

    analysis = models.Analysis(
        ipo_id=req.ipo_id,
        blogger_id=req.blogger_id,
        title=article.title or req.url,
        summary=article.summary,
        content_url=req.url,
        cover_image_url=article.cover_image_url or None,
        source_channel=models.SourceChannel.wechat,
        published_at=article.published_at,
        recommendation=req.recommendation,
    )
    db.add(analysis)
    db.commit()
    db.refresh(analysis)

    return {
        "message": "保存成功",
        "analysis_id": analysis.id,
        "title": article.title,
        "summary": article.summary[:100],
    }
