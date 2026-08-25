from pathlib import Path

from swag.db import Database
from swag.models import Item


def test_add_dedup(tmp_path: Path):
    db = Database(tmp_path / "test.db")
    item = Item(source="github", title="a/b", url="https://github.com/a/b")
    assert db.add(item) is True
    assert db.add(item) is False


def test_mark_published(tmp_path: Path):
    db = Database(tmp_path / "test.db")
    item = Item(source="rss", title="t", url="https://example.com/post")
    db.add(item)
    assert db.is_published(item.url) is False
    db.mark_published(item.url)
    assert db.is_published(item.url) is True


def test_url_hash_normalization():
    from swag.db import url_hash

    assert url_hash("https://GitHub.com/a/b/") == url_hash("https://github.com/a/b")
