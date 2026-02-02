import os
import time
import logging
import feedparser
import smtplib
from google import genai
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

# -------------------------
# Logging 配置
# -------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

logging.info("程序启动 (使用最新版 google-genai SDK)")

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

SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587

# 初始化新版 Gemini 客户端
client = None
if GEMINI_API_KEY:
    client = genai.Client(api_key=GEMINI_API_KEY)
else:
    logging.error("未找到 GEMINI_API_KEY，请检查环境变量。")

# -------------------------
# Gemini API 调用 (新版语法)
# -------------------------
def call_gemini(prompt, max_retries=3):
    if not client:
        raise RuntimeError("Gemini 客户端未初始化")

    for attempt in range(max_retries):
        try:
            # 使用最新的 SDK 调用方式
            response = client.models.generate_content(
                model="gemini-1.5-flash",
                contents=prompt
            )

            if response.text:
                logging.info("Gemini 生成成功")
                return response.text
            else:
                logging.warning("Gemini 返回空响应")

        except Exception as e:
            wait = 2 ** attempt
            logging.warning(f"Gemini 调用失败 (尝试 {attempt+1}): {e}, 等待 {wait}s")
            time.sleep(wait)

    logging.error("Gemini API 多次重试后失败")
    raise RuntimeError("Gemini API failed")

# -------------------------
# 获取新闻内容
# -------------------------
def fetch_news():
    logging.info("正在抓取 RSS 源")
    all_news = []
    seen_titles = set()

    for url in NEWS_FEEDS:
        try:
            feed = feedparser.parse(url)
            for entry in feed.entries[:10]:
                title = entry.title.strip()
                if title in seen_titles:
                    continue
                seen_titles.add(title)

                summary = entry.get("summary", "")
                link = entry.link
                all_news.append(f"Title: {title}\nLink: {link}\nSummary: {summary}\n")
        except Exception as e:
            logging.error(f"抓取 {url} 失败: {e}")

    logging.info(f"共抓取到 {len(all_news)} 条新闻")
    return "\n---\n".join(all_news)

# -------------------------
# 生成摘要 (HTML 格式)
# -------------------------
def summarize_news(raw_text):
    logging.info("正在生成 AI 摘要...")
    prompt = f"""
你是一位专业的科技新闻编辑。请将以下新闻内容总结为 8–10 条精选项目，并翻译成简体中文。

{raw_text}

要求：
1. 优先筛选 AI、半导体和前沿科技相关内容。
2. 语言风格专业、简洁。
3. 严格输出 HTML <li> 格式，不要包含任何前导词或结语。

格式模板：
<li>
  <strong>标题：</strong> 中文标题<br>
  <span>摘要：简短的中文介绍</span>
</li>
"""
    return call_gemini(prompt)

# -------------------------
# 发送邮件
# -------------------------
def send_email(content_html):
    logging.info("正在发送邮件...")
    msg = MIMEMultipart()
    msg["From"] = SENDER_EMAIL
    msg["To"] = RECEIVER_EMAIL
    msg["Subject"] = "🌐 每日 AI & 科技新闻摘要"

    html_template = f"""
    <html>
      <body style="font-family: 'Microsoft YaHei', Arial, sans-serif; line-height: 1.6; color: #333;">
        <h2 style="color: #2c3e50;">每日科技 & AI 新闻精选</h2>
        <ul>
          {content_html}
        </ul>
        <hr>
        <p style="font-size: 12px; color: #888;">本邮件由 Gemini 1.5 Flash 自动生成。</p>
      </body>
    </html>
    """

    msg.attach(MIMEText(html_template, "html"))

    try:
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(SENDER_EMAIL, SENDER_PASSWORD)
            server.send_message(msg)
        logging.info("邮件发送成功")
    except Exception as e:
        logging.error(f"邮件发送失败: {e}")

# -------------------------
# 主程序
# -------------------------
if __name__ == "__main__":
    try:
        raw_news = fetch_news()
        if raw_news:
            summary_html = summarize_news(raw_news)
            send_email(summary_html)
        else:
            logging.warning("未获取到任何新闻内容")
    except Exception as e:
        logging.error(f"程序运行出错: {e}")