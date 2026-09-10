# Job Research Agent（求职调研智能体）

面向求职者的深度调研 Agent：粘贴目标岗位 JD 与个人背景，自动生成五段式中文求职调研报告。
内置大纲人机确认、反思循环、成本/轮次护栏与评测器。

## 功能

- 输入：公司/岗位 + JD 全文 + 个人背景
- 输出：Markdown 报告（JD 要求拆解 / 公司与团队背景 / 面经与考核点 / 匹配度差距 / 行动清单），结论尽量带来源
- HITL：Planner 生成大纲后暂停，人工确认或粘贴修改后的 JSON 再继续
- 反思循环：资料不足时自动补搜，受最大轮次与 token 预算双重限制
- 评测器：固定基准任务 + 规则/LLM 双打分，结果落盘 `outputs/eval/`
- Mock/离线测试：pytest 全离线可跑，不消耗 API

## 快速开始

前置：Python 3.10+ 与 [uv](https://docs.astral.sh/uv/)。

```powershell
cd C:\Users\29056\Documents\Codex\2026-09-09\wo-s\work\job-research-agent
Copy-Item .env.example .env   # 填入 DEEPSEEK_API_KEY / TAVILY_API_KEY
uv sync
uv run job-research-agent
```

交互说明：

1. 输入目标公司/岗位；
2. 粘贴 JD，粘贴完后输入一个空行结束；
3. 输入个人背景（可直接回车跳过）；
4. Agent 生成大纲后暂停：直接回车=确认，粘贴 JSON=替换大纲，输入 no=退出；
5. 调研完成后报告保存在 `outputs/reports/`。

### Web 界面（推荐）

```powershell
.\.venv\Scripts\streamlit.exe run app.py
# 或：uv run streamlit run app.py
```

浏览器打开 `http://localhost:8501`：

- **岗位推荐**：选择主题方向，按省份 / 城市 / 公司分层（大厂、中厂）筛选，
  结果优先展示企业官网与招聘平台岗位，自动过滤博客与帖子；
- **JD 调研**：粘贴 JD → 生成调研大纲 → 在页面上直接修改章节与关键词 →
  选择报告语言（中文 / English）→ 开始多轮调研 → 在线查看并下载 Markdown 报告。
- **简历润色**：上传 txt / md / PDF / 图片简历 → 自动分板块 → 粘贴目标 JD →
  生成按岗位定制的润色结果并下载（图片 OCR 需安装 Tesseract）。

## 测试

```powershell
.\.venv\Scripts\python.exe -m pytest -q
```

全量测试离线运行，不联网、不消耗 API。

## 评测

固定基准集定义在 `src/job_research_agent/benchmark_cases.py`（5 个求职场景）。
真实运行会消耗少量 API 费用：

```powershell
.\.venv\Scripts\python.exe -c "from pathlib import Path; from job_research_agent.llm import LLMClient; from job_research_agent.search import TavilySearchProvider; from job_research_agent.graph import build_research_graph; from job_research_agent.eval_harness import run_benchmark; from job_research_agent.benchmark_cases import DEFAULT_CASES; run_benchmark(lambda: build_research_graph(LLMClient(), TavilySearchProvider(), max_keyword_groups=1, keywords_per_group=1, results_per_keyword=2, max_pages=2, max_chars=600, max_iterations=1), DEFAULT_CASES, judge=LLMClient(), output_dir=Path('outputs/eval'))"
```

最近一次真实基准（2026-09-09）：5/5 通过，规则分均 100，综合分均 94。

## 架构

```text
CLI / runner
  → Planner（LLM 结构化输出调研计划）
  → [HITL] confirm：人工确认/修改大纲（interrupt/resume + SQLite checkpointer）
  → Search（Tavily 搜索，可注入替身）
  → Fetch（requests + BeautifulSoup 清洗，失败自动跳过）
  → Reflect（判断资料是否足够）
       不足且未超护栏 → 补关键词回 Search
       足够/超护栏 → Analyze
  → Analyze（按报告章节归类）
  → Report（生成五段式 Markdown）
  → Eval（规则 + LLM 打分，落盘）
```

模块划分：

| 模块 | 职责 |
|---|---|
| `config.py` | .env 与默认配置 |
| `schemas.py` | Pydantic 模板（含模型输出形态归一化） |
| `llm.py` | DeepSeek 封装：chat / structured / MockLLM |
| `search.py` / `fetch.py` | 搜索与网页抓取 |
| `prompts.py` | 提示词集中管理 |
| `state.py` / `nodes.py` / `graph.py` | LangGraph 状态、节点、组装 |
| `eval_harness.py` | 评测与落盘 |
| `runner.py` / `cli.py` | 编排入口与交互 CLI |

## 已验证证据（2026-09-09）

- 全量单元测试：通过（30+）
- 端到端：输入 JD → 五段式中文报告（多轮真实运行）
- HITL：真实暂停 → 修改大纲 → 恢复 → 报告生成
- 真实基准：5/5 通过，规则均分 100，综合均分 94
- 过程中修复的真实模型兼容问题：包裹式 JSON、字典型关键词组、`sufficient` 同义字段、自由字段名（通过注入 JSON Schema 解决）

## 已知限制与技术债

- 部分站点（如 Glassdoor/Reddit）反爬会返回 403，fetch 会跳过该来源而非中断
- LangGraph checkpoint 对 Pydantic 对象有 msgpack 反序列化警告（当前可用；后续可注册序列化模块或把 state 改为纯 dict）
- 评测与真实调研需要 DeepSeek/Tavily 密钥并产生少量费用
- 报告中的“公司与团队/面经”质量依赖搜索引擎可达性

## 后续扩展方向

Web/Streamlit 界面、MCP Server、多智能体 Supervisor、浏览器渲染抓取、跨会话记忆、PDF/图片导出等接口已在设计中预留（见 spec 扩展约束）。
