import os
import time
import logging
import feedparser
import requests
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

# -------------------------
# 日志配置
# -------------------------
logging.basicConfig(
    filename="news_bot.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

logging.info("程序启动")

# -------------------------
# 配置区
# -------------------------
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
MODEL_ID = "meta-llama/llama-3.1-8b-instruct:free"

NEWS_FEEDS = [
    "https://rss.slashdot.org/Slashdot/slashdotMain",
    "https://feeds.bbci.co.uk/news/world/rss.xml"
]

SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
SENDER_EMAIL = os.getenv("EMAIL_USER")
SENDER_PASSWORD = os.getenv("EMAIL_PASS")
RECEIVER_EMAIL = "你的实际接收邮箱@example.com"


# -------------------------
# 工具函数：OpenRouter API 调用（带重试）
# -------------------------
def call_openrouter(messages, model=MODEL_ID, max_retries=3):
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "HTTP-Referer": "http://localhost",
        "X-Title": "News Summary Script"
    }

    payload = {
        "model": model,
        "messages": messages
    }

    for attempt in range(max_retries):
        try:
            response = requests.post(url, headers=headers, json=payload, timeout=20)
            response.raise_for_status()
            data = response.json()
            return data["choices"][0]["message"]["content"]

        except Exception as e:
            wait = 2 ** attempt
            logging.warning(f"API 调用失败（第 {attempt+1} 次），错误：{e}，等待 {wait}s 重试")
            time.sleep(wait)

    logging.error("API 多次重试仍失败")
    raise RuntimeError("OpenRouter API 调用失败")


# -------------------------
# 自动翻译（非中文 → 中文）
# -------------------------
def translate_to_chinese(text):
    logging.info("检测并翻译新闻内容")

    detect_prompt = f"请判断以下文本是否为中文，只回答 '是' 或 '否'：\n{text[:200]}"
    is_chinese = call_openrouter([{"role": "user", "content": detect_prompt}])

    if "是" in is_chinese:
        return text

    logging.info("检测到非中文新闻，开始翻译")

    translate_prompt = f"请将以下内容翻译成中文：\n{text}"
    return call_openrouter([{"role": "user", "content": translate_prompt}])


# -------------------------
# 抓取新闻 + 去重 + 翻译
# -------------------------
def fetch_news():
    logging.info("开始抓取新闻")
    all_news = []
    seen_titles = set()

    for url in NEWS_FEEDS:
        feed = feedparser.parse(url)
        if hasattr(feed, 'entries'):
            for entry in feed.entries[:5]:
                title = entry.title.strip()

                # 去重
                if title in seen_titles:
                    continue
                seen_titles.add(title)

                summary = entry.get("summary", "")
                link = entry.link

                # 翻译标题和摘要
                title_cn = translate_to_chinese(title)
                summary_cn = translate_to_chinese(summary)

                all_news.append(
                    f"标题: {title_cn}\n链接: {link}\n摘要: {summary_cn}\n"
                )

    logging.info(f"抓取完成，共 {len(all_news)} 条新闻")
    return "\n---\n".join(all_news)


# -------------------------
# 新闻摘要
# -------------------------
def summarize_news(raw_text):
    logging.info("开始生成摘要")

    prompt = f"""
你是一名专业的科技新闻编辑，擅长从大量资讯中提取重点。

请根据以下原始新闻内容，完成高质量摘要：
{raw_text}

【任务要求】
1. 从所有新闻中筛选出 **最值得关注的 3–5 条科技或 AI 相关内容**。
2. 每条新闻需包含：
   - **一句话标题（10–15 字）**
   - **一句话摘要（不超过 40 字）**
3. 输出格式必须为 HTML 的 <li> 列表项，结构如下：

<li>
  <strong>标题：</strong>xxx<br>
  <span>摘要：xxx</span>
</li>

【注意事项】
- 不要编造不存在的新闻。
- 不要输出与科技或 AI 无关的内容。
- 不要添加额外解释或前后缀。
- 输出必须是纯 HTML 列表项，不要包含 <ul> 标签。
"""

    return call_openrouter([{"role": "user", "content": prompt}])


# -------------------------
# 发送邮件
# -------------------------
def send_email(content_html):
    logging.info("开始发送邮件")

    msg = MIMEMultipart()
    msg['From'] = SENDER_EMAIL
    msg['To'] = RECEIVER_EMAIL
    msg['Subject'] = "🌟 今日 AI 精选要闻简报"

    html_template = f"""
    <html>
      <body style="font-family: 'Microsoft YaHei', sans-serif; line-height: 1.6; color: #333;">
        <h2 style="color: #2c3e50; border-bottom: 2px solid #3498db; padding-bottom: 10px;">今日新闻摘要</h2>
        <ul>
          {content_html}
        </ul>
        <hr>
        <p style="font-size: 12px; color: #7f8c8d;">此邮件由 AI 自动生成推送。</p>
      </body>
    </html>
    """

    msg.attach(MIMEText(html_template, 'html'))

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
            logging.warning("没有抓取到新闻内容")
    except Exception as e:
        logging.error(f"程序运行失败：{e}")
