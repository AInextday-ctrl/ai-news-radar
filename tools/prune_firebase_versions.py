#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Firebase Hosting Stale Version Pruner
=====================================
Deletes old unused Firebase Hosting versions via the official v1beta1 REST API
so cumulative snapshots never hit the project Hosting storage quota (HTTP 429).
Always preserves the current `live` channel version plus the newest `keep` versions.
"""
from __future__ import annotations

import os
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, List, Optional, Set, Tuple

import requests

PROJECT_ID = "ai-radar-news"
SITE_ID = "ai-radar-news"
BASE_URL = f"https://firebasehosting.googleapis.com/v1beta1/projects/{PROJECT_ID}/sites/{SITE_ID}"

PROXIES: Optional[Dict[str, str]] = (
    {"http": "http://127.0.0.1:7890", "https": "http://127.0.0.1:7890"}
    if os.environ.get("GITHUB_ACTIONS", "").lower() != "true"
    else None
)


def _get_access_token() -> str:
    env_tok = os.environ.get("GCP_ACCESS_TOKEN", "").strip()
    if env_tok:
        return env_tok
    return subprocess.check_output(
        "gcloud auth print-access-token", shell=True, text=True
    ).strip()


def _headers(token: str) -> Dict[str, str]:
    return {
        "Authorization": f"Bearer {token}",
        "X-Goog-User-Project": PROJECT_ID,
    }


def _get_live_version_name(hdrs: Dict[str, str]) -> Optional[str]:
    r = requests.get(f"{BASE_URL}/channels/live", headers=hdrs, proxies=PROXIES, timeout=15)
    if r.status_code != 200:
        return None
    return r.json().get("release", {}).get("version", {}).get("name")


def _delete_one(vname: str, hdrs: Dict[str, str]) -> Tuple[str, int, str]:
    r = requests.delete(
        f"https://firebasehosting.googleapis.com/v1beta1/{vname}",
        headers=hdrs,
        proxies=PROXIES,
        timeout=20,
    )
    return vname.split("/")[-1], r.status_code, r.text[:160]


def prune_old_versions(keep: int = 2, max_pages: int = 12) -> None:
    token = _get_access_token()
    hdrs = _headers(token)

    live_ver = _get_live_version_name(hdrs)
    protected: Set[str] = set()
    if live_ver:
        protected.add(live_ver)

    all_versions = []
    page_token: Optional[str] = None
    for page_no in range(1, max_pages + 1):
        params: Dict[str, str] = {"pageSize": "100"}
        if page_token:
            params["pageToken"] = page_token
        resp = requests.get(
            f"{BASE_URL}/versions", headers=hdrs, params=params, proxies=PROXIES, timeout=20
        )
        resp.raise_for_status()
        data = resp.json()
        batch = data.get("versions", [])
        all_versions.extend(batch)
        print(f"[PAGE {page_no}] Fetched {len(batch)} versions (total={len(all_versions)})", flush=True)
        page_token = data.get("nextPageToken")
        if not page_token:
            break

    kept_finalized = 0
    for v in all_versions:
        vname = v.get("name", "")
        if v.get("status") == "FINALIZED" and kept_finalized < keep:
            protected.add(vname)
            kept_finalized += 1

    candidates = [
        v for v in all_versions
        if v.get("name") not in protected and v.get("status") != "DELETED"
    ]
    print(
        f"[INFO] Found {len(all_versions)} versions (live={live_ver.split('/')[-1] if live_ver else 'none'}), "
        f"pruning {len(candidates)} stale versions (keeping {len(protected)})...",
        flush=True,
    )

    deleted = 0
    failed = 0
    with ThreadPoolExecutor(max_workers=8) as pool:
        futs = [pool.submit(_delete_one, v["name"], hdrs) for v in candidates]
        for idx, fut in enumerate(as_completed(futs), 1):
            vid, code, err = fut.result()
            if code in (200, 204, 404):
                deleted += 1
            else:
                failed += 1
                if failed <= 5:
                    print(f"[WARN] Failed to delete {vid}: {code} {err}", flush=True)
            if idx % 50 == 0 or idx == len(candidates):
                print(f"  [{idx}/{len(candidates)}] deleted={deleted}, failed={failed}", flush=True)

    print(f"[DONE] Pruned {deleted} stale Firebase Hosting versions (failed={failed}).", flush=True)


if __name__ == "__main__":
    keep_n = int(sys.argv[1]) if len(sys.argv) > 1 else 2
    prune_old_versions(keep=keep_n)
