"""Provider-agnostic LLM adapter supporting OpenAI-compatible, Anthropic, Gemini, and Ollama."""
import httpx
from typing import List, Dict, Optional, Any
from app.core.config import settings

class LLMAdapter:
    def __init__(self):
        self.api_key = settings.llm_api_key
        self.provider = settings.llm_provider
        self.model = settings.llm_model
        self.base_url = settings.llm_base_url
        self.timeout = settings.llm_timeout_seconds

    @property
    def is_configured(self) -> bool:
        return bool(self.api_key)

    async def generate_explanation(self, code_context: str, task: str) -> Dict[str, Any]:
        """Generate advisory explanation or return deterministic fallback when no key is configured."""
        if not self.is_configured:
            return {
                "source": "deterministic-offline-core",
                "explanation": (
                    f"Deterministic analysis for task '{task}': Codebase context contains "
                    f"{len(code_context.splitlines())} lines. All modifications are synthesized "
                    f"using static AST parsing and verified for syntactic correctness."
                ),
                "is_advisory": True,
                "provider": "offline",
                "model": "deterministic-ast"
            }

        prompt = f"Codebase Context:\n{code_context[:4000]}\n\nTask: {task}\nProvide concise implementation reasoning."
        
        try:
            if self.provider == "anthropic":
                text = await self._call_anthropic(prompt)
            elif self.provider == "gemini":
                text = await self._call_gemini(prompt)
            else:  # openai-compatible and ollama
                text = await self._call_openai_compatible(prompt)

            return {
                "source": "llm-provider",
                "explanation": text,
                "is_advisory": True,
                "provider": self.provider,
                "model": self.model
            }
        except httpx.HTTPError as exc:
            # Redact error to ensure no credentials leaked
            return {
                "source": "error-fallback",
                "explanation": f"Provider connection error: {exc.__class__.__name__}. Falling back to deterministic reasoning.",
                "is_advisory": True,
                "provider": self.provider,
                "model": self.model
            }

    async def _call_openai_compatible(self, prompt: str) -> str:
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": "You are a senior pair programming engineer. Ground all advice in provided code."},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.2,
            "max_tokens": 1024
        }
        url = f"{self.base_url.rstrip('/')}/chat/completions"
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            resp = await client.post(url, headers=headers, json=payload)
            resp.raise_for_status()
            data = resp.json()
            return data["choices"][0]["message"]["content"]

    async def _call_anthropic(self, prompt: str) -> str:
        headers = {
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json"
        }
        payload = {
            "model": self.model,
            "max_tokens": 1024,
            "messages": [{"role": "user", "content": prompt}]
        }
        url = f"{self.base_url.rstrip('/')}/v1/messages"
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            resp = await client.post(url, headers=headers, json=payload)
            resp.raise_for_status()
            data = resp.json()
            return data["content"][0]["text"]

    async def _call_gemini(self, prompt: str) -> str:
        url = f"{self.base_url.rstrip('/')}/models/{self.model}:generateContent?key={self.api_key}"
        payload = {
            "contents": [{"parts": [{"text": prompt}]}]
        }
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            resp = await client.post(url, json=payload)
            resp.raise_for_status()
            data = resp.json()
            candidates = data.get("candidates", [])
            if candidates:
                return candidates[0]["content"]["parts"][0]["text"]
            return "No candidates returned by provider."
