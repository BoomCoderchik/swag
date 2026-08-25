from swag.publisher import build_caption


def test_caption_within_limit():
    caption = build_caption(
        "owner/repo",
        "очень длинное описание " * 200,
        "⭐ 100 · 🍴 10 · Python",
        "https://github.com/x/y",
        ["ai", "free-tier"],
    )
    assert len(caption) <= 1024
    assert "<b>owner/repo</b>" in caption
    assert "#ai" in caption
    assert "#free_tier" in caption
    assert "…" in caption


def test_caption_short_description_kept():
    caption = build_caption("repo", "Короткое описание", "", "https://example.com", [])
    assert "Короткое описание" in caption
    assert "https://example.com" in caption


def test_caption_escapes_html():
    caption = build_caption("a<b> & c", "desc & <tag>", "", "https://e.com/?a=1&b=2", [])
    assert "<b>a&lt;b&gt; &amp; c</b>" in caption
    assert "desc &amp; &lt;tag&gt;" in caption
