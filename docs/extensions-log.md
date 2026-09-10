# 扩展功能开发日志

> 每个扩展里程碑完成后记录：目的、改动、验证证据、已知问题、下一步。

## 进度总表

| 顺序 | 扩展 | 状态 |
|---|---|---|
| 1 | 岗位发现与多主体分类筛选 | 已完成（2026-09-10） |
| 1.1 | 数据来源扩展 + 博客抑制 + 地区筛选 | 已完成（2026-09-10） |
| 1.2 | 中大厂聚焦 + 来源全面性 + 搜索预算定标 | 已完成（2026-09-10） |
| 2 | Streamlit / Web 界面 | 已完成（2026-09-10） |
| 3 | 多语言输出（中文 / English） | 已完成（2026-09-10） |
| 4 | 简历速填与润色（解析 / 分块 / 按 JD 润色） | 已完成（2026-09-10） |
| 5 | MCP Server | 待开始 |
| 6 | 浏览器自动化 + 公司官网简历自动填写（人审后提交） | 待开始 |
| 7 | 跨会话长期记忆与向量库 | 待开始 |
| 8 | PDF / 图片报告 | 待开始 |
| 9 | 多智能体 Supervisor 架构 | 待开始 |
| 10 | 微信小程序（后端 API + 小程序前端） | 暂缓（可行性已确认） |

---

## M1：岗位发现与多主体分类筛选（2026-09-10）

### 目的与作用

- 新增“主题 → 自动搜集 → 分类 → 条件筛选 → 推荐”能力，后续 UI 可先选主题再看推荐；
- 多主体分类：把岗位按方向（AI Agent 应用 / RAG/检索 / 大模型应用 / 智能硬件 / 算法 / 后端）和技术栈（langgraph、rag、mcp、llm 等）打标；
- 支撑后续：Streamlit 界面可直接展示筛选后的推荐列表；向量记忆可按方向沉淀历史岗位。

### 改动

- `src/job_research_agent/job_discovery.py`：方向/技术规则、`classify_posting`、`filter_postings`、`score_posting`、`recommend_jobs`、5 个默认主题
- `src/job_research_agent/schemas.py`：新增 `JobPosting`、`JobSearchTheme`
- `tests/test_job_discovery.py`：5 个离线测试（TDD 先红后绿）

### 验证证据

- 单元测试：5 passed；全量 36 passed
- 真实运行（Tavily，主题“AI Agent 应用”，每关键词 3 条）：
  - 推荐 5 个岗位，均完成方向分类与技术栈打标
  - 示例：国家大学生就业服务平台“Agent 开发工程师实习生”，tags = langgraph/langchain/rag/agent/mcp/llm/prompt/python/embedding

### 已知问题

- 搜索结果里混入少量博客/资讯页（非招聘页），后续可在分类阶段加“招聘页特征”过滤或接入 Playwright 后重排；
- 目前仅规则分类，未使用 LLM；后续可与向量记忆结合做语义聚类。

### 下一步

Steamlit / Web 界面（M2）：主题选择 + 推荐列表 + 报告生成入口。

---

## M1.2：中大厂聚焦 + 来源全面性 + 搜索预算定标（2026-09-10）

### 目的与作用

- 聚焦高价值岗位：新增公司分层（大厂 / 中厂 / 其他）与公司类型（互联网 / 外企 / 硬件电子 / 其他），排序权重向中大厂倾斜；
- 保证信息全面：平台白名单扩充（新增 中华英才、大街、赶集、Indeed、Glassdoor），每主题关键词从 3 个扩到 5 个；
- 牛客权重保持：`job_platform` 权重 1.15（高于其他来源），只过滤其 /feed/、/discuss/ 与文章标题；
- 搜索预算定标：真实跑 6/9/12/15 轮对比，12 轮为拐点，默认 `max_searches=12`。

### 搜索预算实验结果（真实 Tavily）

| 搜索轮数 | 结果条数 | 大厂数 | 来源构成 |
|---|---|---|---|
| 6 | 16 | 6 | 平台 4 / 官网 3 / 其他 9 |
| 9 | 23 | 10 | 平台 6 / 官网 5 / 其他 12 |
| 12 | 30（触顶） | 17 | 平台 9 / 官网 10 / 其他 11 |
| 15 | 30（触顶） | 18 | 平台 13 / 官网 12 / 其他 4 / 校园 1 |

结论：12 轮后结果数触顶，大厂占比明显提升；15 轮仅多 1 条大厂、边际收益低。默认定为 **12 轮 / 每轮 5 条 / 最多返回 20 条**。

