import hashlib
import sqlite3
from pathlib import Path

from swag.models import Item

_SCHEMA = """
CREATE TABLE IF NOT EXISTS posts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    url_hash TEXT UNIQUE NOT NULL,
    source TEXT NOT NULL,
    title TEXT NOT NULL,
    url TEXT NOT NULL,
    description TEXT,
    metrics TEXT,
    tags TEXT,
    status TEXT NOT NULL DEFAULT 'new',
    created_at TEXT DEFAULT (datetime('now')),
    published_at TEXT
);
CREATE INDEX IF NOT EXISTS idx_posts_status ON posts(status);
"""


def url_hash(url: str) -> str:
    normalized = url.strip().rstrip("/").lower()
    return hashlib.sha256(normalized.encode()).hexdigest()


class Database:
    def __init__(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(path)
        self._conn.executescript(_SCHEMA)
        self._conn.commit()

    def add(self, item: Item) -> bool:
        try:
            self._conn.execute(
                "INSERT INTO posts (url_hash, source, title, url, description, metrics, tags)"
                " VALUES (?, ?, ?, ?, ?, ?, ?)",
                (
                    url_hash(item.url),
                    item.source,
                    item.title,
                    item.url,
                    item.description,
                    item.metrics,
                    ",".join(item.tags),
                ),
            )
            self._conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False

    def mark_published(self, url: str) -> None:
        self._conn.execute(
            "UPDATE posts SET status = 'published', published_at = datetime('now')"
            " WHERE url_hash = ?",
            (url_hash(url),),
        )
        self._conn.commit()

    def is_published(self, url: str) -> bool:
        row = self._conn.execute(
            "SELECT status FROM posts WHERE url_hash = ?", (url_hash(url),)
        ).fetchone()
        return bool(row) and row[0] == "published"
