"""CLI 入口：收集输入 → HITL 确认大纲 → 生成并保存报告。"""

from __future__ import annotations

import json
import sys
from pathlib import Path

from langgraph.checkpoint.sqlite import SqliteSaver

from job_research_agent.llm import LLMClient
from job_research_agent.runner import run_research, save_report
from job_research_agent.schemas import JobResearchInput, ResearchPlan
from job_research_agent.search import TavilySearchProvider


def _read_multiline(prompt: str) -> str:
    print(prompt)
    lines: list[str] = []
    while True:
        try:
            line = input()
        except EOFError:
            break
        if line.strip() == "":
            break
        lines.append(line)
    return "\n".join(lines).strip()


def confirm_plan_interactive(plan: ResearchPlan) -> ResearchPlan:
    print("\n=== 调研大纲（待你确认）===")
    print(plan.model_dump_json(indent=2, ensure_ascii=False))
    print("\n操作：直接回车 = 按此大纲继续；粘贴 JSON = 替换大纲；输入 no = 退出")
    try:
        reply = input().strip()
    except EOFError:
        reply = ""
    if reply.lower() == "no":
        sys.exit("已退出，未生成报告。")
    if not reply:
        return plan
    try:
        return ResearchPlan.model_validate(json.loads(reply))
    except Exception as exc:
        print(f"JSON 解析失败（{exc}），按原大纲继续。")
        return plan


def main(argv: list[str] | None = None) -> None:
    print("Job Research Agent —— 求职岗位深度调研")
    company = input("目标公司/岗位：").strip()
    if not company:
        sys.exit("公司/岗位不能为空。")
    jd_text = _read_multiline("请粘贴 JD 全文，粘贴完输入一个空行结束：")
    if not jd_text:
        sys.exit("JD 不能为空。")
    print("个人背景简述（可跳过，直接回车）：")
    try:
        profile_text = input().strip()
    except EOFError:
        profile_text = ""
    print("报告语言（zh=中文 / en=English，默认 zh）：")
    try:
        language = input().strip().lower() or "zh"
    except EOFError:
        language = "zh"
    if language not in {"zh", "en"}:
        language = "zh"

    user_input = JobResearchInput(
        company=company,
        jd_text=jd_text,
        profile_text=profile_text,
        language=language,
    )
    checkpoints_dir = Path("outputs")
    checkpoints_dir.mkdir(parents=True, exist_ok=True)
    db_path = checkpoints_dir / "checkpoints.sqlite"
    with SqliteSaver.from_conn_string(str(db_path)) as checkpointer:
        state = run_research(
            user_input,
            llm=LLMClient(),
            search_provider=TavilySearchProvider(),
            confirm_plan=confirm_plan_interactive,
            checkpointer=checkpointer,
            thread_id="cli",
        )
    report_path = save_report(state)
    print("\n报告已保存：", report_path)
    print(
        "摘要：",
        f"来源 {len(state.get('sources', []))} 个，"
        f"正文 {len(state.get('pages', []))} 页，"
        f"报告 {len(state.get('final_report', ''))} 字",
    )


if __name__ == "__main__":
    main()
