"""
Main pipeline entrypoint 2.0 - Coordinates fetching, Gemini processing, Top 3 digest, and output saving.
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


def extract_top_three(items: list) -> list:
    """Extract 3 most impactful highlights across categories for the 60-second top banner."""
    top = []
    
    # 1. 最重要的大事件/突发
    news_items = [i for i in items if i.get("category") == "news" and i.get("image_url")]
    if news_items:
        top.append({
            "badge": "⚡ 今日头条",
            "title": news_items[0].get("title_zh") or news_items[0]["title"],
            "summary": news_items[0].get("summary_zh") or news_items[0]["content_snippet"][:80],
            "url": news_items[0]["url"],
            "source": news_items[0]["source"]
        })

    # 2. 最重磅的领袖声音
    celeb_items = [i for i in items if i.get("category") == "celebrity"]
    if celeb_items:
        top.append({
            "badge": "🐦 领袖观点",
            "title": f"{celeb_items[0].get('author', '行业领袖')}：{celeb_items[0].get('title_zh') or celeb_items[0]['title']}",
            "summary": celeb_items[0].get("summary_zh") or celeb_items[0]["content_snippet"][:80],
            "url": celeb_items[0]["url"],
            "source": celeb_items[0].get("author_handle") or celeb_items[0]["source"]
        })

    # 3. 最值得体验的新工具/新视频
    app_items = [i for i in items if i.get("category") in ["tools", "videos"] and (i.get("image_url") or i.get("video_id"))]
    if app_items:
        top.append({
            "badge": "🛠️ 爆款尝鲜",
            "title": app_items[0].get("title_zh") or app_items[0]["title"],
            "summary": app_items[0].get("summary_zh") or app_items[0]["content_snippet"][:80],
            "url": app_items[0]["url"],
            "source": app_items[0]["source"]
        })

    return top


def save_news(items: list):
    """Save processed items to local JSON file for frontend and deployment."""
    os.makedirs(DATA_DIR, exist_ok=True)
    os.makedirs(PUBLIC_DATA_DIR, exist_ok=True)
    
    # 按照四大核心分类组织视图
    grouped = {cat_key: [] for cat_key in CATEGORIES}
    for item in items:
        cat = item.get("category", "news")
        if cat not in grouped:
            cat = "news"
        grouped[cat].append(item)

    # 提炼今日 60 秒极速风向标 (Top 3)
    top_three = extract_top_three(items)

    payload = {
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "total_count": len(items),
        "categories": CATEGORIES,
        "top_three": top_three,
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
    print(f"  🔥 今日必读 60s Top 3: {len(top_three)} 条")
    print("=" * 60)


def run_pipeline():
    start_time = datetime.now()
    print("=" * 60)
    print(f"🕒 AI 资讯雷达 2.0 启动: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    # 1. 抓取多渠道资讯 (视频/工具/名人大V/新闻)
    raw_items = fetch_all_sources()
    if not raw_items:
        print("⚠️ 未抓取到任何数据，请检查网络连接或源配置。")
        return

    # 2. 借助 Gemini 进行清洗、摘要和分类 (带自动中文翻译容错)
    processed_items = process_items_batch(raw_items)

    # 3. 存储结果
    save_news(processed_items)
    
    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds()
    print(f"✨ 全流程执行完毕，耗时: {duration:.2f} 秒\n")


if __name__ == "__main__":
    run_pipeline()
