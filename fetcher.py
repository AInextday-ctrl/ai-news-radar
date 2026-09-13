"""
Fetcher 2.0 - Rich multi-media data collector:
- YouTube 16:9 videos
- Product Hunt & GitHub applied tools (filtered, no raw models)
- Social voices & celebrity quotes (with avatars and handles)
- Curated practical prompts
"""

import sys

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

import re
import hashlib
import time
from typing import List, Dict, Any, Optional
import httpx
import feedparser
from config import SOURCES, CELEBRITY_PROFILES, SCENARIO_TAGS, PRICING_TAGS

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36 AI-Radar/2.0"
}


import html
from datetime import datetime, timezone

def make_id(url: str, title: str) -> str:
    raw = f"{url}-{title}".encode("utf-8")
    return hashlib.md5(raw).hexdigest()[:16]


def parse_to_iso(published_parsed: Any = None, raw_str: str = "") -> str:
    """Standardize publication time to ISO-8601 string."""
    if published_parsed:
        try:
            dt = datetime(*published_parsed[:6], tzinfo=timezone.utc)
            return dt.isoformat()
        except Exception:
            pass
    if raw_str:
        try:
            import email.utils
            parsed = email.utils.parsedate_to_datetime(raw_str)
            if parsed:
                return parsed.astimezone(timezone.utc).isoformat()
        except Exception:
            pass
        # 匹配常见 ISO 格式
        if re.match(r'^\d{4}-\d{2}-\d{2}', raw_str):
            return raw_str
    return datetime.now(timezone.utc).isoformat()


def get_smart_cover_url(title: str, category: str = "news", source: str = "") -> Optional[str]:
    """
    Return None for articles without authentic images, so frontend can render
    clean, readable typographic cards instead of repetitive generic placeholder images.
    """
    return None


def extract_image_url(entry: Any, raw_html: str = "") -> Optional[str]:
    """Extract featured cover image from feed entry or HTML snippet."""
    # 1. media:content
    if hasattr(entry, "media_content") and entry.media_content:
        for m in entry.media_content:
            if "url" in m and (m.get("medium") == "image" or "image" in m.get("type", "") or not m.get("medium")):
                return html.unescape(m["url"])
        if "url" in entry.media_content[0]:
            return html.unescape(entry.media_content[0]["url"])

    # 2. media:thumbnail
    if hasattr(entry, "media_thumbnail") and entry.media_thumbnail:
        for t in entry.media_thumbnail:
            if "url" in t:
                return html.unescape(t["url"])

    # 3. enclosures
    if hasattr(entry, "enclosures") and entry.enclosures:
        for enc in entry.enclosures:
            if "image" in enc.get("type", "") and "href" in enc:
                return html.unescape(enc["href"])

    # 4. 正文与摘要中的 <img> 标签 (含 Reddit preview)
    text_to_search = raw_html or ""
    if hasattr(entry, "content") and entry.content:
        for c in entry.content:
            text_to_search += " " + c.get("value", "")
    if hasattr(entry, "summary"):
        text_to_search += " " + getattr(entry, "summary", "")

    img_matches = re.findall(r'<img[^>]+src=["\'](https?://[^"\'>]+)["\']', text_to_search, re.IGNORECASE)
    for img_url in img_matches:
        img_url = html.unescape(img_url)
        # 过滤跟踪像素和无意义图标
        if not any(bad in img_url.lower() for bad in ["tracking", "spacer", "pixel", "avatar", "icon", "1x1"]):
            return img_url

    return None


def match_celebrity_profile(title: str, content: str) -> Optional[Dict[str, Any]]:
    """Match leader profile based on names."""
    combined = f"{title} {content}".lower()
    for key, profile in CELEBRITY_PROFILES.items():
        if re.search(r'\b' + re.escape(key) + r'\b', combined):
            return profile
    return None


