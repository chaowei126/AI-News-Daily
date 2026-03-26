"""
Fetcher package.

Usage:
    from ai_news_daily.fetcher import aggregate_news
    articles = aggregate_news()
"""

import logging
from typing import List

from ai_news_daily.config import config
from ai_news_daily.fetcher.serper import SerperFetcher
from ai_news_daily.fetcher.newsapi import NewsAPIFetcher
from ai_news_daily.models import Article

logger = logging.getLogger(__name__)


def aggregate_news() -> List[Article]:
    """
    Fetch from all enabled sources and return a deduplicated list of Articles.
    A source failure is logged but does NOT abort the pipeline.
    """
    fetchers = [SerperFetcher(), NewsAPIFetcher()]
    seen_titles: set = set()
    combined: List[Article] = []

    for fetcher in fetchers:
        articles = fetcher.safe_fetch(
            query=config.news_query,
            max_results=config.max_articles_per_source,
        )
        for article in articles:
            normalized = article.title.lower().strip()
            if normalized not in seen_titles:
                seen_titles.add(normalized)
                combined.append(article)

    logger.info("Total unique articles after deduplication: %d", len(combined))
    return combined
