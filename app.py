"""Streamlit Web 界面：岗位推荐 + JD 调研。"""

import streamlit as st

from job_research_agent.job_discovery import DEFAULT_THEMES, recommend_jobs
from job_research_agent.llm import LLMClient
from job_research_agent.runner import generate_plan, run_research, save_report
from job_research_agent.schemas import JobResearchInput
from job_research_agent.search import TavilySearchProvider
from job_research_agent.ui_helpers import (
    editable_to_plan,
    format_job_markdown,
    plan_to_editable,
)

PROVINCES = [
    "北京市",
    "上海市",
    "广东省",
    "浙江省",
    "江苏省",
    "四川省",
    "湖北省",
    "陕西省",
    "天津市",
    "重庆市",
    "安徽省",
    "湖南省",
    "山东省",
    "福建省",
    "辽宁省",
]

CITIES = [
    "北京",
    "上海",
    "深圳",
    "广州",
    "杭州",
    "南京",
    "苏州",
    "成都",
    "武汉",
    "西安",
    "天津",
    "重庆",
    "合肥",
    "长沙",
    "青岛",
    "济南",
    "厦门",
    "福州",
    "大连",
    "沈阳",
]

st.set_page_config(page_title="Job Research Agent", layout="wide")
st.title("Job Research Agent")
st.caption("岗位推荐（中大厂优先）· JD 深度调研 · 人机确认大纲 · 评测体系")

tab_jobs, tab_research = st.tabs(["岗位推荐", "JD 调研"])

with tab_jobs:
    theme = st.selectbox("主题方向", [item.name for item in DEFAULT_THEMES])
    col_left, col_right = st.columns(2)
    provinces = col_left.multiselect("省份筛选", PROVINCES)
    cities = col_right.multiselect("城市筛选", CITIES)
    col_tier, col_flags = st.columns([2, 1])
    tiers = col_tier.multiselect(
        "公司分层",
        ["大厂", "中厂", "其他"],
        default=["大厂", "中厂"],
    )
    allow_remote = col_flags.checkbox("包含远程岗位", value=True)
    max_results = st.slider("最多返回条数", min_value=5, max_value=30, value=20)

    if st.button("开始搜索岗位", type="primary"):
        with st.spinner("正在多源检索、分类与筛选..."):
            try:
                st.session_state["jobs"] = recommend_jobs(
                    theme,
                    search_provider=TavilySearchProvider(),
                    max_results=max_results,
                    provinces=provinces or None,
                    cities=cities or None,
                    company_tiers=tiers or None,
                    allow_remote=allow_remote,
                )
            except Exception as exc:  # noqa: BLE001 - UI 层展示错误
                st.error(f"检索失败：{exc}")

    jobs = st.session_state.get("jobs", [])
    st.caption(f"共 {len(jobs)} 条结果（12 轮搜索预算，官网 / 招聘平台优先，博客与帖子已过滤）")
    for job in jobs:
        st.markdown(format_job_markdown(job))
        st.divider()

with tab_research:
    company = st.text_input("目标公司/岗位", placeholder="例：字节跳动 AI Agent 实习")
    jd_text = st.text_area("JD 全文", height=200)
    profile_text = st.text_area("个人背景", height=100)

    if st.button("生成调研大纲"):
        if not company or not jd_text:
            st.warning("请先填写公司/岗位和 JD 全文。")
        else:
            with st.spinner("正在生成大纲..."):
                try:
                    st.session_state["plan"] = generate_plan(
                        JobResearchInput(
                            company=company,
                            jd_text=jd_text,
                            profile_text=profile_text,
                        ),
                        llm=LLMClient(),
                    )
                except Exception as exc:  # noqa: BLE001
                    st.error(f"生成失败：{exc}")

    plan = st.session_state.get("plan")
    if plan:
        outline_text, keywords_text = plan_to_editable(plan)
        outline_edit = st.text_area("调研大纲（每行一章，可修改）", value=outline_text, height=150)
        keywords_edit = st.text_area(
            "搜索关键词（每行一组，逗号分隔，可修改）",
            value=keywords_text,
            height=100,
        )
        if st.button("开始调研", type="primary"):
            edited_plan = editable_to_plan(plan, outline_edit, keywords_edit)
            with st.spinner("多轮检索与报告生成中，请稍候..."):
                try:
                    state = run_research(
                        JobResearchInput(
                            company=company,
                            jd_text=jd_text,
                            profile_text=profile_text,
                        ),
                        llm=LLMClient(),
                        search_provider=TavilySearchProvider(),
                        confirm_plan=lambda _: edited_plan,
                        thread_id="streamlit",
                    )
                    st.session_state["report_state"] = state
                    st.session_state["report_path"] = str(save_report(state))
                except Exception as exc:  # noqa: BLE001
                    st.error(f"调研失败：{exc}")

    state = st.session_state.get("report_state")
    if state:
        st.success(f"报告已保存：{st.session_state.get('report_path', '')}")
        st.markdown(state.get("final_report", ""))
        st.download_button(
            "下载 Markdown 报告",
            data=state.get("final_report", ""),
            file_name="job-research-report.md",
            mime="text/markdown",
        )
