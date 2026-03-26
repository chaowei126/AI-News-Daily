"""
Fetcher backed by NewsAPI.org.
Docs: https://newsapi.org/docs/endpoints/everything
Endpoint: GET https://newsapi.org/v2/everything
"""

import logging
from typing import List

import requests

from ai_news_daily.config import config
from ai_news_daily.fetcher.base import BaseFetcher
from ai_news_daily.models import Article

logger = logging.getLogger(__name__)

_ENDPOINT = "https://newsapi.org/v2/everything"
_TIMEOUT = 15  # seconds


class NewsAPIFetcher(BaseFetcher):
    name = "newsapi"

    def fetch(self, query: str, max_results: int) -> List[Article]:
        params = {
            "apiKey": config.news_api_key,
            "q": query,
            "language": "en",
            "sortBy": "publishedAt",
            "pageSize": min(max_results, 100),  # NewsAPI max page size is 100
        }

        response = requests.get(_ENDPOINT, params=params, timeout=_TIMEOUT)
        response.raise_for_status()

        data = response.json()

        if data.get("status") != "ok":
            raise RuntimeError(
                f"NewsAPI returned status '{data.get('status')}': "
                f"{data.get('message', 'unknown error')}"
            )

        raw_articles = data.get("articles", [])

        articles: List[Article] = []
        for item in raw_articles[:max_results]:
            title = (item.get("title") or "").strip()
            # NewsAPI sometimes returns "[Removed]" for deleted articles
            if not title or title == "[Removed]":
                continue
            articles.append(
                Article(
                    title=title,
                    url=item.get("url", ""),
                    summary=item.get("description") or item.get("content") or "",
                    source=self.name,
                    published_at=item.get("publishedAt", ""),
                )
            )

        return articles
