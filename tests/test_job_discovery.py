"""岗位发现：多主体分类、条件筛选与主题推荐。"""

from job_research_agent.job_discovery import (
    classify_posting,
    filter_postings,
    recommend_jobs,
    theme_by_name,
)
from job_research_agent.schemas import JobPosting, SourceItem


def _posting(title: str, description: str = "", url: str = "https://x/1") -> JobPosting:
    return JobPosting(title=title, url=url, description=description)


def test_classify_posting_fills_direction_and_tech_tags():
    posting = _posting(
        "AI Agent 应用开发实习",
        "使用 LangGraph 与 RAG 构建 Agent，熟悉 MCP 优先",
    )
    result = classify_posting(posting)
    assert result.direction == "AI Agent 应用"
    assert "langgraph" in result.tech_tags
    assert "rag" in result.tech_tags
    assert "mcp" in result.tech_tags


def test_classify_posting_keeps_existing_direction_and_merges_tags():
    posting = _posting("大模型应用实习", "提示词工程与评测")
    posting.direction = "人工标注方向"
    posting.tech_tags = ["python"]
    result = classify_posting(posting)
    assert result.direction == "人工标注方向"
    assert "prompt" in result.tech_tags
    assert "python" in result.tech_tags


def test_filter_postings_by_theme_conditions():
    theme = theme_by_name("RAG/检索")
    keep = _posting("RAG 检索增强实习", "向量检索与重排")
    keep.direction = "RAG/检索"
    keep.tech_tags = ["rag"]
    drop = _posting("后端开发实习", "Java 微服务")
    drop.direction = "后端/平台"
    drop.tech_tags = ["java"]
    result = filter_postings([keep, drop], theme)
    assert [item.title for item in result] == ["RAG 检索增强实习"]


class FakeSearch:
    def __init__(self, results):
        self.results = results
        self.queries: list[str] = []

    def search(self, query, max_results=5):
        self.queries.append(query)
        return self.results


def test_recommend_jobs_searches_classifies_filters_and_ranks():
    strong = SourceItem(
        url="https://x/agent",
        title="AI Agent 应用开发实习（LangGraph/RAG）",
        snippet="负责 Agent 工具调用与 RAG 检索，熟悉 MCP 优先",
    )
    weak = SourceItem(
        url="https://x/backend",
        title="后端开发实习",
        snippet="Java 微服务与数据库",
    )
    search = FakeSearch([strong, weak])
    results = recommend_jobs("AI Agent 应用", search_provider=search, max_results=5)
    assert search.queries, "should search with theme keywords"
    assert len(results) >= 1
    assert results[0].url == "https://x/agent"
    assert results[0].direction == "AI Agent 应用"
    assert all(item.url != "https://x/backend" for item in results)


def test_recommend_jobs_deduplicates_by_url():
    same = SourceItem(url="https://x/dup", title="AI Agent 实习", snippet="agent langgraph")
    search = FakeSearch([same, same])
    results = recommend_jobs("AI Agent 应用", search_provider=search, max_results=5)
    assert len([item for item in results if item.url == "https://x/dup"]) == 1
