#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Gerador dos recursos gráficos do tema global "Onze" para KDE Plasma 6.

Gera, dentro de ../src:
  - color-schemes/OnzeClaro.colors e OnzeEscuro.colors
  - desktoptheme/Onze            (estilo do Plasma: painel, menus, dicas, tarefas)
  - aurorae/Onze-Claro|Escuro     (decoração das janelas)
  - wallpapers/Onze               (papel de parede original, claro e escuro)
  - previews dos pacotes look-and-feel

Requisitos (apenas para regenerar; o tema já vem gerado):
  pip install numpy pillow shapely scipy

Uso:  python3 tools/gerar_tema.py [--procedural-wallpaper]
"""
import base64
import gzip
import io
import json
import math
import os
import shutil
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont
from scipy.ndimage import gaussian_filter
from shapely.geometry import LineString, Polygon, box
from shapely.ops import unary_union

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Authorship and version used in every generated metadata file
VERSION = "1.4"
AUTHOR = {"Name": "Rafael Carvalho Ramos", "Email": "rafaelramosmacae@gmail.com"}
COPYRIGHT = "© 2026 Projeto Onze — Rafael Carvalho Ramos"
SRC = os.path.join(ROOT, "src")

# ---------------------------------------------------------------------------
# Paleta (valores de referência do Fluent Design / Windows 11)
# ---------------------------------------------------------------------------
LIGHT = dict(
    window="#F3F3F3", view="#FFFFFF", alt="#F9F9F9", button="#FBFBFB",
    text="#1A1A1A", inactive="#5F5F5F", disabled="#A0A0A0",
    accent="#0067C0", hl_text="#FFFFFF", link="#005FB8", visited="#7A4EB0",
    negative="#C42B1C", neutral="#9D5D00", positive="#0F7B0F",
    tooltip="#F9F9F9", focus="#0067C0", hover="#1975C5",
)
DARK = dict(
    window="#202020", view="#272727", alt="#2B2B2B", button="#2D2D2D",
    text="#FFFFFF", inactive="#A8A8A8", disabled="#6E6E6E",
    accent="#4CC2FF", hl_text="#000000", link="#99EBFF", visited="#D7A6FF",
    negative="#FF99A4", neutral="#FCE100", positive="#6CCB5F",
    tooltip="#2C2C2C", focus="#4CC2FF", hover="#60CDFF",
)


def rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def rgbs(h):
    return ",".join(str(c) for c in rgb(h))


def write(path, data, mode="w"):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, mode) as f:
        f.write(data)


# ---------------------------------------------------------------------------
# 1. Esquemas de cores
# ---------------------------------------------------------------------------
def color_scheme(p, name, ident, dark):
    def group(bg, alt, fg, inactive, extra_hl=None):
        return {
            "BackgroundAlternate": alt, "BackgroundNormal": bg,
            "DecorationFocus": p["focus"], "DecorationHover": p["hover"],
            "ForegroundActive": p["accent"] if extra_hl is None else extra_hl,
            "ForegroundInactive": inactive, "ForegroundLink": p["link"],
            "ForegroundNegative": p["negative"], "ForegroundNeutral": p["neutral"],
            "ForegroundNormal": fg, "ForegroundPositive": p["positive"],
            "ForegroundVisited": p["visited"],
        }

    groups = {
        "Colors:Button": group(p["button"], p["alt"], p["text"], p["inactive"]),
        "Colors:Complementary": group(DARK["window"], DARK["alt"], DARK["text"],
                                      DARK["inactive"], DARK["accent"]),
        "Colors:Header": group(p["window"], p["alt"], p["text"], p["inactive"]),
        "Colors:Header][Inactive": group(p["window"], p["alt"], p["text"], p["inactive"]),
        "Colors:Selection": group(p["accent"], p["hover"], p["hl_text"], p["hl_text"],
                                  p["hl_text"]),
        "Colors:Tooltip": group(p["tooltip"], p["alt"], p["text"], p["inactive"]),
        "Colors:View": group(p["view"], p["alt"], p["text"], p["inactive"]),
        "Colors:Window": group(p["window"], p["alt"], p["text"], p["inactive"]),
    }
    # Links/realces dentro da seleção precisam continuar legíveis
    groups["Colors:Selection"]["ForegroundLink"] = p["hl_text"]
    groups["Colors:Selection"]["ForegroundVisited"] = p["hl_text"]

    out = [
        "[ColorEffects:Disabled]",
        "Color=56,56,56", "ColorAmount=0", "ColorEffect=0",
        "ContrastAmount=0.65", "ContrastEffect=1",
        "IntensityAmount=0.1", "IntensityEffect=2", "",
        "[ColorEffects:Inactive]",
        "ChangeSelectionColor=false", "Color=112,111,110", "ColorAmount=0.025",
        "ColorEffect=2", "ContrastAmount=0.1", "ContrastEffect=2", "Enable=false",
        "IntensityAmount=0", "IntensityEffect=0", "",
    ]
    for g in sorted(groups):
        out.append(f"[{g}]")
        for k in sorted(groups[g]):
            out.append(f"{k}={rgbs(groups[g][k])}")
        out.append("")
    out += [
        "[General]", f"ColorScheme={ident}", f"Name={name}",
        "shadeSortColumn=true", "", "[KDE]", "contrast=4", "",
        "[WM]",
        f"activeBackground={rgbs(p['window'])}",
        f"activeBlend={rgbs(p['window'])}",
        f"activeForeground={rgbs(p['text'])}",
        f"inactiveBackground={rgbs(p['window'])}",
        f"inactiveBlend={rgbs(p['window'])}",
        f"inactiveForeground={rgbs(p['disabled'])}", "",
    ]
    write(os.path.join(SRC, "color-schemes", f"{ident}.colors"), "\n".join(out))


# ---------------------------------------------------------------------------
# 2. Utilidades de geometria / SVG
# ---------------------------------------------------------------------------
def rrect(x0, y0, x1, y1, r, corners=(1, 1, 1, 1), n=24):
    """Retângulo arredondado (y para baixo). corners = (tl, tr, br, bl)."""
    if r <= 0:
        return box(x0, y0, x1, y1)
    tl, tr, br, bl = corners
    pts = []

    def arc(cx, cy, a0, a1):
        return [(cx + r * math.cos(math.radians(a0 + (a1 - a0) * i / n)),
                 cy + r * math.sin(math.radians(a0 + (a1 - a0) * i / n)))
                for i in range(n + 1)]
    pts += arc(x0 + r, y0 + r, 180, 270) if tl else [(x0, y0)]
    pts += arc(x1 - r, y0 + r, 270, 360) if tr else [(x1, y0)]
    pts += arc(x1 - r, y1 - r, 0, 90) if br else [(x1, y1)]
    pts += arc(x0 + r, y1 - r, 90, 180) if bl else [(x0, y1)]
    return Polygon(pts)


def ring(x0, y0, x1, y1, r, w=1.0, corners=(1, 1, 1, 1)):
    return rrect(x0, y0, x1, y1, r, corners).difference(
        rrect(x0 + w, y0 + w, x1 - w, y1 - w, max(r - w, 0), corners))


def pill(x0, y0, x1, y1):
    r = min(x1 - x0, y1 - y0) / 2
    return rrect(x0, y0, x1, y1, r)


def to_d(g, dx=0.0, dy=0.0):
    if g.is_empty:
        return ""
    polys = [g] if g.geom_type == "Polygon" else [
        p for p in getattr(g, "geoms", []) if p.geom_type == "Polygon"]
    parts = []
    for p in polys:
        for rg in [p.exterior, *p.interiors]:
            c = list(rg.coords)[:-1]
            if len(c) < 3:
                continue
            parts.append("M" + " L".join(f"{x + dx:.3f},{y + dy:.3f}" for x, y in c) + "Z")
    return " ".join(parts)


def png_b64(img):
    buf = io.BytesIO()
    img.save(buf, "PNG", optimize=True)
    return base64.b64encode(buf.getvalue()).decode()


class Paint:
    """Pintura de uma camada: classe do esquema de cores ou cor fixa."""

    def __init__(self, cls=None, color=None, opacity=1.0):
        self.cls, self.color, self.opacity = cls, color, opacity

    def attrs(self):
        op = f";fill-opacity:{self.opacity:.3f}" if self.opacity < 1 else ""
        if self.cls:
            return f'class="{self.cls}" style="fill:currentColor{op};stroke:none"'
        return f'style="fill:{self.color}{op};stroke:none"'


NAMES = [["topleft", "top", "topright"],
         ["left", "center", "right"],
         ["bottomleft", "bottom", "bottomright"]]


class SvgSheet:
    """Folha SVG que acumula molduras 9-slice (formato FrameSvg do KSvg)."""

    GAP = 6

    def __init__(self):
        self.parts = []
        self.y = 0
        self.width = 0

    def frame(self, prefix, cols, rows, layers=(), image=None, hints=None):
        """cols/rows: [(a,b),(c,c+1),(d,e)] intervalos na origem;
        layers: [(geom, Paint)]; image: PIL RGBA no mesmo sistema de coordenadas."""
        pre = f"{prefix}-" if prefix else ""
        x_cursor_base = 0
        row_y = self.y
        for i in range(3):
            x_cursor = x_cursor_base
            th = rows[i][1] - rows[i][0]
            for j in range(3):
                tw = cols[j][1] - cols[j][0]
                sx, sy = cols[j][0], rows[i][0]
                dx, dy = x_cursor - sx, row_y - sy
                tile = box(sx, sy, sx + tw, sy + th)
                el = [f'<g id="{pre}{NAMES[i][j]}">',
                      f'<rect x="{x_cursor}" y="{row_y}" width="{tw}" height="{th}" '
                      f'style="fill:none;stroke:none"/>']
                if image is not None:
                    crop = image.crop((sx, sy, sx + tw, sy + th))
                    if crop.getbbox() is not None:
                        el.append(f'<image x="{x_cursor}" y="{row_y}" width="{tw}" '
                                  f'height="{th}" preserveAspectRatio="none" '
                                  f'xlink:href="data:image/png;base64,{png_b64(crop)}"/>')
                for geom, paint in layers:
                    piece = geom.intersection(tile)
                    d = to_d(piece, dx, dy)
                    if d:
                        el.append(f'<path {paint.attrs()} fill-rule="evenodd" d="{d}"/>')
                el.append("</g>")
                self.parts.append("".join(el))
                x_cursor += tw + self.GAP
            self.width = max(self.width, x_cursor)
            row_y += th + self.GAP
        hx = self.width + self.GAP
        for name, (w, h) in (hints or {}).items():
            self.parts.append(f'<rect id="{pre}{name}" x="{hx}" y="{self.y}" width="{w}" '
                              f'height="{h}" style="fill:none;stroke:none"/>')
            hx += w + self.GAP
        self.width = max(self.width, hx)
        self.y = row_y + self.GAP * 2

    def raw(self, svg_fragment, w, h):
        self.parts.append(f'<g transform="translate(0,{self.y})">{svg_fragment}</g>')
        self.width = max(self.width, w)
        self.y += h + self.GAP * 2

    def svg(self, scheme=True):
        style = ""
        if scheme:
            style = ('<defs><style type="text/css" id="current-color-scheme">'
                     ".ColorScheme-Text{color:#1a1a1a;}"
                     ".ColorScheme-Background{color:#f3f3f3;}"
                     ".ColorScheme-ViewBackground{color:#ffffff;}"
                     ".ColorScheme-Highlight{color:#0067c0;}"
                     ".ColorScheme-NeutralText{color:#9d5d00;}"
                     ".ColorScheme-NegativeText{color:#c42b1c;}"
                     "</style></defs>")
        return ('<?xml version="1.0" encoding="UTF-8"?>\n'
                f'<svg xmlns="http://www.w3.org/2000/svg" '
                f'xmlns:xlink="http://www.w3.org/1999/xlink" version="1.1" '
                f'width="{self.width}" height="{self.y}" '
                f'viewBox="0 0 {self.width} {self.y}">{style}'
                + "\n".join(self.parts) + "</svg>\n")


def save_svgz(sheet, path, scheme=True):
    data = sheet.svg(scheme).encode()
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with gzip.open(path, "wb", compresslevel=9) as f:
        f.write(data)
    return data


# ---------------------------------------------------------------------------
# 3. Sombras (rasterizadas e fatiadas)
# ---------------------------------------------------------------------------
def shadow_image(W, H, win, shape, layers):
    """Retorna imagem RGBA (preto + alfa) com a sombra de `shape`,
    recortando a área ocupada pela própria janela.
    layers: [(sigma, offset_y, alpha)]"""
    m = Image.new("L", (W * 4, H * 4), 0)
    ImageDraw.Draw(m).polygon([(x * 4, y * 4) for x, y in shape.exterior.coords], fill=255)
    m = np.asarray(m.resize((W, H), Image.LANCZOS), dtype=np.float32) / 255.0
    acc = np.zeros_like(m)
    for sigma, offy, alpha in layers:
        sh = np.roll(m, offy, axis=0)
        if offy > 0:
            sh[:offy, :] = 0
        acc = 1 - (1 - acc) * (1 - alpha * gaussian_filter(sh, sigma))
    a = np.clip(acc * (1 - m), 0, 1)
    img = np.zeros((H, W, 4), dtype=np.uint8)
    img[..., 3] = (a * 255 + 0.5).astype(np.uint8)
    return Image.fromarray(img, "RGBA")


def add_shadow_frame(sheet, prefix, S, r, layers, top=None, bottom=None):
    """Adiciona elementos shadow-* (para Dialog/Tooltip do Plasma)."""
    top = S if top is None else top
    bottom = S if bottom is None else bottom
    ww, wh = 240, 160
    W, H = ww + 2 * S, wh + top + bottom
    win = (S, top, S + ww, top + wh)
    shape = rrect(*win, r)
    img = shadow_image(W, H, win, shape, layers)
    cols = [(0, S + r), (W // 2, W // 2 + 1), (W - S - r, W)]
    rows = [(0, top + r), (H // 2, H // 2 + 1), (H - bottom - r, H)]
    pre = f"{prefix}-shadow" if prefix else "shadow"
    hints = {"hint-top-margin": (1, top), "hint-bottom-margin": (1, bottom),
             "hint-left-margin": (S, 1), "hint-right-margin": (S, 1)}
    sheet.frame(pre, cols, rows, image=img, hints=hints)


# ---------------------------------------------------------------------------
# 4. Estilo do Plasma (desktoptheme)
# ---------------------------------------------------------------------------
BG = "ColorScheme-Background"
TX = "ColorScheme-Text"
HL = "ColorScheme-Highlight"
NE = "ColorScheme-NeutralText"


def rounded_box_frame(sheet, prefix, r, fill_op, border_op, sides=(1, 1, 1, 1),
                      corners=(1, 1, 1, 1), fill_cls=BG, hints=None, mask=True,
                      core=None):
    """Moldura arredondada simples com borda de 1px.
    sides = (top, right, bottom, left) -> 1 desenha a borda naquele lado."""
    c = max(r, 2) if core is None else core
    W = H = 2 * c + 1
    outer = rrect(0, 0, W, H, r, corners)
    t, rt, b, lf = sides
    inner = rrect(lf, t, W - rt, H - b, max(r - 1, 0), corners)
    border = outer.difference(inner)
    layers = []
    if fill_op > 0:
        layers.append((inner, Paint(cls=fill_cls, opacity=fill_op)))
    if border_op > 0 and not border.is_empty:
        layers.append((border, Paint(cls=TX, opacity=border_op)))
    cols = [(0, c), (c, c + 1), (c + 1, W)]
    sheet.frame(prefix, cols, cols, layers, hints=hints)
    if mask:
        mp = f"mask-{prefix}" if prefix else "mask"
        sheet.frame(mp, cols, cols, [(outer, Paint(color="#000000"))])


def desktoptheme():
    base = os.path.join(SRC, "desktoptheme", "Onze")
    if os.path.isdir(base):
        shutil.rmtree(base)

    dlg_shadow = [(1.5, 1, 0.10), (9, 5, 0.26)]
    tip_shadow = [(1.2, 1, 0.10), (5, 2, 0.18)]

    # --- dialogs/background (menus, popups, Kickoff) -------------------------
    for sub, op in (("", 0.97), ("translucent/", 0.84), ("opaque/", 1.0)):
        s = SvgSheet()
        r = 0 if sub == "opaque/" else 8
        rounded_box_frame(s, "", r, op, 0.13,
                          hints={"hint-top-margin": (1, 10), "hint-bottom-margin": (1, 10),
                                 "hint-left-margin": (10, 1), "hint-right-margin": (10, 1)},
                          mask=(sub != "opaque/"))
        if sub != "opaque/":
            add_shadow_frame(s, "", 22, 8, dlg_shadow, top=18, bottom=28)
        save_svgz(s, os.path.join(base, sub + "dialogs/background.svgz"))

    # --- widgets/background (widgets na área de trabalho) --------------------
    for sub, op in (("", 0.92), ("translucent/", 0.78), ("opaque/", 1.0)):
        s = SvgSheet()
        r = 0 if sub == "opaque/" else 8
        rounded_box_frame(s, "", r, op, 0.10,
                          hints={"hint-top-margin": (1, 12), "hint-bottom-margin": (1, 12),
                                 "hint-left-margin": (12, 1), "hint-right-margin": (12, 1)},
                          mask=(sub != "opaque/"))
        if sub != "opaque/":
            add_shadow_frame(s, "", 18, 8, dlg_shadow, top=14, bottom=22)
        save_svgz(s, os.path.join(base, sub + "widgets/background.svgz"))

    # --- widgets/tooltip ----------------------------------------------------
    for sub, op in (("", 0.98), ("translucent/", 0.88), ("opaque/", 1.0)):
        s = SvgSheet()
        r = 0 if sub == "opaque/" else 6
        rounded_box_frame(s, "", r, op, 0.13,
                          hints={"hint-top-margin": (1, 6), "hint-bottom-margin": (1, 6),
                                 "hint-left-margin": (8, 1), "hint-right-margin": (8, 1)},
                          mask=(sub != "opaque/"))
        if sub != "opaque/":
            add_shadow_frame(s, "", 12, 6, tip_shadow, top=10, bottom=14)
        save_svgz(s, os.path.join(base, sub + "widgets/tooltip.svgz"))

    # --- widgets/panel-background (barra de tarefas) -------------------------
    for sub, op in (("", 0.95), ("translucent/", 0.80), ("opaque/", 1.0)):
        s = SvgSheet()
        m = 3
        hints = {"hint-top-margin": (1, m), "hint-bottom-margin": (1, m),
                 "hint-left-margin": (m, 1), "hint-right-margin": (m, 1)}
        # sem prefixo: painel flutuante (todo arredondado)
        rounded_box_frame(s, "", 0 if sub == "opaque/" else 8, op, 0.12, hints=hints,
                          mask=(sub != "opaque/"))
        # painel encostado na borda: plano, só a linha de separação
        for loc, sides in (("south", (1, 0, 0, 0)), ("north", (0, 0, 1, 0)),
                           ("west", (0, 1, 0, 0)), ("east", (0, 0, 0, 1))):
            rounded_box_frame(s, loc, 0, op, 0.10, sides=sides, hints=hints,
                              mask=(sub != "opaque/"))
        save_svgz(s, os.path.join(base, sub + "widgets/panel-background.svgz"))

    # --- widgets/tasks (botões da barra de tarefas) ------------------------
    s = SvgSheet()
    task_hints = {"hint-top-margin": (1, 4), "hint-bottom-margin": (1, 4),
                  "hint-left-margin": (4, 1), "hint-right-margin": (4, 1)}

    def task_frame(prefix, loc, fill_op, pill_k, pill_paint, fill_cls=TX, r=5):
        # moldura lógica: cantos k x k
        k = max(pill_k, r + 1)
        W = H = 2 * k + 1
        layers = []
        if fill_op > 0:
            layers.append((rrect(0, 0, W, H, r), Paint(cls=fill_cls, opacity=fill_op)))
        if pill_paint is not None:
            a, b = k - 3, W - (k - 3)   # extensão ao longo da borda
            t0, t1 = 1.0, 4.0          # 3px de espessura, 1px da borda
            if loc == "south":
                g = pill(a, H - t1, b, H - t0)
            elif loc == "north":
                g = pill(a, t0, b, t1)
            elif loc == "west":
                g = pill(t0, a, t1, b)
            else:
                g = pill(W - t1, a, W - t0, b)
            layers.append((g, pill_paint))
        cols = [(0, k), (k, k + 1), (k + 1, W)]
        pre = prefix if loc == "south" else f"{loc}-{prefix}"
        s.frame(pre, cols, cols, layers, hints=task_hints)
        if loc == "south":
            # variante explícita com prefixo de localização
            s.frame(f"south-{prefix}", cols, cols, layers, hints=task_hints)

    gray = Paint(cls=TX, opacity=0.45)
    accent = Paint(cls=HL)
    for loc in ("south", "north", "west", "east"):
        task_frame("normal", loc, 0.0, 22, gray)
        task_frame("minimized", loc, 0.0, 22, gray)
        task_frame("focus", loc, 0.075, 15, accent)
        task_frame("hover", loc, 0.055, 6, None)
        task_frame("attention", loc, 0.22, 15, Paint(cls=NE), fill_cls=NE)
        task_frame("progress", loc, 0.30, 6, None, fill_cls=HL)
    save_svgz(s, os.path.join(base, "widgets/tasks.svgz"))

    # --- widgets/viewitem (itens de listas: Kickoff, bandeja, etc.) ------------
    s = SvgSheet()
    vi_hints = {"hint-top-margin": (1, 4), "hint-bottom-margin": (1, 4),
                "hint-left-margin": (6, 1), "hint-right-margin": (6, 1)}
    for prefix, op in (("normal", 0.0), ("hover", 0.06), ("selected", 0.09),
                       ("selected+hover", 0.12)):
        rounded_box_frame(s, prefix, 5, op, 0.0, fill_cls=TX, hints=vi_hints, mask=False)
    save_svgz(s, os.path.join(base, "widgets/viewitem.svgz"))

    # --- widgets/plasmoidheading (cabeçalho/rodapé de popups) -----------------
    s = SvgSheet()
    for prefix, sides, bop in (("header", (0, 0, 0, 0), 0.0),
                               ("footer", (1, 0, 0, 0), 0.08)):
        rounded_box_frame(s, prefix, 0, 0.0, bop, sides=sides, mask=False,
                          hints={"hint-top-margin": (1, 6), "hint-bottom-margin": (1, 6),
                                 "hint-left-margin": (6, 1), "hint-right-margin": (6, 1)})
    save_svgz(s, os.path.join(base, "widgets/plasmoidheading.svgz"))

    # --- metadados ------------------------------------------------------------
    meta = {
        "KPackageStructure": "Plasma/Theme",
        "KPlugin": {
            "Authors": [AUTHOR],
            "Copyright": COPYRIGHT,
            "Category": "",
            "Description": "Plasma style inspired by Fluent Design (Windows 11)",
            "EnabledByDefault": True,
            "Id": "Onze",
            "License": "GPL-3.0-or-later",
            "Name": "Onze",
            "Version": VERSION,
        },
        "X-Plasma-API": "5.0",
    }
    write(os.path.join(base, "metadata.json"), json.dumps(meta, indent=4, ensure_ascii=False) + "\n")
    write(os.path.join(base, "metadata.desktop"), "\n".join([
        "[Desktop Entry]", "Name=Onze",
        "Comment=Plasma style inspired by Fluent Design (Windows 11)",
        f"X-KDE-PluginInfo-Author={AUTHOR['Name']}", f"X-KDE-PluginInfo-Email={AUTHOR['Email']}",
        "X-KDE-PluginInfo-Name=Onze", f"X-KDE-PluginInfo-Version={VERSION}", "X-KDE-PluginInfo-License=GPL-3.0-or-later",
        "X-KDE-PluginInfo-EnabledByDefault=true", "X-Plasma-API=5.0", "",
        "[ContrastEffect]", "enabled=true", "contrast=0.25", "intensity=1.6",
        "saturation=1.9", "", "[AdaptiveTransparency]", "enabled=true", "",
    ]))
    write(os.path.join(base, "plasmarc"), "\n".join([
        "[ContrastEffect]", "enabled=true", "contrast=0.25", "intensity=1.6",
        "saturation=1.9", "", "[AdaptiveTransparency]", "enabled=true", "",
    ]))


# ---------------------------------------------------------------------------
# 5. Decoração de janelas (Aurorae)
# ---------------------------------------------------------------------------
AUR = dict(PL=26, PR=26, PT=20, PB=32, R=8, TITLE=32, BW=46, BH=31, FRAME=4)


def aurorae(variant):
    claro = variant == "Claro"
    label = "Light" if claro else "Dark"
    name = f"Onze-{variant}"
    base = os.path.join(SRC, "aurorae", name)
    if os.path.isdir(base):
        shutil.rmtree(base)
    P = AUR
    bg = LIGHT["window"] if claro else DARK["window"]
    if claro:
        border_a, border_i = ("#000000", 0.16), ("#000000", 0.11)
        sh_a = [(1.5, 1, 0.12), (10, 6, 0.30)]
        sh_i = [(1.5, 1, 0.10), (6, 3, 0.18)]
    else:
        border_a, border_i = ("#FFFFFF", 0.13), ("#FFFFFF", 0.09)
        sh_a = [(1.5, 1, 0.35), (10, 6, 0.55)]
        sh_i = [(1.5, 1, 0.30), (6, 3, 0.38)]

    ww, wh = 420, 300
    W, H = ww + P["PL"] + P["PR"], wh + P["PT"] + P["PB"]
    x0, y0 = P["PL"], P["PT"]
    x1, y1 = x0 + ww, y0 + wh
    R = P["R"]
    # all four corners rounded: the 4 px frame (BorderLeft/Right/Bottom) is wide enough for the
    # square corners of the window contents to sit inside the 8 px curve
    corners = (1, 1, 1, 1)
    outer = rrect(x0, y0, x1, y1, R, corners)
    inner = rrect(x0 + 1, y0 + 1, x1 - 1, y1 - 1, R - 1, corners)
    border = outer.difference(inner)
    cols = [(0, x0 + R), (W // 2, W // 2 + 1), (x1 - R, W)]
    rows = [(0, y0 + P["TITLE"]), (y0 + 200, y0 + 201), (y1 - R, H)]

    s = SvgSheet()
    for prefix, bd, sh in (("decoration", border_a, sh_a),
                           ("decoration-inactive", border_i, sh_i)):
        img = shadow_image(W, H, (x0, y0, x1, y1), outer, sh)
        layers = [(inner, Paint(color=bg)),
                  (border, Paint(color=bd[0], opacity=bd[1]))]
        s.frame(prefix, cols, rows, layers, image=img)
    # maximizada: plana, sem borda e sem sombra
    mc = [(0, 1), (1, 2), (2, 3)]
    mr = [(0, P["TITLE"] - 1), (P["TITLE"] - 1, P["TITLE"]), (P["TITLE"], P["TITLE"] + 1)]
    full = box(0, 0, 3, P["TITLE"] + 1)
    for prefix in ("decoration-maximized", "decoration-maximized-inactive"):
        s.frame(prefix, mc, mr, [(full, Paint(color=bg))])
    write(os.path.join(base, "decoration.svg"), s.svg(scheme=False))

    # --- botões ----------------------------------------------------------------
    fg = LIGHT["text"] if claro else DARK["text"]
    fg_in = "#9A9A9A" if claro else "#7A7A7A"
    hov = ("#000000", 0.045) if claro else ("#FFFFFF", 0.065)
    prs = ("#000000", 0.025) if claro else ("#FFFFFF", 0.04)
    BW, BH = P["BW"], P["BH"]
    cx, cy = BW / 2, 15.0

    def glyph(kind):
        if kind == "minimize":
            return box(cx - 5, cy + 0.5, cx + 5, cy + 1.5)
        if kind == "maximize":
            return ring(cx - 5, cy - 5, cx + 5, cy + 5, 1.5)
        if kind == "restore":
            front = ring(cx - 5, cy - 3, cx + 3, cy + 5, 1.5)
            back = ring(cx - 3, cy - 5, cx + 5, cy + 3, 1.5).difference(
                rrect(cx - 5.6, cy - 3.6, cx + 3.6, cy + 5.6, 2))
            return unary_union([front, back])
        if kind == "close":
            l1 = LineString([(cx - 5, cy - 5), (cx + 5, cy + 5)]).buffer(0.55, cap_style=2)
            l2 = LineString([(cx + 5, cy - 5), (cx - 5, cy + 5)]).buffer(0.55, cap_style=2)
            return unary_union([l1, l2]).intersection(box(cx - 5, cy - 5, cx + 5, cy + 5))
        if kind == "alldesktops":
            return unary_union([ring(cx - 5, cy - 5, cx + 5, cy + 5, 5),
                                rrect(cx - 2, cy - 2, cx + 2, cy + 2, 2)])
        if kind == "keepabove":
            return unary_union([box(cx - 5, cy - 5, cx + 5, cy - 4),
                                Polygon([(cx, cy - 2), (cx + 4, cy + 3), (cx - 4, cy + 3)])])
        if kind == "keepbelow":
            return unary_union([box(cx - 5, cy + 4, cx + 5, cy + 5),
                                Polygon([(cx, cy + 2), (cx + 4, cy - 3), (cx - 4, cy - 3)])])
        raise ValueError(kind)

    def button(kind):
        is_close = kind == "close"
        g = glyph(kind)
        bgshape = rrect(0, 0, BW, BH, R - 1, (0, 1, 0, 0)) if is_close else box(0, 0, BW, BH)
        states = {
            "active": (None, (fg, 1.0)),
            "inactive": (None, (fg_in, 1.0)),
            "hover": (("#C42B1C", 1.0) if is_close else hov,
                      ("#FFFFFF", 1.0) if is_close else (fg, 1.0)),
            "pressed": (("#C83C31", 0.9) if is_close else prs,
                        ("#FFFFFF", 0.75) if is_close else (fg, 0.65)),
            "deactivated": (None, (fg, 0.35)),
        }
        parts = []
        oy = 0
        for st, (bgc, gc) in states.items():
            el = [f'<g id="{st}-center">',
                  f'<rect x="0" y="{oy}" width="{BW}" height="{BH}" style="fill:none;stroke:none"/>']
            if bgc:
                el.append(f'<path {Paint(color=bgc[0], opacity=bgc[1]).attrs()} d="{to_d(bgshape, 0, oy)}"/>')
            el.append(f'<path {Paint(color=gc[0], opacity=gc[1]).attrs()} fill-rule="evenodd" d="{to_d(g, 0, oy)}"/>')
            el.append("</g>")
            parts.append("".join(el))
            oy += BH + 6
        svg = ('<?xml version="1.0" encoding="UTF-8"?>\n'
               f'<svg xmlns="http://www.w3.org/2000/svg" version="1.1" width="{BW}" '
               f'height="{oy}" viewBox="0 0 {BW} {oy}">' + "\n".join(parts) + "</svg>\n")
        write(os.path.join(base, f"{kind}.svg"), svg)

    for k in ("close", "minimize", "maximize", "restore", "alldesktops",
              "keepabove", "keepbelow"):
        button(k)

    rc = [
        "[General]",
        f"ActiveTextColor={rgbs(fg)}",
        f"InactiveTextColor={rgbs(fg_in)}",
        "TitleAlignment=Left", "TitleVerticalAlignment=Center",
        "Animation=120", "Shadow=true", "UseTextShadow=false", "",
        "[Layout]",
        f"BorderLeft={P['FRAME']}", f"BorderRight={P['FRAME']}", f"BorderBottom={P['FRAME']}",
        "TitleEdgeTop=1", "TitleEdgeBottom=0", "TitleEdgeLeft=1", "TitleEdgeRight=1",
        "TitleEdgeTopMaximized=0", "TitleEdgeBottomMaximized=0",
        "TitleEdgeLeftMaximized=0", "TitleEdgeRightMaximized=0",
        "TitleBorderLeft=11", "TitleBorderRight=8",
        f"TitleHeight={P['TITLE'] - 1}",
        f"ButtonWidth={BW}", f"ButtonHeight={BH}",
        "ButtonSpacing=0", "ButtonMarginTop=0", "ExplicitButtonSpacer=8",
        f"PaddingLeft={P['PL']}", f"PaddingRight={P['PR']}",
        f"PaddingTop={P['PT']}", f"PaddingBottom={P['PB']}", "",
    ]
    write(os.path.join(base, f"{name}rc"), "\n".join(rc))
    write(os.path.join(base, "metadata.desktop"), "\n".join([
        "[Desktop Entry]", f"Name=Onze {label}",
        f"Comment=Windows 11 style window decoration ({label.lower()})",
        f"X-KDE-PluginInfo-Author={AUTHOR['Name']}", f"X-KDE-PluginInfo-Email={AUTHOR['Email']}",
        f"X-KDE-PluginInfo-Name={name}", f"X-KDE-PluginInfo-Version={VERSION}", "X-KDE-PluginInfo-License=GPL-3.0-or-later",
        "X-KDE-PluginInfo-EnabledByDefault=true", "",
    ]))
    write(os.path.join(base, "metadata.json"), json.dumps({
        "KPlugin": {"Authors": [AUTHOR], "Copyright": COPYRIGHT,
                    "Description": f"Windows 11 style window decoration ({label.lower()})",
                    "Id": name, "License": "GPL-3.0-or-later",
                    "Name": f"Onze {label}", "Version": VERSION},
        "KPackageStructure": "KWin/Decoration",
    }, indent=4, ensure_ascii=False) + "\n")


# ---------------------------------------------------------------------------
# 6. Papel de parede original (faixas fluidas)
# ---------------------------------------------------------------------------
def wallpaper(dark, W=3840, H=2160):
    """Folhas finas empilhadas em onda, com luz de dobra e sombras suaves.
    Arte original; azul propositalmente pouco saturado."""
    def hx(h):
        h = h.lstrip("#")
        return np.array([int(h[i:i + 2], 16) for i in (0, 2, 4)], np.float32)

    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    u, v = xx / W, yy / H
    if dark:
        bg0, bg1 = hx("#1B2940"), hx("#0A111C")
        c_dark, c_mid, c_light = hx("#0F2344"), hx("#2A5799"), hx("#80AAE0")
    else:
        bg0, bg1 = hx("#DCE5EF"), hx("#9FB4CC")
        c_dark, c_mid, c_light = hx("#234F92"), hx("#3772C4"), hx("#A6C7EF")
    r = np.sqrt((u - 0.42) ** 2 + ((v - 0.30) / 0.8) ** 2)
    t = np.clip(r / 0.9, 0, 1)[..., None]
    img = bg0 * (1 - t) + bg1 * t

    N = 22
    x = np.arange(W, dtype=np.float32) / W
    light = np.array([-0.55, -0.83])
    for k in range(N):
        t = k / (N - 1)
        hump = ((0.70 - 0.36 * t) * np.exp(-((x - (0.66 - 0.10 * t + 0.025 * np.sin(k * 1.7))) / (0.20 + 0.05 * t)) ** 2)
                + (0.30 - 0.12 * t) * np.exp(-((x - (0.30 + 0.12 * t)) / (0.13 + 0.04 * t)) ** 2)
                + 0.035 * np.sin(2 * np.pi * (x * 1.25 + k * 0.29)) * (0.4 + 0.6 * np.exp(-((x - 0.55) / 0.35) ** 2))
                + 0.010 * np.sin(2 * np.pi * (x * 3.1 + k * 0.53)))
        yk = H * (1.04 - hump)                       # borda superior da folha
        dy = np.gradient(yk) * 1.1                     # inclinação (independe da resolução)
        nn = np.sqrt(dy ** 2 + 1)
        lam = 0.5 + 0.5 * ((dy / nn) * light[0] + (-1 / nn) * light[1])
        d = yy - yk[None, :]
        inside = np.clip(d + 0.5, 0, 1)
        # sombra da folha sobre o que está atrás dela
        sh = np.where(d < 0, np.exp(d / (0.012 * H)), 0) * (0.10 if k == 0 else 0.40)
        img = img * (1 - sh[..., None])
        depth = 0.35 + 0.65 * t
        base = c_dark * (1 - depth) + c_mid * depth
        col = base[None, None, :] + (c_light - base)[None, None, :] * (0.85 * lam[None, :, None] ** 1.3)
        dd = np.clip(d, 0, None)
        fall = np.exp(-dd / (0.06 * H))[..., None]
        glow = np.exp(-dd / (0.025 * H))[..., None]
        col = col * (0.70 + 0.30 * fall) + (c_light - col) * glow * 0.35
        rim = np.exp(-dd / (0.0018 * H))[..., None] * 0.35
        col = col + (255 - col) * rim * (0.6 if dark else 1.0)
        img = img * (1 - inside[..., None]) + col * inside[..., None]

    noise = np.random.default_rng(3).normal(0, 1.2, (H, W)).astype(np.float32)[..., None]
    return Image.fromarray(np.clip(img + noise, 0, 255).astype(np.uint8), "RGB")


def wallpapers():
    base = os.path.join(SRC, "wallpapers", "Onze")
    os.makedirs(os.path.join(base, "contents", "images"), exist_ok=True)
    os.makedirs(os.path.join(base, "contents", "images_dark"), exist_ok=True)
    for dark, sub in ((False, "images"), (True, "images_dark")):
        im = wallpaper(dark)
        im.save(os.path.join(base, "contents", sub, "3840x2160.jpg"), quality=92, optimize=True)
        im.resize((1920, 1080), Image.LANCZOS).save(
            os.path.join(base, "contents", sub, "1920x1080.jpg"), quality=92, optimize=True)
        im.resize((400, 225), Image.LANCZOS).save(
            os.path.join(base, "contents", "screenshot.png" if not dark else "screenshot_dark.png"))
    write(os.path.join(base, "metadata.json"), json.dumps({
        "KPlugin": {"Authors": [AUTHOR], "Copyright": COPYRIGHT, "Id": "Onze",
                    "License": "CC-BY-SA-4.0", "Name": "Onze"},
        "KPackageStructure": "Wallpaper/Images",
    }, indent=4, ensure_ascii=False) + "\n")


# ---------------------------------------------------------------------------
# 7. Pré-visualizações dos temas globais
# ---------------------------------------------------------------------------
def font(size, bold=False):
    for f in ("/usr/share/fonts/opentype/inter/Inter-SemiBold.otf" if bold else
              "/usr/share/fonts/opentype/inter/Inter-Regular.otf",
              "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"):
        if os.path.exists(f):
            return ImageFont.truetype(f, size)
    return ImageFont.load_default()


def preview(dark):
    p = DARK if dark else LIGHT
    wp_path = os.path.join(SRC, "wallpapers", "Onze", "contents",
                           "images_dark" if dark else "images", "1920x1080.jpg")
    img = Image.open(wp_path).convert("RGBA")
    W, H = img.size
    ov = Image.new("RGBA", img.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(ov)

    def shadowed(rect, radius, fill, outline):
        sh = Image.new("RGBA", img.size, (0, 0, 0, 0))
        ImageDraw.Draw(sh).rounded_rectangle((rect[0], rect[1] + 8, rect[2], rect[3] + 8), radius,
                                             fill=(0, 0, 0, 110 if dark else 70))
        sh = sh.filter(ImageFilter.GaussianBlur(18))
        ov.alpha_composite(sh)
        d.rounded_rectangle(rect, radius, fill=fill, outline=outline, width=1)

    # janela
    win = (300, 150, 1250, 760)
    shadowed(win, 8, rgb(p["window"]) + (255,), (255, 255, 255, 30) if dark else (0, 0, 0, 40))
    d.rectangle((301, 182, 1249, 759), fill=rgb(p["view"]) + (255,))
    d.text((314, 158), "Documentos — Dolphin", font=font(15), fill=rgb(p["text"]))
    gx = 1249
    for kind in ("x", "max", "min"):
        cx = gx - 23
        c = rgb(p["text"])
        if kind == "x":
            d.line((cx - 5, 160, cx + 5, 170), fill=c, width=1)
            d.line((cx + 5, 160, cx - 5, 170), fill=c, width=1)
        elif kind == "max":
            d.rounded_rectangle((cx - 5, 160, cx + 5, 170), 2, outline=c, width=1)
        else:
            d.line((cx - 5, 166, cx + 5, 166), fill=c, width=1)
        gx -= 46
    # barra lateral + itens
    d.rectangle((301, 182, 520, 759), fill=rgb(p["window"]) + (255,))
    for i, t in enumerate(["Início", "Área de trabalho", "Documentos", "Downloads", "Imagens", "Música"]):
        y = 200 + i * 40
        if i == 2:
            d.rounded_rectangle((310, y - 6, 510, y + 26), 5, fill=(255, 255, 255, 18) if dark else (0, 0, 0, 12))
            d.rounded_rectangle((311, y + 3, 314, y + 17), 2, fill=rgb(p["accent"]))
        d.text((330, y), t, font=font(15), fill=rgb(p["text"]))
    for i in range(12):
        x = 560 + (i % 6) * 112
        y = 210 + (i // 6) * 130
        d.rounded_rectangle((x, y, x + 72, y + 58), 6, fill=rgb(p["accent"]) + (200,))
        d.text((x, y + 70), f"Pasta {i + 1}", font=font(13), fill=rgb(p["text"]))

    # menu iniciar
    sm = (W // 2 - 320, H - 48 - 12 - 660, W // 2 + 320, H - 48 - 12)
    shadowed(sm, 8, rgb(p["window"]) + (238,), (255, 255, 255, 30) if dark else (0, 0, 0, 40))
    d.rounded_rectangle((sm[0] + 30, sm[1] + 28, sm[2] - 30, sm[1] + 64), 18,
                        fill=rgb(p["view"]) + (255,), outline=rgb(p["accent"]), width=1)
    d.text((sm[0] + 60, sm[1] + 36), "Pesquisar aplicativos, configurações e documentos",
           font=font(14), fill=rgb(p["inactive"]))
    d.text((sm[0] + 40, sm[1] + 90), "Fixados", font=font(16, True), fill=rgb(p["text"]))
    cols = ["#2F7DE1", "#E8A33A", "#3BA55C", "#C04CC8", "#E05A47", "#2CB5C0"]
    for i in range(18):
        x = sm[0] + 50 + (i % 6) * 92
        y = sm[1] + 130 + (i // 6) * 92
        d.rounded_rectangle((x + 14, y, x + 50, y + 36), 8, fill=rgb(cols[i % 6]))
        d.text((x + 6, y + 46), "Aplicativo", font=font(12), fill=rgb(p["text"]))
    d.line((sm[0] + 1, sm[3] - 64, sm[2] - 1, sm[3] - 64), fill=(255, 255, 255, 25) if dark else (0, 0, 0, 20))
    d.ellipse((sm[0] + 40, sm[3] - 46, sm[0] + 68, sm[3] - 18), fill=rgb(p["accent"]))
    d.text((sm[0] + 80, sm[3] - 40), "Usuário", font=font(14), fill=rgb(p["text"]))
    d.ellipse((sm[2] - 60, sm[3] - 42, sm[2] - 40, sm[3] - 22), outline=rgb(p["text"]), width=2)

    # barra de tarefas
    tb_h = 48
    d.rectangle((0, H - tb_h, W, H), fill=rgb(p["window"]) + (225,))
    d.line((0, H - tb_h, W, H - tb_h), fill=(255, 255, 255, 25) if dark else (0, 0, 0, 25))
    items = ["start", "search", "taskview", "app", "app", "focus", "app", "app"]
    widths = {"start": 44, "search": 220, "taskview": 44, "app": 44, "focus": 44}
    x = W // 2 - sum(widths[i] for i in items) // 2
    ci = 0
    for it in items:
        if it == "search":
            d.rounded_rectangle((x + 4, H - 40, x + 214, H - 8), 16,
                                fill=rgb(p["view"]) + (255,),
                                outline=(255, 255, 255, 30) if dark else (0, 0, 0, 25))
            d.ellipse((x + 18, H - 31, x + 30, H - 19), outline=rgb(p["text"]), width=2)
            d.text((x + 40, H - 34), "Pesquisar", font=font(14), fill=rgb(p["inactive"]))
        elif it == "start":
            d.ellipse((x + 11, H - 35, x + 33, H - 13), outline=rgb(p["accent"]), width=4)
            d.ellipse((x + 18, H - 28, x + 26, H - 20), fill=rgb(p["accent"]))
        elif it == "taskview":
            d.rounded_rectangle((x + 12, H - 34, x + 32, H - 16), 3, outline=rgb(p["text"]), width=2)
        else:
            if it == "focus":
                d.rounded_rectangle((x + 2, H - 44, x + 42, H - 4), 5,
                                    fill=(255, 255, 255, 20) if dark else (0, 0, 0, 14))
                d.rounded_rectangle((x + 14, H - 7, x + 30, H - 4), 2, fill=rgb(p["accent"]))
            else:
                d.rounded_rectangle((x + 19, H - 7, x + 25, H - 4), 2, fill=(150, 150, 150, 255))
            d.rounded_rectangle((x + 10, H - 36, x + 34, H - 12), 6, fill=rgb(cols[ci % 6]))
            ci += 1
        x += widths[it]
    d.text((W - 110, H - 42), "14:32", font=font(13), fill=rgb(p["text"]))
    d.text((W - 120, H - 24), "24/10/2026", font=font(13), fill=rgb(p["text"]))

    img.alpha_composite(ov)
    return img.convert("RGB")


def splash_preview(dark=True):
    W, H = 1920, 1080
    img = Image.new("RGB", (W, H), rgb("#101010"))
    d = ImageDraw.Draw(img)
    cx, cy = W // 2, H // 2 - 60
    d.ellipse((cx - 64, cy - 64, cx + 64, cy + 64), outline=rgb("#4CC2FF"), width=14)
    d.ellipse((cx - 22, cy - 22, cx + 22, cy + 22), fill=rgb("#4CC2FF"))
    for i in range(5):
        a = math.radians(-90 + i * 26)
        x, y = cx + 34 * math.cos(a), cy + 260 + 34 * math.sin(a)
        d.ellipse((x - 3, y - 3, x + 3, y + 3), fill=(255, 255, 255))
    return img


def previews():
    for ident, dark in (("org.kde.onze.claro.desktop", False), ("org.kde.onze.escuro.desktop", True)):
        base = os.path.join(SRC, "look-and-feel", ident, "contents", "previews")
        os.makedirs(base, exist_ok=True)
        full = preview(dark)
        full.save(os.path.join(base, "fullscreenpreview.jpg"), quality=88)
        full.resize((512, 288), Image.LANCZOS).save(os.path.join(base, "preview.png"))
        splash_preview(dark).resize((512, 288), Image.LANCZOS).save(os.path.join(base, "splash.png"))


# ---------------------------------------------------------------------------
def main():
    color_scheme(LIGHT, "Onze Light", "OnzeClaro", False)
    color_scheme(DARK, "Onze Dark", "OnzeEscuro", True)
    desktoptheme()
    aurorae("Claro")
    aurorae("Escuro")
    # The wallpaper comes from tools/wallpaper/source.png (see tools/prepare_wallpaper.py).
    # The old procedural wallpaper is only generated on request.
    if "--procedural-wallpaper" in sys.argv:
        wallpapers()
    previews()
    print("Recursos gerados em", SRC)


if __name__ == "__main__":
    main()
