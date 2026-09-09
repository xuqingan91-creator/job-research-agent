"""schemas 模板行为测试。"""

import pytest
from pydantic import ValidationError

from job_research_agent.schemas import (
    JobResearchInput,
    ReflectionDecision,
    ResearchPlan,
    SourceItem,
)


def test_job_research_input_accepts_valid_data():
    item = JobResearchInput(
        company="小米 AIoT Agent 实习",
        jd_text="负责 Agent 应用开发",
        profile_text="211 电子信息，Python 基础",
    )
    assert item.company == "小米 AIoT Agent 实习"
    assert item.profile_text


def test_job_research_input_requires_company_and_jd():
    with pytest.raises(ValidationError):
        JobResearchInput(company="", jd_text="")


def test_research_plan_holds_outline_and_keyword_groups():
    plan = ResearchPlan(
        topic="AI Agent 实习调研",
        outline=["岗位要求", "公司背景"],
        keyword_groups=[["AI Agent 实习 面经"], ["小米 Agent 团队"]],
    )
    assert len(plan.outline) == 2
    assert len(plan.keyword_groups) == 2


def test_reflection_decision_defaults_to_empty_lists():
    decision = ReflectionDecision(enough=False)
    assert decision.gaps == []
    assert decision.new_keywords == []


def test_source_item_requires_url():
    with pytest.raises(ValidationError):
        SourceItem(url="")
