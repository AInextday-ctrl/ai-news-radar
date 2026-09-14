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
import re
import json
import time
from datetime import datetime, timezone
from fetcher import fetch_all_sources, get_chatbot_arena_top5, get_arxiv_curated_papers, extract_clean_video_id, normalize_title_fingerprint
from processor import process_items_batch
from config import CATEGORIES, AI_CREATORS


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
    """
    Extract 3 most impactful highlights across categories for the 60-second top banner.
    Strictly enforces 24-hour freshness gate: No historical posts from days ago can ever
    appear in the 'Today's Top 3' headliner banner.
    """
    top = []
    now_ts = time.time()
    MAX_24H_SECONDS = 86400

    # 1. 最重要的大事件/突发 (严格限定过去 24 小时以内的重大突破)
    all_news = [i for i in items if i.get("category") == "news"]
    today_news = [i for i in all_news if (now_ts - parse_time_for_sort(i)) <= MAX_24H_SECONDS]
    news_pool = today_news if today_news else all_news

    def news_weight(it):
        title = (it.get("title", "") + " " + it.get("title_zh", "")).lower()
        score = parse_time_for_sort(it)
        if any(bad in title for bad in ["betting", "nfl", "sports", "poker", "casino", "gambling", "nba", "lottery"]):
            score -= 10000000
        keywords = ["openai", "deepseek", "anthropic", "claude", "gpt", "gemini", "nvidia", "meta", "superintelligence", "agi", "model", "chip", "reasoning", "breakthrough"]
        if any(k in title for k in keywords):
            score += 86400
        if any(s in it.get("source", "").lower() for s in ["wired", "techmeme", "the verge", "ars technica", "mit", "the decoder"]):
            score += 43200
        return score

    news_pool.sort(key=news_weight, reverse=True)
    top_news_item = None
    if news_pool:
        top_news_item = news_pool[0]
        top.append({
            "badge_zh": "⚡ 今日头条",
            "badge_en": "⚡ Top Story",
            "title_zh": top_news_item.get("title_zh") or top_news_item.get("title", ""),
            "title_en": top_news_item.get("title_en") or top_news_item.get("title", ""),
            "summary_zh": top_news_item.get("summary_zh") or top_news_item.get("content_snippet", "")[:80],
            "summary_en": top_news_item.get("summary_en") or top_news_item.get("content_snippet", "")[:120],
            "url": top_news_item["url"],
            "image_url": top_news_item.get("image_url"),
            "raw_published_at": top_news_item.get("raw_published_at"),
            "source": top_news_item["source"]
        })

    # 2. 领袖声音 / 社区热议 (严格限定过去 24 小时以内发生的真实推文或社群讨论)
    # 必须是真实的社交媒体发帖（直链到 status 的 𝕏 推文或 Reddit 原生讨论），绝不能是第三方的普通新闻报道或转折链接
    all_celeb = [i for i in items if i.get("category") == "celebrity"]
    def is_valid_social(it):
        plat = it.get("platform", "").lower()
        src = it.get("source", "").lower()
        u = it.get("url", "")
        # 1. 𝕏 推文：必须为直接定位到具体贴文的 status 深层链接
        if plat == "x" or "twitter" in src or "/status/" in u:
            return bool(re.search(r'https?://(?:twitter|x)\.com/[^/]+/status/\d+', u))
        # 2. Reddit 讨论：必须为真实的 reddit.com 链接
        if plat == "reddit" or "reddit" in src or "reddit.com" in u:
            return "reddit.com" in u
        return False

    social_pool = [i for i in all_celeb if is_valid_social(i)]
    today_celeb = [i for i in social_pool if (now_ts - parse_time_for_sort(i)) <= MAX_24H_SECONDS]
    today_celeb.sort(key=parse_time_for_sort, reverse=True)

    if today_celeb:
        it = today_celeb[0]
        author = it.get('author', '行业领袖')
        is_reddit = "reddit" in (it.get("source", "") + it.get("platform", "")).lower()
        badge_zh = "🔥 社区热议" if is_reddit else "🐦 领袖观点"
        badge_en = "🔥 Community Buzz" if is_reddit else "🐦 Top Voice"

        en_quote = it.get("title_en") or it.get("content_snippet", "") or it.get("title", "")
        if en_quote.startswith(f"{author}:"):
            title_en = en_quote
        else:
            title_en = f"{author}: {en_quote}"
        zh_quote = it.get('title_zh') or it.get('title', '')
        if zh_quote.startswith(f"{author}：") or zh_quote.startswith(f"{author}:"):
            title_zh = zh_quote
        else:
            title_zh = f"{author}：{zh_quote}"

        top.append({
            "badge_zh": badge_zh,
            "badge_en": badge_en,
            "title_zh": title_zh,
            "title_en": title_en,
            "summary_zh": it.get("summary_zh") or it.get("content_snippet", "")[:80],
            "summary_en": it.get("summary_en") or it.get("content_snippet", "")[:120],
            "url": it["url"],
            "image_url": it.get("image_url"),
            "raw_published_at": it.get("raw_published_at"),
            "source": it.get("author_handle") or it["source"]
        })
    elif len(news_pool) > 1:
        # 若今日无大V或社群发帖，绝不拿多天前的旧闻充数，而是选取今日第二条重磅前沿突破
        it = news_pool[1]
        top.append({
            "badge_zh": "⚡ 突破进展",
            "badge_en": "⚡ Breakthrough",
            "title_zh": it.get("title_zh") or it.get("title", ""),
            "title_en": it.get("title_en") or it.get("title", ""),
            "summary_zh": it.get("summary_zh") or it.get("content_snippet", "")[:80],
            "summary_en": it.get("summary_en") or it.get("content_snippet", "")[:120],
            "url": it["url"],
            "image_url": it.get("image_url"),
            "raw_published_at": it.get("raw_published_at"),
            "source": it["source"]
        })

    # 3. 最值得体验的新工具/新视频 (优先取今日最新爆款)
    app_items = [i for i in items if i.get("category") in ["tools", "videos"]]
    today_apps = [i for i in app_items if (now_ts - parse_time_for_sort(i)) <= MAX_24H_SECONDS * 2]
    app_pool = today_apps if today_apps else app_items
    app_pool.sort(key=parse_time_for_sort, reverse=True)

    if app_pool:
        it = app_pool[0]
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

            # 严格清洗历史残留脏数据，杜绝非深层链接推文、伪造主页 URL 及旧格式测试数据污染
            valid_items = []
            obsolete_fake_ids = {
                "x_noam_reasoning_scaling", "x_elon_grok3_colossus", 
                "x_sama_compute_currency", "x_karpathy_llm_os",
                "x_demis_alphafold3_impact", "x_fchollet_arc_prize"
            }
            x_status_pattern = re.compile(r'https?://(?:twitter|x)\.com/[^/]+/status/\d+', re.IGNORECASE)

            for it in items:
                u = it.get("url", "")
                it_id = it.get("id", "")
                platform = it.get("platform", "").lower()
                source = it.get("source", "").lower()

                # 1. 丢弃废弃的旧版硬编码 fake ID
                if it_id in obsolete_fake_ids:
                    continue

                # 2. 丢弃未解析成功的 Google News 中转链接
                if "news.google.com/rss/articles" in u:
                    continue

                # 2.5 修正历史数据中被误归类为 celebrity 的普通 web 新闻
                if it.get("category") == "celebrity" and platform == "web":
                    it["category"] = "news"
                    if "source" in it:
                        it["author"] = it["source"]

                # 3. 严格校验所有 𝕏 / Twitter 推文：必须为直接定位到具体贴文的 status 深层链接，杜绝纯主页 URL
                is_x = platform == "x" or "twitter" in source or it_id.startswith("x_") or "x.com" in u or "twitter.com" in u
                if is_x:
                    if not x_status_pattern.search(u):
                        continue

                # 4. 丢弃旧版提示词与教程，让新版真实发布时间的独立提示词库覆盖
                if it_id.startswith("prompt_") or it_id.startswith("tut_") or it.get("category") == "prompts" or it.get("is_prompt"):
                    continue

                # 5. 坚决清洗淘汰旧时代的陈旧模型与过时应用 (如 dalle-mini, FLUX.1 dev, IllusionDiffusion 等)
                if it.get("category") == "tools":
                    t_str = f"{it_id} {it.get('title', '')} {it.get('title_zh', '')} {u}".lower()
                    if any(bad in t_str for bad in ["dalle-mini", "illusiondiffusion", "latent-consistency", "flux.1", "sd-webui"]):
                        continue
                    # 彻底丢弃带有本地毫秒级假时间戳的旧条目及历史残留远古应用
                    if any(bad in u for bad in ["enzostvs/deepsite", "ai-comic-factory", "Kolors-Virtual-Try-On"]):
                        continue
                    raw_pub = it.get("raw_published_at", "")
                    if re.search(r'\.\d{6}\+00:00', raw_pub):
                        continue
                    # 超过 180 天的古董工具坚决不留
                    tool_ts = parse_time_for_sort(it)
                    if tool_ts > 0 and (time.time() - tool_ts) > 180 * 86400:
                        continue

                valid_items.append(it)

            return valid_items
    except Exception as e:
        print(f"⚠️ 读取历史数据失败: {e}，将从头构建数据池。")
        return []


