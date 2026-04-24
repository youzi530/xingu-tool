"""
数据同步路由
POST /sync/ipos     — 手动触发从 iTick 同步港股新股列表
POST /sync/articles — 手动触发搜狗搜索，自动发现并入库各博主的打新文章
GET  /sync/status   — 查看上次同步状态
"""
import logging
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, BackgroundTasks
from sqlalchemy.orm import Session

from database import get_db
import models
from itick_service import fetch_hk_ipos, normalize_ipo
from sogou_monitor import monitor_ipo_articles
from ipo_enricher import enrich_ipos_from_articles, discover_new_ipos

router = APIRouter(prefix="/sync", tags=["数据同步"])
logger = logging.getLogger(__name__)

# 简单内存状态（生产可改 Redis）
_sync_state = {
    "last_sync_at": None,
    "last_sync_count": 0,
    "last_sync_status": "never",
    "is_running": False,
}


async def _do_sync(db: Session) -> dict:
    """
    核心同步逻辑：
    1. 拉取 iTick upcoming + recent 两类数据
    2. Upsert 到本地数据库（已存在则更新，不存在则新建）
    """
    _sync_state["is_running"] = True
    created = updated = skipped = 0

    try:
        # 分两批拉取：即将上市 + 近期已上市
        upcoming = await fetch_hk_ipos("upcoming")
        recent = await fetch_hk_ipos("recent")
        all_raws = upcoming + recent

        if not all_raws:
            _sync_state.update({
                "last_sync_at": datetime.now().isoformat(),
                "last_sync_status": "skipped_no_token",
                "is_running": False,
            })
            return {"created": 0, "updated": 0, "message": "ITICK_TOKEN 未配置，跳过同步"}

        # 预加载数据库中已有的 stock_code 集合，避免逐条查询
        existing_codes: dict = {
            row.stock_code: row
            for row in db.query(models.IPO).all()
        }

        # 本批次已处理的 code（避免 upcoming + recent 重复）
        seen_in_batch: set = set()

        for raw in all_raws:
            normalized = normalize_ipo(raw)
            code = normalized["stock_code"]
            if not code:
                continue

            # 同一批次出现重复 code 时，取 upcoming 优先（先出现的）
            if code in seen_in_batch:
                skipped += 1
                continue
            seen_in_batch.add(code)

            if code in existing_codes:
                existing = existing_codes[code]
                # 仅覆盖 iTick 字段，保留人工填写的 industry / lot_size / description
                for field in [
                    "stock_name", "exchange", "ipo_price_min", "ipo_price_max",
                    "subscribe_start", "subscribe_end", "allotment_date",
                    "listing_date", "market_cap", "status", "data_source",
                ]:
                    val = normalized.get(field)
                    if val is not None:
                        setattr(existing, field, val)
                updated += 1
            else:
                ipo = models.IPO(**normalized)
                db.add(ipo)
                existing_codes[code] = ipo  # 加入本地缓存，防止后续重复
                created += 1

        db.commit()
        logger.info("iTick 同步完成：新建 %d，更新 %d，跳过重复 %d", created, updated, skipped)

        _sync_state.update({
            "last_sync_at": datetime.now().isoformat(),
            "last_sync_count": created + updated,
            "last_sync_status": "ok",
            "is_running": False,
        })
        return {"created": created, "updated": updated, "skipped": skipped, "total": len(all_raws)}

    except Exception as e:
        db.rollback()
        logger.exception("同步异常")
        _sync_state.update({
            "last_sync_at": datetime.now().isoformat(),
            "last_sync_status": f"error: {e}",
            "is_running": False,
        })
        raise


