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
