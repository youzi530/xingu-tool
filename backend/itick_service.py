"""
iTick API 客户端
文档：https://docs.itick.org/zh-cn/rest-api/stocks/stock-ipo
"""
import os
import logging
from datetime import datetime, date, timezone
from typing import List, Optional
from dataclasses import dataclass

import httpx
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

ITICK_BASE = "https://api.itick.org"
ITICK_TOKEN = os.getenv("ITICK_TOKEN", "")


@dataclass
class ITIckIPO:
    """iTick 返回的原始新股数据"""
    listing_ts_ms: int          # dt  — 上市日期时间戳（毫秒）
    company_name: str           # cn  — 公司名称
    stock_code: str             # sc  — 股票代码
    exchange: str               # ex  — 交易所
    market_cap: str             # mc  — 市值（如 "10.5B"）
    price_range: str            # pr  — 发行价（如 "3.50-4.50" 或 "5.00"）
    country: str                # ct  — 国家代码
    subscribe_start_ts: int     # bs  — 申购开始时间（秒）
    subscribe_end_ts: int       # es  — 申购截止时间（秒）
    allotment_ts: int           # ro  — 公布中签时间（秒）


def _ts_ms_to_date(ts_ms: int) -> Optional[date]:
    """毫秒时间戳 → date"""
    if not ts_ms:
        return None
    try:
        return datetime.fromtimestamp(ts_ms / 1000, tz=timezone.utc).date()
    except Exception:
        return None


def _ts_s_to_date(ts_s: int) -> Optional[date]:
    """秒时间戳 → date"""
    if not ts_s:
        return None
    try:
        return datetime.fromtimestamp(ts_s, tz=timezone.utc).date()
    except Exception:
        return None


def _parse_price(price_str: str) -> tuple[Optional[str], Optional[str]]:
    """
    解析价格区间字符串
    "3.50-4.50"  → ("3.50", "4.50")
    "5.00"       → ("5.00", "5.00")
    ""           → (None, None)
    """
    if not price_str:
        return None, None
    if "-" in price_str:
        parts = price_str.split("-", 1)
        return parts[0].strip(), parts[1].strip()
    return price_str.strip(), price_str.strip()


def _compute_status(
    subscribe_start: Optional[date],
    subscribe_end: Optional[date],
    listing_date: Optional[date],
) -> str:
    """根据日期推算新股当前状态"""
    today = date.today()

    if listing_date and listing_date <= today:
        return "listed"
    if subscribe_end and listing_date and subscribe_end < today < listing_date:
        return "listing"
    if subscribe_start and subscribe_end and subscribe_start <= today <= subscribe_end:
        return "subscribing"
    return "upcoming"


def _raw_to_ipo(item: dict) -> ITIckIPO:
    return ITIckIPO(
        listing_ts_ms=item.get("dt", 0),
        company_name=item.get("cn", ""),
        stock_code=item.get("sc", ""),
        exchange=item.get("ex", "HKEX"),
        market_cap=item.get("mc", ""),
        price_range=item.get("pr", ""),
        country=item.get("ct", ""),
        subscribe_start_ts=item.get("bs", 0),
        subscribe_end_ts=item.get("es", 0),
        allotment_ts=item.get("ro", 0),
    )


async def fetch_hk_ipos(ipo_type: str = "upcoming") -> List[ITIckIPO]:
    """
    拉取港股新股列表
    :param ipo_type: "upcoming"（即将上市）或 "recent"（近期已上市）
    :return: ITIckIPO 列表
    """
    if not ITICK_TOKEN or ITICK_TOKEN == "your_itick_token_here":
        logger.warning("ITICK_TOKEN 未配置，跳过 API 拉取")
        return []

    url = f"{ITICK_BASE}/stock/ipo"
    params = {"type": ipo_type, "region": "HK"}
    headers = {"accept": "application/json", "token": ITICK_TOKEN}

    all_items: List[ITIckIPO] = []
    page = 0

    async with httpx.AsyncClient(timeout=15) as client:
        while True:
            try:
                resp = await client.get(url, params={**params, "page": page}, headers=headers)
                resp.raise_for_status()
                data = resp.json()

                if data.get("code") != 0:
                    logger.error("iTick API 返回错误: %s", data.get("msg"))
                    break

                content = data.get("data", {}).get("content", [])
                if not content:
                    break

                all_items.extend(_raw_to_ipo(item) for item in content)

                payload = data.get("data", {})
                if payload.get("last", True):
                    break
                page += 1

            except httpx.HTTPError as e:
                logger.error("iTick HTTP 请求失败: %s", e)
                break

    logger.info("iTick 拉取 %s 港股新股 %d 条", ipo_type, len(all_items))
    return all_items


def normalize_ipo(raw: ITIckIPO) -> dict:
    """
    将 iTick 原始数据标准化为我们数据库字段格式
    """
    price_min, price_max = _parse_price(raw.price_range)
    subscribe_start = _ts_s_to_date(raw.subscribe_start_ts)
    subscribe_end = _ts_s_to_date(raw.subscribe_end_ts)
    listing_date = _ts_ms_to_date(raw.listing_ts_ms)
    allotment_date = _ts_s_to_date(raw.allotment_ts)
    status = _compute_status(subscribe_start, subscribe_end, listing_date)

    return {
        "stock_code": raw.stock_code,
        "stock_name": raw.company_name,
        "exchange": raw.exchange or "HKEX",
        "ipo_price_min": price_min,
        "ipo_price_max": price_max,
        "subscribe_start": subscribe_start,
        "subscribe_end": subscribe_end,
        "listing_date": listing_date,
        "allotment_date": allotment_date,
        "market_cap": raw.market_cap,
        "status": status,
        "data_source": "itick",
    }
