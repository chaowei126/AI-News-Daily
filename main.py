import feedparser
from google import genai
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

# --- 配置区 ---
GEMINI_API_KEY = "你的_GEMINI_API_KEY"
# 推荐使用 Flash 模型，速度快且免费
MODEL_ID = "gemini-2.0-flash" 

# RSS 新闻源 (可以添加多个)
NEWS_FEEDS = [
    "https://rss.slashdot.org/Slashdot/slashdotMain", # 科技新闻示例
    "https://feeds.bbci.co.uk/news/world/rss.xml"    # 国际新闻示例
]

# 邮件配置
SMTP_SERVER = "smtp.gmail.com" # 如果是163则是 smtp.163.com
SMTP_PORT = 587
SENDER_EMAIL = "你的邮箱@gmail.com"
SENDER_PASSWORD = "你的授权码" # 注意：不是登录密码
RECEIVER_EMAIL = "接收者的邮箱@example.com"

# --- 第一步：抓取新闻 ---
def fetch_news():
    print("正在抓取新闻...")
    all_news = []
    for url in NEWS_FEEDS:
        feed = feedparser.parse(url)
        for entry in feed.entries[:5]: # 每个源取前 5 条
            all_news.append(f"标题: {entry.title}\n链接: {entry.link}\n摘要: {entry.get('summary', '')}\n")
    return "\n---\n".join(all_news)

# --- 第二步：Gemini AI 总结 ---
def summarize_news(raw_text):
    print("正在调用 Gemini 进行 AI 总结...")
    client = genai.Client(api_key=GEMINI_API_KEY)
    
    prompt = f"""
    你是一个专业的新闻编辑。请分析以下抓取到的原始新闻内容：
    {raw_text}
    
    任务：
    1. 请多关注AI科技新闻，选出最值得关注的 3-5 条。
    2. 用中文总结每条新闻的核心内容（50字以内）。
    3. 输出格式要求为 HTML 的 <li> 列表项。
    """
    
    response = client.models.generate_content(model=MODEL_ID, contents=prompt)
    return response.text

# --- 第三步：发送邮件 ---
def send_email(content_html):
    print("正在发送邮件...")
    msg = MIMEMultipart()
    msg['From'] = SENDER_EMAIL
    msg['To'] = RECEIVER_EMAIL
    msg['Subject'] = "🌟 今日 AI 精选要闻简报"

    # 邮件正文模版
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
            server.starttls() # 启用安全传输
            server.login(SENDER_EMAIL, SENDER_PASSWORD)
            server.send_message(msg)
        print("邮件发送成功！")
    except Exception as e:
        print(f"邮件发送失败: {e}")

# --- 执行主程序 ---
if __name__ == "__main__":
    raw_news = fetch_news()
    if raw_news:
        summary_html = summarize_news(raw_news)
        send_email(summary_html)
    else:
        print("没有抓取到新闻。")