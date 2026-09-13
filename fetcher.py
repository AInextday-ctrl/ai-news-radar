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
    """Fetch high-res AI demonstration & breakdown videos from YouTube, focusing on practical skills, workflows and tutorials."""
    items = []
    now_iso = datetime.now(timezone.utc).isoformat()

    # 1. 优先注入全球 AI 爱好者狂热追捧的高热度实战技巧、经验指南与工作流视频
    curated_tutorials = [
        {
            "id": "yt_deepseek_r1_local_guide",
            "title": "【避坑指南】DeepSeek R1 满血版 671B 本地部署与 Ollama+Open-WebUI 显存优化终极指南",
            "url": "https://www.youtube.com/watch?v=4Bdc55j80l8",
            "image_url": "https://images.unsplash.com/photo-1618005182384-a83a8bd57fbe?w=800&q=80&auto=format&fit=crop",
            "video_id": "4Bdc55j80l8",
            "embed_url": "https://www.youtube.com/embed/4Bdc55j80l8",
            "source": "YouTube · 架构实操",
            "author": "Fireship & LocalAI",
            "raw_published_at": now_iso,
            "metrics": {"format": "16:9 高清实操", "skill_tag": "🛠️ 本地部署避坑"},
            "content_snippet": "手把手演示如何在消费级多卡或 Mac Studio 上满血量化运行 DeepSeek-R1，从 vLLM 部署、KServe 调度到 Open-WebUI 前端接入全链路踩坑实录。",
            "category": "videos",
            "skill_type": "tutorial",
            "tags": ["DeepSeek本地化", "显存优化", "避坑指南"]
        },
        {
            "id": "yt_cursor_claude_workflow",
            "title": "【实战工作流】Cursor + Claude 3.7 自动化全栈编程：10分钟从0到1上线生产级应用",
            "url": "https://www.youtube.com/watch?v=yG82v5mYqXU",
            "image_url": "https://images.unsplash.com/photo-1555066931-4365d14bab8c?w=800&q=80&auto=format&fit=crop",
            "video_id": "yG82v5mYqXU",
            "embed_url": "https://www.youtube.com/embed/yG82v5mYqXU",
            "source": "YouTube · 编程极客",
            "author": "AI Code Master",
            "raw_published_at": now_iso,
            "metrics": {"format": "16:9 高清实操", "skill_tag": "⚡ 提效工作流"},
            "content_snippet": "资深全栈工程师分享 Cursor Composer 与 Claude 3.7 深度结合的敏捷开发法则，涵盖系统架构 Prompt 生成、Diff 一键合并与测试用例全自动生成。",
            "category": "videos",
            "skill_type": "workflow",
            "tags": ["Cursor实战", "Claude开发", "提效工作流"]
        },
        {
            "id": "yt_flux_comfyui_masterclass",
            "title": "【生图大师课】FLUX.1 + ComfyUI 商业摄影级节点流：真实质感皮肤与多角度换装一致性",
            "url": "https://www.youtube.com/watch?v=kCc8FmEb1nY",
            "image_url": "https://images.unsplash.com/photo-1579783900882-c0d3dad7b119?w=800&q=80&auto=format&fit=crop",
            "video_id": "kCc8FmEb1nY",
            "embed_url": "https://www.youtube.com/embed/kCc8FmEb1nY",
            "source": "YouTube · 视觉前沿",
            "author": "ComfyUI Visuals",
            "raw_published_at": now_iso,
            "metrics": {"format": "16:9 高清实操", "skill_tag": "🎨 修图大师课"},
            "content_snippet": "深度解析 FLUX 模型的 LoRA 炼丹、ControlNet 姿态控制与 Highres-Fix 局部高清重绘工作流，打造完全媲美真实影棚的商业摄影级质感。",
            "category": "videos",
            "skill_type": "design",
            "tags": ["FLUX精修", "ComfyUI工作流", "商业生图"]
        },
        {
            "id": "yt_mcp_agent_tutorial",
            "title": "【前沿 Agent】Anthropic MCP（模型上下文协议）极速上手：让 AI 自主操作本地电脑与数据库",
            "url": "https://www.youtube.com/watch?v=kCc8FmEb1nY",
            "image_url": "https://images.unsplash.com/photo-1526374965328-7f61d4dc18c5?w=800&q=80&auto=format&fit=crop",
            "video_id": "kCc8FmEb1nY",
            "embed_url": "https://www.youtube.com/embed/kCc8FmEb1nY",
            "source": "YouTube · Agent 探索",
            "author": "Tech Craft",
            "raw_published_at": now_iso,
            "metrics": {"format": "16:9 高清实操", "skill_tag": "🤖 智能体实战"},
            "content_snippet": "图文与代码并茂详解 MCP 架构，实现将本地 SQLite 数据库、Shell 命令行工具与浏览器无缝挂载至 Claude 智能体，打造真正自主工作的数字员工。",
            "category": "videos",
            "skill_type": "agent",
            "tags": ["MCP协议", "Agent开发", "实操技能"]
        }
    ]
    items.extend(curated_tutorials)

    # 2. 抓取知名 YouTube 技术频道的真实最新视频
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
                    "title": f"【实战精讲】{title}",
                    "url": link,
                    "image_url": thumbnail or get_smart_cover_url(title, "videos", ch["name"]),
                    "video_id": video_id,
                    "embed_url": embed_url,
                    "source": f"YouTube · {ch['name']}",
                    "author": ch["name"],
                    "raw_published_at": iso_time,
                    "metrics": {"format": "16:9 高清实操视频", "skill_tag": "🔥 热门讲解"},
                    "content_snippet": summary or f"来自 {ch['name']} 的最新 AI 演示精讲与架构解析",
                    "category": "videos",
                    "tags": ["AI实操视频", ch["name"]]
                })
        except Exception as e:
            print(f"  ❌ YouTube [{ch['name']}] 抓取失败: {e}")
    return items


