# LLM 客户端与结构化输出 Implementation Plan（Day 2-3 里程碑）

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 把已经验证的 `hello_llm.py` 正式封装为可复用的 `config.py` / `schemas.py` / `llm.py`，并建立 MockLLM 与 pytest 测试基线。

**Architecture:** 三个新模块全部位于 `src/job_research_agent/`：`config.py` 读环境与常量；`schemas.py` 定义 Pydantic 数据模板；`llm.py` 提供 `LLMClient.chat()`（底层调用）、`LLMClient.structured()`（JSON+Pydantic 校验+重试）与 `MockLLM`（离线替身）。模块之间单向依赖：`llm.py` 依赖 `config.py` 与 `schemas.py`，不依赖 LangGraph。

**Tech Stack:** Python 3.10 / uv / openai / python-dotenv / pydantic / pytest

**Spec:** `docs/superpowers/specs/2026-09-09-job-research-agent-design.md`

## Global Constraints

- 代码路径：`src/job_research_agent/`；测试路径：`tests/`
- `llm / search / fetch / schemas` 不 import LangGraph
- 所有 Pydantic 模型放在 `schemas.py`
- `.env` 与真实 Key 永不提交；测试禁止联网、禁止花钱
- 每条验收必须贴真实命令输出到 `docs/changelog.md` 才算完成
- 运行测试：在项目根目录执行 `.\.venv\Scripts\python.exe -m pytest -v`（或 `python -m uv run pytest -v`）
- 每次任务结束单独 commit

---

## Task 1: 安装 pydantic 与 pytest

**Files:**
- Modify: `pyproject.toml`

**Interfaces:**
- Consumes: 无
- Produces: 依赖 `pydantic`、`pytest`；pytest 可发现 `tests/`

- [ ] **Step 1: 添加依赖**

```powershell
cd C:\Users\29056\Documents\Codex\2026-09-09\wo-s\work\job-research-agent
python -m uv add pydantic
python -m uv add --dev pytest
```

- [ ] **Step 2: 在 `pyproject.toml` 追加 pytest 配置**

```toml
[tool.pytest.ini_options]
testpaths = ["tests"]
```

- [ ] **Step 3: 验证依赖可导入**

```powershell
.\.venv\Scripts\python.exe -c "import pydantic, pytest; print('pydantic', pydantic.__version__)"
```

Expected: `pydantic 2.x.x`

- [ ] **Step 4: Commit**

```powershell
git add pyproject.toml uv.lock
git commit -m "chore: add pydantic and pytest"
```

---

## Task 2: `config.py`

**Files:**
- Create: `src/job_research_agent/config.py`

**Interfaces:**
- Consumes: `.env`（DEEPSEEK_API_KEY、TAVILY_API_KEY）
- Produces: `DEEPSEEK_API_KEY`、`DEEPSEEK_BASE_URL`、`DEEPSEEK_MODEL`、`DEFAULT_TIMEOUT_SECONDS`、`DEFAULT_MAX_RETRIES`、`RETRY_BACKOFF_SECONDS`

- [ ] **Step 1: 创建文件**

```python
"""集中读取 .env 与默认配置。本模块不包含业务逻辑。"""

import os
from pathlib import Path

from dotenv import load_dotenv

# src/job_research_agent/config.py -> 项目根目录
PROJECT_ROOT = Path(__file__).resolve().parents[2]
load_dotenv(PROJECT_ROOT / ".env")

DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "")
DEEPSEEK_BASE_URL = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com")
DEEPSEEK_MODEL = os.getenv("DEEPSEEK_MODEL", "deepseek-chat")

DEFAULT_TIMEOUT_SECONDS = 30
DEFAULT_MAX_RETRIES = 2
RETRY_BACKOFF_SECONDS = 0.5
```

- [ ] **Step 2: 验证导入且不触发网络**

```powershell
.\.venv\Scripts\python.exe -c "from job_research_agent import config; print(config.DEEPSEEK_MODEL, config.PROJECT_ROOT)"
```

Expected: 打印 `deepseek-chat` 与项目根目录路径

- [ ] **Step 3: Commit**

```powershell
git add src/job_research_agent/config.py
git commit -m "feat: add config module"
```

---

## Task 3: `schemas.py` 核心模板

**Files:**
- Create: `src/job_research_agent/schemas.py`
- Test: `tests/test_schemas.py`

**Interfaces:**
- Consumes: pydantic
- Produces: `JobResearchInput`、`ResearchPlan`、`ReflectionDecision`、`SourceItem`

- [ ] **Step 1: 写失败测试**

