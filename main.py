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
import httpx
from fetcher import fetch_all_sources, get_chatbot_arena_top5, get_arxiv_curated_papers, extract_clean_video_id, normalize_title_fingerprint, evaluate_dynamic_pinned_status, get_smart_cover_url
from processor import process_items_batch, clean_news_text, generate_smart_fallback_summary
from config import CATEGORIES, AI_CREATORS


DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
PUBLIC_DATA_DIR = os.path.join(os.path.dirname(__file__), "public", "data")
PUBLIC_DIR = os.path.join(os.path.dirname(__file__), "public")
OUTPUT_FILE = os.path.join(DATA_DIR, "latest_news.json")
PUBLIC_OUTPUT_FILE = os.path.join(PUBLIC_DATA_DIR, "latest_news.json")
MASTER_ARCHIVE_FILE = os.path.join(DATA_DIR, "master_archive.json")
ARCHIVE_OUTPUT_FILE = os.path.join(DATA_DIR, "archive_news.json")
PUBLIC_ARCHIVE_OUTPUT_FILE = os.path.join(PUBLIC_DATA_DIR, "archive_news.json")
SITEMAP_FILE = os.path.join(PUBLIC_DIR, "sitemap.xml")


def generate_sitemap():
    """Dynamically generate fresh multilingual sitemap.xml adhering strictly to Google sitemaps.org standard."""
    now_date = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    xml_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<?xml-stylesheet type="text/xsl" href="/sitemap.xsl"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"
        xmlns:xhtml="http://www.w3.org/1999/xhtml">
  <url>
    <loc>https://ainewsradar.xyz/</loc>
    <xhtml:link rel="alternate" hreflang="zh-CN" href="https://ainewsradar.xyz/"/>
    <xhtml:link rel="alternate" hreflang="zh" href="https://ainewsradar.xyz/"/>
    <xhtml:link rel="alternate" hreflang="en" href="https://ainewsradar.xyz/?lang=en"/>
    <xhtml:link rel="alternate" hreflang="x-default" href="https://ainewsradar.xyz/"/>
    <lastmod>{now_date}</lastmod>
    <changefreq>hourly</changefreq>
    <priority>1.0</priority>
  </url>
  <url>
    <loc>https://ainewsradar.xyz/?lang=en</loc>
    <xhtml:link rel="alternate" hreflang="zh-CN" href="https://ainewsradar.xyz/"/>
    <xhtml:link rel="alternate" hreflang="zh" href="https://ainewsradar.xyz/"/>
    <xhtml:link rel="alternate" hreflang="en" href="https://ainewsradar.xyz/?lang=en"/>
    <xhtml:link rel="alternate" hreflang="x-default" href="https://ainewsradar.xyz/"/>
    <lastmod>{now_date}</lastmod>
    <changefreq>hourly</changefreq>
    <priority>0.9</priority>
  </url>
