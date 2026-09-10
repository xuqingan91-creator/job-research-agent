"""多语言报告：输入语言、提示词章节与评测标记。"""

from job_research_agent.eval_harness import score_state
from job_research_agent.prompts import report_user_prompt, section_titles
from job_research_agent.schemas import JobResearchInput


def test_default_language_is_chinese():
    item = JobResearchInput(company="小米", jd_text="JD")
    assert item.language == "zh"


def test_report_prompt_uses_english_sections():
    item = JobResearchInput(
        company="Microsoft AI Agent Intern",
        jd_text="Build agents with LangGraph",
        language="en",
    )
    prompt = report_user_prompt(item, "evidence text", [])
    assert "English" in prompt
    assert "JD Breakdown" in prompt
    assert "Action Plan" in prompt


def test_section_titles_are_language_specific():
    assert section_titles("zh")[0] == "JD 要求拆解"
    assert section_titles("en")[0] == "JD Breakdown"
    assert section_titles("ja")[0] == "JD要件の分解"


def test_eval_accepts_english_report_markers():
    report = (
        "## JD Breakdown\ntext\n## Company & Team\ntext\n"
        "## Interviews & Assessment\ntext\n## Fit Gap\ntext\n"
        "## Action Plan\ntext\n" + "body" * 300
    )
    state = {
        "user_input": JobResearchInput(
            company="Microsoft", jd_text="JD", language="en"
        ),
        "final_report": report,
        "sources": [object()],
        "pages": ["p"],
        "iteration": 1,
    }
    result = score_state(state)
    assert result.markers_missing == []
    assert result.passed is True
