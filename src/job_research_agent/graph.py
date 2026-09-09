"""LangGraph 组装：线性流水线（后续加反思循环与 HITL）。"""

from collections.abc import Callable

from langgraph.graph import END, START, StateGraph

from job_research_agent.fetch import fetch_page
from job_research_agent.llm import LLMClient
from job_research_agent.nodes import (
    make_analyze_node,
    make_fetch_node,
    make_planner_node,
    make_reflect_node,
    make_report_node,
    make_search_node,
)
from job_research_agent.state import ResearchState


def build_research_graph(
    llm: LLMClient,
    search_provider,
    fetcher: Callable[[str, int], str] = fetch_page,
    *,
    max_keyword_groups: int = 3,
    keywords_per_group: int = 2,
    results_per_keyword: int = 3,
    max_pages: int = 5,
    max_chars: int = 1500,
    max_iterations: int = 2,
    token_budget: int = 20000,
) -> Callable:
    graph = StateGraph(ResearchState)
    graph.add_node("planner", make_planner_node(llm))
    graph.add_node(
        "search",
        make_search_node(
            search_provider,
            max_keyword_groups=max_keyword_groups,
            keywords_per_group=keywords_per_group,
            results_per_keyword=results_per_keyword,
        ),
    )
    graph.add_node(
        "fetch",
        make_fetch_node(fetcher, max_pages=max_pages, max_chars=max_chars),
    )
    graph.add_node("reflect", make_reflect_node(llm))
    graph.add_node("analyze", make_analyze_node())
    graph.add_node("report", make_report_node(llm))

    def route_after_reflect(state: ResearchState) -> str:
        if (
            not state.get("enough", True)
            and state.get("iteration", 0) < max_iterations
            and llm.total_tokens < token_budget
        ):
            return "search"
        return "analyze"

    graph.add_edge(START, "planner")
    graph.add_edge("planner", "search")
    graph.add_edge("search", "fetch")
    graph.add_edge("fetch", "reflect")
    graph.add_conditional_edges(
        "reflect",
        route_after_reflect,
        {"search": "search", "analyze": "analyze"},
    )
    graph.add_edge("analyze", "report")
    graph.add_edge("report", END)
    return graph.compile()