```python
"""schemas 模板行为测试。"""

import pytest
from pydantic import ValidationError

from job_research_agent.schemas import (
    JobResearchInput,
    ReflectionDecision,
    ResearchPlan,
    SourceItem,
)


def test_job_research_input_accepts_valid_data():
    item = JobResearchInput(
        company="小米 AIoT Agent 实习",
        jd_text="负责 Agent 应用开发",
        profile_text="211 电子信息，Python 基础",
    )
    assert item.company == "小米 AIoT Agent 实习"
    assert item.profile_text


def test_job_research_input_requires_company_and_jd():
    with pytest.raises(ValidationError):
        JobResearchInput(company="", jd_text="")


def test_research_plan_holds_outline_and_keyword_groups():
    plan = ResearchPlan(
        topic="AI Agent 实习调研",
        outline=["岗位要求", "公司背景"],
        keyword_groups=[["AI Agent 实习 面经"], ["小米 Agent 团队"]],
    )
    assert len(plan.outline) == 2
    assert len(plan.keyword_groups) == 2


def test_reflection_decision_defaults_to_empty_lists():
    decision = ReflectionDecision(enough=False)
    assert decision.gaps == []
    assert decision.new_keywords == []


def test_source_item_requires_url():
    with pytest.raises(ValidationError):
        SourceItem(url="")
```

- [ ] **Step 2: 运行测试确认失败**

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_schemas.py -v
```

Expected: FAIL（ModuleNotFoundError / ImportError）

- [ ] **Step 3: 创建 `schemas.py`**

```python
"""全项目共用的 Pydantic 数据模板。"""

from pydantic import BaseModel, Field


class JobResearchInput(BaseModel):
    company: str = Field(..., min_length=1, description="公司/岗位名称")
    jd_text: str = Field(..., min_length=1, description="JD 全文")
    profile_text: str = Field(default="", description="个人背景简述")


class ResearchPlan(BaseModel):
    topic: str = Field(..., description="调研主题")
    outline: list[str] = Field(..., description="报告章节")
    keyword_groups: list[list[str]] = Field(..., description="分组搜索关键词")


class ReflectionDecision(BaseModel):
    enough: bool = Field(..., description="资料是否足够")
    gaps: list[str] = Field(default_factory=list, description="缺口描述")
    new_keywords: list[str] = Field(default_factory=list, description="补充关键词")


class SourceItem(BaseModel):
    url: str = Field(..., min_length=1, description="来源网址")
    title: str = Field(default="", description="标题")
    snippet: str = Field(default="", description="摘要")
```

- [ ] **Step 4: 运行测试确认通过**

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_schemas.py -v
```

Expected: 5 passed

- [ ] **Step 5: Commit**

```powershell
git add src/job_research_agent/schemas.py tests/test_schemas.py
git commit -m "feat: add schemas with validation tests"
```

---

## Task 4: `llm.py` 底层 chat + 异常与用量

**Files:**
- Create: `src/job_research_agent/llm.py`
- Test: `tests/test_llm_chat.py`

**Interfaces:**
- Consumes: `config.DEEPSEEK_API_KEY` 等
- Produces:
  - `class Usage`（prompt_tokens / completion_tokens / total_tokens）
  - `class ChatResult`（content / usage）
  - `class LLMError(Exception)`、`class LLMStructuredOutputError(LLMError)`
  - `class LLMClient`：`chat(messages, *, temperature=0.3, json_mode=False) -> ChatResult`

- [ ] **Step 1: 写失败测试（用 Fake 子类，不联网）**

```python
"""llm.chat 的重试、用量与异常行为（使用 FakeLLM，不联网）。"""

import pytest

from job_research_agent.llm import ChatResult, LLMClient, LLMError, Usage


class _FakeMessage:
    def __init__(self, content: str):
        self.content = content


class _FakeChoice:
    def __init__(self, content: str):
        self.message = _FakeMessage(content)


class _FakeUsage:
    prompt_tokens = 10
    completion_tokens = 20
    total_tokens = 30


class _FakeResponse:
    def __init__(self, content: str, usage=None):
        self.choices = [_FakeChoice(content)]
        self.usage = usage


class FakeLLM(LLMClient):
    def __init__(self, responses):
        super().__init__(api_key="fake-key", max_retries=1)
        self._responses = list(responses)
        self.calls = []

    def _post(self, messages, temperature, json_mode):
        self.calls.append((messages, json_mode))
        if not self._responses:
            raise LLMError("transport exhausted")
        return self._responses.pop(0)


def test_chat_returns_content_and_usage():
    fake = FakeLLM([_FakeResponse("hello", _FakeUsage())])
    result = fake.chat([{"role": "user", "content": "hi"}])
    assert isinstance(result, ChatResult)
    assert result.content == "hello"
    assert result.usage.total_tokens == 30


def test_chat_retries_transient_error_then_succeeds():
    responses = [None, _FakeResponse("ok")]
    fake = FakeLLM(responses)
    # 第一次 _post 抛 LLMError，第二次成功
    def flaky_post(messages, temperature, json_mode):
        if len(fake.calls) == 0:
            fake.calls.append((messages, json_mode))
            raise LLMError("temporary failure")
        fake.calls.append((messages, json_mode))
        return _FakeResponse("ok")

    fake._post = flaky_post
    result = fake.chat([{"role": "user", "content": "hi"}])
    assert result.content == "ok"


def test_chat_raises_after_retries_exhausted():
    fake = FakeLLM([])
    with pytest.raises(LLMError):
        fake.chat([{"role": "user", "content": "hi"}])
```

