import asyncio
from datetime import UTC, datetime, timedelta

import httpx

from swag.models import Item

_API = "https://api.github.com/search/repositories"


async def _search(client: httpx.AsyncClient, params: dict) -> dict:
    resp = await client.get(_API, params=params)
    if resp.status_code == 401:
        client.headers.pop("Authorization", None)
        resp = await client.get(_API, params=params)
    resp.raise_for_status()
    return resp.json()


async def fetch_github(
    topics: list[str],
    days: int,
    min_stars: int,
    max_results: int,
    token: str = "",
) -> list[Item]:
    since = (datetime.now(UTC) - timedelta(days=days)).strftime("%Y-%m-%d")
    headers = {"Accept": "application/vnd.github+json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    items: list[Item] = []
    async with httpx.AsyncClient(headers=headers, timeout=30) as client:
        for topic in topics:
            params = {
                "q": f"topic:{topic} created:>{since} stars:>={min_stars}",
                "sort": "stars",
                "order": "desc",
                "per_page": max_results,
            }
            data = await _search(client, params)
            for repo in data.get("items", []):
                created = datetime.fromisoformat(repo["created_at"].replace("Z", "+00:00"))
                items.append(
                    Item(
                        source="github",
                        kind="github",
                        title=repo["full_name"],
                        url=repo["html_url"],
                        description=repo.get("description") or "",
                        metrics=(
                            f"⭐ {repo.get('stargazers_count', 0)}"
                            f" · 🍴 {repo.get('forks_count', 0)}"
                            f" · {repo.get('language') or '—'}"
                        ),
                        tags=repo.get("topics", [])[:4],
                        published_ts=created.timestamp(),
                    )
                )
            await asyncio.sleep(2)
    return items
