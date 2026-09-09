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


def _unwrap_wrapped_payload(payload: Any) -> Any:
    """部分模型会把 JSON 包在单键对象里，例如 {"research_plan": {...}}。"""
    if isinstance(payload, dict) and len(payload) == 1:
        inner = next(iter(payload.values()))
        if isinstance(inner, dict):
            return inner
    return None


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
                try:
                    return output_model.model_validate(payload)
                except ValidationError:
                    inner = _unwrap_wrapped_payload(payload)
                    if inner is not None:
                        return output_model.model_validate(inner)
                    raise
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
