#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Onze Icons — original icon theme generator (Fluent / Windows 11 inspired).

Every icon is drawn from scratch by this script (geometry + gradients). Nothing
is copied or traced from other icon themes. Text labels on file-type icons are
converted to outlines from the Inter font (SIL Open Font License).

Output:
  src/icons/OnzeIcons/        light variant (falls back to Breeze)
  src/icons/OnzeIcons-Dark/   dark variant (same drawings, falls back to Breeze Dark)
  tools/previa-icones.png     contact sheet for review (not installed)

Requirements: pip install matplotlib cairosvg pillow
Usage:        python3 tools/gerar_icones.py
"""
import math
import os
import shutil

from matplotlib.font_manager import FontProperties
from matplotlib.textpath import TextPath

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "src", "icons")
LIGHT = os.path.join(OUT, "OnzeIcons")
DARK = os.path.join(OUT, "OnzeIcons-Dark")
VERSION = "1.3"
FONT = "/usr/share/fonts/opentype/inter/Inter-Bold.otf"

# --------------------------------------------------------------------------------
# SVG helpers
# --------------------------------------------------------------------------------
class Icon:
    """Collects gradients and shapes for one 64x64 icon."""

    def __init__(self):
        self.defs, self.body, self.n = [], [], 0

    def grad(self, c1, c2, x1=0, y1=0, x2=0, y2=1):
        self.n += 1
        gid = f"g{self.n}"
        self.defs.append(
            f'<linearGradient id="{gid}" x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}">'
            f'<stop offset="0" stop-color="{c1}"/><stop offset="1" stop-color="{c2}"/></linearGradient>')
        return f"url(#{gid})"

    def rgrad(self, c1, c2, cx=0.5, cy=0.5, r=0.5):
        self.n += 1
        gid = f"g{self.n}"
        self.defs.append(
            f'<radialGradient id="{gid}" cx="{cx}" cy="{cy}" r="{r}">'
            f'<stop offset="0" stop-color="{c1}"/><stop offset="1" stop-color="{c2}"/></radialGradient>')
        return f"url(#{gid})"

    def add(self, s):
        self.body.append(s)
        return self

    def rect(self, x, y, w, h, r, fill, op=1, stroke=None, sw=1):
        st = f' stroke="{stroke}" stroke-width="{sw}"' if stroke else ""
        o = f' opacity="{op}"' if op < 1 else ""
        return self.add(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{r}" fill="{fill}"{st}{o}/>')

    def circle(self, cx, cy, r, fill, op=1, stroke=None, sw=1):
        st = f' stroke="{stroke}" stroke-width="{sw}"' if stroke else ""
        o = f' opacity="{op}"' if op < 1 else ""
        return self.add(f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="{fill}"{st}{o}/>')

    def path(self, d, fill="none", op=1, stroke=None, sw=1, cap="round", join="round", rule=None):
        st = (f' stroke="{stroke}" stroke-width="{sw}" stroke-linecap="{cap}" stroke-linejoin="{join}"'
              if stroke else "")
        o = f' opacity="{op}"' if op < 1 else ""
        fr = f' fill-rule="{rule}"' if rule else ""
        return self.add(f'<path d="{d}" fill="{fill}"{st}{o}{fr}/>')

    def group(self, inner, transform):
        return self.add(f'<g transform="{transform}">{inner}</g>')

    def svg(self, size=64):
        d = f"<defs>{''.join(self.defs)}</defs>" if self.defs else ""
        return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{size}" height="{size}" '
                f'viewBox="0 0 64 64">{d}{"".join(self.body)}</svg>\n')


def text_d(txt, size, cx, cy):
    """Text converted to outline path data, centered at (cx, cy)."""
    tp = TextPath((0, 0), txt, size=size, prop=FontProperties(fname=FONT))
    ext = tp.get_extents()
    ox = cx - (ext.x0 + ext.x1) / 2
    oy = cy + (ext.y0 + ext.y1) / 2
    parts, verts = [], tp.vertices
    i = 0
    codes = tp.codes
    while i < len(codes):
        c = codes[i]
        x, y = verts[i]
        X, Y = x + ox, oy - y
        if c == 1:
            parts.append(f"M{X:.2f},{Y:.2f}")
            i += 1
        elif c == 2:
            parts.append(f"L{X:.2f},{Y:.2f}")
            i += 1
        elif c == 3:
            x2, y2 = verts[i + 1]
            parts.append(f"Q{X:.2f},{Y:.2f} {x2 + ox:.2f},{oy - y2:.2f}")
            i += 2
        elif c == 4:
            (x2, y2), (x3, y3) = verts[i + 1], verts[i + 2]
            parts.append(f"C{X:.2f},{Y:.2f} {x2 + ox:.2f},{oy - y2:.2f} {x3 + ox:.2f},{oy - y3:.2f}")
            i += 3
        elif c == 79:
            parts.append("Z")
            i += 1
        else:
            i += 1
    return "".join(parts)


def rrpath(x, y, w, h, r):
    return (f"M{x + r},{y}H{x + w - r}A{r},{r} 0 0 1 {x + w},{y + r}V{y + h - r}"
            f"A{r},{r} 0 0 1 {x + w - r},{y + h}H{x + r}A{r},{r} 0 0 1 {x},{y + h - r}"
            f"V{y + r}A{r},{r} 0 0 1 {x + r},{y}Z")


# --------------------------------------------------------------------------------
# Glyphs: white pictograms drawn in a 24x24 box (used on badges, tiles, pages)
# --------------------------------------------------------------------------------
def glyph(name, color="#FFFFFF", sw=2.2):
    s = f'stroke="{color}" stroke-width="{sw}" stroke-linecap="round" stroke-linejoin="round" fill="none"'
    f = f'fill="{color}"'
    g = {
        "doc": f'<path {s} d="M6 6h12M6 11h12M6 16h8"/>',
        "down": f'<path {s} d="M12 4v12M7 11l5 5 5-5M5 20h14"/>',
        "up": f'<path {s} d="M12 18V6M7 11l5-5 5 5M5 20h14"/>',
        "music": f'<path {s} d="M10 17V5l9-2v12"/><circle cx="7.5" cy="17.5" r="2.8" {f}/><circle cx="16.5" cy="15.5" r="2.8" {f}/>',
        "picture": f'<path {f} d="M3 19l6-8 4 5 3-3 5 6z"/><circle cx="16.5" cy="7" r="2.6" {f}/>',
        "play": f'<path {f} d="M8 5.5v13a1 1 0 0 0 1.5.86l10.4-6.5a1 1 0 0 0 0-1.72L9.5 4.64A1 1 0 0 0 8 5.5z"/>',
        "monitor": f'<rect x="3" y="4" width="18" height="12" rx="2" {s}/><path {s} d="M9 20h6M12 16v4"/>',
        "template": f'<rect x="4" y="4" width="16" height="16" rx="2" {s}/><path {s} d="M4 10h16M10 10v10"/>',
        "people": f'<circle cx="9" cy="8" r="3.2" {f}/><path {f} d="M3 19a6 6 0 0 1 12 0z"/><circle cx="16.5" cy="9" r="2.6" {f} opacity=".85"/><path {f} opacity=".85" d="M14.5 19a5 5 0 0 1 7-4.6V19z"/>',
        "home": f'<path {f} d="M12 3.5l9 7.5h-2.5v9h-5v-6h-3v6h-5v-9H3z"/>',
        "cloud": f'<path {f} d="M7 19a4.5 4.5 0 0 1-.6-8.96A6 6 0 0 1 17.8 8.6 4.5 4.5 0 0 1 17.5 19z"/>',
        "code": f'<path {s} d="M8.5 7L3.5 12l5 5M15.5 7l5 5-5 5M13.5 5l-3 14"/>',
        "game": f'<path {f} fill-rule="evenodd" d="M7.5 7.5h9c2.9 0 4.9 2 5.4 4.9l.9 5.3a2.4 2.4 0 0 1-4.1 2.1L16 17H8l-2.7 2.8a2.4 2.4 0 0 1-4.1-2.1l.9-5.3C2.6 9.5 4.6 7.5 7.5 7.5zM6.6 10.2v1.7H4.9v1.6h1.7v1.7h1.6v-1.7h1.7v-1.6H8.2v-1.7zM16.5 10.3a1.2 1.2 0 1 0 0 2.4 1.2 1.2 0 0 0 0-2.4zM18.6 12.7a1.2 1.2 0 1 0 0 2.4 1.2 1.2 0 0 0 0-2.4z"/>',
        "star": f'<path {f} d="M12 3l2.7 5.6 6.1.8-4.5 4.2 1.1 6.1L12 16.8l-5.4 2.9 1.1-6.1-4.5-4.2 6.1-.8z"/>',
        "lock": f'<rect x="5" y="10.5" width="14" height="10" rx="2" {f}/><path {s} d="M8.5 10.5V8a3.5 3.5 0 0 1 7 0v2.5"/>',
        "clock": f'<circle cx="12" cy="12" r="8.5" {s}/><path {s} d="M12 7.5V12l3 2"/>',
        "globe": f'<circle cx="12" cy="12" r="8.5" {s}/><path {s} d="M3.5 12h17M12 3.5c-3 3.2-3 13.8 0 17M12 3.5c3 3.2 3 13.8 0 17"/>',
        "heart": f'<path {f} d="M12 20s-8-5-8-10.5A4.3 4.3 0 0 1 12 7a4.3 4.3 0 0 1 8 2.5C20 15 12 20 12 20z"/>',
        "warn": f'<path {s} d="M12 6v8"/><circle cx="12" cy="18" r="1.5" {f}/>',
        "book": f'<path {s} d="M4 5.5A2 2 0 0 1 6 4h6v15H6a2 2 0 0 0-2 1.5zM20 5.5A2 2 0 0 0 18 4h-6v15h6a2 2 0 0 1 2 1.5z"/>',
        "terminal": f'<path {s} d="M5 7l5 5-5 5M12.5 17H19"/>',
        "gear": "",
        "search": f'<circle cx="10.5" cy="10.5" r="6" {s}/><path {s} d="M15 15l5 5"/>',
        "check": f'<path {s} d="M5 12.5l4.5 4.5L19 7.5"/>',
        "x": f'<path {s} d="M7 7l10 10M17 7L7 17"/>',
        "question": f'<path {s} d="M9 9a3 3 0 1 1 4.2 2.75c-.75.33-1.2 1.07-1.2 1.9V14"/><circle cx="12" cy="18" r="1.5" {f}/>',
        "info": f'<path {s} d="M12 11v7"/><circle cx="12" cy="7" r="1.6" {f}/>',
        "share": f'<circle cx="6" cy="12" r="2.6" {f}/><circle cx="17.5" cy="6" r="2.6" {f}/><circle cx="17.5" cy="18" r="2.6" {f}/><path {s} d="M8.3 10.8l7-3.6M8.3 13.2l7 3.6"/>',
        "server": f'<rect x="4" y="4" width="16" height="7" rx="1.6" {s}/><rect x="4" y="13" width="16" height="7" rx="1.6" {s}/><circle cx="8" cy="7.5" r="1.2" {f}/><circle cx="8" cy="16.5" r="1.2" {f}/>',
        "box": f'<path {s} d="M4 8l8-4 8 4v8l-8 4-8-4zM4 8l8 4 8-4M12 12v8"/>',
        "trash": f'<path {s} d="M5 7h14M10 4h4M7 7l1 13h8l1-13"/>',
    }[name]
    return g


# --------------------------------------------------------------------------------
# Folder family
# --------------------------------------------------------------------------------
FOLDER = dict(back1="#F2B53A", back2="#E09A12", front1="#FFE07A", front2="#FFC33D", edge="#FFF2C4")
BADGES = {  # badge color pairs (top, bottom)
    "blue": ("#4FA8F8", "#1A73D9"), "green": ("#45C46C", "#1E9447"), "red": ("#F2645A", "#D23A2F"),
    "purple": ("#A77BF5", "#7445D6"), "teal": ("#3CC9C1", "#14968F"), "orange": ("#FFA24A", "#EA7317"),
    "pink": ("#F76FA8", "#D63F7F"), "gray": ("#8E9AAA", "#5E6B7C"), "indigo": ("#6D84F5", "#3E52CF"),
}


def folder(badge=None, glyph_name=None, open_=False):
    ic = Icon()
    # shadow
    ic.rect(5, 15, 54, 42, 5, "#000000", op=.10)
    # back plate with tab
    back = ic.grad(FOLDER["back1"], FOLDER["back2"])
    ic.path("M9 10h13.2a4 4 0 0 1 2.9 1.25L28.4 15H55a4 4 0 0 1 4 4v31a4 4 0 0 1-4 4H9a4 4 0 0 1-4-4V14a4 4 0 0 1 4-4z",
            fill=back)
    # sheet of paper peeking out
    ic.rect(9, 18, 46, 20, 2.5, "#FFFFFF", op=.96)
    ic.rect(9, 18, 46, 20, 2.5, ic.grad("#FFFFFF", "#E9EEF4"), op=.9)
    # front plate
    front = ic.grad(FOLDER["front1"], FOLDER["front2"])
    if open_:
        ic.path("M11 26h47.5a3 3 0 0 1 2.9 3.8l-5.6 21.3A4 4 0 0 1 51.9 54H9a4 4 0 0 1-4-4V30a4 4 0 0 1 4-4z", fill=front)
    else:
        ic.path("M9 24h46a4 4 0 0 1 4 4v22a4 4 0 0 1-4 4H9a4 4 0 0 1-4-4V28a4 4 0 0 1 4-4z", fill=front)
        ic.path("M9 24.6h46", stroke=FOLDER["edge"], sw=1.2, op=.9)
    if badge:
        c1, c2 = BADGES[badge]
        g = ic.grad(c1, c2)
        ic.rect(35.5, 33.5, 25, 25, 7, "#000000", op=.12)
        ic.rect(35, 32, 25, 25, 7, g)
        ic.rect(35, 32, 25, 25, 7, "none", stroke="#FFFFFF", sw=1, op=.25)
        ic.group(glyph(glyph_name), "translate(37.5,34.5) scale(0.83)")
    return ic.svg()


# --------------------------------------------------------------------------------
# File (mimetype) family
# --------------------------------------------------------------------------------
def page(ic, color=None):
    ic.path("M15 6h23l14 14v36a3 3 0 0 1-3 3H15a3 3 0 0 1-3-3V9a3 3 0 0 1 3-3z", fill="#000000", op=.10)
    body = ic.grad("#FFFFFF", "#EEF1F5")
    ic.path("M15 5h23l14 14v36a3 3 0 0 1-3 3H15a3 3 0 0 1-3-3V8a3 3 0 0 1 3-3z", fill=body,
            stroke="#C5CCD6", sw=1)
    ic.path("M38 5v11a3 3 0 0 0 3 3h11z", fill=ic.grad("#E3E8EF", "#C9D1DC"), stroke="#C5CCD6", sw=1)


def mime_label(label, color, content=None):
    ic = Icon()
    page(ic)
    c1, c2 = color
    if content:
        content(ic, c1, c2)
    g = ic.grad(c1, c2)
    ic.rect(7, 35, 36, 17, 4, g)
    size = 10.5 if len(label) <= 3 else 8.6
    ic.path(text_d(label, size, 25, 43.6), fill="#FFFFFF")
    return ic.svg()


def mime_glyph(draw):
    ic = Icon()
    page(ic)
    draw(ic)
    return ic.svg()


def c_lines(color):
    def f(ic, *a):
        for i, w in enumerate((24, 24, 18)):
            ic.rect(18, 22 + i * 5, w, 2.6, 1.3, color, op=.85)
    return f


def draw_text(ic):
    for i, w in enumerate((26, 26, 26, 20, 26, 14)):
        ic.rect(19, 23 + i * 5.3, w, 2.4, 1.2, "#7D8896", op=.8)


def draw_image(ic):
    ic.rect(17, 25, 30, 25, 3, ic.grad("#7CC8FF", "#3A8FE8"))
    ic.path("M17 46l9-11 6 7 4-4 11 10.5V47a3 3 0 0 1-3 3H20a3 3 0 0 1-3-3z", fill=ic.grad("#4CC97A", "#1E8E4E"))
    ic.circle(40, 31.5, 3.2, "#FFE45C")


def draw_audio(ic):
    ic.circle(32, 38, 13, ic.grad("#FF7A93", "#E0386A"))
    ic.group(glyph("music"), "translate(22.5,28.5) scale(0.8)")


def draw_video(ic):
    ic.rect(17, 27, 30, 22, 4, ic.grad("#B48CFF", "#7B4CE0"))
    ic.group(glyph("play"), "translate(23.5,29.5) scale(0.72)")


def draw_archive(ic):
    ic.rect(28, 5.5, 8, 50, 0, ic.grad("#FFC761", "#F2A43A"))
    for i in range(7):
        ic.rect(28 + (i % 2) * 4, 8 + i * 4, 4, 4, 0, "#B36F12", op=.75)
    ic.rect(26.5, 37, 11, 12, 2.5, ic.grad("#FFD27A", "#E9952A"), stroke="#B36F12", sw=1)
    ic.rect(29.5, 41, 5, 4, 1, "#8C540A", op=.8)


def draw_code(ic):
    ic.group(glyph("code", "#2F7FE0", 2.6), "translate(17,24) scale(1.25)")


def draw_script(ic):
    ic.rect(17, 25, 30, 24, 4, ic.grad("#3A3F47", "#23272D"))
    ic.group(glyph("terminal", "#6BE38F", 2.6), "translate(20,26) scale(0.95)")


def draw_sheet(ic):
    ic.rect(17, 23, 30, 27, 2.5, "#FFFFFF", stroke="#2E9E58", sw=1.4)
    ic.rect(17, 23, 30, 6, 2.5, ic.grad("#4CC97A", "#21934F"))
    for x in (27, 37):
        ic.path(f"M{x} 29v21", stroke="#2E9E58", sw=1.2)
    for y in (35.5, 42.5):
        ic.path(f"M17 {y}h30", stroke="#2E9E58", sw=1.2)


def draw_pres(ic):
    ic.rect(17, 24, 30, 22, 2.5, ic.grad("#FFA65A", "#EA6E1F"))
    for i, h in enumerate((7, 12, 9, 15)):
        ic.rect(21 + i * 6, 42 - h, 4, h, 1, "#FFFFFF", op=.95)


def draw_writer(ic):
    ic.rect(17, 23, 30, 6, 2, ic.grad("#4FA8F8", "#1A73D9"))
    for i, w in enumerate((30, 30, 22, 30, 16)):
        ic.rect(17, 33 + i * 4.6, w, 2.4, 1.2, "#1A73D9", op=.7)


def draw_font(ic):
    ic.path(text_d("Aa", 17, 32, 38), fill="#3E4A5A")


def draw_unknown(ic):
    ic.circle(32, 37, 12, ic.grad("#A8B2C0", "#7B8696"))
    ic.group(glyph("question", "#FFFFFF", 2.6), "translate(22,27) scale(0.83)")


def draw_exec(ic):
    gear(ic, 32, 38, 13, ic.grad("#9AA6B6", "#5E6B7C"))


def draw_disc(ic):
    ic.circle(32, 37, 14, ic.grad("#E9EDF2", "#B6C0CC"), stroke="#98A3B1", sw=1)
    ic.circle(32, 37, 14, ic.rgrad("#B7E3FF", "#D9C4FF", .3, .3, .9), op=.55)
    ic.circle(32, 37, 4, "#FFFFFF", stroke="#98A3B1", sw=1)


def draw_package(ic):
    ic.path("M32 24l13 6v15l-13 6-13-6V30z", fill=ic.grad("#E8B66A", "#C98A35"))
    ic.path("M19 30l13 6 13-6M32 36v15", stroke="#9E6A24", sw=1.4)
    ic.path("M25.5 27l13 6", stroke="#FFF3DA", sw=2.2)


def draw_desktopfile(ic):
    ic.rect(18, 26, 28, 22, 6, ic.grad("#4FA8F8", "#1A73D9"))
    ic.group(glyph("star"), "translate(22,27) scale(0.85)")


def draw_html(ic):
    ic.circle(32, 37, 12.5, ic.grad("#3CC9C1", "#14968F"))
    ic.group(glyph("globe"), "translate(21.5,26.5) scale(0.88)")


def draw_json(ic):
    ic.path(text_d("{ }", 15, 32, 37), fill="#D08A12")


def draw_markdown(ic):
    ic.rect(16, 28, 32, 19, 3, "none", stroke="#3E4A5A", sw=2)
    ic.path("M20.5 42v-9l3.8 4.5 3.8-4.5v9M36.5 33v8.5M33 38.5l3.5 3.5 3.5-3.5", stroke="#3E4A5A", sw=2)


def draw_db(ic):
    g = ic.grad("#7C8CF8", "#4A5BD8")
    ic.path("M20 28v16c0 2.8 5.4 5 12 5s12-2.2 12-5V28", fill=g)
    ic.add('<ellipse cx="32" cy="28" rx="12" ry="5" fill="#A7B3FF"/>')
    ic.path("M20 36c0 2.8 5.4 5 12 5s12-2.2 12-5", stroke="#FFFFFF", sw=1.3, op=.6)


def draw_calendar(ic):
    ic.rect(18, 25, 28, 24, 3, "#FFFFFF", stroke="#C5CCD6", sw=1)
    ic.rect(18, 25, 28, 7, 3, ic.grad("#F2645A", "#D23A2F"))
    for r in range(3):
        for c in range(4):
            ic.rect(21 + c * 6, 35 + r * 4.6, 3.6, 2.8, .8, "#8E9AAA", op=.8)


def draw_contact(ic):
    ic.circle(32, 33, 5.5, "#5E6B7C")
    ic.path("M21 49a11 11 0 0 1 22 0z", fill="#5E6B7C")


# --------------------------------------------------------------------------------
# Shapes for apps/devices
# --------------------------------------------------------------------------------
def gear(ic, cx, cy, r, fill, teeth=8, hole=True):
    pts = []
    for i in range(teeth * 4):
        a = 2 * math.pi * i / (teeth * 4) - math.pi / 2
        rr = r if (i % 4) in (0, 1) else r * 0.78
        pts.append((cx + rr * math.cos(a), cy + rr * math.sin(a)))
    d = "M" + " L".join(f"{x:.2f},{y:.2f}" for x, y in pts) + "Z"
    if hole:
        hr = r * 0.36
        d += f"M{cx + hr},{cy}A{hr},{hr} 0 1 0 {cx - hr},{cy}A{hr},{hr} 0 1 0 {cx + hr},{cy}Z"
    ic.path(d, fill=fill, rule="evenodd", stroke=fill, sw=1.2)


def tile(ic, c1, c2, x=8, y=8, s=48, r=12):
    ic.rect(x, y + 1.5, s, s, r, "#000000", op=.12)
    ic.rect(x, y, s, s, r, ic.grad(c1, c2, 0, 0, 1, 1))
    ic.rect(x + .5, y + .5, s - 1, s - 1, r - .5, "none", stroke="#FFFFFF", sw=1, op=.22)


def monitor(ic, screen=("#5DB7FF", "#1F6FD1")):
    ic.rect(6, 10, 52, 35, 4, ic.grad("#4A5361", "#2B3139"))
    ic.rect(9, 13, 46, 29, 2, ic.grad(*screen, 0, 0, 1, 1))
    ic.path("M9 34c10-6 20 6 46-4v10a2 2 0 0 1-2 2H11a2 2 0 0 1-2-2z", fill="#FFFFFF", op=.18)
    ic.path("M27 45l-2 8h14l-2-8z", fill=ic.grad("#C3CAD3", "#9AA4B1"))
    ic.rect(20, 52, 24, 4, 2, ic.grad("#C3CAD3", "#8E99A7"))


# --------------------------------------------------------------------------------
# Icon definitions
# --------------------------------------------------------------------------------
def start_here():
    ic = Icon()
    g = ic.grad("#6CCBFF", "#0A6CD6", 0, 0, 1, 1)
    r, gap = 12.2, 2.2
    o = r + gap / 1.41
    for dx, dy in ((0, -o), (o, 0), (0, o), (-o, 0)):
        cx, cy = 32 + dx, 32 + dy
        ic.path(f"M{cx},{cy - r}L{cx + r},{cy}L{cx},{cy + r}L{cx - r},{cy}Z", fill=g, stroke=g, sw=.9)
    return ic.svg()


def start_here_symbolic():
    r, gap = 3.0, .55
    o = r + gap / 1.41
    d = "".join(f"M{8 + dx},{8 + dy - r}L{8 + dx + r},{8 + dy}L{8 + dx},{8 + dy + r}L{8 + dx - r},{8 + dy}Z"
                for dx, dy in ((0, -o), (o, 0), (0, o), (-o, 0)))
    return ('<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 16 16">'
            '<style id="current-color-scheme">.ColorScheme-Text{color:#232629;}</style>'
            f'<path class="ColorScheme-Text" fill="currentColor" d="{d}"/></svg>\n')


# --- session / power actions (monochrome line glyphs that follow the color scheme) ---
def _arc(cx, cy, r, a0, a1):
    """SVG arc path from angle a0 to a1 (degrees, 0 = up, clockwise)."""
    p = lambda a: (cx + r * math.sin(math.radians(a)), cy - r * math.cos(math.radians(a)))
    (x0, y0), (x1, y1) = p(a0), p(a1)
    large = 1 if (a1 - a0) % 360 > 180 else 0
    return f"M{x0:.2f},{y0:.2f}A{r},{r} 0 {large} 1 {x1:.2f},{y1:.2f}"


def session_icon(kind, color):
    """24x24 line glyph; color is the default for the ColorScheme-Text class (recolored by KDE)."""
    s, f = [], []          # stroked paths, filled paths
    if kind == "shutdown":           # power symbol
        s += [_arc(12, 12.8, 7.6, 40, 320), "M12,3.2V11.6"]
    elif kind == "reboot":           # circular arrow
        s += [_arc(12, 12.5, 7.4, 60, 360 + 10)]
        f += ["M13.2,1.9L18.6,4.9L13.4,8.6Z"]
    elif kind == "suspend":          # crescent moon
        s += ["M15.6,3.8A8.3,8.3 0 1 0 20.4,15.8A6.9,6.9 0 0 1 15.6,3.8Z"]
    elif kind == "hibernate":        # moon over a resting line
        s += ["M14.6,3.4A7,7 0 1 0 19.2,13.8A5.8,5.8 0 0 1 14.6,3.4Z", "M3.5,20.5H20.5"]
    elif kind == "log-out":          # door frame with an arrow leaving it
        s += ["M10.5,3.5H5.8A1.8,1.8 0 0 0 4,5.3V18.7A1.8,1.8 0 0 0 5.8,20.5H10.5",
              "M10,12H20.5", "M16.5,7.8L20.7,12L16.5,16.2"]
    elif kind == "lock-screen":      # padlock
        s += ["M7.5,10.5V7.5A4.5,4.5 0 0 1 16.5,7.5V10.5",
              "M6.3,10.5H17.7A1.8,1.8 0 0 1 19.5,12.3V19A1.8,1.8 0 0 1 17.7,20.8H6.3A1.8,1.8 0 0 1 4.5,19V12.3"
              "A1.8,1.8 0 0 1 6.3,10.5Z", "M12,14.6V16.6"]
    elif kind == "switch-user":      # two people
        s += ["M9.3,4.2A3.4,3.4 0 1 1 9.29,4.2Z", "M3,19.5C3,15.8 5.8,13.6 9.3,13.6S15.6,15.8 15.6,19.5",
              "M15.4,4.6A3,3 0 0 1 15.4,10.4", "M17.6,13.9C19.6,14.6 21,16.6 21,19.5"]
    elif kind == "save-session":     # bookmark ribbon with a check
        s += ["M6.5,3.5H17.5V20.5L12,16.6L6.5,20.5Z", "M9.2,9.6L11.2,11.6L14.9,7.9"]
    body = "".join(f'<path class="ColorScheme-Text" d="{d}" fill="none" stroke="currentColor" stroke-width="1.6" '
                   f'stroke-linecap="round" stroke-linejoin="round"/>' for d in s)
    body += "".join(f'<path class="ColorScheme-Text" d="{d}" fill="currentColor"/>' for d in f)
    return ('<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24">'
            f'<style id="current-color-scheme">.ColorScheme-Text{{color:{color};}}</style>{body}</svg>\n')


SESSION_ICONS = {  # kind: names (each also gets a "-symbolic" twin)
    "shutdown": ["system-shutdown", "system-shutdown-update"],
    "reboot": ["system-reboot", "system-reboot-update"],
    "suspend": ["system-suspend", "system-suspend-hibernate"],
    "hibernate": ["system-hibernate"],
    "log-out": ["system-log-out", "system-log-out-rtl"],
    "lock-screen": ["system-lock-screen"],
    "switch-user": ["system-switch-user"],
    "save-session": ["system-save-session"],
}


def user_home():
    ic = Icon()
    ic.path("M32 9L6 30h7v24h38V30h7z", fill="#000000", op=.1)
    ic.path("M13 29v23a2 2 0 0 0 2 2h34a2 2 0 0 0 2-2V29L32 13z", fill=ic.grad("#FFFFFF", "#E3E9F0"),
            stroke="#C5CCD6", sw=1)
    ic.path("M32 7.5a3 3 0 0 1 1.9.7l24 20a2.5 2.5 0 0 1-3.2 3.8L32 13 9.3 32a2.5 2.5 0 0 1-3.2-3.8l24-20a3 3 0 0 1 1.9-.7z",
            fill=ic.grad("#4FA8F8", "#1A73D9"))
    ic.rect(27, 38, 10, 16, 2, ic.grad("#FFC33D", "#E09A12"))
    return ic.svg()


def recycle_symbol(cx, cy, r, fill):
    """Universal recycling symbol (public domain): three chasing arrows
    along the sides of a triangle, drawn here with original geometry."""
    parts = []
    for k in range(3):
        a0 = math.radians(-90 + 120 * k)          # vertex k
        a1 = math.radians(-90 + 120 * (k + 1))    # vertex k+1
        p0 = (cx + r * math.cos(a0), cy + r * math.sin(a0))
        p1 = (cx + r * math.cos(a1), cy + r * math.sin(a1))
        # band along the side, from 18% to 72% of the way, with an arrowhead
        def lerp(t):
            return (p0[0] + (p1[0] - p0[0]) * t, p0[1] + (p1[1] - p0[1]) * t)
        dx, dy = p1[0] - p0[0], p1[1] - p0[1]
        ln = math.hypot(dx, dy)
        ux, uy = dx / ln, dy / ln            # along the side
        nx, ny = uy, -ux                      # outward normal
        w, hw, hl = r * 0.2, r * 0.38, r * 0.44
        s0, s1 = lerp(0.16), lerp(0.62)
        tip = lerp(0.62 + hl / ln)
        pts = [
            (s0[0] + nx * w, s0[1] + ny * w), (s1[0] + nx * w, s1[1] + ny * w),
            (s1[0] + nx * hw, s1[1] + ny * hw), tip,
            (s1[0] - nx * hw * .55, s1[1] - ny * hw * .55), (s1[0] - nx * w * .2, s1[1] - ny * w * .2),
            (s0[0] - nx * w * .2, s0[1] - ny * w * .2),
        ]
        parts.append("M" + " L".join(f"{x:.2f},{y:.2f}" for x, y in pts) + "Z")
    return f'<path fill="{fill}" stroke="{fill}" stroke-width="1" stroke-linejoin="round" d="{"".join(parts)}"/>'


def trash(full=False):
    """Translucent "glass" bin with the recycling symbol; papers show through when full."""
    ic = Icon()
    ic.add('<ellipse cx="32" cy="57.5" rx="16" ry="2.6" fill="#000000" opacity=".14"/>')
    body = "M14 14h36l-3.6 38.6A4 4 0 0 1 42.4 56H21.6a4 4 0 0 1-4-3.4z"
    if full:
        # light inner base so the glass does not turn gray on dark backgrounds
        ic.path(body, fill=ic.grad("#F3F8FD", "#D6E4F1"))
        # papers inside the bin (seen through the glass)
        ic.path("M19 20l9-6 7 5-3 30H22z", fill="#FFFFFF", stroke="#B9C6D3", sw=.8)
        ic.path("M30 17l12 2-2 31H31z", fill=ic.grad("#FFFFFF", "#E6ECF2"), stroke="#B9C6D3", sw=.8)
        ic.path("M22 30l18-3 1 18-17 2z", fill="#9CC8F2", op=.85)
        # crumpled sheets sticking out of the top
        ic.path("M17 15l4-9 7 4 5-6 6 5 6-3 2 9z", fill=ic.grad("#FFFFFF", "#DCE4EC"), stroke="#AFBCCA", sw=.9)
        ic.path("M24 9l5 3M36 7l3 4", stroke="#AFBCCA", sw=.9)
    # glass body
    ic.path(body, fill=ic.grad("#EAF4FF", "#BFD7EE"), op=(.62 if full else .9))
    ic.path(body, fill=ic.grad("#FFFFFF", "#FFFFFF", 0, 0, 1, 0), op=.0)
    # left highlight and right shade give the glass its volume
    ic.path("M17 16h6l-1.6 37.5h-2.2a2 2 0 0 1-2-1.8z", fill="#FFFFFF", op=.55)
    ic.path("M41 16h7l-3.4 37a2 2 0 0 1-2 1.8H40z", fill="#7FA3C6", op=.22)
    ic.path(body, stroke="#8FAAC4", sw=1.2)
    # rim
    ic.rect(11, 11, 42, 6, 3, ic.grad("#F7FBFF", "#C9DAEB"), stroke="#8FAAC4", sw=1.1)
    ic.path("M14 12.6h36", stroke="#FFFFFF", sw=1, op=.9)
    # recycling symbol
    ic.add(recycle_symbol(32, 36.5, 10.5, ic.grad("#3FA2F5", "#1460C8", 0, 0, 1, 1)))
    return ic.svg()


def desktop_place():
    ic = Icon()
    monitor(ic, ("#3CC9C1", "#1A73D9"))
    return ic.svg()


def network_place(kind="workgroup"):
    ic = Icon()
    ic.circle(32, 32, 24, ic.grad("#4FC3F7", "#1A73D9", 0, 0, 1, 1))
    ic.path("M8 32h48M32 8c-8 8-8 40 0 48M32 8c8 8 8 40 0 48M13 19h38M13 45h38", stroke="#FFFFFF", sw=2.4, op=.9)
    if kind == "server":
        ic.rect(34, 34, 24, 24, 6, ic.grad("#8E9AAA", "#5E6B7C"))
        ic.group(glyph("server"), "translate(36,36) scale(0.83)")
    return ic.svg()


def terminal_app():
    ic = Icon()
    ic.rect(6, 11, 52, 44, 7, "#000000", op=.14)
    ic.rect(6, 9, 52, 44, 7, ic.grad("#3A3F47", "#1E2227"))
    ic.path("M13 9h38a7 7 0 0 1 7 7v1H6v-1a7 7 0 0 1 7-7z", fill="#4C535D")
    for i, c in enumerate(("#FF6159", "#FFBD2E", "#28C941")):
        ic.circle(13 + i * 5.5, 13, 1.6, c, op=.0)
    ic.group(glyph("terminal", "#6BE38F", 2.4), "translate(12,19) scale(1.35)")
    ic.rect(6, 9, 52, 44, 7, "none", stroke="#FFFFFF", sw=1, op=.12)
    return ic.svg()


def settings_app():
    ic = Icon()
    ic.circle(32, 33.5, 24, "#000000", op=.10)
    gear(ic, 32, 32, 25, ic.grad("#A5B1C2", "#5E6B7C", 0, 0, 1, 1), teeth=9)
    ic.circle(32, 32, 9, ic.grad("#4FA8F8", "#1A73D9"))
    ic.circle(32, 32, 4, "#FFFFFF")
    return ic.svg()


def store_app():
    ic = Icon()
    ic.path("M14 22h36l-2.5 30a4 4 0 0 1-4 3.7H20.5a4 4 0 0 1-4-3.7z", fill="#000000", op=.1)
    ic.path("M14 20h36l-2.5 30a4 4 0 0 1-4 3.7H20.5a4 4 0 0 1-4-3.7z", fill=ic.grad("#4FA8F8", "#1A5FC9"))
    ic.path("M23 24v-6a9 9 0 0 1 18 0v6", stroke="#1A5FC9", sw=3.2)
    for i, c in enumerate(("#FF6B5E", "#45C46C", "#FFC33D", "#4FC3F7")):
        x, y = 26 + (i % 2) * 7, 31 + (i // 2) * 7
        ic.rect(x, y, 6, 6, 1.4, c)
    return ic.svg()


def editor_app():
    ic = Icon()
    page(ic)
    for i, w in enumerate((26, 26, 20, 26, 14)):
        ic.rect(18, 24 + i * 5.3, w, 2.4, 1.2, "#7D8896", op=.75)
    ic.path("M47 27l6 6-17 17-8 2 2-8z", fill=ic.grad("#4FA8F8", "#1A5FC9"))
    ic.path("M47 27l6 6", stroke="#0D3E8A", sw=2)
    ic.path("M30 44l-2 8 8-2z", fill="#FFD27A")
    return ic.svg()


def browser_app():
    ic = Icon()
    ic.circle(32, 33.5, 25, "#000000", op=.10)
    ic.circle(32, 32, 25, ic.grad("#4FD1F7", "#1F6FD1", 0, 0, 1, 1))
    ic.path("M7 32h50M32 7c-9 9-9 41 0 50M32 7c9 9 9 41 0 50M11 19h42M11 45h42", stroke="#FFFFFF", sw=2.4, op=.85)
    return ic.svg()


def sysmon_app():
    ic = Icon()
    tile(ic, "#2F3540", "#1C2027")
    ic.path("M13 42l9-8 6 5 9-14 6 8 8-6", stroke="#45E07C", sw=3.2)
    ic.path("M13 42l9-8 6 5 9-14 6 8 8-6V50H13z", fill="#45E07C", op=.18)
    return ic.svg()


def calc_app():
    ic = Icon()
    tile(ic, "#3A3F47", "#1E2227", x=12, y=6, s=40, r=8)
    ic.rect(12, 6, 40, 52, 8, ic.grad("#3A3F47", "#1E2227"))
    ic.rect(17, 11, 30, 10, 3, "#7FC6A8", op=.9)
    for r in range(3):
        for c in range(3):
            col = "#FF9A3D" if (c == 2 and r == 2) else "#5A626E"
            ic.rect(17 + c * 10.5, 26 + r * 10, 8, 7.5, 2, col)
    return ic.svg()


def archive_app():
    ic = Icon()
    ic.path("M32 6l24 11v30L32 58 8 47V17z", fill="#000000", op=.1)
    ic.path("M32 5l24 11v30L32 57 8 46V16z", fill=ic.grad("#F0C47A", "#C98A35"))
    ic.path("M8 16l24 11 24-11", fill=ic.grad("#F7D9A3", "#E3AE5C"))
    ic.path("M8 16l24 11v30L8 46z", fill="#000000", op=.08)
    ic.path("M20 10.5l24 11v9", stroke="#FFF3DA", sw=4.5, cap="butt")
    return ic.svg()


def viewer_image_app():
    ic = Icon()
    ic.rect(7, 12, 50, 40, 6, "#000000", op=.1)
    ic.rect(7, 10, 50, 40, 6, ic.grad("#7CC8FF", "#2E86E6"))
    ic.path("M7 42l14-14 10 10 7-7 19 17v2a6 6 0 0 1-6 6H13a6 6 0 0 1-6-6z", fill=ic.grad("#5AD38A", "#1E8E4E"))
    ic.circle(43, 22, 5, "#FFE45C")
    return ic.svg()


def viewer_doc_app():
    ic = Icon()
    page(ic)
    for i, w in enumerate((26, 26, 20)):
        ic.rect(18, 24 + i * 5.3, w, 2.4, 1.2, "#7D8896", op=.75)
    ic.circle(38, 42, 9, ic.grad("#FFFFFF", "#DDEBFB"), stroke="#1A73D9", sw=3.4)
    ic.path("M44.5 48.5l8 8", stroke="#1A73D9", sw=4.2)
    return ic.svg()


def screenshot_app():
    ic = Icon()
    tile(ic, "#4FA8F8", "#1A5FC9")
    ic.path("M18 26v-8h8M38 18h8v8M46 38v8h-8M26 46h-8v-8", stroke="#FFFFFF", sw=3.2)
    ic.circle(32, 32, 5.5, "#FFFFFF")
    return ic.svg()


def round_glyph_app(c, gname, sc=1.25):
    ic = Icon()
    ic.circle(32, 33.5, 24, "#000000", op=.10)
    ic.circle(32, 32, 24, ic.grad(*BADGES[c], 0, 0, 1, 1))
    off = 32 - 12 * sc
    ic.group(glyph(gname, "#FFFFFF", 2.4), f"translate({off},{off}) scale({sc})")
    return ic.svg()


def tile_glyph_app(c, gname, sc=1.25):
    ic = Icon()
    tile(ic, *BADGES[c])
    off = 32 - 12 * sc
    ic.group(glyph(gname, "#FFFFFF", 2.4), f"translate({off},{off}) scale({sc})")
    return ic.svg()


def player_video_app():
    ic = Icon()
    tile(ic, *BADGES["purple"])
    for y in (12, 46):
        for i in range(6):
            ic.rect(12 + i * 7.3, y, 4, 4, 1, "#FFFFFF", op=.45)
    ic.group(glyph("play"), "translate(19.5,19.5) scale(1.05)")
    return ic.svg()


def kdeconnect_app():
    ic = Icon()
    ic.rect(8, 14, 40, 28, 3, ic.grad("#4A5361", "#2B3139"))
    ic.rect(11, 17, 34, 22, 1.5, ic.grad("#5DB7FF", "#1F6FD1", 0, 0, 1, 1))
    ic.path("M4 44h48l-2 4H6z", fill=ic.grad("#C3CAD3", "#9AA4B1"))
    ic.rect(40, 24, 18, 32, 4, ic.grad("#3A3F47", "#1E2227"))
    ic.rect(42, 27, 14, 25, 2, ic.grad("#7CC8FF", "#2E86E6"))
    return ic.svg()


def disk_app():
    ic = Icon()
    ic.circle(32, 33.5, 24, "#000000", op=.10)
    ic.circle(32, 32, 24, ic.grad("#A5B1C2", "#6B7788"))
    ic.path("M32 32V8a24 24 0 0 1 22.8 16.6z", fill=ic.grad("#4FA8F8", "#1A73D9"))
    ic.path("M32 32l22.8-7.4A24 24 0 0 1 46 51.4z", fill=ic.grad("#45C46C", "#1E9447"))
    ic.circle(32, 32, 7, "#FFFFFF")
    return ic.svg()


def wallet_app():
    ic = Icon()
    ic.rect(6, 16, 52, 38, 7, "#000000", op=.1)
    ic.rect(6, 14, 52, 38, 7, ic.grad("#A77BF5", "#6A3DCB"))
    ic.path("M10 14l30-8a4 4 0 0 1 5 3.2L46 14z", fill="#C9AFFF")
    ic.rect(38, 26, 20, 14, 5, ic.grad("#C9AFFF", "#9C72EE"))
    ic.circle(46, 33, 3, "#FFFFFF")
    return ic.svg()


def file_manager_app():
    # folder with a blue window bar — the "Files" app
    ic = Icon()
    ic.rect(5, 15, 54, 42, 5, "#000000", op=.10)
    ic.path("M9 10h13.2a4 4 0 0 1 2.9 1.25L28.4 15H55a4 4 0 0 1 4 4v31a4 4 0 0 1-4 4H9a4 4 0 0 1-4-4V14a4 4 0 0 1 4-4z",
            fill=ic.grad(FOLDER["back1"], FOLDER["back2"]))
    ic.rect(9, 18, 46, 20, 2.5, "#FFFFFF")
    ic.path("M9 24h46a4 4 0 0 1 4 4v22a4 4 0 0 1-4 4H9a4 4 0 0 1-4-4V28a4 4 0 0 1 4-4z",
            fill=ic.grad(FOLDER["front1"], FOLDER["front2"]))
    ic.path("M5 44h54v6a4 4 0 0 1-4 4H9a4 4 0 0 1-4-4z", fill=ic.grad("#4FA8F8", "#1A73D9"))
    return ic.svg()


def help_app():
    return round_glyph_app("blue", "question")


def info_app():
    return round_glyph_app("indigo", "info")


# --- categories (Kickoff sidebar) ----------------------------------------------------
def category(c, gname, sc=1.2):
    return tile_glyph_app(c, gname, sc)


# --- devices -----------------------------------------------------------------------------
def computer():
    ic = Icon()
    monitor(ic)
    return ic.svg()


def laptop():
    ic = Icon()
    ic.rect(10, 12, 44, 30, 3, ic.grad("#4A5361", "#2B3139"))
    ic.rect(13, 15, 38, 24, 1.5, ic.grad("#5DB7FF", "#1F6FD1", 0, 0, 1, 1))
    ic.path("M4 44h56l-3 6a3 3 0 0 1-2.7 1.7H9.7A3 3 0 0 1 7 50z", fill=ic.grad("#D3D9E0", "#9AA4B1"))
    ic.rect(26, 44, 12, 2, 1, "#7D8896")
    return ic.svg()


def harddisk(ssd=False):
    ic = Icon()
    ic.rect(6, 20, 52, 28, 5, "#000000", op=.1)
    ic.rect(6, 18, 52, 28, 5, ic.grad("#E1E6EC", "#A9B4C1"))
    ic.rect(6, 18, 52, 28, 5, "none", stroke="#8E99A7", sw=1)
    if ssd:
        for i in range(4):
            ic.rect(12 + i * 9, 24, 7, 10, 1.5, "#3E4A5A", op=.85)
    else:
        ic.rect(11, 36, 30, 3, 1.5, "#8E99A7")
    ic.circle(50, 38, 2.4, "#45E07C")
    return ic.svg()


def usb_stick():
    ic = Icon()
    ic.rect(24, 6, 16, 14, 2, ic.grad("#D3D9E0", "#9AA4B1"))
    ic.rect(27.5, 10, 3, 3, .6, "#5E6B7C")
    ic.rect(33.5, 10, 3, 3, .6, "#5E6B7C")
    ic.rect(18, 19, 28, 40, 6, ic.grad("#4FA8F8", "#1A5FC9"))
    ic.rect(25, 40, 14, 3, 1.5, "#FFFFFF", op=.7)
    return ic.svg()


def optical():
    ic = Icon()
    draw = Icon()
    ic.circle(32, 33.5, 25, "#000000", op=.10)
    ic.circle(32, 32, 25, ic.grad("#EEF2F6", "#B6C0CC"), stroke="#98A3B1", sw=1)
    ic.circle(32, 32, 25, ic.rgrad("#B7E3FF", "#E3C4FF", .3, .3, 1), op=.55)
    ic.circle(32, 32, 7, "#FFFFFF", stroke="#98A3B1", sw=1)
    ic.circle(32, 32, 2.5, "#98A3B1")
    return ic.svg()


def phone():
    ic = Icon()
    ic.rect(17, 5, 30, 54, 7, ic.grad("#3A3F47", "#1E2227"))
    ic.rect(20, 10, 24, 42, 3, ic.grad("#7CC8FF", "#2E86E6", 0, 0, 1, 1))
    ic.rect(28, 54.5, 8, 1.6, .8, "#8E99A7")
    return ic.svg()


def keyboard():
    ic = Icon()
    ic.rect(4, 19, 56, 28, 5, "#000000", op=.1)
    ic.rect(4, 17, 56, 28, 5, ic.grad("#E1E6EC", "#B3BDC9"), stroke="#8E99A7", sw=1)
    for r in range(3):
        for c in range(10 - (r == 2) * 0):
            ic.rect(8.5 + c * 4.8 + (r % 2) * 1.5, 21.5 + r * 5.6, 3.6, 3.8, .8, "#5E6B7C", op=.85)
    ic.rect(18, 38.5, 28, 3.6, .8, "#5E6B7C", op=.85)
    return ic.svg()


def mouse():
    ic = Icon()
    ic.rect(17, 7, 30, 50, 15, ic.grad("#E1E6EC", "#AAB4C1"), stroke="#8E99A7", sw=1)
    ic.path("M32 7v18M17 25h30", stroke="#8E99A7", sw=1.2)
    ic.rect(30, 12, 4, 8, 2, "#1A73D9")
    return ic.svg()


def printer():
    ic = Icon()
    ic.rect(17, 6, 30, 16, 2, "#FFFFFF", stroke="#C5CCD6", sw=1)
    ic.rect(6, 20, 52, 26, 6, ic.grad("#5A6472", "#363D47"))
    ic.rect(15, 38, 34, 20, 2, "#FFFFFF", stroke="#C5CCD6", sw=1)
    for i in range(3):
        ic.rect(19, 43 + i * 4.5, 26 - i * 6, 2, 1, "#8E9AAA")
    ic.circle(50, 27, 2, "#45E07C")
    return ic.svg()


def camera():
    ic = Icon()
    ic.path("M23 14h18l3 6H20z", fill="#5A6472")
    ic.rect(5, 18, 54, 36, 7, ic.grad("#5A6472", "#2B3139"))
    ic.circle(32, 36, 12, "#1E2227", stroke="#A5B1C2", sw=2)
    ic.circle(32, 36, 7.5, ic.rgrad("#7CC8FF", "#1A3F7A", .35, .35, .8))
    ic.circle(50, 25, 2, "#FFC33D")
    return ic.svg()


def headphones():
    ic = Icon()
    ic.path("M12 38v-6a20 20 0 0 1 40 0v6", stroke=ic.grad("#5A6472", "#2B3139"), sw=5)
    ic.rect(8, 34, 13, 22, 5, ic.grad("#4FA8F8", "#1A5FC9"))
    ic.rect(43, 34, 13, 22, 5, ic.grad("#4FA8F8", "#1A5FC9"))
    return ic.svg()


def speakers():
    ic = Icon()
    ic.rect(15, 5, 34, 54, 6, ic.grad("#5A6472", "#2B3139"))
    ic.circle(32, 18, 6, "#1E2227", stroke="#A5B1C2", sw=1.5)
    ic.circle(32, 40, 11, "#1E2227", stroke="#A5B1C2", sw=1.5)
    ic.circle(32, 40, 4, "#4FA8F8")
    return ic.svg()


def gamepad():
    ic = Icon()
    ic.group(glyph("game", "#7D8896"), "translate(6,5) scale(2.17)")
    return ic.svg()


def ethernet():
    ic = Icon()
    ic.rect(14, 10, 36, 32, 5, ic.grad("#A5B1C2", "#6B7788"))
    ic.rect(20, 18, 24, 16, 2, "#2B3139")
    for i in range(5):
        ic.rect(22.5 + i * 4, 18, 2, 6, .5, "#FFC33D")
    ic.rect(28, 42, 8, 16, 2, "#5E6B7C")
    return ic.svg()


def scanner():
    ic = Icon()
    ic.rect(4, 26, 56, 22, 5, ic.grad("#E1E6EC", "#A9B4C1"), stroke="#8E99A7", sw=1)
    ic.path("M6 26l4-10h44l4 10z", fill=ic.grad("#5A6472", "#363D47"))
    ic.rect(10, 36, 44, 3, 1.5, "#4FA8F8")
    return ic.svg()


def battery_dev():
    ic = Icon()
    ic.rect(4, 18, 52, 28, 6, "none", stroke="#5E6B7C", sw=3)
    ic.rect(56, 26, 5, 12, 2, "#5E6B7C")
    ic.rect(9, 23, 34, 18, 3, ic.grad("#5AD38A", "#1E8E4E"))
    return ic.svg()


# --- status / dialogs ------------------------------------------------------------
def dialog(kind):
    if kind == "warning":
        ic = Icon()
        ic.path("M32 7a5 5 0 0 1 4.3 2.5l21 37A5 5 0 0 1 53 54H11a5 5 0 0 1-4.3-7.5l21-37A5 5 0 0 1 32 7z",
                fill=ic.grad("#FFD25E", "#F2A60C"))
        ic.group(glyph("warn", "#3B2A00", 3), "translate(20,18) scale(1.0)")
        return ic.svg()
    c, g = {"information": ("blue", "info"), "error": ("red", "x"), "question": ("blue", "question"),
            "ok": ("green", "check")}[kind]
    return round_glyph_app(c, g, 1.3)


def shield(c, gname):
    ic = Icon()
    d = "M32 5l22 8v16c0 14-9.5 24-22 30C19.5 53 10 43 10 29V13z"
    ic.path(d, fill="#000000", op=.1)
    ic.path(d, fill=ic.grad(*BADGES[c], 0, 0, 1, 1))
    ic.group(glyph(gname, "#FFFFFF", 2.6), "translate(19,17) scale(1.08)")
    return ic.svg()


# --------------------------------------------------------------------------------
# Name map: context -> {file name: svg} + aliases
# --------------------------------------------------------------------------------
def build():
    icons = {"places": {}, "mimetypes": {}, "devices": {}, "apps": {}, "categories": {}, "status": {}}
    aliases = {}

    def put(ctx, name, svg, *alias):
        icons[ctx][name] = svg
        for a in alias:
            aliases[(ctx, a)] = name

    P = "places"
    put(P, "folder", folder(), "inode-directory", "folder-blue", "folder-yellow", "gtk-directory",
        "folder-orange", "folder_open", "folder-new")
    put(P, "folder-open", folder(open_=True), "folder-drag-accept", "folder-visiting")
    put(P, "folder-documents", folder("blue", "doc"), "folder-text", "folder-txt")
    put(P, "folder-download", folder("teal", "down"), "folder-downloads")
    put(P, "folder-music", folder("pink", "music"), "folder-sound", "folder-audio")
    put(P, "folder-pictures", folder("green", "picture"), "folder-images", "folder-image", "folder-photos")
    put(P, "folder-videos", folder("purple", "play"), "folder-video", "folder-movies")
    put(P, "folder-templates", folder("gray", "template"))
    put(P, "folder-publicshare", folder("orange", "people"), "folder-public")
    put(P, "folder-desktop", folder("indigo", "monitor"))
    put(P, "folder-cloud", folder("blue", "cloud"), "folder-onedrive", "folder-gdrive", "folder-dropbox",
        "folder-nextcloud", "folder-owncloud")
    put(P, "folder-development", folder("indigo", "code"), "folder-code", "folder-git", "folder-script")
    put(P, "folder-games", folder("red", "game"), "folder-steam")
    put(P, "folder-favorites", folder("orange", "star"), "folder-bookmark", "folder-bookmarks", "folder-important")
    put(P, "folder-locked", folder("gray", "lock"), "folder-encrypted")
    put(P, "folder-recent", folder("blue", "clock"))
    put(P, "folder-remote", folder("teal", "globe"), "folder-network")
    put(P, "folder-root", folder("red", "warn"))
    put(P, "folder-book", folder("purple", "book"), "folder-library")
    put(P, "folder-build", folder("gray", "box"), "folder-snap", "folder-flatpak")
    put(P, "user-home", user_home(), "folder-home", "user-home-symbolic-color", "go-home-color")
    put(P, "user-desktop", desktop_place())
    put(P, "user-trash", trash(), "trashcan_empty", "user-trash-empty", "emptytrash")
    put(P, "user-trash-full", trash(True), "trashcan_full")
    put(P, "network-workgroup", network_place(), "folder-network-workgroup", "network-workgroup-symbolic-color")
    put(P, "network-server", network_place("server"))
    put(P, "start-here", start_here(), "start-here-kde", "start-here-kde-plasma", "start-here-kubuntu",
        "distributor-logo", "start-here-branding")
    put(P, "bookmarks", category("orange", "star"), "favorites", "user-bookmarks")

    M = "mimetypes"
    put(M, "text-x-generic", mime_glyph(draw_text), "text-plain", "text-x-log", "application-x-zerosize",
        "text-x-readme", "text-x-changelog", "text-x-copying", "text-x-authors", "text-x-install")
    put(M, "unknown", mime_glyph(draw_unknown), "application-octet-stream", "application-x-generic")
    put(M, "image-x-generic", mime_glyph(draw_image), "image-png", "image-jpeg", "image-gif", "image-bmp",
        "image-webp", "image-tiff", "image-x-icon", "image-heic", "image-avif", "image-x-xcf", "image-svg+xml",
        "image-x-krita", "image-vnd.microsoft.icon")
    put(M, "audio-x-generic", mime_glyph(draw_audio), "audio-mpeg", "audio-x-mp3", "audio-flac", "audio-ogg",
        "audio-x-vorbis+ogg", "audio-x-wav", "audio-mp4", "audio-aac", "audio-x-m4a", "audio-opus", "audio-x-flac")
    put(M, "video-x-generic", mime_glyph(draw_video), "video-mp4", "video-x-matroska", "video-webm",
        "video-quicktime", "video-x-msvideo", "video-mpeg", "video-ogg", "video-x-flv")
    put(M, "package-x-generic", mime_glyph(draw_archive), "application-zip", "application-x-tar",
        "application-x-compressed-tar", "application-x-bzip-compressed-tar", "application-x-xz-compressed-tar",
        "application-x-7z-compressed", "application-x-rar", "application-vnd.rar", "application-gzip",
        "application-x-gzip", "application-x-bzip", "application-x-xz", "application-x-archive",
        "application-x-zstd-compressed-tar", "application-zstd", "application-x-lzma")
    put(M, "application-pdf", mime_label("PDF", BADGES["red"], c_lines("#D23A2F")), "application-x-pdf",
        "application-vnd.adobe.pdf")
    put(M, "x-office-document", mime_glyph(draw_writer), "application-vnd.oasis.opendocument.text",
        "application-msword", "application-vnd.openxmlformats-officedocument.wordprocessingml.document",
        "application-rtf", "text-rtf", "application-vnd.ms-word", "x-office-document-template",
        "application-vnd.oasis.opendocument.text-template")
    put(M, "x-office-spreadsheet", mime_glyph(draw_sheet), "application-vnd.oasis.opendocument.spreadsheet",
        "application-vnd.ms-excel", "application-vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        "text-csv", "text-x-csv", "x-office-spreadsheet-template")
    put(M, "x-office-presentation", mime_glyph(draw_pres), "application-vnd.oasis.opendocument.presentation",
        "application-vnd.ms-powerpoint",
        "application-vnd.openxmlformats-officedocument.presentationml.presentation", "x-office-presentation-template")
    put(M, "x-office-drawing", mime_label("ODG", BADGES["orange"], c_lines("#EA7317")),
        "application-vnd.oasis.opendocument.graphics")
    put(M, "x-office-calendar", mime_glyph(draw_calendar), "text-calendar", "text-x-vcalendar")
    put(M, "x-office-address-book", mime_glyph(draw_contact), "text-vcard", "text-x-vcard", "text-directory")
    put(M, "text-html", mime_glyph(draw_html), "application-xhtml+xml", "text-x-html")
    put(M, "text-x-script", mime_glyph(draw_script), "application-x-shellscript", "text-x-sh",
        "application-x-executable-script", "text-x-bash")
    put(M, "text-x-source", mime_glyph(draw_code), "text-x-csrc", "text-x-chdr", "text-x-c++src", "text-x-c++hdr",
        "text-x-java", "text-x-go", "text-x-rust", "text-rust", "application-javascript", "text-javascript",
        "text-css", "text-x-qml", "application-x-php", "text-x-makefile", "text-x-cmake", "text-x-c", "text-x-c++")
    put(M, "text-x-python", mime_label("PY", BADGES["blue"], c_lines("#1A73D9")), "text-x-python3",
        "application-x-python-bytecode")
    put(M, "application-json", mime_glyph(draw_json), "application-x-yaml", "text-x-yaml", "application-toml",
        "text-x-toml", "application-x-ipynb+json")
    put(M, "application-xml", mime_label("XML", BADGES["orange"], c_lines("#EA7317")), "text-xml")
    put(M, "text-markdown", mime_glyph(draw_markdown), "text-x-markdown")
    put(M, "application-x-executable", mime_glyph(draw_exec), "application-x-sharedlib", "application-x-object",
        "application-x-elf", "application-x-appimage", "application-vnd.appimage", "application-x-ms-dos-executable",
        "application-x-msdownload", "application-x-msi")
    put(M, "application-x-desktop", mime_glyph(draw_desktopfile), "application-x-kde-plasmoid")
    put(M, "application-x-cd-image", mime_glyph(draw_disc), "application-x-iso9660-image", "application-x-iso",
        "application-vnd.efi.iso", "application-x-raw-disk-image")
    put(M, "application-x-deb", mime_glyph(draw_package), "application-vnd.debian.binary-package",
        "application-x-rpm", "application-x-flatpak", "application-vnd.flatpak.ref", "application-vnd.snap",
        "application-x-redhat-package-manager")
    put(M, "font-x-generic", mime_glyph(draw_font), "application-x-font-ttf", "font-ttf", "font-otf",
        "application-x-font-otf", "font-woff", "font-woff2", "application-x-font-type1")
    put(M, "application-sql", mime_glyph(draw_db), "application-x-sqlite3", "application-vnd.sqlite3",
        "application-x-sqlite2")
    put(M, "application-epub+zip", mime_label("EPUB", BADGES["green"], c_lines("#1E9447")),
        "application-x-mobipocket-ebook", "application-vnd.amazon.ebook")
    put(M, "application-x-trash", mime_glyph(draw_unknown))

    D = "devices"
    put(D, "computer", computer(), "video-display", "computer-symbolic-color", "preferences-desktop-display")
    put(D, "computer-laptop", laptop())
    put(D, "drive-harddisk", harddisk(), "drive-harddisk-root", "drive-harddisk-system", "harddrive",
        "drive-multidisk", "drive-harddisk-encrypted")
    put(D, "drive-harddisk-solidstate", harddisk(True), "drive-harddisk-ssd", "drive-harddisk-nvme")
    put(D, "drive-removable-media", usb_stick(), "drive-removable-media-usb", "media-flash",
        "drive-removable-media-usb-pendrive", "media-flash-memory-stick", "media-flash-sd-mmc", "drive-removable")
    put(D, "media-optical", optical(), "drive-optical", "media-optical-cd", "media-optical-dvd",
        "media-optical-blu-ray", "media-optical-audio", "media-optical-data")
    put(D, "phone", phone(), "smartphone", "pda", "phone-symbolic-color", "kdeconnect")
    put(D, "input-keyboard", keyboard(), "preferences-desktop-keyboard")
    put(D, "input-mouse", mouse(), "preferences-desktop-mouse")
    put(D, "printer", printer(), "printer-network", "printer-printing", "preferences-devices-printer",
        "printer-symbolic-color")
    put(D, "camera-photo", camera(), "camera-web", "camera-video", "accessories-camera")
    put(D, "audio-headphones", headphones(), "audio-headset", "headphones")
    put(D, "audio-speakers", speakers(), "audio-card", "audio-speakers-symbolic-color")
    put(D, "input-gaming", gamepad(), "input-gamepad", "joystick")
    put(D, "network-wired", ethernet(), "network-card")
    put(D, "scanner", scanner(), "org.kde.skanlite", "org.kde.skanpage")
    put(D, "battery", battery_dev(), "preferences-system-power", "preferences-system-power-management")

    A = "apps"
    put(A, "system-file-manager", file_manager_app(), "org.kde.dolphin", "dolphin", "file-manager",
        "org.gnome.Nautilus", "nautilus", "thunar", "nemo", "pcmanfm")
    put(A, "utilities-terminal", terminal_app(), "org.kde.konsole", "konsole",
        "org.gnome.Terminal", "gnome-terminal", "org.kde.yakuake", "xterm")
    put(A, "preferences-system", settings_app(), "systemsettings", "preferences-desktop",
        "org.kde.systemsettings", "gnome-settings", "preferences-other", "applications-system-settings")
    put(A, "system-software-install", store_app(), "org.kde.discover", "plasmadiscover", "software-store",
        "system-software-update", "softwarecenter", "org.gnome.Software", "applications-store")
    put(A, "accessories-text-editor", editor_app(), "org.kde.kate", "org.kde.kwrite", "kate", "kwrite",
        "text-editor", "org.gnome.TextEditor", "gedit")
    put(A, "internet-web-browser", browser_app(), "web-browser", "applications-webbrowsers")
    put(A, "utilities-system-monitor", sysmon_app(), "org.kde.plasma-systemmonitor", "ksysguard",
        "plasma-systemmonitor", "gnome-system-monitor", "htop", "system-monitor")
    put(A, "accessories-calculator", calc_app(), "org.kde.kcalc", "kcalc",
        "org.gnome.Calculator", "galculator", "org.kde.kalk")
    put(A, "utilities-archiver", archive_app(), "org.kde.ark", "ark", "file-roller", "archive-manager",
        "org.gnome.FileRoller")
    put(A, "image-viewer", viewer_image_app(), "org.kde.gwenview", "gwenview", "eog", "org.gnome.eog",
        "multimedia-photo-viewer", "applications-graphics-viewer")
    put(A, "document-viewer", viewer_doc_app(), "org.kde.okular", "okular", "evince", "org.gnome.Evince",
        "atril", "org.gnome.Papers")
    put(A, "applets-screenshooter", screenshot_app(), "org.kde.spectacle", "spectacle",
        "gnome-screenshot", "org.gnome.Screenshot", "accessories-screenshot")
    put(A, "help-browser", help_app(), "system-help", "org.kde.help", "khelpcenter", "yelp")
    put(A, "hwinfo", info_app(), "org.kde.kinfocenter", "kinfocenter", "system-information", "dialog-information-app")
    put(A, "multimedia-video-player", player_video_app(), "org.kde.dragonplayer", "dragonplayer",
        "org.kde.haruna", "haruna", "totem", "org.gnome.Totem", "video-player", "mpv", "celluloid")
    put(A, "multimedia-audio-player", round_glyph_app("pink", "music"), "org.kde.elisa", "elisa",
        "audio-player", "rhythmbox", "org.gnome.Rhythmbox3", "juk", "amarok", "org.kde.juk")
    put(A, "org.kde.kdeconnect.app", kdeconnect_app(), "kdeconnect-app", "kdeconnectindicator")
    put(A, "partitionmanager", disk_app(), "org.kde.partitionmanager", "gparted", "gnome-disks",
        "org.gnome.DiskUtility", "org.kde.filelight", "filelight", "baobab")
    put(A, "kwalletmanager", wallet_app(), "org.kde.kwalletmanager5", "org.kde.kwalletmanager", "kwalletmanager2",
        "wallet-open", "seahorse", "org.gnome.seahorse.Application")
    put(A, "system-search", round_glyph_app("indigo", "search"), "org.kde.kfind", "kfind", "edit-find-app",
        "catfish", "org.kde.krunner")
    put(A, "preferences-desktop-notification", round_glyph_app("orange", "info"), "notifications-app")
    put(A, "accessories-character-map", tile_glyph_app("gray", "book"), "org.kde.kcharselect", "kcharselect",
        "gucharmap")
    put(A, "system-users", round_glyph_app("teal", "people"), "preferences-system-users", "user-identity",
        "preferences-desktop-user", "kuser", "system-config-users")
    put(A, "preferences-system-network", round_glyph_app("blue", "globe"), "preferences-system-network-connection",
        "network-manager", "nm-device-wired", "preferences-desktop-network")
    put(A, "preferences-system-privacy", shield("indigo", "lock"), "preferences-security", "security-medium-app",
        "preferences-system-firewall", "firewall-config")
    put(A, "preferences-desktop-wallpaper", viewer_image_app(), "preferences-desktop-theme",
        "preferences-desktop-color", "preferences-desktop-theme-global", "preferences-desktop-icons")
    put(A, "applications-games-app", category("red", "game"), "org.kde.kpat", "kpat", "org.kde.kmahjongg",
        "kmahjongg", "org.kde.kmines", "kmines", "gnome-mines", "aisleriot")

    C = "categories"
    put(C, "applications-internet", category("blue", "globe"), "applications-network")
    put(C, "applications-multimedia", category("pink", "play"), "applications-media")
    put(C, "applications-graphics", category("green", "picture"), "applications-photography")
    put(C, "applications-office", category("orange", "doc"), "applications-documentation")
    put(C, "applications-development", category("indigo", "code"), "applications-engineering",
        "applications-programming")
    put(C, "applications-games", category("red", "game"), "applications-gaming")
    put(C, "applications-system", category("gray", "server"), "applications-administration")
    put(C, "applications-utilities", category("teal", "box"), "applications-accessories")
    put(C, "applications-education", category("purple", "book"), "applications-education-miscellaneous",
        "applications-education-language", "applications-education-school")
    put(C, "applications-science", category("teal", "search"), "applications-education-science")
    put(C, "applications-other", category("gray", "star"), "applications-all", "applications-miscellaneous")
    put(C, "preferences-desktop-accessibility", category("blue", "people"), "preferences-desktop-accessibility-app")

    S = "status"
    put(S, "dialog-information", dialog("information"), "dialog-information-color")
    put(S, "dialog-warning", dialog("warning"), "dialog-warning-color", "emblem-warning")
    put(S, "dialog-error", dialog("error"), "dialog-error-color", "emblem-error")
    put(S, "dialog-question", dialog("question"), "dialog-question-color")
    put(S, "dialog-ok", dialog("ok"), "emblem-success", "emblem-ok", "dialog-ok-apply-color")
    put(S, "security-high", shield("green", "check"), "security-high-color")
    put(S, "security-medium", shield("orange", "warn"), "security-medium-color")
    put(S, "security-low", shield("red", "x"), "security-low-color")
    return icons, aliases


# --------------------------------------------------------------------------------
# Writing the themes
# --------------------------------------------------------------------------------
CONTEXTS = {"actions": "Actions", "animations": "Animations", "applets": "Applets", "apps": "Applications",
            "categories": "Categories", "devices": "Devices", "emblems": "Emblems", "emotes": "Emotes",
            "mimetypes": "MimeTypes", "places": "Places", "preferences": "Applications", "status": "Status"}
BREEZE_REF = os.path.join(ROOT, "tools", "breeze-ref")
SESSION_COLOR = {"light": "#232629", "dark": "#FCFCFC"}
MEDIA_TYPES = {"text", "application", "image", "audio", "inode", "video", "message", "model", "multipart",
               "x-content", "x-epoc"}


def kiconloader_match(name, have):
    """Which name of `have` KIconLoader picks for `name` inside one theme (or None).

    Same steps as KIconLoaderPrivate::findMatchingIcon (KDE Frameworks 6): before moving on to the
    inherited theme (Breeze), KDE shortens the name inside the current theme, "a-b-c" -> "a-b" -> "a".
    A short name in Onze Icons would therefore win over Breeze's exact icon: e.g. a "system" icon
    would replace system-shutdown, system-reboot, system-lock-screen...
    """
    symbolic = name.endswith("-symbolic")
    cur, generic = name, False
    while cur:
        if cur in have:
            return cur
        if generic:
            break
        if symbolic:
            cur = cur[:-len("-symbolic")]
            if cur in have:
                return cur
        i = cur.rfind("-")
        if i > 1:
            cur = cur[:i]
            if cur.endswith("-x"):
                cur = cur[:-2]
            if symbolic:
                cur += "-symbolic"
        elif cur in MEDIA_TYPES:
            cur, generic = cur + "-x-generic", True
        else:
            break
    return None


def capture_is_wanted(requested, got, ctx, breeze_ctx):
    """Is it fine that `requested` (a Breeze icon of context breeze_ctx) shows Onze's `got` instead?"""
    if requested.endswith("-symbolic"):
        return ctx == "actions"                     # our session glyphs are monochrome already
    if ctx == "mimetypes" and breeze_ctx == {"mimetypes"}:
        return True                                 # e.g. *-template -> same document type
    if ctx == "places" and got.startswith("folder") and breeze_ctx == {"places"}:
        return True                                 # folder-activities -> plain Onze folder
    if ctx == "actions":
        return "inhibited" not in requested         # system-reboot-update -> reboot
    return False


