"""
Email notifier – sends the daily digest via SMTP (Gmail by default).
"""

import logging
import smtplib
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from ai_news_daily.config import config

logger = logging.getLogger(__name__)

_HTML_TEMPLATE = """\
<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <title>每日新闻摘要</title>
  <style>
    body  {{ font-family: 'PingFang SC', 'Microsoft YaHei', Arial, sans-serif;
             background: #f5f7fa; color: #333; margin: 0; padding: 20px; }}
    .card {{ background: #fff; border-radius: 8px; max-width: 680px;
             margin: 0 auto; padding: 32px; box-shadow: 0 2px 8px rgba(0,0,0,.08); }}
    h2    {{ color: #1a1a2e; border-bottom: 3px solid #4a90d9;
             padding-bottom: 10px; margin-top: 0; }}
    ul    {{ padding-left: 0; list-style: none; }}
    li    {{ padding: 12px 0; border-bottom: 1px solid #eee; }}
    li:last-child {{ border-bottom: none; }}
    strong {{ color: #2c3e50; }}
    span  {{ color: #555; font-size: 14px; }}
    footer {{ text-align: center; font-size: 11px; color: #aaa; margin-top: 20px; }}
  </style>
</head>
<body>
  <div class="card">
    <h2>📰 今日科技要闻精选</h2>
    <p style="color:#888;font-size:13px;">更新时间：{date}</p>
    <ul>
      {content}
    </ul>
    <footer>此邮件由 AI-News-Daily 自动生成 · 数据来源：Serper &amp; NewsAPI</footer>
  </div>
</body>
</html>
"""


def send(content_html: str) -> None:
    """
    Compose and send the digest email.

    Args:
        content_html: Raw <li>…</li> HTML string from the summarizer.
    """
    today = datetime.now().strftime("%Y年%m月%d日 %H:%M")
    full_html = _HTML_TEMPLATE.format(date=today, content=content_html)

    msg = MIMEMultipart("alternative")
    msg["From"] = config.sender_email
    msg["To"] = config.receiver_email
    msg["Subject"] = config.email_subject
    msg.attach(MIMEText(full_html, "html", "utf-8"))

    logger.info(
        "Sending email to %s via %s:%d",
        config.receiver_email,
        config.smtp_server,
        config.smtp_port,
    )

    with smtplib.SMTP(config.smtp_server, config.smtp_port) as server:
        server.ehlo()
        server.starttls()
        server.login(config.sender_email, config.sender_password)
        server.send_message(msg)

    logger.info("Email sent successfully.")
