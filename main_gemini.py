import os
import time
import logging
import feedparser
import smtplib
import google.generativeai as genai
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

# -------------------------
# Logging
# -------------------------
logging.basicConfig(
    filename="news_bot_gemini.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

logging.info("Program started (Gemini Version)")

# -------------------------
# Config
# -------------------------
# 请确保环境变量中设置了 GEMINI_API_KEY
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

NEWS_FEEDS = [
    "https://rss.slashdot.org/Slashdot/slashdotMain",
    "https://feeds.bbci.co.uk/news/world/rss.xml"
]

SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
SENDER_EMAIL = os.getenv("EMAIL_USER")
SENDER_PASSWORD = os.getenv("EMAIL_PASS")
RECEIVER_EMAIL = os.getenv("EMAIL_USER")

# 配置 Gemini
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
else:
    logging.error("GEMINI_API_KEY not found in environment variables.")

# -------------------------
# Gemini API Call
# -------------------------
def call_gemini(prompt, max_retries=3):
    # 使用 Gemini 1.5 Flash 模型，速度快且免费额度高
    model_name = "gemini-1.5-flash"

    logging.info(f"Calling Gemini model: {model_name}")

    for attempt in range(max_retries):
        try:
            model = genai.GenerativeModel(model_name)
            response = model.generate_content(prompt)

            if response.text:
                logging.info("Gemini generation succeeded")
                return response.text
            else:
                logging.warning("Gemini returned empty response")

        except Exception as e:
            wait = 2 ** attempt
            logging.warning(
                f"Gemini call failed (attempt {attempt+1}): {e}, waiting {wait}s"
            )
            time.sleep(wait)

    logging.error("Gemini API failed after retries")
    raise RuntimeError("Gemini API failed")


# -------------------------
# Fetch News (Increased Volume)
# -------------------------
def fetch_news():
    logging.info("Fetching RSS feeds")
    all_news = []
    seen_titles = set()

    for url in NEWS_FEEDS:
        feed = feedparser.parse(url)
        if hasattr(feed, "entries"):
            # 修改点：从获取前5条改为获取前10条，增加新闻量
            for entry in feed.entries[:10]:
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
# Summarize news (Chinese + Increased Volume)
# -------------------------
def summarize_news(raw_text):
    logging.info("Generating summary with Gemini")

    # 修改点：
    # 1. 角色设定增加中文翻译能力
    # 2. 数量要求改为 8-10 条
    # 3. 输出语言强制为简体中文
    prompt = f"""
You are a professional news editor specializing in technology, AI, and U.S.-related global affairs.

Please summarize the following raw news content into **8–10 key news items** and translate them into **Simplified Chinese**.

{raw_text}

Selection rules:  
1. Prioritize news related to technology, AI, and science.  
2. If there are not enough tech/AI stories, include major international news related to the United States (e.g., foreign policy, geopolitical conflicts).  
3. Do not include minor local news, sports, entertainment, or irrelevant topics.  
4. Absolutely no fabricated news.

Output rules:  
1. All content must be in **Simplified Chinese**.  
2. Each item must include:  
   - A short title (maximum 15 Chinese characters)  
   - A one-sentence summary (maximum 50 Chinese characters)  
3. The output format must strictly follow the HTML <li> structure:

<li>
  <strong>标题：</strong> xxx<br>
  <span>摘要：xxx</span>
</li>

4. Do not add any explanations, introductions, or closing remarks—only output the `<li>` list items.
"""

    return call_gemini(prompt)


# -------------------------
# Send email (Chinese Content)
# -------------------------
def send_email(content_html):
    logging.info("Sending email")

    msg = MIMEMultipart()
    msg["From"] = SENDER_EMAIL
    msg["To"] = RECEIVER_EMAIL
    # 修改点：邮件标题改为中文
    msg["Subject"] = "🌐 每日 AI & 科技新闻摘要"

    # 修改点：HTML 模板中的标题和页脚改为中文
    html_template = f"""
    <html>
      <body style="font-family: 'Microsoft YaHei', Arial, sans-serif; line-height: 1.6; color: #333;">
        <h2 style="color: #2c3e50;">每日科技 & AI 新闻精选</h2>
        <ul>
          {content_html}
        </ul>
        <hr>
        <p style="font-size: 12px; color: #888;">本邮件由 AI 自动生成。</p>
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