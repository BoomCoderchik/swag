import re
from datetime import UTC, datetime, timedelta

from swag.models import Item

_FREE_PATTERNS = (
    "free",
    "freebie",
    "giveaway",
    "promo",
    "limited time",
    "for free",
    "бесплатн",
    "халява",
    "холява",
    "раздач",
    "промокод",
    "даром",
    "open-source",
    "open source",
    "open-weights",
    "open weights",
)

_AI_PATTERNS = (
    "ai",
    "a.i.",
    "artificial intelligence",
    "llm",
    "gpt",
    "claude",
    "gemini",
    "llama",
    "mistral",
    "deepseek",
    "qwen",
    "openai",
    "anthropic",
    "copilot",
    "grok",
    "kimi",
    "chatbot",
    "model",
    "нейросет",
    "нейрон",
    "модель",
)


def _matches_any(text: str, patterns: tuple[str, ...]) -> bool:
    return any(re.search(rf"\b{re.escape(p)}", text) for p in patterns)


def is_fresh(published_ts: float | None, fresh_hours: int) -> bool:
    if published_ts is None:
        return False
    age = datetime.now(UTC) - datetime.fromtimestamp(published_ts, UTC)
    return age <= timedelta(hours=fresh_hours)


def is_relevant(item: Item) -> bool:
    text = f"{item.title} {item.description}".lower()
    return _matches_any(text, _AI_PATTERNS) and _matches_any(text, _FREE_PATTERNS)


def has_free_signal_in_title(item: Item) -> bool:
    return _matches_any(item.title.lower(), _FREE_PATTERNS)
