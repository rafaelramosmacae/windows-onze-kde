#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Onze store artwork: logo (mark and tile) and a promotional banner.

Output (tools/store-kit/logo/):
  onze-logo.svg / onze-logo-512.png / onze-logo-256.png   the mark (four diamonds), transparent
  onze-logo-tile.svg / onze-logo-tile-512.png             white mark on a blue rounded tile
  onze-banner-1920x1080.png                                wallpaper + mark + name (artwork, not a screenshot)

Requirements: pip install cairosvg pillow
"""
import io
import os

import cairosvg
from PIL import Image, ImageDraw, ImageFilter, ImageFont

KIT = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(KIT))
LOGO = os.path.join(KIT, "logo")
FONT_B = "/usr/share/fonts/opentype/inter/Inter-SemiBold.otf"
FONT_R = "/usr/share/fonts/opentype/inter/Inter-Regular.otf"


def diamonds(fill, size=64):
    r, gap = 12.2, 2.2
    o = r + gap / 1.41
    d = ""
    for dx, dy in ((0, -o), (o, 0), (0, o), (-o, 0)):
        cx, cy = 32 + dx, 32 + dy
        d += f"M{cx:.2f},{cy - r:.2f}L{cx + r:.2f},{cy:.2f}L{cx:.2f},{cy + r:.2f}L{cx - r:.2f},{cy:.2f}Z"
    return f'<path d="{d}" fill="{fill}" stroke="{fill}" stroke-width=".9" stroke-linejoin="round"/>'


def mark_svg():
    return ('<svg xmlns="http://www.w3.org/2000/svg" width="512" height="512" viewBox="0 0 64 64">'
            '<defs><linearGradient id="g" x1="0" y1="0" x2="1" y2="1">'
            '<stop offset="0" stop-color="#6CCBFF"/><stop offset="1" stop-color="#0A6CD6"/></linearGradient></defs>'
            + diamonds("url(#g)") + "</svg>\n")


def tile_svg():
    return ('<svg xmlns="http://www.w3.org/2000/svg" width="512" height="512" viewBox="0 0 64 64">'
            '<defs><linearGradient id="t" x1="0" y1="0" x2="1" y2="1">'
            '<stop offset="0" stop-color="#4CC2FF"/><stop offset="1" stop-color="#0A5BC4"/></linearGradient></defs>'
            '<rect x="0" y="0" width="64" height="64" rx="14" fill="url(#t)"/>'
            '<g transform="translate(32,32) scale(.62) translate(-32,-32)">' + diamonds("#FFFFFF") + "</g></svg>\n")


def png(svg, size):
    return Image.open(io.BytesIO(cairosvg.svg2png(bytestring=svg.encode(), output_width=size,
                                                  output_height=size))).convert("RGBA")


def banner():
    W, H = 1920, 1080
    wp = os.path.join(ROOT, "src", "wallpapers", "Onze", "contents", "images", "3840x2160.jpg")
    src = Image.open(wp).convert("RGBA").resize((1920, 1080), Image.LANCZOS)
    # background: soft light gradient; the wallpaper's sculpture sits on the right
    bg = Image.new("RGBA", (W, H))
    g = ImageDraw.Draw(bg)
    for y in range(H):
        t = y / H
        g.line([(0, y), (W, y)], fill=(int(238 - 14 * t), int(244 - 10 * t), 255, 255))
    crop = src.crop((300, 0, 1620, 1080))            # sculpture region
    shift = W - crop.width + 80
    mask = Image.new("L", crop.size, 255)
    md = ImageDraw.Draw(mask)
    fade = 360
    for x in range(fade):
        md.line([(x, 0), (x, crop.height)], fill=int(255 * (x / fade) ** 1.6))
    bg.paste(crop, (shift, 0), mask)
    img = bg
    mark = png(mark_svg(), 200)
    sh = Image.new("RGBA", img.size, (0, 0, 0, 0))
    sh.paste((10, 60, 140, 70), (132, 330), mark)
    sh = sh.filter(ImageFilter.GaussianBlur(14))
    img.alpha_composite(sh)
    img.alpha_composite(mark, (122, 312))
    d = ImageDraw.Draw(img)
    d.text((360, 300), "Onze", font=ImageFont.truetype(FONT_B, 150), fill=(20, 32, 48))
    d.text((128, 560), "Windows 11 style global theme", font=ImageFont.truetype(FONT_R, 50), fill=(35, 50, 70))
    d.text((128, 624), "for KDE Plasma 6", font=ImageFont.truetype(FONT_R, 50), fill=(35, 50, 70))
    small = ImageFont.truetype(FONT_R, 30)
    for i, line in enumerate(("Light & Dark  •  Centered taskbar", "Original icons and cursors")):
        d.text((130, 730 + i * 46), line, font=small, fill=(70, 88, 110))
    return img.convert("RGB")


def main():
    os.makedirs(LOGO, exist_ok=True)
    m, t = mark_svg(), tile_svg()
    open(os.path.join(LOGO, "onze-logo.svg"), "w").write(m)
    open(os.path.join(LOGO, "onze-logo-tile.svg"), "w").write(t)
    for s in (512, 256):
        png(m, s).save(os.path.join(LOGO, f"onze-logo-{s}.png"))
    png(t, 512).save(os.path.join(LOGO, "onze-logo-tile-512.png"))
    banner().save(os.path.join(LOGO, "onze-banner-1920x1080.png"))
    print("Artwork written to", LOGO)


if __name__ == "__main__":
    main()
