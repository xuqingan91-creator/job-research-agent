"""V1 固定评测基准集（真实运行时会消耗少量 API 费用）。"""

from job_research_agent.eval_harness import BenchmarkCase
from job_research_agent.schemas import JobResearchInput


def _case(name: str, company: str, jd: str, profile: str = "") -> BenchmarkCase:
    return BenchmarkCase(
        name=name,
        user_input=JobResearchInput(company=company, jd_text=jd, profile_text=profile),
    )


DEFAULT_CASES: list[BenchmarkCase] = [
    _case(
        "agent-intern-basic",
        "AI Agent 应用开发实习",
        "负责基于 LangGraph 的 Agent 应用开发，熟悉 RAG 与工具调用，有 Python 基础。",
        "211 电子信息本科，Python 基础，做过 LangGraph 调研 Agent。",
    ),
    _case(
        "llm-app-intern",
        "大模型应用开发实习",
        "参与大模型应用研发，涉及提示词工程、评测体系建设、API 服务开发。",
        "熟悉 DeepSeek API 与结构化输出，有评测 Harness 经验。",
    ),
    _case(
        "rag-engineer-intern",
        "RAG 检索增强实习生",
        "负责知识库问答系统，要求掌握向量检索、混合召回、重排与效果评测。",
        "实现过网页检索管线与正文清洗。",
    ),
    _case(
        "aiot-agent-intern",
        "智能硬件 Agent 实习生",
        "将大模型能力落地到智能硬件场景，熟悉设备数据接入与端云协同。",
        "电子信息专业，做过 ESP32 端云项目，熟悉传感器与云端链路。",
    ),
    _case(
        "ml-platform-intern",
        "机器学习平台实习生",
        "支撑算法团队的数据与模型评测流程，要求 Python 与自动化测试能力。",
        "有 pytest 与 CLI 工具开发经验。",
    ),
]
