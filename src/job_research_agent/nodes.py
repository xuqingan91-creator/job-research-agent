"""LangGraph 节点工厂：每个节点只做一件事。"""

from collections.abc import Callable

from langgraph.types import interrupt

from job_research_agent.llm import ChatResult, LLMClient
from job_research_agent.prompts import (
    PLANNER_SYSTEM,
    REFLECT_SYSTEM,
    REPORT_SYSTEM,
    planner_user_prompt,
    reflect_user_prompt,
    report_user_prompt,
)
from job_research_agent.schemas import (
    JobResearchInput,
    ReflectionDecision,
    ResearchPlan,
    SourceItem,
)
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
        items: list[SourceItem] = list(state.get("sources", []))
        seen: set[str] = {item.url for item in items}
        searched: set[str] = set(state.get("searched_keywords", []))
        for group in plan.keyword_groups[:max_keyword_groups]:
            for keyword in group[:keywords_per_group]:
                if keyword in searched:
                    continue
                searched.add(keyword)
                for item in search_provider.search(keyword, max_results=results_per_keyword):
                    if item.url and item.url not in seen:
                        seen.add(item.url)
                        items.append(item)
        return {"sources": items, "searched_keywords": sorted(searched)}

    return search_node


def make_fetch_node(
    fetcher: Fetcher,
    max_pages: int = 5,
    max_chars: int = 1500,
) -> Callable[[ResearchState], dict]:
    def fetch_node(state: ResearchState) -> dict:
        pages: list[str] = list(state.get("pages", []))
        fetched: set[str] = set(state.get("fetched_urls", []))
        for item in state.get("sources", [])[:max_pages]:
            if item.url in fetched:
                continue
            try:
                pages.append(fetcher(item.url, max_chars))
                fetched.add(item.url)
            except Exception:
                continue
        return {"pages": pages, "fetched_urls": sorted(fetched)}

    return fetch_node


def make_reflect_node(llm: LLMClient) -> Callable[[ResearchState], dict]:
    def reflect_node(state: ResearchState) -> dict:
        user_input: JobResearchInput = state["user_input"]
        plan: ResearchPlan = state["plan"]
        decision: ReflectionDecision = llm.structured(
            ReflectionDecision,
            system_prompt=REFLECT_SYSTEM,
            user_prompt=reflect_user_prompt(
                user_input,
                plan,
                state.get("sources", []),
                len(state.get("pages", [])),
                state.get("iteration", 0),
            ),
        )
        if decision.enough:
            return {
                "enough": True,
                "iteration": state.get("iteration", 0),
            }
        groups = plan.keyword_groups
        if decision.new_keywords:
            groups = groups + [decision.new_keywords]
        return {
            "enough": False,
            "iteration": state.get("iteration", 0) + 1,
            "plan": plan.model_copy(update={"keyword_groups": groups}),
        }

    return reflect_node


def make_confirm_node() -> Callable[[ResearchState], dict]:
    def confirm_node(state: ResearchState) -> dict:
        plan: ResearchPlan = state["plan"]
        reply = interrupt({"type": "plan_review", "plan": plan})
        if reply is not None:
            return {"plan": reply}
        return {}

    return confirm_node


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
