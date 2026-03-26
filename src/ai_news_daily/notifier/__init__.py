"""
Notifier package.

Usage:
    from ai_news_daily.notifier import send_email
    send_email(html_string)
"""

from ai_news_daily.notifier.email_sender import send as send_email

__all__ = ["send_email"]