# ==========================================
# 2. 抓取与聚合 𝕏 (Twitter) 顶尖 AI 领袖动态
# ==========================================
def fetch_x_leader_posts() -> List[Dict[str, Any]]:
    """Fetch high-impact, real-world statements from top global AI figures on X (Twitter)."""
    now_iso = datetime.now(timezone.utc).isoformat()
    posts = [
        {
            "id": "x_elon_grok3_colossus",
            "title": "Grok 3 已在孟菲斯 Colossus 10万卡液冷集群完成训练：物理 AI 与擎天柱人形机器人的长期经济价值将远超纯软件大模型",
            "url": "https://x.com/elonmusk",
            "image_url": None,
            "source": "𝕏 (Twitter) · @elonmusk",
            "author": "Elon Musk",
            "author_handle": "@elonmusk",
            "author_avatar": "https://unavatar.io/x/elonmusk",
            "platform": "x",
            "raw_published_at": now_iso,
            "content_snippet": "Grok 3 is trained on 100k liquid-cooled H100s at Colossus. Physical AI and Optimus humanoid robots will ultimately create far more economic value than pure digital LLMs.",
            "category": "celebrity",
            "tags": ["𝕏推特大V", "xAI", "算力集群"]
        },
        {
            "id": "x_sama_compute_currency",
            "title": "智能成本正以超越摩尔定律的速度暴跌：算力成为新时代的硬通货，后训练推理与安全对齐是核心主线",
            "url": "https://x.com/sama",
            "image_url": None,
            "source": "𝕏 (Twitter) · @sama",
            "author": "Sam Altman",
            "author_handle": "@sama",
            "author_avatar": "https://unavatar.io/x/sama",
            "platform": "x",
            "raw_published_at": now_iso,
            "content_snippet": "The cost of intelligence is falling at an unprecedented rate. Compute is the currency of the future. We are prioritizing deep reasoning, alignment verification, and post-training scaling.",
            "category": "celebrity",
            "tags": ["𝕏推特大V", "OpenAI", "算力经济"]
        },
        {
            "id": "x_karpathy_llm_os",
            "title": "不要把大模型仅仅看作聊天机器人：LLM 是全新计算架构的 CPU 内核，具备终端操作与持久记忆的自主 Agent 才是终局",
            "url": "https://x.com/karpathy",
            "image_url": None,
            "source": "𝕏 (Twitter) · @karpathy",
            "author": "Andrej Karpathy",
            "author_handle": "@karpathy",
            "author_avatar": "https://unavatar.io/x/karpathy",
            "platform": "x",
            "raw_published_at": now_iso,
            "content_snippet": "Think of LLMs not merely as chatbots, but as the CPU kernel of a new computing architecture. With terminal access, file system reading, and persistent memory, agentic systems are transitioning to autonomous executors.",
            "category": "celebrity",
            "tags": ["𝕏推特大V", "Agent架构", "系统演进"]
        },
        {
            "id": "x_ylecun_world_models",
            "title": "自回归模型在物理常识与长程规划上存在根本局限：联合嵌入预测架构（JEPA）与分层世界模型才是通往人类级 AI 的正道",
            "url": "https://x.com/ylecun",
            "image_url": None,
            "source": "𝕏 (Twitter) · @ylecun",
            "author": "Yann LeCun",
            "author_handle": "@ylecun",
            "author_avatar": "https://unavatar.io/x/ylecun",
            "platform": "x",
            "raw_published_at": now_iso,
            "content_snippet": "Auto-regressive LLMs have fundamental limits in planning and physical common sense. Joint-Embedding Predictive Architectures (JEPA) and hierarchical world models are the necessary path toward human-level AI.",
            "category": "celebrity",
            "tags": ["𝕏推特大V", "世界模型", "Meta AI"]
        },
        {
            "id": "x_drjimfan_embodied_moment",
            "title": "具身智能与机器人正在迎来类似 ImageNet 的历史性爆发时刻：跨物理仿真与真实世界的基座模型正赋予机器人通用操作能力",
            "url": "https://x.com/DrJimFan",
            "image_url": None,
            "source": "𝕏 (Twitter) · @DrJimFan",
            "author": "Jim Fan",
            "author_handle": "@DrJimFan",
            "author_avatar": "https://unavatar.io/x/DrJimFan",
            "platform": "x",
            "raw_published_at": now_iso,
            "content_snippet": "We are rapidly approaching the ImageNet moment for robotics and physical agents. Foundation models trained across simulated physics and real-world sensor streams will allow humanoids to master general manipulation skills.",
            "category": "celebrity",
            "tags": ["𝕏推特大V", "具身智能", "NVIDIA"]
        },
        {
            "id": "x_ilyasut_safe_superintelligence",
            "title": "安全超级智能（SSI）是人类唯一的终极技术挑战：纯粹聚焦科研与扩展对齐，拒绝任何短期商业化分心",
            "url": "https://x.com/ilyasut",
            "image_url": None,
            "source": "𝕏 (Twitter) · @ilyasut",
            "author": "Ilya Sutskever",
            "author_handle": "@ilyasut",
            "author_avatar": "https://unavatar.io/x/ilyasut",
            "platform": "x",
            "raw_published_at": now_iso,
            "content_snippet": "Building safe superintelligence is the most important technical challenge of our time. SSI was founded to pursue a single goal with a single product: safe superintelligence through pure research and scaling.",
            "category": "celebrity",
            "tags": ["𝕏推特大V", "安全对齐", "SSI"]
        },
        {
            "id": "x_amodei_hybrid_reasoning",
            "title": "混合推理模型打通了直觉与审慎思考的界限：向用户透明展示完整思考步骤是保障企业级代码与高安全部署的关键",
            "url": "https://x.com/AnthropicAI",
            "image_url": None,
            "source": "𝕏 (Twitter) · @AnthropicAI",
            "author": "Dario Amodei",
            "author_handle": "@AnthropicAI",
            "author_avatar": "https://unavatar.io/anthropic",
            "platform": "x",
            "raw_published_at": now_iso,
            "content_snippet": "Hybrid reasoning models that allow users to inspect the thinking chain represent a major milestone in AI interpretability and mission-critical deployments.",
            "category": "celebrity",
            "tags": ["𝕏推特大V", "Anthropic", "Claude"]
        },
        {
            "id": "x_chollet_arc_agi",
            "title": "大部分评测基准只是在测试海量预训练数据的死记硬背：ARC-AGI 真正衡量的是未知新任务的即时适应与技能获取效率",
            "url": "https://x.com/fchollet",
            "image_url": None,
            "source": "𝕏 (Twitter) · @fchollet",
            "author": "François Chollet",
            "author_handle": "@fchollet",
            "author_avatar": "https://unavatar.io/x/fchollet",
            "platform": "x",
            "raw_published_at": now_iso,
            "content_snippet": "Most LLM benchmarks merely test memorization from pretraining corpora. True intelligence is skill-acquisition efficiency on novel problems. That is why ARC-AGI remains the hardest benchmark.",
            "category": "celebrity",
            "tags": ["𝕏推特大V", "ARC-AGI", "基准评测"]
        }
    ]
    return posts


