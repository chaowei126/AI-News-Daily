"""
Centralized configuration loaded from environment variables.
All secrets must be set as environment variables (or GitHub Secrets in CI).
"""

import os
import logging
from dataclasses import dataclass, field
from typing import List


# ---------------------------------------------------------------------------
# Logging setup (call once at import time)
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("news_bot.log", encoding="utf-8"),
    ],
)


def _require(key: str) -> str:
    """Read an env var; raise clearly if it is missing."""
    value = os.getenv(key)
    if not value:
        raise EnvironmentError(
            f"Required environment variable '{key}' is not set. "
            "Check your .env file or GitHub Secrets."
        )
    return value


def _optional(key: str, default: str = "") -> str:
    return os.getenv(key, default)


# ---------------------------------------------------------------------------
# Config dataclass
# ---------------------------------------------------------------------------
@dataclass
class AppConfig:
    # ── News fetching ──────────────────────────────────────────────────────
    serper_api_key: str = field(default_factory=lambda: _require("SERPER_API_KEY"))
    news_api_key: str = field(default_factory=lambda: _require("NEWS_API_KEY"))

    # Search query used for both Serper and NewsAPI
    news_query: str = field(
        default_factory=lambda: _optional(
            "NEWS_QUERY",
            "AI OR artificial intelligence OR technology OR machine learning",
        )
    )
    # Max articles to fetch per source
    max_articles_per_source: int = 15

    # ── LLM (OpenRouter) ───────────────────────────────────────────────────
    openrouter_api_key: str = field(
        default_factory=lambda: _require("OPENROUTER_API_KEY")
    )
    # Free-tier model priority list; first healthy model wins.
    # openrouter/free auto-selects from all available free models (recommended).
    # Specific models are fallbacks in case the auto-router is unavailable.
    llm_models: List[str] = field(
        default_factory=lambda: [
            "openrouter/free",
            "deepseek/deepseek-chat:free",
            "google/gemma-3-27b-it:free",
            "meta-llama/llama-3.3-70b-instruct:free",
        ]
    )
    llm_max_retries: int = 2
    # Base wait seconds between retries (exponential: base * 2^attempt)
    llm_retry_base_wait: int = 5

    # ── Email ──────────────────────────────────────────────────────────────
    smtp_server: str = field(default_factory=lambda: _optional("SMTP_SERVER", "smtp.gmail.com"))
    smtp_port: int = 587
    sender_email: str = field(default_factory=lambda: _require("EMAIL_USER"))
    sender_password: str = field(default_factory=lambda: _require("EMAIL_PASS"))
    receiver_email: str = field(
        default_factory=lambda: _optional("RECEIVER_EMAIL") or _require("EMAIL_USER")
    )
    email_subject: str = "🌐 每日 AI & 科技新闻摘要"


# Singleton – imported by all modules
config = AppConfig()