- [ ] **Step 2: 运行测试确认失败**

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_llm_chat.py -v
```

Expected: FAIL（ImportError / class not defined）

- [ ] **Step 3: 创建 `llm.py`（本任务先实现 chat 部分）**

```python
"""LLM 客户端封装：真实 DeepSeek 调用与离线 Mock 共用同一接口。"""

from __future__ import annotations

import json
import time
from dataclasses import dataclass
from typing import Any

from openai import OpenAI
from pydantic import BaseModel, ValidationError

from job_research_agent import config


class LLMError(RuntimeError):
    """所有 LLM 调用失败的基类。"""


class LLMStructuredOutputError(LLMError):
    """结构化输出经重试后仍然失败。"""


@dataclass
class Usage:
    prompt_tokens: int = 0
    completion_tokens: int = 0

    @property
    def total_tokens(self) -> int:
        return self.prompt_tokens + self.completion_tokens


@dataclass
class ChatResult:
    content: str
    usage: Usage | None = None


class LLMClient:
    def __init__(
        self,
        *,
        api_key: str | None = None,
        base_url: str | None = None,
        model: str | None = None,
        timeout: float | None = None,
        max_retries: int | None = None,
        retry_backoff: float | None = None,
    ) -> None:
        self.api_key = api_key or config.DEEPSEEK_API_KEY
        self.base_url = base_url or config.DEEPSEEK_BASE_URL
        self.model = model or config.DEEPSEEK_MODEL
        self.timeout = timeout or config.DEFAULT_TIMEOUT_SECONDS
        self.max_retries = (
            config.DEFAULT_MAX_RETRIES if max_retries is None else max_retries
        )
        self.retry_backoff = (
            config.RETRY_BACKOFF_SECONDS
            if retry_backoff is None
            else retry_backoff
        )
        self._openai_client: OpenAI | None = None

    def _get_client(self) -> OpenAI:
        if self._openai_client is None:
            self._openai_client = OpenAI(
                api_key=self.api_key,
                base_url=self.base_url,
                timeout=self.timeout,
            )
        return self._openai_client

    def _post(
        self, messages: list[dict[str, str]], temperature: float, json_mode: bool
    ) -> Any:
        kwargs: dict[str, Any] = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
        }
        if json_mode:
            kwargs["response_format"] = {"type": "json_object"}
        return self._get_client().chat.completions.create(**kwargs)

    def chat(
        self,
        messages: list[dict[str, str]],
        *,
        temperature: float = 0.3,
        json_mode: bool = False,
    ) -> ChatResult:
        last_error: Exception | None = None
        for attempt in range(self.max_retries + 1):
            try:
                response = self._post(messages, temperature, json_mode)
                content = response.choices[0].message.content or ""
                usage = response.usage
                if usage is not None:
                    usage_data = Usage(
                        prompt_tokens=usage.prompt_tokens,
                        completion_tokens=usage.completion_tokens,
                    )
                else:
                    usage_data = None
                return ChatResult(content=content, usage=usage_data)
            except Exception as exc:  # 网络/鉴权/超时等一律走重试
                last_error = exc
                if attempt >= self.max_retries:
                    break
                time.sleep(self.retry_backoff * (2**attempt))
        raise LLMError(f"LLM call failed after {self.max_retries + 1} attempts") from last_error
```

- [ ] **Step 4: 运行测试确认通过**

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_llm_chat.py -v
```

Expected: 3 passed

- [ ] **Step 5: Commit**

```powershell
git add src/job_research_agent/llm.py tests/test_llm_chat.py
git commit -m "feat: add LLMClient.chat with retry and usage"
```

