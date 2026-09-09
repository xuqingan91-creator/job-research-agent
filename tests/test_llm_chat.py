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
    fake = FakeLLM([])

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