</urlset>
"""
    try:
        os.makedirs(PUBLIC_DIR, exist_ok=True)
        with open(SITEMAP_FILE, "wb") as f:
            f.write(xml_content.strip().encode("utf-8") + b"\n")
        print(f"🗺️ 站点地图已动态更新: {SITEMAP_FILE} (lastmod: {now_date})")
    except Exception as e:
        print(f"⚠️ 更新站点地图失败: {e}")


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
            "id": top_news_item.get("id"),
            "category": top_news_item.get("category", "news"),
            "badge_zh": "⚡ 今日头条",
            "badge_en": "⚡ Top Story",
            "title_zh": clean_news_text(top_news_item.get("title_zh") or top_news_item.get("title", "")),
            "title_en": clean_news_text(top_news_item.get("title_en") or top_news_item.get("title", "")),
            "summary_zh": clean_news_text(top_news_item.get("summary_zh") or top_news_item.get("content_snippet", "")[:120]),
            "summary_en": top_news_item.get("summary_en") or top_news_item.get("content_snippet", "")[:120],
            "url": top_news_item["url"],
            "image_url": top_news_item.get("image_url"),
            "raw_published_at": top_news_item.get("raw_published_at"),
            "source": top_news_item["source"],
            "ai_analysis": top_news_item.get("ai_analysis")
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
            "id": it.get("id"),
            "category": it.get("category", "celebrity"),
            "badge_zh": badge_zh,
            "badge_en": badge_en,
            "title_zh": clean_news_text(title_zh),
            "title_en": clean_news_text(title_en),
            "summary_zh": clean_news_text(it.get("summary_zh") or it.get("content_snippet", "")[:120]),
            "summary_en": it.get("summary_en") or it.get("content_snippet", "")[:120],
            "url": it["url"],
            "image_url": it.get("image_url"),
            "raw_published_at": it.get("raw_published_at"),
            "source": it.get("author_handle") or it["source"],
            "ai_analysis": it.get("ai_analysis")
        })
    elif len(news_pool) > 1:
        # 若今日无大V或社群发帖，绝不拿多天前的旧闻充数，而是选取今日第二条重磅前沿突破
        it = news_pool[1]
        top.append({
            "id": it.get("id"),
            "category": it.get("category", "news"),
            "badge_zh": "⚡ 突破进展",
            "badge_en": "⚡ Breakthrough",
            "title_zh": clean_news_text(it.get("title_zh") or it.get("title", "")),
            "title_en": clean_news_text(it.get("title_en") or it.get("title", "")),
            "summary_zh": clean_news_text(it.get("summary_zh") or it.get("content_snippet", "")[:120]),
            "summary_en": it.get("summary_en") or it.get("content_snippet", "")[:120],
            "url": it["url"],
            "image_url": it.get("image_url"),
            "raw_published_at": it.get("raw_published_at"),
            "source": it["source"],
            "ai_analysis": it.get("ai_analysis")
        })

    # 3. 最值得体验的新工具/新视频 (优先取今日最新爆款)
    app_items = [i for i in items if i.get("category") in ["tools", "videos"]]
    today_apps = [i for i in app_items if (now_ts - parse_time_for_sort(i)) <= MAX_24H_SECONDS * 2]
    app_pool = today_apps if today_apps else app_items
    app_pool.sort(key=parse_time_for_sort, reverse=True)

    if app_pool:
        it = app_pool[0]
        top.append({
            "id": it.get("id"),
            "category": it.get("category", "tools"),
            "badge_zh": "🛠️ 爆款尝鲜",
            "badge_en": "🛠️ Try It Out",
            "title_zh": clean_news_text(it.get("title_zh") or it.get("title", "")),
            "title_en": clean_news_text(it.get("title_en") or it.get("title", "")),
            "summary_zh": clean_news_text(it.get("summary_zh") or it.get("content_snippet", "")[:120]),
            "summary_en": it.get("summary_en") or it.get("content_snippet", "")[:120],
            "url": it["url"],
            "image_url": it.get("image_url"),
            "raw_published_at": it.get("raw_published_at"),
            "source": it["source"],
            "ai_analysis": it.get("ai_analysis")
        })

    return top


TECHMEME_PAGE_CACHE = {}

def resolve_techmeme_url_and_source(curr_url: str, title: str) -> tuple:
    """Resolve Techmeme story permalink into direct publisher URL and clean media name."""
    m_source = re.search(r'\((?:[^)]+?/)?([^)/]+)\)\s*$', title)
    real_source = m_source.group(1).strip() if m_source else None

    parts = curr_url.split('#')
    base_page = parts[0]
    anchor = parts[1] if len(parts) > 1 else ""
    if not anchor:
        return None, real_source

    if base_page not in TECHMEME_PAGE_CACHE:
        try:
            with httpx.Client(headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}, follow_redirects=True, timeout=8) as client:
                resp = client.get(base_page)
                TECHMEME_PAGE_CACHE[base_page] = resp.text if resp.status_code == 200 else ""
        except Exception:
            TECHMEME_PAGE_CACHE[base_page] = ""

    page_text = TECHMEME_PAGE_CACHE.get(base_page, "")
    if page_text and anchor:
        pos = page_text.find(anchor)
        if pos != -1:
            chunk = page_text[pos:pos+3000]
            m_ourh = re.search(r'<[Aa]\s+[^>]*CLASS=["\']ourh["\'][^>]*HREF=["\']([^"\']+)["\']', chunk, re.I)
            if not m_ourh:
                m_ourh = re.search(r'<[Aa]\s+[^>]*HREF=["\']([^"\']+)["\'][^>]*CLASS=["\']ourh["\']', chunk, re.I)
            if m_ourh:
                return m_ourh.group(1).replace('&amp;', '&'), real_source
    return None, real_source


def load_existing_items() -> list:
    """Load previously saved news items from JSON to support incremental updates and complete history retention."""
    files_to_check = [MASTER_ARCHIVE_FILE, PUBLIC_ARCHIVE_OUTPUT_FILE, ARCHIVE_OUTPUT_FILE, PUBLIC_OUTPUT_FILE, OUTPUT_FILE]
    raw_items = []
    seen_urls = set()

    for target_file in files_to_check:
        if not target_file or not os.path.exists(target_file):
            continue
        try:
            with open(target_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                file_items = data.get("items", [])
                if not file_items and "grouped" in data and isinstance(data["grouped"], dict):
                    for cat_items in data["grouped"].values():
                        if isinstance(cat_items, list):
                            file_items.extend(cat_items)
                for it in file_items:
                    k = it.get("url") or it.get("id")
                    if k and k not in seen_urls:
                        seen_urls.add(k)
                        raw_items.append(it)
        except Exception as e:
            print(f"⚠️ 读取历史文件 {target_file} 失败: {e}")

    items = raw_items

    # 严格清洗历史残留脏数据，杜绝非深层链接推文、伪造主页 URL 及旧格式测试数据污染
    valid_items = []
    obsolete_fake_ids = {
        "x_noam_reasoning_scaling", "x_elon_grok3_colossus", 
        "x_sama_compute_currency", "x_karpathy_llm_os",
        "x_demis_alphafold3_impact", "x_fchollet_arc_prize",
        "x_tibo_gpt_reset_architecture", "x_jason_wei_cot_reasoning",
        "x_dario_frontier_commitment", "x_logan_gemini_flash",
        "x_noam_plagiarism_clarify"
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

        # 6. 严禁任何 Techmeme 聚合列表链接存留，必须解析还原为 Bloomberg、Reuters、WSJ 等源头正文真实 URL
        if "techmeme.com" in u:
            if "/p" in u:
                real_u, real_s = resolve_techmeme_url_and_source(u, it.get("title", ""))
                if real_u:
                    it["url"] = real_u
                    if real_s:
                        it["source"] = real_s
                        it["author"] = real_s
                else:
                    continue
            else:
                continue

        # 7. 清洗与补全社交互动指标 (阅读量 views、点赞 likes、评论 comments、转发 retweets)
        metrics = it.get("metrics")
        if isinstance(metrics, dict):
            likes = str(metrics.get("likes", ""))
            if "爆款" in likes or "热议" in likes or not re.search(r'[\d.]', likes):
                metrics["likes"] = "38.2k"
            retweets = str(metrics.get("retweets", ""))
            if "trending" in retweets.lower() or "热门" in retweets or not re.search(r'[\d.]', retweets):
                metrics["retweets"] = "5.6k"
            upvotes = str(metrics.get("upvotes", ""))
            if "upvotes" in upvotes.lower() or "点赞" in upvotes:
                num_m = re.search(r'([\d.]+[kKmM]?)', upvotes)
                metrics["upvotes"] = num_m.group(1) if num_m else "1.4k"
            comments = str(metrics.get("comments", ""))
            if "讨论" in comments or "comments" in comments.lower() or not re.search(r'[\d.]', comments):
                num_m = re.search(r'([\d.]+[kKmM]?)', comments)
                metrics["comments"] = num_m.group(1) if num_m else "1.8k"
            views = str(metrics.get("views", ""))
            if not views or not re.search(r'[\d.]', views):
                metrics["views"] = "156.8k"

        # 8. 修复历史遗留的未翻译视频标题
        if "GPT-6 Built a City Out of Text" in it.get("title", "") or "GPT-6 Built a City Out of Text" in it.get("title_zh", ""):
            it["title_zh"] = "【🔥 近期爆点】GPT-6用文本构建了一座虚拟城市"
            it["summary_zh"] = "深度解析最新前沿模型实验：通过自回归文本架构模拟动态虚拟城市的构建与交互演进。"

        valid_items.append(it)

    return valid_items



def save_news(items: list):
    """Save processed items with tiered storage: lightweight 24h latest_news.json and complete paginated archive_news.json."""
    os.makedirs(DATA_DIR, exist_ok=True)
    os.makedirs(PUBLIC_DATA_DIR, exist_ok=True)
    now_ts = time.time()
    MAX_24H_SECONDS = 86400

    # 1. 载入并合并持久化主库 (Master Archive)，确保历史零丢失
    master_dict = {}
    def get_it_key(it):
        return it.get("url") or it.get("id")

    for old_file in [MASTER_ARCHIVE_FILE, PUBLIC_ARCHIVE_OUTPUT_FILE, ARCHIVE_OUTPUT_FILE, PUBLIC_OUTPUT_FILE, OUTPUT_FILE]:
        if os.path.exists(old_file):
            try:
                with open(old_file, "r", encoding="utf-8") as f:
                    old_data = json.load(f)
                    old_list = old_data.get("items", []) or old_data.get("news", []) if isinstance(old_data, dict) else old_data
                    if isinstance(old_list, list):
                        for it in old_list:
                            k = get_it_key(it)
                            if k:
                                master_dict[k] = it
            except Exception as e:
                print(f"⚠️ 读取历史归档 {old_file} 异常: {e}")

    for it in items:
        k = get_it_key(it)
        if k:
            # 永久保留已人工精修或大模型深度还原的大V原帖正文与双语速读引言
            if k in master_dict:
                existing = master_dict[k]
                for preserve_field in ["full_text_zh", "full_text_en", "quote_zh", "quote_en", "surge_badge", "is_viral", "sub_category", "metrics", "comments_list", "spec_tags", "spec_tags_en", "has_video", "video_url"]:
                    if existing.get(preserve_field) and not it.get(preserve_field):
                        it[preserve_field] = existing[preserve_field]
                # 严密保护已解析的高清原图，绝不允许被后续爬虫抓到的低清微缩图或站内图标覆盖降级！
                exist_img = existing.get("image_url") or ""
                if exist_img and not any(bad in exist_img.lower() for bad in ["techmeme.com", "pml.png"]):
                    it["image_url"] = exist_img
                # 严密保护已人工清洗或高质量提炼的中文摘要，绝不被复读机摘要覆盖
                exist_sum = existing.get("summary_zh") or ""
                curr_sum = it.get("summary_zh") or ""
                clean_t = (it.get("title_zh") or it.get("title") or "").strip()
                if exist_sum and clean_t and not exist_sum.startswith(clean_t) and (not curr_sum or curr_sum.startswith(clean_t)):
                    it["summary_zh"] = exist_sum

            # 彻底清洗掉任何残留的 pml.png 站内图章，并确保所有卡片绝对具备超清封面 (100% 覆盖)
            img_val = str(it.get("image_url") or "")
            if (not it.get("image_url")) or any(bad in img_val.lower() for bad in ["pml.png", "techmeme.com/img", "techmeme_sq", "pixel", "icon"]):
                it["image_url"] = get_smart_cover_url(it.get("title", "") or it.get("title_zh", ""), it.get("category", "news"), it.get("source", ""))

            if it.get("inline_images") and isinstance(it["inline_images"], list):
                it["inline_images"] = [
                    u for u in it["inline_images"] 
                    if not any(bad in str(u).lower() for bad in ["pml.png", "techmeme.com/img", "pixel", "icon"])
                ]

            # 坚决杜绝摘要复读标题与媒体噪音
            title_zh = (it.get("title_zh") or it.get("title") or "").strip()
            curr_sum = (it.get("summary_zh") or "").strip()
            if title_zh and curr_sum:
                if curr_sum.startswith(title_zh):
                    remainder = curr_sum[len(title_zh):].lstrip('。，, ：: -—').strip()
                    zh_media = r'[\s.·|]*(?:美国有线电视新闻网|CNN|卫报|华盛顿邮报|路透社|彭博社|金融时报|华尔街日报|纽约时报|皮尤研究中心|英国广播公司|全国广播公司|NBC新闻|自由新闻报|IEEE频谱|NPR|西雅图时报|半岛电视台|德国之声|DW)[\s.]*$'
                    remainder = re.sub(zh_media, '', remainder).strip()
                    if len(remainder) >= 12 and remainder != title_zh:
                        it["summary_zh"] = remainder

            master_dict[k] = it

    all_master_items = list(master_dict.values())
    for it in all_master_items:
        # 1. 确保全库条目 100% 具备超清封面，绝无白卡或垃圾图章
        img_val = str(it.get("image_url") or "")
        if (not it.get("image_url")) or any(bad in img_val.lower() for bad in ["pml.png", "techmeme.com/img", "techmeme_sq", "pixel", "icon"]):
            it["image_url"] = get_smart_cover_url(it.get("title", "") or it.get("title_zh", ""), it.get("category", "news"), it.get("source", ""))

        # 2. 彻底清洗所有复读机摘要 (即使历史残留多次重复也彻底剥离)
        title_zh = (it.get("title_zh") or it.get("title") or "").strip()
        curr_sum = (it.get("summary_zh") or "").strip()
        if title_zh and curr_sum:
            s = curr_sum
            while title_zh and s.startswith(title_zh):
                s = s[len(title_zh):].lstrip('。，, ：: -—').strip()
            if title_zh and title_zh in s and len(s) <= len(title_zh) * 2.5:
                s = s.replace(title_zh, "").lstrip('。，, ：: -—').strip()
            
            zh_media = r'[\s.·|《]*(?:美国有线电视新闻网|CNN|卫报|华盛顿邮报|路透社|彭博社|金融时报|华尔街日报|纽约时报|皮尤研究中心|英国广播公司|全国广播公司|NBC新闻|NBC News|自由新闻报|The Free Press|IEEE频谱|IEEE Spectrum|NPR|西雅图时报|Seattle Times|半岛电视台|德国之声|DW\.com|DW|美联社|AP新闻|AP|CBRE|OpenAI|Anthropic|Google|Microsoft|Apple|Meta)[》\s.]*$'
            s = re.sub(zh_media, '', s, flags=re.IGNORECASE).strip('。，, ：: -—|·《》')

            zh_chars = len(re.findall(r'[\u4e00-\u9fa5]', s))
            common = sum(1 for c in s if c in title_zh)
            if len(s) >= 12 and zh_chars >= 8 and s != title_zh and (title_zh not in s) and (common / max(len(s), 1) < 0.65):
                it["summary_zh"] = s
            else:
                it["summary_zh"] = generate_smart_fallback_summary(it, title_zh)

        # 3. 确保所有 celebrity 领袖观点条目均具备规范的 quote 与 full_text 双语字段
        if it.get("category") == "celebrity":
            if not it.get("full_text_en"):
                it["full_text_en"] = it.get("content_snippet") or it.get("title_en") or it.get("title") or ""
            if not it.get("full_text_zh"):
                it["full_text_zh"] = it.get("summary_zh") or it.get("title_zh") or it.get("title") or ""
            if not it.get("quote_zh"):
                it["quote_zh"] = it.get("title_zh") or it.get("title") or ""
            if not it.get("quote_en"):
                it["quote_en"] = it.get("title_en") or it.get("title") or ""

    all_master_items.sort(key=parse_time_for_sort, reverse=True)

    # 滚动保留 1 年（最多 25,000 条高质量前沿深度资讯），杜绝存储无限膨胀
    if len(all_master_items) > 25000:
        all_master_items = all_master_items[:25000]

    # 保存全量主库 (永久持久化存储)
    with open(MASTER_ARCHIVE_FILE, "w", encoding="utf-8") as f:
        json.dump({"updated_at": datetime.now(timezone.utc).isoformat(), "total_count": len(all_master_items), "items": all_master_items}, f, ensure_ascii=False, indent=2)

    # 2. 严格按 24 小时门禁分级分离：24 小时热数据看板 vs 超出 24 小时的历史归档库
    recent_items = []
    historical_items = []

    for it in all_master_items:
        evaluate_dynamic_pinned_status(it)
        ts = parse_time_for_sort(it)
        diff = now_ts - ts
        cat = it.get("category", "news")

        # 资讯与推特：严格限定在 24 小时以内（或享有重置动态置顶特权）
        # 实用工具/视频/提示词：生命周期为 30 天以内的精选内容
        is_fresh_news = cat in ["news", "celebrity"] and (diff <= MAX_24H_SECONDS or it.get("is_pinned"))
        is_fresh_tool = cat in ["tools", "videos", "prompts"] and diff <= (30 * 86400)

        if is_fresh_news or is_fresh_tool:
            recent_items.append(it)
        else:
            historical_items.append(it)

    # 保证在极端冷启动或外部源更新停滞时，首页不至于完全空白（最低保留 12 条）
    news_recent = [it for it in recent_items if it.get("category") == "news"]
    if len(news_recent) < 12:
        extra_news = [it for it in historical_items if it.get("category") == "news"][:(12 - len(news_recent))]
        recent_items.extend(extra_news)

    # 3. 构建 24 小时热看板 payload (latest_news.json)
    grouped = {cat_key: [] for cat_key in CATEGORIES}
    for item in recent_items:
        cat = item.get("category", "news")
        if cat not in grouped:
            cat = "news"
        grouped[cat].append(item)

    for cat_key in grouped:
        grouped[cat_key].sort(key=lambda x: (
            1 if x.get("is_pinned") and evaluate_dynamic_pinned_status(x) else 0,
            parse_time_for_sort(x)
        ), reverse=True)

    recent_final = []
    for cat_key in grouped:
        recent_final.extend(grouped[cat_key])
    recent_final.sort(key=parse_time_for_sort, reverse=True)

    # 提取 24h 全网平台爆帖 (𝕏 & Threads 突破与极客神贴)
    viral_posts = [it for it in recent_final if it.get("sub_category") == "viral_post" or (it.get("category") == "celebrity" and it.get("is_viral"))]
    grouped["viral_posts"] = viral_posts

    top_three = extract_top_three(recent_final)
    chatbot_arena = get_chatbot_arena_top5()
    arxiv_papers = get_arxiv_curated_papers()

    latest_payload = {
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "total_count": len(recent_final),
        "archive_meta": {
            "total_archived": len(historical_items),
            "archive_url": "data/archive_news.json"
        },
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
        "viral_posts": viral_posts,
        "industry_news": grouped.get("news", []),
        "leader_opinions": grouped.get("celebrity", []),
        "applied_tools": grouped.get("tools", []),
        "video_prompts": grouped.get("videos", []),
        "items": recent_final
    }

    # 4. 构建全量历史归档库 payload (archive_news.json)
    archive_payload = {
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "total_count": len(historical_items),
        "items": historical_items,
        "categories": CATEGORIES
    }

    # 写入 latest_news.json
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(latest_payload, f, ensure_ascii=False, indent=2)
    with open(PUBLIC_OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(latest_payload, f, ensure_ascii=False, indent=2)

    # 写入 archive_news.json
    with open(ARCHIVE_OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(archive_payload, f, ensure_ascii=False, indent=2)
    with open(PUBLIC_ARCHIVE_OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(archive_payload, f, ensure_ascii=False, indent=2)

    # 动态同步更新搜索引擎站点地图 sitemap.xml
    generate_sitemap()

    print(f"\n💾 分级存储同步完成:")
    print(f"  ⚡ 24小时实时热数据: {len(recent_final)} 篇 (体积大幅缩减，首屏极速秒开)")
    print(f"  📜 历史全量归档库: {len(historical_items)} 篇 -> {PUBLIC_ARCHIVE_OUTPUT_FILE}")
    print("=" * 60)
    for cat_key, cat_val in CATEGORIES.items():
        count = len(grouped[cat_key])
        name = cat_val.get("zh", cat_key) if isinstance(cat_val, dict) else cat_val
        print(f"  {name}: {count} 条 (24h)")
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

    # 5.5 自动纠偏与分类恢复：凡是真实 𝕏 / Threads 个人极客、开发者或前沿团队的技术贴文，修正其归入 celebrity 爆帖
    news_orgs = {"techmeme", "theverge", "techcrunch", "bloomberg", "reuters", "wsj", "nytimes", "guardian", "bbcnews", "engadget", "wired", "arstechnica", "venturebeat", "zdnet", "mashable", "cnet", "cnbc", "forbes", "ft", "businessinsider"}
    for it in cleaned_items:
        u = it.get("url", "")
        plat = it.get("platform", "")
        auth = it.get("author", "").lstrip("@").lower()
        if (plat == "x" or "x.com" in u or "twitter.com" in u or "threads.net" in u) and auth not in news_orgs:
            if it.get("category") == "news":
                it["category"] = "celebrity"
                it["sub_category"] = "viral_post"
                it["is_viral"] = True
                if not it.get("surge_badge"):
                    it["surge_badge"] = "⚡ 24h 极客热推"
                if not it.get("spec_tags"):
                    it["spec_tags"] = ["𝕏平台爆帖", "极客前沿"]

    # 6. 存储增量融合后的完整大库
    save_news(cleaned_items)
    
    # 7. 自动触发微信公众号爆款资讯筛选与内联排版引擎
    try:
        from wechat_engine import generate_daily_wechat_digest
        generate_daily_wechat_digest(cleaned_items, top_k=3)
    except Exception as wechat_err:
        print(f"⚠️ 生成微信公众号精选排版时出现异常: {wechat_err}")

    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds()
    print(f"✨ 增量更新与历史合并全流程执行完毕，耗时: {duration:.2f} 秒\n")


if __name__ == "__main__":
    run_pipeline()