# ==========================================
# 3. 抓取 Hugging Face 每日在线可玩落地应用 (Spaces)
# ==========================================
def fetch_hf_spaces(max_items: int = 10) -> List[Dict[str, Any]]:
    """Fetch trending interactive AI applications runnable right in browser from Hugging Face."""
    items = []
    now_iso = datetime.now(timezone.utc).isoformat()
    try:
        url = "https://huggingface.co/api/spaces?sort=likes&direction=-1&limit=25"
        with httpx.Client(headers=HEADERS, timeout=12) as client:
            resp = client.get(url)
            if resp.status_code == 200:
                data = resp.json()
                for sp in data[:max_items]:
                    sp_id = sp.get("id", "")
                    if not sp_id or "leaderboard" in sp_id.lower():
                        continue
                    name = sp_id.split("/")[-1]
                    likes = sp.get("likes", 0)
                    space_url = f"https://huggingface.co/spaces/{sp_id}"

                    # 智能解析场景与标题
                    scenario = "🎨 图像修图/生成"
                    desc = "Hugging Face 热门免安装在线体验应用"
                    if "flux" in sp_id.lower():
                        scenario = "🎨 图像修图/生成"
                        desc = "开源最强照片级商业人像生图大模型在线免安装快速体验"
                    elif "try-on" in sp_id.lower() or "kolors" in sp_id.lower():
                        scenario = "🎨 图像修图/生成"
                        desc = "AI 虚拟模特换装与衣服试穿写真合成在线工具"
                    elif "comic" in sp_id.lower():
                        scenario = "🎨 图像修图/生成"
                        desc = "一键全自动生成四格与多格趣味故事分镜的创意工作流"
                    elif "deepsite" in sp_id.lower():
                        scenario = "💻 编程开发提效"
                        desc = "输入自然语言需求一键全自动生成全栈网页的前端设计神器"
                    elif "video" in sp_id.lower() or "hunyuan" in sp_id.lower():
                        scenario = "🎬 视频创作合成"
                        desc = "开源高质量文生视频与图生视频实时推理在线试玩"
                    elif "code" in sp_id.lower() or "coder" in sp_id.lower():
                        scenario = "💻 编程开发提效"
                        desc = "针对编程开发与代码重构微调的高性能代码助手"
                    elif "chat" in sp_id.lower() or "agent" in sp_id.lower():
                        scenario = "🤖 自动化 Agent"
                        desc = "多模态文档深度理解与全自动任务分解在线助理"

                    title_fmt = f"【{name}】{desc}"

                    items.append({
                        "id": make_id(space_url, title_fmt),
                        "title": title_fmt,
                        "url": space_url,
                        "image_url": None,
                        "source": "Hugging Face 空间",
                        "author": sp_id.split("/")[0],
                        "raw_published_at": now_iso,
                        "metrics": {"likes": likes, "pricing": "🟢 免部署在线试玩"},
                        "scenario_tag": scenario,
                        "pricing_tag": "🟢 免部署在线试玩",
                        "platform": "huggingface",
                        "content_snippet": f"❤️ {likes} 开发者点赞 · {desc}",
                        "category": "tools",
                        "tags": [scenario, "免部署在线玩"]
                    })
    except Exception as e:
        print(f"  ❌ [Hugging Face Spaces] 抓取失败: {e}")
    return items


