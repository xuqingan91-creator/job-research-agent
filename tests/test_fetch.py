"""fetch 网页清洗与错误处理的测试（不联网）。"""

import pytest
import requests

from job_research_agent.fetch import FetchError, clean_html, fetch_page


SAMPLE_HTML = """
<html><head><title>T</title></head>
<body>
  <script>var secret = 1;</script>
  <nav>导航</nav>
  <p>这是正文第一句。</p>
  <p>这是正文第二句。</p>
</body></html>
"""


def test_clean_html_removes_script_and_nav():
    text = clean_html(SAMPLE_HTML)
    assert "secret" not in text
    assert "导航" not in text
    assert "这是正文第一句" in text
    assert "这是正文第二句" in text


def test_clean_html_truncates():
    text = clean_html(SAMPLE_HTML, max_chars=8)
    assert len(text) <= 8


def test_fetch_page_raises_fetch_error_on_network_failure(monkeypatch):
    def fake_get(url, headers=None, timeout=None):
        raise requests.ConnectionError("network down")

    monkeypatch.setattr("job_research_agent.fetch.requests.get", fake_get)
    with pytest.raises(FetchError):
        fetch_page("https://example.com/")
