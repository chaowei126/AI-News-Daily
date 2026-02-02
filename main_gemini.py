import os
import time
import logging
import feedparser
import smtplib
from google import genai  # 导入最新版 SDK
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

# -------------------------
# Logging 配置
# -------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

logging.info("程序启动 (方案 2: 使用 google-genai 最新 SDK)")

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
        # 初始化客户端，新版 SDK 会自动处理 v1beta 逻辑
        client = genai.Client(api_key=GEMINI_API_KEY)
        logging.info("Gemini 客户端初始化成功")
    except Exception as e:
        logging.error(f"客户端初始化失败: {e}")
else:
    logging.error("未找到 GEMINI_API_KEY，请检查 GitHub Secrets 设置")

# -------------------------
# Gemini API 调用
# -------------------------
def call_gemini(prompt, max_retries=3):
    if not client:
        raise RuntimeError("Gemini 客户端未初始化")

    for attempt in range(max_retries):
        try:
            # 修正点：直接使用简短模型名称 "gemini-1.5-flash"
            response = client.models.generate_content(
                model="gemini-1.5-flash", 
                contents=prompt
            )

            if response and response.text:
                return response.text
            else:
                logging.warning("Gemini 返回响应内容为空")

        except Exception as e:
            wait = 2 ** attempt
            logging.warning(f"Gemini 调用失败 (第 {attempt+1} 次): {e}, {wait}s 后重试")
            time.sleep(wait)

    raise RuntimeError("Gemini API 在多次重试后仍然返回 404 或其他错误")

# -------------------------
# 获取新闻内容
# -------------------------
def fetch_news():
    logging.info("正在抓取 RSS 源...")
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
                all_news.append(f"Title: {title}\nSummary: {summary}\n")
        except Exception as e:
            logging.error(f"抓取失败 {url}: {e}")

    return "\n---\n".join(all_news)

# -------------------------
# 生成摘要
# -------------------------
def summarize_news(raw_text):
    logging.info("正在调用 AI 生成摘要...")
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
    if not SENDER_EMAIL or not SENDER_PASSWORD:
        logging.error("邮件配置缺失 (EMAIL_USER 或 EMAIL_PASS)")
        return

    msg = MIMEMultipart()
    msg["From"] = SENDER_EMAIL
    msg["To"] = RECEIVER_EMAIL
    msg["Subject"] = "🌐 每日 AI & 科技新闻摘要"

    html_template = f"<html><body><ul>{content_html}</ul></body></html>"
    msg.attach(MIMEText(html_template, "html"))

    try:
        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()
            server.login(SENDER_EMAIL, SENDER_PASSWORD)
            server.send_message(msg)
        logging.info("邮件发送成功")
    except Exception as e:
        logging.error(f"邮件发送失败: {e}")

# -------------------------
# 主入口
# -------------------------
if __name__ == "__main__":
    try:
        raw_news = fetch_news()
        if raw_news:
            summary_html = summarize_news(raw_news)
            send_email(summary_html)
        else:
            logging.warning("未抓取到新闻")
    except Exception as e:
        logging.error(f"程序终止: {e}")