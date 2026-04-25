from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func
from typing import List, Optional

from database import get_db
import models, schemas

router = APIRouter(prefix="/ipos", tags=["IPO新股"])


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
def get_ipo(ipo_id: int, blogger_id: Optional[int] = None, db: Session = Depends(get_db)):
    """获取单只新股详情及所有分析"""
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