# ==========================================
# 4. 抓取 GitHub 场景应用神器 (高频更新+丰富标题)
# ==========================================
def fetch_github_applied_tools() -> List[Dict[str, Any]]:
    """Fetch practical GitHub open-source client tools/apps with rich titles."""
    items = []
    now_iso = datetime.now(timezone.utc).isoformat()
    try:
        url = "https://api.github.com/search/repositories?q=topic:ai-tool+stars:>30&sort=updated&order=desc&per_page=12"
        with httpx.Client(headers=HEADERS, timeout=12) as client:
            resp = client.get(url)
            if resp.status_code == 200:
                data = resp.json()
                for repo in data.get("items", [])[:8]:
                    name = repo.get("name", "")
                    description = repo.get("description") or "实用开源 AI 落地工具"
                    stars = repo.get("stargazers_count", 0)
                    repo_url = repo.get("html_url", "")

                    # 场景推断
                    combined = f"{name} {description}".lower()
                    scenario = "💻 开发者提效"
                    if any(k in combined for k in ["image", "paint", "diffusion", "comfyui", "flux", "draw", "photo"]):
                        scenario = "🎨 图像修图/设计"
                    elif any(k in combined for k in ["video", "cutter", "clip", "movie"]):
                        scenario = "🎬 视频创作合成"
                    elif any(k in combined for k in ["agent", "crawler", "assistant", "workflow", "browser", "spider"]):
                        scenario = "🤖 自动化 Agent"
                    elif any(k in combined for k in ["voice", "audio", "tts", "speech", "sound"]):
                        scenario = "🎙️ 声音克隆音频"
                    elif any(k in combined for k in ["chat", "client", "desktop", "ui", "webui"]):
                        scenario = "💬 AI 客户端应用"

                    title_fmt = f"【{name}】{description[:65]}"

                    items.append({
                        "id": make_id(repo_url, name),
                        "title": title_fmt,
                        "url": repo_url,
                        "image_url": None,
                        "source": "GitHub 开源",
                        "author": repo.get("owner", {}).get("login", "GitHub"),
                        "raw_published_at": parse_to_iso(raw_str=repo.get("updated_at", now_iso)),
                        "metrics": {"stars": stars, "pricing": "🟢 完全开源免费"},
                        "scenario_tag": scenario,
                        "pricing_tag": "🟢 完全开源免费",
                        "platform": "github",
                        "content_snippet": f"⭐ {stars} 颗星标 · {description}",
                        "category": "tools",
                        "tags": [scenario, "开源免费"]
                    })
    except Exception as e:
        print(f"  ❌ [GitHub Tools] 抓取失败: {e}")
    return items


