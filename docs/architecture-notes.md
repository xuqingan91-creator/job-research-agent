# GPT-Researcher 架构笔记

> 参考仓库：assafelovic/gpt-researcher
> 本地路径：reference/gpt-researcher
> 阅读日期：2026-09-09

---

## 问题 1：它的输入是什么？输出是什么？

### 输入

GPTResearcher.__init__() 接收的核心参数：

| 参数 | 类型 | 说明 |
|------|------|------|
| query | str | 研究主题/问题 |
| report_type | str | 报告类型：basic_report / detailed_report / deep_research 等 |
| report_source | str | 数据来源：web / local / hybrid / azure / langchain |
| source_urls / document_urls | list | 预指定的来源 URL |
| tone | str | 报告语气 |
| report_format | str | 输出格式（markdown 等） |
| query_domains | list | 限定搜索域名 |
| agent / role | str | 预设代理类型和角色 prompt |
| vector_store | object | 向量存储实例 |
| websocket | object | 实时进度推送 |
| mcp_configs | dict | MCP 服务器配置 |

多代理模式下还需传入：task（任务描述）、report_type、report_source、human_feedback 等参数。

### 输出

- write_report() 返回 Markdown 格式的研究报告字符串
- 多代理模式下，PublisherAgent 输出 PDF / Docx / Markdown 格式的最终报告
- 侧产物：research_sources（来源列表）、research_images（图片列表）、visited_urls（已访问 URL）、research_costs（成本记录）

---

## 问题 2：它分哪几个阶段？每个阶段谁负责？

### 单代理模式（GPTResearcher 主类编排）

| 阶段 | 负责模块 | 关键函数/类 |
|------|---------|------------|
| 1. 初始化组件 | GPTResearcher.__init__() | 创建 ResearchConductor、ReportGenerator、ContextManager、BrowserManager、SourceCurator |
| 2. 选择代理角色 | actions/agent_creator.py | choose_agent() - LLM 根据 query 自动选择 agent 类型和角色 prompt |
| 3. 生成研究计划 | actions/query_processing.py | plan_research_outline() - 生成研究大纲和子查询 |
| 4. 搜索资料 | skills/researcher.py | ResearchConductor.conduct_research() - 通过 retriever 执行搜索 |
| 5. 抓取网页 | skills/browser.py | BrowserManager.browse_urls() -> scrape_urls() |
| 6. 上下文压缩 | skills/context_manager.py | ContextManager - embedding 语义匹配，压缩冗余内容 |
| 7. 来源排序 | skills/curator.py | SourceCurator - LLM 对来源质量排序 |
| 8. 生成报告 | skills/writer.py | ReportGenerator.write_report() -> generate_report() |
| 9. 图片生成（可选） | skills/image_generator.py | ImageGenerator.plan_and_generate_images() |

### 多代理模式（LangGraph 工作流）

| 阶段 | 代理角色 | 职责 |
|------|---------|------|
| 1. 浏览阶段 | ResearchAgent | 执行初始研究（浏览器阶段） |
| 2. 规划阶段 | EditorAgent | 基于初始研究生成报告大纲 |
| 3. 人机审核 | HumanAgent | 审核大纲，可接受或要求修订 |
| 4. 深度研究 | ResearchAgent | 各子课题并行深度研究（委托 GPTResearcher） |
| 5. 审核 | ReviewerAgent | 根据用户指南审核草稿 |
| 6. 修订 | ReviserAgent | 根据 Reviewer 反馈修改草稿 |
| 7. 撰写 | WriterAgent | 汇总所有章节，编写引言、结论、来源引用 |
| 8. 发布 | PublisherAgent | 生成最终报告（PDF/Docx/Markdown） |

编排器：ChiefEditorAgent（multi_agents/agents/orchestrator.py）创建 LangGraph StateGraph，定义阶段间的跳转和循环。

---

## 问题 3：资料从哪来？搜索和抓取怎么组织的？

### 搜索引擎（17 种检索后端）

gpt_researcher/retrievers/ 下注册了 17 种 retriever：

