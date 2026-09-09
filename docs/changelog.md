# 开发日志

## 2026-09-09（Day 1 修正版）
- 完成：项目初始化（git + uv）；依赖安装；hello_llm.py / hello_search.py 就位；gpt-researcher 架构笔记
- 真实验证（附输出）：
  - DeepSeek：返回合法 JSON（topic/keywords/outline），prompt_tokens=95, completion_tokens=106, total_tokens=201 → 通过
  - Tavily：返回 3 条真实搜索结果（牛客/CSDN 面经）→ 通过（网络可用）
  - .env 已 git 忽略；reference/ 已移出版本控制
- 修正：此前的 changelog/commit 声称“已连通”，当时实际未用真实 Key 验证；现以真实输出为准
- 卡点：GitHub clone 连接被重置，改用 ZIP 下载解决；uv 0.12 默认 src 布局，运行方式需用 .venv python 或 uv run
- 明天第一件事：搭 LLM 客户端封装（Day 2）

## 2026-09-09（Day 2-3 里程碑验收）
- 完成：config / schemas / llm / MockLLM 模块落地；pytest 全量通过（13 passed）
- 真实运行输出（LLMClient.structured → ResearchPlan）：

```json
{"topic":"AI Agent internship research","outline":["Overview of AI Agent field and internship landscape","Key skills and qualifications required","Top companies offering AI Agent internships","Application process and timeline","Resources for finding opportunities"],"keyword_groups":[["AI agent","internship","machine learning","NLP"],["LLM","reinforcement learning","autonomous agents","career"],["OpenAI","Anthropic","DeepMind","research"]]}
```

- 说明：上述输出为 .venv python 真实调用 DeepSeek 的结果，未做修改

## 2026-09-09（Day 4-5 里程碑验收）
- 完成：search.py（Tavily 搜索统一接口）+ fetch.py（requests + BeautifulSoup 正文清洗）
- pytest：search 2 + fetch 3 = 5 个新测试通过
- 真实验证（TavilySearchProvider.search）：返回 5 条真实结果
- 真实验证（fetch_page）：
  - Reddit 页面 → FetchError（403/反爬）→ 符合“单条失败不崩”设计
  - eightfold.ai 页面 → FETCH_OK，成功清洗并截断 300 字符

## 2026-09-09（LangGraph 线性流水线里程碑验收）
- 完成：state.py / prompts.py / nodes.py / graph.py，Planner → Search → Fetch → Analyze → Report 线性流程
- 真实 bug 与修复：DeepSeek 把 ResearchPlan 包在 {"research_plan": {...}} 外层导致校验失败；
  增加自动解包逻辑 + 提示词禁止包裹，新增测试锁定该行为
- pytest：新增 graph 2 + wrapped-json 1 = 3 个测试
- 端到端真实验证：输入英文 JD → 产出中文五段式报告
  - SOURCES 3，PAGES 1，final_report 为完整 Markdown（含 JD 拆解表格）

## 2026-09-09（反思循环 + 护栏里程碑验收）
- 完成：Reflect 节点 + 条件路由（不足→回 Search / 足够→Analyze）
- 完成：双重护栏（max_iterations + token 预算），超限强制收尾仍产出报告
- 修复两个循环 bug：重复搜索旧关键词、重复抓取旧来源（searched_keywords / fetched_urls 去重）
- pytest：新增 reflect 循环 + 护栏测试，全量 23 passed
- 端到端真实验证（max_iterations=2）：
  - SOURCES 2，PAGES 1，ITERATION 2，ENOUGH False
  - Reflect 两次判断资料不足 → 被护栏截停 → 仍生成 3397 字报告（符合设计）

## 2026-09-09（评测器里程碑验收）
- 完成：eval_harness.py（固定基准任务 + 规则打分 + 可选 LLM 打分 + JSON 落盘）
- pytest：新增 3 个测试（完整报告高分 / 空报告低分 / benchmark 落盘）
- 真实基准运行（1 case，规则 + 真实 LLM judge）：
  - AVG_RULE 100.0，AVG_FINAL 88.0，PASSED 1
  - 报告 3744 字，SOURCES 2，PAGES 1
  - 结果已落盘 outputs/eval/eval-*.json（git 忽略，作为简历数字证据）

## 2026-09-09（HITL 大纲人机确认里程碑验收）
- 完成：confirm 节点（interrupt）→ Planner 出大纲后暂停，人工修改后 Command(resume) 恢复
- pytest：新增 HITL 测试（暂停 → 修改 → 恢复 → 新关键词被搜索），全量 27 passed
- 端到端真实验证：
  - PAUSED_PLAN_TOPIC=AI Agent Internship Research Plan
  - RESUME 后大纲改为“自定义大纲：聚焦 RAG 面经”并生效
  - 恢复后产出 4880 字报告
- 技术债记录：LangGraph checkpoint 对 Pydantic 对象有 msgpack 反序列化警告
  （当前可用，未来版本可能阻止；后续可注册模块或把 state 改为纯 dict）

## 2026-09-09（V1 收尾）
- 完成：runner.py（非交互编排入口）+ cli.py（交互 CLI，SQLite checkpointer）+ .env.example
- 真实兼容修复（基准运行暴露）：
  - 关键词组为 dict 形态 → ResearchPlan 归一化
  - ReflectionDecision 返回 sufficient 同义字段 → 归一化
  - 模型自由改字段名 → structured() 自动注入 JSON Schema 并强制字段名
- 固定基准集 benchmark_cases.py（5 个求职场景）
- 真实基准运行：5/5 通过，规则均分 100，综合均分 94
  - 各 case 报告长度 3279-4233 字，来源 2 个/任务
- README 更新为完整使用文档；outputs/ 加入 git 忽略
