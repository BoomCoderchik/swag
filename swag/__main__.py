import argparse
import asyncio
import logging
import sys

from apscheduler.schedulers.asyncio import AsyncIOScheduler

from swag.config import load_settings
from swag.db import Database
from swag.pipeline import run_cycle
from swag.publisher import Publisher
from swag.sources import load_sources


async def main() -> None:
    parser = argparse.ArgumentParser(prog="swag")
    parser.add_argument("--once", action="store_true", help="run a single cycle and exit")
    args = parser.parse_args()

    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")

    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s"
    )
    settings = load_settings()
    db = Database(settings.db_path)
    publisher = Publisher(settings.bot_token, settings.channel_id, settings.dry_run)
    sources = load_sources()

    if args.once:
        await run_cycle(settings, db, publisher, sources)
        return

    scheduler = AsyncIOScheduler(timezone=settings.timezone)
    scheduler.add_job(
        run_cycle,
        "interval",
        minutes=settings.poll_interval_min,
        args=(settings, db, publisher, sources),
        next_run_time=None,
    )
    scheduler.start()
    logging.info(
        "scheduler started: every %d min, dry_run=%s", settings.poll_interval_min, settings.dry_run
    )
    await asyncio.Event().wait()


if __name__ == "__main__":
    asyncio.run(main())
