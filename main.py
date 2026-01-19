import os
import time
import logging
import feedparser
import requests
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

# -------------------------
# Logging
# -------------------------
logging.basicConfig(
    filename="news_bot.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

logging.info("Program started")

# -------------------------
# Config
# -------------------------
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

# Free model fallback list (priority order)
FREE_MODELS = [
    "qwen/qwen3-coder:free",
    "google/gemma-3-27b-it:free",
    "meta-llama/llama-3.3-70b-instruct:free"
]

NEWS_FEEDS = [
    "https://rss.slashdot.org/Slashdot/slashdotMain",
    "https://feeds.bbci.co.uk/news/world/rss.xml"
]

SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
SENDER_EMAIL = os.getenv("EMAIL_USER")
SENDER_PASSWORD = os.getenv("EMAIL_PASS")
RECEIVER_EMAIL = "your-real-email@example.com"


# -------------------------
# OpenRouter API with fallback
# -------------------------
def call_openrouter(messages, max_retries=3):
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "HTTP-Referer": "http://localhost",
        "X-Title": "News Summary Script"
    }

    for model in FREE_MODELS:
        logging.info(f"Trying model: {model}")

        payload = {
            "model": model,
            "messages": messages
        }

        for attempt in range(max_retries):
            try:
                response = requests.post(url, headers=headers, json=payload, timeout=30)
                response.raise_for_status()
                data = response.json()
                logging.info(f"Model succeeded: {model}")
                return data["choices"][0]["message"]["content"]

            except Exception as e:
                wait = 2 ** attempt
                logging.warning(
                    f"Model {model} failed (attempt {attempt+1}): {e}, waiting {wait}s"
                )
                time.sleep(wait)

        logging.warning(f"Model failed completely: {model}, switching to next model")

    logging.error("All models failed after fallback attempts")
    raise RuntimeError("All OpenRouter models failed")


# -------------------------
# Fetch English news
# -------------------------
def fetch_news():
    logging.info("Fetching RSS feeds")
    all_news = []
    seen_titles = set()

    for url in NEWS_FEEDS:
        feed = feedparser.parse(url)
        if hasattr(feed, "entries"):
            for entry in feed.entries[:5]:
                title = entry.title.strip()
                if title in seen_titles:
                    continue
                seen_titles.add(title)

                summary = entry.get("summary", "")
                link = entry.link

                all_news.append(
                    f"Title: {title}\nLink: {link}\nSummary: {summary}\n"
                )

    logging.info(f"Fetched {len(all_news)} news items")
    return "\n---\n".join(all_news)


# -------------------------
# Summarize news (English)
# -------------------------
def summarize_news(raw_text):
    logging.info("Generating summary")

    prompt = f"""
You are a professional tech news editor.

Summarize the following raw news content into **3–5 key tech or AI stories**:

{raw_text}

Requirements:
1. Only include tech, AI, or science-related news.
2. Each item must include:
   - A short title (max 12 words)
   - A one-sentence summary (max 30 words)
3. Output MUST be in HTML <li> format:

<li>
  <strong>Title:</strong> xxx<br>
  <span>Summary: xxx</span>
</li>

Do NOT add explanations or extra text.
Only output the <li> items.
"""

    return call_openrouter([{"role": "user", "content": prompt}])


# -------------------------
# Send email
# -------------------------
def send_email(content_html):
    logging.info("Sending email")

    msg = MIMEMultipart()
    msg["From"] = SENDER_EMAIL
    msg["To"] = RECEIVER_EMAIL
    msg["Subject"] = "🌐 Daily AI & Tech News Summary"

    html_template = f"""
    <html>
      <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
        <h2 style="color: #2c3e50;">Daily Tech & AI News Summary</h2>
        <ul>
          {content_html}
        </ul>
        <hr>
        <p style="font-size: 12px; color: #888;">This email was automatically generated.</p>
      </body>
    </html>
    """

    msg.attach(MIMEText(html_template, "html"))

    try:
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(SENDER_EMAIL, SENDER_PASSWORD)
            server.send_message(msg)
        logging.info("Email sent successfully")
    except Exception as e:
        logging.error(f"Email failed: {e}")


# -------------------------
# Main
# -------------------------
if __name__ == "__main__":
    try:
        raw_news = fetch_news()
        if raw_news:
            summary_html = summarize_news(raw_news)
            send_email(summary_html)
        else:
            logging.warning("No news fetched")
    except Exception as e:
        logging.error(f"Program failed: {e}")
