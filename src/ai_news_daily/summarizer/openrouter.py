"""
Summarizer backed by OpenRouter (free model fallback chain).
Docs: https://openrouter.ai/docs
"""

import logging
import time
from typing import List

import requests

from ai_news_daily.config import config
from ai_news_daily.models import Article

logger = logging.getLogger(__name__)

_ENDPOINT = "https://openrouter.ai/api/v1/chat/completions"
_TIMEOUT = 60  # seconds; LLM calls can be slow

_PROMPT_TEMPLATE = """\
你是一位专业的科技与政治新闻编辑，擅长追踪 AI 行业趋势、特朗普政府政策以及美伊地缘政治。

请从以下新闻列表中精选 8-10 条要闻，整理成中文摘要。

选题原则（优先级排序）：
1. 特朗普与美伊动态：特朗普政府对伊朗的最新制裁、外交施压、军事威慑或关于核协议的言论。
2. 特朗普对内政策：涉及 AI 监管、关税、科技限制及能源（影响数据中心）的白宫新政。
3. AI 核心进展：大模型更新、Agentic AI（智能体）架构、开源模型以及 AI 芯片供应链动态。
4. 排除项：严禁收录体育、娱乐、地方性及与上述主题无关的内容。

输出格式（严格遵守）：
- 仅输出 HTML <li> 条目，不加任何前言或后记。
- 每条格式：
  <li>
    <strong>标题：</strong>（最多 15 字，需包含特朗普、AI 或美伊等关键词）<br>
    <span>摘要：</span>（最多 60 字，精炼陈述事实及其核心影响）
  </li>

原始新闻如下：
---
{articles_text}
---
"""


def _build_prompt(articles: List[Article]) -> str:
    blocks = [a.to_prompt_block() for a in articles]
    return _PROMPT_TEMPLATE.format(articles_text="\n\n".join(blocks))


def _call_model(model: str, messages: list) -> str:
    """Single attempt against one model. Raises on any failure."""
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {config.openrouter_api_key}",
        "HTTP-Referer": "https://github.com/ai-news-daily",
        "X-Title": "AI-News-Daily",
    }
    payload = {"model": model, "messages": messages}

    response = requests.post(
        _ENDPOINT, headers=headers, json=payload, timeout=_TIMEOUT
    )

    # Log response body on client errors to aid debugging
    if response.status_code >= 400:
        logger.debug("OpenRouter error body: %s", response.text[:500])

    response.raise_for_status()

    data = response.json()
    return data["choices"][0]["message"]["content"]


def summarize(articles: List[Article]) -> str:
    """
    Try each model in the configured fallback chain.
    Returns the generated HTML string on first success.
    Raises RuntimeError if all models fail.
    """
    if not articles:
        raise ValueError("No articles provided for summarization.")

    messages = [{"role": "user", "content": _build_prompt(articles)}]

    for model in config.llm_models:
        logger.info("Trying model: %s", model)

        for attempt in range(config.llm_max_retries):
            try:
                result = _call_model(model, messages)
                logger.info("Model succeeded: %s", model)
                return result
            except Exception as exc:
                wait = config.llm_retry_base_wait * (2 ** attempt)
                logger.warning(
                    "Model %s attempt %d/%d failed: %s – retrying in %ds",
                    model,
                    attempt + 1,
                    config.llm_max_retries,
                    exc,
                    wait,
                )
                time.sleep(wait)

        logger.warning("Model exhausted all retries: %s", model)

    raise RuntimeError("All OpenRouter models failed after fallback chain exhausted.")
