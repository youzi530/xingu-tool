from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
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
    q = db.query(models.IPO)
    if status:
        q = q.filter(models.IPO.status == status)
    ipos = q.order_by(models.IPO.subscribe_start.desc()).offset(skip).limit(limit).all()

    result = []
    for ipo in ipos:
        count = db.query(func.count(models.Analysis.id)).filter(
            models.Analysis.ipo_id == ipo.id
        ).scalar()
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

    analyses_query = db.query(models.Analysis).filter(models.Analysis.ipo_id == ipo_id)
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
