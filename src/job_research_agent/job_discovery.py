"""岗位发现：多主体分类 + 条件筛选 + 主题推荐。"""

from __future__ import annotations

from job_research_agent.schemas import JobPosting, JobSearchTheme, SourceItem

DIRECTION_RULES: list[tuple[str, list[str]]] = [
    ("AI Agent 应用", ["ai agent", "agent 开发", "智能体", "langgraph", "agent"]),
    ("RAG/检索", ["rag", "检索增强", "向量检索", "知识库"]),
    ("大模型应用", ["大模型应用", "llm", "提示词", "prompt"]),
    ("智能硬件/AIoT", ["aiot", "物联网", "iot", "嵌入式", "端侧"]),
    ("算法/模型", ["pytorch", "微调", "算法", "模型训练", "nlp"]),
    ("后端/平台", ["后端", "java", "微服务", "backend", "fastapi"]),
]

TECH_RULES: dict[str, list[str]] = {
    "langgraph": ["langgraph"],
    "langchain": ["langchain"],
    "rag": ["rag", "检索增强", "向量检索"],
    "agent": ["agent", "智能体"],
    "mcp": ["mcp"],
    "llm": ["大模型", "llm"],
    "prompt": ["prompt", "提示词"],
    "python": ["python"],
    "fastapi": ["fastapi"],
    "pytorch": ["pytorch", "torch"],
    "embedding": ["embedding", "向量"],
    "aiot": ["aiot", "物联网", "iot"],
}

DEFAULT_THEMES: list[JobSearchTheme] = [
    JobSearchTheme(
        name="AI Agent 应用",
        keywords=["AI Agent 实习", "LangGraph 实习", "Agent 开发 实习"],
        directions=["AI Agent 应用"],
        tech_tags=["langgraph", "agent", "mcp"],
    ),
    JobSearchTheme(
        name="RAG/检索",
        keywords=["RAG 实习", "检索增强 实习", "知识库 问答 实习"],
        directions=["RAG/检索"],
        tech_tags=["rag", "embedding"],
    ),
    JobSearchTheme(
        name="大模型应用",
        keywords=["大模型应用 实习", "LLM 应用开发 实习", "提示词工程 实习"],
        directions=["大模型应用"],
        tech_tags=["llm", "prompt", "python"],
    ),
    JobSearchTheme(
        name="智能硬件/AIoT",
        keywords=["AIoT Agent 实习", "智能硬件 大模型 实习", "端侧 AI 实习"],
        directions=["智能硬件/AIoT"],
        tech_tags=["aiot", "embedding"],
    ),
    JobSearchTheme(
        name="算法/模型",
        keywords=["大模型算法 实习", "NLP 算法 实习", "模型微调 实习"],
        directions=["算法/模型"],
        tech_tags=["pytorch", "llm"],
    ),
]


def theme_by_name(name: str) -> JobSearchTheme:
    for theme in DEFAULT_THEMES:
        if theme.name == name:
            return theme
    raise KeyError(f"unknown theme: {name}")


def _text(posting: JobPosting) -> str:
    return f"{posting.title} {posting.description}".lower()


def classify_posting(posting: JobPosting) -> JobPosting:
    text = _text(posting)
    direction = posting.direction
    if not direction:
        best_name = ""
        best_score = 0
        for name, patterns in DIRECTION_RULES:
            score = 0
            for pattern in patterns:
                if pattern in posting.title.lower():
                    score += 3
                elif pattern in text:
                    score += 1
            if score > best_score:
                best_name = name
                best_score = score
        direction = best_name or "其他"

    tags = list(posting.tech_tags)
    for tag, patterns in TECH_RULES.items():
        if tag in tags:
            continue
        if any(pattern in text for pattern in patterns):
            tags.append(tag)
    return posting.model_copy(update={"direction": direction, "tech_tags": tags})


def filter_postings(
    postings: list[JobPosting],
    theme: JobSearchTheme,
) -> list[JobPosting]:
    result: list[JobPosting] = []
    for posting in postings:
        if theme.directions and posting.direction not in theme.directions:
            if not (theme.tech_tags and set(theme.tech_tags) & set(posting.tech_tags)):
                continue
        if theme.locations and posting.location and posting.location not in theme.locations:
            continue
        result.append(posting)
    return result


def score_posting(posting: JobPosting, theme: JobSearchTheme) -> float:
    text = _text(posting)
    score = 0.0
    for keyword in theme.keywords:
        for token in keyword.lower().split():
            if token in text:
                score += 1.0
    for tag in theme.tech_tags:
        if tag in posting.tech_tags:
            score += 2.0
    if posting.direction in theme.directions:
        score += 3.0
    return score


def recommend_jobs(
    theme_name: str,
    *,
    search_provider,
    max_results: int = 10,
    results_per_keyword: int = 5,
) -> list[JobPosting]:
    theme = theme_by_name(theme_name)
    seen: set[str] = set()
    candidates: list[JobPosting] = []
    for keyword in theme.keywords:
        for item in search_provider.search(keyword, max_results=results_per_keyword):
            if not item.url or item.url in seen:
                continue
            seen.add(item.url)
            candidates.append(
                JobPosting(
                    title=item.title or item.snippet[:40] or item.url,
                    url=item.url,
                    description=item.snippet,
                    source="web",
                )
            )
    classified = [classify_posting(item) for item in candidates]
    filtered = filter_postings(classified, theme)
    ranked = sorted(filtered, key=lambda item: score_posting(item, theme), reverse=True)
    return ranked[:max_results]
