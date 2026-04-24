"""
从港股打新文章中提取 IPO 关键字段

支持从以下文本来源提取：
  - 文章标题
  - 搜狗摘要片段
  - 微信文章全文

提取字段：
  - stock_code        股票代码（如 01609、6978）
  - stock_name        股票名称
  - ipo_price_min     发行价区间下限
  - ipo_price_max     发行价区间上限
  - lot_size          每手股数
  - lot_cost          入场费（港元）
  - subscribe_start   认购开始日期
  - subscribe_end     认购截止日期
  - allotment_date    中签公布日期
  - listing_date      上市日期
"""

import re
import logging
from datetime import date, datetime, timedelta
from typing import Optional

logger = logging.getLogger(__name__)


# ── 辅助：日期解析 ──────────────────────────────────────────────────────────

def _parse_date_cn(text: str, ref_year: int = None) -> Optional[date]:
    """
    解析各种中文日期格式
    支持：4月25日 / 2026年4月25日 / 4/25 / 2026-04-25
    """
    if not text:
        return None
    year = ref_year or datetime.now().year

    # 2026年4月25日 or 4月25日
    m = re.search(r'(?:(\d{4})年)?(\d{1,2})月(\d{1,2})日', text)
    if m:
        y = int(m.group(1)) if m.group(1) else year
        try:
            return date(y, int(m.group(2)), int(m.group(3)))
        except ValueError:
            pass

    # 2026-04-25 or 2026/04/25
    m = re.search(r'(\d{4})[-/](\d{1,2})[-/](\d{1,2})', text)
    if m:
        try:
            return date(int(m.group(1)), int(m.group(2)), int(m.group(3)))
        except ValueError:
            pass

    # 4/25
    m = re.search(r'\b(\d{1,2})/(\d{1,2})\b', text)
    if m:
        try:
            return date(year, int(m.group(1)), int(m.group(2)))
        except ValueError:
            pass

    return None


def _clean_number(s: str) -> Optional[str]:
    """去掉逗号、空格，保留小数点"""
    if not s:
        return None
    cleaned = s.replace(',', '').replace('，', '').replace(' ', '').strip()
    if re.match(r'^\d+\.?\d*$', cleaned):
        return cleaned
    return None


# ── 核心提取函数 ────────────────────────────────────────────────────────────

