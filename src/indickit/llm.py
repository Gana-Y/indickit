"""Minimal, dependency-free model clients for the benchmark."""
from __future__ import annotations

import json
import os
import time
import urllib.error
import urllib.request
from typing import Any, Dict, Optional


class ProviderError(RuntimeError):
    pass


def _post(url: str, headers: Dict[str, str], body: Dict[str, Any], timeout: float = 90, retries: int = 3) -> Dict[str, Any]:
    data = json.dumps(body).encode()
    delay, last = 1.5, None
    for attempt in range(retries):
        req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json", **headers})
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                return json.loads(resp.read().decode())
        except urllib.error.HTTPError as exc:
            last = ProviderError(f"HTTP {exc.code}: {exc.read().decode('utf-8', 'replace')[:300]}")
            if exc.code not in (408, 429, 500, 502, 503, 504):
                raise last from None
        except (urllib.error.URLError, TimeoutError) as exc:
            last = ProviderError(f"network error: {exc}")
        if attempt < retries - 1:
            time.sleep(delay)
            delay *= 2
    raise last  # type: ignore[misc]


class OpenAICompatible:
    """OpenAI, Ollama, Groq, OpenRouter, Gemini (OpenAI endpoint), vLLM, LM Studio ..."""

    def __init__(self, model: str, base_url: str = "https://api.openai.com/v1", api_key_env: str = "OPENAI_API_KEY", temperature: float = 0.0):
        self.model, self.base_url, self.api_key_env, self.temperature = model, base_url.rstrip("/"), api_key_env, temperature
        self.name = model

    def complete(self, prompt: str, task=None) -> str:
        key = os.environ.get(self.api_key_env, "")
        headers = {"Authorization": f"Bearer {key}"} if key else {}
        data = _post(
            f"{self.base_url}/chat/completions", headers,
            {"model": self.model, "temperature": self.temperature, "messages": [{"role": "user", "content": prompt}]},
        )
        try:
            return data["choices"][0]["message"]["content"] or ""
        except (KeyError, IndexError, TypeError):
            raise ProviderError(f"unexpected response: {str(data)[:200]}") from None


class Anthropic:
    def __init__(self, model: str, base_url: str = "https://api.anthropic.com", temperature: float = 0.0):
        self.model, self.base_url, self.temperature = model, base_url.rstrip("/"), temperature
        self.name = model

    def complete(self, prompt: str, task=None) -> str:
        key = os.environ.get("ANTHROPIC_API_KEY", "")
        data = _post(
            f"{self.base_url}/v1/messages", {"x-api-key": key, "anthropic-version": "2023-06-01"},
            {"model": self.model, "max_tokens": 512, "temperature": self.temperature,
             "messages": [{"role": "user", "content": prompt}]},
        )
        try:
            return "".join(b.get("text", "") for b in data["content"] if b.get("type") == "text")
        except (KeyError, TypeError):
            raise ProviderError(f"unexpected response: {str(data)[:200]}") from None


class Oracle:
    """Always answers correctly (returns the reference). Sanity-checks the harness; upper bound."""

    name = "mock-oracle"

    def complete(self, prompt: str, task=None) -> str:
        if task is None:
            return "ok"
        if task.reference is not None:
            return task.reference
        from .corpus import PARALLEL

        return PARALLEL[task.lang][1]   # free-form "respond" task: any sentence in the right script


class Echo:
    """Repeats the prompt. A trivial lower-bound baseline."""

    name = "mock-echo"

    def complete(self, prompt: str, task=None) -> str:
        return prompt


PRESETS = {
    "openai": ("https://api.openai.com/v1", "OPENAI_API_KEY"),
    "groq": ("https://api.groq.com/openai/v1", "GROQ_API_KEY"),
    "openrouter": ("https://openrouter.ai/api/v1", "OPENROUTER_API_KEY"),
    "gemini": ("https://generativelanguage.googleapis.com/v1beta/openai", "GEMINI_API_KEY"),
    "ollama": ("http://localhost:11434/v1", "OLLAMA_API_KEY"),
}


def make_provider(provider: str, model: Optional[str] = None, base_url: Optional[str] = None):
    if provider == "mock-oracle":
        return Oracle()
    if provider == "mock-echo":
        return Echo()
    if not model:
        raise ValueError("--model is required")
    if provider == "anthropic":
        return Anthropic(model, base_url or "https://api.anthropic.com")
    if provider in PRESETS or base_url:
        url, env = PRESETS.get(provider, (base_url, "OPENAI_API_KEY"))
        return OpenAICompatible(model, base_url or url, env)
    raise ValueError(f"unknown provider {provider!r}; use one of {sorted(PRESETS)}, anthropic, or --base-url")
