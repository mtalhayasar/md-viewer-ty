"""Uygulama ve .md dosya ikonlarını üretir: assets/icon.ico, assets/md-file.ico, assets/icon.png

Kullanım: python tools/make_icons.py
"""
from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter

ROOT = Path(__file__).resolve().parent.parent
ASSETS = ROOT / "assets"
UI = ROOT / "mdviewer" / "ui"

S = 1024  # çizim tuvali; küçük boyutlara yüksek kaliteyle indirgenir
ACCENT_TOP = (205, 104, 58)
ACCENT_BOTTOM = (156, 62, 26)
PAPER = (253, 249, 241)
INK = (43, 39, 34)
LINE = (214, 200, 182)
ICO_SIZES = [16, 20, 24, 32, 40, 48, 64, 96, 128, 256]


def gradient(size: int, top: tuple, bottom: tuple) -> Image.Image:
    g = Image.new("RGB", (1, size))
    for y in range(size):
        t = y / (size - 1)
        g.putpixel((0, y), tuple(round(a + (b - a) * t) for a, b in zip(top, bottom)))
    return g.resize((size, size))


def rounded_mask(size: int, box: tuple, radius: int) -> Image.Image:
    m = Image.new("L", (size, size), 0)
    ImageDraw.Draw(m).rounded_rectangle(box, radius=radius, fill=255)
    return m


def page_polygon(x0, y0, x1, y1, fold):
    return [(x0, y0), (x1 - fold, y0), (x1, y0 + fold), (x1, y1), (x0, y1)]


def draw_markdown_mark(d: ImageDraw.ImageDraw, cx: float, cy: float, w: float, color, stroke: float):
    """Markdown'ın 'M↓' işareti: köşeli bir M ve aşağı ok."""
    h = w * 0.62
    mw = w * 0.56
    x0, y0 = cx - w / 2, cy - h / 2
    x1, y1 = x0 + mw, y0 + h
    mid = x0 + mw / 2
    d.line([(x0, y1), (x0, y0), (mid, y0 + h * 0.5), (x1, y0), (x1, y1)],
           fill=color, width=round(stroke), joint="curve")
    # ok
    ax = x1 + (w - mw) * 0.55
    d.line([(ax, y0), (ax, y1 - stroke * 0.6)], fill=color, width=round(stroke))
    aw = (w - mw) * 0.42
    d.polygon([(ax - aw - stroke * 0.25, y1 - h * 0.38), (ax + aw + stroke * 0.25, y1 - h * 0.38), (ax, y1 + stroke * 0.15)],
              fill=color)


def app_icon(detail: bool = True) -> Image.Image:
    img = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    pad = 56 if detail else 8
    tile = (pad, pad, S - pad, S - pad)

    if detail:  # yumuşak gölge; küçük boyutlarda bulanıklık yaratmasın diye yalnızca büyüklerde
        shadow = Image.new("RGBA", (S, S), (0, 0, 0, 0))
        ImageDraw.Draw(shadow).rounded_rectangle((pad, pad + 24, S - pad, S - pad + 24), radius=210, fill=(90, 40, 15, 110))
        img.alpha_composite(shadow.filter(ImageFilter.GaussianBlur(28)))

    bg = gradient(S, ACCENT_TOP, ACCENT_BOTTOM).convert("RGBA")
    img.paste(bg, (0, 0), rounded_mask(S, tile, 210))

    # kâğıt
    px0, py0, px1, py1 = 250, 190, 774, 840
    fold = 150
    page = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    pd = ImageDraw.Draw(page)
    pd.polygon([(p[0], p[1] + 16) for p in page_polygon(px0, py0, px1, py1, fold)], fill=(70, 25, 5, 90))
    page = page.filter(ImageFilter.GaussianBlur(14))
    pd = ImageDraw.Draw(page)
    pd.polygon(page_polygon(px0, py0, px1, py1, fold), fill=PAPER)
    pd.polygon([(px1 - fold, py0), (px1 - fold, py0 + fold), (px1, py0 + fold)], fill=(232, 214, 192))
    img.alpha_composite(page)

    d = ImageDraw.Draw(img)
    if detail:
        draw_markdown_mark(d, (px0 + px1) / 2 - 10, 455, 330, ACCENT_BOTTOM, 46)
        for i, (y, frac) in enumerate([(640, 0.78), (712, 0.62)]):
            x = px0 + 78
            d.rounded_rectangle((x, y, x + (px1 - px0 - 156) * frac, y + 30), radius=15, fill=LINE)
    else:
        draw_markdown_mark(d, (px0 + px1) / 2 - 10, 520, 400, ACCENT_BOTTOM, 78)
    return img


def file_icon(detail: bool = True) -> Image.Image:
    img = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    px0, py0, px1, py1 = 170, 60, 854, 964
    fold = 220
    sh = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    ImageDraw.Draw(sh).polygon([(p[0], p[1] + 14) for p in page_polygon(px0, py0, px1, py1, fold)], fill=(0, 0, 0, 70))
    img.alpha_composite(sh.filter(ImageFilter.GaussianBlur(16)))
    d = ImageDraw.Draw(img)
    d.polygon(page_polygon(px0, py0, px1, py1, fold), fill=(255, 255, 255), outline=(200, 190, 178), width=10)
    d.polygon([(px1 - fold, py0), (px1 - fold, py0 + fold), (px1, py0 + fold)], fill=(236, 226, 212), outline=(200, 190, 178))
    # alt şerit
    band = (px0 + 5, 560, px1 - 5, 860)
    d.rectangle(band, fill=ACCENT_BOTTOM)
    draw_markdown_mark(d, (px0 + px1) / 2, 712, 400, PAPER, 56)
    if detail:
        for y, frac in [(300, 0.72), (380, 0.55), (460, 0.65)]:
            x = px0 + 100
            d.rounded_rectangle((x, y, x + (px1 - px0 - 200) * frac, y + 34), radius=17, fill=LINE)
    return img


def save_ico(make, path: Path) -> None:
    detailed = make(True)
    simple = make(False)
    frames = []
    for size in ICO_SIZES:
        src = detailed if size >= 40 else simple
        frames.append(src.resize((size, size), Image.LANCZOS))
    frames[-1].save(path, format="ICO", sizes=[(s, s) for s in ICO_SIZES], append_images=frames[:-1])


def main() -> None:
    ASSETS.mkdir(exist_ok=True)
    save_ico(app_icon, ASSETS / "icon.ico")
    save_ico(file_icon, ASSETS / "md-file.ico")
    big = app_icon(True)
    big.resize((512, 512), Image.LANCZOS).save(ASSETS / "icon.png")
    big.resize((256, 256), Image.LANCZOS).save(UI / "icon.png")
    # önizleme: farklı boyutlar yan yana
    sheet = Image.new("RGBA", (16 + 24 + 32 + 48 + 64 + 128 + 256 + 90, 300), (251, 248, 242, 255))
    x = 10
    for size in [16, 24, 32, 48, 64, 128, 256]:
        src = app_icon(size >= 40)
        sheet.alpha_composite(src.resize((size, size), Image.LANCZOS), (x, 280 - size))
        x += size + 12
    sheet.save(ASSETS / "icon-preview.png")
    print("İkonlar üretildi:", ASSETS)


if __name__ == "__main__":
    main()
