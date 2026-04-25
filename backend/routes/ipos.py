import logging

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func
from typing import List, Optional

from database import get_db, SessionLocal
import models, schemas

router = APIRouter(prefix="/ipos", tags=["IPO新股"])
logger = logging.getLogger(__name__)

# 文章数低于此阈值时，自动触发后台同步
_AUTO_SYNC_THRESHOLD = 15


async def _bg_sync_ipo(ipo_id: int) -> None:
    """后台任务：为指定 IPO 拉取新文章（使用独立 DB session）"""
    from sogou_monitor import sync_single_ipo_articles

    db = SessionLocal()
    try:
        saved = await sync_single_ipo_articles(ipo_id, db)
        if saved:
            logger.info("后台同步完成 IPO %d：新增 %d 篇文章", ipo_id, saved)
    except Exception:
        logger.exception("后台同步 IPO %d 失败", ipo_id)
    finally:
        db.close()


@router.get("/", response_model=List[schemas.IPOOut])
def list_ipos(
    status: Optional[models.IPOStatus] = None,
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
):
    """获取新股列表，可按状态筛选"""
    # 用子查询一次性拿到所有 analysis 计数，避免 N+1 查询
    count_subq = (
        db.query(
            models.Analysis.ipo_id,
            func.count(models.Analysis.id).label("cnt"),
        )
        .group_by(models.Analysis.ipo_id)
        .subquery()
    )

    q = (
        db.query(models.IPO, func.coalesce(count_subq.c.cnt, 0).label("analysis_count"))
        .outerjoin(count_subq, models.IPO.id == count_subq.c.ipo_id)
    )
    if status:
        q = q.filter(models.IPO.status == status)
    rows = q.order_by(models.IPO.subscribe_start.desc()).offset(skip).limit(limit).all()

    result = []
    for ipo, count in rows:
        out = schemas.IPOOut.model_validate(ipo)
        out.analysis_count = count
        result.append(out)
    return result


@router.get("/{ipo_id}", response_model=schemas.IPOWithAnalyses)
async def get_ipo(
    ipo_id: int,
    background_tasks: BackgroundTasks,
    blogger_id: Optional[int] = None,
    db: Session = Depends(get_db),
):
    """获取单只新股详情及所有分析。文章数不足时自动触发后台补抓。"""
    ipo = db.query(models.IPO).filter(models.IPO.id == ipo_id).first()
    if not ipo:
        raise HTTPException(status_code=404, detail="新股不存在")

    analyses_query = (
        db.query(models.Analysis)
        .options(joinedload(models.Analysis.blogger))  # 避免 blogger 懒加载 N+1
        .filter(models.Analysis.ipo_id == ipo_id)
    )
    if blogger_id:
        analyses_query = analyses_query.filter(models.Analysis.blogger_id == blogger_id)
    analyses = analyses_query.order_by(models.Analysis.published_at.desc()).all()

    # 文章数不足时，在后台自动补抓（用户立即看到现有数据，不等待）
    if len(analyses) < _AUTO_SYNC_THRESHOLD:
        background_tasks.add_task(_bg_sync_ipo, ipo_id)
        logger.info("IPO %d 文章数(%d) < %d，已触发后台补抓", ipo_id, len(analyses), _AUTO_SYNC_THRESHOLD)

    ipo_data = schemas.IPOOut.model_validate(ipo).model_dump()
    ipo_data['analysis_count'] = len(analyses)
    return schemas.IPOWithAnalyses(
        **ipo_data,
        analyses=[schemas.AnalysisOut.model_validate(a) for a in analyses],
    )


@router.post("/", response_model=schemas.IPOOut, status_code=201)
def create_ipo(payload: schemas.IPOCreate, db: Session = Depends(get_db)):
    existing = db.query(models.IPO).filter(models.IPO.stock_code == payload.stock_code).first()
    if existing:
        raise HTTPException(status_code=400, detail="该股票代码已存在")
    ipo = models.IPO(**payload.model_dump())
    db.add(ipo)
    db.commit()
    db.refresh(ipo)
    return schemas.IPOOut.model_validate(ipo)


@router.put("/{ipo_id}", response_model=schemas.IPOOut)
def update_ipo(ipo_id: int, payload: schemas.IPOCreate, db: Session = Depends(get_db)):
    ipo = db.query(models.IPO).filter(models.IPO.id == ipo_id).first()
    if not ipo:
        raise HTTPException(status_code=404, detail="新股不存在")
    for k, v in payload.model_dump().items():
        setattr(ipo, k, v)
    db.commit()
    db.refresh(ipo)
    return schemas.IPOOut.model_validate(ipo)