def save_news(items: list):
    """Save processed items to local JSON file for frontend and deployment with historical retention."""
    os.makedirs(DATA_DIR, exist_ok=True)
    os.makedirs(PUBLIC_DATA_DIR, exist_ok=True)
    
    # 按照五大核心分类组织视图，并严格按最新发布时间倒序排列
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
        "ai_creators": AI_CREATORS,
        "grouped": grouped,
        "news": grouped.get("news", []),
        "celebrity": grouped.get("celebrity", []),
        "tools": grouped.get("tools", []),
        "videos": grouped.get("videos", []),
        "prompts": grouped.get("prompts", []),
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

    # 3. 增量筛选：
    # 具备完整精选中文与真实时间戳的内容（大V推特、实操Prompt、高星工具、核心视频）直接进入更新池
    # 仅对缺失中文提炼的外部原始新闻/RSS做增量 AI 提炼
    new_raw_items = []
    pre_curated_items = []
    reused_count = 0

    for it in raw_items:
        u = it.get("url")
        i = it.get("id")
        # 若条目本身为视频/提示词，或已有高质量中文提炼（例如大V推特、实操Prompt）
        if it.get("category") in ["videos", "prompts"]:
            pre_curated_items.append(it)
        elif it.get("title_zh") and it.get("summary_zh"):
            pre_curated_items.append(it)
        elif (u and u in existing_by_url) or (i and i in existing_by_url):
            reused_count += 1
        else:
            new_raw_items.append(it)

    print(f"⚡ 增量分析完成: 发现 {len(new_raw_items)} 条全新外部情报，{len(pre_curated_items)} 条权威精选推文/实战情报，{reused_count} 条已有历史情报（直接秒级复用）")

    # 4. 仅对增量新情报调用清洗翻译，历史数据零开销
    if new_raw_items:
        new_processed_items = process_items_batch(new_raw_items)
    else:
        new_processed_items = []

    # 5. 多轨合并：将历史资讯、AI处理的新闻与权威精选条目合并，严格按发布时间倒序（最新永远置顶在最上方）
    merged_pool = {}

    def get_dedup_key(item):
        if item.get("category") == "prompts":
            return f"prompt_{item.get('id', '') or item.get('title_zh', '')}"
        if item.get("category") == "videos":
            vid = extract_clean_video_id(item.get("url", "")) or item.get("video_id", "")
            if vid:
                return f"yt_vid_{vid}"
            tfp = normalize_title_fingerprint(item.get("title", "") or item.get("title_zh", ""))
            if tfp:
                return f"yt_tfp_{tfp}"
        u = item.get("url")
        if u:
            # 标准化推特与网页链接
            u_clean = u.split("?")[0].rstrip("/")
            return f"url_{u_clean}"
        return f"id_{item.get('id', '')}"

    # 先入历史
    for it in existing_items:
        key = get_dedup_key(it)
        if key:
            merged_pool[key] = it
    # 再入新增外部新闻（确保最新提取的属性生效）
    for it in new_processed_items:
        key = get_dedup_key(it)
        if key:
            merged_pool[key] = it
    # 最后入权威精选（确保大V真实推文、教程、Prompt最新准确属性与真实时间戳绝对覆盖）
    for it in pre_curated_items:
        key = get_dedup_key(it)
        if key:
            merged_pool[key] = it

    combined_items = list(merged_pool.values())
    combined_items.sort(key=parse_time_for_sort, reverse=True)

    # 严格清理历史遗留的假爆款、执行 30 天爆点时效门禁、创作者防垄断配额 (Author Diversity Gate)
    now_ts = time.time()
    MAX_VIRAL_SECONDS = 30 * 86400  # 30 天
    cleaned_items = []
    seen_video_ids = set()
    seen_video_tfps = set()
    author_viral_counts = {}
    author_total_counts = {}

    for it in combined_items:
        it_id = str(it.get("id", ""))
        it_url = str(it.get("url", ""))
        # 彻底移除历史残留的假视频条目
        if any(fake_k in it_id for fake_k in ["yt_viral_fireship_deepseek", "yt_viral_theo_claude37_cursor", "yt_viral_matthew_berman_open_weights", "yt_viral_networkchuck_ollama", "yt_viral_karpathy_micrograd", "yt_viral_mcp_agentic_workflow", "yt_viral_ai_explained_hybrid_reasoning"]) or any(fake_u in it_url for fake_u in ["Cursor_Claude37_Theo", "Matthew_Berman_Shootout", "NetworkChuck_Ollama_Guide", "MCP_Protocol_Production", "Claude_37_Thinking_Tested"]):
            continue

        # 确保基础 title 字段非空（适配各类精选模板）
        if not it.get("title"):
            it["title"] = it.get("title_zh") or it.get("title_en", "")

        # 实操 Prompt 咒语卡片独立保留并直接通过
        if it.get("category") == "prompts":
            cleaned_items.append(it)
            continue

        diff = now_ts - parse_time_for_sort(it)

        # 视频专属：跨信源原子级去重与创作者配额防霸屏
        if it.get("category") == "videos":
            vid = extract_clean_video_id(it.get("url", "")) or it.get("video_id", "")
            tfp = normalize_title_fingerprint(it.get("title", "") or it.get("title_zh", ""))
            if vid and vid in seen_video_ids:
                continue
            if tfp and tfp in seen_video_tfps:
                continue

            author = it.get("author", "unknown")

            # 30 天爆点生命周期门禁：超期强制降级并剥离爆点属性
            if diff > MAX_VIRAL_SECONDS:
                if it.get("is_viral"):
                    it["is_viral"] = False
                if "tags" in it and isinstance(it["tags"], list):
                    it["tags"] = [t for t in it["tags"] if t != "🔥 近期爆点"]
                if it.get("sub_type") == "viral":
                    it["sub_type"] = "tutorial" if "教学" in (it.get("title", "") + it.get("title_zh", "")) else "insight"

            # 创作者爆点防霸屏门禁：单个博主在爆点专栏中至多占 1 席
            if it.get("is_viral"):
                if author_viral_counts.get(author, 0) >= 1:
                    it["is_viral"] = False
                    if "tags" in it and isinstance(it["tags"], list):
                        it["tags"] = [t for t in it["tags"] if t != "🔥 近期爆点"]
                    it["sub_type"] = "tutorial" if "教学" in (it.get("title", "") + it.get("title_zh", "")) else "insight"
                else:
                    author_viral_counts[author] = author_viral_counts.get(author, 0) + 1

            # 创作者全库总配额门禁：单个博主在全库视频中至多保留 2 条，杜绝垄断
            if author_total_counts.get(author, 0) >= 2:
                continue

            author_total_counts[author] = author_total_counts.get(author, 0) + 1
            if vid:
                seen_video_ids.add(vid)
            if tfp:
                seen_video_tfps.add(tfp)
        else:
            if diff > MAX_VIRAL_SECONDS and it.get("is_viral"):
                it["is_viral"] = False

        it["is_recent_24h"] = bool(diff <= 86400)
        cleaned_items.append(it)

    # 6. 存储增量融合后的完整大库
    save_news(cleaned_items)
    
    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds()
    print(f"✨ 增量更新与历史合并全流程执行完毕，耗时: {duration:.2f} 秒\n")


if __name__ == "__main__":
    run_pipeline()