def breeze_links(names_ctx):
    """Breeze icons that Onze would hide through the shortened-name lookup -> (dir, name) to link."""
    import gzip
    with gzip.open(os.path.join(BREEZE_REF, "files.txt.gz"), "rt") as f:
        files = [l.strip() for l in f if l.strip() and not l.startswith("#")]
    by_name = {}
    for path in files:
        d, n = path.rsplit("/", 1)
        by_name.setdefault(n, []).append(d)
    links, wanted = [], 0
    for n, dirs in sorted(by_name.items()):
        if n in names_ctx:
            continue
        got = kiconloader_match(n, names_ctx)
        if got is None:
            continue
        if capture_is_wanted(n, got, names_ctx[got], {d.split("/")[0] for d in dirs}):
            wanted += 1
            continue
        links += [(d, n) for d in dirs]
    return links, wanted


def breeze_dir_specs():
    specs, cur = {}, None
    for line in open(os.path.join(BREEZE_REF, "dirs.ini")):
        line = line.strip()
        if line.startswith("[") and line.endswith("]"):
            cur = line[1:-1]
            specs[cur] = []
        elif cur and "=" in line:
            specs[cur].append(line)
    return specs


def index_theme(name, comment, inherits, dirs):
    """dirs: list of (directory, [key=value, ...])"""
    lines = ["[Icon Theme]", f"Name={name}", f"Comment={comment}", f"Inherits={inherits}",
             "Example=folder", "DisplayDepth=32", "FollowsColorScheme=true",
             "LinkOverlay=link", "LockOverlay=lockoverlay",
             "ZipOverlay=zip", "DesktopDefault=48", "ToolbarDefault=22", "MainToolbarDefault=22",
             "SmallDefault=16", "PanelDefault=48", "",
             "Directories=" + ",".join(d for d, _ in dirs), ""]
    for d, keys in dirs:
        lines += [f"[{d}]"] + keys + [""]
    return "\n".join(lines)