---

## Task 5: `structured()` 结构化输出与重试

**Files:**
- Modify: `src/job_research_agent/llm.py`
- Test: `tests/test_llm_structured.py`

**Interfaces:**
- Consumes: `LLMClient.chat`
- Produces: `LLMClient.structured(output_model, *, system_prompt, user_prompt, temperature=0.3) -> BaseModel 子类实例`

- [ ] **Step 1: 写失败测试**

```python
"""structured() 的 JSON 解析、校验与重试行为。"""

import json

import pytest
from pydantic import BaseModel

from job_research_agent.llm import LLMClient, LLMStructuredOutputError


class _FakeMessage:
    def __init__(self, content: str):
        self.content = content


class _FakeChoice:
    def __init__(self, content: str):
        self.message = _FakeMessage(content)


class _FakeResponse:
    def __init__(self, content: str):
        self.choices = [_FakeChoice(content)]
        self.usage = None


class FakeStructuredLLM(LLMClient):
    def __init__(self, contents):
        super().__init__(api_key="fake-key", max_retries=2)
        self.contents = list(contents)
        self.calls = []

    def _post(self, messages, temperature, json_mode):
        self.calls.append((messages, json_mode))
        if not self.contents:
            raise LLMStructuredOutputError("exhausted")
        return _FakeResponse(self.contents.pop(0))


class KeywordPlan(BaseModel):
    keywords: list[str]


def test_structured_parses_valid_json():
    fake = FakeStructuredLLM([json.dumps({"keywords": ["a", "b"]})])
    plan = fake.structured(
        KeywordPlan,
        system_prompt="你是规划助手",
        user_prompt="生成关键词",
    )
    assert plan.keywords == ["a", "b"]
    assert len(fake.calls) == 1


def test_structured_retries_then_succeeds():
    fake = FakeStructuredLLM(["not json at all", json.dumps({"keywords": ["ok"]})])
    plan = fake.structured(
        KeywordPlan,
        system_prompt="你是规划助手",
        user_prompt="生成关键词",
    )
    assert plan.keywords == ["ok"]
    assert len(fake.calls) == 2


def test_structured_raises_after_max_retries():
    fake = FakeStructuredLLM(["bad", "bad", "bad"])
    with pytest.raises(LLMStructuredOutputError):
        fake.structured(
            KeywordPlan,
            system_prompt="你是规划助手",
            user_prompt="生成关键词",
        )
```

- [ ] **Step 2: 运行测试确认失败**

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_llm_structured.py -v
```

Expected: FAIL（LLMClient 还没有 structured 方法）

- [ ] **Step 3: 在 `llm.py` 的 `LLMClient` 类内追加方法**

```python
    def structured(
        self,
        output_model: type[BaseModel],
        *,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.3,
    ) -> BaseModel:
        messages: list[dict[str, str]] = [
            {"role": "system", "content": system_prompt},
            {
                "role": "user",
                "content": user_prompt
                + "\n\n请严格只输出合法 JSON，不要输出任何解释。",
            },
        ]
        last_error: Exception | None = None
        for attempt in range(self.max_retries + 1):
            result: ChatResult | None = None
            try:
                result = self.chat(
                    messages, temperature=temperature, json_mode=True
                )
                payload = json.loads(result.content)
                return output_model.model_validate(payload)
            except (json.JSONDecodeError, ValidationError) as exc:
                last_error = exc
                if attempt >= self.max_retries:
                    break
                messages.append({"role": "assistant", "content": result.content})
                messages.append(
                    {
                        "role": "user",
                        "content": f"你上一次输出无法通过校验：{exc}。请重新只输出合法 JSON。",
                    }
                )
            except LLMError as exc:
                last_error = exc
                break
        raise LLMStructuredOutputError(
            f"Structured output failed after {self.max_retries + 1} attempts"
        ) from last_error
```

注意：`structured` 方法需要 `import json` 与 `from pydantic import BaseModel, ValidationError`，以及 `from job_research_agent.llm import ChatResult` 位于同一模块内（已在 Task 4 定义）。

- [ ] **Step 4: 运行测试确认通过**

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_llm_structured.py -v
```

Expected: 3 passed

- [ ] **Step 5: Commit**

```powershell
git add src/job_research_agent/llm.py tests/test_llm_structured.py
git commit -m "feat: add structured output with retry and validation"
```

---

## Task 6: `MockLLM` 离线替身

**Files:**
- Modify: `src/job_research_agent/llm.py`
- Test: `tests/test_llm_mock.py`

