#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Prepares the Onze wallpaper package from a single source image.

  tools/wallpaper/source.png  ->  src/wallpapers/Onze/contents/
                                    images/       (light)  16:9 and 16:10
                                    images_dark/  (dark)   16:9 and 16:10

Steps
  1. Upscale (EDSR x3 neural super-resolution if the model is available,
     otherwise high-quality Lanczos).
  2. 16:9 version: the background is extended on the left and right
     (extrapolating its gradient) so nothing of the artwork is cropped.
  3. Dark version: the background is separated from the artwork (flood fill
     bounded by the artwork's contours, with a soft matte on the edges) and
     replaced by a navy gradient; the artwork is slightly deepened.
  4. Exports 3840/2560/1920 px wide JPEGs for each aspect ratio, plus previews.

Requirements: pip install numpy pillow opencv-contrib-python-headless
EDSR model (optional, ~38 MB):
  git clone --depth 1 https://github.com/Saafke/EDSR_Tensorflow.git
  python3 tools/prepare_wallpaper.py --edsr EDSR_Tensorflow/models/EDSR_x3.pb

Usage: python3 tools/prepare_wallpaper.py [--edsr MODEL.pb] [--upscaled FILE.png]
  --upscaled reuses an image that was already upscaled (EDSR takes ~20 min on CPU).
"""
import argparse
import json
import os
import shutil

import cv2
import numpy as np
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SOURCE = os.path.join(ROOT, "tools", "wallpaper", "source.png")
OUT = os.path.join(ROOT, "src", "wallpapers", "Onze")
SIZES = {"16x9": [(3840, 2160), (2560, 1440), (1920, 1080)],
         "16x10": [(3840, 2400), (2560, 1600), (1920, 1200)]}


# --- 1. upscale ----------------------------------------------------------------------
def upscale_edsr(bgr, model, scale=3, tile=200, pad=16):
    sr = cv2.dnn_superres.DnnSuperResImpl_create()
    sr.readModel(model)
    sr.setModel("edsr", scale)
    H, W = bgr.shape[:2]
    out = np.zeros((H * scale, W * scale, 3), np.float32)
    wsum = np.zeros((H * scale, W * scale, 1), np.float32)
    for y in range(0, H, tile):
        for x in range(0, W, tile):
            y0, x0 = max(0, y - pad), max(0, x - pad)
            y1, x1 = min(H, y + tile + pad), min(W, x + tile + pad)
            up = sr.upsample(bgr[y0:y1, x0:x1]).astype(np.float32)
            h, w = up.shape[:2]
            wy = np.minimum(np.arange(h) + 1, np.arange(h)[::-1] + 1).astype(np.float32)
            wx = np.minimum(np.arange(w) + 1, np.arange(w)[::-1] + 1).astype(np.float32)
            wgt = np.minimum(np.minimum(wy[:, None], wx[None, :]), pad * scale)[..., None]
            out[y0 * scale:y1 * scale, x0 * scale:x1 * scale] += up * wgt
            wsum[y0 * scale:y1 * scale, x0 * scale:x1 * scale] += wgt
        print(f"  EDSR: row {y}/{H}", flush=True)
    return np.clip(out / wsum, 0, 255).astype(np.uint8)


# --- 2. extend to 16:9 ------------------------------------------------------------------
def extend_sides(rgb, target_aspect=16 / 9, fit_cols=None):
    """Adds columns left and right, continuing each row's gradient linearly."""
    H, W = rgb.shape[:2]
    newW = int(round(H * target_aspect))
    add = (newW - W) // 2
    if add <= 0:
        return rgb
    f = rgb.astype(np.float32)
    n = fit_cols or max(40, W // 12)
    out = np.zeros((H, W + 2 * add, 3), np.float32)
    out[:, add:add + W] = f
    xs = np.arange(n, dtype=np.float32)
    for side in ("left", "right"):
        block = f[:, :n] if side == "left" else f[:, W - n:]
        # least squares per row/channel: value = a + b*x
        xm = xs.mean()
        b = ((block - block.mean(1, keepdims=True)) * (xs - xm)[None, :, None]).sum(1) / ((xs - xm) ** 2).sum()
        a = block.mean(1) - b * xm
        b = cv2.GaussianBlur(b, (1, 0), 0, sigmaY=H / 200)  # smooth the slope vertically
        steps = np.arange(1, add + 1, dtype=np.float32)
        if side == "left":
            # x = -steps (to the left of column 0); damp the slope so it fades out
            damp = steps * (1 - 0.5 * steps / add)
            vals = (a[:, None, :] + b[:, None, :] * (0 - damp[None, :, None]))
            out[:, :add] = vals[:, ::-1]
        else:
            damp = steps * (1 - 0.5 * steps / add)
            vals = a[:, None, :] + b[:, None, :] * ((n - 1) + damp[None, :, None])
            out[:, add + W:] = vals
    return np.clip(out + 0.5, 0, 255).astype(np.uint8)


# --- 3. dark version -------------------------------------------------------------------
def background_mask(rgb, s=1.0):
    img = cv2.GaussianBlur(rgb, (0, 0), 1.2 * s)
    H, W = img.shape[:2]
    mask = np.zeros((H + 2, W + 2), np.uint8)
    gray = cv2.cvtColor(rgb, cv2.COLOR_RGB2GRAY)
    if s > 1:
        small = cv2.resize(gray, (int(W / s), int(H / s)), interpolation=cv2.INTER_AREA)
        edges = cv2.resize(cv2.Canny(small, 8, 24), (W, H), interpolation=cv2.INTER_NEAREST)
    else:
        edges = cv2.Canny(gray, 8, 24)
    k = max(3, int(3 * s) | 1)
    edges = cv2.dilate(edges, np.ones((k, k), np.uint8))
    mask[1:-1, 1:-1][edges > 0] = 1
    flags = 4 | cv2.FLOODFILL_MASK_ONLY | (255 << 8)
    step = max(10, W // 40)
    seeds = [(x, 0) for x in range(0, W, step)] + [(0, y) for y in range(0, H, step)] + \
            [(W - 1, y) for y in range(0, H, step)]
    for sx, sy in seeds:
        if mask[sy + 1, sx + 1] == 0:
            cv2.floodFill(img, mask, (sx, sy), 0, (2, 2, 2), (2, 2, 2), flags)
    m = (mask[1:-1, 1:-1] == 255).astype(np.float32)
    m = cv2.morphologyEx(m, cv2.MORPH_CLOSE, np.ones((k, k), np.uint8))
    f = rgb.astype(np.float32)
    bgcol = cv2.GaussianBlur(f * m[..., None], (0, 0), 6 * s) / \
        (cv2.GaussianBlur(m, (0, 0), 6 * s)[..., None] + 1e-6)
    kb = int(9 * s) | 1
    band = (cv2.dilate(m, np.ones((kb, kb), np.uint8)) > 0) & (m < 1)
    dist = np.linalg.norm(f - bgcol, axis=-1)
    alpha = np.clip(1.0 - (dist - 4.0) / 22.0, 0, 1)
    m = np.where(band, alpha, m).astype(np.float32)
    return cv2.GaussianBlur(m, (0, 0), 0.6 * s)


def dark_version(rgb, s=1.0):
    m = background_mask(rgb, s)[..., None]
    a = rgb.astype(np.float32) / 255.0
    H, W = a.shape[:2]
    artwork = np.power(a, 1.35) * 0.85
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    r = np.sqrt(((xx / W) - 0.45) ** 2 + (((yy / H) - 0.35) / 0.9) ** 2)
    t = np.clip(r / 0.75, 0, 1)[..., None]
    bg = np.array([0.13, 0.20, 0.32], np.float32) * (1 - t) + np.array([0.04, 0.07, 0.12], np.float32) * t
    out = artwork * (1 - m) + bg * m
    # light dithering to avoid banding in the smooth navy gradient
    out += np.random.default_rng(7).normal(0, 0.6 / 255, out.shape[:2]).astype(np.float32)[..., None]
    return np.clip(out * 255 + 0.5, 0, 255).astype(np.uint8)


# --- 4. export ---------------------------------------------------------------------------
def export(rgb, folder, sizes):
    os.makedirs(folder, exist_ok=True)
    im = Image.fromarray(rgb)
    for w, h in sizes:
        im.resize((w, h), Image.LANCZOS).save(os.path.join(folder, f"{w}x{h}.jpg"),
                                               quality=94, subsampling=0, optimize=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--edsr", help="path to EDSR_x3.pb (optional)")
    ap.add_argument("--upscaled", help="already upscaled image to reuse")
    args = ap.parse_args()

    src = np.asarray(Image.open(SOURCE).convert("RGB"))
    print(f"Source: {src.shape[1]}x{src.shape[0]}")
    if args.upscaled:
        big = np.asarray(Image.open(args.upscaled).convert("RGB"))
    elif args.edsr and os.path.exists(args.edsr):
        big = cv2.cvtColor(upscale_edsr(cv2.cvtColor(src, cv2.COLOR_RGB2BGR), args.edsr), cv2.COLOR_BGR2RGB)
    else:
        print("EDSR model not given: using Lanczos")
        big = np.asarray(Image.fromarray(src).resize((src.shape[1] * 3, src.shape[0] * 3), Image.LANCZOS))
    scale = big.shape[1] / src.shape[1]
    print(f"Upscaled: {big.shape[1]}x{big.shape[0]}")

    # artwork aspect is 16:10 -> 16:10 as is, 16:9 by extending the sides
    light = {"16x10": big, "16x9": extend_sides(big, 16 / 9)}
    if os.path.isdir(os.path.join(OUT, "contents")):
        shutil.rmtree(os.path.join(OUT, "contents"))
    for ratio, img in light.items():
        export(img, os.path.join(OUT, "contents", "images"), SIZES[ratio])
        dark = dark_version(img, s=scale)
        export(dark, os.path.join(OUT, "contents", "images_dark"), SIZES[ratio])
        if ratio == "16x9":
            Image.fromarray(img).resize((400, 225), Image.LANCZOS).save(os.path.join(OUT, "contents", "screenshot.png"))
            Image.fromarray(dark).resize((400, 225), Image.LANCZOS).save(os.path.join(OUT, "contents", "screenshot_dark.png"))
    with open(os.path.join(OUT, "metadata.json"), "w") as f:
        json.dump({"KPlugin": {"Authors": [{"Name": "Rafael Carvalho Ramos",
                                            "Email": "rafaelramosmacae@gmail.com"}],
                               "Copyright": "© 2026 Projeto Onze — Rafael Carvalho Ramos",
                               "Id": "Onze", "License": "CC0-1.0", "Name": "Onze", "Version": "1.4"},
                   "KPackageStructure": "Wallpaper/Images"}, f, indent=4)
        f.write("\n")
    print("Wallpaper package written to", OUT)


if __name__ == "__main__":
    main()
