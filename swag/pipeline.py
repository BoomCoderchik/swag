import asyncio
import logging

import httpx

from swag.config import Settings
from swag.db import Database
from swag.fetchers.rss import fetch_rss
from swag.filter import has_free_signal_in_title, is_fresh, is_relevant
from swag.llm import score_relevance
from swag.models import Item
from swag.publisher import Publisher

logger = logging.getLogger(__name__)


async def _gather_items(sources: dict) -> list[Item]:
    tasks = [fetch_rss(feed["name"], feed["url"]) for feed in sources.get("rss") or []]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    items: list[Item] = []
    for result in results:
        if isinstance(result, BaseException):
            logger.warning("source failed: %s", result)
        else:
            items.extend(result)
    return items


async def _passes_quality(item: Item, settings: Settings, client: httpx.AsyncClient) -> bool:
    if not is_relevant(item):
        return False
    if not settings.gemini_api_key:
        return has_free_signal_in_title(item)
    verdict = await score_relevance(client, settings.gemini_api_key, settings.gemini_model, item)
    if verdict is None:
        return has_free_signal_in_title(item)
    relevant, score = verdict
    return relevant and score >= settings.min_llm_score


async def run_cycle(
    settings: Settings, db: Database, publisher: Publisher, sources: dict
) -> int:
    items = await _gather_items(sources)
    published = 0
    async with httpx.AsyncClient() as client:
        for item in items:
            if published >= settings.max_posts_per_cycle:
                logger.info("post cap reached (%d), stopping cycle", published)
                break
            if not item.title or db.is_published(item.url):
                continue
            if not is_fresh(item.published_ts, settings.fresh_hours):
                continue
            if not await _passes_quality(item, settings, client):
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
            await asyncio.sleep(3)
    logger.info("cycle done: %d fetched, %d published", len(items), published)
    return published
