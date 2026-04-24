from sqlalchemy import Column, Integer, String, Text, Date, DateTime, ForeignKey, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum

from database import Base


class IPOStatus(str, enum.Enum):
    upcoming = "upcoming"       # 即将认购
    subscribing = "subscribing" # 认购中
    listing = "listing"         # 即将上市
    listed = "listed"           # 已上市


class SourceChannel(str, enum.Enum):
    wechat = "wechat"   # 微信公众号
    xhs = "xhs"         # 小红书
    broker = "broker"   # 券商 App
    other = "other"


class IPO(Base):
    __tablename__ = "ipos"

    id = Column(Integer, primary_key=True, index=True)
    stock_code = Column(String(20), unique=True, index=True, nullable=False)
    stock_name = Column(String(100), nullable=False)
    exchange = Column(String(20), default="HKEX")          # 交易所，默认港交所
    industry = Column(String(50))                           # 所属行业
    ipo_price_min = Column(String(20))                      # 发行价区间下限
    ipo_price_max = Column(String(20))                      # 发行价区间上限
    lot_size = Column(Integer)                              # 每手股数
    subscribe_start = Column(Date)                          # 认购开始日
    subscribe_end = Column(Date)                            # 认购结束日
    allotment_date = Column(Date)                           # 中签结果公布日
    listing_date = Column(Date)                             # 上市日期
    status = Column(Enum(IPOStatus), default=IPOStatus.upcoming)
    market_cap = Column(String(30))                         # 市值（iTick 返回，如 "10.5B"）
    description = Column(Text)                              # 公司简介
    data_source = Column(String(20), default="manual")      # 数据来源：manual / itick
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    analyses = relationship("Analysis", back_populates="ipo", cascade="all, delete-orphan")


class Blogger(Base):
    __tablename__ = "bloggers"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)             # 博主名称
    channel = Column(Enum(SourceChannel), default=SourceChannel.wechat)
    wechat_id = Column(String(100))                        # 公众号 ID
    avatar_url = Column(String(500))                       # 头像链接
    description = Column(Text)                             # 博主简介
    follower_count = Column(String(20))                    # 粉丝数量（展示用）
    created_at = Column(DateTime, server_default=func.now())

    analyses = relationship("Analysis", back_populates="blogger")


class Analysis(Base):
    __tablename__ = "analyses"

    id = Column(Integer, primary_key=True, index=True)
    ipo_id = Column(Integer, ForeignKey("ipos.id"), nullable=False)
    blogger_id = Column(Integer, ForeignKey("bloggers.id"), nullable=False)
    title = Column(String(300), nullable=False)            # 文章标题
    summary = Column(Text)                                 # 摘要（从文章提取）
    content_url = Column(String(1000))                     # 原文链接
    cover_image_url = Column(String(500))                  # 封面图
    source_channel = Column(Enum(SourceChannel), default=SourceChannel.wechat)
    published_at = Column(DateTime)                        # 发布时间
    view_count = Column(Integer, default=0)                # 阅读量
    like_count = Column(Integer, default=0)                # 点赞数
    recommendation = Column(String(20))                    # 推荐结论：积极/中性/谨慎
    created_at = Column(DateTime, server_default=func.now())

    ipo = relationship("IPO", back_populates="analyses")
    blogger = relationship("Blogger", back_populates="analyses")
