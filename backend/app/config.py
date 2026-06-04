"""Application settings, loaded from environment / .env.

Security note: `LBANK_API_SECRET` is loaded here but MUST NEVER be
serialized into any response, log line, or error message. Helpers that
expose settings always exclude it.
"""
from __future__ import annotations

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(".env", "../.env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # First-version main line. Real endpoints are NOT verified yet, so the
    # default is mock mode.
    mock_mode: bool = Field(default=True, alias="LBANK_WIDGET_MOCK_MODE")

    api_key: str = Field(default="", alias="LBANK_API_KEY")
    # Backend-only. Never expose.
    api_secret: str = Field(default="", alias="LBANK_API_SECRET")

    signature_method: str = Field(default="HmacSHA256", alias="LBANK_SIGNATURE_METHOD")
    base_url: str = Field(default="https://lbkperp.lbank.com/", alias="LBANK_BASE_URL")

    db_url: str = Field(default="sqlite:///./lbank_widget.db", alias="LBANK_DB_URL")

    def public_dict(self) -> dict:
        """Safe-to-expose subset. Deliberately omits api_secret (and key)."""
        return {
            "mock_mode": self.mock_mode,
            "signature_method": self.signature_method,
            "base_url": self.base_url,
        }


@lru_cache
def get_settings() -> Settings:
    return Settings()