Tavily（默认）、Google、Bing、Searx、DuckDuckGo、SerpApi、Serper、Arxiv、Semantic Scholar、PubMed Central、Exa、SearchApi、GetXAPI、BoCha、Xquik、MCPRetriever、Custom。

入口函数：
- actions/query_processing.py: get_search_results() - 直接实例化 retriever 并调用 .search()
- actions/retriever.py: get_retrievers() - 根据配置创建多个 retriever（支持多引擎并行搜索）

### 网页抓取（8 种 Scraper）

gpt_researcher/scraper/scraper.py 的 Scraper 类作为统一入口，根据 URL 类型自动选择：

| Scraper | 适用场景 |
|---------|---------|
| BeautifulSoup (bs) | 默认 HTML 页面 |
| PyMuPDF | PDF 文件 |
| ArxivScraper | Arxiv 论文页面 |
| WebBaseLoader | LangChain 兼容 |
| Playwright (browser) | JS 渲染页面 |
| NoDriver | 无头浏览器 |
| TavilyExtract | Tavily 抓取 API |
| FireCrawl | FireCrawl 服务 |

支持去重 URL、并发控制（MAX_SCRAPER_WORKERS 默认 15）、速率限制。

### 组织方式

1. ResearchConductor._search_relevant_source_urls() 遍历 retriever，调用 .search() 获取 URL 列表
2. _scrape_data_by_urls() 拿到 URL 后调用 BrowserManager.browse_urls()
3. browse_urls() 调用 scrape_urls() 实例化 Scraper 并执行抓取
4. 抓取结果交给 ContextManager 做 embedding 语义匹配和压缩
5. SourceCurator 用 LLM 对来源质量排序

搜索和抓取通过 asyncio.gather 并发执行，提高效率。

---

## 问题 4：它怎么决定"继续深挖还是收尾"？

关键发现：gpt-researcher 没有通过 LLM 主动判断"信息是否足够"的语义闭环。

现有的深度控制机制：

### 普通模式

- plan_research_outline() 生成一组 sub-queries（子查询）
- 所有 sub-queries 在 asyncio.gather 中并发处理完毕后，直接进入报告生成
- 没有循环判断、没有"资料不足则重新搜索"的逻辑

### Deep Research 模式

DeepResearchSkill（skills/deep_research.py）通过配置参数控制递归：

| 参数 | 说明 |
|------|------|
| breadth | 每一层并行查询数量（控制广度） |
| depth | 递归深度（控制深度） |
| concurrency_limit | 并发查询限制 |
| MAX_CONTEXT_WORDS = 25000 | 上下文词数上限 |

流程：generate_research_plan() 生成 follow-up questions -> deep_research() 递归执行 -> 每层按 breadth 并行，按 depth 递归 -> 达到 depth 上限后收束结果。

### 多代理模式

Researcher -> Reviewer -> Reviser 循环：Reviewer 审核草稿，如果不满意返回修改意见，Reviser 修改后再次审核。但循环次数由 LangGraph 图的边定义控制，不是动态判断。

结论：gpt-researcher 用"参数配置 + 递归结构"控制深度，而非"LLM 判断信息是否足够"的语义闭环。这是我们故意要做得不同的地方。

---

## 问题 5：它的状态/数据在模块之间怎么传递？

### 单代理模式

核心状态载体：GPTResearcher 实例本身。各 skill 持有 self.researcher 引用，直接读写其属性。

关键属性：

    GPTResearcher
      |-- query / agent / role          # 输入参数
      |-- context: str                  # 累积的研究上下文（核心数据）
      |-- visited_urls: set             # 已访问的 URL 集合
      |-- research_sources: list        # 来源列表
      |-- research_images: list         # 图片列表
      |-- available_images: list        # 可用图片
      |-- research_costs / step_costs   # 成本记录
      |-- 指向各 skill 实例              # 组件引用

数据流：
1. ResearchConductor 读取 query、retrievers、config -> 写入 context
2. BrowserManager 读取 URL 列表 -> 写入 research_sources、research_images
3. ContextManager 读取 pages / vector_store -> embedding 语义匹配 -> 返回压缩后上下文
4. SourceCurator 读取 source_data -> LLM 排序后返回
5. ReportGenerator 读取 context、query、report_type -> 写入报告

