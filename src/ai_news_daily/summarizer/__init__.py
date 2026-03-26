"""
Summarizer package.

Usage:
    from ai_news_daily.summarizer import summarize
    html = summarize(articles)
"""

from ai_news_daily.summarizer.openrouter import summarize

__all__ = ["summarize"]
