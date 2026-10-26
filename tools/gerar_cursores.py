#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Gera o tema de cursores "Onze" (formato Xcursor) em ../src/cursors/Onze-cursors.

Seta branca com contorno preto fino e sombra discreta, no estilo do Windows 11.
Não precisa de xcursorgen: os arquivos Xcursor são escritos diretamente.

Requisitos: pip install numpy pillow shapely scipy
Uso:        python3 tools/gerar_cursores.py
"""
import math
import os
import shutil
import struct

import numpy as np
from PIL import Image, ImageDraw, ImageFont
from scipy.ndimage import gaussian_filter
from shapely import affinity
from shapely.geometry import LineString, Point, Polygon, box
from shapely.ops import unary_union

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "src", "cursors", "Onze-cursors")

SIZES = [24, 30, 36, 48, 72, 96]
U = 32.0            # unidades de desenho (grade 32 x 32)
SS = 8              # superamostragem
SCALE = 0.85        # scale of the drawing inside the canvas (1.0 = original size)
OUTLINE = 4 / 3 / SCALE   # outline thickness in units (= 1 px at size 24 after scaling)
PIVOT = (0.0, 0.0)  # point kept fixed when scaling (set per cursor in main())


def tx(x, y):
    """Applies SCALE around PIVOT (design units)."""
    return PIVOT[0] + (x - PIVOT[0]) * SCALE, PIVOT[1] + (y - PIVOT[1]) * SCALE
ACCENT = (0, 103, 192)


def rrect(x0, y0, x1, y1, r):
    return box(x0 + r, y0 + r, x1 - r, y1 - r).buffer(r, quad_segs=16) if r > 0 else box(x0, y0, x1, y1)


# ---------------------------------------------------------------------------
# Formas (coordenadas na grade 32 x 32, y para baixo)
# ---------------------------------------------------------------------------
# alinhada à grade de pixels no tamanho 24 (borda esquerda nítida)
ARROW = affinity.translate(Polygon([(2, 2), (2, 22.6), (6.9, 17.9), (10.2, 25.2), (13.2, 23.9),
                                    (10.0, 16.7), (16.6, 16.7)]), -2 / 3, -2 / 3)


def hand():
    index = rrect(10.2, 3, 14.2, 19, 2.0)
    middle = rrect(14.2, 11.2, 18.2, 19.5, 2.0)
    ring = rrect(18.2, 12.2, 22.0, 20, 1.9)
    little = rrect(22.0, 13.8, 25.4, 21, 1.7)
    palm = Polygon([(10.2, 16), (25.4, 17), (25.0, 24), (22.5, 28.6), (12.4, 28.6),
                    (8.0, 23.8)]).buffer(0.8, join_style=1)
    thumb = LineString([(10.6, 22.4), (5.6, 16.6)]).buffer(1.9, quad_segs=12)
    return unary_union([index, middle, ring, little, palm, thumb])


def finger_lines():
    w = 0.5
    return unary_union([
        box(14.2 - w / 2, 12.6, 14.2 + w / 2, 18.4),
        box(18.2 - w / 2, 13.6, 18.2 + w / 2, 18.8),
        box(22.0 - w / 2, 15.0, 22.0 + w / 2, 19.4),
    ])


def double_arrow(length=26.0, head=6.5, half_w=5.6, shaft=1.5):
    """Seta dupla vertical centrada em (16,16)."""
    c, h = 16.0, length / 2
    up = Polygon([(c, c - h), (c + half_w, c - h + head), (c - half_w, c - h + head)])
    down = Polygon([(c, c + h), (c + half_w, c + h - head), (c - half_w, c + h - head)])
    s = box(c - shaft, c - h + head - 0.5, c + shaft, c + h - head + 0.5)
    return unary_union([up, down, s])


def four_way():
    v = double_arrow(29, 5.2, 4.4, 1.1)
    return unary_union([v, affinity.rotate(v, 90, origin=(16, 16))])


def ibeam():
    stem = box(15.33 - 0.67, 6.5, 15.33 + 0.67, 25.5)
    tops = unary_union([
        LineString([(11.9, 5.2), (13.9, 5.2), (15.33, 6.6), (16.8, 5.2), (18.8, 5.2)]),
        LineString([(11.9, 26.8), (13.9, 26.8), (15.33, 25.4), (16.8, 26.8), (18.8, 26.8)]),
    ]).buffer(0.55, cap_style=2, join_style=2)
    return unary_union([stem, tops])


def crosshair():
    return unary_union([box(14.67, 4, 16.0, 28), box(4, 14.67, 28, 16.0)])


def not_allowed():
    ring = Point(16, 16).buffer(9.5, quad_segs=24).difference(Point(16, 16).buffer(7.0, quad_segs=24))
    bar = affinity.rotate(box(8.2, 14.75, 23.8, 17.25), -45, origin=(16, 16))
    return unary_union([ring, bar.intersection(Point(16, 16).buffer(8.0))])


# ---------------------------------------------------------------------------
# Renderização
# ---------------------------------------------------------------------------
def poly_mask(geom, size, scale):
    """Rasteriza geometria (unidades) num canvas de size*SS pixels."""
    W = size * SS
    img = Image.new("L", (W, W), 0)
    d = ImageDraw.Draw(img)
    k = scale * SS
    geoms = [geom] if geom.geom_type == "Polygon" else list(getattr(geom, "geoms", []))
    for g in geoms:
        if g.is_empty or g.geom_type != "Polygon":
            continue
        d.polygon([tuple(c * k for c in tx(x, y)) for x, y in g.exterior.coords], fill=255)
        for hole in g.interiors:
            d.polygon([tuple(c * k for c in tx(x, y)) for x, y in hole.coords], fill=0)
    return np.asarray(img, dtype=np.float32) / 255.0


def down(a, size):
    """Reduz de size*SS para size com média por blocos (antialias exato)."""
    return a.reshape(size, SS, size, SS, *a.shape[2:]).mean(axis=(1, 3))


def compose(size, layers, shadow=True):
    """layers: [(geom, (r,g,b), alpha)] desenhadas de baixo para cima.
    Retorna array RGBA float (0..1) size x size."""
    scale = size / U
    rgb = np.zeros((size * SS, size * SS, 3), np.float32)
    a = np.zeros((size * SS, size * SS), np.float32)
    for geom, color, alpha in layers:
        m = poly_mask(geom, size, scale) * alpha
        col = np.array(color, np.float32) / 255.0
        rgb = rgb * (1 - m[..., None]) + col * m[..., None]
        a = a + m * (1 - a)
    rgb_s, a_s = down(rgb * a[..., None], size), down(a, size)
    if shadow:
        sh = gaussian_filter(a_s, sigma=max(0.8, size / 26))
        off = max(1, round(size / 40))
        sh = np.roll(sh, off, axis=0) * 0.30
        out_a = a_s + sh * (1 - a_s)
        out_rgb = rgb_s  # sombra é preta: só soma alfa
    else:
        out_a, out_rgb = a_s, rgb_s
    return out_rgb, out_a  # rgb já pré-multiplicado


def outlined(shape, fill=(255, 255, 255), line=(0, 0, 0), t=OUTLINE, extra=()):
    return [(shape.buffer(t, join_style=2, mitre_limit=3.0), line, 1.0),
            (shape, fill, 1.0), *extra]


def spinner_layers(cx, cy, r, w, angle, track=True):
    ring = Point(cx, cy).buffer(r + w / 2, quad_segs=32).difference(Point(cx, cy).buffer(r - w / 2, quad_segs=32))
    a0 = math.radians(angle)
    pts = [(cx, cy)] + [(cx + 2 * r * math.cos(a0 + math.radians(i)), cy + 2 * r * math.sin(a0 + math.radians(i)))
                        for i in range(0, 111, 5)]
    arc = ring.intersection(Polygon(pts))
    lay = [(ring.buffer(0.9), (0, 0, 0), 0.55)] if track else []
    lay += [(ring, (235, 235, 235), 1.0), (arc, ACCENT, 1.0)]
    return lay


def text_layer(size, txt, cx, cy, px):
    """'?' desenhado com fonte e convertido em máscara já reduzida."""
    scale = size / U
    W = size * SS
    img = Image.new("L", (W, W), 0)
    d = ImageDraw.Draw(img)
    fpath = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
    f = ImageFont.truetype(fpath, int(px * SCALE * scale * SS))
    cx, cy = tx(cx, cy)
    d.text((cx * scale * SS, cy * scale * SS), txt, font=f, fill=255, anchor="mm")
    return np.asarray(img, dtype=np.float32) / 255.0


# ---------------------------------------------------------------------------
# Definição de cada cursor: (função que devolve frames, hotspot em unidades)
# ---------------------------------------------------------------------------
def frames_static(builder):
    def f(size):
        return [(compose(size, builder(size)), 0)]
    return f


def help_frames(size):
    rgb, a = compose(size, outlined(ARROW))
    # bolha com "?" no canto inferior direito
    scale = size / U
    bub = Point(23.5, 24.5).buffer(6.2, quad_segs=24)
    rgb2, a2 = compose(size, [(bub.buffer(OUTLINE), (0, 0, 0), 1.0), (bub, (255, 255, 255), 1.0)], shadow=False)
    q = down(text_layer(size, "?", 23.5, 24.8, 10), size)
    rgb2 = rgb2 * (1 - q[..., None])  # "?" preto
    rgb = rgb * (1 - a2[..., None]) + rgb2
    a = a + a2 * (1 - a)
    return [((rgb, a), 0)]


def progress_frames(size):
    out = []
    for i in range(18):
        lay = outlined(ARROW) + spinner_layers(22.5, 23.5, 4.6, 2.4, i * 20)
        out.append((compose(size, lay), 45))
    return out


def wait_frames(size):
    out = []
    for i in range(24):
        out.append((compose(size, spinner_layers(16, 16, 9.0, 3.2, i * 15)), 40))
    return out


# point kept fixed when scaling each cursor (the tip of arrows, the center of the rest)
PIVOTS = {"default": (4 / 3, 4 / 3), "help": (4 / 3, 4 / 3), "progress": (4 / 3, 4 / 3),
          "pointer": (12.2, 3), "text": (15.33, 15.33), "vertical-text": (15.33, 15.33),
          "crosshair": (15.33, 15.33)}

CURSORS = {
    "default": (frames_static(lambda s: outlined(ARROW)), (1.33, 1.33)),
    "pointer": (frames_static(lambda s: outlined(hand(), extra=[(finger_lines(), (0, 0, 0), 0.85)])), (12.2, 3)),
    "text": (frames_static(lambda s: [(ibeam().buffer(0.8, join_style=2), (255, 255, 255), 1.0),
                                      (ibeam(), (0, 0, 0), 1.0)]), (15.33, 16)),
    "vertical-text": (frames_static(lambda s: [(affinity.rotate(ibeam(), 90, origin=(16, 16)).buffer(0.8, join_style=2), (255, 255, 255), 1.0),
                                               (affinity.rotate(ibeam(), 90, origin=(16, 16)), (0, 0, 0), 1.0)]), (16, 16)),
    "crosshair": (frames_static(lambda s: [(crosshair().buffer(0.8, join_style=2), (255, 255, 255), 1.0),
                                           (crosshair(), (0, 0, 0), 1.0)]), (15.33, 15.33)),
    "move": (frames_static(lambda s: outlined(four_way())), (16, 16)),
    "ns-resize": (frames_static(lambda s: outlined(double_arrow())), (16, 16)),
    "ew-resize": (frames_static(lambda s: outlined(affinity.rotate(double_arrow(), 90, origin=(16, 16)))), (16, 16)),
    "nwse-resize": (frames_static(lambda s: outlined(affinity.rotate(double_arrow(24), -45, origin=(16, 16)))), (16, 16)),
    "nesw-resize": (frames_static(lambda s: outlined(affinity.rotate(double_arrow(24), 45, origin=(16, 16)))), (16, 16)),
    "not-allowed": (frames_static(lambda s: outlined(not_allowed(), t=1.0)), (16, 16)),
    "help": (help_frames, (1.33, 1.33)),
    "progress": (progress_frames, (1.33, 1.33)),
    "wait": (wait_frames, (16, 16)),
}

ALIASES = {
    "default": ["left_ptr", "arrow", "top_left_arrow", "left_arrow", "right_ptr"],
    "pointer": ["hand1", "hand2", "pointing_hand", "hand",
                "e29285e634086352946a0e7090d73106", "9d800788f1b08800ae810202380a0822"],
    "text": ["xterm", "ibeam"],
    "crosshair": ["cross", "tcross", "cell", "plus", "color-picker", "target"],
    "move": ["fleur", "all-scroll", "size_all", "4498f0e0c1937ffe01fd06f973665830",
             "9081237383d90e509aa00f00170e968f", "dnd-move"],
    "ns-resize": ["n-resize", "s-resize", "size_ver", "sb_v_double_arrow", "v_double_arrow",
                  "row-resize", "split_v", "top_side", "bottom_side", "double_arrow",
                  "00008160000006810000408080010102", "2870a09082c103050810ffdffffe0204"],
    "ew-resize": ["e-resize", "w-resize", "size_hor", "sb_h_double_arrow", "h_double_arrow",
                  "col-resize", "split_h", "left_side", "right_side",
                  "028006030e0e7ebffc7f7070c0600140", "14fef782d02440884392942c11205230"],
    "nwse-resize": ["nw-resize", "se-resize", "size_fdiag", "top_left_corner", "bottom_right_corner",
                    "c7088f0f3e6c8088236ef8e1e3e70000", "38c5dff7c7b8962045400281044508d2"],
    "nesw-resize": ["ne-resize", "sw-resize", "size_bdiag", "top_right_corner", "bottom_left_corner",
                    "fcf1c3c7cd4491d801f1e1c78f100000", "50585d75b494802d0151028115016902"],
    "not-allowed": ["no-drop", "forbidden", "circle", "crossed_circle", "dnd-no-drop",
                    "03b6e0fcb3499374a867c041f52298f0"],
    "help": ["question_arrow", "whats_this", "left_ptr_help",
             "d9ce0ab605698f320427677b458ad60b", "5c6cd98b3f3ebcb1f9c7f1c204630408"],
    "progress": ["left_ptr_watch", "half-busy", "3ecb610c1bf2410f44200f48c40d3599",
                 "08e8e1c95fe2fc01f976f1e063a24ccd"],
    "wait": ["watch"],
}


# ---------------------------------------------------------------------------
# Escrita no formato Xcursor
# ---------------------------------------------------------------------------
def to_argb(rgb_premul, a):
    r, g, b = (np.clip(rgb_premul[..., i] * 255 + 0.5, 0, 255).astype(np.uint32) for i in range(3))
    al = np.clip(a * 255 + 0.5, 0, 255).astype(np.uint32)
    r, g, b = np.minimum(r, al), np.minimum(g, al), np.minimum(b, al)
    return ((al << 24) | (r << 16) | (g << 8) | b).astype("<u4").tobytes()


def write_xcursor(path, images):
    """images: [(nominal, w, h, xhot, yhot, delay, argb_bytes)]"""
    n = len(images)
    header = struct.pack("<4sIII", b"Xcur", 16, 0x10000, n)
    pos = 16 + n * 12
    toc, chunks = b"", b""
    for nominal, w, h, xh, yh, delay, px in images:
        toc += struct.pack("<III", 0xFFFD0002, nominal, pos)
        chunk = struct.pack("<IIIIIIIII", 36, 0xFFFD0002, nominal, 1, w, h, xh, yh, delay) + px
        chunks += chunk
        pos += len(chunk)
    with open(path, "wb") as f:
        f.write(header + toc + chunks)


def main():
    if os.path.isdir(OUT):
        shutil.rmtree(OUT)
    cdir = os.path.join(OUT, "cursors")
    os.makedirs(cdir)
    previews = {}
    global PIVOT
    for name, (builder, (hx, hy)) in CURSORS.items():
        PIVOT = PIVOTS.get(name, (16.0, 16.0))
        hx, hy = tx(hx, hy)
        images = []
        for size in SIZES:
            frames = builder(size)
            xh = min(size - 1, int(round(hx * size / U)))
            yh = min(size - 1, int(round(hy * size / U)))
            for (rgb, a), delay in frames:
                images.append((size, size, size, xh, yh, delay, to_argb(rgb, a)))
            if size == 48:
                (rgb, a), _ = frames[0]
                im = np.zeros((size, size, 4), np.uint8)
                with np.errstate(invalid="ignore", divide="ignore"):
                    im[..., :3] = np.clip(np.nan_to_num(rgb / a[..., None]) * 255, 0, 255)
                im[..., 3] = np.clip(a * 255, 0, 255)
                previews[name] = Image.fromarray(im, "RGBA")
        write_xcursor(os.path.join(cdir, name), images)
        for alias in ALIASES.get(name, []):
            os.symlink(name, os.path.join(cdir, alias))
    with open(os.path.join(OUT, "index.theme"), "w") as f:
        f.write("[Icon Theme]\nName=Onze\nComment=Cursores finos no estilo Windows 11\n"
                "Inherits=breeze_cursors\n")
    # folha de prévia (não instalada)
    names = list(previews)
    sheet = Image.new("RGBA", (len(names) * 64 + 16, 80), (243, 243, 243, 255))
    for i, n in enumerate(names):
        sheet.alpha_composite(previews[n], (8 + i * 64 + 8, 16))
    sheet.save(os.path.join(ROOT, "tools", "previa-cursores.png"))
    print("Cursores gerados em", OUT)


if __name__ == "__main__":
    main()