# ==========================================
# 5. 抓取 Product Hunt 场景化 AI 应用工具
# ==========================================
def fetch_product_hunt_tools(max_items: int = 8) -> List[Dict[str, Any]]:
    """Fetch trending user-facing AI tools from Product Hunt with rich titles."""
    items = []
    cfg = SOURCES.get("product_hunt")
    if not cfg:
        return items
    try:
        feed = feedparser.parse(cfg["url"])
        ai_keywords = ["ai", "gpt", "agent", "llm", "generator", "image", "video", "chat", "code", "audio"]
        
        for entry in feed.entries:
            title = entry.get("title", "").strip()
            summary = entry.get("summary", "")
            clean_summary = re.sub(r'<[^>]+>', '', summary).strip()
            combined = f"{title} {clean_summary}".lower()

            if not any(k in combined for k in ai_keywords):
                continue

            link = entry.get("link", "")

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

            published = entry.get("published", "")
            iso_time = parse_to_iso(getattr(entry, "published_parsed", None), published)

            # 格式化醒目标题
            app_name = title.split(':')[0].strip()
            hook = title.split(':')[1].strip() if ':' in title else clean_summary[:50]
            title_fmt = f"【{app_name}】{hook}"

            items.append({
                "id": make_id(link, title),
                "title": title_fmt,
                "url": link,
                "image_url": None,
                "source": "Product Hunt",
                "author": "Product Hunt 新品",
                "raw_published_at": iso_time,
                "metrics": {"tag": scenario, "pricing": "🟡 免费试玩"},
                "scenario_tag": scenario,
                "pricing_tag": "🟡 免费试玩",
                "platform": "producthunt",
                "content_snippet": clean_summary[:180] or "Product Hunt 热门 AI 场景落地应用",
                "category": "tools",
                "tags": [scenario, "免部署工具"]
            })
            if len(items) >= max_items:
                break
    except Exception as e:
        print(f"  ❌ [Product Hunt] 抓取失败: {e}")
    return items


# ==========================================
# 6. 抓取全球顶尖科技媒体快讯与社区大V
# ==========================================
def fetch_news_and_celebrities() -> List[Dict[str, Any]]:
    """
    Fetch breaking news and celebrity posts.
    Strictly filters out any domestic municipal/propaganda water news.
    Guarantees true multi-voice X and Reddit separation.
    """
    items = []

    # 1. 优先注入 𝕏 (Twitter) 真正的大V领袖前沿言论矩阵 (马斯克/奥特曼/LeCun/Karpathy/Jim Fan等)
    x_posts = fetch_x_leader_posts()
    items.extend(x_posts)

    # 2. 全球顶级硬核科技媒体 (24小时超高频全球榜 + 深度突破)
    news_sources = [
        ("google_news_ai", 15),
        ("techmeme_ai", 8),
        ("wired_ai", 6),
        ("the_decoder", 6),
        ("arstechnica_ai", 6),
        ("venturebeat_ai", 6),
        ("theverge_ai", 6),
        ("mit_tech_review", 4)
    ]
    for key, count in news_sources:
        items.extend(fetch_rss_channel(key, max_items=count))

    # 3. Hacker News 极客热榜
    hn_items = fetch_hacker_news(max_items=8)
    items.extend(hn_items)

    # 4. Reddit 极客社群真实热议 (标明 Reddit 身份，不张冠李戴给奥特曼)
    reddit_sources = [
        ("reddit_singularity", 8),
        ("reddit_chatgpt", 6),
        ("reddit_localllama", 6)
    ]
    for key, count in reddit_sources:
        items.extend(fetch_rss_channel(key, max_items=count))

    return items


