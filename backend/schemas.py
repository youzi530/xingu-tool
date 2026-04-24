from pydantic import BaseModel
from typing import Optional, List
from datetime import date, datetime
from models import IPOStatus, SourceChannel


# ── Blogger ──────────────────────────────────────────────────────────────────

class BloggerBase(BaseModel):
    name: str
    channel: SourceChannel = SourceChannel.wechat
    wechat_id: Optional[str] = None
    avatar_url: Optional[str] = None
    description: Optional[str] = None
    follower_count: Optional[str] = None


class BloggerCreate(BloggerBase):
    pass


class BloggerOut(BloggerBase):
    id: int
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# ── IPO ──────────────────────────────────────────────────────────────────────

class IPOBase(BaseModel):
    stock_code: str
    stock_name: str
    exchange: str = "HKEX"
    industry: Optional[str] = None
    ipo_price_min: Optional[str] = None
    ipo_price_max: Optional[str] = None
    lot_size: Optional[int] = None
    subscribe_start: Optional[date] = None
    subscribe_end: Optional[date] = None
    allotment_date: Optional[date] = None
    listing_date: Optional[date] = None
    status: IPOStatus = IPOStatus.upcoming
    market_cap: Optional[str] = None
    description: Optional[str] = None
    data_source: Optional[str] = "manual"


class IPOCreate(IPOBase):
    pass


class IPOOut(IPOBase):
    id: int
    analysis_count: Optional[int] = 0
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# ── Analysis ─────────────────────────────────────────────────────────────────

class AnalysisBase(BaseModel):
    ipo_id: int
    blogger_id: int
    title: str
    summary: Optional[str] = None
    content_url: Optional[str] = None
    cover_image_url: Optional[str] = None
    source_channel: SourceChannel = SourceChannel.wechat
    published_at: Optional[datetime] = None
    view_count: int = 0
    like_count: int = 0
    recommendation: Optional[str] = None


class AnalysisCreate(AnalysisBase):
    pass


class AnalysisOut(AnalysisBase):
    id: int
    blogger: Optional[BloggerOut] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class IPOWithAnalyses(IPOOut):
    analyses: List[AnalysisOut] = []

    class Config:
        from_attributes = True