# ==========================================
# 1. 抓取 YouTube 顶级实战与演示视频
# ==========================================
def fetch_youtube_videos(max_per_channel: int = 4) -> List[Dict[str, Any]]:
    """Fetch high-res AI demonstration & breakdown videos from YouTube."""
    items = []
    channels = SOURCES.get("youtube_channels", [])

    for ch in channels:
        rss_url = f"https://www.youtube.com/feeds/videos.xml?channel_id={ch['id']}"
        try:
            feed = feedparser.parse(rss_url)
            for entry in feed.entries[:max_per_channel]:
                title = entry.get("title", "").strip()
                link = entry.get("link", "")
                published = entry.get("published", "")
                iso_time = parse_to_iso(getattr(entry, "published_parsed", None), published)
                summary = entry.get("summary", "")[:220]

                # 提取 YouTube 视频 ID 与封面
                video_id = ""
                if "v=" in link:
                    video_id = link.split("v=")[-1].split("&")[0]
                elif "embed/" in link:
                    video_id = link.split("embed/")[-1].split("?")[0]

                thumbnail = f"https://i.ytimg.com/vi/{video_id}/hqdefault.jpg" if video_id else ""
                embed_url = f"https://www.youtube.com/embed/{video_id}" if video_id else ""

                items.append({
                    "id": make_id(link, title),
                    "title": title,
                    "url": link,
                    "image_url": thumbnail or get_smart_cover_url(title, "videos", ch["name"]),
                    "video_id": video_id,
                    "embed_url": embed_url,
                    "source": f"YouTube · {ch['name']}",
                    "author": ch["name"],
                    "raw_published_at": iso_time,
                    "metrics": {"format": "16:9 高清实操视频"},
                    "content_snippet": summary or f"来自 {ch['name']} 的最新 AI 演示精讲",
                    "category": "videos",
                    "tags": ["AI实操视频", ch["name"]]
                })
        except Exception as e:
            print(f"  ❌ YouTube [{ch['name']}] 抓取失败: {e}")
    return items


# ==========================================
# 2. 抓取 Product Hunt 场景化 AI 应用工具
# ==========================================
def fetch_product_hunt_tools(max_items: int = 10) -> List[Dict[str, Any]]:
    """Fetch trending user-facing AI tools from Product Hunt."""
    items = []
    cfg = SOURCES["product_hunt"]
    try:
        feed = feedparser.parse(cfg["url"])
        ai_keywords = ["ai", "gpt", "agent", "llm", "generator", "image", "video", "chat", "code", "audio"]
        
        for entry in feed.entries:
            title = entry.get("title", "").strip()
            summary = entry.get("summary", "")
            clean_summary = re.sub(r'<[^>]+>', '', summary).strip()
            combined = f"{title} {clean_summary}".lower()

            # 严格筛选面向用户的 AI 工具
            if not any(k in combined for k in ai_keywords):
                continue

            link = entry.get("link", "")
            img_url = extract_image_url(entry, summary)

            # 场景推测
            scenario = "🤖 智能体/工作流"
            if any(k in combined for k in ["image", "photo", "pic", "design", "art", "paint"]):
                scenario = "🎨 图像修图/设计"
            elif any(k in combined for k in ["video", "clip", "movie", "reel"]):
                scenario = "🎬 视频创作合成"
            elif any(k in combined for k in ["code", "dev", "programming", "terminal"]):
                scenario = "💻 编程开发提效"
            elif any(k in combined for k in ["write", "doc", "email", "office", "note"]):
                scenario = "✍️ 写作办公知识库"
            elif any(k in combined for k in ["audio", "voice", "speech", "sound", "clone"]):
                scenario = "🎙️ 声音克隆音频"

            if not img_url:
                img_url = get_smart_cover_url(title, "tools", "Product Hunt")

            published = entry.get("published", "")
            iso_time = parse_to_iso(getattr(entry, "published_parsed", None), published)

            items.append({
                "id": make_id(link, title),
                "title": title,
                "url": link,
                "image_url": img_url,
                "source": "Product Hunt",
                "author": "Product Hunt 新品",
                "raw_published_at": iso_time,
                "metrics": {"tag": scenario, "pricing": "🟡 免费试玩"},
                "scenario_tag": scenario,
                "pricing_tag": "🟡 免费试玩",
                "content_snippet": clean_summary[:200] or "Product Hunt 热门 AI 场景应用",
                "category": "tools",
                "tags": [scenario, "免部署工具"]
            })
            if len(items) >= max_items:
                break
    except Exception as e:
        print(f"  ❌ [Product Hunt] 抓取失败: {e}")
    return items


