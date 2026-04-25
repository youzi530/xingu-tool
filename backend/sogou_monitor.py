"""
搜狗微信搜索监控服务

工作机制：
  搜狗微信搜索（weixin.sogou.com）无需登录即可搜索公众号文章。
  对每只活跃新股，搜索 "{股票名} 打新"，从结果中提取：
    - 标题、发布账号、摘要片段、真实微信文章链接

反爬应对（三道防线）：
  1. 代理自动探测：启动时检测本地是否有 HTTP/SOCKS5 代理（ClashX 等），
     有则 Python 直接走代理出口，避开数据中心 IP 封禁。
     也可手动在 .env 中配置 SOGOU_PROXY=http://127.0.0.1:7890。
  2. Cookie 复用：.env 中配置 SOGOU_COOKIE，通过 Cookie 降低触发验证码概率。
  3. Playwright 兜底：当 httpx 被反爬拦截时，自动切换到 Playwright 浏览器
     重试，浏览器会继承系统代理（如 TUN 模式 VPN）并自动刷新 Cookie。

部署建议：
  - 部署到国内/香港云服务器后，IP 通常不被搜狗封禁，无需以上配置。
"""

import asyncio
import logging
import os
import random
import re
import subprocess
from dataclasses import dataclass
from datetime import datetime
from difflib import SequenceMatcher
from typing import List, Optional

import httpx
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

SOGOU_SEARCH = "https://weixin.sogou.com/weixin"
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
    "Accept-Encoding": "gzip, deflate, br",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1",
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "none",
    "Referer": "https://weixin.sogou.com/",
}

# ─── 代理管理 ──────────────────────────────────────────────────────────────────

_proxy_cache: Optional[str] = None   # 已探测到的可用代理 URL，None 表示尚未探测
_proxy_detected: bool = False        # 是否已完成探测


def _get_sogou_cookie() -> str:
    """从环境变量读取 Sogou Cookie"""
    return os.getenv("SOGOU_COOKIE", "")


async def _test_proxy(url: str) -> Optional[str]:
    """测试一个代理 URL 是否可用（能访问 Sogou 且不触发反爬），返回代理 URL 或 None"""
    try:
        async with httpx.AsyncClient(
            proxy=url,
            follow_redirects=False,
            timeout=5,
        ) as c:
            r = await c.get(
                SOGOU_SEARCH,
                params={"type": "2", "query": "test", "ie": "utf8"},
            )
            # 能正常返回（200 或带有 set-cookie 的 302 非 antispider）
            if r.status_code == 200:
                return url
            loc = r.headers.get("location", "")
            if r.status_code in (301, 302) and "antispider" not in loc:
                return url
    except Exception:
        pass
    return None


async def _detect_proxy() -> Optional[str]:
    """
    自动探测本地可用的代理。探测顺序：
    1. 环境变量 SOGOU_PROXY（用户手动配置）
    2. ClashX Pro / Clash 默认端口 7890（HTTP）、7891（SOCKS5）
    3. 其他常见代理端口
    """
    global _proxy_cache, _proxy_detected
    if _proxy_detected:
        return _proxy_cache
    _proxy_detected = True

    # 1. 环境变量优先
    env_proxy = os.getenv("SOGOU_PROXY", "").strip()
    if env_proxy:
        logger.info("使用环境变量配置的代理: %s", env_proxy)
        _proxy_cache = env_proxy
        return _proxy_cache

    # 2. 常见代理端口，HTTP 优先，再试 SOCKS5
    candidates = []
    for port in [7890, 7891, 1080, 1086, 1087, 8080, 8888, 10808]:
        candidates.append(f"http://127.0.0.1:{port}")
        candidates.append(f"socks5://127.0.0.1:{port}")

    tasks = [_test_proxy(p) for p in candidates]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    for proxy_url, result in zip(candidates, results):
        if result and isinstance(result, str):
            logger.info("✅ 探测到可用代理: %s", proxy_url)
            _proxy_cache = proxy_url
            return _proxy_cache

    logger.info("未探测到可用本地代理，将直连（若部署在云服务器则属正常）")
    _proxy_cache = None
    return None


def reset_proxy_cache():
    """重置代理探测缓存，下次请求时重新探测（切换代理后调用）"""
    global _proxy_detected
    _proxy_detected = False


# ─── 辅助工具 ──────────────────────────────────────────────────────────────────

def _is_antispider_response(resp: httpx.Response) -> bool:
    if "antispider" in str(resp.url):
        return True
    if resp.status_code in (302, 301):
        location = resp.headers.get("location", "")
        if "antispider" in location:
            return True
    return False


