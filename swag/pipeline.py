import asyncio
import logging

from swag.config import Settings
from swag.db import Database
from swag.fetchers.github import fetch_github
from swag.fetchers.rss import fetch_rss
from swag.models import Item
from swag.publisher import Publisher

logger = logging.getLogger(__name__)


async def _gather_items(settings: Settings, sources: dict) -> list[Item]:
    tasks = []
    gh = sources.get("github") or {}
    if gh.get("topics"):
        tasks.append(
            fetch_github(
                topics=gh["topics"],
                days=gh.get("days", 7),
                min_stars=gh.get("min_stars", 0),
                max_results=gh.get("max_results", 15),
                token=settings.github_token,
            )
        )
    for feed in sources.get("rss") or []:
        tasks.append(fetch_rss(feed["name"], feed["url"]))
    results = await asyncio.gather(*tasks, return_exceptions=True)
    items: list[Item] = []
    for result in results:
        if isinstance(result, BaseException):
            logger.warning("source failed: %s", result)
        else:
            items.extend(result)
    return items


async def run_cycle(
    settings: Settings, db: Database, publisher: Publisher, sources: dict
) -> int:
    items = await _gather_items(settings, sources)
    published = 0
    for item in items:
        if not item.title or db.is_published(item.url):
            continue
        try:
            await publisher.publish(
                title=item.title,
                description=item.description,
                metrics=item.metrics,
                url=item.url,
                tags=item.tags,
            )
            db.add(item)
            db.mark_published(item.url)
            published += 1
        except Exception:
            logger.exception("failed to publish %s", item.url)
    logger.info("cycle done: %d fetched, %d published", len(items), published)
    return published