**Interfaces:**
- Produces: `MockLLM(responses: dict[str, str], scenario: str = "default")`；记录每次调用的 messages 到 `calls`

- [ ] **Step 1: 写失败测试**

```python
"""MockLLM：无网络、无 Key 的离线替身。"""

from job_research_agent.llm import MockLLM, Usage


def test_mockllm_returns_preset_content_by_scenario():
    mock = MockLLM(
        responses={
            "default": '{"keywords": ["a"]}',
            "research": '{"keywords": ["b"]}',
        },
        scenario="research",
    )
    result = mock.chat([{"role": "user", "content": "hi"}])
    assert result.content == '{"keywords": ["b"]}'
    assert isinstance(result.usage, Usage)


def test_mockllm_records_calls():
    mock = MockLLM(responses={"default": "ok"})
    messages = [{"role": "user", "content": "hello"}]
    mock.chat(messages)
    assert len(mock.calls) == 1
    assert mock.calls[0][0]["content"] == "hello"
```

- [ ] **Step 2: 运行测试确认失败**

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_llm_mock.py -v
```

Expected: FAIL（MockLLM 不存在）

- [ ] **Step 3: 在 `llm.py` 文件末尾添加 MockLLM 类**

```python
class MockLLM(LLMClient):
    """离线替身：按 scenario 返回预设文本，不联网、不花钱。"""

    def __init__(
        self,
        responses: dict[str, str] | None = None,
        *,
        scenario: str = "default",
    ) -> None:
        super().__init__(api_key="mock-key", max_retries=0)
        self.responses = responses or {}
        self.scenario = scenario
        self.calls: list[list[dict[str, str]]] = []

    def chat(
        self,
        messages: list[dict[str, str]],
        *,
        temperature: float = 0.3,
        json_mode: bool = False,
    ) -> ChatResult:
        self.calls.append(messages)
        content = self.responses.get(self.scenario, "")
        return ChatResult(content=content, usage=Usage())
```

- [ ] **Step 4: 运行测试确认通过**

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_llm_mock.py -v
```

Expected: 2 passed

- [ ] **Step 5: Commit**

```powershell
git add src/job_research_agent/llm.py tests/test_llm_mock.py
git commit -m "feat: add MockLLM offline stand-in"
```

---

## Task 7: 全量测试 + 真实冒烟验证 + changelog

**Files:**
- Modify: `docs/changelog.md`
- Modify（验证用，不提交真实输出外的敏感内容）: `hello_llm.py` 可选保留

**Interfaces:**
- Consumes: 前面全部任务
- Produces: 全量测试通过的证据 + 一次真实 DeepSeek 调用输出

- [ ] **Step 1: 全量运行测试**

```powershell
.\.venv\Scripts\python.exe -m pytest -v
```

Expected: 全部 passed（schemas 5 + chat 3 + structured 3 + mock 2 = 13）

- [ ] **Step 2: 真实冒烟：用正式 `LLMClient` 调一次结构化输出**

在项目根目录执行（不提交该临时脚本，或用 `python -c`）：

```powershell
.\.venv\Scripts\python.exe -c "from job_research_agent.llm import LLMClient; from job_research_agent.schemas import ResearchPlan; c=LLMClient(); p=c.structured(ResearchPlan, system_prompt='你是求职调研规划助手', user_prompt='调研主题：AI Agent 实习岗位'); print(p.model_dump_json())"
```

Expected: 打印合法 JSON（ResearchPlan 结构，含 topic / outline / keyword_groups 字段）

- [ ] **Step 3: 把真实输出贴进 `docs/changelog.md`**

```markdown
## 2026-09-09（Day 2-3 里程碑验收）
- 完成：config / schemas / llm / MockLLM 四个模块，pytest 全量通过（13 passed）
- 真实验证：LLMClient.structured 返回合法 ResearchPlan JSON（粘贴真实输出）
- 说明：本行以下内容是真实命令输出，未做修改
```

- [ ] **Step 4: Commit**

```powershell
git add docs/changelog.md
git commit -m "docs: Day 2-3 LLM 里程碑验证记录"
```

---

## Self-Review 结果（写入时已完成）

- Spec 覆盖：本节对应 spec 第 5 节（config/schemas/llm）、第 7 节（结构化输出与出错阶梯）、第 10 节（Mock 测试）；无缺项
- Placeholder 扫描：无 TBD/TODO；每个代码步骤给出可直接运行的代码或命令
- 类型一致性：`LLMClient.chat` / `structured` / `MockLLM` 的签名在 Task 4-6 中保持一致；测试中 Fake 子类统一覆写 `_post`