WebSocket 用于向 UI 实时推送进度日志（content、logs、path 事件）。

### 多代理模式

状态通过 ResearchState TypedDict（multi_agents/memory/research.py）在 LangGraph 节点间传递：

- title、headers、query、max_sections
- data（研究数据）
- sources、costs、task、report_type
- human_feedback（人机反馈）

各代理函数返回更新的 state dict，LangGraph 自动合并。

---

## 问题 6：哪些设计我们直接借鉴？哪些我们故意做得不一样？

### 直接借鉴

| 设计 | 我们如何用 |
|------|-----------|
| 子查询拆分 | plan_research_outline() 生成子查询的思路 -> 我们也做关键词扩展，生成多组搜索词 |
| Retriver 抽象层 | 统一接口 .search() + 可插拔后端 -> 我们复用 Tavily，但保留切换搜索引擎的抽象 |
| Scraper 统一入口 | 根据 URL 类型自动选择 scraper -> 我们简化版只需 BeautifulSoup + PDF |
| 上下文压缩 | embedding 语义匹配去冗余 -> 我们用 DeepSeek + 摘要压缩替代 embedding |
| Config 配置系统 | JSON + 环境变量 + 默认值三层 -> 我们简化为 .env + Python 常量 |
| 多代理角色分工 | Researcher / Writer / Reviewer 分离 -> 我们也分"搜索-分析-撰写"三阶段 |
| WebSocket 实时进度 | 向 UI 推送进度 -> 我们用 print 日志，后期可升级 |

### 故意做得不一样

| GPT-Researcher 的设计 | 我们的做法 | 原因 |
|----------------------|-----------|------|
| 无"信息足够性"判断 - 用参数控制深度 | LLM 主动判断资料是否足够 | 求职场景需要判断"面经是否覆盖核心问题"，不能靠固定深度 |
| 通用研究主题 | 求职垂直场景 | 专门针对"AI Agent 实习"岗位调研，prompt 和评测维度不同 |
| 无人机确认 - HumanAgent 仅在大纲阶段 | 多个人机确认点 | 大纲确认、资料确认、报告确认三道关卡 |
| 无独立评测器 - Reviewer 只审文字质量 | 独立评测器 | 评估报告覆盖面（岗位 JD、面经、技能要求等维度） |
| 重量级架构 - LangGraph + FastAPI + WebSocket | 轻量级 | 先跑通核心流程，不需要完整后端 |
| 固定报告模板 | 求职报告模板 | 输出结构为"岗位概览-技能要求-面经汇总-准备建议"而非通用研究报告 |

---

## 数据流转图

用户输入（求职方向 + 目标岗位）
  |
  v
生成调研计划（大纲 + 关键词）
  |  - DeepSeek 生成结构化大纲
  |  - 拆分为多个子查询关键词
  |
  v
搜索 -> 抓取网页 -> 清洗
  |  - Tavily 搜索获取 URL
  |  - BeautifulSoup/Playwright 抓取内容
  |  - 去重、截断、清洗为纯文本
  |
  v
判断资料是否足够
  |
  +-- 不足 -> 生成新关键词，回到搜索（循环）
  |         - DeepSeek 分析已有资料缺口
  |         - 生成补充搜索关键词
  |
  +-- 足够 -> 整理分析 -> 生成报告
              |  - DeepSeek 按求职报告模板生成
              |  - 包含：岗位概览、技能要求、面经汇总、准备建议
              |
              v
            最终报告（Markdown）
              |
              v
          评测器检查覆盖面
              |
              +-- 通过 -> 输出
              |
              +-- 不通过 -> 补充搜索（回到搜索阶段）

---

## 环境信息

- 参考仓库版本：gpt-researcher master 分支（2026-09-09 下载）
- 仓库结构：
  - gpt_researcher/ - 核心包（agent、skills、actions、retrievers、scraper、context、memory）
  - multi_agents/ - 多代理系统（8 个角色，LangGraph 编排）
  - backend/ - FastAPI 后端
  - frontend/ - React 前端
  - mcp-server/ - MCP 服务器
  - docs/ - 文档
