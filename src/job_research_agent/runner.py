"""非交互式调研入口：供 CLI / 评测 / 脚本共用。"""

from __future__ import annotations

import re
from collections.abc import Callable
from datetime import datetime
from pathlib import Path

from langgraph.checkpoint.memory import InMemorySaver
from langgraph.types import Command

from job_research_agent.fetch import fetch_page
from job_research_agent.graph import build_research_graph
from job_research_agent.llm import LLMClient
from job_research_agent.schemas import JobResearchInput, ResearchPlan
from job_research_agent.state import ResearchState


class PlanReviewRequired(Exception):
    """enable_hitl 且未提供 confirm_plan 时抛出，提示调用方进入人工确认。"""

    def __init__(self, plan: ResearchPlan) -> None:
        self.plan = plan
        super().__init__("plan requires human review")


def run_research(
    user_input: JobResearchInput,
    *,
    llm: LLMClient,
    search_provider,
    fetcher: Callable[[str, int], str] = fetch_page,
    confirm_plan: Callable[[ResearchPlan], ResearchPlan] | None = None,
    enable_hitl: bool = True,
    checkpointer=None,
    thread_id: str = "main",
    max_iterations: int = 2,
    token_budget: int = 20000,
    max_keyword_groups: int = 3,
    keywords_per_group: int = 2,
    results_per_keyword: int = 3,
    max_pages: int = 5,
    max_chars: int = 1500,
) -> ResearchState:
    graph = build_research_graph(
        llm,
        search_provider,
        fetcher=fetcher,
        max_iterations=max_iterations,
        token_budget=token_budget,
        max_keyword_groups=max_keyword_groups,
        keywords_per_group=keywords_per_group,
        results_per_keyword=results_per_keyword,
        max_pages=max_pages,
        max_chars=max_chars,
        enable_hitl=enable_hitl,
        checkpointer=checkpointer or (InMemorySaver() if enable_hitl else None),
    )
    config = {"configurable": {"thread_id": thread_id}}
    first = graph.invoke({"user_input": user_input}, config)
    if enable_hitl and first.get("__interrupt__"):
        plan = first["__interrupt__"][0].value["plan"]
        if confirm_plan is None:
            raise PlanReviewRequired(plan)
        return graph.invoke(Command(resume=confirm_plan(plan)), config)
    return first


def save_report(
    state: ResearchState,
    output_dir: Path = Path("outputs/reports"),
) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    raw_company = state["user_input"].company
    slug = re.sub(r"[^\w\u4e00-\u9fff-]+", "-", raw_company).strip("-") or "report"
    path = output_dir / f"{datetime.now():%Y%m%d-%H%M%S}-{slug}.md"
    path.write_text(state.get("final_report", ""), encoding="utf-8")
    return path
