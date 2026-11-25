#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Affiliate Product Studio Background Cleaner
===========================================
Converts contiguous pure-white studio backdrops on hardware/digital product
photos under `public/images/products/*.webp` into clean anti-aliased alpha
transparency (RGBA WebP) so products blend harmoniously onto both Light Mode
porcelain stages and Dark Mode obsidian glass pedestals.

Books (`category == "book"`) and full-frame editorial photos are preserved
intact without background stripping.
"""
from __future__ import annotations

import collections
import json
import os
from typing import Any, Dict, List, Tuple

from PIL import Image

WORKSPACE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CATALOG_PATH = os.path.join(WORKSPACE_DIR, "data", "affiliate_products.json")
PRODUCTS_DIR = os.path.join(WORKSPACE_DIR, "public", "images", "products")

HOLLOW_ICON_TYPES = {"xr", "earbuds", "glasses"}


def _is_studio_white(r: int, g: int, b: int, lum_min: int = 242, chroma_max: int = 12) -> bool:
    return r >= lum_min and g >= lum_min and b >= lum_min and (max(r, g, b) - min(r, g, b)) <= chroma_max


def _strip_studio_bg(im: Image.Image, category: str, icon_type: str) -> Tuple[Image.Image, bool]:
    if category == "book":
        return im, False

    rgba = im.convert("RGBA")
    w, h = rgba.size
    px = rgba.load()

    border_coords = (
        [(x, 0) for x in range(w)]
        + [(x, h - 1) for x in range(w)]
        + [(0, y) for y in range(1, h - 1)]
        + [(w - 1, y) for y in range(1, h - 1)]
    )

    white_border = [c for c in border_coords if _is_studio_white(*px[c][:3], lum_min=243, chroma_max=12)]
    if len(white_border) < len(border_coords) * 0.25:
        return im, False

    visited = bytearray(w * h)
    bg_mask = bytearray(w * h)
    q: collections.deque[Tuple[int, int]] = collections.deque()

    for x, y in white_border:
        idx = y * w + x
        if not visited[idx]:
            visited[idx] = 1
            bg_mask[idx] = 1
            q.append((x, y))

    while q:
        x, y = q.popleft()
        r0, g0, b0, _ = px[x, y]
        for nx, ny in ((x - 1, y), (x + 1, y), (x, y - 1), (x, y + 1)):
            if 0 <= nx < w and 0 <= ny < h:
                nidx = ny * w + nx
                if not visited[nidx]:
                    r, g, b, _ = px[nx, ny]
                    if _is_studio_white(r, g, b, lum_min=238, chroma_max=14):
                        if abs(r - r0) <= 15 and abs(g - g0) <= 15 and abs(b - b0) <= 15:
                            visited[nidx] = 1
                            bg_mask[nidx] = 1
                            q.append((nx, ny))

    # Also clear enclosed pure-white cavities inside rings, glasses, and open earbuds
    if icon_type in HOLLOW_ICON_TYPES:
        hole_visited = bytearray(w * h)
        for y in range(1, h - 1):
            for x in range(1, w - 1):
                idx = y * w + x
                if bg_mask[idx] or hole_visited[idx]:
                    continue
                r, g, b, _ = px[x, y]
                if r >= 251 and g >= 251 and b >= 251 and (max(r, g, b) - min(r, g, b)) <= 5:
                    comp: List[int] = []
                    hq: collections.deque[Tuple[int, int]] = collections.deque([(x, y)])
                    hole_visited[idx] = 1
                    while hq:
                        cx, cy = hq.popleft()
                        comp.append(cy * w + cx)
                        for nx, ny in ((cx - 1, cy), (cx + 1, cy), (cx, cy - 1), (cx, cy + 1)):
                            if 0 <= nx < w and 0 <= ny < h:
                                nidx = ny * w + nx
                                if not bg_mask[nidx] and not hole_visited[nidx]:
                                    nr, ng, nb, _ = px[nx, ny]
                                    if nr >= 246 and ng >= 246 and nb >= 246 and (max(nr, ng, nb) - min(nr, ng, nb)) <= 8:
                                        hole_visited[nidx] = 1
                                        hq.append((nx, ny))
                    if len(comp) >= 300:
                        for cidx in comp:
                            bg_mask[cidx] = 1

    # Soft edge anti-aliasing & fringe reduction
    out = rgba.copy()
    opx = out.load()
    for y in range(h):
        for x in range(w):
            idx = y * w + x
            if bg_mask[idx]:
                opx[x, y] = (0, 0, 0, 0)
            else:
                bg_n = 0
                for nx, ny in ((x - 1, y), (x + 1, y), (x, y - 1), (x, y + 1)):
                    if 0 <= nx < w and 0 <= ny < h and bg_mask[ny * w + nx]:
                        bg_n += 1
                if bg_n > 0:
                    r, g, b, a = opx[x, y]
                    lum = (r + g + b) / 3.0
                    if lum > 205 and (max(r, g, b) - min(r, g, b)) <= 18:
                        new_a = max(35, int(255 * max(0.0, 1.0 - (lum - 200) / 58.0)))
                        opx[x, y] = (r, g, b, min(a, new_a))

    return out, True


def main() -> None:
    with open(CATALOG_PATH, "r", encoding="utf-8") as f:
        items: List[Dict[str, Any]] = json.load(f)

    cleaned = 0
    preserved = 0
    for it in items:
        pid = it["id"]
        path = os.path.join(PRODUCTS_DIR, f"{pid}.webp")
        if not os.path.exists(path):
            continue
        with Image.open(path) as im:
            out, changed = _strip_studio_bg(im, it.get("category", ""), it.get("iconType", ""))
            if changed:
                tmp = path + ".tmp"
                out.save(tmp, format="WEBP", quality=84, method=4)
                os.replace(tmp, path)
                cleaned += 1
            else:
                preserved += 1

    print(f"[DONE] Studio background cleanup finished: {cleaned} converted to transparent RGBA WebP, {preserved} preserved intact.")


if __name__ == "__main__":
    main()
