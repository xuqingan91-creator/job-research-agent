"""提示词集中管理：改文案不碰代码。"""

from job_research_agent.schemas import (
    JobResearchInput,
    ParsedResume,
    ResearchPlan,
    SourceItem,
)

PLANNER_SYSTEM = (
    "You are a job research planner. "
    "Always answer with valid JSON matching the required schema. "
    "Do NOT wrap the JSON inside another field."
)

REPORT_SYSTEM = (
    "You are a senior career consultant. "
    "Write a structured Chinese job research report based only on the provided evidence."
)

SECTION_TITLES: dict[str, list[str]] = {
    "zh": ["JD 要求拆解", "公司与团队背景", "面经与考核点", "匹配度差距", "行动清单"],
    "en": [
        "JD Breakdown",
        "Company & Team",
        "Interviews & Assessment",
        "Fit Gap",
        "Action Plan",
    ],
}

LANGUAGE_NAMES = {
    "zh": "Chinese (简体中文)",
    "en": "English",
}


def section_titles(language: str) -> list[str]:
    return SECTION_TITLES.get(language, SECTION_TITLES["zh"])


def language_name(language: str) -> str:
    return LANGUAGE_NAMES.get(language, LANGUAGE_NAMES["zh"])

REFLECT_SYSTEM = (
    "You are a research quality controller. "
    "Always answer with valid JSON matching the required schema. "
    "Do NOT wrap the JSON inside another field."
)

JUDGE_SYSTEM = (
    "You are a strict report quality judge. "
    "Always answer with valid JSON matching the required schema. "
    "Do NOT wrap the JSON inside another field."
)

POLISH_SYSTEM = (
    "You are a senior resume consultant for tech internships. "
    "Rewrite and reorganize the resume to match the target JD, "
    "but NEVER fabricate experience, projects, or metrics. "
    "Only rephrase, reorder, and highlight existing content. "
    "Always answer with valid JSON matching ResumePolishResult. "
    "Do NOT wrap the JSON inside another field."
)


def planner_user_prompt(user_input: JobResearchInput) -> str:
    return (
        f"目标岗位：{user_input.company}\n"
        f"JD 全文：\n{user_input.jd_text}\n"
        f"个人背景：\n{user_input.profile_text or '（未提供）'}\n\n"
        f"请用 {language_name(user_input.language)} 生成 ResearchPlan："
        "包含调研主题、报告章节、分组搜索关键词。"
    )


def report_user_prompt(
    user_input: JobResearchInput,
    evidence_text: str,
    sources: list[SourceItem],
) -> str:
    source_lines = "\n".join(f"- {item.title}: {item.url}" for item in sources)
    titles = section_titles(user_input.language)
    section_text = " / ".join(
        f"{index}) {title}" for index, title in enumerate(titles, start=1)
    )
    return (
        f"目标岗位：{user_input.company}\n"
        f"个人背景：{user_input.profile_text or '（未提供）'}\n\n"
        f"可用资料：\n{evidence_text or '（无可用资料，请基于 JD 给出框架性建议并注明资料缺口）'}\n\n"
        f"来源列表：\n{source_lines or '（无）'}\n\n"
        f"请用 {language_name(user_input.language)} 输出 Markdown 报告，"
        f"五个章节标题必须使用以下原文：{section_text}。"
    )


def reflect_user_prompt(
    user_input: JobResearchInput,
    plan: ResearchPlan,
    sources: list[SourceItem],
    page_count: int,
    iteration: int,
) -> str:
    source_lines = "\n".join(f"- {item.title}: {item.url}" for item in sources)
    return (
        f"目标岗位：{user_input.company}\n"
        f"报告大纲：{plan.outline}\n"
        f"已收集来源：\n{source_lines or '（无）'}\n"
        f"已抓取正文页数：{page_count}\n"
        f"当前迭代轮次：{iteration}\n\n"
        "请判断资料是否足以撰写五段式求职报告。"
        "若不足，说明缺口并给出补充搜索关键词（ReflectionDecision JSON）。"
    )


def judge_user_prompt(
    company: str,
    report: str,
    source_count: int,
) -> str:
    return (
        f"目标岗位：{company}\n"
        f"来源数量：{source_count}\n"
        f"报告内容：\n{report[:6000]}\n\n"
        "请从结构完整度、内容可执行性、来源支撑三个维度打分（1-5），并给一句话评语。"
    )


def resume_polish_user_prompt(parsed: ParsedResume, jd_text: str) -> str:
    section_lines = "\n\n".join(
        f"【{section.title}】\n{section.content}" for section in parsed.sections
    )
    return (
        f"目标岗位 JD：\n{jd_text}\n\n"
        f"候选人简历（分板块）：\n{section_lines or parsed.raw_text}\n\n"
        "请输出 ResumePolishResult：\n"
        "1) summary：总体匹配度评价；\n"
        "2) sections：逐板块给出 original / polished / keywords_added；\n"
        "3) suggestions：需要补充或量化的地方；\n"
        "4) matched_keywords：JD 中已匹配的关键词。\n"
        "要求：只重组与改写已有内容，不得编造经历或数据。"
    )
