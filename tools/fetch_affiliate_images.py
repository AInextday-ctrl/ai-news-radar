#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Affiliate Product Real Photo Fetcher & Optimizer
================================================
Fetches real organic product photographs (or verified ISBN book covers),
validates image resolution & subject match, optimizes them to compact local
WebP thumbnails under `public/images/products/{id}.webp`, and writes the local
`/images/products/{id}.webp` path into `data/affiliate_products.json`.
"""
from __future__ import annotations

import html
import io
import json
import os
import random
import re
import time
import urllib.parse
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any, Dict, List, Optional, Tuple

from curl_cffi import requests
from PIL import Image

WORKSPACE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CATALOG_PATH = os.path.join(WORKSPACE_DIR, "data", "affiliate_products.json")
OUT_DIR = os.path.join(WORKSPACE_DIR, "public", "images", "products")

PROXIES: Optional[Dict[str, str]] = (
    {"http": "http://127.0.0.1:7890", "https": "http://127.0.0.1:7890"}
    if os.environ.get("GITHUB_ACTIONS", "").lower() != "true"
    else None
)

ACCESSORY_PENALTY_WORDS = {
    "case", "cover", "sleeve", "skin", "sticker", "screen protector",
    "tempered glass", "replacement ear", "ear tips", "charging cable",
    "adapter only", "mount only", "stand only", "carrying bag", "pouch",
}


def _tokenize(text: str) -> List[str]:
    return [
        w for w in re.findall(r"[a-z0-9]+", (text or "").lower())
        if len(w) >= 2 and w not in {"the", "for", "with", "and", "pro", "plus", "edition", "series"}
    ]


def _score_candidate(product_name: str, alt: str) -> float:
    p_toks = set(_tokenize(product_name))
    a_toks = set(_tokenize(alt))
    if not p_toks or not a_toks:
        return 0.0
    overlap = len(p_toks & a_toks) / max(1, len(p_toks))
    alt_low = alt.lower()
    name_low = product_name.lower()
    for bad in ACCESSORY_PENALTY_WORDS:
        if bad in alt_low and bad not in name_low:
            overlap -= 0.45
    return overlap


def _extract_amz_candidates(html_text: str, url: str, product_name: str) -> List[Tuple[float, str, str]]:
    cands: List[Tuple[float, str, str]] = []
    if "/dp/" in url:
        for pat in [
            r'id="(?:landingImage|imgBlkFront|ebooksImgBlkFront)"[^>]+?(?:data-old-hires|src)="(https://m\.media-amazon\.com/images/I/[^"]+)"',
            r'"hiRes":"(https://m\.media-amazon\.com/images/I/[^"]+)"',
            r'"large":"(https://m\.media-amazon\.com/images/I/[^"]+)"',
        ]:
            m = re.search(pat, html_text)
            if m:
                src = m.group(1)
                hires = re.sub(r'\._[^.]+\.(jpg|jpeg|png|webp)$', '._AC_SX679_.jpg', src)
                cands.append((2.0, hires, "dp-direct"))
                break

    blocks = html_text.split('data-component-type="s-search-result"')
    for idx, blk in enumerate(blocks[1:14]):
        head = blk[:1400]
        if "AdHolder" in head or "puis-sponsored" in head or ">Sponsored<" in head:
            continue
        m_img = re.search(r'<img[^>]+class="[^"]*s-image[^"]*"[^>]*>', blk)
        if not m_img:
            continue
        tag = m_img.group(0)
        m_src = re.search(r'src="(https://m\.media-amazon\.com/images/I/[^"]+)"', tag)
        m_alt = re.search(r'alt="([^"]*)"', tag)
        if not m_src:
            continue
        src = m_src.group(1)
        alt = html.unescape(m_alt.group(1)) if m_alt else ""
        hires = re.sub(r'\._[^.]+\.(jpg|jpeg|png|webp)$', '._AC_SX679_.jpg', src)
        score = _score_candidate(product_name, alt) - idx * 0.02
        cands.append((score, hires, alt))

    cands.sort(key=lambda x: x[0], reverse=True)
    return cands


def _download_and_optimize_image(img_url: str, dest_path: str) -> bool:
    try:
        r = requests.get(
            img_url,
            impersonate="chrome",
            proxies=PROXIES,
            timeout=15,
            headers={"Referer": "https://www.amazon.com/"},
        )
        if r.status_code != 200 or len(r.content) < 2500:
            return False
        im = Image.open(io.BytesIO(r.content))
        if im.width < 120 or im.height < 120:
            return False
        if im.mode not in ("RGB", "RGBA"):
            im = im.convert("RGB")
        # Composite alpha onto pure crisp white for uniform product photography
        if im.mode == "RGBA":
            bg = Image.new("RGB", im.size, (255, 255, 255))
            bg.paste(im, mask=im.split()[3])
            im = bg
        im.thumbnail((480, 480), Image.Resampling.LANCZOS)
        tmp_path = dest_path + ".tmp"
        im.save(tmp_path, format="WEBP", quality=82, method=4)
        os.replace(tmp_path, dest_path)
        return os.path.exists(dest_path) and os.path.getsize(dest_path) > 1500
    except Exception:
        return False


def _fetch_one(item: Dict[str, Any]) -> Tuple[str, bool, str]:
    pid = item["id"]
    name = item["en"]["name"]
    url = item["url"]
    dest_path = os.path.join(OUT_DIR, f"{pid}.webp")

    if os.path.exists(dest_path) and os.path.getsize(dest_path) > 1800:
        return pid, True, "cached"

    # Fast reliable path for ISBN-10 books: try Amazon DP first, fallback to OpenLibrary L cover
    isbn_m = re.search(r"/dp/([A-Z0-9]{10})", url)
    queries = [url]
    # Also try clean name search if needed
    clean_q = re.sub(r"\([^)]*\)", "", name).strip()
    queries.append("https://www.amazon.com/s?k=" + urllib.parse.quote_plus(clean_q))

    for attempt_idx in range(2):
        target_url = queries[min(attempt_idx, len(queries) - 1)]
        try:
            time.sleep(random.uniform(0.25, 0.75))
            r = requests.get(
                target_url,
                impersonate="chrome",
                proxies=PROXIES,
                timeout=18,
                headers={"Accept-Language": "en-US,en;q=0.9"},
            )
            if r.status_code == 200:
                cands = _extract_amz_candidates(r.text, target_url, name)
                for _score, img_url, alt in cands[:4]:
                    if _download_and_optimize_image(img_url, dest_path):
                        return pid, True, f"amz:{alt[:35]}"
        except Exception:
            pass

    if isbn_m:
        isbn = isbn_m.group(1)
        ol_url = f"https://covers.openlibrary.org/b/isbn/{isbn}-L.jpg?default=false"
        if _download_and_optimize_image(ol_url, dest_path):
            return pid, True, "openlibrary"

    return pid, False, "failed"


def main() -> None:
    os.makedirs(OUT_DIR, exist_ok=True)
    with open(CATALOG_PATH, "r", encoding="utf-8") as f:
        items: List[Dict[str, Any]] = json.load(f)

    total = len(items)
    cached = sum(
        1 for it in items
        if os.path.exists(os.path.join(OUT_DIR, f"{it['id']}.webp"))
        and os.path.getsize(os.path.join(OUT_DIR, f"{it['id']}.webp")) > 1800
    )
    print(f"[INFO] Starting product image sync for {total} products ({cached} already cached)...")

    ok_count = 0
    failed: List[str] = []

    with ThreadPoolExecutor(max_workers=4) as pool:
        futs = {pool.submit(_fetch_one, it): it for it in items}
        for idx, fut in enumerate(as_completed(futs), 1):
            pid, ok, info = fut.result()
            if ok:
                ok_count += 1
            else:
                failed.append(pid)
            if idx % 25 == 0 or idx == total or not ok:
                print(f"[{idx}/{total}] {pid}: {'OK' if ok else 'FAIL'} ({info})")

    # Update `image` field on every catalog entry whose WebP file exists
    for it in items:
        pid = it["id"]
        rel_img = f"/images/products/{pid}.webp"
        if os.path.exists(os.path.join(OUT_DIR, f"{pid}.webp")):
            it["image"] = rel_img

    with open(CATALOG_PATH, "w", encoding="utf-8") as f:
        json.dump(items, f, ensure_ascii=False, indent=2)

    print(f"[DONE] Real product photos ready: {ok_count}/{total}, failed: {len(failed)}")
    if failed:
        print("[WARN] Failed IDs:", failed)


if __name__ == "__main__":
    main()