def scalable(ctx, size=64):
    return [f"Size={size}", f"Context={CONTEXTS[ctx]}", "Type=Scalable", "MinSize=8", "MaxSize=512"]


def write_theme():
    icons, aliases = build()
    for d in (LIGHT, DARK):
        if os.path.isdir(d):
            shutil.rmtree(d)
    dirs = []
    count = 0
    for ctx, items in icons.items():
        folder_ = os.path.join(LIGHT, ctx, "scalable")
        os.makedirs(folder_, exist_ok=True)
        dirs.append((f"{ctx}/scalable", scalable(ctx)))
        for name, svg in items.items():
            with open(os.path.join(folder_, name + ".svg"), "w") as f:
                f.write(svg)
            count += 1
    for (ctx, alias), target in aliases.items():
        link = os.path.join(LIGHT, ctx, "scalable", alias + ".svg")
        if not os.path.exists(link):
            os.symlink(target + ".svg", link)
    # symbolic Start icons (for menus that ask for the symbolic variant)
    sym = os.path.join(LIGHT, "places", "symbolic")
    os.makedirs(sym, exist_ok=True)
    dirs.append(("places/symbolic", scalable("places", 16)))
    with open(os.path.join(sym, "start-here-symbolic.svg"), "w") as f:
        f.write(start_here_symbolic())
    for a in ("start-here-kde-symbolic", "start-here-kde-plasma-symbolic"):
        os.symlink("start-here-symbolic.svg", os.path.join(sym, a + ".svg"))

    # session / power actions (Start menu: sleep, restart, shut down, lock, log out, switch user).
    # Monochrome; each variant gets its own copy with a matching default color.
    dirs.append(("actions/symbolic", scalable("actions", 24)))
    for theme, variant in ((LIGHT, "light"), (DARK, "dark")):
        out = os.path.join(theme, "actions", "symbolic")
        os.makedirs(out, exist_ok=True)
        for kind, names in SESSION_ICONS.items():
            with open(os.path.join(out, names[0] + ".svg"), "w") as f:
                f.write(session_icon(kind, SESSION_COLOR[variant]))
            for n in names[1:] + [x + "-symbolic" for x in names]:
                os.symlink(names[0] + ".svg", os.path.join(out, n + ".svg"))
    count += len(SESSION_ICONS)

    # every name Onze provides, with its context
    names_ctx = {}
    for ctx, items in icons.items():
        names_ctx.update({n: ctx for n in items})
    names_ctx.update({a: ctx for (ctx, a) in aliases})
    names_ctx.update({n: "places" for n in ("start-here-symbolic", "start-here-kde-symbolic",
                                             "start-here-kde-plasma-symbolic")})
    for names in SESSION_ICONS.values():
        names_ctx.update({n: "actions" for n in names + [x + "-symbolic" for x in names]})

    # Breeze icons that the shortened-name lookup would replace with an unrelated Onze icon
    # (battery levels, network states, System Settings pages...) are linked to the installed
    # Breeze files, so they look exactly as they would with Breeze. Links are absolute; a missing
    # target is simply skipped by KDE and the normal fallback applies.
    links, wanted = breeze_links(names_ctx)
    specs = breeze_dir_specs()
    used = sorted({d for d, _ in links if d in specs})
    for theme, breeze in ((LIGHT, "breeze"), (DARK, "breeze-dark")):
        for d, n in links:
            if d not in specs:
                continue
            out = os.path.join(theme, "breeze-links", d)
            os.makedirs(out, exist_ok=True)
            os.symlink(f"/usr/share/icons/{breeze}/{d}/{n}.svg", os.path.join(out, n + ".svg"))
    dirs += [(f"breeze-links/{d}", specs[d]) for d in used]
    n_links = sum(1 for d, _ in links if d in specs)

    comment = "Original Fluent-style icons for the Onze theme (Windows 11 inspired)"
    with open(os.path.join(LIGHT, "index.theme"), "w") as f:
        f.write(index_theme("Onze", comment, "breeze,hicolor", dirs))
    # dark variant: same drawings (shared through symlinks), dark fallbacks
    for ctx in icons:
        os.symlink(f"../OnzeIcons/{ctx}", os.path.join(DARK, ctx))
    with open(os.path.join(DARK, "index.theme"), "w") as f:
        f.write(index_theme("Onze Dark", comment + " — dark variant", "breeze-dark,hicolor", dirs))
    for d in (LIGHT, DARK):
        with open(os.path.join(d, "AUTHORS"), "w") as f:
            f.write("Onze Icons " + VERSION + "\nProjeto Onze — Rafael Carvalho Ramos <rafaelramosmacae@gmail.com>\n"
                    "All icons are original work, generated by tools/gerar_icones.py.\n"
                    "Text labels use outlines of the Inter font (SIL Open Font License 1.1).\n"
                    "breeze-links/ only holds links to the Breeze icons already installed on the system\n"
                    "(no Breeze files are included).\n")
    n_alias = sum(1 for _ in aliases)
    print(f"Onze Icons: {count} drawings, {n_alias} alias names, {n_links} links to Breeze "
          f"({len({n for _, n in links})} names; {wanted} shortened-name matches kept on purpose) -> {LIGHT}")
    return icons


