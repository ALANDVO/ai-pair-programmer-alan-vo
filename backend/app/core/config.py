"""Application configuration and environment management."""
import os
from pydantic import BaseModel, Field

class Settings(BaseModel):
    app_name: str = "ai-pair-programmer-alan-vo"
    app_version: str = "1.0.0"
    author_name: str = "Alan Vo"
    author_email: str = "alanvo@gmail.com"
    app_env: str = Field(default_factory=lambda: os.environ.get("APP_ENV", "development"))

    # LLM Settings (LLM_API_KEY is the only credential variable)
    llm_api_key: str = Field(default_factory=lambda: os.environ.get("LLM_API_KEY", ""))
    llm_provider: str = Field(default_factory=lambda: os.environ.get("LLM_PROVIDER", "openai-compatible"))
    llm_model: str = Field(default_factory=lambda: os.environ.get("LLM_MODEL", "gpt-4o"))
    llm_base_url: str = Field(default_factory=lambda: os.environ.get("LLM_BASE_URL", "https://api.openai.com/v1"))
    llm_timeout_seconds: float = 30.0

    # Auth & Demo mode settings
    auth_demo_mode: bool = Field(default_factory=lambda: os.environ.get("AUTH_DEMO_MODE", "true").lower() in ("true", "1", "yes"))
    keycloak_url: str = Field(default_factory=lambda: os.environ.get("KEYCLOAK_URL", "http://localhost:8080"))
    keycloak_realm: str = Field(default_factory=lambda: os.environ.get("KEYCLOAK_REALM", "ai-pair-programmer"))
    keycloak_client_id: str = Field(default_factory=lambda: os.environ.get("KEYCLOAK_CLIENT_ID", "pair-programmer-client"))

    # Server binding
    host: str = Field(default_factory=lambda: os.environ.get("HOST", "127.0.0.1"))
    port: int = Field(default_factory=lambda: int(os.environ.get("PORT", "8000")))

    # Safety limits
    max_context_files: int = 25
    max_file_size_bytes: int = 500_000

    @property
    def is_production(self) -> bool:
        return self.app_env.lower() == "production"

    def redacted_api_key(self) -> str:
        if not self.llm_api_key:
            return ""
        if len(self.llm_api_key) <= 8:
            return "********"
        return f"{self.llm_api_key[:3]}...{self.llm_api_key[-3:]}"

settings = Settings()