# ==========================================
# 3. 抓取 GitHub 场景应用神器 (非纯模型权重)
# ==========================================
def fetch_github_applied_tools() -> List[Dict[str, Any]]:
    """Fetch practical GitHub open-source client tools/apps."""
    items = []
    cfg = SOURCES["github_tools"]
    try:
        with httpx.Client(headers=HEADERS, timeout=15) as client:
            resp = client.get(cfg["url"])
            if resp.status_code == 200:
                data = resp.json()
                for repo in data.get("items", [])[:8]:
                    full_name = repo.get("full_name", "")
                    description = repo.get("description") or "Open source AI tool"
                    stars = repo.get("stargazers_count", 0)
                    url = repo.get("html_url", "")

                    # 场景推测
                    combined = f"{full_name} {description}".lower()
                    scenario = "💻 开发者提效"
                    if any(k in combined for k in ["image", "paint", "diffusion", "comfyui", "flux", "draw"]):
                        scenario = "🎨 图像修图/设计"
                    elif any(k in combined for k in ["agent", "crawler", "assistant", "workflow", "browser"]):
                        scenario = "🤖 自动化 Agent"
                    elif any(k in combined for k in ["voice", "audio", "tts", "speech", "sound"]):
                        scenario = "🎙️ 声音克隆音频"
                    elif any(k in combined for k in ["chat", "client", "desktop", "ui", "webui"]):
                        scenario = "💬 AI 客户端应用"

                    og_image = f"https://opengraph.githubassets.com/1/{full_name}"
                    iso_time = parse_to_iso(raw_str=repo.get("created_at", ""))

                    items.append({
                        "id": make_id(url, full_name),
                        "title": f"{repo.get('name')}: {description[:60]}",
                        "url": url,
                        "image_url": og_image,
                        "source": "GitHub 开源",
                        "author": repo.get("owner", {}).get("login", "GitHub"),
                        "raw_published_at": iso_time,
                        "metrics": {"stars": stars, "pricing": "🟢 完全开源免费"},
                        "scenario_tag": scenario,
                        "pricing_tag": "🟢 完全开源免费",
                        "content_snippet": f"⭐ {stars} 颗星标 · {description}",
                        "category": "tools",
                        "tags": [scenario, "开源免费"]
                    })
    except Exception as e:
        print(f"  ❌ [GitHub Tools] 抓取失败: {e}")
    return items


# ==========================================
# 4. 抓取名人大V、社交争论与突发快讯
# ==========================================
def fetch_news_and_celebrities() -> List[Dict[str, Any]]:
    """Fetch breaking news and celebrity tweets/posts with rich profiles."""
    items = []

    # 1. 24小时超高频全球与中文AI突发（确保当天最新鲜的事件占绝对核心）
    gn_items = fetch_rss_channel("google_news_ai", max_items=15)
    items.extend(gn_items)

    gn_zh_items = fetch_rss_channel("google_news_zh", max_items=12)
    items.extend(gn_zh_items)

    tm_items = fetch_rss_channel("techmeme_ai", max_items=8)
    items.extend(tm_items)

    # 2. 行业顶级资讯（深度报道）
    ars_items = fetch_rss_channel("arstechnica_ai", max_items=6)
    items.extend(ars_items)

    vb_items = fetch_rss_channel("venturebeat_ai", max_items=6)
    items.extend(vb_items)

    vg_items = fetch_rss_channel("theverge_ai", max_items=6)
    items.extend(vg_items)

    mit_items = fetch_rss_channel("mit_tech_review", max_items=4)
    items.extend(mit_items)

    tc_items = fetch_rss_channel("techcrunch_ai", max_items=6)
    items.extend(tc_items)

    # 3. Hacker News 极客热榜
    hn_items = fetch_hacker_news(max_items=8)
    items.extend(hn_items)

    # 4. 领袖大V博客与推文热点
    altman_items = fetch_rss_channel("sam_altman_blog", max_items=4)
    items.extend(altman_items)

    # 5. Reddit 极客社群真实热议
    sing_items = fetch_rss_channel("reddit_singularity", max_items=8)
    items.extend(sing_items)

    gpt_items = fetch_rss_channel("reddit_chatgpt", max_items=8)
    items.extend(gpt_items)

    local_items = fetch_rss_channel("reddit_localllama", max_items=8)
    items.extend(local_items)

    return items


