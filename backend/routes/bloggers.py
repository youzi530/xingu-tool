from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from database import get_db
import models, schemas

router = APIRouter(prefix="/bloggers", tags=["博主"])


@router.get("/", response_model=List[schemas.BloggerOut])
def list_bloggers(db: Session = Depends(get_db)):
    return db.query(models.Blogger).order_by(models.Blogger.name).all()


@router.get("/{blogger_id}", response_model=schemas.BloggerOut)
def get_blogger(blogger_id: int, db: Session = Depends(get_db)):
    b = db.query(models.Blogger).filter(models.Blogger.id == blogger_id).first()
    if not b:
        raise HTTPException(status_code=404, detail="博主不存在")
    return b


@router.post("/", response_model=schemas.BloggerOut, status_code=201)
def create_blogger(payload: schemas.BloggerCreate, db: Session = Depends(get_db)):
    blogger = models.Blogger(**payload.model_dump())
    db.add(blogger)
    db.commit()
    db.refresh(blogger)
    return blogger
