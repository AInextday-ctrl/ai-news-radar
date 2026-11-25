#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Affiliate Product Studio Background Cleaner & Edge De-Fringer
=============================================================
Converts pure-white studio backdrops on hardware/digital product photos under
`public/images/products/*.webp` into anti-aliased RGBA transparency and removes
1-2px bright white edge halos (color decontamination) so items float cleanly
with zero pale outline on dark obsidian glass cards.

Books (`category == "book"`) and full-frame editorial photos stay untouched.
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

HOLLOW_ICON_TYPES = {"xr", "earbuds", "glasses", "drone", "robot", "keyboard"}


def _is_studio_white(r: int, g: int, b: int, lum_min: int = 240, chroma_max: int = 14) -> bool:
    return r >= lum_min and g >= lum_min and b >= lum_min and (max(r, g, b) - min(r, g, b)) <= chroma_max


def _defringe_alpha_edges(rgba: Image.Image) -> Image.Image:
    """Erodes/feathers bright neutral 1-2px halos bordering transparent background."""
    w, h = rgba.size
    out = rgba.copy()
    px = rgba.load()
    opx = out.load()

    # Distance-1 and Distance-2 edge ring relative to alpha == 0
    ring1 = bytearray(w * h)
    for y in range(h):
        for x in range(w):
            if px[x, y][3] <= 12:
                continue
            has_trans_neighbor = False
            for nx, ny in ((x - 1, y), (x + 1, y), (x, y - 1), (x, y + 1), (x - 1, y - 1), (x + 1, y - 1), (x - 1, y + 1), (x + 1, y + 1)):
                if 0 <= nx < w and 0 <= ny < h and px[nx, ny][3] <= 12:
                    has_trans_neighbor = True
                    break
            if has_trans_neighbor:
                ring1[y * w + x] = 1
                r, g, b, a = px[x, y]
                lum = (r + g + b) / 3.0
                chroma = max(r, g, b) - min(r, g, b)
                # Strip bright white/pale neutral studio fringe pixels completely or feather cleanly
                if lum >= 224 and chroma <= 18:
                    opx[x, y] = (0, 0, 0, 0)
                elif lum >= 180 and chroma <= 20:
                    # Decontaminate white mix toward nearby darker interior pixel if available
                    new_a = max(30, min(a, int(255 * max(0.0, 1.0 - (lum - 170) / 70.0))))
                    opx[x, y] = (int(r * 0.78), int(g * 0.78), int(b * 0.78), new_a)

    # Ring 2 soft clean for subtle outer light halo
    px2 = out.load()
    for y in range(h):
        for x in range(w):
            if px2[x, y][3] <= 12 or ring1[y * w + x]:
                continue
            near_clear = False
            for nx, ny in ((x - 1, y), (x + 1, y), (x, y - 1), (x, y + 1)):
                if 0 <= nx < w and 0 <= ny < h and px2[nx, ny][3] <= 24:
                    near_clear = True
                    break
            if near_clear:
                r, g, b, a = px2[x, y]
                lum = (r + g + b) / 3.0
                chroma = max(r, g, b) - min(r, g, b)
                if lum >= 232 and chroma <= 14:
                    opx[x, y] = (int(r * 0.85), int(g * 0.85), int(b * 0.85), min(a, 140))

    return out


def _strip_studio_bg(im: Image.Image, category: str, icon_type: str) -> Tuple[Image.Image, bool]:
    if category == "book":
        return im, False

    was_rgba = im.mode == "RGBA"
    rgba = im.convert("RGBA")
    w, h = rgba.size
    px = rgba.load()

    if not was_rgba:
        border_coords = (
            [(x, 0) for x in range(w)]
            + [(x, h - 1) for x in range(w)]
            + [(0, y) for y in range(1, h - 1)]
            + [(w - 1, y) for y in range(1, h - 1)]
        )
        white_border = [c for c in border_coords if _is_studio_white(*px[c][:3], lum_min=242, chroma_max=12)]
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
                        if _is_studio_white(r, g, b, lum_min=236, chroma_max=15):
                            if abs(r - r0) <= 15 and abs(g - g0) <= 15 and abs(b - b0) <= 15:
                                visited[nidx] = 1
                                bg_mask[nidx] = 1
                                q.append((nx, ny))

        out = rgba.copy()
        opx = out.load()
        for y in range(h):
            for x in range(w):
                if bg_mask[y * w + x]:
                    opx[x, y] = (0, 0, 0, 0)
        rgba = out
        px = rgba.load()

    # Clear enclosed white pockets inside hollow products (rings, glasses, headphones)
    if icon_type in HOLLOW_ICON_TYPES:
        hole_visited = bytearray(w * h)
        clear_cells: List[int] = []
        for y in range(1, h - 1):
            for x in range(1, w - 1):
                idx = y * w + x
                if px[x, y][3] <= 12 or hole_visited[idx]:
                    continue
                r, g, b, _ = px[x, y]
                if r >= 249 and g >= 249 and b >= 249 and (max(r, g, b) - min(r, g, b)) <= 6:
                    comp: List[int] = []
                    hq: collections.deque[Tuple[int, int]] = collections.deque([(x, y)])
                    hole_visited[idx] = 1
                    while hq:
                        cx, cy = hq.popleft()
                        comp.append(cy * w + cx)
                        for nx, ny in ((cx - 1, cy), (cx + 1, cy), (cx, cy - 1), (cx, cy + 1)):
                            if 0 <= nx < w and 0 <= ny < h:
                                nidx = ny * w + nx
                                if px[nx, ny][3] > 12 and not hole_visited[nidx]:
                                    nr, ng, nb, _ = px[nx, ny]
                                    if nr >= 244 and ng >= 244 and nb >= 244 and (max(nr, ng, nb) - min(nr, ng, nb)) <= 10:
                                        hole_visited[nidx] = 1
                                        hq.append((nx, ny))
                    if len(comp) >= 180:
                        clear_cells.extend(comp)
        if clear_cells:
            out = rgba.copy()
            opx = out.load()
            for cidx in clear_cells:
                opx[cidx % w, cidx // w] = (0, 0, 0, 0)
            rgba = out

    # Only run defringe on images that actually have transparent pixels
    alpha_extrema = rgba.getchannel("A").getextrema()
    if alpha_extrema[0] < 20:
        defringed = _defringe_alpha_edges(rgba)
        return defringed, True

    return im, False


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

    print(f"[DONE] Studio background & edge halo cleanup finished: {cleaned} refined RGBA WebP, {preserved} preserved intact.")


if __name__ == "__main__":
    main()