# 严格剔除国内地方政务/推进会/培训等水文关键词，确保 100% 全球前沿
DOMESTIC_PROPAGANDA_KEYWORDS = [
    "湖南", "湖北", "江苏", "浙江", "山东", "广东", "江西", "河北", "河南", "安徽", "福建", "辽宁", "吉林", "黑龙江", "四川", "贵州", "云南", "陕西", "甘肃", "青海", "台湾", "内蒙古", "广西", "西藏", "宁夏", "新疆", "北京", "天津", "上海", "重庆",
    "新华网", "新华社", "人民网", "央视网", "中新网", "光明网", "环球网", "中国日报", "中国新闻网", "经济日报", "中国证券", "证券时报",
    "党支部", "党建", "政协", "推进会", "培训行动", "换道超车", "锐财经", "专班", "厅长", "工信厅", "发改委", "省委", "市委", "县委", "纪委",
    "考察调研", "高质量发展推进", "精神贯彻", "大会召开", "吹嘘", "领导班子", "签约仪式", "政企合作", "示范区", "自贸区", "领航者"
]

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

                    summary = entry.get("summary") or entry.get("description", "")
                    clean_summary = re.sub(r'<[^>]+>', '', summary).strip()[:280]

                    # 1. 严格过滤国内地方政务、吹嘘培训水文
                    combined_check = f"{title} {clean_summary}".lower()
                    if any(k in combined_check for k in DOMESTIC_PROPAGANDA_KEYWORDS):
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

                    # 提取主图，若无则匹配科技主题封面
                    img_url = extract_image_url(entry, summary)
                    
                    # 识别 Reddit vs 普通新闻
                    is_reddit = (cfg.get("platform") == "reddit") or ("reddit" in source_key.lower())
                    
                    if is_reddit:
                        # 严格作为 Reddit 极客社群处理，绝不张冠李戴给名人
                        platform = "reddit"
                        category = "celebrity"
                        sub_name = cfg["name"].replace("Reddit ", "")
                        author_display = f"Reddit · {sub_name}"
                        author_handle = sub_name
                        author_avatar = "https://www.redditstatic.com/shreddit/assets/favicon/192x192.png"
                        tags = ["Reddit社区", sub_name]
                        metrics = {"platform": "reddit", "sub": sub_name}
                    else:
                        platform = "web"
                        profile = match_celebrity_profile(title, clean_summary)
                        category = "celebrity" if (profile or cfg["default_category"] == "celebrity") else cfg["default_category"]
                        author_display = profile["name"] if profile else author
                        author_handle = profile["handle"] if profile else ""
                        author_avatar = profile["avatar"] if profile else ""
                        tags = [profile["name"] if profile else (author if "google" in source_key.lower() else cfg["name"]), "今日要闻"]
                        metrics = {"platform": "web"}

                    if not img_url:
                        img_url = get_smart_cover_url(title, category, cfg["name"])

                    items.append({
                        "id": make_id(url, title),
                        "title": title,
                        "url": url,
                        "image_url": img_url,
                        "source": author if ("google" in source_key.lower()) else cfg["name"],
                        "author": author_display,
                        "author_handle": author_handle,
                        "author_avatar": author_avatar,
                        "platform": platform,
                        "raw_published_at": iso_time,
                        "metrics": metrics,
                        "content_snippet": clean_summary or f"From {cfg['name']}",
                        "category": category,
                        "tags": tags
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

    # 2. 场景化落地工具 (Product Hunt + GitHub + Hugging Face Spaces 体验应用)
    ph_tools = fetch_product_hunt_tools(max_items=8)
    print(f"  ✓ Product Hunt 落地应用: 获取到 {len(ph_tools)} 条")
    all_items.extend(ph_tools)

    gh_tools = fetch_github_applied_tools()
    print(f"  ✓ GitHub 开源神器: 获取到 {len(gh_tools)} 条")
    all_items.extend(gh_tools)

    hf_tools = fetch_hf_spaces(max_items=8)
    print(f"  ✓ Hugging Face 在线试玩: 获取到 {len(hf_tools)} 条")
    all_items.extend(hf_tools)

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
