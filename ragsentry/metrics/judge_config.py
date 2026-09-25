from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any
from pydantic import BaseModel, Field


PROVIDER_PRESETS: dict[str, dict[str, Any]] = {
    "openai": {
        "model": "gpt-4o-mini",
        "api_base": None,
        "api_key_env": "OPENAI_API_KEY",
    },
    "anthropic": {
        "model": "claude-3-5-haiku-latest",
        "api_base": None,
        "api_key_env": "ANTHROPIC_API_KEY",
    },
    "gemini": {
        "model": "gemini-1.5-flash",
        "api_base": "https://generativelanguage.googleapis.com/v1beta/openai/",
        "api_key_env": "GEMINI_API_KEY",
        "fallback_env": "GOOGLE_API_KEY",
    },
    "groq": {
        "model": "llama-3.1-8b-instant",
        "api_base": "https://api.groq.com/openai/v1",
        "api_key_env": "GROQ_API_KEY",
    },
    "xai": {
        "model": "grok-2-latest",
        "api_base": "https://api.x.ai/v1",
        "api_key_env": "XAI_API_KEY",
    },
    "ollama": {
        "model": "llama3.2",
        "api_base": "http://localhost:11434/v1",
        "api_key": "ollama",
        "api_key_env": "OLLAMA_API_KEY",
    },
    "local": {
        "model": "local-model",
        "api_base": "http://localhost:8000/v1",
        "api_key": "dummy",
        "api_key_env": "LOCAL_API_KEY",
    },
    "openrouter": {
        "model": "openai/gpt-4o-mini",
        "api_base": "https://openrouter.ai/api/v1",
        "api_key_env": "OPENROUTER_API_KEY",
    },
    "deepseek": {
        "model": "deepseek-chat",
        "api_base": "https://api.deepseek.com/v1",
        "api_key_env": "DEEPSEEK_API_KEY",
    },
}


class JudgeConfig(BaseModel):
    """Configuration for the evaluation judge LLM."""
    provider: str = "openai"
    model: str = "gpt-4o-mini"
    api_base: str | None = None
    api_key: str | None = None
    api_key_env: str = "OPENAI_API_KEY"
    temperature: float = 0.0
    extra_params: dict[str, Any] = Field(default_factory=dict)

    @classmethod
    def create(
        cls,
        provider: str | None = None,
        model: str | None = None,
        api_base: str | None = None,
        api_key: str | None = None,
    ) -> JudgeConfig:
        """Create configuration with smart provider presets and auto-detection."""
        prov = (provider or "").lower().strip()

        # Auto-detect provider if not explicitly given
        if not prov:
            if model:
                m_low = model.lower()
                if "claude" in m_low:
                    prov = "anthropic"
                elif "gemini" in m_low:
                    prov = "gemini"
                elif "grok" in m_low:
                    prov = "xai"
                elif "deepseek" in m_low:
                    prov = "deepseek"
                elif "llama" in m_low:
                    if os.environ.get("GROQ_API_KEY"):
                        prov = "groq"
                    else:
                        prov = "ollama"
            elif api_key:
                if api_key.startswith("xai-"):
                    prov = "xai"
                elif api_key.startswith("gsk_"):
                    prov = "groq"
                elif api_key.startswith("sk-ant-"):
                    prov = "anthropic"
                elif api_key.startswith("sk-or-"):
                    prov = "openrouter"
                elif api_key.startswith("AIza"):
                    prov = "gemini"

        if not prov:
            # Check environment variables in priority order
            groq_val = os.environ.get("GROQ_API_KEY", "")
            if groq_val.startswith("xai-") or os.environ.get("XAI_API_KEY"):
                prov = "xai"
            elif os.environ.get("ANTHROPIC_API_KEY"):
                prov = "anthropic"
            elif os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY"):
                prov = "gemini"
            elif groq_val:
                prov = "groq"
            elif os.environ.get("DEEPSEEK_API_KEY"):
                prov = "deepseek"
            elif os.environ.get("OPENROUTER_API_KEY"):
                prov = "openrouter"
            else:
                prov = "openai"

        preset = PROVIDER_PRESETS.get(prov, PROVIDER_PRESETS["openai"])

        chosen_model = model or preset.get("model", "gpt-4o-mini")
        chosen_base = api_base if api_base is not None else preset.get("api_base")
        chosen_key_env = preset.get("api_key_env", "OPENAI_API_KEY")
        chosen_key = api_key or preset.get("api_key")

        return cls(
            provider=prov,
            model=chosen_model,
            api_base=chosen_base,
            api_key=chosen_key,
            api_key_env=chosen_key_env,
        )

    def get_api_key(self) -> str:
        """Resolve API key from explicit value or environment variable."""
        if self.api_key:
            return self.api_key

        key = os.environ.get(self.api_key_env)

        # Fallback aliases
        if not key and self.provider == "gemini":
            key = os.environ.get("GOOGLE_API_KEY")
        if not key and self.provider == "xai":
            groq_val = os.environ.get("GROQ_API_KEY", "")
            if groq_val.startswith("xai-"):
                key = groq_val

        if not key:
            raise ValueError(
                f"No API key provided for provider '{self.provider}'. "
                f"Please set environment variable '{self.api_key_env}' or pass --api-key."
            )
        return key

    @classmethod
    def from_file(cls, path: str | Path) -> JudgeConfig:
        """Load configuration from a JSON file."""
        config_path = Path(path)
        if not config_path.exists():
            raise FileNotFoundError(f"Judge config file not found: {config_path}")
        with open(config_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        prov = data.get("provider", "").lower()
        if prov and prov in PROVIDER_PRESETS:
            preset = dict(PROVIDER_PRESETS[prov])
            preset.update(data)
            data = preset

        return cls(**data)