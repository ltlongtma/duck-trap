"""Generate an original macOS-style desktop image used as the built-in
default decoy. Run: python tools/make_default_decoy.py

This draws its own artwork (gradient wallpaper + menu bar + dock); it does not
copy any third-party screenshot. Replace duck_trap/assets/default_decoy.png
with your own screenshot any time if you prefer.
"""

from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter

W, H = 2560, 1600
OUT = Path(__file__).resolve().parent.parent / "duck_trap" / "assets" / "default_decoy.png"


def lerp(a, b, t):
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))


def wallpaper() -> Image.Image:
    # Diagonal gradient reminiscent of a modern macOS wallpaper.
    top = (44, 62, 120)     # deep blue
    mid = (120, 86, 168)    # purple
    bot = (222, 132, 120)   # warm coral
    img = Image.new("RGB", (W, H))
    px = img.load()
    for y in range(H):
        t = y / (H - 1)
        if t < 0.5:
            c = lerp(top, mid, t / 0.5)
        else:
            c = lerp(mid, bot, (t - 0.5) / 0.5)
        for x in range(W):
            px[x, y] = c
    # Soft glow in the upper area.
    glow = Image.new("L", (W, H), 0)
    gd = ImageDraw.Draw(glow)
    gd.ellipse([W * 0.55, -H * 0.25, W * 1.15, H * 0.55], fill=120)
    glow = glow.filter(ImageFilter.GaussianBlur(220))
    light = Image.new("RGB", (W, H), (255, 240, 210))
    img = Image.composite(light, img, glow)
    return img


def rounded(draw, box, radius, fill):
    draw.rounded_rectangle(box, radius=radius, fill=fill)


def draw_menubar(img):
    d = ImageDraw.Draw(img, "RGBA")
    bar_h = 36
    d.rectangle([0, 0, W, bar_h], fill=(255, 255, 255, 40))
    d.rectangle([0, 0, W, bar_h], fill=(20, 20, 30, 60))
    # Left menu items (as simple bars, no real logos).
    x = 24
    for wdt in (16, 60, 40, 40, 46, 52):
        d.rounded_rectangle([x, 12, x + wdt, 24], radius=3, fill=(255, 255, 255, 210))
        x += wdt + 20
    # Right status items + clock.
    x = W - 30
    for wdt in (70, 26, 26, 30):
        d.rounded_rectangle([x - wdt, 12, x, 24], radius=3, fill=(255, 255, 255, 200))
        x -= wdt + 18


def draw_dock(img):
    d = ImageDraw.Draw(img, "RGBA")
    n = 12
    icon = 92
    gap = 22
    dock_w = n * icon + (n + 1) * gap
    dock_h = icon + 2 * gap
    x0 = (W - dock_w) // 2
    y0 = H - dock_h - 26
    rounded(d, [x0, y0, x0 + dock_w, y0 + dock_h], 34, (255, 255, 255, 45))
    palette = [
        (94, 154, 255), (255, 138, 128), (126, 211, 155), (255, 205, 96),
        (186, 140, 255), (96, 214, 214), (255, 168, 96), (140, 176, 255),
        (255, 122, 170), (120, 200, 120), (200, 200, 210), (110, 130, 160),
    ]
    x = x0 + gap
    y = y0 + gap
    for i in range(n):
        c = palette[i % len(palette)]
        rounded(d, [x, y, x + icon, y + icon], 22, c + (255,))
        # subtle top highlight
        d.rounded_rectangle([x + 8, y + 8, x + icon - 8, y + icon // 2],
                            radius=14, fill=(255, 255, 255, 40))
        x += icon + gap


def main():
    OUT.parent.mkdir(parents=True, exist_ok=True)
    img = wallpaper()
    draw_menubar(img)
    draw_dock(img)
    # Downscale a touch for smoothing, then save.
    img.save(OUT, "PNG", optimize=True)
    print(f"Wrote {OUT} ({OUT.stat().st_size // 1024} KB)")


if __name__ == "__main__":
    main()
