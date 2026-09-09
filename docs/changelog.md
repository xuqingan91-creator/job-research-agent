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
