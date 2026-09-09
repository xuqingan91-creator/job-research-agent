# Job Research Agent（求职调研智能体）

## 定位

为求职者提供目标岗位深度调研：粘贴 JD + 个人背景，输出结构化调研报告。

## 用户故事

> 我输入"华为 AI 工程师实习"的 JD 和我的背景，Agent 先给我一份调研大纲确认，
> 再自主搜索公司/团队/岗位要求/面经，最后输出五段式报告和行动清单。

## 输入 / 输出

- **输入**：公司/岗位名称、JD 全文、个人背景简述
- **输出**：Markdown 报告（JD 拆解 / 公司调研 / 面经整理 / 匹配度差距 / 行动清单 + 来源）

## 差异化设计

1. **Human-in-the-loop**：大纲人工确认后恢复执行
2. **成本与轮次护栏**：防失控、可量化
3. **评测器 + 固定基准集**：每次迭代有分数对比

## 技术栈

- Python 3.10 + uv 包管理
- DeepSeek API（LLM，结构化 JSON 输出）
- Tavily API（联网搜索）
- python-dotenv（环境变量管理）

## 项目结构

```
job-research-agent/
├── .env                    # API 密钥（已被 git 忽略）
├── .gitignore
├── pyproject.toml          # 依赖声明
├── uv.lock                 # 锁定版本
├── README.md               # 产品定义（本文件）
├── hello_llm.py            # DeepSeek 连通测试
├── hello_search.py         # Tavily 搜索测试
├── src/
│   └── job_research_agent/
│       └── __init__.py     # 入口（uv init 生成）
├── docs/
│   ├── architecture-notes.md  # gpt-researcher 架构笔记
│   └── changelog.md           # 开发日志
└── reference/
    └── gpt-researcher/     # 参考仓库（只读）
```

## 快速开始

```bash
# 1. 安装依赖
uv sync

# 2. 配置密钥
cp .env.example .env  # 填入你的 DEEPSEEK_API_KEY 和 TAVILY_API_KEY

# 3. 运行测试
uv run hello_llm.py      # 验证 DeepSeek 连通
uv run hello_search.py   # 验证 Tavily 搜索
```
