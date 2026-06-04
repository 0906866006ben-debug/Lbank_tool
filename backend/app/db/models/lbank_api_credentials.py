"""Credential storage record (read-only usage only).

SECURITY:
  - The API secret is NEVER returned by any route or serializer. The
    `to_public_dict()` helper is the only sanctioned way to surface a
    credential record, and it omits the secret entirely.
  - The key MUST be configured as read-only on LBank. This app performs no
    trading or withdrawal calls regardless of key permissions.
  - Storing the secret in a DB is optional; the first-version main line
    keeps it in the backend .env only. This table exists so multiple
    read-only accounts can be referenced by label without exposing secrets.
"""
from __future__ import annotations

from sqlalchemy import Boolean, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.database import Base


class LbankApiCredential(Base):
    __tablename__ = "lbank_api_credentials"

    account_id: Mapped[str] = mapped_column(String, primary_key=True)
    api_key: Mapped[str] = mapped_column(String, nullable=False)
    # Secret column kept private. Never serialized outward.
    api_secret: Mapped[str] = mapped_column(String, nullable=False)
    read_only: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    def to_public_dict(self) -> dict:
        """The only sanctioned outward representation — no secret, no key."""
        return {
            "account_id": self.account_id,
            "read_only": self.read_only,
            # api_key/api_secret deliberately omitted.
        }
