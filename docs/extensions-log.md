# 扩展功能开发日志

> 每个扩展里程碑完成后记录：目的、改动、验证证据、已知问题、下一步。

## 进度总表

| 顺序 | 扩展 | 状态 |
|---|---|---|
| 1 | 岗位发现与多主体分类筛选 | 已完成（2026-09-10） |
| 2 | Streamlit / Web 界面 | 待开始 |
| 3 | 多语言输出 | 待开始 |
| 4 | MCP Server | 待开始 |
| 5 | 浏览器自动化 / JS 渲染抓取 | 待开始 |
| 6 | 跨会话长期记忆与向量库 | 待开始 |
| 7 | PDF / 图片报告 | 待开始 |
| 8 | 多智能体 Supervisor 架构 | 待开始 |
| 9 | 半自动投递（人审后提交） | 待开始 |

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
