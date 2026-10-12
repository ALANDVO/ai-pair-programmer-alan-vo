"""Unit tests for multi-provider LLM adapter and deterministic fallback."""
import asyncio
import pytest
from app.services.llm_adapter import LLMAdapter
from app.core.config import settings

def test_llm_adapter_offline_deterministic_fallback():
    adapter = LLMAdapter()
    adapter.api_key = ""  # explicitly unconfigured

    resp = asyncio.run(adapter.generate_explanation(
        code_context="def add(a, b): return a + b\n",
        task="optimize addition function"
    ))

    assert resp["source"] == "deterministic-offline-core"
    assert resp["is_advisory"] is True
    assert "deterministic" in resp["explanation"].lower()
    assert resp["provider"] == "offline"

def test_settings_key_redaction():
    s = settings
    s.llm_api_key = "sk-fake-key-for-test-123456"
    redacted = s.redacted_api_key()
    assert "..." in redacted
    s.llm_api_key = ""
    assert s.redacted_api_key() == ""
