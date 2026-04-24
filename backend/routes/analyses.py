from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from database import get_db
import models, schemas

router = APIRouter(prefix="/analyses", tags=["分析文章"])


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


@router.delete("/{analysis_id}", status_code=204)
def delete_analysis(analysis_id: int, db: Session = Depends(get_db)):
    a = db.query(models.Analysis).filter(models.Analysis.id == analysis_id).first()
    if not a:
        raise HTTPException(status_code=404, detail="分析不存在")
    db.delete(a)
    db.commit()
