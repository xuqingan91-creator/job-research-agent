"""评测器测试（离线 Fake，不联网）。"""

from job_research_agent.eval_harness import (
    REQUIRED_MARKERS,
    BenchmarkCase,
    run_benchmark,
    score_state,
)
from job_research_agent.schemas import JobResearchInput, ReportJudgeScore


def _state(report: str = "", sources: int = 0, pages: int = 0) -> dict:
    return {
        "user_input": JobResearchInput(
            company="小米 AIoT Agent 实习",
            jd_text="JD",
            profile_text="背景",
        ),
        "final_report": report,
        "sources": [object() for _ in range(sources)],
        "pages": ["p"] * pages,
        "iteration": 1,
    }


def _good_report() -> str:
    return (
        "# 报告\n## JD 要求拆解\n内容\n## 公司与团队背景\n内容\n"
        "## 面经与考核点\n内容\n## 我的匹配度差距\n内容\n## 行动清单\n内容\n"
        + "正文" * 500
    )


def test_score_state_high_score_for_complete_report():
    result = score_state(_state(report=_good_report(), sources=3, pages=2))
    assert result.passed is True
    assert result.rule_score >= 80
    assert result.markers_missing == []


def test_score_state_low_score_for_empty_report():
    result = score_state(_state(report="nothing", sources=0, pages=0))
    assert result.passed is False
    assert result.markers_missing == REQUIRED_MARKERS


class FakeJudge:
    def structured(self, output_model, *, system_prompt, user_prompt, temperature=0.3):
        return ReportJudgeScore(quality_score=4, summary="ok")


class FakeGraph:
    def invoke(self, state_input):
        return _state(report=_good_report(), sources=2, pages=1)


def test_run_benchmark_saves_payload(tmp_path):
    case = BenchmarkCase(
        name="case1",
        user_input=JobResearchInput(company="小米", jd_text="JD", profile_text=""),
    )
    payload = run_benchmark(
        lambda: FakeGraph(),
        [case],
        judge=FakeJudge(),
        output_dir=tmp_path,
    )
    assert payload["case_count"] == 1
    assert payload["passed_count"] == 1
    assert payload["avg_final_score"] >= 60
    assert len(list(tmp_path.glob("eval-*.json"))) == 1