def _extract_weixin_url_from_text(text: str) -> Optional[str]:
    patterns = [
        r'https?://mp\.weixin\.qq\.com/s/[A-Za-z0-9_\-]{10,}',
        r'https?://mp\.weixin\.qq\.com/s\?[A-Za-z0-9_\-=&%*]{20,}',
    ]
    for p in patterns:
        m = re.search(p, text)
        if m:
            return m.group(0).rstrip('"\'\\')
    return None


def _decode_sogou_url_param(sogou_url: str) -> Optional[str]:
    from urllib.parse import urlparse, parse_qs, unquote
    try:
        parsed = urlparse(sogou_url)
        params = parse_qs(parsed.query)
        raw = params.get("url", [""])[0]
        if not raw:
            return None
        decoded = unquote(raw)
        if "mp.weixin.qq.com" in decoded:
            return decoded
        m = re.search(r'https?://mp\.weixin\.qq\.com/[^\s\'"]+', decoded)
        if m:
            return m.group(0)
    except Exception:
        pass
    return None


def _fuzzy_match(a: str, b: str, threshold: float = 0.6) -> bool:
    a, b = a.strip().lower(), b.strip().lower()
    if a in b or b in a:
        return True
    return SequenceMatcher(None, a, b).ratio() >= threshold


def _parse_date(text: str) -> Optional[datetime]:
    from datetime import timedelta
    now = datetime.now()
    if not text:
        return None
    m = re.search(r'(\d+)小时前', text)
    if m:
        return now - timedelta(hours=int(m.group(1)))
    m = re.search(r'(\d+)天前', text)
    if m:
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


# ─── URL 解析 ─────────────────────────────────────────────────────────────────

async def resolve_article_url(url: str) -> str:
    """将搜狗跳转链接解析为永久的 mp.weixin.qq.com 链接"""
    if not url or "mp.weixin.qq.com" in url:
        return url

    decoded = _decode_sogou_url_param(url)
    if decoded:
        return decoded

    proxy = await _detect_proxy()
    try:
        async with httpx.AsyncClient(
            headers={**HEADERS, "Referer": "https://weixin.sogou.com/"},
            proxy=proxy,
            follow_redirects=True,
            timeout=10,
        ) as client:
            resp = await client.get(url)
            final = str(resp.url)
            if "mp.weixin.qq.com" in final:
                return final
            weixin_url = _extract_weixin_url_from_text(resp.text)
            if weixin_url:
                return weixin_url
    except Exception as e:
        logger.debug("URL 解析异常: %s", e)

    return url


# ─── 数据结构 ─────────────────────────────────────────────────────────────────

@dataclass
class SogouArticle:
    title: str
    account_name: str
    content_url: str
    summary: str
    published_at: Optional[datetime] = None


# ─── Playwright 兜底抓取 ──────────────────────────────────────────────────────

