"""
Abstract base class for all news fetchers.
"""

import logging
from abc import ABC, abstractmethod
from typing import List

from ai_news_daily.models import Article

logger = logging.getLogger(__name__)


class BaseFetcher(ABC):
    """All fetchers must implement fetch() and return a list of Article."""

    name: str = "base"

    @abstractmethod
    def fetch(self, query: str, max_results: int) -> List[Article]:
        ...

    def safe_fetch(self, query: str, max_results: int) -> List[Article]:
        """Wraps fetch() so a single-source failure never kills the pipeline."""
        try:
            articles = self.fetch(query, max_results)
            logger.info("[%s] fetched %d articles", self.name, len(articles))
            return articles
        except Exception as exc:
            logger.error("[%s] fetch failed: %s", self.name, exc)
            return []
