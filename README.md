---

```markdown
# 🤖 AI-News-Daily: 基于 Gemini 的自动新闻简报

这是一个轻量化的自动化程序，每天定时抓取主流媒体 RSS 新闻，利用 **Google Gemini 2.0 Flash** 智能模型进行深度总结，并自动发送精美的 HTML 简报邮件。



## ✨ 功能特性

- **多源抓取**：支持自定义多个 RSS 订阅源（如 BBC, WSJ, 科技媒体等）。
- **AI 智能总结**：集成 Gemini 2.0 Flash 模型，自动翻译、去重并提炼核心要闻。
- **全自动化运行**：基于 GitHub Actions，无需服务器，每天准时推送。
- **精美邮件模板**：生成的邮件经过 HTML 格式化，阅读体验优良。
- **零成本**：完全利用 Google AI 和 GitHub 的免费额度。

## 🛠️ 环境准备

1. **Python 环境**：Python 3.9+
2. **API Key**：前往 [Google AI Studio](https://aistudio.google.com/) 获取免费的 Gemini API Key。
3. **邮箱授权码**：开启发件邮箱的 SMTP 服务并获取“授权码”（非登录密码）。

## 🚀 快速开始

### 1. 克隆仓库
```bash
git clone [https://github.com/你的用户名/你的仓库名.git](https://github.com/你的用户名/你的仓库名.git)
cd 你的仓库名

```

### 2. 安装依赖

```bash
pip install -r requirements.txt

```

### 3. 本地测试

在代码中配置好你的 `API_KEY` 和邮箱信息，运行：

```bash
python main.py

```

## 🤖 自动化部署 (GitHub Actions)

为了实现每天自动发送，请在 GitHub 仓库中进行以下设置：

1. 进入 **Settings > Secrets and variables > Actions**。
2. 添加以下 **Repository secrets**:
* `GEMINI_API_KEY`: 你的 Gemini API 密钥。
* `EMAIL_USER`: 你的发件邮箱地址。
* `EMAIL_PASS`: 你的邮箱 SMTP 授权码。


3. 检查 `.github/workflows/daily_news.yml` 中的 `cron` 时间（默认为每天北京时间 8:00）。

## 📂 文件结构

* `main.py`: 主程序逻辑（抓取、AI 处理、发信）。
* `requirements.txt`: 项目所需的 Python 库。
* `.github/workflows/daily_news.yml`: GitHub Actions 自动化脚本。

## 📜 许可证

MIT License

```

---

### 💡 建议操作：
1.  **替换链接**：记得把 README 里的 `你的用户名/你的仓库名` 替换成实际的。
2.  **添加效果图**：如果你运行成功收到了邮件，可以截一张邮件效果图放在 README 里，这会让项目看起来更有成就感。

```