async def _search_with_playwright(query: str, proxy: Optional[str] = None) -> List[SogouArticle]:
    """
    用 Playwright 浏览器搜索搜狗（httpx 被反爬时的兜底方案）。
    浏览器会继承系统代理（TUN 模式 VPN 等），并自动处理 Cookie。
    自动将获取到的 Cookie 回写到 .env 文件，供下次 httpx 使用。
    """
    try:
        from playwright.async_api import async_playwright
    except ImportError:
        logger.warning("playwright 未安装，无法使用浏览器兜底。pip install playwright && playwright install chromium")
        return []

    results: List[SogouArticle] = []
    launch_kwargs = {
        "headless": True,
        "args": ["--no-sandbox", "--disable-dev-shm-usage"],
    }
    if proxy:
        launch_kwargs["proxy"] = {"server": proxy}

    try:
        async with async_playwright() as p:
            # 优先用系统 Chrome（继承系统代理），找不到再用 Playwright 自带 Chromium
            try:
                browser = await p.chromium.launch(channel="chrome", **launch_kwargs)
                logger.info("Playwright 使用系统 Chrome")
            except Exception:
                try:
                    browser = await p.chromium.launch(**launch_kwargs)
                    logger.info("Playwright 使用内置 Chromium")
                except Exception as e:
                    logger.warning("Playwright 浏览器启动失败: %s", e)
                    return []

            context = await browser.new_context(
                user_agent=HEADERS["User-Agent"],
                locale="zh-CN",
            )

            # 注入已有 Cookie
            cookie_str = _get_sogou_cookie()
            if cookie_str:
                cookies = []
                for part in cookie_str.split(";"):
                    part = part.strip()
                    if "=" in part:
                        k, v = part.split("=", 1)
                        cookies.append({"name": k.strip(), "value": v.strip(), "domain": ".sogou.com", "path": "/"})
                if cookies:
                    await context.add_cookies(cookies)

            page = await context.new_page()

            # 测试是否能正常访问
            url = f"{SOGOU_SEARCH}?type=2&query={query}&ie=utf8&page=1"
            try:
                resp = await page.goto(url, wait_until="domcontentloaded", timeout=20000)
            except Exception as e:
                logger.warning("Playwright 导航失败: %s", e)
                await browser.close()
                return []

            current_url = page.url
            if "antispider" in current_url:
                logger.warning("Playwright 也被反爬拦截！当前 IP 被搜狗完全封禁，需更换 IP 或等待解封。")
                await browser.close()
                return []

            # 自动刷新 Cookie：从 Playwright 浏览器提取并回写到 .env
            await _refresh_cookie_from_playwright(context)

            # 解析结果
            html = await page.content()
            soup = BeautifulSoup(html, "lxml")
            items = soup.select(".news-box .news-list li")
            logger.info("Playwright 搜狗搜索 [%s] 找到 %d 条结果", query, len(items))

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
                if href.startswith("/"):
                    href = f"https://weixin.sogou.com{href}"

                for el in [title_el, item]:
                    for attr in ("data-url", "data-weixin-url", "data-article-url"):
                        candidate = el.get(attr, "")
                        if candidate and "mp.weixin.qq.com" in candidate:
                            href = candidate
                            break
                    if "mp.weixin.qq.com" in href:
                        break

                if "mp.weixin.qq.com" not in href and "sogou.com" in href:
                    decoded = _decode_sogou_url_param(href)
                    if decoded:
                        href = decoded

                title = re.sub(r"<!--.*?-->", "", title_el.get_text(separator="", strip=True))
                account = account_el.get_text(strip=True) if account_el else ""
                summary = summary_el.get_text(strip=True)[:200] if summary_el else ""
                summary = re.sub(r"<!--.*?-->", "", summary)
                results.append(SogouArticle(
                    title=title,
                    account_name=account,
                    content_url=href,
                    summary=summary,
                    published_at=_parse_date(date_el.get_text(strip=True) if date_el else ""),
                ))

            await browser.close()

    except Exception as e:
        logger.warning("Playwright 抓取异常: %s", e)

    return results


async def _refresh_cookie_from_playwright(context) -> None:
    """从 Playwright 浏览器提取 Sogou Cookie 并自动更新 .env 文件"""
    try:
        cookies = await context.cookies("https://weixin.sogou.com")
        if not cookies:
            return
        cookie_str = "; ".join(f'{c["name"]}={c["value"]}' for c in cookies)
        if not cookie_str:
            return

        # 更新内存中的环境变量
        os.environ["SOGOU_COOKIE"] = cookie_str

        # 回写 .env 文件
        env_path = os.path.join(os.path.dirname(__file__), ".env")
        if not os.path.exists(env_path):
            return

        with open(env_path, "r", encoding="utf-8") as f:
            lines = f.readlines()

        new_lines = []
        found = False
        for line in lines:
            if line.startswith("SOGOU_COOKIE="):
                new_lines.append(f"SOGOU_COOKIE={cookie_str}\n")
                found = True
            else:
                new_lines.append(line)
        if not found:
            new_lines.append(f"\nSOGOU_COOKIE={cookie_str}\n")

        with open(env_path, "w", encoding="utf-8") as f:
            f.writelines(new_lines)

        logger.info("✅ Sogou Cookie 已自动刷新（%d 个字符）", len(cookie_str))
    except Exception as e:
        logger.debug("Cookie 自动刷新失败: %s", e)


# ─── 主搜索入口 ───────────────────────────────────────────────────────────────

async def search_articles(query: str, max_pages: int = 2) -> List[SogouArticle]:
    """
    搜索搜狗微信，返回文章列表。
    先用 httpx 快速尝试（会自动使用代理），被反爬则切换到 Playwright 浏览器。
    """
    proxy = await _detect_proxy()
    results = await _search_with_httpx(query, max_pages, proxy)

    if not results:
        # httpx 失败或被拦截，切换 Playwright 兜底
        logger.info("httpx 搜索为空，切换 Playwright 浏览器重试: %s", query)
        results = await _search_with_playwright(query, proxy)

    return results


