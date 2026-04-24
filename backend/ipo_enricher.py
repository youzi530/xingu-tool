"""
IPO 数据回填引擎 + 新股发现引擎

职责：
  1. enrich_ipos_from_articles()
     对 iTick 数据不全的新股，从已抓取的分析文章中提取缺失字段并回填。

  2. discover_new_ipos()
     扫描最近 N 天的文章，发现 iTick 未收录的新股名称，
     反向用搜狗搜索获取更多信息，自动创建 IPO 记录。

流程图：
  iTick 同步 → 字段残缺 IPO
       ↓
  扫描相关文章（title + summary + 全文）
       ↓
  article_extractor 提取字段
       ↓
  回填到 IPO 记录（只填空字段，不覆盖已有数据）
       ↓
  如发现文章提到的新股不在 DB 中 → 创建新 IPO → 再次搜狗补充信息
"""

import asyncio
import logging
import re
from datetime import date, datetime, timedelta
from typing import Optional

from sqlalchemy.orm import Session

import models
from article_extractor import extract_ipo_fields, extract_ipo_name_from_text, fields_missing
from wechat_scraper import fetch_article
from sogou_monitor import search_articles

logger = logging.getLogger(__name__)

# 只处理这个日期之后的文章（避免旧文章干扰）
CUTOFF_DATE = date(2026, 4, 24)


def _is_recent(analysis: models.Analysis) -> bool:
    """判断分析文章是否在截止日期之后"""
    if analysis.published_at:
        return analysis.published_at.date() >= CUTOFF_DATE
    # 如果没有发布时间，保守地认为是最近的（入库时间）
    if analysis.created_at:
        return analysis.created_at.date() >= CUTOFF_DATE
    return False


def _apply_fields(ipo: models.IPO, extracted: dict) -> list[str]:
    """
    将提取到的字段写入 IPO 对象（只填充空字段，不覆盖已有值）
    返回实际被填充的字段名列表
    """
    filled = []
    field_map = {
        'ipo_price_min': 'ipo_price_min',
        'ipo_price_max': 'ipo_price_max',
        'lot_size': 'lot_size',
        'subscribe_start': 'subscribe_start',
        'subscribe_end': 'subscribe_end',
        'allotment_date': 'allotment_date',
        'listing_date': 'listing_date',
    }
    for ext_key, model_key in field_map.items():
        val = extracted.get(ext_key)
        if val is None:
            continue
        current = getattr(ipo, model_key, None)
        if current is None:
            setattr(ipo, model_key, val)
            filled.append(model_key)

    # 状态重新计算（可能因回填了日期而改变）
    if filled and any(f in filled for f in ['subscribe_start', 'subscribe_end', 'listing_date']):
        new_status = _compute_status(ipo.subscribe_start, ipo.subscribe_end, ipo.listing_date)
        if new_status != ipo.status.value:
            ipo.status = models.IPOStatus(new_status)
            filled.append('status')

    return filled


def _compute_status(
    subscribe_start: Optional[date],
    subscribe_end: Optional[date],
    listing_date: Optional[date],
) -> str:
    today = date.today()
    if listing_date and listing_date <= today:
        return "listed"
    if subscribe_end and listing_date and subscribe_end < today < listing_date:
        return "listing"
    if subscribe_start and subscribe_end and subscribe_start <= today <= subscribe_end:
        return "subscribing"
    return "upcoming"


async def _get_article_text(analysis: models.Analysis) -> str:
    """
    尽力获取文章全文。
    策略：
      1. 若 content_url 是 mp.weixin.qq.com 链接 → 直接抓取
      2. 否则（搜狗跳转链接）→ 仅使用 title + summary
    """
    url = analysis.content_url or ""
    if "mp.weixin.qq.com" in url:
        try:
            art = await fetch_article(url)
            if art.success and art.content_text:
                return art.content_text
        except Exception as e:
            logger.debug("抓取文章失败 %s: %s", url, e)
    # 降级：title + summary
    parts = []
    if analysis.title:
        parts.append(analysis.title)
    if analysis.summary:
        parts.append(analysis.summary)
    return " ".join(parts)


# ── 1. 回填缺失字段 ───────────────────────────────────────────────────────────

async def enrich_ipos_from_articles(db: Session) -> dict:
    """
    扫描有分析文章但 ITick 字段不全的新股，从文章中提取并回填缺失字段。
    """
    total_filled = 0
    ipos_enriched = 0

    # 取所有有分析文章且字段不完整的新股
    all_ipos = db.query(models.IPO).all()
    ipos_with_gaps = [ipo for ipo in all_ipos if fields_missing(ipo)]

    logger.info("发现 %d 只新股字段不完整，开始从文章回填…", len(ipos_with_gaps))

    for ipo in ipos_with_gaps:
        missing = fields_missing(ipo)
        logger.debug("  %s 缺失字段: %s", ipo.stock_name, missing)

        # 取该新股的最近文章
        analyses = db.query(models.Analysis).filter(
            models.Analysis.ipo_id == ipo.id
        ).order_by(models.Analysis.published_at.desc()).limit(10).all()

        recent_analyses = [a for a in analyses if _is_recent(a)]
        if not recent_analyses:
            recent_analyses = analyses[:3]  # 没有recent的，取最新3篇

        combined_extracted = {}
        for analysis in recent_analyses:
            text = await _get_article_text(analysis)
            if not text:
                continue
            extracted = extract_ipo_fields(text)
            # 合并：优先取已提取到的值
            for k, v in extracted.items():
                if k not in combined_extracted:
                    combined_extracted[k] = v
            # 如果所有缺失字段都找到了，提前停止
            if all(f in combined_extracted for f in missing):
                break
            await asyncio.sleep(0.3)  # 避免过快请求

        if combined_extracted:
            filled = _apply_fields(ipo, combined_extracted)
            if filled:
                total_filled += len(filled)
                ipos_enriched += 1
                logger.info("  ✅ %s 回填字段: %s", ipo.stock_name, filled)

    db.commit()
    logger.info("回填完成：%d 只新股，共回填 %d 个字段", ipos_enriched, total_filled)
    return {
        "ipos_checked": len(ipos_with_gaps),
        "ipos_enriched": ipos_enriched,
        "fields_filled": total_filled,
    }


