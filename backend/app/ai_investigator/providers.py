"""
Provider-agnostic LLM adapter layer.

The rest of the app (ai_investigator/investigator.py) only ever calls
`get_provider().generate(system_prompt, user_prompt)`. Which actual API
gets hit is decided purely by the LLM_PROVIDER env var, so swapping
OpenAI <-> Anthropic <-> another OpenAI-compatible provider requires
ZERO changes to investigation logic.

Configure via environment variables (see .env.example):
  LLM_PROVIDER=anthropic|openai|none
  LLM_API_KEY=...
  LLM_MODEL=...            (optional, sensible default per provider)
  LLM_BASE_URL=...         (optional, for OpenAI-compatible self-hosted/proxy endpoints)
"""
import os
import abc
import httpx


class LLMProvider(abc.ABC):
    @abc.abstractmethod
    def generate(self, system_prompt: str, user_prompt: str) -> str:
        ...


class AnthropicProvider(LLMProvider):
    def __init__(self, api_key: str, model: str = None):
        self.api_key = api_key
        self.model = model or "claude-sonnet-5"
        self.base_url = os.getenv("LLM_BASE_URL", "https://api.anthropic.com/v1/messages")

    def generate(self, system_prompt: str, user_prompt: str) -> str:
        headers = {
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        }
        payload = {
            "model": self.model,
            "max_tokens": 800,
            "system": system_prompt,
            "messages": [{"role": "user", "content": user_prompt}],
        }
        with httpx.Client(timeout=30) as client:
            resp = client.post(self.base_url, headers=headers, json=payload)
            resp.raise_for_status()
            data = resp.json()
        blocks = data.get("content", [])
        return "".join(b.get("text", "") for b in blocks if b.get("type") == "text")


class OpenAIProvider(LLMProvider):
    def __init__(self, api_key: str, model: str = None):
        self.api_key = api_key
        self.model = model or "gpt-4o-mini"
        self.base_url = os.getenv("LLM_BASE_URL", "https://api.openai.com/v1/chat/completions")

    def generate(self, system_prompt: str, user_prompt: str) -> str:
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": self.model,
            "max_tokens": 800,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        }
        with httpx.Client(timeout=30) as client:
            resp = client.post(self.base_url, headers=headers, json=payload)
            resp.raise_for_status()
            data = resp.json()
        return data["choices"][0]["message"]["content"]


class NoOpProvider(LLMProvider):
    """Used when no LLM key is configured. Lets the rest of the pipeline
    (ML detection, risk scoring, evidence) work fully; the AI Investigator
    layer degrades to a clearly-labeled rule-based explanation instead of
    failing the whole request."""

    def generate(self, system_prompt: str, user_prompt: str) -> str:
        raise RuntimeError("No LLM provider configured")


_provider_instance = None


def get_provider() -> LLMProvider:
    global _provider_instance
    if _provider_instance is not None:
        return _provider_instance

    provider_name = os.getenv("LLM_PROVIDER", "none").lower()
    api_key = os.getenv("LLM_API_KEY", "")
    model = os.getenv("LLM_MODEL")

    if provider_name == "anthropic" and api_key:
        _provider_instance = AnthropicProvider(api_key, model)
    elif provider_name == "openai" and api_key:
        _provider_instance = OpenAIProvider(api_key, model)
    else:
        _provider_instance = NoOpProvider()

    return _provider_instance
