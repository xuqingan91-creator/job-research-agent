"""LangGraph 线性流水线测试（全离线）。"""

from job_research_agent.fetch import FetchError
from job_research_agent.graph import build_research_graph
from job_research_agent.llm import ChatResult, Usage
from job_research_agent.schemas import (
    JobResearchInput,
    ReflectionDecision,
    ResearchPlan,
    SourceItem,
)


class FakeLLM:
    def __init__(self, not_enough_until: int = 0):
        self.structured_calls = 0
        self.chat_calls = 0
        self.reflect_calls = 0
        self.not_enough_until = not_enough_until

    @property
    def total_tokens(self) -> int:
        return 0

    def structured(self, output_model, *, system_prompt, user_prompt, temperature=0.3):
        self.structured_calls += 1
        if output_model is ResearchPlan:
            return ResearchPlan(
                topic="AI Agent 实习调研",
                outline=["岗位要求", "公司背景"],
                keyword_groups=[["AI Agent 实习 面经"]],
            )
        if output_model is ReflectionDecision:
            self.reflect_calls += 1
            if self.reflect_calls < self.not_enough_until:
                return ReflectionDecision(
                    enough=False,
                    gaps=["缺少公司背景资料"],
                    new_keywords=["小米 IoT Agent 团队"],
                )
            return ReflectionDecision(enough=True)
        raise AssertionError(f"unexpected output_model: {output_model}")

    def chat(self, messages, *, temperature=0.3, json_mode=False):
        self.chat_calls += 1
        return ChatResult(content="# Job Research Report\n\n这是测试报告正文。", usage=Usage())


class FakeSearch:
    def search(self, query, max_results=5):
        return [SourceItem(url="https://example.com/a", title="来源 A", snippet="摘要")]


class QuerySearch:
    def __init__(self):
        self.calls: list[str] = []

    def search(self, query, max_results=5):
        self.calls.append(query)
        index = len(self.calls)
        return [
            SourceItem(
                url=f"https://example.com/page/{index}",
                title=f"来源 {index}",
                snippet=query,
            )
        ]


def _input() -> JobResearchInput:
    return JobResearchInput(
        company="小米 AIoT Agent 实习",
        jd_text="负责 Agent 应用开发",
        profile_text="211 电子信息，Python 基础",
    )


def _fetcher(url, max_chars=1500):
    return "这是抓取到的正文内容，用于生成报告。"


def test_linear_graph_produces_report():
    llm = FakeLLM()
    graph = build_research_graph(llm, FakeSearch(), fetcher=_fetcher)
    result = graph.invoke({"user_input": _input()})
    assert result["plan"].topic == "AI Agent 实习调研"
    assert len(result["sources"]) == 1
    assert result["evidence_text"].startswith("这是抓取到")
    assert result["final_report"].startswith("# Job Research Report")
    assert llm.structured_calls == 2  # planner + reflect
    assert llm.reflect_calls == 1
    assert llm.chat_calls == 1


def test_linear_graph_degrades_when_all_fetch_fail():
    def failing_fetcher(url, max_chars=1500):
        raise FetchError("blocked")

    llm = FakeLLM()
    graph = build_research_graph(llm, FakeSearch(), fetcher=failing_fetcher)
    result = graph.invoke({"user_input": _input()})
    assert result["pages"] == []
    assert result["evidence_text"] == ""
    assert result["final_report"].startswith("# Job Research Report")


def test_reflect_loop_searches_again_when_not_enough():
    llm = FakeLLM(not_enough_until=2)
    search = QuerySearch()
    graph = build_research_graph(
        llm,
        search,
        fetcher=_fetcher,
        max_iterations=3,
    )
    result = graph.invoke({"user_input": _input()})
    assert len(search.calls) == 2
    assert len(result["sources"]) == 2
    assert len(result["pages"]) == 2
    assert result["final_report"].startswith("# Job Research Report")


def test_max_iterations_guardrail_stops_loop():
    llm = FakeLLM(not_enough_until=99)
    search = QuerySearch()
    graph = build_research_graph(
        llm,
        search,
        fetcher=_fetcher,
        max_iterations=1,
    )
    result = graph.invoke({"user_input": _input()})
    assert len(search.calls) == 1
    assert result["iteration"] == 1
    assert result["enough"] is False
    assert result["final_report"].startswith("# Job Research Report")