def extract_ipo_fields(text: str) -> dict:
    """
    从任意文本中提取 IPO 关键字段，返回 dict（未找到的字段不包含在内）
    """
    if not text:
        return {}
    result = {}

    # ── 股票代码 ────────────────────────────────────────────────────────────
    # 匹配：01609 / 6978 / (1609.HK) / 01609.HK
    for pattern in [
        r'\(0?(\d{4})\.HK\)',           # (1609.HK)
        r'(?:港股代码|股票代码|代码)[：:]\s*0?(\d{4})',
        r'\b(0\d{4})\b',               # 05位数以0开头，如 01609
    ]:
        m = re.search(pattern, text, re.IGNORECASE)
        if m:
            code = m.group(1).lstrip('0')
            result['stock_code'] = code
            break

    # ── 发行价区间 ──────────────────────────────────────────────────────────
    # 匹配：HK$3.50-4.50 / 发行价3.5港元至4.5港元 / 招股价3.50 - 4.50 / 发行价约4.00
    price_patterns = [
        # 区间：X.XX-Y.YY
        r'(?:发行价|招股价|发售价)[格]?[约为是]?(?:港币|港元|HK\$?)?\s*(\d+\.?\d*)\s*[-至到~～]\s*(\d+\.?\d*)',
        r'(?:HK\$|港元|港币)\s*(\d+\.?\d*)\s*[-至到~～]\s*(\d+\.?\d*)',
        r'定价区间[约为是]?(?:港币|港元|HK\$?)?\s*(\d+\.?\d*)\s*[-至到~～]\s*(\d+\.?\d*)',
    ]
    for p in price_patterns:
        m = re.search(p, text, re.IGNORECASE)
        if m:
            lo = _clean_number(m.group(1))
            hi = _clean_number(m.group(2))
            if lo and hi:
                result['ipo_price_min'] = lo
                result['ipo_price_max'] = hi
                break

    if 'ipo_price_min' not in result:
        # 单价
        for p in [
            r'(?:发行价|招股价|发售价)[格]?[约为是]?(?:港币|港元|HK\$?)?\s*(\d+\.?\d+)',
            r'(?:HK\$|港元|港币)\s*(\d+\.?\d+)\s*(?:认购|招股|每股)',
        ]:
            m = re.search(p, text, re.IGNORECASE)
            if m:
                v = _clean_number(m.group(1))
                if v:
                    result['ipo_price_min'] = v
                    result['ipo_price_max'] = v
                    break

    # ── 每手股数 ────────────────────────────────────────────────────────────
    for p in [
        r'每手\s*(\d{2,6})\s*股',
        r'一手\s*(\d{2,6})\s*股',
        r'(?:认购|申购)单位[为是]?\s*(\d{2,6})\s*股',
        r'手数[为是]?\s*(\d{2,6})\s*股',
    ]:
        m = re.search(p, text)
        if m:
            v = _clean_number(m.group(1))
            if v:
                result['lot_size'] = int(v)
                break

    # 从入场费+发行价反推每手股数
    if 'lot_size' not in result and 'ipo_price_min' in result:
        for p in [
            r'入场费[约为]?\s*([\d,]+(?:\.\d+)?)\s*港元',
            r'(?:最低|认购)费用[约为]?\s*([\d,]+(?:\.\d+)?)\s*港元',
        ]:
            m = re.search(p, text)
            if m:
                fee = _clean_number(m.group(1))
                price = float(result['ipo_price_min'])
                if fee and price > 0:
                    lot = round(float(fee) / price)
                    # 取最近的整百数
                    for base in [100, 200, 500, 1000, 2000, 5000]:
                        if abs(lot - base) / base < 0.1:
                            result['lot_size'] = base
                            break
                break

    # ── 入场费（直接存储，供展示用）─────────────────────────────────────────
    for p in [
        r'入场费[约为]?\s*([\d,]+(?:\.\d+)?)\s*(?:港元|HK\$|港币)',
        r'每手费用[约为]?\s*([\d,]+(?:\.\d+)?)\s*(?:港元|HK\$)',
    ]:
        m = re.search(p, text)
        if m:
            v = _clean_number(m.group(1))
            if v:
                result['lot_cost'] = v
                break

    # ── 认购日期 ─────────────────────────────────────────────────────────────
    # 认购开始
    for p in [
        r'(?:招股|认购|申购)(?:开始|起)[日期]?[：:\s]*([\d年月日/\-]+)',
        r'(?:即日|今日|明日|今起|即起)起?招股',
        r'自\s*([\d年月日/\-]+)\s*(?:起|开始)(?:招股|认购)',
    ]:
        m = re.search(p, text)
        if m and m.lastindex and m.group(1):
            d = _parse_date_cn(m.group(1))
            if d:
                result['subscribe_start'] = d
                break

    # 认购截止
    for p in [
        r'(?:招股|认购|申购)(?:截止|结束|至)[日期]?[：:\s为]?([\d年月日/\-]+)',
        r'(?:截止|结束)(?:招股|认购|申购)[日期]?[：:\s为]?([\d年月日/\-]+)',
        r'招股至\s*([\d年月日/\-]+)',
        r'认购期(?:至|到|截至)\s*([\d年月日/\-]+)',
    ]:
        m = re.search(p, text)
        if m:
            d = _parse_date_cn(m.group(1))
            if d:
                result['subscribe_end'] = d
                break

    # 认购区间（如 "4月22日至4月25日"）
    m = re.search(
        r'(?:招股|认购|申购)(?:日期|期间)?[：:\s]?([\d月日/\-]+)\s*(?:至|到|~|～|-)\s*([\d年月日/\-]+)',
        text
    )
    if m:
        if 'subscribe_start' not in result:
            d = _parse_date_cn(m.group(1))
            if d:
                result['subscribe_start'] = d
        if 'subscribe_end' not in result:
            d = _parse_date_cn(m.group(2))
            if d:
                result['subscribe_end'] = d

    # ── 中签公布日 ───────────────────────────────────────────────────────────
    for p in [
        r'(?:中签|认购结果|配售结果)(?:公布|公告|揭晓)[：:\s]*([\d年月日/\-]+)',
        r'(?:公布|公告)(?:中签|认购结果)[：:\s]*([\d年月日/\-]+)',
    ]:
        m = re.search(p, text)
        if m:
            d = _parse_date_cn(m.group(1))
            if d:
                result['allotment_date'] = d
                break

    # ── 上市日期 ─────────────────────────────────────────────────────────────
    for p in [
        r'(?:预计|预期)?上市(?:日期|时间)?[：:\s]*([\d年月日/\-]+)',
        r'([\d年月日/\-]+)\s*(?:正式)?上市',
        r'挂牌(?:日期)?[：:\s]*([\d年月日/\-]+)',
    ]:
        m = re.search(p, text)
        if m:
            d = _parse_date_cn(m.group(1))
            if d:
                result['listing_date'] = d
                break

    return result


