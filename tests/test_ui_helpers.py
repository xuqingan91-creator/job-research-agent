"""UI 辅助逻辑与大纲生成（离线测试）。"""

from job_research_agent.llm import ChatResult, Usage
from job_research_agent.runner import generate_plan
from job_research_agent.schemas import JobPosting, JobResearchInput, ResearchPlan
from job_research_agent.ui_helpers import (
    editable_to_plan,
    format_job_markdown,
    plan_to_editable,
)


class FakeLLM:
    def structured(self, output_model, *, system_prompt, user_prompt, temperature=0.3):
        return ResearchPlan(
            topic="AI Agent 实习调研",
            outline=["岗位要求", "公司背景"],
            keyword_groups=[["AI Agent 实习", "LangGraph 实习"]],
        )


def test_generate_plan_returns_research_plan():
    plan = generate_plan(
        JobResearchInput(company="小米", jd_text="JD", profile_text="背景"),
        llm=FakeLLM(),
    )
    assert isinstance(plan, ResearchPlan)
    assert plan.topic == "AI Agent 实习调研"


def test_plan_editable_round_trip():
    plan = ResearchPlan(
        topic="主题",
        outline=["章节一", "章节二"],
        keyword_groups=[["关键词A", "关键词B"], ["关键词C"]],
    )
    outline_text, keywords_text = plan_to_editable(plan)
    restored = editable_to_plan(plan, outline_text, keywords_text)
    assert restored.outline == plan.outline
    assert restored.keyword_groups == plan.keyword_groups


def test_editable_to_plan_uses_user_edits():
    plan = ResearchPlan(topic="主题", outline=["旧"], keyword_groups=[["旧词"]])
    restored = editable_to_plan(plan, "新章节一\n新章节二", "新词A, 新词B")
    assert restored.outline == ["新章节一", "新章节二"]
    assert restored.keyword_groups == [["新词A", "新词B"]]


def test_format_job_markdown_contains_key_fields():
    job = JobPosting(
        title="AI Agent 实习",
        url="https://jobs.bytedance.com/1",
        location="北京",
        province="北京市",
        direction="AI Agent 应用",
        tech_tags=["langgraph", "rag"],
        source_type="official",
        company_tier="大厂",
        company_type="互联网",
    )
    text = format_job_markdown(job)
    assert "大厂" in text
    assert "AI Agent 实习" in text
    assert "langgraph" in text
    assert "https://jobs.bytedance.com/1" in text
