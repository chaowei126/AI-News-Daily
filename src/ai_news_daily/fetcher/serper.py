"""
Fetcher backed by the Serper Google News API.
Docs: https://serper.dev/
Endpoint: POST https://google.serper.dev/news
"""

import logging
from typing import List

import requests

from ai_news_daily.config import config
from ai_news_daily.fetcher.base import BaseFetcher
from ai_news_daily.models import Article

logger = logging.getLogger(__name__)

_ENDPOINT = "https://google.serper.dev/news"
_TIMEOUT = 15  # seconds


class SerperFetcher(BaseFetcher):
    name = "serper"

    def fetch(self, query: str, max_results: int) -> List[Article]:
        headers = {
            "X-API-KEY": config.serper_api_key,
            "Content-Type": "application/json",
        }
        payload = {
            "q": query,
            "num": max_results,
            "hl": "en",   # response language hint
            "gl": "us",   # geo location hint
        }

        response = requests.post(
            _ENDPOINT, headers=headers, json=payload, timeout=_TIMEOUT
        )
        response.raise_for_status()

        data = response.json()
        news_items = data.get("news", [])

        articles: List[Article] = []
        for item in news_items[:max_results]:
            title = (item.get("title") or "").strip()
            if not title:
                continue
            articles.append(
                Article(
                    title=title,
                    url=item.get("link", ""),
                    summary=item.get("snippet", ""),
                    source=self.name,
                    published_at=item.get("date", ""),
                )
            )

        return articles
