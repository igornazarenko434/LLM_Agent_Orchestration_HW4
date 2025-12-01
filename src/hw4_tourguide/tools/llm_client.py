"""
LLM client abstraction (Mission M7.7b).
Provides a unified interface for multiple providers with timeouts, retries,
redacted logging, and cost-awareness hooks.
"""

import time
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, Callable
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeout

from hw4_tourguide.logger import get_logger


class LLMError(RuntimeError):
    pass


class LLMClient(ABC):
    def __init__(self, timeout: float = 30.0, max_retries: int = 3, backoff: str = "exponential", max_prompt_chars: int = 4000, max_tokens: Optional[int] = None):
        self.timeout = timeout
        self.max_retries = max_retries
        self.backoff = backoff
        self.max_prompt_chars = max_prompt_chars
        self.max_tokens = max_tokens
        self.tokens_used = 0
        self.logger = get_logger("llm")

    @abstractmethod
    def _call(self, prompt: str) -> Dict[str, Any]:
        """Provider-specific call. Returns dict with 'text' and optional 'usage'."""
        raise NotImplementedError

    def query(self, prompt: str) -> Dict[str, Any]:
        """Call the provider with retries and timeout."""
        if self.max_tokens is not None and self.tokens_used >= self.max_tokens:
            raise LLMError("LLM token budget exceeded")
        if len(prompt) > self.max_prompt_chars:
            prompt = prompt[: self.max_prompt_chars]
        last_exc: Optional[Exception] = None
        for attempt in range(self.max_retries):
            start = time.time()
            try:
                with ThreadPoolExecutor(max_workers=1) as ex:
                    fut = ex.submit(self._call, prompt)
                    result = fut.result(timeout=self.timeout)
                usage = result.get("usage", {})
                prompt_tokens = usage.get("prompt_tokens", 0) if isinstance(usage, dict) else 0
                completion_tokens = usage.get("completion_tokens", 0) if isinstance(usage, dict) else 0
                if self.max_tokens is not None:
                    self.tokens_used += prompt_tokens + completion_tokens
                    if self.tokens_used > self.max_tokens:
                        raise LLMError("LLM token budget exceeded")
                duration_ms = (time.time() - start) * 1000
                self.logger.info(
                    f"LLM | provider={self.__class__.__name__} | ms={duration_ms:.1f} | prompt_len={len(prompt)} | tokens_used={self.tokens_used}",
                    extra={"event_tag": "LLM"},
                )
                return result
            except FuturesTimeout as exc:
                last_exc = exc
                self.logger.warning(
                    f"LLM TIMEOUT | provider={self.__class__.__name__} | attempt={attempt+1}/{self.max_retries} | timeout={self.timeout}s",
                    extra={"event_tag": "LLM"},
                )
            except Exception as exc:
                last_exc = exc
                self.logger.warning(
                    f"LLM ERROR | provider={self.__class__.__name__} | attempt={attempt+1}/{self.max_retries} | error={exc}",
                    extra={"event_tag": "LLM"},
                )
            if attempt < self.max_retries - 1:
                delay = self._compute_backoff(attempt)
                time.sleep(delay)
        raise LLMError(f"LLM call failed after retries: {last_exc}")

    def _compute_backoff(self, attempt: int) -> float:
        if self.backoff == "linear":
            return min(self.timeout, 1.0 * (attempt + 1))
        return min(self.timeout, 0.5 * (2 ** attempt))


