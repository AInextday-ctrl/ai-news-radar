"""
Main pipeline entrypoint - Coordinates fetching, Gemini processing, and output saving.
"""

import sys

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

import os

import json
from datetime import datetime, timezone
from fetcher import fetch_all_sources
from processor import process_items_batch
from config import CATEGORIES

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
PUBLIC_DATA_DIR = os.path.join(os.path.dirname(__file__), "public", "data")
OUTPUT_FILE = os.path.join(DATA_DIR, "latest_news.json")
PUBLIC_OUTPUT_FILE = os.path.join(PUBLIC_DATA_DIR, "latest_news.json")


def save_news(items: list):
    """Save processed items to local JSON file for frontend and local inspection."""
    os.makedirs(DATA_DIR, exist_ok=True)
    os.makedirs(PUBLIC_DATA_DIR, exist_ok=True)
    
    # 按照分类组织视图
    grouped = {cat_key: [] for cat_key in CATEGORIES}
    for item in items:
        cat = item.get("category", "news")
        if cat not in grouped:
            cat = "news"
        grouped[cat].append(item)

    payload = {
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "total_count": len(items),
        "categories": CATEGORIES,
        "grouped": grouped,
        "items": items
    }

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)

    with open(PUBLIC_OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)

    print(f"\n💾 数据已成功保存在: {OUTPUT_FILE} 及 {PUBLIC_OUTPUT_FILE}")
    print("=" * 60)
    for cat_key, cat_val in CATEGORIES.items():
        count = len(grouped[cat_key])
        name = cat_val.get("zh", cat_key) if isinstance(cat_val, dict) else cat_val
        print(f"  {name}: {count} 条")
    print("=" * 60)


def run_pipeline():
    start_time = datetime.now()
    print("=" * 60)
    print(f"🕒 AI 资讯雷达启动: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    # 1. 抓取多渠道资讯
    raw_items = fetch_all_sources()
    if not raw_items:
        print("⚠️ 未抓取到任何数据，请检查网络连接或源配置。")
        return

    # 2. 借助 Gemini 进行清洗、摘要和分类
    processed_items = process_items_batch(raw_items)

    # 3. 存储结果
    save_news(processed_items)
    
    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds()
    print(f"✨ 全流程执行完毕，耗时: {duration:.2f} 秒\n")


if __name__ == "__main__":
    run_pipeline()
