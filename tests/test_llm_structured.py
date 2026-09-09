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


def test_structured_accepts_wrapped_json():
    fake = FakeStructuredLLM(
        [json.dumps({"research_plan": {"keywords": ["a", "b"]}})]
    )
    plan = fake.structured(
        KeywordPlan,
        system_prompt="你是规划助手",
        user_prompt="生成关键词",
    )
    assert plan.keywords == ["a", "b"]
    assert len(fake.calls) == 1


def test_structured_user_prompt_includes_json_schema():
    fake = FakeStructuredLLM([json.dumps({"keywords": ["a"]})])
    fake.structured(
        KeywordPlan,
        system_prompt="你是规划助手",
        user_prompt="生成关键词",
    )
    first_user = fake.calls[0][0][-1]["content"]
    assert '"keywords"' in first_user
    assert "JSON Schema" in first_user


def test_structured_raises_after_max_retries():
    fake = FakeStructuredLLM(["bad", "bad", "bad"])
    with pytest.raises(LLMStructuredOutputError):
        fake.structured(
            KeywordPlan,
            system_prompt="你是规划助手",
            user_prompt="生成关键词",
        )
