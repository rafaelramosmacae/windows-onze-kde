#!/usr/bin/env python3
"""
Onze Icons — showcase image with the main icons (1920x1080), for the README and the store gallery.

Draws straight from the SVGs produced by gerar_icones.py (nothing else is used).
Requirements: pip install matplotlib cairosvg pillow
Usage:        python3 tools/make-icon-showcase.py [output.png]   (default: tools/onze-icons-showcase.png)
"""
import io
import os
import sys

import cairosvg
from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gerar_icones as g  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, "tools", "onze-icons-showcase.png")
FONTS = "/usr/share/fonts/opentype/inter/"
S = 2  # supersampling

ROWS = [
    ("Folders", [("folder", "Folder"), ("folder-documents", "Documents"), ("folder-download", "Downloads"),
                 ("folder-music", "Music"), ("folder-pictures", "Pictures"), ("folder-videos", "Videos"),
                 ("folder-desktop", "Desktop"), ("folder-cloud", "Cloud"), ("folder-development", "Code"),
                 ("user-home", "Home"), ("user-trash", "Trash"), ("user-trash-full", "Trash (full)")]),
    ("Apps", [("system-file-manager", "Files"), ("utilities-terminal", "Terminal"),
              ("preferences-system", "Settings"), ("system-software-install", "Software"),
              ("accessories-text-editor", "Text editor"), ("internet-web-browser", "Browser"),
              ("utilities-system-monitor", "System monitor"), ("accessories-calculator", "Calculator"),
              ("utilities-archiver", "Archiver"), ("image-viewer", "Image viewer"),
              ("document-viewer", "Document viewer"), ("applets-screenshooter", "Screenshot")]),
    ("Files", [("text-x-generic", "Text"), ("application-pdf", "PDF"), ("x-office-document", "Document"),
               ("x-office-spreadsheet", "Spreadsheet"), ("x-office-presentation", "Presentation"),
               ("image-x-generic", "Image"), ("audio-x-generic", "Audio"), ("video-x-generic", "Video"),
               ("package-x-generic", "Archive"), ("text-x-python", "Python"), ("text-html", "Web page"),
               ("application-x-executable", "Program")]),
    ("Devices", [("computer", "Computer"), ("computer-laptop", "Laptop"), ("drive-harddisk", "Hard disk"),
                 ("drive-removable-media", "USB drive"), ("media-optical", "Disc"), ("phone", "Phone"),
                 ("input-keyboard", "Keyboard"), ("printer", "Printer"), ("camera-photo", "Camera"),
                 ("audio-headphones", "Headphones"), ("input-gaming", "Gamepad"), ("network-wired", "Network")]),
]
DIALOGS = ["dialog-information", "dialog-warning", "dialog-error", "dialog-question", "dialog-ok",
           "security-high", "security-medium", "security-low"]


def font(name, size):
    return ImageFont.truetype(FONTS + f"Inter-{name}.otf", size * S)


def render(svg, px):
    png = cairosvg.svg2png(bytestring=svg.encode(), output_width=px * S, output_height=px * S)
    return Image.open(io.BytesIO(png)).convert("RGBA")


def card(d, box, fill, outline=None):
    x0, y0, x1, y1 = (v * S for v in box)
    d.rounded_rectangle((x0, y0, x1, y1), radius=14 * S, fill=fill, outline=outline, width=S)


def main():
    icons, _ = g.build()
    svgs = {n: s for d in icons.values() for n, s in d.items()}
    W, H = 1920, 1080
    im = Image.new("RGBA", (W * S, H * S), (243, 243, 243, 255))
    d = ImageDraw.Draw(im)
    text = lambda xy, t, f, c, anchor="la": d.text((xy[0] * S, xy[1] * S), t, font=f, fill=c, anchor=anchor)
    paste = lambda img, x, y: im.alpha_composite(img, (int(x * S), int(y * S)))

    # header
    paste(render(svgs["start-here"], 64), 70, 46)
    text((152, 50), "Onze Icons", font("Bold", 40), (28, 28, 28))
    text((154, 100), "Original icon theme of the Onze global theme for KDE Plasma 6 — drawn from scratch, "
         "light & dark", font("Regular", 18), (96, 96, 96))
    n_draw = sum(len(v) for v in icons.values()) + len(g.SESSION_ICONS)
    text((W - 70, 62), f"{n_draw} drawings", font("SemiBold", 22), (0, 95, 184), "ra")
    text((W - 70, 94), "all scalable (SVG)", font("Regular", 16), (110, 110, 110), "ra")

    # icon rows
    y, cell, x0 = 160, 138, 214
    lab, small = font("SemiBold", 18), font("Regular", 13)
    for title, items in ROWS:
        card(d, (50, y, W - 50, y + 156), (255, 255, 255), (229, 229, 229))
        text((76, y + 66), title, lab, (40, 40, 40))
        for i, (name, label) in enumerate(items):
            cx = x0 + i * cell + cell / 2
            paste(render(svgs[name], 72), cx - 36, y + 22)
            text((cx, y + 112), label, small, (80, 80, 80), "ma")
        y += 172

    # bottom: dialogs + session buttons (light and dark)
    yb = y + 4
    card(d, (50, yb, 700, yb + 168), (255, 255, 255), (229, 229, 229))
    text((76, yb + 20), "Dialogs & security", lab, (40, 40, 40))
    for i, n in enumerate(DIALOGS):
        paste(render(svgs[n], 56), 80 + i * 76, yb + 66)

    kinds = [("suspend", "Sleep"), ("reboot", "Restart"), ("shutdown", "Shut down"), ("lock-screen", "Lock"),
             ("log-out", "Log out"), ("switch-user", "Switch user")]
    for k, (x, bg, fg, var) in enumerate(((716, (255, 255, 255), (40, 40, 40), "light"),
                                          (1300, (32, 32, 32), (235, 235, 235), "dark"))):
        card(d, (x, yb, x + 570, yb + 168), bg, (229, 229, 229) if var == "light" else None)
        text((x + 26, yb + 20), "Start menu — " + var, lab, fg)
        for i, (kind, label) in enumerate(kinds):
            cx = x + 70 + i * 86
            paste(render(g.session_icon(kind, g.SESSION_COLOR[var]), 32), cx - 16, yb + 70)
            text((cx, yb + 118), label, small, fg, "ma")

    text((W / 2, H - 30), "© 2026 Projeto Onze — Rafael Carvalho Ramos · GPL-3.0-or-later",
         font("Regular", 13), (130, 130, 130), "ma")
    im.resize((W, H), Image.LANCZOS).convert("RGB").save(OUT, optimize=True)
    print("Showcase:", OUT)


if __name__ == "__main__":
    main()