### 最终验证（默认参数，主题“AI Agent 应用”）

- 搜索 12 轮，返回 20 条
- 公司分层：大厂 14 / 其他 6
- 公司类型：互联网 11 / 外企 3 / 其他 6
- 来源构成：官网 10 / 招聘平台 6 / 其他 4
- 文章/帖子残留：0（含牛客 /discuss/ 帖已过滤）

### 已知问题

- BOSS直聘等强反爬平台的搜索索引覆盖有限；
- 公司分层基于规则名单，未收录公司会落到“其他”；
- 距离筛选仍未实现（需要地理编码/坐标）。

### 下一步

Streamlit / Web 界面（M2）：主题选择 + 地区筛选 + 公司分层筛选 + 推荐列表。

---

## M2：Streamlit / Web 界面（2026-09-10）

### 目的与作用

- 把岗位推荐与 JD 调研搬进浏览器，不再依赖命令行；
- 「岗位推荐」页：主题方向 + 省份/城市 + 公司分层（大厂/中厂/其他）+ 远程开关 + 条数上限；
- 「JD 调研」页：粘贴 JD → 生成调研大纲 → 页面内直接修改章节与关键词 → 开始调研 → 在线查看与下载 Markdown 报告；
- 复用现有 graph 与 `runner.run_research`，通过 `confirm_plan` 回调把人工修改的大纲注入真实 HITL 流程，无需重写编排。

### 改动

- 新增 `app.py`（Streamlit 双页签界面）
- 新增 `ui_helpers.py`（`plan_to_editable` / `editable_to_plan` / `format_job_markdown`）
- `runner.py` 新增 `generate_plan()`（供界面首屏生成大纲）
- 依赖新增 `streamlit==1.63.0`（含 pandas/pyarrow 等）

### 验证证据

- 单元测试：UI 辅助 4 passed；全量 **55 passed**
- 启动验证：`streamlit run app.py --server.headless true` 启动成功
  - `GET /_stcore/health` → 200 `ok`
  - `GET /` → 200，7459 bytes

### 已知问题

- 岗位推荐每次点击都会实时消耗 Tavily 配额（默认 12 轮搜索）；
- 调研过程暂无流式进度条，只有 spinner（后续可接 SSE/流式输出）。

### 下一步

多语言输出（M3）：报告支持中/英切换（面向外企 JD）。

---

## M3：多语言输出（2026-09-10）

### 目的与作用

- 报告支持中文 / English / 日本語，适配外企 JD（英飞凌、特斯拉、微软等）；
- 大纲、报告章节标题、评测标记全部按语言切换，保证评测器在多语言下仍能正确打分；
- CLI 与 Streamlit 界面都可选择报告语言。

### 改动

- `schemas.py`：`JobResearchInput` 新增 `language`（zh/en/ja，默认 zh）
- `prompts.py`：新增 `SECTION_TITLES` / `section_titles()` / `language_name()`，Planner 与 Report 提示词按语言生成
- `eval_harness.py`：评测标记按报告语言选择
- `cli.py` / `app.py`：新增语言选择

### 验证证据

- 单元测试：多语言 4 passed；全量 **59 passed**
- 端到端真实验证（language=en）：
  - 报告长度 9716 字符
  - 五个英文章节标记全部命中：JD Breakdown / Company & Team / Interviews & Assessment / Fit Gap / Action Plan

### 已知问题

- 语言只影响提示词与章节标题，检索关键词仍以中文主题词为主（后续可按语言生成搜索词）；
- 评测器对日文的规则标记较粗（仅章节标题级），未做日文语义评测。

### 下一步

MCP Server（M4）：把“岗位调研/岗位发现”封装成可被其他 Agent 调用的工具。

---

## 队列项：微信小程序（暂缓）

### 可行性结论

可行。现有核心逻辑已是独立 Python 模块（`runner` / `job_discovery` / graph），只需：

1. 增加一层 FastAPI 服务暴露接口（调研、岗位推荐、报告下载）；
2. 前端用 uni-app / Taro 或微信原生小程序，通过 HTTPS 调用该服务；
3. 微信要求：已备案的 HTTPS 域名 + 小程序 AppID；报告长文本可用分页或云存储链接传递。

### 暂缓原因

需要域名与备案等外部条件，当前优先完成无需备案的能力（MCP、抓取、记忆、导出等）。

---

## M4：简历速填与润色（2026-09-10）

### 目的与作用

