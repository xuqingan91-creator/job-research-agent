"""Streamlit Web 界面：岗位推荐 + JD 调研。"""

from pathlib import Path

import streamlit as st

from job_research_agent.job_discovery import DEFAULT_THEMES, recommend_jobs
from job_research_agent.llm import LLMClient
from job_research_agent.resume import (
    ResumeParseError,
    extract_text,
    polish_resume,
    render_polished_markdown,
    split_resume_sections,
)
from job_research_agent.runner import generate_plan, run_research, save_report
from job_research_agent.schemas import JobResearchInput, ParsedResume
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

tab_jobs, tab_research, tab_resume = st.tabs(["岗位推荐", "JD 调研", "简历润色"])

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
    language = st.selectbox(
        "报告语言",
        options=["zh", "en"],
        format_func=lambda code: {"zh": "中文", "en": "English"}[code],
    )

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
                            language=language,
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
                            language=language,
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

with tab_resume:
    st.subheader("简历速填与润色")
    st.caption("支持 txt / md / PDF / 图片（图片需本机安装 Tesseract OCR）")
    uploaded = st.file_uploader(
        "上传简历",
        type=["txt", "md", "pdf", "png", "jpg", "jpeg"],
    )
    jd_for_resume = st.text_area("目标岗位 JD（用于匹配润色）", height=160)

    if st.button("解析简历"):
        if uploaded is None:
            st.warning("请先上传简历文件。")
        else:
            upload_dir = Path("outputs/uploads")
            upload_dir.mkdir(parents=True, exist_ok=True)
            file_path = upload_dir / uploaded.name
            file_path.write_bytes(uploaded.getbuffer())
            try:
                text = extract_text(file_path)
                parsed = ParsedResume(
                    raw_text=text,
                    sections=split_resume_sections(text),
                    source=file_path.suffix.lstrip("."),
                )
                st.session_state["parsed_resume"] = parsed
            except ResumeParseError as exc:
                st.error(str(exc))
            except Exception as exc:  # noqa: BLE001
                st.error(f"解析失败：{exc}")

    parsed_resume = st.session_state.get("parsed_resume")
    if parsed_resume:
        st.success(f"解析成功：识别出 {len(parsed_resume.sections)} 个板块")
        with st.expander("查看分板块内容", expanded=False):
            for section in parsed_resume.sections:
                st.markdown(f"**{section.title}**")
                st.text(section.content)

        if st.button("按目标 JD 润色", type="primary"):
            if not jd_for_resume.strip():
                st.warning("请粘贴目标岗位 JD。")
            else:
                with st.spinner("正在按 JD 润色..."):
                    try:
                        st.session_state["polish_result"] = polish_resume(
                            parsed_resume,
                            jd_text=jd_for_resume,
                            llm=LLMClient(),
                        )
                    except Exception as exc:  # noqa: BLE001
                        st.error(f"润色失败：{exc}")

    polish_result = st.session_state.get("polish_result")
    if polish_result:
        markdown = render_polished_markdown(polish_result)
        st.markdown(markdown)
        st.download_button(
            "下载润色结果",
            data=markdown,
            file_name="resume-polished.md",
            mime="text/markdown",
        )
    st.info("后续版本将支持在企业招聘官网自动填写信息（人工确认后提交）。")
