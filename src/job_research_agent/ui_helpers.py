"""Streamlit 界面用的纯函数（便于离线测试）。"""

from job_research_agent.schemas import JobPosting, ResearchPlan


def plan_to_editable(plan: ResearchPlan) -> tuple[str, str]:
    outline_text = "\n".join(plan.outline)
    keywords_text = "\n".join(", ".join(group) for group in plan.keyword_groups)
    return outline_text, keywords_text


def editable_to_plan(
    plan: ResearchPlan,
    outline_text: str,
    keywords_text: str,
) -> ResearchPlan:
    outline = [line.strip() for line in outline_text.splitlines() if line.strip()]
    groups = []
    for line in keywords_text.splitlines():
        keywords = [item.strip() for item in line.split(",") if item.strip()]
        if keywords:
            groups.append(keywords)
    return plan.model_copy(
        update={
            "outline": outline or plan.outline,
            "keyword_groups": groups or plan.keyword_groups,
        }
    )


def format_job_markdown(job: JobPosting) -> str:
    tags = ", ".join(job.tech_tags) or "暂无标签"
    location = job.location or job.province or "地点未知"
    tier = job.company_tier or "其他"
    company_type = job.company_type or "其他"
    return (
        f"**[{tier}·{company_type}] {job.title}**\n\n"
        f"- 地点：{location}{'（可远程）' if job.remote else ''}\n"
        f"- 方向：{job.direction or '未分类'}｜技术：{tags}\n"
        f"- 来源：{job.source_type}｜[岗位链接]({job.url})"
    )
