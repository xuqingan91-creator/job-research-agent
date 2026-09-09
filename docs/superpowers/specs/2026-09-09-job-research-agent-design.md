# Job Research Agent（求职调研智能体）V1 设计文档

> 日期：2026-09-09
> 状态：已与用户分节确认（模块边界、数据流、LLM 封装、搜索/抓取）
> 学习模式：边做边讲——每个模块先讲 10 分钟设计，再实现、运行、记录

## 1. 目标与用户故事

做一个面向求职者的深度调研 Agent：输入“目标公司/岗位 + JD 全文 + 个人背景”，自动产出结构化求职调研报告，用于自己求职，同时作为简历与面试的核心项目。

用户故事：

> 我把想投的岗位 JD 粘贴进去，简单描述背景。Agent 先给我一份调研大纲让我确认或修改；确认后自主多轮搜索公司背景、团队技术栈、岗位要求、公开面经；最后输出一份包含“JD 拆解 / 公司与团队调研 / 面经整理 / 匹配度差距 / 行动清单”的报告，结论尽量带来源。

## 2. V1 范围

### 做

- CLI 驱动完整流程（当前无界面，先跑通核心）
- DeepSeek API 真实调用（已验证可连通）
- Tavily 搜索（已验证网络可用）
- 网页抓取与正文清洗
- LangGraph 状态机编排：Planner / Search / Reflect / Analyze / Report
- 大纲人机确认（HITL）与断点恢复
- 成本与轮次护栏
- 评测器 + 固定基准集
- Markdown 报告输出（中文，五段式 + 来源）
- MockLLM 离线模式与 pytest 测试

### 不做（V1 明确排除）

- Streamlit / Web 界面
- MCP Server
- 多智能体 Supervisor 架构
- 浏览器自动化 / JS 渲染抓取
- 跨会话长期记忆与向量库
- PDF / 图片报告
- 自动投递简历
- 多语言输出

## 3. 输入与输出

### 输入（JobResearchInput）

- `company`：公司/岗位名称
- `jd_text`：JD 全文
- `profile_text`：个人背景简述（供匹配度分析）

### 输出

- 最终报告：Markdown 文件，章节固定
  1. JD 要求拆解（硬性 / 软性 / 加分项）
  2. 公司与目标团队背景
  3. 公开面经与考核点整理
  4. 我的匹配度分析
  5. 下一步行动清单
- 附：来源列表；每轮调用的 token / 费用 / 轮次日志

## 4. 技术栈与环境

| 项 | 选型 | 现状 |
|---|---|---|
| 语言 | Python 3.10（uv 管理） | 已就绪 |
| 依赖 | openai / python-dotenv / tavily-python | 已安装 |
| 后续新增 | pydantic、requests、beautifulsoup4、langgraph、pytest | 按里程碑现场安装 |
| 密钥 | `.env`（DeepSeek、Tavily） | 已配置且已验证 |

## 5. 架构与模块划分

统一放入 `src/job_research_agent/`：

| 模块 | 职责 |
|---|---|
| `config.py` | 读 .env / 默认预算 / 模型名 / 输出目录 |
| `schemas.py` | 全部 Pydantic 模板（输入、计划、反思决策、来源、报告） |
| `llm.py` | DeepSeek 封装：chat、结构化输出、重试、token/费用记录、MockLLM |
| `search.py` | 搜索接口抽象 + Tavily 实现 |
| `fetch.py` | 网页请求、HTML 清洗、截断、去重 |
| `prompts.py` | 所有提示词集中管理 |
| `state.py` | LangGraph 状态类型 |
| `nodes.py` | 各节点实现（planner / search / reflect / analyze / report） |
| `graph.py` | StateGraph 组装、条件路由、Checkpointer |
| `eval_harness.py` | 基准集、规则 + LLM 评分、结果落盘与对比 |
| `cli.py` | 收输入、调 graph、打印日志、保存报告 |

测试放 `tests/`，与 src 一一对应；固定数据放 `tests/fixtures/`。

### 依赖铁律

1. `llm / search / fetch / schemas` 不 import LangGraph；
2. 只有 `state / nodes / graph` 与 LangGraph 相关；
3. `cli` 只做编排，不直接调 API；
4. 改 prompts 不碰代码，改搜索实现不碰报告逻辑。

## 6. 数据流与状态

### 状态字段（共享白板）

| 字段 | 内容 | 写入者 |
|---|---|---|
| user_input | 用户输入 | cli |
| plan | 大纲 + 分组关键词 | planner |
| sources | 来源列表 | search |
| pages | 清洗后的正文 | fetch |
| reflection | 最近一次“够不够”判断 | reflect |
| iteration | 当前轮数 | graph |
| budget | 已用 token / 次数 / 费用 | 各节点 |
| evidence | 按报告章节归类的素材 | analyze |
| final_report | 最终 Markdown | report |
| status | 当前步骤 / 是否等人确认 | graph |

