"""搜索统一接口：先实现 Tavily，未来可平替其他引擎。"""

from __future__ import annotations

from typing import Any

from job_research_agent import config
from job_research_agent.schemas import SourceItem


class SearchProvider:
    """所有搜索引擎的统一接口。"""

    def search(self, query: str, max_results: int = 5) -> list[SourceItem]:
        raise NotImplementedError


class TavilySearchProvider(SearchProvider):
    """Tavily 实现；client 可注入 Fake，便于离线测试。"""

    def __init__(self, client: Any | None = None) -> None:
        self._client = client

    def _get_client(self) -> Any:
        if self._client is None:
            from tavily import TavilyClient

            self._client = TavilyClient(api_key=config.TAVILY_API_KEY)
        return self._client

    def search(self, query: str, max_results: int = 5) -> list[SourceItem]:
        response = self._get_client().search(query, max_results=max_results)
        items: list[SourceItem] = []
        for raw in response.get("results", []):
            items.append(
                SourceItem(
                    url=raw.get("url", ""),
                    title=raw.get("title", ""),
                    snippet=raw.get("content", ""),
                )
            )
        return items
