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
你是一位专业的科技新闻编辑，擅长 AI、科技和全球时事领域。

请从以下新闻列表中精选 6-8 条最值得关注的要闻，并整理成中文摘要。

选题原则：
1. 优先选择 AI、科技、科学类新闻。
2. 若科技类不足，可补充美国外交、中美关系、地缘政治等重大国际新闻。
3. 不收录体育、娱乐、地方性等低价值内容。
4. 绝对不捏造或推断不存在的新闻。

输出格式（严格遵守）：
- 仅输出 HTML <li> 条目，不加任何前言或后记。
- 每条格式：
  <li>
    <strong>标题：</strong>（最多15字）<br>
    <span>摘要：</span>（最多50字）
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
