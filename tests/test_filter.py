import asyncio

import httpx

from swag.config import Settings
from swag.filter import has_free_signal_in_title
from swag.llm import parse_verdict
from swag.models import Item


def _item(title: str, kind: str = "news") -> Item:
    return Item(source="rss", title=title, url="https://example.com/1", kind=kind)


def test_github_items_pass_without_llm_key():
    async def run() -> bool:
        from swag.pipeline import _enrich

        settings = Settings(gemini_api_key="", _env_file=None)
        async with httpx.AsyncClient() as client:
            return await _enrich(_item("owner/repo", kind="github"), settings, client)

    assert asyncio.run(run()) is True


def test_free_signal_in_title():
    assert has_free_signal_in_title(_item("Google makes Gemini free for a limited time"))
    assert has_free_signal_in_title(_item("Раздача бесплатных подписок на Copilot"))
    assert not has_free_signal_in_title(_item("New benchmarks for local LLM quants"))


def test_parse_verdict_full_json():
    verdict = parse_verdict(
        '{"relevant": true, "score": 8, "ru_title": "Gemini стал бесплатным",'
        ' "ru_summary": "Google открыла доступ. Ограничение по времени."}'
    )
    assert verdict == (True, 8, "Gemini стал бесплатным", "Google открыла доступ. Ограничение по времени.")


def test_parse_verdict_minimal_json():
    assert parse_verdict('{"relevant": false, "score": 2}') == (False, 2, "", "")


def test_parse_verdict_with_prose_and_fence():
    text = 'Вот вердикт:\n```json\n{"relevant": false, "score": 2}\n```'
    assert parse_verdict(text) == (False, 2, "", "")


def test_parse_verdict_garbage():
    assert parse_verdict("no json here") is None
    assert parse_verdict('{"relevant": "maybe"}') is None