def fetch_rss_channel(source_key: str, max_items: int = 8) -> List[Dict[str, Any]]:
    items = []
    cfg = SOURCES.get(source_key)
    if not cfg:
        return items

    try:
        with httpx.Client(headers=HEADERS, follow_redirects=True, timeout=15) as client:
            resp = client.get(cfg["url"])
            if resp.status_code == 200:
                feed = feedparser.parse(resp.text)
                for entry in feed.entries[:max_items]:
                    title = entry.get("title", "").strip()
                    if not title:
                        continue
                    url = entry.get("link", "")
                    author = entry.get("author", cfg["name"])

                    # 针对 Google News 优化标题与信源识别
                    if " - " in title and ("google" in source_key.lower()):
                        parts = title.rsplit(" - ", 1)
                        title = parts[0].strip()
                        author = parts[1].strip()
                    
                    # 标准化时间戳
                    published_raw = entry.get("published") or entry.get("updated", "")
                    iso_time = parse_to_iso(getattr(entry, "published_parsed", None), published_raw)

                    summary = entry.get("summary") or entry.get("description", "")
                    clean_summary = re.sub(r'<[^>]+>', '', summary).strip()[:280]

                    # 提取主图，若无则匹配科技主题封面
                    img_url = extract_image_url(entry, summary)
                    
                    # 识别是否包含名人领袖
                    profile = match_celebrity_profile(title, clean_summary)
                    category = "celebrity" if (profile or cfg["default_category"] == "celebrity") else cfg["default_category"]

                    if not img_url:
                        img_url = get_smart_cover_url(title, category, cfg["name"])

                    author_display = profile["name"] if profile else author
                    author_handle = profile["handle"] if profile else ""
                    author_avatar = profile["avatar"] if profile else ""

                    items.append({
                        "id": make_id(url, title),
                        "title": title,
                        "url": url,
                        "image_url": img_url,
                        "source": author if ("google" in source_key.lower()) else cfg["name"],
                        "author": author_display,
                        "author_handle": author_handle,
                        "author_avatar": author_avatar,
                        "raw_published_at": iso_time,
                        "metrics": {},
                        "content_snippet": clean_summary or f"From {cfg['name']}",
                        "category": category,
                        "tags": [profile["name"] if profile else (author if "google" in source_key.lower() else cfg["name"]), "今日要闻"]
                    })
    except Exception as e:
        print(f"  ❌ [{cfg['name']}] 抓取失败: {e}")
    return items


def fetch_hacker_news(max_items: int = 10) -> List[Dict[str, Any]]:
    items = []
    cfg = SOURCES["hacker_news"]
    try:
        with httpx.Client(headers=HEADERS, timeout=12) as client:
            resp = client.get(cfg["url"])
            if resp.status_code == 200:
                data = resp.json()
                for hit in data.get("hits", [])[:max_items]:
                    title = hit.get("title")
                    if not title:
                        continue
                    url = hit.get("url") or f"https://news.ycombinator.com/item?id={hit.get('objectID')}"
                    points = hit.get("points") or 0
                    comments = hit.get("num_comments") or 0
                    snippet = f"HN 极客热议: {points} 点赞, {comments} 讨论"
                    iso_time = parse_to_iso(raw_str=hit.get("created_at", ""))

                    profile = match_celebrity_profile(title, snippet)
                    category = "celebrity" if profile else "news"
                    img_url = get_smart_cover_url(title, category, "Hacker News")

                    items.append({
                        "id": make_id(url, title),
                        "title": title,
                        "url": url,
                        "image_url": img_url,
                        "source": "Hacker News",
                        "author": profile["name"] if profile else hit.get("author", "HN User"),
                        "author_handle": profile["handle"] if profile else "",
                        "author_avatar": profile["avatar"] if profile else "",
                        "raw_published_at": iso_time,
                        "metrics": {"score": points, "comments": comments},
                        "content_snippet": snippet,
                        "category": category,
                        "tags": ["黑客探讨", "行业热议"]
                    })
    except Exception as e:
        print(f"  ❌ [Hacker News] 抓取失败: {e}")
    return items


