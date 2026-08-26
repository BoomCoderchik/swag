import html

from aiogram.types import FSInputFile

MAX_CAPTION = 1024


def build_caption(
    title: str,
    description: str,
    metrics: str,
    url: str,
    tags: list[str],
    link_text: str = "Читать",
) -> str:
    safe_title = html.escape(title.strip())
    safe_url = html.escape(url.strip(), quote=True)
    link_line = f'\n\n🔗 <a href="{safe_url}">{html.escape(link_text)}</a>'
    metrics_line = f"\n\n{metrics}" if metrics else ""
    hashtags = " ".join("#" + t.replace("-", "_") for t in tags)
    tags_line = f"\n\n{hashtags}" if hashtags else ""
    overhead = (
        len(safe_title)
        + len("<b></b>")
        + 2
        + len(link_line)
        + len(metrics_line)
        + len(tags_line)
    )
    budget = max(MAX_CAPTION - overhead, 0)
    desc = html.escape(description.strip())
    if len(desc) > budget:
        desc = desc[: budget - 1].rstrip() + "…"
    body = f"<b>{safe_title}</b>"
    if desc:
        body += f"\n\n{desc}"
    return body + metrics_line + link_line + tags_line


class Publisher:
    def __init__(self, bot_token: str, channel_id: str, dry_run: bool = True) -> None:
        self._channel_id = channel_id
        self._dry_run = dry_run
        self._bot = None
        if not dry_run:
            from aiogram import Bot

            self._bot = Bot(bot_token)

    async def publish(
        self,
        title: str,
        description: str,
        metrics: str,
        url: str,
        tags: list[str],
        link_text: str = "Читать",
        card_path=None,
    ) -> None:
        caption = build_caption(title, description, metrics, url, tags, link_text)
        if self._dry_run:
            print(f"[DRY RUN] {url}\n{caption}\n{'-' * 60}")
            return
        if card_path is not None:
            await self._bot.send_photo(
                chat_id=self._channel_id,
                photo=FSInputFile(card_path),
                caption=caption,
                parse_mode="HTML",
            )
            return
        await self._bot.send_message(
            chat_id=self._channel_id, text=caption, parse_mode="HTML"
        )
