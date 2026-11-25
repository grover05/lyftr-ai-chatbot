import os
from typing import List, Tuple
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    LLM_API_KEYS: str = "sk-placeholder-key-1,sk-placeholder-key-2"
    DATABASE_URL: str = "sqlite:///./app.db"
    ALLOWED_ORIGINS: str = "http://localhost:3000,http://127.0.0.1:3000"
    ENABLE_FAILURE_SIMULATION: bool = True
    MODEL_NAME: str = "gemini/gemini-2.0-flash"
    LITELLM_CACHE_TYPE: str = "disk"  # or "local"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    @property
    def key_pool(self) -> List[Tuple[str, str]]:
        """
        Parses LLM_API_KEYS into ordered list of (key_id, raw_key).
        e.g. [('key_1', 'sk-...'), ('key_2', 'sk-...')]
        """
        raw_keys = [k.strip() for k in self.LLM_API_KEYS.split(",") if k.strip()]
        return [(f"key_{i + 1}", key) for i, key in enumerate(raw_keys)]

    @property
    def parsed_allowed_origins(self) -> List[str]:
        return [origin.strip() for origin in self.ALLOWED_ORIGINS.split(",") if origin.strip()]


settings = Settings()
