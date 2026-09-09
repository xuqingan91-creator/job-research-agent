"""评测器：固定基准任务 + 规则/LLM 打分 + 结果落盘。"""

from __future__ import annotations

import json
from collections.abc import Callable
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path

from job_research_agent.llm import LLMClient
from job_research_agent.prompts import JUDGE_SYSTEM, judge_user_prompt
from job_research_agent.schemas import JobResearchInput, ReportJudgeScore
from job_research_agent.state import ResearchState

REQUIRED_MARKERS = ["JD", "公司", "面经", "匹配度", "行动清单"]


@dataclass
class BenchmarkCase:
    name: str
    user_input: JobResearchInput
    min_sources: int = 1


@dataclass
class EvalResult:
    case_name: str
    rule_score: float
    judge_score: int | None
    final_score: float
    report_len: int
    sources: int
    pages: int
    iteration: int
    passed: bool
    markers_found: list[str]
    markers_missing: list[str]


def score_state(
    state: ResearchState,
    min_sources: int = 1,
    judge_score: int | None = None,
) -> EvalResult:
    report = state.get("final_report", "")
    sources = len(state.get("sources", []))
    pages = len(state.get("pages", []))
    found = [marker for marker in REQUIRED_MARKERS if marker in report]
    missing = [marker for marker in REQUIRED_MARKERS if marker not in report]

    section_part = len(found) / len(REQUIRED_MARKERS) * 70.0
    source_part = 15.0 if sources >= min_sources else 0.0
    length_part = 15.0 if len(report) >= 800 else 0.0
    rule_score = round(section_part + source_part + length_part, 1)

    if judge_score is not None:
        final_score = round(rule_score * 0.7 + judge_score * 20 * 0.3, 1)
    else:
        final_score = rule_score

    return EvalResult(
        case_name=state["user_input"].company,
        rule_score=rule_score,
        judge_score=judge_score,
        final_score=final_score,
        report_len=len(report),
        sources=sources,
        pages=pages,
        iteration=state.get("iteration", 0),
        passed=final_score >= 60.0,
        markers_found=found,
        markers_missing=missing,
    )


def run_benchmark(
    make_graph: Callable[[], object],
    cases: list[BenchmarkCase],
    judge: LLMClient | None = None,
    output_dir: Path = Path("outputs/eval"),
) -> dict:
    results: list[dict] = []
    for case in cases:
        graph = make_graph()
        state: ResearchState = graph.invoke({"user_input": case.user_input})
        judge_score: int | None = None
        if judge is not None:
            score: ReportJudgeScore = judge.structured(
                ReportJudgeScore,
                system_prompt=JUDGE_SYSTEM,
                user_prompt=judge_user_prompt(
                    case.user_input.company,
                    state.get("final_report", ""),
                    len(state.get("sources", [])),
                ),
            )
            judge_score = score.quality_score
        result = score_state(state, case.min_sources, judge_score)
        results.append(asdict(result))

    rule_scores = [item["rule_score"] for item in results]
    final_scores = [item["final_score"] for item in results]
    payload = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "case_count": len(results),
        "avg_rule_score": round(sum(rule_scores) / len(rule_scores), 1),
        "avg_final_score": round(sum(final_scores) / len(final_scores), 1),
        "passed_count": sum(1 for item in results if item["passed"]),
        "results": results,
    }
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / f"eval-{datetime.now():%Y%m%d-%H%M%S}.json"
    output_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return payload