- 支持上传简历（txt / md / PDF / 图片），自动提取文字并**分板块**（教育背景、项目经历、专业技能等）；
- 结合目标岗位 JD 做**按岗位润色**：重组表达、突出匹配关键词、给出量化建议；
- 明确约束“不得编造经历/数据”，只允许改写与重组已有内容；
- 输出可下载的 Markdown 润色结果，并在界面中提示后续将支持官网自动填写。

### 改动

- `resume.py`：`extract_text`（按扩展名分派）、`extract_text_from_pdf`（pdfplumber）、
  `extract_text_from_image`（pytesseract OCR）、`split_resume_sections`、`polish_resume`、
  `render_polished_markdown`
- `schemas.py`：`ResumeSection` / `ParsedResume` / `PolishedSection` / `ResumePolishResult`
- `prompts.py`：`POLISH_SYSTEM` 与 `resume_polish_user_prompt`（强调不得编造）
- `app.py`：新增「简历润色」页签（上传 → 解析 → 分板块展示 → 按 JD 润色 → 下载）
- 依赖：`pdfplumber`、`pytesseract`（dev：`reportlab` 用于测试生成 PDF）
- 同时按要求移除日语支持（仅保留中文 / English）

### 验证证据

- 单元测试：简历模块 7 passed（含真实 PDF 解析、OCR 包装逻辑、润色提示词与渲染）；全量 **66 passed**
- 端到端真实验证（真实 DeepSeek 润色）：
  - 板块识别：个人信息 / 教育背景 / 项目经历 / 专业技能 / 荣誉奖项（5 个）
  - 输出：summary + matched_keywords（Python、LangGraph、RAG）+ 5 个板块润色 + 建议
  - 建议中明确提示“若无 MCP 经历则不建议编造”

### 已知问题

- **图片 OCR 需本机安装 Tesseract**（未安装时给出明确报错）：
  `winget install --id UB-Mannheim.TesseractOCR`，并安装 chi_sim 语言包；
- 简历分块基于标题规则，非标准排版（如两栏 PDF）可能分块不准；
- 企业官网自动填写尚未实现（见下一步）。

### 下一步

MCP Server（M5）；之后 M6 做浏览器自动化 + 公司官网简历自动填写（Playwright + 人工确认后提交）。

---

## M1.1：数据来源扩展 + 博客抑制 + 地区筛选（2026-09-10）

### 目的与作用

- 数据来源扩展：企业官网招聘（careers./jobs./recruit 路径识别）+ 招聘平台（BOSS直聘、智联、猎聘、51job、拉勾、实习僧、牛客、LinkedIn 等域名白名单）；
- 博客抑制：默认过滤个人博客与文章帖（含 /feed/、/blog/、/article/、csdn、知乎、掘金等），大幅削减非岗位结果；
- 按用户要求屏蔽南开大学就业网（`career.nankai.edu.cn`）；
- 地区筛选：支持按省份、城市、是否接受远程过滤（如仅看广东省 / 仅看北京）。

### 改动

- `job_discovery.py`：`classify_source` 来源分类、`SOURCE_WEIGHTS` 排序权重、`BLOCKED_DOMAINS`、`ARTICLE_URL_PATTERNS`、`extract_location`（城市→省份映射）
- `recommend_jobs` 新增参数：`include_blogs`、`provinces`、`cities`、`allow_remote`、`use_source_queries`
- 搜索策略：每个主题关键词额外发起“官网招聘”查询与招聘平台域名限定查询（Tavily `include_domains`）
- `search.py`：`TavilySearchProvider.search` 支持 `include_domains`
- `schemas.py`：`JobPosting` 新增 `source_type`、`province`、`remote`

### 验证证据

- 单元测试：发现+来源相关 13 passed；全量 44 passed
- 真实运行（主题“AI Agent 应用”，筛选广东省）：
  - 推荐 2 条，均为真实岗位：国家大学生就业服务平台（官网/校招类）、牛客岗位详情（招聘平台）
  - 个人博客与牛客 feed 帖子被默认过滤
- 对比 M1：之前 5 条中含个人博客与资讯页；现在 0 条

### 已知问题

- BOSS直聘等平台反爬强、搜索引擎索引有限，命中率不稳定；
- “官网招聘”依赖 URL 特征（careers./jobs.），未枚举全部企业域名；
- **距离筛选未实现**：需要地理编码/坐标库（后续可与 M6 记忆/向量库一起做）。

### 下一步

Streamlit / Web 界面（M2）：主题选择 + 地区筛选 + 岗位推荐列表 + JD 调研入口。
