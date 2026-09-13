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


def parse_time_for_sort(it):
    raw = it.get("raw_published_at", "")
    if not raw:
        return 0
    try:
        return datetime.fromisoformat(raw.replace("Z", "+00:00")).timestamp()
    except Exception:
        return 0


def extract_top_three(items: list) -> list:
    """Extract 3 most impactful highlights across categories for the 60-second top banner."""
    top = []
    
    # 1. 最重要的大事件/突发 (优先前沿重大模型与技术突破)
    news_items = [i for i in items if i.get("category") == "news"]
    
    def news_weight(it):
        title = (it.get("title", "") + " " + it.get("title_zh", "")).lower()
        score = parse_time_for_sort(it)
        # 降权非纯 AI 科技突破（如纯体育博彩下注等）
        if any(bad in title for bad in ["betting", "nfl", "sports", "poker", "casino", "gambling"]):
            score -= 10000000
        # 优先重大模型/架构/领袖公司突破
        keywords = ["openai", "deepseek", "anthropic", "claude", "gpt", "gemini", "nvidia", "meta", "superintelligence", "agi", "model", "chip", "reasoning", "breakthrough"]
        if any(k in title for k in keywords):
            score += 86400
        if any(s in it.get("source", "").lower() for s in ["wired", "techmeme", "the verge", "ars technica", "mit", "the decoder"]):
            score += 43200
        return score

    news_items.sort(key=news_weight, reverse=True)
    if news_items:
        it = news_items[0]
        top.append({
            "badge_zh": "⚡ 今日头条",
            "badge_en": "⚡ Top Story",
            "title_zh": it.get("title_zh") or it["title"],
            "title_en": it["title"],
            "summary_zh": it.get("summary_zh") or it["content_snippet"][:80],
            "summary_en": it["content_snippet"][:80],
            "url": it["url"],
            "image_url": it.get("image_url"),
            "raw_published_at": it.get("raw_published_at"),
            "source": it["source"]
        })

    # 2. 最重磅的领袖声音 (严格取最新的领袖推文/言论)
    celeb_items = [i for i in items if i.get("category") == "celebrity"]
    celeb_items.sort(key=parse_time_for_sort, reverse=True)
    if celeb_items:
        it = celeb_items[0]
        author = it.get('author', '行业领袖')
        top.append({
            "badge_zh": "🐦 领袖观点",
            "badge_en": "🐦 Top Voice",
            "title_zh": f"{author}：{it.get('title_zh') or it['title']}",
            "title_en": f"{author}: {it['title']}",
            "summary_zh": it.get("summary_zh") or it["content_snippet"][:80],
            "summary_en": it["content_snippet"][:80],
            "url": it["url"],
            "image_url": it.get("image_url"),
            "raw_published_at": it.get("raw_published_at"),
            "source": it.get("author_handle") or it["source"]
        })

    # 3. 最值得体验的新工具/新视频 (优先取今日最新爆款)
    app_items = [i for i in items if i.get("category") in ["tools", "videos"]]
    app_items.sort(key=parse_time_for_sort, reverse=True)
    if app_items:
        it = app_items[0]
        top.append({
            "badge_zh": "🛠️ 爆款尝鲜",
            "badge_en": "🛠️ Try It Out",
            "title_zh": it.get("title_zh") or it["title"],
            "title_en": it["title"],
            "summary_zh": it.get("summary_zh") or it["content_snippet"][:80],
            "summary_en": it["content_snippet"][:80],
            "url": it["url"],
            "image_url": it.get("image_url"),
            "raw_published_at": it.get("raw_published_at"),
            "source": it["source"]
        })

    return top


def save_news(items: list):
    """Save processed items to local JSON file for frontend and deployment."""
    os.makedirs(DATA_DIR, exist_ok=True)
    os.makedirs(PUBLIC_DATA_DIR, exist_ok=True)
    
    # 按照四大核心分类组织视图，并严格按最新发布时间倒序排列
    grouped = {cat_key: [] for cat_key in CATEGORIES}
    for item in items:
        cat = item.get("category", "news")
        if cat not in grouped:
            cat = "news"
        grouped[cat].append(item)

    for cat_key in grouped:
        grouped[cat_key].sort(key=parse_time_for_sort, reverse=True)

    # 提炼今日 60 秒极速风向标 (Top 3)
    top_three = extract_top_three(items)

    payload = {
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "total_count": len(items),
        "categories": CATEGORIES,
        "top_three": top_three,
        "grouped": grouped,
        "news": grouped.get("news", []),
        "celebrity": grouped.get("celebrity", []),
        "tools": grouped.get("tools", []),
        "videos": grouped.get("videos", []),
        "industry_news": grouped.get("news", []),
        "leader_opinions": grouped.get("celebrity", []),
        "applied_tools": grouped.get("tools", []),
        "video_prompts": grouped.get("videos", []),
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
