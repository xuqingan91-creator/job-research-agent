"""search 接口与 Tavily 实现的测试（Fake client，不联网）。"""

from job_research_agent.schemas import SourceItem
from job_research_agent.search import SearchProvider, TavilySearchProvider


class FakeTavilyClient:
    def __init__(self, results):
        self.results = results
        self.last_query = None
        self.last_max = None

    def search(self, query, max_results=5):
        self.last_query = query
        self.last_max = max_results
        return {"results": self.results}


def test_provider_search_returns_source_items():
    fake = FakeTavilyClient(
        [
            {"title": "面经 A", "url": "https://a.example.com/1", "content": "摘要 A"},
            {"title": "面经 B", "url": "https://b.example.com/2", "content": "摘要 B"},
        ]
    )
    provider = TavilySearchProvider(client=fake)
    items = provider.search("AI Agent 实习 面经", max_results=2)
    assert len(items) == 2
    assert isinstance(items[0], SourceItem)
    assert items[0].url == "https://a.example.com/1"
    assert fake.last_query == "AI Agent 实习 面经"
    assert fake.last_max == 2


def test_provider_search_handles_empty_results():
    provider = TavilySearchProvider(client=FakeTavilyClient([]))
    assert provider.search("nothing", max_results=5) == []
