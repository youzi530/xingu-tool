"""
搜狗微信搜索监控服务

原理：
  搜狗微信搜索（weixin.sogou.com）无需登录即可搜索公众号文章。
  对每只活跃新股，搜索 "{股票名} 打新"，从结果中提取：
    - 标题、发布账号、摘要片段、搜狗跳转链接
  与数据库中已配置的博主名单做匹配，命中则自动入库。

注意：
  - content_url 存储搜狗跳转链接，App 内 WebView 能正常打开（真实浏览器不被拦截）
  - 每只新股搜索间隔 2 秒，避免被搜狗封 IP
  - 若文章 URL 已存在则跳过（去重）
"""

import asyncio
import logging
import re
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional
from difflib import SequenceMatcher

import httpx
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

SOGOU_SEARCH = "https://weixin.sogou.com/weixin"
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9",
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
    "Referer": "https://weixin.sogou.com/",
}


@dataclass
class SogouArticle:
    title: str
    account_name: str           # 公众号名
    content_url: str            # 搜狗跳转链接（可在浏览器/WebView 打开）
    summary: str                # 搜狗摘要片段
    published_at: Optional[datetime] = None


def _fuzzy_match(a: str, b: str, threshold: float = 0.6) -> bool:
    """模糊匹配两个字符串，相似度超过阈值视为匹配"""
    a, b = a.strip().lower(), b.strip().lower()
    if a in b or b in a:
        return True
    ratio = SequenceMatcher(None, a, b).ratio()
    return ratio >= threshold


def _parse_date(text: str) -> Optional[datetime]:
    """从搜狗结果里解析时间，如 '4小时前' / '1天前' / '2026-04-24'"""
    now = datetime.now()
    if not text:
        return None
    m = re.search(r'(\d+)小时前', text)
    if m:
        from datetime import timedelta
        return now - timedelta(hours=int(m.group(1)))
    m = re.search(r'(\d+)天前', text)
    if m:
        from datetime import timedelta
        return now - timedelta(days=int(m.group(1)))
    m = re.search(r'(\d{4})-(\d{2})-(\d{2})', text)
    if m:
        try:
            return datetime(int(m.group(1)), int(m.group(2)), int(m.group(3)))
        except Exception:
            pass
    m = re.search(r'(\d+)月(\d+)日', text)
    if m:
        try:
            return datetime(now.year, int(m.group(1)), int(m.group(2)))
        except Exception:
            pass
    return None


async def search_articles(query: str, max_pages: int = 2) -> List[SogouArticle]:
    """
    搜索搜狗微信，返回文章列表
    :param query: 搜索关键词，如 "天星医疗 打新"
    :param max_pages: 最多抓取页数
    """
    results: List[SogouArticle] = []

    async with httpx.AsyncClient(headers=HEADERS, follow_redirects=True, timeout=12) as client:
        for page in range(max_pages):
            params = {
                "type": "2",
                "query": query,
                "ie": "utf8",
                "page": str(page + 1),
            }
            try:
                resp = await client.get(SOGOU_SEARCH, params=params)
                if resp.status_code != 200:
                    logger.warning("搜狗搜索返回 %d, query=%s", resp.status_code, query)
                    break

                soup = BeautifulSoup(resp.text, "lxml")
                items = soup.select(".news-box .news-list li")
                if not items:
                    break

                for item in items:
                    title_el = item.select_one("h3 a")
                    account_el = item.select_one("div.s-p") or item.select_one("span.all-time-y2")
                    summary_el = item.select_one("p.txt-info")
                    date_el = item.select_one("span.s2") or item.select_one("span.time")

                    if not title_el:
                        continue

                    href = title_el.get("href", "")
                    if not href:
                        continue
                    # 补全为完整 URL
                    if href.startswith("/"):
                        href = f"https://weixin.sogou.com{href}"

                    # 清理标题（去掉 em 标签的 HTML 高亮标记）
                    title = re.sub(r"<!--.*?-->", "", title_el.get_text(separator="", strip=True))
                    account = account_el.get_text(strip=True) if account_el else ""
                    summary = summary_el.get_text(strip=True)[:200] if summary_el else ""
                    summary = re.sub(r"<!--.*?-->", "", summary)
                    date_text = date_el.get_text(strip=True) if date_el else ""

                    results.append(SogouArticle(
                        title=title,
                        account_name=account,
                        content_url=href,
                        summary=summary,
                        published_at=_parse_date(date_text),
                    ))

                # 礼貌性等待，避免 IP 被封
                if page < max_pages - 1:
                    await asyncio.sleep(1.5)

            except httpx.HTTPError as e:
                logger.warning("搜狗请求失败: %s", e)
                break

    logger.info("搜狗搜索 [%s] 找到 %d 篇文章", query, len(results))
    return results


async def monitor_ipo_articles(db_session, active_ipos, bloggers) -> dict:
    """
    对每只活跃新股执行搜索，匹配已配置博主，新文章自动入库。

    :param db_session: SQLAlchemy Session
    :param active_ipos:  IPO 对象列表（status in upcoming/subscribing/listing）
    :param bloggers:     Blogger 对象列表
    :return: 统计摘要 {"found": N, "saved": N, "ipos_searched": N}
    """
    import models

    found_total = saved_total = 0
    blogger_names = {b.id: b.name for b in bloggers}

    # 预加载已有 analysis 的 URL 集合，用于去重
    existing_urls: set = {
        row.content_url
        for row in db_session.query(models.Analysis.content_url).all()
        if row.content_url
    }

    for ipo in active_ipos:
        # 构建搜索关键词：股票名 + 打新
        query = f"{ipo.stock_name} 打新"
        logger.info("搜索新股文章: %s", query)

        articles = await search_articles(query, max_pages=2)
        found_total += len(articles)

        for art in articles:
            # 去重
            if art.content_url in existing_urls:
                continue

            # 匹配博主：模糊匹配账号名
            matched_blogger = None
            for blogger in bloggers:
                if _fuzzy_match(blogger.name, art.account_name):
                    matched_blogger = blogger
                    break

            # 未匹配到已配置博主时，自动创建新博主条目
            if not matched_blogger and art.account_name:
                matched_blogger = models.Blogger(
                    name=art.account_name,
                    channel=models.SourceChannel.wechat,
                    description=f"由搜狗搜索自动发现",
                )
                db_session.add(matched_blogger)
                db_session.flush()  # 获取 id
                bloggers.append(matched_blogger)
                logger.info("自动创建新博主: %s", art.account_name)

            if not matched_blogger:
                continue

            analysis = models.Analysis(
                ipo_id=ipo.id,
                blogger_id=matched_blogger.id,
                title=art.title,
                summary=art.summary,
                content_url=art.content_url,
                source_channel=models.SourceChannel.wechat,
                published_at=art.published_at,
            )
            db_session.add(analysis)
            existing_urls.add(art.content_url)
            saved_total += 1
            logger.info("  ✅ 保存: [%s] %s", matched_blogger.name, art.title[:40])

        # 新股之间等待 2 秒
        await asyncio.sleep(2)

    db_session.commit()
    logger.info("文章监控完成：共发现 %d 篇，入库 %d 篇", found_total, saved_total)
    return {
        "found": found_total,
        "saved": saved_total,
        "ipos_searched": len(active_ipos),
    }
