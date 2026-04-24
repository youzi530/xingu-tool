"""
微信公众号文章抓取服务

原理：公众号文章的 HTML 页面即使触发「环境异常」验证横幅，
      真实文章内容依然内嵌在同一个 HTML 的 #js_content 区块内，
      直接解析 DOM 即可提取。

局限：
  - 仅适用于已公开的文章链接（未删除、未设私密）
  - 不需要登录/Cookie
  - 图片链接会失效（微信图片有防盗链），仅可保留 alt 文本
  - 若腾讯加强反爬，可能需要更换 UA 或增加延迟
"""
import re
import logging
from dataclasses import dataclass, field
from typing import Optional
from datetime import datetime

import httpx
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) "
        "AppleWebKit/605.1.15 (KHTML, like Gecko) "
        "Version/16.0 Mobile/15E148 Safari/604.1"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "zh-CN,zh;q=0.9",
    "Referer": "https://mp.weixin.qq.com/",
}


@dataclass
class WechatArticle:
    url: str
    title: str = ""
    author: str = ""           # 作者/公众号名
    published_at: Optional[datetime] = None
    cover_image_url: str = ""
    content_text: str = ""     # 纯文本正文
    content_html: str = ""     # 清理后的 HTML（保留段落结构）
    summary: str = ""          # 前 200 字作摘要
    success: bool = False
    error: str = ""


def _extract_publish_time(soup: BeautifulSoup, html: str) -> Optional[datetime]:
    """从多处尝试提取发布时间"""
    # 方式1：meta 标签
    meta = soup.find("meta", attrs={"name": "og:article:published_time"})
    if meta and meta.get("content"):
        try:
            return datetime.fromisoformat(meta["content"].replace("Z", "+00:00"))
        except Exception:
            pass

    # 方式2：js 变量 var ct = "1234567890"
    m = re.search(r'var\s+ct\s*=\s*"(\d+)"', html)
    if m:
        try:
            return datetime.fromtimestamp(int(m.group(1)))
        except Exception:
            pass

    # 方式3：publish_time span
    span = soup.find("em", id="publish_time")
    if span:
        text = span.get_text(strip=True)
        for fmt in ["%Y-%m-%d", "%Y年%m月%d日"]:
            try:
                return datetime.strptime(text[:10], fmt)
            except Exception:
                pass

    return None


def _clean_content(soup: BeautifulSoup) -> tuple[str, str]:
    """
    从 #js_content 提取正文
    返回 (content_html, content_text)
    """
    content_div = soup.find(id="js_content")
    if not content_div:
        return "", ""

    # 移除脚本和样式
    for tag in content_div.find_all(["script", "style", "iframe"]):
        tag.decompose()

    # 提取纯文本
    content_text = content_div.get_text(separator="\n", strip=True)
    # 压缩连续空行
    content_text = re.sub(r"\n{3,}", "\n\n", content_text).strip()

    # 清理 HTML：移除内联 style / class，保留段落结构
    for tag in content_div.find_all(True):
        tag.attrs = {k: v for k, v in tag.attrs.items()
                     if k in ("href", "src", "alt")}

    content_html = str(content_div)

    return content_html, content_text


async def fetch_article(url: str, timeout: int = 15) -> WechatArticle:
    """
    异步抓取一篇公众号文章，返回结构化数据
    """
    article = WechatArticle(url=url)

    try:
        async with httpx.AsyncClient(
            headers=HEADERS,
            follow_redirects=True,
            timeout=timeout,
        ) as client:
            resp = await client.get(url)
            resp.raise_for_status()
            html = resp.text

        soup = BeautifulSoup(html, "lxml")

        # ── 标题 ──────────────────────────────────────────────────────────
        title_tag = (
            soup.find("h1", id="activity-name")
            or soup.find("h2", class_=re.compile("rich_media_title"))
            or soup.find("meta", attrs={"property": "og:title"})
        )
        if title_tag:
            article.title = (
                title_tag.get("content", "")
                or title_tag.get_text(strip=True)
            )

        # ── 公众号名/作者 ──────────────────────────────────────────────────
        author_tag = (
            soup.find("a", id="js_name")
            or soup.find(id="profileBt")
        )
        if author_tag:
            article.author = author_tag.get_text(strip=True)
        else:
            # fallback: og:site_name
            meta_site = soup.find("meta", attrs={"property": "og:site_name"})
            if meta_site:
                article.author = meta_site.get("content", "")

        # ── 封面图 ────────────────────────────────────────────────────────
        meta_img = soup.find("meta", attrs={"property": "og:image"})
        if meta_img:
            article.cover_image_url = meta_img.get("content", "")

        # ── 发布时间 ──────────────────────────────────────────────────────
        article.published_at = _extract_publish_time(soup, html)

        # ── 正文 ──────────────────────────────────────────────────────────
        article.content_html, article.content_text = _clean_content(soup)

        if not article.content_text:
            article.error = "未找到正文内容（js_content 为空）"
        else:
            # 摘要：取前 200 字，去掉开头空白行
            lines = [l for l in article.content_text.splitlines() if l.strip()]
            article.summary = "".join(lines)[:200]
            article.success = True

        logger.info("抓取成功：%s（%d 字）", article.title[:30], len(article.content_text))

    except httpx.HTTPStatusError as e:
        article.error = f"HTTP {e.response.status_code}"
        logger.warning("抓取失败 %s: %s", url, article.error)
    except Exception as e:
        article.error = str(e)
        logger.warning("抓取异常 %s: %s", url, article.error)

    return article
