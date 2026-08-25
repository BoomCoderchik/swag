import json
import logging

import httpx

from swag.models import Item

logger = logging.getLogger(__name__)

_NEWS_PROMPT = (
    "Новость рассматривается для Telegram-канала о халяве в мире ИИ (на русском языке).\n"
    "Сделай три вещи:\n"
    "1. Определи, сообщает ли новость именно о БЕСПЛАТНОМ: free tier или бесплатный доступ "
    "к ИИ-модели/сервису, бесплатные кредиты или промокоды, временная раздача/акция, "
    "выход бесплатной или open-source ИИ-модели. Обычные новости индустрии, бенчмарки, "
    "финансы, скандалы — not relevant.\n"
    "2. Поставь оценку релевантности 0-10.\n"
    "3. Если relevant=true, подготовь русскую версию: заголовок (короткий, цепляющий, "
    "названия продуктов не переводишь) и пересказ сути в 2-3 коротких предложениях "
    "простым языком, без воды и без вступлений. Если relevant=false — ru_title и "
    "ru_summary пустые строки.\n\n"
    "Заголовок: {title}\nОписание: {description}\n\n"
    "Ответь только JSON без пояснений:\n"
    '{{"relevant": true/false, "score": 0-10, "ru_title": "...", "ru_summary": "..."}}'
)

_GITHUB_PROMPT = (
    "GitHub-инструмент рассматривается для Telegram-канала про ИИ и вайбкодинг "
    "(на русском языке).\n"
    "Сделай три вещи:\n"
    "1. Определи, полезен ли инструмент для работы с нейросетями или вайбкодинга: "
    "AI-агенты, CLI-инструменты, LLM-библиотеки, MCP-серверы, автоматизация с ИИ, "
    "локальные модели. Обычные библиотеки без ИИ-темы, туториалы, списки ссылок — "
    "not relevant.\n"
    "2. Поставь оценку полезности 0-10.\n"
    "3. Если relevant=true, подготовь русскую версию: заголовок (имя репо оставь как есть, "
    "можно добавить короткое пояснение) и описание в 1-2 коротких предложениях простым "
    "языком — что делает и чем полезен. Если relevant=false — ru_title и ru_summary "
    "пустые строки.\n\n"
    "Репозиторий: {title}\nОписание: {description}\n\n"
    "Ответь только JSON без пояснений:\n"
    '{{"relevant": true/false, "score": 0-10, "ru_title": "...", "ru_summary": "..."}}'
)


def parse_verdict(text: str) -> tuple[bool, int, str, str] | None:
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end <= start:
        return None
    try:
        data = json.loads(text[start : end + 1])
        return (
            bool(data["relevant"]),
            int(data["score"]),
            str(data.get("ru_title", "")).strip(),
            str(data.get("ru_summary", "")).strip(),
        )
    except (ValueError, KeyError, TypeError):
        return None


async def analyze(
    client: httpx.AsyncClient, api_key: str, model: str, item: Item
) -> tuple[bool, int, str, str] | None:
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
    template = _GITHUB_PROMPT if item.kind == "github" else _NEWS_PROMPT
    payload = {
        "contents": [
            {
                "parts": [
                    {
                        "text": template.format(
                            title=item.title, description=item.description[:800]
                        )
                    }
                ]
            }
        ],
        "generationConfig": {"temperature": 0.2},
    }
    try:
        resp = await client.post(url, params={"key": api_key}, json=payload, timeout=30)
        resp.raise_for_status()
        parts = resp.json()["candidates"][0]["content"]["parts"]
        return parse_verdict("".join(p.get("text", "") for p in parts))
    except Exception as exc:
        logger.warning("llm analyze failed: %s", exc)
        return None
