import pytest
import requests
from hw4_tourguide.tools.llm_client import MockLLMClient, llm_factory, LLMError, LLMClient


@pytest.mark.unit
def test_mock_llm_client():
    client = MockLLMClient(timeout=0.1, max_retries=1)
    resp = client.query("hello")
    assert "text" in resp
    assert "usage" in resp


@pytest.mark.unit
def test_llm_factory_defaults_to_mock():
    cfg = {"llm_provider": "mock", "llm_timeout": 0.1}
    client = llm_factory(cfg, lambda k: None)
    resp = client.query("test")
    assert resp["text"]


@pytest.mark.unit
def test_llm_retry_and_timeout():
    class SlowClient(MockLLMClient):
        def _call(self, prompt: str):
            import time
            time.sleep(0.2)
            return super()._call(prompt)
    c = SlowClient(timeout=0.05, max_retries=2)
    with pytest.raises(LLMError):
        c.query("slow")


@pytest.mark.unit
def test_llm_budget_guard():
    client = MockLLMClient(timeout=0.1, max_retries=1, max_prompt_chars=10)
    resp = client.query("0123456789abcdefgh")
    assert resp["text"]


@pytest.mark.unit
def test_llm_factory_budget_guard():
    client = llm_factory({"llm_provider": "mock", "llm_timeout": 0.1, "llm_max_tokens": 5}, lambda k: None)
    with pytest.raises(LLMError):
        client.query("x" * 200)  # exceeds token budget


@pytest.mark.unit
def test_llm_factory_openai_call(monkeypatch):
    def fake_post(url, json=None, headers=None, timeout=None):
        class _Resp:
            def raise_for_status(self): return None
            def json(self):
                return {"choices":[{"message":{"content":"hi"}}],"usage":{"prompt_tokens":1,"completion_tokens":1}}
        return _Resp()
    monkeypatch.setattr(requests, "post", fake_post)
    client = llm_factory({"llm_provider": "openai", "llm_timeout": 0.1, "llm_model": "gpt-4o-mini"}, lambda k: "key")
    res = client.query("hello")
    assert "text" in res


@pytest.mark.unit
def test_llm_factory_claude_call(monkeypatch):
    def fake_post(url, headers=None, json=None, timeout=None):
        class _Resp:
            def raise_for_status(self): return None
            def json(self):
                return {"content":[{"text":"hello"}], "usage":{"input_tokens":1,"output_tokens":1}}
        return _Resp()
    monkeypatch.setattr(requests, "post", fake_post)
    client = llm_factory({"llm_provider": "claude", "llm_timeout": 0.1, "llm_model": "claude-3-haiku"}, lambda k: "key")
    res = client.query("hello")
    assert "text" in res


@pytest.mark.unit
def test_llm_factory_gemini_call(monkeypatch):
    def fake_post(url, params=None, json=None, timeout=None):
        class _Resp:
            def raise_for_status(self): return None
            def json(self):
                return {"candidates":[{"content":{"parts":[{"text":"hi"}]}}], "usageMetadata":{"promptTokenCount":1,"candidatesTokenCount":1}}
        return _Resp()
    monkeypatch.setattr(requests, "post", fake_post)
    client = llm_factory({"llm_provider": "gemini", "llm_timeout": 0.1, "llm_model": "gemini-1.5-flash"}, lambda k: "key")
    res = client.query("hello")
    assert "text" in res


@pytest.mark.unit
def test_llm_factory_ollama_call(monkeypatch):
    def fake_post(url, json=None, timeout=None):
        class _Resp:
            def raise_for_status(self): return None
            def json(self):
                return {"response": "hi"}
        return _Resp()
    monkeypatch.setattr(requests, "post", fake_post)
    client = llm_factory({"llm_provider": "ollama", "llm_timeout": 0.1, "llm_model": "llama3"}, lambda k: None)
    res = client.query("hello")
    assert "text" in res


@pytest.mark.unit
def test_llm_factory_auto_selection(monkeypatch):
    """
    Test the 'auto' LLM provider selection logic: claude > openai > gemini > ollama > mock.
    We mock the environment variable retrieval for API keys.
    For this test, we simplify Ollama's availability to be dependent on 'ollama_host' in config.
    """
    config_base = {"llm_provider": "auto", "llm_timeout": 0.1}

    # Helper to mock the 'secrets' callable
    class MockSecrets:
        def __init__(self, env_vars: Dict[str, str]):
            self.env_vars = env_vars
        def __call__(self, key: str) -> Optional[str]:
            return self.env_vars.get(key)

    # Scenario 1: Only Anthropic (Claude) key exists
    secrets_mock = MockSecrets({"ANTHROPIC_API_KEY": "fake_key"})
    client = llm_factory(config_base, secrets_mock)
    assert client.__class__.__name__ == "ClaudeClient"

    # Scenario 2: Only OpenAI key exists
    secrets_mock = MockSecrets({"OPENAI_API_KEY": "fake_key"})
    client = llm_factory(config_base, secrets_mock)
    assert client.__class__.__name__ == "OpenAIClient"

    # Scenario 3: Only Gemini key exists
    secrets_mock = MockSecrets({"GEMINI_API_KEY": "fake_key"})
    client = llm_factory(config_base, secrets_mock)
    assert client.__class__.__name__ == "GeminiClient"

    # Scenario 4: Only Ollama host configured
    secrets_mock = MockSecrets({}) # No API keys
    config_ollama = {"llm_provider": "auto", "llm_timeout": 0.1, "ollama_host": "http://localhost:11434"}
    client = llm_factory(config_ollama, secrets_mock)
    assert client.__class__.__name__ == "OllamaClient"

    # Scenario 5: No API keys, no Ollama host -> should fallback to MockLLMClient
    secrets_mock = MockSecrets({})
    client = llm_factory(config_base, secrets_mock)
    assert isinstance(client, MockLLMClient)

    # Scenario 6: Explicitly set to mock, even if keys exist
    secrets_mock = MockSecrets({"ANTHROPIC_API_KEY": "fake_key"})
    client = llm_factory({"llm_provider": "mock", "llm_timeout": 0.1}, secrets_mock)
    assert isinstance(client, MockLLMClient)
