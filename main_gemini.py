import os
import time
import logging
import feedparser
import smtplib
from google import genai  # 使用 google-genai 库
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

# -------------------------
# Logging 配置
# -------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

# -------------------------
# 配置读取
# -------------------------
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
SENDER_EMAIL = os.getenv("EMAIL_USER")
SENDER_PASSWORD = os.getenv("EMAIL_PASS")
RECEIVER_EMAIL = os.getenv("EMAIL_USER")

NEWS_FEEDS = [
    "https://rss.slashdot.org/Slashdot/slashdotMain",
    "https://feeds.bbci.co.uk/news/world/rss.xml"
]

# -------------------------
# 初始化 Gemini 客户端
# -------------------------
client = None
if GEMINI_API_KEY:
    try:
        # 初始化客户端
        client = genai.Client(api_key=GEMINI_API_KEY)
        logging.info("Gemini 客户端初始化成功")
    except Exception as e:
        logging.error(f"客户端初始化失败: {e}")
else:
    logging.error("未找到 GEMINI_API_KEY，请检查 GitHub Secrets")

# -------------------------
# Gemini API 调用 (修复 404 关键点)
# -------------------------
def call_gemini(prompt, max_retries=3):
    if not client:
        raise RuntimeError("Gemini 客户端未初始化")

    for attempt in range(max_retries):
        try:
            # 关键修正：在某些环境下，需要加上 'models/' 前缀以避免 404
            response = client.models.generate_content(
                model="gemini-1.5-flash", 
                contents=prompt
            )

            if response and response.text:
                return response.text
            else:
                logging.warning("Gemini 返回内容为空")

        except Exception as e:
            # 如果依然报 404，尝试切换带前缀的名称
            if "404" in str(e) and attempt == 0:
                logging.info("尝试使用带前缀的模型名称...")
                try:
                    response = client.models.generate_content(
                        model="models/gemini-1.5-flash",
                        contents=prompt
                    )
                    if response.text: return response.text
                except: pass

            wait = 2 ** attempt
            logging.warning(f"调用失败 (第 {attempt+1} 次): {e}, {wait}s 后重试")
            time.sleep(wait)

    raise RuntimeError("Gemini API 持续返回错误，请检查 API Key 权限或区域限制")

# -------------------------
# 获取新闻逻辑
# -------------------------
def fetch_news():
    logging.info("正在获取 RSS 新闻...")
    all_news = []
    seen_titles = set()
    for url in NEWS_FEEDS:
        try:
            feed = feedparser.parse(url)
            for entry in feed.entries[:10]:
                title = entry.title.strip()
                if title not in seen_titles:
                    seen_titles.add(title)
                    all_news.append(f"Title: {title}\nSummary: {entry.get('summary', '')}\n")
        except Exception as e:
            logging.error(f"RSS 抓取失败: {url}, {e}")
    return "\n---\n".join(all_news)

# -------------------------
# 生成摘要逻辑
# -------------------------
def summarize_news(raw_text):
    prompt = f"""
请将以下新闻总结为 8-10 条简体中文摘要，使用 HTML <li> 格式输出。
包含 <strong>标题</strong> 和 <span>摘要</span>。

{raw_text}
"""
    return call_gemini(prompt)

# -------------------------
# 发送邮件逻辑
# -------------------------
def send_email(content_html):
    if not SENDER_EMAIL or not SENDER_PASSWORD:
        logging.error("邮件配置不全")
        return
    msg = MIMEMultipart()
    msg["From"] = SENDER_EMAIL
    msg["To"] = RECEIVER_EMAIL
    msg["Subject"] = "🌐 每日 AI & 科技新闻摘要"
    html_template = f"<html><body><h2>今日要闻精选</h2><ul>{content_html}</ul></body></html>"
    msg.attach(MIMEText(html_template, "html"))
    try:
        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()
            server.login(SENDER_EMAIL, SENDER_PASSWORD)
            server.send_message(msg)
        logging.info("邮件已发送")
    except Exception as e:
        logging.error(f"邮件发送失败: {e}")

# -------------------------
# 程序入口
# -------------------------
if __name__ == "__main__":
    try:
        news_data = fetch_news()
        if news_data:
            summary = summarize_news(news_data)
            send_email(summary)
        else:
            logging.warning("无新闻可处理")
    except Exception as e:
        logging.error(f"运行失败: {e}")
