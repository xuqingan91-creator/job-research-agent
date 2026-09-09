"""HITL：Planner 出大纲后暂停，人工修改后恢复。"""

from langgraph.checkpoint.memory import InMemorySaver
from langgraph.types import Command

from job_research_agent.graph import build_research_graph
from job_research_agent.llm import ChatResult, Usage
from job_research_agent.schemas import (
    JobResearchInput,
    ReflectionDecision,
    ResearchPlan,
    SourceItem,
)


class FakeLLM:
    @property
    def total_tokens(self) -> int:
        return 0

    def structured(self, output_model, *, system_prompt, user_prompt, temperature=0.3):
        if output_model is ResearchPlan:
            return ResearchPlan(
                topic="AI Agent 实习调研",
                outline=["岗位要求", "公司背景"],
                keyword_groups=[["初始关键词"]],
            )
        if output_model is ReflectionDecision:
            return ReflectionDecision(enough=True)
        raise AssertionError(output_model)

    def chat(self, messages, *, temperature=0.3, json_mode=False):
        return ChatResult(content="# Report\n\nfinal", usage=Usage())


class QuerySearch:
    def __init__(self):
        self.calls: list[str] = []

    def search(self, query, max_results=5):
        self.calls.append(query)
        return [SourceItem(url=f"https://example.com/{query}", title="t", snippet="s")]


def _input() -> JobResearchInput:
    return JobResearchInput(company="小米", jd_text="JD", profile_text="背景")


def _fetcher(url, max_chars=1500):
    return "正文内容"


def test_hitl_pauses_then_resumes_with_modified_plan():
    llm = FakeLLM()
    search = QuerySearch()
    graph = build_research_graph(
        llm,
        search,
        fetcher=_fetcher,
        enable_hitl=True,
        checkpointer=InMemorySaver(),
    )
    config = {"configurable": {"thread_id": "thread-1"}}

    first = graph.invoke({"user_input": _input()}, config)
    interrupts = first.get("__interrupt__")
    assert interrupts, "graph should pause at plan review"
    assert interrupts[0].value["type"] == "plan_review"
    assert first["plan"].keyword_groups == [["初始关键词"]]

    modified = ResearchPlan(
        topic="AI Agent 实习调研（已修改）",
        outline=["自定义大纲"],
        keyword_groups=[["小米 IoT 自定义关键词"]],
    )
    final = graph.invoke(Command(resume=modified), config)
    assert final["plan"].keyword_groups == [["小米 IoT 自定义关键词"]]
    assert "小米 IoT 自定义关键词" in search.calls
    assert final["final_report"].startswith("# Report")
