"""
main.py – entry point for AI-News-Daily.

Run locally:
    python main.py

Or via GitHub Actions (see .github/workflows/daily_news.yml).
"""

import logging
import sys

# Ensure the src/ package tree is importable when running from project root
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from ai_news_daily.fetcher import aggregate_news
from ai_news_daily.summarizer import summarize
from ai_news_daily.notifier import send_email

logger = logging.getLogger(__name__)


def run() -> None:
    logger.info("=== AI-News-Daily pipeline started ===")

    # 1. Fetch
    articles = aggregate_news()
    if not articles:
        logger.warning("No articles fetched – aborting pipeline.")
        sys.exit(1)

    # 2. Summarise
    digest_html = summarize(articles)
    logger.info("Summary generated (%d chars)", len(digest_html))

    # 3. Notify
    send_email(digest_html)

    logger.info("=== Pipeline finished successfully ===")


if __name__ == "__main__":
    try:
        run()
    except Exception as exc:
        logger.error("Fatal error: %s", exc, exc_info=True)
        sys.exit(1)
