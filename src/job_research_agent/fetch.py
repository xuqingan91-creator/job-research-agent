"""网页抓取与正文清洗：requests + BeautifulSoup。"""

from __future__ import annotations

import requests
from bs4 import BeautifulSoup

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36"
)


class FetchError(RuntimeError):
    """网页抓取失败。"""


def clean_html(html: str, max_chars: int = 4000) -> str:
    """把 HTML 清洗成纯正文并截断；可离线测试。"""
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["script", "style", "nav", "header", "footer", "aside", "noscript"]):
        tag.decompose()
    lines = [line.strip() for line in soup.get_text("\n").splitlines() if line.strip()]
    return "\n".join(lines)[:max_chars]


def fetch_page(url: str, max_chars: int = 4000, timeout: float = 15.0) -> str:
    """抓取单个网页并返回清洗后的正文；失败抛 FetchError。"""
    try:
        response = requests.get(
            url,
            headers={"User-Agent": USER_AGENT},
            timeout=timeout,
        )
        response.raise_for_status()
    except requests.RequestException as exc:
        raise FetchError(f"fetch failed for {url}: {exc}") from exc
    return clean_html(response.text, max_chars=max_chars)