# ── 2. 从文章发现 iTick 未收录的新股 ─────────────────────────────────────────

async def discover_new_ipos(db: Session, days_back: int = 7) -> dict:
    """
    扫描最近 days_back 天的文章，提取文章中提到的新股名称，
    与数据库对比，发现未收录的新股 → 反向搜狗搜索 → 提取字段 → 入库。
    """
    cutoff = datetime.now() - timedelta(days=days_back)
    discovered = 0
    created = 0

    # 取最近的文章
    recent_analyses = db.query(models.Analysis).filter(
        models.Analysis.created_at >= cutoff
    ).order_by(models.Analysis.created_at.desc()).all()

    if not recent_analyses:
        return {"discovered": 0, "created": 0, "message": "没有找到最近的文章"}

    # 所有现有股票名称（用于去重）
    existing_names = {ipo.stock_name for ipo in db.query(models.IPO).all()}
    existing_codes = {ipo.stock_code for ipo in db.query(models.IPO).all()}

    # 从文章中提取新股名称
    candidate_names: set = set()
    for analysis in recent_analyses:
        text = f"{analysis.title or ''} {analysis.summary or ''}"
        names = extract_ipo_name_from_text(text)
        for name in names:
            # 过滤太短的名称和已存在的
            if len(name) >= 2 and name not in existing_names:
                candidate_names.add(name)

    logger.info("从文章发现 %d 个候选新股名称", len(candidate_names))
    discovered = len(candidate_names)

    for name in candidate_names:
        logger.info("  反向搜索新股: %s", name)

        # 用搜狗搜索这个新股名
        articles = await search_articles(f"{name} 港股 打新 招股", max_pages=1)
        if not articles:
            articles = await search_articles(f"{name} IPO HK", max_pages=1)

        if not articles:
            logger.debug("  未找到 %s 的相关文章", name)
            continue

        # 用所有搜索结果的 title + summary 提取字段
        all_text = " ".join([f"{a.title} {a.summary}" for a in articles[:5]])
        extracted = extract_ipo_fields(all_text)

        # 再次检查股票代码是否已存在（iTick 数据可能已包含）
        code = extracted.get('stock_code')
        if code and code in existing_codes:
            logger.debug("  股票代码 %s 已存在，跳过 %s", code, name)
            continue

        # 模糊匹配名称（避免"天星医疗"和"港股打新|天星医疗"重复入库）
        normalized = re.sub(r'(?:港股打新|打新|招股|IPO|【|】|「|」|[|｜\s])', '', name).strip()
        if any(normalized in n or n in normalized for n in existing_names if len(n) >= 2):
            logger.debug("  名称相似已存在，跳过 %s", name)
            continue

        # 构建新 IPO 记录
        ipo_data = {
            'stock_name': name,
            'exchange': 'HKEX',
            'status': 'upcoming',
            'data_source': 'article_discovery',
            **{k: v for k, v in extracted.items()
               if k in ['stock_code', 'ipo_price_min', 'ipo_price_max',
                        'lot_size', 'subscribe_start', 'subscribe_end',
                        'allotment_date', 'listing_date']},
        }

        # 股票代码缺失时用名字作临时 code 避免冲突
        if 'stock_code' not in ipo_data or not ipo_data['stock_code']:
            ipo_data['stock_code'] = f"DISC_{re.sub(r'[^a-zA-Z0-9]', '', name)[:8]}"

        if ipo_data['stock_code'] in existing_codes:
            continue

        new_ipo = models.IPO(**ipo_data)
        db.add(new_ipo)
        db.flush()
        existing_names.add(name)
        existing_codes.add(ipo_data['stock_code'])
        created += 1
        logger.info("  ✅ 新建 IPO: %s (%s)", name, ipo_data.get('stock_code', '?'))

        # 为新发现的 IPO 保存关联文章
        bloggers = {b.name: b for b in db.query(models.Blogger).all()}
        for art in articles[:5]:
            if not art.account_name:
                continue
            blogger = bloggers.get(art.account_name)
            if not blogger:
                blogger = models.Blogger(
                    name=art.account_name,
                    channel=models.SourceChannel.wechat,
                    description="由文章发现自动创建",
                )
                db.add(blogger)
                db.flush()
                bloggers[art.account_name] = blogger

            # 去重检查
            exists = db.query(models.Analysis).filter(
                models.Analysis.content_url == art.content_url
            ).first()
            if not exists:
                analysis = models.Analysis(
                    ipo_id=new_ipo.id,
                    blogger_id=blogger.id,
                    title=art.title,
                    summary=art.summary,
                    content_url=art.content_url,
                    source_channel=models.SourceChannel.wechat,
                    published_at=art.published_at,
                )
                db.add(analysis)

        await asyncio.sleep(2)  # 搜狗请求间隔

    db.commit()
    logger.info("新股发现完成：发现候选 %d，成功入库 %d 只", discovered, created)
    return {
        "candidates_found": discovered,
        "new_ipos_created": created,
    }