async def _search_with_httpx(query: str, max_pages: int, proxy: Optional[str]) -> List[SogouArticle]:
    """用 httpx 搜索搜狗（快速路径）"""
    results: List[SogouArticle] = []

    request_headers = dict(HEADERS)
    cookie = _get_sogou_cookie()
    if cookie:
        request_headers["Cookie"] = cookie

    async with httpx.AsyncClient(
        headers=request_headers,
        proxy=proxy,
        follow_redirects=False,
        timeout=12,
    ) as client:
        for page in range(max_pages):
            params = {"type": "2", "query": query, "ie": "utf8", "page": str(page + 1)}
            try:
                resp = await client.get(SOGOU_SEARCH, params=params)

                if _is_antispider_response(resp):
                    proxy_info = f"（代理: {proxy}）" if proxy else "（直连）"
                    logger.warning("搜狗触发反爬拦截 %s，query=%s，将切换 Playwright", proxy_info, query)
                    break

                if resp.status_code in (301, 302):
                    location = resp.headers.get("location", "")
                    if location and "antispider" not in location:
                        resp = await client.get(location)

                if resp.status_code != 200:
                    logger.warning("搜狗返回 %d，query=%s", resp.status_code, query)
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
                    if href.startswith("/"):
                        href = f"https://weixin.sogou.com{href}"
                    for el in [title_el, item]:
                        for attr in ("data-url", "data-weixin-url", "data-article-url"):
                            candidate = el.get(attr, "")
                            if candidate and "mp.weixin.qq.com" in candidate:
                                href = candidate
                                break
                        if "mp.weixin.qq.com" in href:
                            break
                    if "mp.weixin.qq.com" not in href and "sogou.com" in href:
                        decoded = _decode_sogou_url_param(href)
                        if decoded:
                            href = decoded

                    title = re.sub(r"<!--.*?-->", "", title_el.get_text(separator="", strip=True))
                    account = account_el.get_text(strip=True) if account_el else ""
                    summary = summary_el.get_text(strip=True)[:200] if summary_el else ""
                    results.append(SogouArticle(
                        title=title,
                        account_name=account,
                        content_url=href,
                        summary=summary,
                        published_at=_parse_date(date_el.get_text(strip=True) if date_el else ""),
                    ))

                if page < max_pages - 1:
                    await asyncio.sleep(random.uniform(3, 6))

            except httpx.HTTPError as e:
                logger.warning("搜狗请求异常: %s", e)
                break

    logger.info("httpx 搜索 [%s] 找到 %d 篇", query, len(results))
    return results


# ─── 批量新股监控 ─────────────────────────────────────────────────────────────

async def monitor_ipo_articles(db_session, active_ipos, bloggers) -> dict:
    """对每只活跃新股执行搜索，新文章自动入库。"""
    import models

    found_total = saved_total = 0

    existing_urls: set = {
        row.content_url
        for row in db_session.query(models.Analysis.content_url).all()
        if row.content_url
    }

    for ipo in active_ipos:
        has_chinese = any('\u4e00' <= c <= '\u9fff' for c in ipo.stock_name)
        if not has_chinese:
            logger.info("跳过英文名股票（搜索无效）: %s [%s]", ipo.stock_name, ipo.stock_code)
            continue

        query = f"{ipo.stock_name} 打新"
        logger.info("搜索新股文章: %s", query)

        articles = await search_articles(query, max_pages=2)
        found_total += len(articles)

        for art in articles:
            if art.content_url in existing_urls:
                continue

            matched_blogger = None
            for blogger in bloggers:
                if _fuzzy_match(blogger.name, art.account_name):
                    matched_blogger = blogger
                    break

            if not matched_blogger and art.account_name:
                matched_blogger = models.Blogger(
                    name=art.account_name,
                    channel=models.SourceChannel.wechat,
                    description="由搜狗搜索自动发现",
                )
                db_session.add(matched_blogger)
                db_session.flush()
                bloggers.append(matched_blogger)
                logger.info("自动创建新博主: %s", art.account_name)

            if not matched_blogger:
                continue

            real_url = await resolve_article_url(art.content_url)

            analysis = models.Analysis(
                ipo_id=ipo.id,
                blogger_id=matched_blogger.id,
                title=art.title,
                summary=art.summary,
                content_url=real_url,
                source_channel=models.SourceChannel.wechat,
                published_at=art.published_at,
            )
            db_session.add(analysis)
            existing_urls.add(art.content_url)
            saved_total += 1
            logger.info("  ✅ 保存: [%s] %s", matched_blogger.name, art.title[:40])
            await asyncio.sleep(0.5)

        await asyncio.sleep(random.uniform(8, 15))

    db_session.commit()
    logger.info("文章监控完成：共发现 %d 篇，入库 %d 篇", found_total, saved_total)
    return {
        "found": found_total,
        "saved": saved_total,
        "ipos_searched": len(active_ipos),
    }
