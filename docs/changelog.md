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