def extract_ipo_name_from_text(text: str) -> list[str]:
    """
    从文章文本中提取可能的新股名称列表（精确匹配，降低噪音）
    """
    names = []

    # 噪音词，含这些词的名称直接过滤
    NOISE_WORDS = {'佳节', '福利', '集赞', '活动', '转发', '抽奖', '恭喜', '祝福',
                   '通知', '公告', '声明', '招聘', '直播', '课程', '讲座', '报名',
                   '元宵', '春节', '国庆', '中秋', '端午', '五一', '十一'}

    def is_valid_name(n: str) -> bool:
        if len(n) < 2 or len(n) > 12:
            return False
        # 含噪音词的过滤
        if any(w in n for w in NOISE_WORDS):
            return False
        # 纯英文数字跳过（可能是股票代码）
        if re.match(r'^[A-Za-z0-9\s.]+$', n):
            return False
        # 含太多标点的跳过
        if len(re.findall(r'[，。！？、；：""''【】]', n)) > 1:
            return False
        return True

    # 模式1：公司名 + HK 代码（最可靠）
    for m in re.finditer(r'([^\s（(,，。！\n]{2,12})\s*[\(（]0?\d{4}\.HK[\)）]', text):
        name = m.group(1).strip()
        if is_valid_name(name):
            names.append(name)

    # 模式2：【公司名】打新 或 「公司名」
    for m in re.finditer(r'[【「]\s*([^【】「」|｜\n,，]{2,12})\s*[】」]', text):
        name = m.group(1).strip()
        # 后面必须紧跟打新/招股/IPO 相关词
        pos = m.end()
        context = text[pos:pos+10]
        if re.search(r'打新|招股|IPO|认购|申购', context) and is_valid_name(name):
            if name not in names:
                names.append(name)

    # 模式3：港股打新| or 港股打新丨后面的公司名
    for m in re.finditer(r'港股打新\s*[|｜丨]\s*([^\s|｜丨\n,，。！]{2,12})', text):
        name = m.group(1).strip()
        if is_valid_name(name) and name not in names:
            names.append(name)

    return list(dict.fromkeys(names))  # 保序去重


def fields_missing(ipo) -> list[str]:
    """返回 IPO 对象中缺失的关键字段列表"""
    missing = []
    if not ipo.ipo_price_min:
        missing.append('ipo_price_min')
    if not ipo.ipo_price_max:
        missing.append('ipo_price_max')
    if not ipo.lot_size:
        missing.append('lot_size')
    if not ipo.subscribe_start:
        missing.append('subscribe_start')
    if not ipo.subscribe_end:
        missing.append('subscribe_end')
    if not ipo.listing_date:
        missing.append('listing_date')
    return missing