class MockLLMClient(LLMClient):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def _call(self, prompt: str) -> Dict[str, Any]:
        return {"text": "Mock response", "usage": {"prompt_tokens": len(prompt)//4, "completion_tokens": 10}}


class OllamaClient(LLMClient):
    def __init__(self, model: str = "llama3", host: str = "http://localhost:11434", **kwargs):
        super().__init__(**kwargs)
        self.model = model
        self.host = host

    def _call(self, prompt: str) -> Dict[str, Any]:
        import requests
        resp = requests.post(f"{self.host}/api/generate", json={"model": self.model, "prompt": prompt}, timeout=self.timeout)
        resp.raise_for_status()
        data = resp.json()
        return {"text": data.get("response", ""), "usage": {}}


class OpenAIClient(LLMClient):
    def __init__(self, api_key: str, model: str = "gpt-4o-mini", **kwargs):
        super().__init__(**kwargs)
        self.api_key = api_key
        self.model = model

    def _call(self, prompt: str) -> Dict[str, Any]:
        import requests
        headers = {"Authorization": f"Bearer {self.api_key}"}
        payload = {"model": self.model, "messages": [{"role": "user", "content": prompt}]}
        resp = requests.post("https://api.openai.com/v1/chat/completions", json=payload, headers=headers, timeout=self.timeout)
        resp.raise_for_status()
        data = resp.json()
        text = data.get("choices", [{}])[0].get("message", {}).get("content", "")
        usage = data.get("usage", {})
        return {"text": text, "usage": usage}


class ClaudeClient(LLMClient):
    def __init__(self, api_key: str, model: str = "claude-3-haiku-20240307", **kwargs):
        super().__init__(**kwargs)
        self.api_key = api_key
        self.model = model

    def _call(self, prompt: str) -> Dict[str, Any]:
        import requests
        headers = {
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        }
        payload = {"model": self.model, "max_tokens": 256, "messages": [{"role": "user", "content": prompt}]}
        resp = requests.post("https://api.anthropic.com/v1/messages", json=payload, headers=headers, timeout=self.timeout)
        resp.raise_for_status()
        data = resp.json()
        text = ""
        try:
            text = data.get("content", [{}])[0].get("text", "")
        except Exception:
            pass
        usage = data.get("usage", {})
        return {"text": text, "usage": usage}


class GeminiClient(LLMClient):
    def __init__(self, api_key: str, model: str = "gemini-2.5-flash", **kwargs):
        super().__init__(**kwargs)
        self.api_key = api_key
        self.model = model

    def _call(self, prompt: str) -> Dict[str, Any]:
        import requests
        params = {"key": self.api_key}
        payload = {"contents": [{"parts": [{"text": prompt}]}]}
        # Use v1 endpoint with gemini-2.5-flash model (latest stable as of June 2025)
        url = f"https://generativelanguage.googleapis.com/v1/models/{self.model}:generateContent"
        resp = requests.post(url, json=payload, params=params, timeout=self.timeout)
        resp.raise_for_status()
        data = resp.json()
        text = ""
        try:
            text = data.get("candidates", [{}])[0].get("content", {}).get("parts", [{}])[0].get("text", "")
        except Exception:
            pass
        return {"text": text, "usage": {}}


def llm_factory(config: Dict[str, Any], secrets: Callable[[str], Optional[str]]) -> LLMClient:
    provider = (config.get("llm_provider") or config.get("provider") or "auto").lower()
    timeout = float(config.get("llm_timeout", config.get("llm_query_timeout", config.get("timeout", 30.0))))
    retries = int(config.get("llm_retries", config.get("retries", 3)))
    backoff = config.get("llm_backoff", config.get("backoff", "exponential"))
    max_prompt_chars = int(config.get("llm_max_prompt_chars", 4000))
    max_tokens = config.get("llm_max_tokens", None)

    # Auto selection priority: claude > openai > gemini > ollama > mock
    if provider == "auto":
        if secrets("ANTHROPIC_API_KEY"):
            provider = "claude"
        elif secrets("OPENAI_API_KEY"):
            provider = "openai"
        elif secrets("GEMINI_API_KEY"):
            provider = "gemini"
        elif config.get("ollama_host"):
            provider = "ollama"
        else:
            provider = "mock"

    if provider == "ollama":
        return OllamaClient(model=config.get("llm_model", "llama3.1:8b"), host=config.get("ollama_host", "http://localhost:11434"), timeout=timeout, max_retries=retries, backoff=backoff, max_prompt_chars=max_prompt_chars, max_tokens=max_tokens)
    if provider == "openai":
        key = secrets("OPENAI_API_KEY")
        if not key:
            return MockLLMClient(timeout=timeout, max_retries=retries, backoff=backoff, max_prompt_chars=max_prompt_chars, max_tokens=max_tokens)
        return OpenAIClient(api_key=key, model=config.get("llm_model", "gpt-4o-mini"), timeout=timeout, max_retries=retries, backoff=backoff, max_prompt_chars=max_prompt_chars, max_tokens=max_tokens)
    if provider == "claude":
        key = secrets("ANTHROPIC_API_KEY")
        if not key:
            return MockLLMClient(timeout=timeout, max_retries=retries, backoff=backoff, max_prompt_chars=max_prompt_chars, max_tokens=max_tokens)
        return ClaudeClient(api_key=key, model=config.get("llm_model", "claude-3-haiku-20240307"), timeout=timeout, max_retries=retries, backoff=backoff, max_prompt_chars=max_prompt_chars, max_tokens=max_tokens)
    if provider == "gemini":
        key = secrets("GEMINI_API_KEY")
        if not key:
            return MockLLMClient(timeout=timeout, max_retries=retries, backoff=backoff, max_prompt_chars=max_prompt_chars, max_tokens=max_tokens)
        return GeminiClient(api_key=key, model=config.get("llm_model", "gemini-2.5-flash"), timeout=timeout, max_retries=retries, backoff=backoff, max_prompt_chars=max_prompt_chars, max_tokens=max_tokens)
    return MockLLMClient(timeout=timeout, max_retries=retries, backoff=backoff, max_prompt_chars=max_prompt_chars, max_tokens=max_tokens)
