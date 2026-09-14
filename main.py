"""
Main pipeline entrypoint 2.0 - Coordinates fetching, Gemini processing, Top 3 digest, and output saving.
"""

import sys

try:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8")
except Exception:
    pass

import os
import json
from datetime import datetime, timezone
from fetcher import fetch_all_sources, get_chatbot_arena_top5, get_arxiv_curated_papers
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
        if any(bad in title for bad in ["betting", "nfl", "sports", "poker", "casino", "gambling", "nba", "lottery"]):
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
            "title_zh": it.get("title_zh") or it.get("title", ""),
            "title_en": it.get("title_en") or it.get("title", ""),
            "summary_zh": it.get("summary_zh") or it.get("content_snippet", "")[:80],
            "summary_en": it.get("summary_en") or it.get("content_snippet", "")[:120],
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
        en_quote = it.get("title_en") or it.get("content_snippet", "") or it.get("title", "")
        # 如果 en_quote 带有 Author: 前缀，避免重复
        if en_quote.startswith(f"{author}:"):
            title_en = en_quote
        else:
            title_en = f"{author}: {en_quote}"
        top.append({
            "badge_zh": "🐦 领袖观点",
            "badge_en": "🐦 Top Voice",
            "title_zh": f"{author}：{it.get('title_zh') or it.get('title', '')}",
            "title_en": title_en,
            "summary_zh": it.get("summary_zh") or it.get("content_snippet", "")[:80],
            "summary_en": it.get("summary_en") or it.get("content_snippet", "")[:120],
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
            "title_zh": it.get("title_zh") or it.get("title", ""),
            "title_en": it.get("title_en") or it.get("title", ""),
            "summary_zh": it.get("summary_zh") or it.get("content_snippet", "")[:80],
            "summary_en": it.get("summary_en") or it.get("content_snippet", "")[:120],
            "url": it["url"],
            "image_url": it.get("image_url"),
            "raw_published_at": it.get("raw_published_at"),
            "source": it["source"]
        })

    return top


def load_existing_items() -> list:
    """Load previously saved news items from JSON to support incremental updates and history retention."""
    target_file = PUBLIC_OUTPUT_FILE if os.path.exists(PUBLIC_OUTPUT_FILE) else OUTPUT_FILE
    if not os.path.exists(target_file):
        return []
    try:
        with open(target_file, "r", encoding="utf-8") as f:
            data = json.load(f)
            # 优先从 items 取，次优从 grouped 展平
            items = data.get("items", [])
            if not items and "grouped" in data:
                for cat_items in data["grouped"].values():
                    items.extend(cat_items)
            return items or []
    except Exception as e:
        print(f"⚠️ 读取历史数据失败: {e}，将从头构建数据池。")
        return []


def save_news(items: list):
    """Save processed items to local JSON file for frontend and deployment with historical retention."""
    os.makedirs(DATA_DIR, exist_ok=True)
    os.makedirs(PUBLIC_DATA_DIR, exist_ok=True)
    
    # 按照四大核心分类组织视图，并严格按最新发布时间倒序排列
    grouped = {cat_key: [] for cat_key in CATEGORIES}
    for item in items:
        cat = item.get("category", "news")
        if cat not in grouped:
            cat = "news"
        # 各分类保留最多 200 条高质量深度历史情报
        if len(grouped[cat]) < 200:
            grouped[cat].append(item)

    for cat_key in grouped:
        grouped[cat_key].sort(key=parse_time_for_sort, reverse=True)

    # 重新聚合去重后的有效项目池
    final_items = []
    for cat_key in grouped:
        final_items.extend(grouped[cat_key])
    final_items.sort(key=parse_time_for_sort, reverse=True)

    # 提炼今日 60 秒极速风向标 (Top 3)
    top_three = extract_top_three(final_items)

    # 载入发烧友必备基准：LMSYS Arena Top 5 与 ArXiv 前沿突破论文
    chatbot_arena = get_chatbot_arena_top5()
    arxiv_papers = get_arxiv_curated_papers()

    payload = {
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "total_count": len(final_items),
        "categories": CATEGORIES,
        "top_three": top_three,
        "chatbot_arena": chatbot_arena,
        "arxiv_papers": arxiv_papers,
        "grouped": grouped,
        "news": grouped.get("news", []),
        "celebrity": grouped.get("celebrity", []),
        "tools": grouped.get("tools", []),
        "videos": grouped.get("videos", []),
        "industry_news": grouped.get("news", []),
        "leader_opinions": grouped.get("celebrity", []),
        "applied_tools": grouped.get("tools", []),
        "video_prompts": grouped.get("videos", []),
        "items": final_items
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
    print(f"🕒 AI 资讯雷达 增量更新启动: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    # 1. 载入已有历史资讯池以支持增量合并
    existing_items = load_existing_items()
    existing_by_url = {}
    for it in existing_items:
        url = it.get("url")
        if url:
            existing_by_url[url] = it
        item_id = it.get("id")
        if item_id:
            existing_by_url[item_id] = it
    print(f"📦 已载入历史资讯池: {len(existing_items)} 条 (已建立增量比对索引)")

    # 2. 抓取多渠道全网最新资讯 (视频/工具/名人大V/新闻/当天爆款推文)
    raw_items = fetch_all_sources()
    if not raw_items:
        print("⚠️ 未抓取到任何数据，请检查网络连接或源配置。")
        return

    # 3. 增量筛选：分离出真正的新增条目 vs 历史已有条目
    new_raw_items = []
    reused_count = 0
    for it in raw_items:
        u = it.get("url")
        i = it.get("id")
        # 如果已经存在且已有中文提炼，直接复用已有结果
        if (u and u in existing_by_url) or (i and i in existing_by_url):
            reused_count += 1
        else:
            new_raw_items.append(it)

    print(f"⚡ 增量分析完成: 发现 {len(new_raw_items)} 条全新情报，{reused_count} 条已有历史情报（直接秒级复用）")

    # 4. 仅对增量新情报调用清洗翻译，历史数据零开销
    if new_raw_items:
        new_processed_items = process_items_batch(new_raw_items)
    else:
        new_processed_items = []

    # 5. 双轨合并：将新资讯与历史资讯合并，严格按发布时间倒序（最新永远置顶在最上方）
    merged_pool = {}
    # 先入历史
    for it in existing_items:
        key = it.get("url") or it.get("id")
        if key:
            merged_pool[key] = it
    # 再入新增（确保最新提取的属性生效）
    for it in new_processed_items:
        key = it.get("url") or it.get("id")
        if key:
            merged_pool[key] = it

    combined_items = list(merged_pool.values())
    combined_items.sort(key=parse_time_for_sort, reverse=True)

    # 6. 存储增量融合后的完整大库
    save_news(combined_items)
    
    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds()
    print(f"✨ 增量更新与历史合并全流程执行完毕，耗时: {duration:.2f} 秒\n")


if __name__ == "__main__":
    run_pipeline()
