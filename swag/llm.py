import json
import logging

import httpx

from swag.models import Item

logger = logging.getLogger(__name__)

_PROMPT = (
    "Новость рассматривается для Telegram-канала о халяве в мире ИИ. "
    "Определи, сообщает ли новость именно о БЕСПЛАТНОМ: free tier или бесплатный доступ "
    "к ИИ-модели/сервису, бесплатные кредиты или промокоды, временная раздача/акция, "
    "выход бесплатной или open-source ИИ-модели. Обычные новости индустрии, бенчмарки, "
    "финансы, скандалы — not relevant.\n\n"
    "Заголовок: {title}\nОписание: {description}\n\n"
    'Ответь только JSON: {{"relevant": true/false, "score": 0-10}}'
)


def parse_verdict(text: str) -> tuple[bool, int] | None:
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end <= start:
        return None
    try:
        data = json.loads(text[start : end + 1])
        return bool(data["relevant"]), int(data["score"])
    except (ValueError, KeyError, TypeError):
        return None


async def score_relevance(
    client: httpx.AsyncClient, api_key: str, model: str, item: Item
) -> tuple[bool, int] | None:
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
    payload = {
        "contents": [
            {
                "parts": [
                    {
                        "text": _PROMPT.format(
                            title=item.title, description=item.description[:800]
                        )
                    }
                ]
            }
        ],
        "generationConfig": {"temperature": 0},
    }
    try:
        resp = await client.post(url, params={"key": api_key}, json=payload, timeout=30)
        resp.raise_for_status()
        parts = resp.json()["candidates"][0]["content"]["parts"]
        return parse_verdict("".join(p.get("text", "") for p in parts))
    except Exception as exc:
        logger.warning("llm scoring failed: %s", exc)
        return None
