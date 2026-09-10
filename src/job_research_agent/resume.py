"""简历解析（文本 / PDF / 图片）与按 JD 润色。"""

from __future__ import annotations

from pathlib import Path

import pdfplumber
import pytesseract
from PIL import Image

from job_research_agent.llm import LLMClient
from job_research_agent.prompts import POLISH_SYSTEM, resume_polish_user_prompt
from job_research_agent.schemas import (
    ParsedResume,
    ResumePolishResult,
    ResumeSection,
)

TEXT_SUFFIXES = {".txt", ".md"}
PDF_SUFFIXES = {".pdf"}
IMAGE_SUFFIXES = {".png", ".jpg", ".jpeg", ".webp"}

HEADING_RULES: list[tuple[str, list[str]]] = [
    ("个人信息", ["个人信息", "联系方式"]),
    ("教育背景", ["教育背景", "教育经历", "education"]),
    ("实习/工作经历", ["实习经历", "工作经历", "实习经验", "工作经验", "experience"]),
    ("项目经历", ["项目经历", "项目经验", "projects", "project experience"]),
    ("专业技能", ["专业技能", "技能特长", "技能", "skills"]),
    ("荣誉奖项", ["荣誉奖项", "获奖情况", "获奖", "荣誉", "awards"]),
    ("校园经历", ["校园经历", "社团经历", "campus"]),
    ("科研/论文", ["科研经历", "论文", "研究成果", "publications"]),
    ("自我评价", ["自我评价", "个人优势", "个人总结", "summary"]),
]


class ResumeParseError(RuntimeError):
    """简历解析失败。"""


def extract_text_from_pdf(path: str | Path) -> str:
    with pdfplumber.open(str(path)) as pdf:
        pages = [page.extract_text() or "" for page in pdf.pages]
    return "\n".join(pages).strip()


def extract_text_from_image(path: str | Path) -> str:
    try:
        image = Image.open(str(path))
        return pytesseract.image_to_string(image, lang="chi_sim+eng").strip()
    except Exception as exc:  # 缺少 tesseract 或语言包时给出明确提示
        raise ResumeParseError(
            "图片 OCR 失败：请确认已安装 Tesseract OCR 及 chi_sim/eng 语言包"
            f"（原始错误：{exc}）"
        ) from exc


def extract_text(path: str | Path) -> str:
    resume_path = Path(path)
    if not resume_path.exists():
        raise ResumeParseError(f"文件不存在：{resume_path}")
    suffix = resume_path.suffix.lower()
    if suffix in TEXT_SUFFIXES:
        return resume_path.read_text(encoding="utf-8", errors="replace")
    if suffix in PDF_SUFFIXES:
        return extract_text_from_pdf(resume_path)
    if suffix in IMAGE_SUFFIXES:
        return extract_text_from_image(resume_path)
    raise ResumeParseError(f"不支持的文件类型：{suffix}（支持 txt/md/pdf/png/jpg）")


def split_resume_sections(text: str) -> list[ResumeSection]:
    sections: list[ResumeSection] = []
    current_title = ""
    current_lines: list[str] = []
    saw_heading = False

    def flush() -> None:
        if current_title:
            content = "\n".join(line for line in current_lines if line.strip()).strip()
            sections.append(ResumeSection(title=current_title, content=content))
        elif current_lines:
            content = "\n".join(line for line in current_lines if line.strip()).strip()
            if content:
                sections.append(ResumeSection(title="个人信息", content=content))

    for raw_line in text.splitlines():
        line = raw_line.strip()
        matched_title = ""
        if len(line) <= 24:
            lowered = line.lower()
            for title, patterns in HEADING_RULES:
                if any(pattern.lower() in lowered for pattern in patterns):
                    matched_title = title
                    break
        if matched_title:
            flush()
            current_title = matched_title
            current_lines = []
            saw_heading = True
        else:
            current_lines.append(line)
    flush()

    if not saw_heading:
        content = text.strip()
        return [ResumeSection(title="简历全文", content=content)] if content else []
    return sections


def polish_resume(
    parsed: ParsedResume,
    *,
    jd_text: str,
    llm: LLMClient,
) -> ResumePolishResult:
    return llm.structured(
        ResumePolishResult,
        system_prompt=POLISH_SYSTEM,
        user_prompt=resume_polish_user_prompt(parsed, jd_text),
    )


def render_polished_markdown(result: ResumePolishResult) -> str:
    lines = ["# 简历润色结果", "", f"**总体评价**：{result.summary}", ""]
    if result.matched_keywords:
        lines.append(f"**已匹配关键词**：{', '.join(result.matched_keywords)}")
        lines.append("")
    for section in result.sections:
        lines.append(f"## {section.title}")
        if section.polished:
            lines.append(section.polished)
        if section.keywords_added:
            lines.append("")
            lines.append(f"新增关键词：{', '.join(section.keywords_added)}")
        lines.append("")
    if result.suggestions:
        lines.append("## 改进建议")
        lines.extend(f"- {item}" for item in result.suggestions)
    return "\n".join(lines)
