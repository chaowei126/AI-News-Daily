"""
Shared domain model used across the entire pipeline.
"""

from dataclasses import dataclass


@dataclass
class Article:
    """A single news article fetched from any source."""
    title: str
    url: str
    summary: str = ""
    source: str = ""      # e.g. "serper", "newsapi"
    published_at: str = ""

    def to_prompt_block(self) -> str:
        """Human-readable representation fed into the LLM prompt."""
        lines = [f"Title: {self.title}"]
        if self.summary:
            lines.append(f"Summary: {self.summary}")
        if self.url:
            lines.append(f"URL: {self.url}")
        return "\n".join(lines)
