# 🤖 AI-News-Daily

基于 **Serper + NewsAPI** 双源抓取、**OpenRouter** 免费模型摘要、**GitHub Actions** 全自动推送的每日科技新闻简报。

---

## ✨ 功能特性

| 特性 | 说明 |
|------|------|
| 双源抓取 | Serper（Google 新闻）+ NewsAPI，互为容灾，自动去重 |
| AI 摘要 | OpenRouter 免费模型多级回退（Qwen3 → Gemma3 → LLaMA3.3） |
| 精美邮件 | 响应式 HTML 模板，支持移动端阅读 |
| 全自动化 | GitHub Actions 每天北京时间 08:00 定时运行，无需服务器 |
| 零成本 | 所有 API 均有免费额度，日常使用完全免费 |

---

## 📂 项目结构

```
AI-News-Daily/
├── main.py                              # 统一入口
├── requirements.txt
├── .env.example                         # 环境变量说明模板
├── .github/
│   └── workflows/
│       └── daily_news.yml               # GitHub Actions 定时任务
└── src/
    └── ai_news_daily/
        ├── config.py                    # 统一配置（读取环境变量）
        ├── models.py                    # 共享数据模型 Article
        ├── fetcher/
        │   ├── __init__.py              # aggregate_news() 聚合入口
        │   ├── base.py                  # BaseFetcher 抽象基类
        │   ├── serper.py                # Serper Google 新闻抓取
        │   └── newsapi.py               # NewsAPI.org 抓取
        ├── summarizer/
        │   ├── __init__.py
        │   └── openrouter.py            # OpenRouter LLM 摘要
        └── notifier/
            ├── __init__.py
            └── email_sender.py          # Gmail SMTP 发送
```

---

## 🔑 API Key 申请

| 服务 | 免费额度 | 申请地址 |
|------|---------|---------|
| Serper | 2,500 次/月 | https://serper.dev/ |
| NewsAPI | 100 次/天（开发者账号） | https://newsapi.org/ |
| OpenRouter | 多个免费模型 | https://openrouter.ai/ |

---

## 🚀 快速开始

### 本地运行

```bash
# 1. 克隆仓库
git clone https://github.com/你的用户名/AI-News-Daily.git
cd AI-News-Daily

# 2. 安装依赖
pip install -r requirements.txt

# 3. 配置环境变量
cp .env.example .env
# 编辑 .env，填入你的 API Key 和邮箱信息

# 4. 加载 .env 并运行（Linux/macOS）
export $(grep -v '^#' .env | xargs) && python main.py

# Windows PowerShell
Get-Content .env | Where-Object { $_ -notmatch '^#' } |
  ForEach-Object { $k,$v = $_ -split '=',2; [System.Environment]::SetEnvironmentVariable($k,$v) }
python main.py
```

### GitHub Actions 自动化部署

1. 进入仓库 **Settings → Secrets and variables → Actions**
2. 添加以下 Repository Secrets：

| Secret 名称 | 说明 |
|------------|------|
| `SERPER_API_KEY` | Serper API Key |
| `NEWS_API_KEY` | NewsAPI Key |
| `OPENROUTER_API_KEY` | OpenRouter API Key |
| `EMAIL_USER` | Gmail 发件地址 |
| `EMAIL_PASS` | Gmail 应用专用密码（非登录密码） |

> Gmail 应用专用密码申请：先开启两步验证，再访问  
> https://myaccount.google.com/apppasswords

3. 推送代码后，Actions 将在每天 **北京时间 08:00** 自动运行。也可在 Actions 页面点击 **Run workflow** 手动触发。

---

## ⚙️ 自定义配置

所有配置均通过环境变量控制，无需修改代码：

| 环境变量 | 默认值 | 说明 |
|---------|-------|------|
| `NEWS_QUERY` | `AI OR artificial intelligence OR technology` | 新闻搜索关键词 |
| `RECEIVER_EMAIL` | 与 `EMAIL_USER` 相同 | 收件邮箱（可设为不同地址） |

---

## 📜 License

MIT
