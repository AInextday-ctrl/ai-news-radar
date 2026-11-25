#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Affiliate Product Catalog Validator & Compiler
==============================================
Validates `data/affiliate_products.json` (>= 100 unique AI/tech items, all Amazon URLs
with `tag=purrpulse-20`, zero hardcoded prices, bilingual EN+ZH fields) and injects the
validated catalog cleanly into `public/js/monetization.js`.
"""
from __future__ import annotations

import json
import os
import re
import sys
from typing import Any, Dict, List

WORKSPACE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CATALOG_PATH = os.path.join(WORKSPACE_DIR, "data", "affiliate_products.json")
MONETIZATION_JS_PATH = os.path.join(WORKSPACE_DIR, "public", "js", "monetization.js")


def validate_catalog(items: List[Dict[str, Any]]) -> None:
    assert isinstance(items, list), "Catalog must be a JSON array"
    assert len(items) >= 100, f"Catalog must contain >= 100 products, got {len(items)}"

    seen_ids = set()
    seen_urls = set()
    price_re = re.compile(r"\$\s*\d+(?:,\d{3})*(?:\.\d{2})?")

    for idx, it in enumerate(items):
        pid = it.get("id", "")
        assert pid and pid not in seen_ids, f"Duplicate or empty id at index {idx}: {pid}"
        seen_ids.add(pid)

        url = it.get("url", "")
        assert url.startswith("https://www.amazon.com/") and "tag=purrpulse-20" in url, (
            f"Invalid affiliate URL for {pid}: {url}"
        )
        assert url not in seen_urls, f"Duplicate affiliate URL for {pid}: {url}"
        seen_urls.add(url)

        img = it.get("image", "")
        assert img.startswith("/images/products/") and img.endswith(".webp"), (
            f"Missing or invalid product photo path on {pid}: {img}"
        )
        img_disk = os.path.join(WORKSPACE_DIR, "public", img.lstrip("/").replace("/", os.sep))
        assert os.path.exists(img_disk) and os.path.getsize(img_disk) > 1024, (
            f"Product photo missing or too small on disk for {pid}: {img_disk}"
        )

        tags = it.get("tags", [])
        assert isinstance(tags, list) and len(tags) >= 4, f"Too few tags on {pid}"

        for lang in ("en", "zh"):
            block = it.get(lang)
            assert isinstance(block, dict), f"Missing {lang} copy on {pid}"
            for fld in ("badge", "name", "tagline", "cta", "hint"):
                val = str(block.get(fld) or "").strip()
                assert val, f"Empty {lang}.{fld} on {pid}"
                assert not price_re.search(val), f"Hardcoded price forbidden by Amazon TOS in {pid}.{lang}.{fld}: {val}"

    print(f"[OK] Validated {len(items)} unique Amazon Associates (purrpulse-20) AI/tech products.")


def sync_into_monetization_js(items: List[Dict[str, Any]]) -> None:
    with open(MONETIZATION_JS_PATH, "r", encoding="utf-8") as f:
        src = f.read()

    # Check if markers exist; otherwise replace var PRODUCT_POOL = [...];
    json_payload = json.dumps(items, ensure_ascii=False, indent=2)
    # Indent 2 spaces inside IIFE
    indented = "\n".join(("  " + line if line else "") for line in json_payload.splitlines())
    replacement = f"var PRODUCT_POOL = {indented.lstrip()};"

    pattern = re.compile(r"var PRODUCT_POOL = \[[\s\S]*?\n  \];")
    assert pattern.search(src), "Could not locate `var PRODUCT_POOL = [...];` block in public/js/monetization.js"
    updated = pattern.sub(lambda _m: replacement, src, count=1)

    with open(MONETIZATION_JS_PATH, "w", encoding="utf-8") as f:
        f.write(updated)
    print(f"[OK] Synced {len(items)} products into {os.path.relpath(MONETIZATION_JS_PATH, WORKSPACE_DIR)}")


if __name__ == "__main__":
    with open(CATALOG_PATH, "r", encoding="utf-8") as f:
        catalog = json.load(f)
    validate_catalog(catalog)
    sync_into_monetization_js(catalog)
