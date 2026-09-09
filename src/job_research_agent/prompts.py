"""提示词集中管理：改文案不碰代码。"""

from job_research_agent.schemas import JobResearchInput, ResearchPlan, SourceItem

PLANNER_SYSTEM = (
    "You are a job research planner. "
    "Always answer with valid JSON matching the required schema. "
    "Do NOT wrap the JSON inside another field."
)

REPORT_SYSTEM = (
    "You are a senior career consultant. "
    "Write a structured Chinese job research report based only on the provided evidence."
)

REFLECT_SYSTEM = (
    "You are a research quality controller. "
    "Always answer with valid JSON matching the required schema. "
    "Do NOT wrap the JSON inside another field."
)


def planner_user_prompt(user_input: JobResearchInput) -> str:
    return (
        f"目标岗位：{user_input.company}\n"
        f"JD 全文：\n{user_input.jd_text}\n"
        f"个人背景：\n{user_input.profile_text or '（未提供）'}\n\n"
        "请生成 ResearchPlan：包含调研主题、报告章节、分组搜索关键词。"
    )


def report_user_prompt(
    user_input: JobResearchInput,
    evidence_text: str,
    sources: list[SourceItem],
) -> str:
    source_lines = "\n".join(f"- {item.title}: {item.url}" for item in sources)
    return (
        f"目标岗位：{user_input.company}\n"
        f"个人背景：{user_input.profile_text or '（未提供）'}\n\n"
        f"可用资料：\n{evidence_text or '（无可用资料，请基于 JD 给出框架性建议并注明资料缺口）'}\n\n"
        f"来源列表：\n{source_lines or '（无）'}\n\n"
        "请输出中文 Markdown 报告，包含五段："
        "1) JD 要求拆解 2) 公司与团队背景 3) 面经与考核点 4) 我的匹配度差距 5) 下一步行动清单。"
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
