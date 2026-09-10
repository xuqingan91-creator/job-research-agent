"""简历解析、分块与按 JD 润色。"""

from PIL import Image

from job_research_agent.resume import (
    ParsedResume,
    ResumeSection,
    extract_text,
    extract_text_from_pdf,
    polish_resume,
    render_polished_markdown,
    split_resume_sections,
)
from job_research_agent.schemas import (
    PolishedSection,
    ResumePolishResult,
)

SAMPLE_RESUME = """张三
电话：13800000000 邮箱：a@b.com

教育背景
2023-2027 某大学 电子信息工程 本科
GPA 3.7/4.0

项目经历
求职调研 Agent：使用 LangGraph 构建多阶段调研流程
实现 RAG 检索与结构化报告生成

专业技能
Python、Git、Linux；了解 LangGraph、RAG

荣誉奖项
校级一等奖学金
"""


def test_extract_text_from_txt(tmp_path):
    path = tmp_path / "resume.txt"
    path.write_text(SAMPLE_RESUME, encoding="utf-8")
    assert "教育背景" in extract_text(path)


def test_split_resume_sections_recognizes_headings():
    sections = split_resume_sections(SAMPLE_RESUME)
    titles = [section.title for section in sections]
    assert "教育背景" in titles
    assert "项目经历" in titles
    assert "专业技能" in titles
    project = next(s for s in sections if s.title == "项目经历")
    assert "LangGraph" in project.content


def test_split_resume_falls_back_to_single_section():
    sections = split_resume_sections("没有任何标题的简历正文")
    assert len(sections) == 1
    assert sections[0].title == "简历全文"


def test_extract_text_from_real_pdf(tmp_path):
    from reportlab.pdfgen import canvas

    path = tmp_path / "resume.pdf"
    pdf = canvas.Canvas(str(path))
    pdf.drawString(72, 720, "Education")
    pdf.drawString(72, 700, "Tsinghua University Electronic Information")
    pdf.save()
    text = extract_text_from_pdf(path)
    assert "Education" in text
    assert "Tsinghua" in text


def test_extract_text_from_image_uses_ocr(tmp_path, monkeypatch):
    path = tmp_path / "resume.png"
    Image.new("RGB", (20, 20), "white").save(path)

    def fake_image_to_string(image, lang=None):
        return "OCR RESUME CONTENT"

    monkeypatch.setattr(
        "job_research_agent.resume.pytesseract.image_to_string",
        fake_image_to_string,
    )
    assert extract_text(path) == "OCR RESUME CONTENT"


class FakePolishLLM:
    def __init__(self):
        self.user_prompt = ""

    def structured(self, output_model, *, system_prompt, user_prompt, temperature=0.3):
        self.user_prompt = user_prompt
        return ResumePolishResult(
            summary="与 JD 匹配度中等，突出 Agent 项目",
            sections=[
                PolishedSection(
                    title="项目经历",
                    original="求职调研 Agent",
                    polished="基于 LangGraph 构建多阶段求职调研 Agent，覆盖 RAG 检索与结构化报告",
                    keywords_added=["LangGraph", "RAG"],
                )
            ],
            suggestions=["补充量化指标"],
            matched_keywords=["LangGraph", "RAG", "Python"],
        )


def test_polish_resume_passes_jd_to_llm():
    parsed = ParsedResume(
        raw_text=SAMPLE_RESUME,
        sections=[ResumeSection(title="项目经历", content="求职调研 Agent")],
    )
    llm = FakePolishLLM()
    result = polish_resume(parsed, jd_text="要求熟悉 LangGraph 与 RAG", llm=llm)
    assert result.summary
    assert "LangGraph" in llm.user_prompt
    assert result.sections[0].polished


def test_render_polished_markdown_contains_sections():
    result = ResumePolishResult(
        summary="摘要",
        sections=[
            PolishedSection(
                title="项目经历",
                original="旧",
                polished="新描述",
                keywords_added=["RAG"],
            )
        ],
        suggestions=["补充量化"],
        matched_keywords=["RAG"],
    )
    markdown = render_polished_markdown(result)
    assert "摘要" in markdown
    assert "项目经历" in markdown
    assert "新描述" in markdown
