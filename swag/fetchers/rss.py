import asyncio
import html
import re
import socket
import time

import feedparser

from swag.models import Item

_UA = "Mozilla/5.0 (compatible; SwagBot/0.1; +https://github.com/BoomCoderchik/swag)"


def _clean(text: str, limit: int = 500) -> str:
    text = re.sub(r"<[^>]+>", " ", text or "")
    text = html.unescape(text)
    return re.sub(r"\s+", " ", text).strip()[:limit]


def _published_ts(entry) -> float | None:
    parsed = entry.get("published_parsed") or entry.get("updated_parsed")
    return time.mktime(parsed) if parsed else None


def _fetch_sync(name: str, url: str, limit: int) -> list[Item]:
    socket.setdefaulttimeout(30)
    feed = feedparser.parse(url, agent=_UA)
    items: list[Item] = []
    for entry in feed.entries[:limit]:
        link = entry.get("link")
        if not link:
            continue
        items.append(
            Item(
                source=f"rss:{name}",
                title=entry.get("title", ""),
                url=link,
                description=_clean(entry.get("summary", "")),
                published_ts=_published_ts(entry),
            )
        )
    return items


async def fetch_rss(name: str, url: str, limit: int = 10) -> list[Item]:
    return await asyncio.to_thread(_fetch_sync, name, url, limit)
