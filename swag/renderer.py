import re
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

from swag.db import url_hash
from swag.models import Item

W, H = 1280, 720
MARGIN = 80
BG = (6, 6, 6)
WHITE = (245, 245, 245)
GRAY = (178, 178, 178)
DIM = (110, 110, 110)
AURORA_HUES = ((255, 233, 92), (255, 90, 60), (61, 220, 132))
FONT_PATH = Path(__file__).resolve().parent.parent / "assets" / "fonts" / "Inter.ttf"
HEADER_TEXT = "SWAG AI — FREE AI RADAR"
TAG_TEXT = "#SWAGAI"


def _font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    font = ImageFont.truetype(str(FONT_PATH), size)
    try:
        font.set_variation_by_name("Bold" if bold else "Regular")
    except Exception:
        pass
    return font


def _aurora_layer() -> Image.Image:
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    draw = ImageDraw.Draw(layer)
    blobs = (
        ((60, -160, 760, 320), AURORA_HUES[0], 200),
        ((240, -60, 900, 420), AURORA_HUES[1], 170),
        ((-180, 60, 420, 520), AURORA_HUES[2], 150),
    )
    for box, color, alpha in blobs:
        draw.ellipse(box, fill=color + (alpha,))
    return layer.filter(ImageFilter.GaussianBlur(110))


def _tracked(draw: ImageDraw.ImageDraw, pos: tuple[int, int], text: str, font, fill) -> None:
    x, y = pos
    for ch in text:
        draw.text((x, y), ch, font=font, fill=fill)
        x += draw.textlength(ch, font=font) + 5


def _wrap(text: str, font, max_w: int) -> list[str]:
    lines: list[str] = []
    for raw_line in text.splitlines():
        current = ""
        for word in raw_line.split():
            candidate = f"{current} {word}".strip()
            if font.getlength(candidate) <= max_w or not current:
                current = candidate
            else:
                lines.append(current)
                current = word
        lines.append(current)
    return lines


def _fit_block(text: str, bold: bool, max_w: int, max_lines: int, size_hi: int, size_lo: int):
    for size in range(size_hi, size_lo, -4):
        font = _font(size, bold=bold)
        lines = _wrap(text, font, max_w)
        if len(lines) <= max_lines:
            return font, lines[:max_lines]
    font = _font(size_lo, bold=bold)
    lines = _wrap(text, font, max_w)[:max_lines]
    lines[-1] = lines[-1][: len(lines[-1]) - 1].rstrip() + "…"
    return font, lines


def _stats_line(item: Item) -> str:
    if item.kind != "github":
        return "AI NEWS"
    stars = re.search(r"⭐\s*(\d+)", item.metrics)
    forks = re.search(r"🍴\s*(\d+)", item.metrics)
    lang = re.search(r"·\s*([^\s·][^·]*)$", item.metrics)
    parts = []
    if stars:
        parts.append(f"STARS {stars.group(1)}")
    if forks:
        parts.append(f"FORKS {forks.group(1)}")
    if lang:
        parts.append(lang.group(1).strip().upper())
    return " · ".join(parts) or "GITHUB"


def render_card(item: Item, out_dir: Path | None = None) -> Path:
    out_dir = out_dir or Path("cards")
    out_dir.mkdir(parents=True, exist_ok=True)
    img = Image.alpha_composite(
        Image.new("RGBA", (W, H), BG + (255,)), _aurora_layer()
    ).convert("RGB")
    draw = ImageDraw.Draw(img)

    _tracked(draw, (MARGIN, 58), HEADER_TEXT, _font(22), GRAY)

    title = (item.ru_title or item.title).strip()
    title_font, title_lines = _fit_block(title, True, W - 2 * MARGIN, 3, 92, 46)
    y = 190
    for line in title_lines:
        draw.text((MARGIN, y), line, font=title_font, fill=WHITE)
        y += int(title_font.size * 1.08)

    desc = (item.ru_summary or item.description).strip()
    if desc:
        y += 18
        desc_font, desc_lines = _fit_block(desc, False, W - 2 * MARGIN, 3, 30, 20)
        for line in desc_lines:
            draw.text((MARGIN, y), line, font=desc_font, fill=GRAY)
            y += int(desc_font.size * 1.35)

    _tracked(draw, (MARGIN, H - 150), _stats_line(item), _font(26), WHITE)

    tag_font = _font(24)
    tag_w = draw.textlength(TAG_TEXT, font=tag_font) + 5 * (len(TAG_TEXT) - 1)
    _tracked(draw, (int((W - tag_w) / 2), H - 78), TAG_TEXT, tag_font, GRAY)

    path = out_dir / f"{url_hash(item.url)[:16]}.png"
    img.save(path, "PNG", optimize=True)
    return path
