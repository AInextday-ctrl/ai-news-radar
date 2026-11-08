"""
IndexNow Submitter for AI News Radar (https://ainewsradar.xyz)
==============================================================
Empowers instantaneous real-time URL indexing on Microsoft Bing,
Microsoft Copilot, and Yandex via the open IndexNow protocol.

Specifications:
- Protocol: https://www.indexnow.org/documentation
- Endpoint: https://api.indexnow.org/indexnow
- Key: 8f87acc55231fb3e55bf3989fe3dc9ab
- Key Location: https://ainewsradar.xyz/8f87acc55231fb3e55bf3989fe3dc9ab.txt
"""

import os
import sys
import json
import re
import argparse
import urllib.request
import urllib.error
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional

try:
    if sys.stdout.encoding and sys.stdout.encoding.lower() != 'utf-8':
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
except Exception:
    pass

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
PUBLIC_DIR = os.path.join(BASE_DIR, "public")
LEDGER_PATH = os.path.join(DATA_DIR, "indexnow_ledger.json")

INDEXNOW_KEY = "8f87acc55231fb3e55bf3989fe3dc9ab"
INDEXNOW_HOST = "ainewsradar.xyz"
INDEXNOW_KEY_LOCATION = f"https://{INDEXNOW_HOST}/{INDEXNOW_KEY}.txt"
INDEXNOW_ENDPOINT = "https://api.indexnow.org/indexnow"


def load_sitemap_urls() -> List[str]:
    """Extracts all canonical URLs from public/sitemap.xml."""
    sitemap_path = os.path.join(PUBLIC_DIR, "sitemap.xml")
    if not os.path.exists(sitemap_path):
        return []
    try:
        with open(sitemap_path, "r", encoding="utf-8") as f:
            content = f.read()
        urls = re.findall(r"<loc>(https://ainewsradar\.xyz[^<]+)</loc>", content)
        # Deduplicate while preserving order
        seen = set()
        deduped = []
        for u in urls:
            u_clean = u.strip()
            if u_clean and u_clean not in seen:
                seen.add(u_clean)
                deduped.append(u_clean)
        return deduped
    except Exception as e:
        print(f"⚠️ [IndexNow] 读取 sitemap.xml 失败: {e}")
        return []


def load_ledger() -> Dict[str, Any]:
    """Loads previous submission ledger."""
    if os.path.exists(LEDGER_PATH):
        try:
            with open(LEDGER_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {"last_submission": None, "submitted_urls": {}}


def save_ledger(ledger: Dict[str, Any]) -> None:
    """Saves submission ledger."""
    os.makedirs(DATA_DIR, exist_ok=True)
    try:
        with open(LEDGER_PATH, "w", encoding="utf-8") as f:
            json.dump(ledger, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"⚠️ [IndexNow] 写入 ledger 失败: {e}")


def submit_urls_to_indexnow(urls: List[str], batch_size: int = 500) -> Dict[str, Any]:
    """Submits a list of URLs to the IndexNow endpoint in batches."""
    if not urls:
        print("ℹ️ [IndexNow] 没有待提交的 URL 列表。")
        return {"status": "skipped", "count": 0}

    now_iso = datetime.now(timezone.utc).isoformat()
    total_submitted = 0
    results = []

    for i in range(0, len(urls), batch_size):
        chunk = urls[i:i + batch_size]
        payload = {
            "host": INDEXNOW_HOST,
            "key": INDEXNOW_KEY,
            "keyLocation": INDEXNOW_KEY_LOCATION,
            "urlList": chunk
        }

        req = urllib.request.Request(
            INDEXNOW_ENDPOINT,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json; charset=utf-8"},
            method="POST"
        )

        try:
            with urllib.request.urlopen(req, timeout=15) as res:
                code = res.status
                msg = res.reason
                results.append({"code": code, "msg": msg, "count": len(chunk)})
                total_submitted += len(chunk)
                print(f"🚀 [IndexNow Batch {i//batch_size + 1}] 成功推送 {len(chunk)} 条 URL 到 Bing/IndexNow (状态码: {code} {msg})")
        except urllib.error.HTTPError as e:
            print(f"⚠️ [IndexNow Batch {i//batch_size + 1}] HTTP 响应: {e.code} {e.reason}")
            results.append({"code": e.code, "msg": e.reason, "count": 0})
        except Exception as e:
            print(f"⚠️ [IndexNow Batch {i//batch_size + 1}] 网络异常: {e}")
            results.append({"code": 0, "msg": str(e), "count": 0})

    ledger = load_ledger()
    ledger["last_submission"] = now_iso
    for u in urls[:total_submitted]:
        ledger["submitted_urls"][u] = now_iso
    save_ledger(ledger)

    return {
        "status": "success" if total_submitted > 0 else "error",
        "total_submitted": total_submitted,
        "batches": results
    }


def auto_submit_recent_or_all(submit_all: bool = False, max_urls: int = 500) -> Dict[str, Any]:
    """Automatically selects candidate URLs from sitemap and submits them."""
    all_urls = load_sitemap_urls()
    if not all_urls:
        print("⚠️ [IndexNow] 未从 sitemap.xml 发现任何有效 URL。")
        return {"status": "empty", "count": 0}

    ledger = load_ledger()
    submitted_set = set(ledger.get("submitted_urls", {}).keys())

    if submit_all:
        candidates = all_urls[:max_urls]
    else:
        # Submit newly discovered URLs first, plus homepages and daily index
        core_pinned = [
            f"https://{INDEXNOW_HOST}/",
            f"https://{INDEXNOW_HOST}/zh/",
            f"https://{INDEXNOW_HOST}/daily/",
            f"https://{INDEXNOW_HOST}/zh/daily/"
        ]
        unsubmitted = [u for u in all_urls if u not in submitted_set]
        # If all already submitted, pick the top 50 most recently updated
        if not unsubmitted:
            candidates = list(dict.fromkeys(core_pinned + all_urls[:50]))
        else:
            candidates = list(dict.fromkeys(core_pinned + unsubmitted))[:max_urls]

    print(f"📡 [IndexNow 实时索引] 正在准备推送 {len(candidates)} 条 URL 至 Bing 与 Microsoft Copilot...")
    return submit_urls_to_indexnow(candidates)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Submit URLs to Bing/IndexNow")
    parser.add_argument("--all", action="store_true", help="Submit all URLs from sitemap.xml")
    parser.add_argument("--max", type=int, default=500, help="Max URLs to submit")
    args = parser.parse_args()

    res = auto_submit_recent_or_all(submit_all=args.all, max_urls=args.max)
    print(f"✅ [IndexNow 完成] 总计推送: {res.get('total_submitted', 0)} 条 URL。")
