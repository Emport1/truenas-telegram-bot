from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    telegram_token: str
    allowed_user_ids: frozenset[int]
    x_auth_token: str
    x_ct0: str
    x_max_replies: int = 5000
    x_account_db: str = "/tmp/accounts.db"

    @classmethod
    def from_env(cls) -> "Settings":
        required = ("TELEGRAM_BOT_TOKEN", "TELEGRAM_ALLOWED_USER_IDS", "X_AUTH_TOKEN", "X_CT0")
        missing = [name for name in required if not os.environ.get(name, "").strip()]
        if missing:
            raise RuntimeError(f"Missing required environment variables: {', '.join(missing)}")
        try:
            users = frozenset(int(x.strip()) for x in os.environ["TELEGRAM_ALLOWED_USER_IDS"].split(",") if x.strip())
        except ValueError as exc:
            raise RuntimeError("TELEGRAM_ALLOWED_USER_IDS must contain numeric IDs") from exc
        if not users:
            raise RuntimeError("At least one Telegram user ID must be allowed")
        return cls(
            telegram_token=os.environ["TELEGRAM_BOT_TOKEN"],
            allowed_user_ids=users,
            x_auth_token=os.environ["X_AUTH_TOKEN"],
            x_ct0=os.environ["X_CT0"],
            x_max_replies=int(os.getenv("X_MAX_REPLIES", "5000")),
            x_account_db=os.getenv("X_ACCOUNT_DB", "/tmp/accounts.db"),
        )