# ==========================================
# 5. 精选每日可即刻抄用的实战 Prompt 技巧
# ==========================================
def get_curated_actionable_prompts() -> List[Dict[str, Any]]:
    """Curated actionable prompts that AI enthusiasts love to copy and use immediately."""
    now_iso = datetime.now(timezone.utc).isoformat()
    prompts = [
        {
            "id": "prompt_deepseek_reasoning",
            "title": "💡 DeepSeek R1 深度思考解锁咒语：开启极致逻辑链",
            "url": "https://github.com/deepseek-ai/DeepSeek-R1",
            "image_url": "https://images.unsplash.com/photo-1620712943543-bcc4688e7485?w=800&q=80&auto=format&fit=crop",
            "source": "实战技巧 · Prompt",
            "author": "社区实测",
            "category": "videos",
            "is_prompt": True,
            "raw_published_at": now_iso,
            "metrics": {"type": "📋 即抄即用"},
            "content_snippet": "请不要直接给我简短答案，请使用 <thinking> 标签展开每一步推理演算，列出所有假设、边界条件和可能存在的漏洞，最后再给出最佳结论。",
            "prompt_content": "请不要直接给出结论。请以资深架构师兼批判性学者的身份，使用步骤分解法展开思考：1. 分析核心痛点；2. 权衡三种不同方案优劣；3. 给出包含代码/排查清单的生产级交付结果。",
            "tags": ["Prompt神咒", "逻辑推理"]
        },
        {
            "id": "prompt_claude_coding_architect",
            "title": "💡 Claude 3.7 / GPT-4o 复杂工程重构提示词模板",
            "url": "https://docs.anthropic.com/",
            "image_url": "https://images.unsplash.com/photo-1555066931-4365d14bab8c?w=800&q=80&auto=format&fit=crop",
            "source": "实战技巧 · Prompt",
            "author": "工程实战",
            "category": "videos",
            "is_prompt": True,
            "raw_published_at": now_iso,
            "metrics": {"type": "📋 即抄即用"},
            "content_snippet": "你是一个严谨的代码审查官。请在不修改原有业务契约的前提下，识别并重构这段代码的异味（Code Smell），给出前后对比和防御性测试用例。",
            "prompt_content": "你是一个资深全栈架构师。请审查这段代码：1. 指出性能瓶颈与安全漏洞；2. 按照现代 Clean Code 规范进行重构；3. 输出配套的单元测试与异常边界处理。",
            "tags": ["代码重构", "高阶提示词"]
        },
        {
            "id": "prompt_flux_photoreal",
            "title": "💡 FLUX / Midjourney 顶级商业摄影质感提示词神咒",
            "url": "https://blackforestlabs.ai/",
            "image_url": "https://images.unsplash.com/photo-1579783900882-c0d3dad7b119?w=800&q=80&auto=format&fit=crop",
            "source": "实战技巧 · Prompt",
            "author": "视觉实测",
            "category": "videos",
            "is_prompt": True,
            "raw_published_at": now_iso,
            "metrics": {"type": "📋 即抄即用"},
            "content_snippet": "超高清商业人像与胶片质感核心构词法则：85mm f/1.4 镜头虚化、哈苏色彩影调、丁达尔光线与真实皮肤微瑕疵控制。",
            "prompt_content": "A high-end cinematic editorial portrait, shot on 35mm film, Hasselblad H6D-100c, soft natural morning rim light, subtle film grain, hyper-realistic skin texture, 8k resolution, photorealistic, masterpiece.",
            "tags": ["生图神咒", "FLUX/MJ"]
        }
    ]
    return prompts


# ==========================================
# 全局聚合主调度
# ==========================================
def fetch_all_sources() -> List[Dict[str, Any]]:
    """Fetch and aggregate items across all 4 redesigned pillars."""
    print("🚀 开始全网多维聚合 AI 动态 (视频/工具/社交推文/突发大事件)...")
    all_items = []

    # 1. 突发大事件与社交名人大V
    news_and_celeb = fetch_news_and_celebrities()
    print(f"  ✓ 新闻与名人大V言论: 获取到 {len(news_and_celeb)} 条")
    all_items.extend(news_and_celeb)

    # 2. 场景化落地工具 (Product Hunt + GitHub)
    ph_tools = fetch_product_hunt_tools(max_items=8)
    print(f"  ✓ Product Hunt 落地应用: 获取到 {len(ph_tools)} 条")
    all_items.extend(ph_tools)

    gh_tools = fetch_github_applied_tools()
    print(f"  ✓ GitHub 开源神器: 获取到 {len(gh_tools)} 条")
    all_items.extend(gh_tools)

    # 3. 爆款视频
    yt_videos = fetch_youtube_videos(max_per_channel=4)
    print(f"  ✓ YouTube AI 演示视频: 获取到 {len(yt_videos)} 条")
    all_items.extend(yt_videos)

    # 4. 精选实用 Prompt
    prompts = get_curated_actionable_prompts()
    print(f"  ✓ 精选可复制实战提示词: 获取到 {len(prompts)} 条")
    all_items.extend(prompts)

    # 去重并按时间全局倒序排列（最新发布的绝对排在最前）
    seen_ids = set()
    unique_items = []
    for it in all_items:
        if it["id"] not in seen_ids:
            seen_ids.add(it["id"])
            unique_items.append(it)

    def parse_time_for_sort(it):
        raw = it.get("raw_published_at", "")
        if not raw:
            return 0
        try:
            # 标准 ISO 或 RFC 转换
            return datetime.fromisoformat(raw.replace("Z", "+00:00")).timestamp()
        except Exception:
            return 0

    unique_items.sort(key=parse_time_for_sort, reverse=True)

    print(f"🎉 聚合完成！共收集到 {len(unique_items)} 条高质量多媒体情报 (已按最新时间严格倒序)。\n")
    return unique_items


if __name__ == "__main__":
    items = fetch_all_sources()
    print(f"样本: 共 {len(items)} 条")
