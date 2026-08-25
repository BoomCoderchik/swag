import asyncio
import html
import re

import feedparser

from swag.models import Item


def _clean(text: str, limit: int = 500) -> str:
    text = re.sub(r"<[^>]+>", " ", text or "")
    text = html.unescape(text)
    return re.sub(r"\s+", " ", text).strip()[:limit]


def _fetch_sync(name: str, url: str, limit: int) -> list[Item]:
    feed = feedparser.parse(url)
    return [
        Item(
            source=f"rss:{name}",
            title=entry.get("title", ""),
            url=entry.get("link", ""),
            description=_clean(entry.get("summary", "")),
        )
        for entry in feed.entries[:limit]
        if entry.get("link")
    ]


async def fetch_rss(name: str, url: str, limit: int = 10) -> list[Item]:
    return await asyncio.to_thread(_fetch_sync, name, url, limit)
