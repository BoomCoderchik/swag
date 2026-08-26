from PIL import Image

from swag.models import Item
from swag.renderer import render_card


def _github_item() -> Item:
    return Item(
        source="github",
        kind="github",
        title="owner/some-repo",
        url="https://github.com/owner/some-repo",
        description="AI coding agent that helps you write code " * 5,
        metrics="⭐ 149 · 🍴 11 · Python",
        tags=["ai", "llm"],
    )


def test_render_github_card(tmp_path):
    path = render_card(_github_item(), out_dir=tmp_path)
    assert path.exists()
    img = Image.open(path)
    assert img.size == (1280, 720)


def test_render_news_card(tmp_path):
    item = Item(
        source="rss:openai",
        kind="news",
        title="Google makes Gemini free for a limited time",
        url="https://example.com/news/1",
        description="Google announced free access to Gemini Advanced for all users this weekend.",
        published_ts=0.0,
    )
    path = render_card(item, out_dir=tmp_path)
    assert path.exists()
    assert (tmp_path / path.name).stat().st_size > 10_000


def test_render_long_title_fits(tmp_path):
    item = _github_item()
    item.title = "owner/" + "very-long-repo-name-word-" * 8
    path = render_card(item, out_dir=tmp_path)
    assert path.exists()