@router.post("/ipos", summary="手动触发新股列表同步")
async def sync_ipos(
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    """
    从 iTick 拉取港股新股数据并写入数据库。
    - upcoming：即将认购/上市
    - recent：近期已上市
    两批合并 upsert，保留本地人工填写的 industry / lot_size / description。
    """
    if _sync_state["is_running"]:
        return {"message": "同步正在进行中，请稍后"}

    result = await _do_sync(db)
    return {"message": "同步完成", **result}


@router.post("/articles", summary="搜狗搜索：自动发现并入库各博主文章")
async def sync_articles(db: Session = Depends(get_db)):
    """
    对所有活跃新股（upcoming / subscribing / listing）执行搜狗微信搜索，
    自动发现各博主写的打新分析文章并入库。
    新博主账号会自动创建，已存在的文章链接会跳过（去重）。
    """
    active_statuses = [
        models.IPOStatus.upcoming,
        models.IPOStatus.subscribing,
        models.IPOStatus.listing,
    ]
    active_ipos = db.query(models.IPO).filter(
        models.IPO.status.in_(active_statuses)
    ).all()
    bloggers = db.query(models.Blogger).all()

    if not active_ipos:
        return {"message": "暂无活跃新股，跳过搜索"}

    result = await monitor_ipo_articles(db, active_ipos, bloggers)
    return {
        "message": "文章搜索完成",
        **result,
    }


@router.post("/enrich", summary="从文章回填新股缺失字段")
async def sync_enrich(db: Session = Depends(get_db)):
    """
    扫描所有字段不完整的新股，从其关联分析文章中提取并回填：
    发行价区间、每手股数、认购开始/截止日期、上市日期、中签公布日。

    只处理 4/24 之后的文章，避免旧信息干扰。
    已有值的字段不会被覆盖。
    """
    result = await enrich_ipos_from_articles(db)
    return {"message": "字段回填完成", **result}


@router.post("/discover", summary="从文章发现 iTick 未收录的新股")
async def sync_discover(days_back: int = 7, db: Session = Depends(get_db)):
    """
    扫描最近 days_back 天内的分析文章，提取其中提到的新股名称，
    与数据库对比后，对未收录的新股：
      1. 反向搜狗搜索获取更多信息
      2. 提取关键字段（价格、日期等）
      3. 自动创建 IPO 记录并关联相关文章
    """
    result = await discover_new_ipos(db, days_back=days_back)
    return {"message": "新股发现完成", **result}


@router.post("/full", summary="一键全量同步（iTick + 文章搜索 + 字段回填 + 新股发现）")
async def sync_full(db: Session = Depends(get_db)):
    """
    按顺序执行完整同步流程：
      1. iTick 同步新股列表
      2. 搜狗搜索各新股分析文章
      3. 从文章回填缺失字段
      4. 发现 iTick 未收录的新股
    """
    if _sync_state["is_running"]:
        return {"message": "同步正在进行中，请稍后"}

    # Step 1: iTick
    step1 = await _do_sync(db)

    # Step 2: 文章搜索
    active_statuses = [
        models.IPOStatus.upcoming,
        models.IPOStatus.subscribing,
        models.IPOStatus.listing,
    ]
    active_ipos = db.query(models.IPO).filter(
        models.IPO.status.in_(active_statuses)
    ).all()
    bloggers = db.query(models.Blogger).all()
    step2 = await monitor_ipo_articles(db, active_ipos, bloggers)

    # Step 3: 字段回填
    step3 = await enrich_ipos_from_articles(db)

    # Step 4: 新股发现
    step4 = await discover_new_ipos(db, days_back=7)

    return {
        "message": "全量同步完成",
        "itick": step1,
        "articles": step2,
        "enrich": step3,
        "discover": step4,
    }


@router.get("/status", summary="查看上次同步状态")
def sync_status():
    return _sync_state


# ── 供 lifespan 调用的同步函数 ─────────────────────────────────────────────
async def run_sync_once(db: Session):
    """启动时静默同步一次（不抛异常，只记录日志）"""
    try:
        await _do_sync(db)
    except Exception as e:
        logger.warning("启动同步失败（非致命）: %s", e)
