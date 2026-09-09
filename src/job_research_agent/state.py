"""LangGraph 共享状态（白板）类型定义。"""

from typing import TypedDict

from job_research_agent.schemas import JobResearchInput, ResearchPlan, SourceItem


class ResearchState(TypedDict, total=False):
    user_input: JobResearchInput
    plan: ResearchPlan
    sources: list[SourceItem]
    pages: list[str]
    evidence_text: str
    final_report: str
    iteration: int