### 流转

```text
CLI 输入 → user_input
  → planner 生成 plan
  → graph 暂停（HITL：用户确认/修改大纲）
  → search：关键词 → sources
  → fetch：sources → pages（去重、截断）
  → reflect：pages 是否足够？
      不足且未超预算 → 生成新关键词 → 回到 search，iteration + 1
      足够 → analyze：pages → evidence（按报告章节归类）
  → report：evidence → final_report（Markdown）
  → 保存文件；（可选）eval 打分落盘
```

### 状态硬规则

- State 只放可序列化数据（str / int / list / Pydantic 模型），不放网页对象或连接
- 每次调 LLM / 搜索前先检查预算
- 来源按 URL 去重；单篇正文截断

## 7. LLM 客户端与结构化输出

- `llm.chat()`：最底层调用，带超时、重试、费用记录
- `llm.structured(模板, ...)`：要求 JSON → 解析 → Pydantic 校验 → 失败重试（最多 2 次）→ 明确报错
- 报告生成用普通长文调用（给人读）；规划/反思/评测用结构化调用（给机器读）
- `MockLLM`：无网无 Key 可测试，接口与真实客户端一致
- 预算闸门在 llm 层先拦一道，graph 层再拦一道

出错阶梯（每层兜底）：

```text
模型返回 → JSON 解析
  成功 → Pydantic 校验 → 通过 → 使用
                     └ 失败 → 错误信息回填提示词，重试（≤2 次）
  失败 → 换更明确指令再试一次
      └ 仍失败 → LLMStructuredOutputError
          └ 上层兜底：Planner 失败让用户手动给大纲；Reflect 失败按规则默认收尾/续搜
```

## 8. 搜索与网页抓取

- `search.search(query, max_results) -> [SourceItem]`
  - 现由 Tavily 实现（已验证）；接口抽象，便于换备用引擎
- `fetch.fetch(url) -> 正文或失败标记`
  - requests 请求 + BeautifulSoup 清洗 + 截断

错误处理：

```text
搜索失败 → 减少关键词或换引擎；记录后继续
单条网址抓取失败 → 跳过该条，不影响其他
全部抓取失败 → reflect 看到空资料，自动收尾并说明缺口
```

## 9. 后续里程碑的关键设计（实现时逐节确认）

这些方向已在对话中确认，具体细节在对应模块实现前再展开讲解：

- 反思循环：reflect 根据“新增来源数 / 大纲覆盖情况 / 信息缺口”决定继续或收尾
- 护栏：最大轮数 + token/费用预算，超限强制收尾并保留已有产出
- HITL：大纲生成后 interrupt，用户可改大纲/增删关键词，基于 SQLite Checkpointer 断点恢复
- 评测器：固定基准任务集，规则分（章节覆盖/来源数量）+ LLM 分（质量/可行动性），结果落盘，支持版本对比
- 求职垂直化：报告五段式模板 + 求职导向 prompt

## 10. 测试与验证策略

- MockLLM + 固定 fixture：测试不联网、不花钱
- fetch 用本地 HTML 样例测试清洗结果
- 每条验收 = 真实命令输出贴进 `docs/changelog.md`
- “看起来完成”不算完成：无验证证据不写“已完成”

## 11. 目标目录结构（V1 结束态）

```text
job-research-agent/
├── pyproject.toml / uv.lock / .env(忽略) / .gitignore
├── README.md
├── docs/
│   ├── changelog.md
│   ├── architecture-notes.md
│   └── superpowers/specs/2026-09-09-job-research-agent-design.md
├── src/job_research_agent/
│   ├── __init__.py
│   ├── config.py
│   ├── schemas.py
│   ├── llm.py
│   ├── search.py
│   ├── fetch.py
│   ├── prompts.py
│   ├── state.py
│   ├── nodes.py
│   ├── graph.py
│   ├── eval_harness.py
│   └── cli.py
├── tests/
│   ├── fixtures/
│   ├── test_schemas.py
│   ├── test_llm.py
│   ├── test_search.py
│   ├── test_fetch.py
│   └── test_graph.py
└── outputs/（运行时生成报告，git 忽略）
```

## 12. V1 完成验收标准

- 输入真实 JD（如小米/华为实习岗）可在预算内产出完整五段式报告
- 报告 ≥60% 结论带来源；大纲可人工修改并断点恢复
- MockLLM 下无 Key 可跑通测试
- 评测器在固定基准集上能跑出分数并落盘
- 有轮次/token 预算护栏，不会无限循环
- 搜索/抓取失败能降级，不崩溃
- README 含架构图与设计决策；changelog 每天真实记录