def contact_sheet(icons):
    import io
    import cairosvg
    from PIL import Image, ImageDraw, ImageFont
    items = [(ctx, n, s) for ctx, d in icons.items() for n, s in d.items()]
    cols, cell = 12, 92
    rows = (len(items) + cols - 1) // cols
    W, H = cols * cell, rows * cell
    sheet = Image.new("RGB", (W * 2 + 20, H + 40), (255, 255, 255))
    font = ImageFont.truetype("/usr/share/fonts/opentype/inter/Inter-Regular.otf", 9)
    d = ImageDraw.Draw(sheet)
    d.rectangle((W + 20, 0, W * 2 + 20, H + 40), fill=(32, 32, 32))
    for i, (ctx, n, s) in enumerate(items):
        x, y = (i % cols) * cell, (i // cols) * cell + 20
        png = cairosvg.svg2png(bytestring=s.encode(), output_width=48, output_height=48)
        im = Image.open(io.BytesIO(png)).convert("RGBA")
        sm = Image.open(io.BytesIO(cairosvg.svg2png(bytestring=s.encode(), output_width=22, output_height=22))).convert("RGBA")
        for ox, bg in ((0, (243, 243, 243)), (W + 20, (32, 32, 32))):
            sheet.paste(im, (ox + x + 10, y + 4), im)
            sheet.paste(sm, (ox + x + 62, y + 17), sm)
        label = n if len(n) <= 17 else n[:16] + "…"
        d.text((x + 4, y + 56), label, font=font, fill=(60, 60, 60))
        d.text((W + 20 + x + 4, y + 56), label, font=font, fill=(200, 200, 200))
    out = os.path.join(ROOT, "tools", "previa-icones.png")
    sheet.save(out)
    print("Preview:", out)


if __name__ == "__main__":
    icons = write_theme()
    contact_sheet(icons)
