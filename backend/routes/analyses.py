import logging

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from database import get_db
import models, schemas

router = APIRouter(prefix="/analyses", tags=["分析文章"])
logger = logging.getLogger(__name__)


@router.get("/", response_model=List[schemas.AnalysisOut])
def list_analyses(
    ipo_id: Optional[int] = None,
    blogger_id: Optional[int] = None,
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
):
    """获取分析列表，可按新股或博主筛选"""
    q = db.query(models.Analysis)
    if ipo_id:
        q = q.filter(models.Analysis.ipo_id == ipo_id)
    if blogger_id:
        q = q.filter(models.Analysis.blogger_id == blogger_id)
    return q.order_by(models.Analysis.published_at.desc()).offset(skip).limit(limit).all()


@router.post("/", response_model=schemas.AnalysisOut, status_code=201)
def create_analysis(payload: schemas.AnalysisCreate, db: Session = Depends(get_db)):
    ipo = db.query(models.IPO).filter(models.IPO.id == payload.ipo_id).first()
    if not ipo:
        raise HTTPException(status_code=404, detail="新股不存在")
    blogger = db.query(models.Blogger).filter(models.Blogger.id == payload.blogger_id).first()
    if not blogger:
        raise HTTPException(status_code=404, detail="博主不存在")

    analysis = models.Analysis(**payload.model_dump())
    db.add(analysis)
    db.commit()
    db.refresh(analysis)
    return analysis


@router.post("/{analysis_id}/refresh-url", summary="按需刷新文章链接")
async def refresh_article_url(analysis_id: int, db: Session = Depends(get_db)):
    """
    按需 URL 刷新接口（供前端在用户点击"阅读原文"时调用）：
      1. 若链接已是 mp.weixin.qq.com → 直接返回，无需任何网络请求
      2. 若链接是搜狗跳转链接 → 尝试跟随跳转获取真实 URL
         - 跳转成功 → 永久存库，返回真实 URL
         - 已过期  → 用文章标题重新搜狗，获取新链接并立即解析，存库后返回
    """
    from sogou_monitor import resolve_article_url, search_articles

    analysis = db.query(models.Analysis).filter(models.Analysis.id == analysis_id).first()
    if not analysis:
        raise HTTPException(status_code=404, detail="分析不存在")

    url = analysis.content_url or ""

    # 已是永久微信链接，直接返回
    if "mp.weixin.qq.com" in url:
        return {"url": url, "refreshed": False}

    # 尝试解析搜狗链接 → 真实 URL
    if url:
        real_url = await resolve_article_url(url)
        if "mp.weixin.qq.com" in real_url:
            analysis.content_url = real_url
            db.commit()
            logger.info("refresh-url 解析成功 [%d]: %s", analysis_id, real_url[:60])
            return {"url": real_url, "refreshed": True}

    # 链接已过期或为空：用标题重新搜索
    if analysis.title:
        ipo = db.query(models.IPO).filter(models.IPO.id == analysis.ipo_id).first()
        query = f"{ipo.stock_name if ipo else ''} {analysis.title[:20]} 打新".strip()
        articles = await search_articles(query, max_pages=1)
        for art in articles:
            if art.content_url:
                fresh_url = await resolve_article_url(art.content_url)
                if "mp.weixin.qq.com" in fresh_url:
                    analysis.content_url = fresh_url
                    db.commit()
                    logger.info("refresh-url 重新搜索成功 [%d]: %s", analysis_id, fresh_url[:60])
                    return {"url": fresh_url, "refreshed": True}

    # 全部失败，返回原链接兜底
    logger.warning("refresh-url 无法刷新 [%d], 返回原链接", analysis_id)
    return {"url": url, "refreshed": False}


@router.delete("/{analysis_id}", status_code=204)
def delete_analysis(analysis_id: int, db: Session = Depends(get_db)):
    a = db.query(models.Analysis).filter(models.Analysis.id == analysis_id).first()
    if not a:
        raise HTTPException(status_code=404, detail="分析不存在")
    db.delete(a)
    db.commit()
