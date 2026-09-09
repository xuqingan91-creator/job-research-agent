"""runner：非交互式调研入口（供 CLI 使用）。"""

from job_research_agent.llm import ChatResult, Usage
from job_research_agent.runner import run_research
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
                topic="调研主题",
                outline=["岗位要求"],
                keyword_groups=[["初始关键词"]],
            )
        if output_model is ReflectionDecision:
            return ReflectionDecision(enough=True)
        raise AssertionError(output_model)

    def chat(self, messages, *, temperature=0.3, json_mode=False):
        return ChatResult(content="# Report\n\nok", usage=Usage())


class FakeSearch:
    def search(self, query, max_results=5):
        return [SourceItem(url="https://example.com/a", title="A", snippet="s")]


def _fetcher(url, max_chars=1500):
    return "正文"


def test_runner_with_confirm_callback_returns_final_state():
    def confirm(plan: ResearchPlan) -> ResearchPlan:
        return plan.model_copy(
            update={"keyword_groups": [["修改后的关键词"]]}
        )

    state = run_research(
        JobResearchInput(company="小米", jd_text="JD", profile_text="背景"),
        llm=FakeLLM(),
        search_provider=FakeSearch(),
        fetcher=_fetcher,
        confirm_plan=confirm,
    )
    assert state["plan"].keyword_groups == [["修改后的关键词"]]
    assert state["final_report"].startswith("# Report")
