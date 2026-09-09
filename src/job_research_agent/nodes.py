"""LangGraph 节点工厂：每个节点只做一件事。"""

from collections.abc import Callable

from job_research_agent.llm import ChatResult, LLMClient
from job_research_agent.prompts import PLANNER_SYSTEM, REPORT_SYSTEM, planner_user_prompt, report_user_prompt
from job_research_agent.schemas import JobResearchInput, ResearchPlan, SourceItem
from job_research_agent.state import ResearchState

Fetcher = Callable[[str, int], str]


def make_planner_node(llm: LLMClient) -> Callable[[ResearchState], dict]:
    def planner_node(state: ResearchState) -> dict:
        user_input = state["user_input"]
        plan = llm.structured(
            ResearchPlan,
            system_prompt=PLANNER_SYSTEM,
            user_prompt=planner_user_prompt(user_input),
        )
        return {"plan": plan, "iteration": 0}

    return planner_node


def make_search_node(
    search_provider,
    max_keyword_groups: int = 3,
    keywords_per_group: int = 2,
    results_per_keyword: int = 3,
) -> Callable[[ResearchState], dict]:
    def search_node(state: ResearchState) -> dict:
        plan = state["plan"]
        items: list[SourceItem] = []
        seen: set[str] = set()
        for group in plan.keyword_groups[:max_keyword_groups]:
            for keyword in group[:keywords_per_group]:
                for item in search_provider.search(keyword, max_results=results_per_keyword):
                    if item.url and item.url not in seen:
                        seen.add(item.url)
                        items.append(item)
        return {"sources": items}

    return search_node


def make_fetch_node(
    fetcher: Fetcher,
    max_pages: int = 5,
    max_chars: int = 1500,
) -> Callable[[ResearchState], dict]:
    def fetch_node(state: ResearchState) -> dict:
        pages: list[str] = []
        for item in state.get("sources", [])[:max_pages]:
            try:
                pages.append(fetcher(item.url, max_chars))
            except Exception:
                continue
        return {"pages": pages}

    return fetch_node


def make_analyze_node(max_evidence_chars: int = 8000) -> Callable[[ResearchState], dict]:
    def analyze_node(state: ResearchState) -> dict:
        evidence = "\n\n---\n\n".join(state.get("pages", []))
        return {"evidence_text": evidence[:max_evidence_chars]}

    return analyze_node


def make_report_node(llm: LLMClient) -> Callable[[ResearchState], dict]:
    def report_node(state: ResearchState) -> dict:
        user_input: JobResearchInput = state["user_input"]
        result: ChatResult = llm.chat(
            [
                {"role": "system", "content": REPORT_SYSTEM},
                {
                    "role": "user",
                    "content": report_user_prompt(
                        user_input,
                        state.get("evidence_text", ""),
                        state.get("sources", []),
                    ),
                },
            ]
        )
        return {"final_report": result.content}

    return report_node
