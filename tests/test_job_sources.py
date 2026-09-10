"""岗位来源分类、博客抑制与地区筛选。"""

from job_research_agent.job_discovery import (
    classify_posting,
    classify_source,
    extract_location,
    recommend_jobs,
)
from job_research_agent.schemas import JobPosting, SourceItem


def test_classify_source_types():
    assert classify_source("https://careers.tencent.com/job/1") == "official"
    assert classify_source("https://www.zhipin.com/job_detail/x.html") == "job_platform"
    assert classify_source("https://www.zhaopin.com/job/x.html") == "job_platform"
    assert classify_source("https://blog.csdn.net/x/article/1") == "blog"
    assert classify_source("https://www.joyehuang.me/blog/20260309-agent/post") == "blog"
    assert classify_source("https://career.nankai.edu.cn/correcruit/content/id/1.html") == "blocked"
    assert classify_source("https://example.com/unknown") == "other"


def test_article_urls_are_classified_as_blog_even_on_job_platforms():
    assert (
        classify_source("https://www.nowcoder.com/feed/main/detail/abc123")
        == "blog"
    )
    assert (
        classify_source("https://www.nowcoder.com/jobs/detail/444729")
        == "job_platform"
    )


def test_extract_location_from_description():
    location, province, remote = extract_location("工作地点：深圳市南山区，支持部分远程")
    assert location == "深圳"
    assert province == "广东省"
    assert remote is True


def test_extract_location_remote_only():
    location, province, remote = extract_location("远程办公，全国可投")
    assert remote is True
    assert location == "远程" or province == "远程"


class FakeSearch:
    def __init__(self, results):
        self.results = results
        self.queries: list[str] = []

    def search(self, query, max_results=5, include_domains=None):
        self.queries.append(query)
        return self.results


def _items() -> list[SourceItem]:
    return [
        SourceItem(
            url="https://careers.tencent.com/job/agent1",
            title="腾讯 AI Agent 实习（深圳）",
            snippet="负责 LangGraph Agent 开发，工作地点：深圳",
        ),
        SourceItem(
            url="https://www.zhipin.com/job_detail/agent2.html",
            title="AI Agent 实习生",
            snippet="北京 海淀区，RAG 与工具调用",
        ),
        SourceItem(
            url="https://blog.csdn.net/x/article/1",
            title="AI Agent 实习面经分享",
            snippet="个人博客，记录面试经历",
        ),
        SourceItem(
            url="https://career.nankai.edu.cn/correcruit/content/id/1.html",
            title="AI Agent 实习（南开就业网）",
            snippet="校园招聘信息",
        ),
    ]


def test_recommend_jobs_excludes_blogs_and_blocked_domains():
    search = FakeSearch(_items())
    results = recommend_jobs("AI Agent 应用", search_provider=search, max_results=10)
    urls = [item.url for item in results]
    assert all("blog.csdn.net" not in url for url in urls)
    assert all("career.nankai.edu.cn" not in url for url in urls)


def test_recommend_jobs_includes_blogs_when_enabled():
    search = FakeSearch(_items())
    results = recommend_jobs(
        "AI Agent 应用",
        search_provider=search,
        max_results=10,
        include_blogs=True,
    )
    assert any("blog.csdn.net" in item.url for item in results)


def test_recommend_jobs_filters_by_province_and_city():
    search = FakeSearch(_items())
    guangdong = recommend_jobs(
        "AI Agent 应用",
        search_provider=search,
        max_results=10,
        provinces=["广东省"],
    )
    assert [item.url for item in guangdong] == ["https://careers.tencent.com/job/agent1"]

    beijing = recommend_jobs(
        "AI Agent 应用",
        search_provider=search,
        max_results=10,
        cities=["北京"],
    )
    assert [item.url for item in beijing] == ["https://www.zhipin.com/job_detail/agent2.html"]


def test_official_and_platform_outrank_unknown_sources():
    search = FakeSearch(_items())
    results = recommend_jobs("AI Agent 应用", search_provider=search, max_results=10)
    assert results[0].source_type in {"official", "job_platform"}
