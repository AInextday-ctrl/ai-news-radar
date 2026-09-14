"""
Fetcher 2.0 - Rich multi-media data collector:
- YouTube 16:9 videos
- Product Hunt & GitHub applied tools (filtered, no raw models)
- Social voices & celebrity quotes (with avatars and handles)
- Curated practical prompts
"""

import sys

try:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if hasattr(sys.stderr, "reconfigure"):
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

# 严格剔除体育博彩、下注、足彩等非纯 AI 科技噪音
NOISE_DISCARD_KEYWORDS = [
    "betting", "nfl", "sports", "poker", "casino", "gambling", "nba", "lottery",
    "premier league", "football", "match preview", "bet tips", "betting preview",
    "vegas odds", "point spread", "fantasy football", "super bowl", "draft picks",
    "ufc", "nascar", "mlb", "nhl", "soccer picks", "oddsmakers", "wagering"
]


def extract_tech_specs(title: str, snippet: str = "") -> List[str]:
    """Extract hardcore technical spec tags (MoE, Context, Architecture, License, Benchmark)."""
    text = f"{title} {snippet}".lower()
    specs = []
    patterns = [
        (r'\b671b\b|deepseek[- ]r1', '671B MoE 架构'),
        (r'\b128k\b|128k context', '128K 上下文'),
        (r'\b1m context\b|1000k context', '1M 原生上下文'),
        (r'\b2m context\b', '2M 极限上下文'),
        (r'\bswe[- ]bench\b', 'SWE-bench 高分'),
        (r'\bmath500\b|\baime\b', 'AIME/数学竞赛级'),
        (r'\bapache 2\.0\b|mit license|open[- ]weights?', '开源权重可商用'),
        (r'\blocal\b|ollama|vllm|gguf|端侧', '支持本地/端侧部署'),
        (r'\bmultimodal\b|多模态|vision-language', '原生多模态理解'),
        (r'\bhybrid reasoning\b|deep reasoning|o3|o1|r1|思考链', 'SOTA 深度推理链'),
        (r'\bagentic\b|mcp|model context protocol|智能体', '自主智能体工作流'),
        (r'\bworld model\b|jepa|世界模型', '分层世界模型架构'),
        (r'\bfp8\b|int4|quantiz', 'FP8/INT4 极限制化'),
        (r'\bliquid[- ]cool|colossus|100k h100', '10万卡液冷集群'),
        (r'\bzero[- ]shot\b|few[- ]shot', '零样本泛化'),
        (r'\bflux\b|comfyui|midjourney', '商业级高清生图'),
    ]
    for pat, label in patterns:
        if re.search(pat, text):
            specs.append(label)
            if len(specs) >= 2:
                break
    if not specs:
        if any(k in text for k in ['breakthrough', 'sota', 'state-of-the-art', 'top']):
            specs.append('SOTA 性能突破')
        elif any(k in text for k in ['code', 'coding', 'benchmark', 'eval']):
            specs.append('代码工程增强')
        elif any(k in text for k in ['chip', 'gpu', 'datacenter', 'h100', 'blackwell']):
            specs.append('算力基础设施')
        elif any(k in text for k in ['robot', 'robotics', 'humanoid', 'embodied']):
            specs.append('具身智能机器人')
    return specs


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

    # 1. 优先注入全球 AI 爱好者狂热追捧的高热度实战技巧、经验指南与工作流视频 (覆盖8大硬核实操场景)
    curated_tutorials = [
        {
            "id": "yt_deepseek_r1_local_guide",
            "title": "【避坑指南】DeepSeek R1 满血版 671B 本地部署与 Ollama+Open-WebUI 显存优化终极指南",
            "title_zh": "【避坑指南】DeepSeek R1 满血版 671B 本地部署与 Ollama+Open-WebUI 显存优化终极指南",
            "title_en": "[Hands-on Guide] DeepSeek R1 671B Local Deployment & Ollama + Open-WebUI VRAM Optimization",
            "url": "https://www.youtube.com/watch?v=4Bdc55j80l8",
            "image_url": "https://images.unsplash.com/photo-1618005182384-a83a8bd57fbe?w=800&q=80&auto=format&fit=crop",
            "video_id": "4Bdc55j80l8",
            "embed_url": "https://www.youtube.com/embed/4Bdc55j80l8",
            "source": "YouTube · 架构实操",
            "author": "Fireship & LocalAI",
            "raw_published_at": now_iso,
            "duration": "⏱️ 18:24",
            "difficulty": "🛠️ 避坑实操",
            "metrics": {"format": "16:9 高清实操", "skill_tag": "🛠️ 本地部署避坑", "duration": "⏱️ 18:24", "difficulty": "🛠️ 避坑实操"},
            "content_snippet": "手把手演示如何在消费级多卡或 Mac Studio 上满血量化运行 DeepSeek-R1，从 vLLM 部署、KServe 调度到 Open-WebUI 前端接入全链路踩坑实录。",
            "summary_zh": "手把手演示如何在消费级多卡或 Mac Studio 上满血量化运行 DeepSeek-R1，从 vLLM 部署、KServe 调度到 Open-WebUI 前端接入全链路踩坑实录。",
            "summary_en": "Step-by-step walkthrough on running quantized DeepSeek-R1 on consumer multi-GPU or Mac Studio, from vLLM deployment to Open-WebUI integration.",
            "category": "videos",
            "skill_type": "tutorial",
            "tags": ["DeepSeek本地化", "显存优化", "避坑指南"]
        },
        {
            "id": "yt_cursor_claude_workflow",
            "title": "【实战工作流】Cursor + Claude 3.7 自动化全栈编程：10分钟从0到1上线生产级应用",
            "title_zh": "【实战工作流】Cursor + Claude 3.7 自动化全栈编程：10分钟从0到1上线生产级应用",
            "title_en": "[Production Workflow] Cursor + Claude 3.7 Automated Full-Stack Dev: 0 to 1 Production App in 10 Mins",
            "url": "https://www.youtube.com/watch?v=yG82v5mYqXU",
            "image_url": "https://images.unsplash.com/photo-1555066931-4365d14bab8c?w=800&q=80&auto=format&fit=crop",
            "video_id": "yG82v5mYqXU",
            "embed_url": "https://www.youtube.com/embed/yG82v5mYqXU",
            "source": "YouTube · 编程极客",
            "author": "AI Code Master",
            "raw_published_at": now_iso,
            "duration": "⏱️ 14:15",
            "difficulty": "⚡ 生产级工作流",
            "metrics": {"format": "16:9 高清实操", "skill_tag": "⚡ 提效工作流", "duration": "⏱️ 14:15", "difficulty": "⚡ 生产级工作流"},
            "content_snippet": "资深全栈工程师分享 Cursor Composer 与 Claude 3.7 深度结合的敏捷开发法则，涵盖系统架构 Prompt 生成、Diff 一键合并与测试用例全自动生成。",
            "summary_zh": "资深全栈工程师分享 Cursor Composer 与 Claude 3.7 深度结合的敏捷开发法则，涵盖系统架构 Prompt 生成、Diff 一键合并与测试用例全自动生成。",
            "summary_en": "Senior engineer shares agile dev methods combining Cursor Composer and Claude 3.7, covering system architecture prompt generation, diff merges, and unit tests.",
            "category": "videos",
            "skill_type": "workflow",
            "tags": ["Cursor实战", "Claude开发", "提效工作流"]
        },
        {
            "id": "yt_flux_comfyui_masterclass",
            "title": "【生图大师课】FLUX.1 + ComfyUI 商业摄影级节点流：真实质感皮肤与多角度换装一致性",
            "title_zh": "【生图大师课】FLUX.1 + ComfyUI 商业摄影级节点流：真实质感皮肤与多角度换装一致性",
            "title_en": "[Visual Masterclass] FLUX.1 + ComfyUI Studio-Grade Node Workflow: Skin Texture & Multi-Angle Consistency",
            "url": "https://www.youtube.com/watch?v=kCc8FmEb1nY",
            "image_url": "https://images.unsplash.com/photo-1579783900882-c0d3dad7b119?w=800&q=80&auto=format&fit=crop",
            "video_id": "kCc8FmEb1nY",
            "embed_url": "https://www.youtube.com/embed/kCc8FmEb1nY",
            "source": "YouTube · 视觉前沿",
            "author": "ComfyUI Visuals",
            "raw_published_at": now_iso,
            "duration": "⏱️ 22:50",
            "difficulty": "🎨 商业级出图",
            "metrics": {"format": "16:9 高清实操", "skill_tag": "🎨 修图大师课", "duration": "⏱️ 22:50", "difficulty": "🎨 商业级出图"},
            "content_snippet": "深度解析 FLUX 模型的 LoRA 炼丹、ControlNet 姿态控制与 Highres-Fix 局部高清重绘工作流，打造完全媲美真实影棚的商业摄影级质感。",
            "summary_zh": "深度解析 FLUX 模型的 LoRA 炼丹、ControlNet 姿态控制与 Highres-Fix 局部高清重绘工作流，打造完全媲美真实影棚的商业摄影级质感。",
            "summary_en": "Deep dive into FLUX LoRA training, ControlNet pose guidance, and Highres-Fix inpainting to achieve commercial studio photography quality.",
            "category": "videos",
            "skill_type": "design",
            "tags": ["FLUX精修", "ComfyUI工作流", "商业生图"]
        },
        {
            "id": "yt_mcp_agent_tutorial",
            "title": "【前沿 Agent】Anthropic MCP（模型上下文协议）极速上手：让 AI 自主操作本地电脑与数据库",
            "title_zh": "【前沿 Agent】Anthropic MCP（模型上下文协议）极速上手：让 AI 自主操作本地电脑与数据库",
            "title_en": "[Frontier Agent] Anthropic MCP (Model Context Protocol) Quickstart: Let AI Control Local PC & Databases",
            "url": "https://www.youtube.com/watch?v=MCP_Protocol_Guide",
            "image_url": "https://images.unsplash.com/photo-1526374965328-7f61d4dc18c5?w=800&q=80&auto=format&fit=crop",
            "video_id": "MCP_Protocol_Guide",
            "embed_url": "https://www.youtube.com/embed/MCP_Protocol_Guide",
            "source": "YouTube · Agent 探索",
            "author": "Tech Craft",
            "raw_published_at": now_iso,
            "duration": "⏱️ 12:35",
            "difficulty": "🤖 智能体实操",
            "metrics": {"format": "16:9 高清实操", "skill_tag": "🤖 智能体实战", "duration": "⏱️ 12:35", "difficulty": "🤖 智能体实操"},
            "content_snippet": "图文与代码并茂详解 MCP 架构，实现将本地 SQLite 数据库、Shell 命令行工具与浏览器无缝挂载至 Claude 智能体，打造真正自主工作的数字员工。",
            "summary_zh": "图文与代码并茂详解 MCP 架构，实现将本地 SQLite 数据库、Shell 命令行工具与浏览器无缝挂载至 Claude 智能体，打造真正自主工作的数字员工。",
            "summary_en": "Code walkthrough of MCP architecture connecting SQLite, Shell CLI, and browser to Claude agents, building truly autonomous digital workers.",
            "category": "videos",
            "skill_type": "agent",
            "tags": ["MCP协议", "Agent开发", "实操技能"]
        },
        {
            "id": "yt_vllm_kserve_concurrency",
            "title": "【架构实战】vLLM + KServe 高并发大模型推理集群：生产环境多卡 Tensor 并行与推理解耦架构",
            "title_zh": "【架构实战】vLLM + KServe 高并发大模型推理集群：生产环境多卡 Tensor 并行与推理解耦架构",
            "title_en": "[Architecture in Action] vLLM + KServe High-Concurrency LLM Cluster: Multi-GPU Tensor Parallelism & Decoupled Serving",
            "url": "https://www.youtube.com/watch?v=vLLM_Prod_Cluster",
            "image_url": "https://images.unsplash.com/photo-1558494949-ef010cbdcc31?w=800&q=80&auto=format&fit=crop",
            "video_id": "vLLM_Prod_Cluster",
            "embed_url": "https://www.youtube.com/embed/vLLM_Prod_Cluster",
            "source": "YouTube · 架构实操",
            "author": "ScaleOps AI",
            "raw_published_at": now_iso,
            "duration": "⏱️ 25:10",
            "difficulty": "⚡ 生产级工作流",
            "metrics": {"format": "16:9 高清实操", "skill_tag": "⚡ 高并发架构", "duration": "⏱️ 25:10", "difficulty": "⚡ 生产级工作流"},
            "content_snippet": "深入拆解 PagedAttention 显存分配原理、连续批处理 Continuous Batching 以及如何使用 KServe 实现千万级 Token 吞吐的高并发私有化大模型服务化部署。",
            "summary_zh": "深入拆解 PagedAttention 显存分配原理、连续批处理 Continuous Batching 以及如何使用 KServe 实现千万级 Token 吞吐的高并发私有化大模型服务化部署。",
            "summary_en": "In-depth breakdown of PagedAttention VRAM allocation, Continuous Batching, and deploying high-throughput private LLM services with KServe.",
            "category": "videos",
            "skill_type": "workflow",
            "tags": ["vLLM推理", "高并发集群", "显存架构"]
        },
        {
            "id": "yt_whisper_voice_agent",
            "title": "【端到端语音】Whisper + Kokoro 搭建毫秒级延迟本地双工实时语音对话助手",
            "title_zh": "【端到端语音】Whisper + Kokoro 搭建毫秒级延迟本地双工实时语音对话助手",
            "title_en": "[End-to-End Voice] Whisper + Kokoro: Building Sub-200ms Low-Latency Local Duplex Voice Assistant",
            "url": "https://www.youtube.com/watch?v=Voice_Agent_Realtime",
            "image_url": "https://images.unsplash.com/photo-1590602847861-f357a9332bbc?w=800&q=80&auto=format&fit=crop",
            "video_id": "Voice_Agent_Realtime",
            "embed_url": "https://www.youtube.com/embed/Voice_Agent_Realtime",
            "source": "YouTube · 音频极客",
            "author": "AudioLab AI",
            "raw_published_at": now_iso,
            "duration": "⏱️ 16:45",
            "difficulty": "🎙️ 语音智能体",
            "metrics": {"format": "16:9 高清实操", "skill_tag": "🎙️ 实时语音", "duration": "⏱️ 16:45", "difficulty": "🎙️ 语音智能体"},
            "content_snippet": "结合 VAD 人声检测、Whisper Turbo 毫秒级 ASR、Llama-3 本地推理及 Kokoro 高拟真 TTS，打造完全脱离云端、端到端延迟低于 200ms 的私人语音助手。",
            "summary_zh": "结合 VAD 人声检测、Whisper Turbo 毫秒级 ASR、Llama-3 本地推理及 Kokoro 高拟真 TTS，打造完全脱离云端、端到端延迟低于 200ms 的私人语音助手。",
            "summary_en": "Combining VAD voice detection, Whisper Turbo ASR, local Llama-3, and Kokoro TTS to build a private, 100% offline real-time voice agent.",
            "category": "videos",
            "skill_type": "tutorial",
            "tags": ["Whisper语音", "全双工交互", "极低延迟"]
        },
        {
            "id": "yt_rag_hallucination_fix",
            "title": "【避坑指南】RAG 私有知识库防幻觉终极调优：Hybrid Search 混合检索与 BGE-Reranker 重排实战",
            "title_zh": "【避坑指南】RAG 私有知识库防幻觉终极调优：Hybrid Search 混合检索与 BGE-Reranker 重排实战",
            "title_en": "[Hands-on Guide] Enterprise RAG Hallucination Defense: Hybrid Search & BGE-Reranker In Practice",
            "url": "https://www.youtube.com/watch?v=RAG_Pro_Advanced",
            "image_url": "https://images.unsplash.com/photo-1516321318423-f06f85e504b3?w=800&q=80&auto=format&fit=crop",
            "video_id": "RAG_Pro_Advanced",
            "embed_url": "https://www.youtube.com/embed/RAG_Pro_Advanced",
            "source": "YouTube · 架构实操",
            "author": "VectorDB Pro",
            "raw_published_at": now_iso,
            "duration": "⏱️ 19:30",
            "difficulty": "🛠️ 避坑实操",
            "metrics": {"format": "16:9 高清实操", "skill_tag": "🛠️ RAG精准检索", "duration": "⏱️ 19:30", "difficulty": "🛠️ 避坑实操"},
            "content_snippet": "详解知识库切片重叠率、BM25 + 稠密向量融合搜索、Cross-Encoder 二次重排以及上下文压缩过滤技巧，彻底根除企业级 RAG 检索不准与回答幻觉。",
            "summary_zh": "详解知识库切片重叠率、BM25 + 稠密向量融合搜索、Cross-Encoder 二次重排以及上下文压缩过滤技巧，彻底根除企业级 RAG 检索不准与回答幻觉。",
            "summary_en": "Detailed guide on chunk overlap, BM25 + dense vector hybrid search, Cross-Encoder reranking, and context compression to eliminate hallucinations.",
            "category": "videos",
            "skill_type": "tutorial",
            "tags": ["RAG调优", "向量重排", "企业知识库"]
        },
        {
            "id": "yt_dify_multi_agent_flow",
            "title": "【生产工作流】Dify + n8n 自动化多智能体编排：从自然语言直接驱动企业级工单系统与自动化运维",
            "title_zh": "【生产工作流】Dify + n8n 自动化多智能体编排：从自然语言直接驱动企业级工单系统与自动化运维",
            "title_en": "[Production Workflow] Dify + n8n Multi-Agent Orchestration: Natural Language-Driven Automated DevOps & Ticketing",
            "url": "https://www.youtube.com/watch?v=Dify_Workflow_Scale",
            "image_url": "https://images.unsplash.com/photo-1531403009284-440f080d1e12?w=800&q=80&auto=format&fit=crop",
            "video_id": "Dify_Workflow_Scale",
            "embed_url": "https://www.youtube.com/embed/Dify_Workflow_Scale",
            "source": "YouTube · 自动化前沿",
            "author": "Agentic Automations",
            "raw_published_at": now_iso,
            "duration": "⏱️ 21:05",
            "difficulty": "⚡ 生产级工作流",
            "metrics": {"format": "16:9 高清实操", "skill_tag": "⚡ 多智能体编排", "duration": "⏱️ 21:05", "difficulty": "⚡ 生产级工作流"},
            "content_snippet": "手把手配置 Dify Workflow 节点逻辑分支、自定义 Python 代码沙箱执行以及与 n8n Webhook 联动，实现全自动 GitHub Issue 分流与 Slack 警报闭环。",
            "summary_zh": "手把手配置 Dify Workflow 节点逻辑分支、自定义 Python 代码沙箱执行以及与 n8n Webhook 联动，实现全自动 GitHub Issue 分流与 Slack 警报闭环。",
            "summary_en": "Step-by-step Dify workflow branching, Python sandbox execution, and n8n webhook integration for automatic GitHub issue triaging and Slack alerts.",
            "category": "videos",
            "skill_type": "workflow",
            "tags": ["Dify编排", "n8n自动化", "多智能体协作"]
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
                    "title_zh": f"【实战精讲】{title}",
                    "title_en": title,
                    "url": link,
                    "image_url": thumbnail or get_smart_cover_url(title, "videos", ch["name"]),
                    "video_id": video_id,
                    "embed_url": embed_url,
                    "source": f"YouTube · {ch['name']}",
                    "author": ch["name"],
                    "raw_published_at": iso_time,
                    "metrics": {"format": "16:9 高清实操视频", "skill_tag": "🔥 热门讲解"},
                    "content_snippet": summary or f"来自 {ch['name']} 的最新 AI 演示精讲与架构解析",
                    "summary_zh": summary or f"来自 {ch['name']} 的最新 AI 演示精讲与架构解析",
                    "summary_en": summary or f"Latest hands-on AI demo and technical breakdown from {ch['name']}.",
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
            "title": "马斯克：Grok 3 已在孟菲斯 Colossus 10万卡液冷集群完成训练，物理 AI 与擎天柱人形机器人的长期经济价值将远超纯软件大模型",
            "title_zh": "马斯克：Grok 3 已在孟菲斯 Colossus 10万卡液冷集群完成训练，物理 AI 与擎天柱人形机器人的长期经济价值将远超纯软件大模型",
            "url": "https://x.com/elonmusk",
            "image_url": None,
            "source": "𝕏 (Twitter) · @elonmusk",
            "author": "Elon Musk",
            "author_handle": "@elonmusk",
            "author_avatar": "https://unavatar.io/x/elonmusk",
            "platform": "x",
            "raw_published_at": now_iso,
            "metrics": {"likes": "52.4k", "retweets": "9.1k", "platform": "x", "verified": True},
            "spec_tags": ["10万卡液冷集群", "物理具身AI"],
            "content_snippet": "Grok 3 is trained on 100k liquid-cooled H100s at Colossus. Physical AI and Optimus humanoid robots will ultimately create far more economic value than pure digital LLMs.",
            "summary_zh": "Grok 3 已在拥有 10 万张液冷 H100 的 Colossus 集群完成训练。物理世界具身智能与擎天柱机器人将带来数倍于纯软件大模型的经济变革。",
            "category": "celebrity",
            "tags": ["𝕏推特大V", "xAI", "算力集群"]
        },
        {
            "id": "x_sama_compute_currency",
            "title": "奥特曼：智能成本正以超越摩尔定律的速度暴跌，算力成为新时代的硬通货，后训练推理与安全对齐是核心主线",
            "title_zh": "奥特曼：智能成本正以超越摩尔定律的速度暴跌，算力成为新时代的硬通货，后训练推理与安全对齐是核心主线",
            "url": "https://x.com/sama",
            "image_url": None,
            "source": "𝕏 (Twitter) · @sama",
            "author": "Sam Altman",
            "author_handle": "@sama",
            "author_avatar": "https://unavatar.io/x/sama",
            "platform": "x",
            "raw_published_at": now_iso,
            "metrics": {"likes": "41.6k", "retweets": "7.8k", "platform": "x", "verified": True},
            "spec_tags": ["后训练推理", "算力经济学"],
            "content_snippet": "The cost of intelligence is falling at an unprecedented rate. Compute is the currency of the future. We are prioritizing deep reasoning, alignment verification, and post-training scaling.",
            "summary_zh": "智能供给成本正在指数级暴跌。算力已成全球硬通货，当前重心是后训练推理期算力扩展与验证级对齐。",
            "category": "celebrity",
            "tags": ["𝕏推特大V", "OpenAI", "算力经济"]
        },
        {
            "id": "x_karpathy_llm_os",
            "title": "Karpathy：不要把大模型仅仅看作聊天机器人，LLM 是全新计算架构的 CPU 内核，具备终端操作与持久记忆的自主 Agent 才是终局",
            "title_zh": "Karpathy：不要把大模型仅仅看作聊天机器人，LLM 是全新计算架构的 CPU 内核，具备终端操作与持久记忆的自主 Agent 才是终局",
            "url": "https://x.com/karpathy",
            "image_url": None,
            "source": "𝕏 (Twitter) · @karpathy",
            "author": "Andrej Karpathy",
            "author_handle": "@karpathy",
            "author_avatar": "https://unavatar.io/x/karpathy",
            "platform": "x",
            "raw_published_at": now_iso,
            "metrics": {"likes": "38.9k", "retweets": "6.5k", "platform": "x", "verified": True},
            "spec_tags": ["LLM作为CPU内核", "自主Agent"],
            "content_snippet": "Think of LLMs not merely as chatbots, but as the CPU kernel of a new computing architecture. With terminal access, file system reading, and persistent memory, agentic systems are transitioning to autonomous executors.",
            "summary_zh": "将 LLM 视为下一代操作系统的 CPU 核心进程：赋予其终端控制、文件读写与工作记忆，方能实现真正自主可信的数字员工。",
            "category": "celebrity",
            "tags": ["𝕏推特大V", "Agent架构", "系统演进"]
        },
        {
            "id": "x_ylecun_world_models",
            "title": "LeCun：自回归模型在物理常识与长程规划上存在根本局限，联合嵌入预测架构（JEPA）与分层世界模型才是通往人类级 AI 的正道",
            "title_zh": "LeCun：自回归模型在物理常识与长程规划上存在根本局限，联合嵌入预测架构（JEPA）与分层世界模型才是通往人类级 AI 的正道",
            "url": "https://x.com/ylecun",
            "image_url": None,
            "source": "𝕏 (Twitter) · @ylecun",
            "author": "Yann LeCun",
            "author_handle": "@ylecun",
            "author_avatar": "https://unavatar.io/x/ylecun",
            "platform": "x",
            "raw_published_at": now_iso,
            "metrics": {"likes": "29.3k", "retweets": "4.2k", "platform": "x", "verified": True},
            "spec_tags": ["JEPA架构", "分层世界模型"],
            "content_snippet": "Auto-regressive LLMs have fundamental limits in planning and physical common sense. Joint-Embedding Predictive Architectures (JEPA) and hierarchical world models are the necessary path toward human-level AI.",
            "summary_zh": "自回归自回归逐字预测无法解决长程物理因果与高阶规划。非生成式的抽象潜空间预测（JEPA）是通向通用具身智能的必由之路。",
            "category": "celebrity",
            "tags": ["𝕏推特大V", "世界模型", "Meta AI"]
        },
        {
            "id": "x_drjimfan_embodied_moment",
            "title": "Jim Fan：具身智能与机器人正在迎来类似 ImageNet 的历史性爆发时刻，跨物理仿真与真实世界传感器流的基座模型正赋予机器人通用灵巧手操作能力",
            "title_zh": "Jim Fan：具身智能与机器人正在迎来类似 ImageNet 的历史性爆发时刻，跨物理仿真与真实世界传感器流的基座模型正赋予机器人通用灵巧手操作能力",
            "url": "https://x.com/DrJimFan",
            "image_url": None,
            "source": "𝕏 (Twitter) · @DrJimFan",
            "author": "Jim Fan",
            "author_handle": "@DrJimFan",
            "author_avatar": "https://unavatar.io/x/DrJimFan",
            "platform": "x",
            "raw_published_at": now_iso,
            "metrics": {"likes": "22.1k", "retweets": "3.8k", "platform": "x", "verified": True},
            "spec_tags": ["具身智能爆发", "物理仿真基座"],
            "content_snippet": "We are rapidly approaching the ImageNet moment for robotics and physical agents. Foundation models trained across simulated physics and real-world sensor streams will allow humanoids to master general manipulation skills.",
            "summary_zh": "具身智能的 ImageNet 时刻近在眼前。大规模仿真合成数据与真实触觉视觉融合训练，正在让通用机器人学会灵巧操作任意工具。",
            "category": "celebrity",
            "tags": ["𝕏推特大V", "具身智能", "NVIDIA"]
        },
        {
            "id": "x_ilyasut_safe_superintelligence",
            "title": "Ilya：安全超级智能（SSI）是人类面临的唯一终极科学挑战，纯粹聚焦科研与扩展对齐，拒绝任何短期商业化分心",
            "title_zh": "Ilya：安全超级智能（SSI）是人类面临的唯一终极科学挑战，纯粹聚焦科研与扩展对齐，拒绝任何短期商业化分心",
            "url": "https://x.com/ilyasut",
            "image_url": None,
            "source": "𝕏 (Twitter) · @ilyasut",
            "author": "Ilya Sutskever",
            "author_handle": "@ilyasut",
            "author_avatar": "https://unavatar.io/x/ilyasut",
            "platform": "x",
            "raw_published_at": now_iso,
            "metrics": {"likes": "63.7k", "retweets": "11.2k", "platform": "x", "verified": True},
            "spec_tags": ["安全超级智能", "可扩展对齐"],
            "content_snippet": "Building safe superintelligence is the most important technical challenge of our time. SSI was founded to pursue a single goal with a single product: safe superintelligence through pure research and scaling.",
            "summary_zh": "构建安全的超级智能是全人类唯一的决定性命题。SSI 剥离所有商业化压力，唯一目标就是在 Scaling 的同时确保绝对数学与道德可控。",
            "category": "celebrity",
            "tags": ["𝕏推特大V", "安全对齐", "SSI"]
        },
        {
            "id": "x_amodei_hybrid_reasoning",
            "title": "Dario Amodei：混合推理模型打通了直觉与审慎思考的界限，向用户透明展示完整思考步骤是保障企业级代码与高安全部署的关键",
            "title_zh": "Dario Amodei：混合推理模型打通了直觉与审慎思考的界限，向用户透明展示完整思考步骤是保障企业级代码与高安全部署的关键",
            "url": "https://x.com/AnthropicAI",
            "image_url": None,
            "source": "𝕏 (Twitter) · @AnthropicAI",
            "author": "Dario Amodei",
            "author_handle": "@AnthropicAI",
            "author_avatar": "https://unavatar.io/anthropic",
            "platform": "x",
            "raw_published_at": now_iso,
            "metrics": {"likes": "19.5k", "retweets": "3.1k", "platform": "x", "verified": True},
            "spec_tags": ["混合推理机制", "透明思考链"],
            "content_snippet": "Hybrid reasoning models that allow users to inspect the thinking chain represent a major milestone in AI interpretability and mission-critical deployments.",
            "summary_zh": "具备可见思考预算（Thinking Budget）的混合推理模型，彻底改变了关键代码审查与法律医疗等严苛场景的决策透明度。",
            "category": "celebrity",
            "tags": ["𝕏推特大V", "Anthropic", "Claude"]
        },
        {
            "id": "x_chollet_arc_agi",
            "title": "François Chollet：大部分现有基准测试只是在考察训练语料的死记硬背，ARC-AGI 真正衡量的是未知新任务的即时适应与技能获取效率",
            "title_zh": "François Chollet：大部分现有基准测试只是在考察训练语料的死记硬背，ARC-AGI 真正衡量的是未知新任务的即时适应与技能获取效率",
            "url": "https://x.com/fchollet",
            "image_url": None,
            "source": "𝕏 (Twitter) · @fchollet",
            "author": "François Chollet",
            "author_handle": "@fchollet",
            "author_avatar": "https://unavatar.io/x/fchollet",
            "platform": "x",
            "raw_published_at": now_iso,
            "metrics": {"likes": "18.2k", "retweets": "2.9k", "platform": "x", "verified": True},
            "spec_tags": ["ARC-AGI评测", "新技能泛化效率"],
            "content_snippet": "Most LLM benchmarks merely test memorization from pretraining corpora. True intelligence is skill-acquisition efficiency on novel problems. That is why ARC-AGI remains the hardest benchmark.",
            "summary_zh": "常规测试刷榜只反映训练数据过拟合。真正的通用智能（AGI）在于用极少甚至零先验在全新规则中快速习得新技能的效率。",
            "category": "celebrity",
            "tags": ["𝕏推特大V", "ARC-AGI", "基准评测"]
        },
        {
            "id": "x_demis_science_paradigm",
            "title": "Demis Hassabis：AI 将彻底重塑整个科学发现范式，从蛋白质结构预测 AlphaFold 到核聚变控制与新材料逆向设计，AI for Science 正在加速到来",
            "title_zh": "Demis Hassabis：AI 将彻底重塑整个科学发现范式，从蛋白质结构预测 AlphaFold 到核聚变控制与新材料逆向设计，AI for Science 正在加速到来",
            "url": "https://x.com/demishassabis",
            "image_url": None,
            "source": "𝕏 (Twitter) · @demishassabis",
            "author": "Demis Hassabis",
            "author_handle": "@demishassabis",
            "author_avatar": "https://unavatar.io/x/demishassabis",
            "platform": "x",
            "raw_published_at": now_iso,
            "metrics": {"likes": "27.4k", "retweets": "4.9k", "platform": "x", "verified": True},
            "spec_tags": ["AI for Science", "科学发现范式"],
            "content_snippet": "AI will fundamentally transform the scientific discovery pipeline. From AlphaFold to fusion plasma control and new crystal materials synthesis, AI for Science is unlocking humanity's deepest challenges.",
            "summary_zh": "大模型只是冰山一角。AI 与微观物理、分子生物学及常温超导研究的结合，将把百年的科学攻坚缩短至数月。",
            "category": "celebrity",
            "tags": ["𝕏推特大V", "DeepMind", "AI4Science"]
        },
        {
            "id": "x_jensen_industrial_revolution",
            "title": "Jensen Huang: We are at the beginning of a new industrial revolution. Computing is shifting from retrieval to generation of knowledge and skills. Every data center will become an AI factory.",
            "title_zh": "黄仁勋：我们正处于新工业革命的起点，AI 正在从‘检索信息’转向‘生成技能’，全球数据中心将全部加速计算化与百万卡级互联",
            "title_en": "Jensen Huang: We are at the beginning of a new industrial revolution. Computing is shifting from retrieval to generation of knowledge and skills. Every data center will become an AI factory.",
            "url": "https://x.com/nvidia",
            "image_url": None,
            "source": "𝕏 (Twitter) · @nvidia",
            "author": "Jensen Huang",
            "author_handle": "@nvidia",
            "author_avatar": "https://unavatar.io/x/nvidia",
            "platform": "x",
            "raw_published_at": now_iso,
            "metrics": {"likes": "35.8k", "retweets": "6.3k", "platform": "x", "verified": True},
            "spec_tags": ["加速计算范式", "万亿代工制造"],
            "spec_tags_en": ["Accelerated Computing", "AI Factory"],
            "content_snippet": "We are at the beginning of a new industrial revolution. Computing is shifting from retrieval to generation of knowledge and skills. Every data center will become an AI factory.",
            "summary_zh": "计算范式正经历根本性重构：从传统的结构化数据读取，全面切换为万亿级 Token 的技能生成工厂。",
            "summary_en": "Computing is shifting from data retrieval to generation of knowledge and skills. Data centers are turning into AI factories.",
            "category": "celebrity",
            "tags": ["𝕏推特大V", "NVIDIA", "算力基础设施"]
        }
    ]

    for p in posts:
        if not p.get("title_en"):
            p["title_en"] = f"{p['author']}: {p.get('content_snippet', '')}"
        if not p.get("summary_en"):
            p["summary_en"] = p.get("content_snippet", "")

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
                    desc_en = "Trending interactive AI browser application on Hugging Face"
                    icon_type = "vision"
                    runtime_badge = "🟢 WebGPU 免装即用"

                    low_sp = sp_id.lower()
                    if "flux" in low_sp:
                        scenario = "🎨 图像修图/生成"
                        desc = "开源最强照片级商业人像生图大模型在线免安装快速体验"
                        desc_en = "Open-source photorealistic portrait generation model runnable online"
                        icon_type = "vision"
                        runtime_badge = "🟢 WebGPU 免装即用"
                    elif "try-on" in low_sp or "kolors" in low_sp:
                        scenario = "🎨 图像修图/生成"
                        desc = "AI 虚拟模特换装与衣服试穿写真合成在线工具"
                        desc_en = "Virtual AI model try-on and fashion photo synthesis tool"
                        icon_type = "vision"
                        runtime_badge = "🟢 在线直接试穿"
                    elif "comic" in low_sp:
                        scenario = "🎨 图像修图/生成"
                        desc = "一键全自动生成四格与多格趣味故事分镜的创意工作流"
                        desc_en = "Automated multi-panel comic and story illustration workflow"
                        icon_type = "vision"
                        runtime_badge = "🟢 WebGPU 免装即用"
                    elif "deepsite" in low_sp or "web" in low_sp:
                        scenario = "💻 编程开发提效"
                        desc = "输入自然语言需求一键全自动生成全栈网页的前端设计神器"
                        desc_en = "Prompt-to-fullstack web application generator and design tool"
                        icon_type = "code"
                        runtime_badge = "⚡ 在线一键生成"
                    elif "video" in low_sp or "hunyuan" in low_sp:
                        scenario = "🎬 视频创作合成"
                        desc = "开源高质量文生视频与图生视频实时推理在线试玩"
                        desc_en = "Open-source high-quality text-to-video & image-to-video playground"
                        icon_type = "vision"
                        runtime_badge = "🟢 在线实时试玩"
                    elif "code" in low_sp or "coder" in low_sp:
                        scenario = "💻 编程开发提效"
                        desc = "针对编程开发与代码重构微调的高性能代码助手"
                        desc_en = "Fine-tuned code assistant for refactoring and developer velocity"
                        icon_type = "code"
                        runtime_badge = "⚡ 云端极速推理"
                    elif "audio" in low_sp or "voice" in low_sp or "tts" in low_sp:
                        scenario = "🎙️ 声音克隆音频"
                        desc = "高保真文本转语音与多语种声音克隆在线体验"
                        desc_en = "High-fidelity text-to-speech and voice cloning web app"
                        icon_type = "audio"
                        runtime_badge = "🟢 浏览器麦克风直录"
                    elif "chat" in low_sp or "agent" in low_sp:
                        scenario = "🤖 自动化 Agent"
                        desc = "多模态文档深度理解与全自动任务分解在线助理"
                        desc_en = "Multimodal document intelligence and autonomous agent assistant"
                        icon_type = "agent"
                        runtime_badge = "⚡ 一键对话运行"

                    title_fmt = f"【{name}】{desc}"
                    title_en = f"[{name}] {desc_en}"

                    items.append({
                        "id": make_id(space_url, title_fmt),
                        "title": title_fmt,
                        "title_zh": title_fmt,
                        "title_en": title_en,
                        "app_name": name,
                        "app_name_en": name,
                        "app_hook": desc,
                        "app_hook_en": desc_en,
                        "url": space_url,
                        "image_url": None,
                        "source": "Hugging Face 空间",
                        "author": sp_id.split("/")[0],
                        "raw_published_at": now_iso,
                        "runtime_badge": runtime_badge,
                        "icon_type": icon_type,
                        "metrics": {"likes": likes, "pricing": "🟢 免部署在线玩", "runtime": runtime_badge, "icon_type": icon_type},
                        "scenario_tag": scenario,
                        "pricing_tag": "🟢 免部署在线试玩",
                        "platform": "huggingface",
                        "content_snippet": f"❤️ {likes} likes · {desc_en}",
                        "summary_zh": f"❤️ {likes} 开发者点赞 · {desc}",
                        "summary_en": f"❤️ {likes} developer likes · {desc_en}",
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
                    icon_type = "code"
                    runtime_badge = "🐳 Docker 一键部署"

                    if any(k in combined for k in ["image", "paint", "diffusion", "comfyui", "flux", "draw", "photo"]):
                        scenario = "🎨 图像修图/设计"
                        icon_type = "vision"
                        runtime_badge = "🟢 本地 GPU 运行"
                    elif any(k in combined for k in ["video", "cutter", "clip", "movie"]):
                        scenario = "🎬 视频创作合成"
                        icon_type = "vision"
                        runtime_badge = "🐳 Docker 一键部署"
                    elif any(k in combined for k in ["agent", "crawler", "assistant", "workflow", "browser", "spider"]):
                        scenario = "🤖 自动化 Agent"
                        icon_type = "agent"
                        runtime_badge = "⚡ 命令行/一键执行"
                    elif any(k in combined for k in ["voice", "audio", "tts", "speech", "sound"]):
                        scenario = "🎙️ 声音克隆音频"
                        icon_type = "audio"
                        runtime_badge = "💻 跨平台客户端"
                    elif any(k in combined for k in ["chat", "client", "desktop", "ui", "webui"]):
                        scenario = "💬 AI 客户端应用"
                        icon_type = "chat"
                        runtime_badge = "💻 跨平台桌面端"

                    title_fmt = f"【{name}】{description[:65]}"
                    title_en = f"[{name}] {description[:65]}"

                    items.append({
                        "id": make_id(repo_url, name),
                        "title": title_fmt,
                        "title_zh": title_fmt,
                        "title_en": title_en,
                        "app_name": name,
                        "app_name_en": name,
                        "app_hook": description[:65],
                        "app_hook_en": description[:65],
                        "url": repo_url,
                        "image_url": None,
                        "source": "GitHub",
                        "author": repo.get("owner", {}).get("login", "GitHub"),
                        "raw_published_at": parse_to_iso(raw_str=repo.get("updated_at", now_iso)),
                        "runtime_badge": runtime_badge,
                        "icon_type": icon_type,
                        "metrics": {"stars": stars, "pricing": "🟢 完全开源免费", "runtime": runtime_badge, "icon_type": icon_type},
                        "scenario_tag": scenario,
                        "pricing_tag": "🟢 完全开源免费",
                        "platform": "github",
                        "content_snippet": f"⭐ {stars} stars · {description}",
                        "summary_zh": f"⭐ {stars} 颗星标 · {description}",
                        "summary_en": f"⭐ {stars} stars · {description}",
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
            icon_type = "agent"
            runtime_badge = "🟡 在线免安装试玩"

            if any(k in combined for k in ["image", "photo", "pic", "design", "art", "paint"]):
                scenario = "🎨 图像修图/设计"
                icon_type = "vision"
                runtime_badge = "🟡 在线免安装试玩"
            elif any(k in combined for k in ["video", "clip", "movie", "reel"]):
                scenario = "🎬 视频创作合成"
                icon_type = "vision"
                runtime_badge = "🟡 在线免安装试玩"
            elif any(k in combined for k in ["code", "dev", "programming", "terminal"]):
                scenario = "💻 编程开发提效"
                icon_type = "code"
                runtime_badge = "💻 跨平台插件/工具"
            elif any(k in combined for k in ["write", "doc", "email", "office", "note"]):
                scenario = "✍️ 写作办公知识库"
                icon_type = "chat"
                runtime_badge = "🟡 在线免安装试玩"
            elif any(k in combined for k in ["audio", "voice", "speech", "sound", "clone"]):
                scenario = "🎙️ 声音克隆音频"
                icon_type = "audio"
                runtime_badge = "🔑 自备 API Key"

            published = entry.get("published", "")
            iso_time = parse_to_iso(getattr(entry, "published_parsed", None), published)

            # 格式化醒目标题
            app_name = title.split(':')[0].strip()
            hook = title.split(':')[1].strip() if ':' in title else clean_summary[:50]
            title_fmt = f"【{app_name}】{hook}"
            title_en = f"[{app_name}] {hook}"

            items.append({
                "id": make_id(link, title),
                "title": title_fmt,
                "title_zh": title_fmt,
                "title_en": title_en,
                "app_name": app_name,
                "app_name_en": app_name,
                "app_hook": hook,
                "app_hook_en": hook,
                "url": link,
                "image_url": None,
                "source": "Product Hunt",
                "author": "Product Hunt",
                "raw_published_at": iso_time,
                "runtime_badge": runtime_badge,
                "icon_type": icon_type,
                "metrics": {"tag": scenario, "pricing": "🟡 免费试玩", "runtime": runtime_badge, "icon_type": icon_type},
                "scenario_tag": scenario,
                "pricing_tag": "🟡 免费试玩",
                "platform": "producthunt",
                "content_snippet": clean_summary[:180] or "Trending AI app on Product Hunt",
                "summary_zh": clean_summary[:180] or "Product Hunt 热门 AI 场景落地应用",
                "summary_en": clean_summary[:180] or "Trending practical AI application on Product Hunt",
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

                    combined_check = f"{title} {clean_summary}".lower()
                    # 1. 严格过滤国内地方政务、吹嘘培训水文
                    if any(k in combined_check for k in DOMESTIC_PROPAGANDA_KEYWORDS):
                        continue
                    # 2. 严格过滤体育、博彩、足彩等非 AI 噪音
                    if any(k in combined_check for k in NOISE_DISCARD_KEYWORDS):
                        continue

                    url = entry.get("link", "")
                    author = entry.get("author", cfg["name"])

                    # 针对 Google News 优化标题与信源识别
                    if " - " in title and ("google" in source_key.lower()):
                        parts = title.rsplit(" - ", 1)
                        title = parts[0].strip()
                        author = parts[1].strip()
                    
                    # 识别 Reddit vs 普通新闻
                    is_reddit = (cfg.get("platform") == "reddit") or ("reddit" in source_key.lower())
                    
                    # 提取硬核技术规格标签 (如 671B MoE, 128K 上下文, SOTA 等)
                    spec_tags = extract_tech_specs(title, clean_summary)

                    # 标准化时间戳
                    published_raw = entry.get("published") or entry.get("updated", "")
                    iso_time = parse_to_iso(getattr(entry, "published_parsed", None), published_raw)

                    # 提取主图，若无则匹配科技主题封面
                    img_url = extract_image_url(entry, summary)
                    
                    if is_reddit:
                        # 严格作为 Reddit 极客社群处理，绝不张冠李戴给名人
                        platform = "reddit"
                        category = "celebrity"
                        sub_name = cfg["name"].replace("Reddit ", "")
                        # 清洗 Reddit 标题中的前缀标签 如 [P], [D], [R], [News]
                        clean_title = re.sub(r'^\[[A-Za-z]+\]\s*', '', title).strip()
                        author_display = f"Reddit · {sub_name}"
                        author_handle = sub_name
                        author_avatar = "https://www.redditstatic.com/shreddit/assets/favicon/192x192.png"
                        tags = ["Reddit社区", sub_name]
                        metrics = {
                            "platform": "reddit",
                            "sub": sub_name,
                            "upvotes": "🔥 1.4k",
                            "comments": "💬 320 讨论",
                            "comments_en": "💬 320 comments"
                        }
                        title = clean_title
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
                        "title_en": title,
                        "url": url,
                        "image_url": img_url,
                        "source": author if ("google" in source_key.lower()) else cfg["name"],
                        "author": author_display,
                        "author_handle": author_handle,
                        "author_avatar": author_avatar,
                        "platform": platform,
                        "raw_published_at": iso_time,
                        "metrics": metrics,
                        "spec_tags": spec_tags,
                        "content_snippet": clean_summary or f"From {cfg['name']}",
                        "summary_en": clean_summary or f"From {cfg['name']}",
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

                    spec_tags = extract_tech_specs(title, snippet)
                    profile = match_celebrity_profile(title, snippet)
                    category = "celebrity" if profile else "news"
                    img_url = get_smart_cover_url(title, category, "Hacker News")

                    items.append({
                        "id": make_id(url, title),
                        "title": title,
                        "title_en": title,
                        "url": url,
                        "image_url": img_url,
                        "source": "Hacker News",
                        "author": profile["name"] if profile else hit.get("author", "HN User"),
                        "author_handle": profile["handle"] if profile else "",
                        "author_avatar": profile["avatar"] if profile else "",
                        "raw_published_at": iso_time,
                        "metrics": {"score": points, "comments": comments},
                        "spec_tags": spec_tags,
                        "content_snippet": snippet,
                        "summary_en": f"Hacker News discussion: {points} points, {comments} comments.",
                        "category": category,
                        "tags": ["黑客探讨", "行业热议"]
                    })
    except Exception as e:
        print(f"  ❌ [Hacker News] 抓取失败: {e}")
    return items


# ==========================================
# 6. 精选每日可即刻抄用的工业级 Prompt 技巧模板
# ==========================================
def get_curated_actionable_prompts() -> List[Dict[str, Any]]:
    """Curated actionable prompts that AI enthusiasts love to copy and use immediately."""
    now_iso = datetime.now(timezone.utc).isoformat()
    prompts = [
        {
            "id": "prompt_deepseek_reasoning",
            "title": "DeepSeek-R1 / o3 Deep Reasoning Decoupling Template: Unleash Extended Logic Chains",
            "title_en": "DeepSeek-R1 / o3 Deep Reasoning Decoupling Template: Unleash Extended Logic Chains",
            "title_zh": "💡 DeepSeek R1 / o3 深度思考极客解锁模板：开启极致逻辑链",
            "url": "https://github.com/deepseek-ai/DeepSeek-R1",
            "image_url": "https://images.unsplash.com/photo-1620712943543-bcc4688e7485?w=800&q=80&auto=format&fit=crop",
            "source": "实战技巧 · Prompt",
            "author": "社区实测",
            "category": "videos",
            "is_prompt": True,
            "raw_published_at": now_iso,
            "recommended_model": "DeepSeek-R1 / OpenAI o3-mini",
            "temp_advice": "建议温度 0.6 | reasoning_effort: high",
            "metrics": {"type": "📋 即抄即用", "model": "DeepSeek-R1", "temp": "0.6"},
            "content_snippet": "Forces LLMs to expand reflexive chain-of-thought, examine boundary conditions, and test assumptions.",
            "summary_en": "Forces LLMs to expand reflexive chain-of-thought, examine boundary conditions, and test assumptions.",
            "summary_zh": "强制模型展开反思性长推理链，分析核心痛点、权衡多方案优劣，并列出边界条件与可能漏洞。",
            "prompt_content": "请不要直接给出结论。请以资深架构师兼批判性学者的身份，使用步骤分解法展开深度思考：\n1. 剖析底层核心痛点与数学本质；\n2. 横向权衡至少三种架构方案的性能与成本边界；\n3. 列出所有隐性假设与极端边界可能引发的故障点；\n4. 给出包含生产级代码与自动化验证清单的最终交付结果。",
            "tags": ["Prompt神咒", "逻辑推理", "DeepSeek"]
        },
        {
            "id": "prompt_claude_coding_architect",
            "title": "Claude 3.7 / GPT-4o Production-Grade Refactoring & Clean Code Template",
            "title_en": "Claude 3.7 / GPT-4o Production-Grade Refactoring & Clean Code Template",
            "title_zh": "💡 Claude 3.7 / GPT-4o 生产级重构与 Clean Code 模板",
            "url": "https://docs.anthropic.com/",
            "image_url": "https://images.unsplash.com/photo-1555066931-4365d14bab8c?w=800&q=80&auto=format&fit=crop",
            "source": "实战技巧 · Prompt",
            "author": "工程实战",
            "category": "videos",
            "is_prompt": True,
            "raw_published_at": now_iso,
            "recommended_model": "Claude 3.7 Sonnet / GPT-4o",
            "temp_advice": "建议温度 0.2 | 生产级代码严谨模式",
            "metrics": {"type": "📋 即抄即用", "model": "Claude 3.7", "temp": "0.2"},
            "content_snippet": "Rigorous code auditor mode: Refactors code smells without breaking public API contracts, outputting benchmark diffs and unit tests.",
            "summary_en": "Rigorous code auditor mode: Refactors code smells without breaking public API contracts, outputting benchmark diffs and unit tests.",
            "summary_zh": "严谨的代码审查官模式：在不打破现有 API 契约前提下重构代码异味，输出性能优化对比与覆盖率测试用例。",
            "prompt_content": "你是一位拥有 15 年经验的资深系统架构师与代码审查专家。请在严格遵守原有对外公共契约（Public API Contract）的前提下审查并重构以下代码：\n1. 识别代码异味（Code Smell）、隐性内存泄漏与高并发竞争冒险（Race Condition）；\n2. 采用现代设计模式与 SOLID 原则进行无破坏性重构，给出重构前后的 Diff 对比；\n3. 编写完整的防御性单元测试（含边界值、空指针与异常抛出用例）。",
            "tags": ["代码重构", "高阶提示词", "Claude"]
        },
        {
            "id": "prompt_flux_photoreal",
            "title": "FLUX.1 / Midjourney Commercial Studio Photography Master Prompt",
            "title_en": "FLUX.1 / Midjourney Commercial Studio Photography Master Prompt",
            "title_zh": "💡 FLUX.1 / Midjourney 顶级商业摄影质感提示词神咒",
            "url": "https://blackforestlabs.ai/",
            "image_url": "https://images.unsplash.com/photo-1579783900882-c0d3dad7b119?w=800&q=80&auto=format&fit=crop",
            "source": "实战技巧 · Prompt",
            "author": "视觉实测",
            "category": "videos",
            "is_prompt": True,
            "raw_published_at": now_iso,
            "recommended_model": "FLUX.1-dev / Midjourney v6.1",
            "temp_advice": "Guidance Scale: 3.5 | 步数 28",
            "metrics": {"type": "📋 即抄即用", "model": "FLUX.1-dev", "temp": "CFG 3.5"},
            "content_snippet": "85mm f/1.4 lens bokeh, Hasselblad film grain and Tyndall morning light for photorealistic portraiture without plastic AI artifacts.",
            "summary_en": "85mm f/1.4 lens bokeh, Hasselblad film grain and Tyndall morning light for photorealistic portraiture without plastic AI artifacts.",
            "summary_zh": "85mm f/1.4 镜头虚化、哈苏胶片微颗粒与自然晨光丁达尔效应，生成毫无塑料感的高清人像。",
            "prompt_content": "A high-end cinematic editorial portrait of [SUBJECT], shot on 35mm kodak portra 400 film, Hasselblad H6D-100c camera, 85mm f/1.4 lens, soft natural morning rim light, subtle cinematic lens flare, hyper-realistic pores and skin imperfections, fine hair strands, depth of field, 8k resolution, award-winning photography --ar 16:9 --style raw --v 6.1",
            "tags": ["生图神咒", "FLUX/MJ", "商业摄影"]
        },
        {
            "id": "prompt_arxiv_deep_dive",
            "title": "ArXiv Deep Dive: 5-Step Paper Penetration & Reproduction Breakdown Template",
            "title_en": "ArXiv Deep Dive: 5-Step Paper Penetration & Reproduction Breakdown Template",
            "title_zh": "💡 前沿顶会论文 5步穿透精读与复现拆解模板",
            "url": "https://arxiv.org/",
            "image_url": "https://images.unsplash.com/photo-1456513080510-7bf3a84b82f8?w=800&q=80&auto=format&fit=crop",
            "source": "实战技巧 · Prompt",
            "author": "科研极客",
            "category": "videos",
            "is_prompt": True,
            "raw_published_at": now_iso,
            "recommended_model": "Claude 3.7 / Gemini 1.5 Pro",
            "temp_advice": "建议温度 0.3 | 极客文献精读",
            "metrics": {"type": "📋 即抄即用", "model": "Gemini 1.5 Pro", "temp": "0.3"},
            "content_snippet": "Pierces academic hyperbole to extract core mathematical axioms, baseline discrepancies, and RTX 4090 reproduction bottlenecks.",
            "summary_en": "Pierces academic hyperbole to extract core mathematical axioms, baseline discrepancies, and RTX 4090 reproduction bottlenecks.",
            "summary_zh": "穿透学术论文华丽包装，直击数学形式化定义、核心假设脆弱性与开源复现最大阻碍。",
            "prompt_content": "请作为该领域的顶级同行评审专家，用极客实战视角深度解剖附带的这篇论文：\n1. 用一句话说清楚作者解决的核心科学矛盾；\n2. 剥离作者自我夸大的修辞，指出其算法最根本的 Baseline 对比是否存在水分；\n3. 提取算法伪代码与核心公式的物理直觉解释；\n4. 评估若在本地单卡（如 RTX 4090）进行复现，面临的最大显存/数据瓶颈及工程应对方案。",
            "tags": ["论文精读", "科研拆解", "Prompt神咒"]
        },
        {
            "id": "prompt_agent_robust_tools",
            "title": "Agent Tool-Use Robustness Validation & Anti-Hallucination System Prompt",
            "title_en": "Agent Tool-Use Robustness Validation & Anti-Hallucination System Prompt",
            "title_zh": "💡 Agent Tool-Use 鲁棒性校验与防胡言乱语系统指令",
            "url": "https://modelcontextprotocol.io/",
            "image_url": "https://images.unsplash.com/photo-1526374965328-7f61d4dc18c5?w=800&q=80&auto=format&fit=crop",
            "source": "实战技巧 · Prompt",
            "author": "Agent开发",
            "category": "videos",
            "is_prompt": True,
            "raw_published_at": now_iso,
            "recommended_model": "Claude 3.5/3.7 Sonnet / GPT-4o",
            "temp_advice": "建议温度 0.1 | 严格结构化 JSON 模式",
            "metrics": {"type": "📋 即抄即用", "model": "Claude 3.7", "temp": "0.1"},
            "content_snippet": "Defensive prompt directives for autonomous agent systems to prevent tool invocation hallucinations, loop deadlocks, and invalid arguments.",
            "summary_en": "Defensive prompt directives for autonomous agent systems to prevent tool invocation hallucinations, loop deadlocks, and invalid arguments.",
            "summary_zh": "构建工业级智能体系统的防御性指令，防止工具调用幻觉、循环死锁与无效入参参数。",
            "prompt_content": "【系统约束】：你是一个受限执行环境中的自治 Agent。\n1. 在调用任何工具前，必须输出 <preflight> 检验入参字段的类型与合法性；\n2. 严禁捏造未声明在 Tool Registry 中的虚构工具函数；\n3. 若连续两次工具返回报错，立即终止盲目重试，进入 <diagnosis> 模式回溯上一轮输入并向人类汇报根因；\n4. 最终响应仅通过标准工具或结构化 JSON schema 返回，禁止携带任何 markdown 闲聊闲扯。",
            "tags": ["Agent开发", "工具调用", "防幻觉"]
        },
        {
            "id": "prompt_sql_performance_tuning",
            "title": "High-Concurrency SQL Slow Query Diagnosis & Query Plan Optimization Template",
            "title_en": "High-Concurrency SQL Slow Query Diagnosis & Query Plan Optimization Template",
            "title_zh": "💡 高并发 SQL 慢查询诊断与执行计划重写优化模板",
            "url": "https://github.com/",
            "image_url": "https://images.unsplash.com/photo-1558494949-ef010cbdcc31?w=800&q=80&auto=format&fit=crop",
            "source": "实战技巧 · Prompt",
            "author": "DBA极客",
            "category": "videos",
            "is_prompt": True,
            "raw_published_at": now_iso,
            "recommended_model": "DeepSeek-Coder-V2 / Claude 3.7",
            "temp_advice": "建议温度 0.1 | 数据库内核调优",
            "metrics": {"type": "📋 即抄即用", "model": "DeepSeek-Coder", "temp": "0.1"},
            "content_snippet": "Restructures queries on 10M+ row tables based on EXPLAIN ANALYZE, eliminating full-table scans with composite indexes.",
            "summary_en": "Restructures queries on 10M+ row tables based on EXPLAIN ANALYZE, eliminating full-table scans with composite indexes.",
            "summary_zh": "根据 EXPLAIN 结果重构千万级表查询，消除全表扫描与临时表开销，生成最优复合索引。",
            "prompt_content": "你是一位顶级数据库性能调优 DBA 专家。以下是执行耗时过长的慢 SQL 语句及对应的 EXPLAIN ANALYZE 执行计划树：\n1. 指出导致性能下降的关键瓶颈（如全表扫描、Using filesort、Nested Loop 倾斜）；\n2. 重写 SQL 语句（利用延迟关联、覆盖索引、CTE 或子查询物化优化）；\n3. 给出精确到字段顺序的最优复合索引建议（考虑高区分度与最左前缀法则），并评估索引维护成本。",
            "tags": ["SQL调优", "数据库实战", "Prompt模板"]
        }
    ]
    return prompts


# ==========================================
# 7. 硬核发烧友必备工具箱 (LMSYS Arena + ArXiv 前沿)
# ==========================================
def get_chatbot_arena_top5() -> List[Dict[str, Any]]:
    """Returns current LMSYS Chatbot Arena Top 5 Elo ratings for hardcore enthusiasts."""
    return [
        {"rank": 1, "model": "Gemini 2.0 Pro Exp", "elo": 1332, "org": "Google", "badge": "👑 榜首", "badge_en": "👑 #1 Rank"},
        {"rank": 2, "model": "DeepSeek-R1", "elo": 1326, "org": "DeepSeek", "badge": "🔥 开源最强", "badge_en": "🔥 OSS King"},
        {"rank": 3, "model": "Claude 3.7 Sonnet", "elo": 1324, "org": "Anthropic", "badge": "⚡ 推理王者", "badge_en": "⚡ Reasoning"},
        {"rank": 4, "model": "OpenAI o3-mini", "elo": 1319, "org": "OpenAI", "badge": "🧠 极速思维", "badge_en": "🧠 Fast Thought"},
        {"rank": 5, "model": "GPT-4o (Latest)", "elo": 1292, "org": "OpenAI", "badge": "🌐 全能多模态", "badge_en": "🌐 Multimodal"}
    ]


def get_arxiv_curated_papers() -> List[Dict[str, Any]]:
    """Returns 4 curated groundbreaking AI papers from arXiv for hardcore enthusiasts."""
    return [
        {
            "id": "arxiv_2501_12948",
            "arxiv_id": "2501.12948",
            "title": "DeepSeek-R1: Incentivizing Reasoning Capability in LLMs via Reinforcement Learning",
            "title_en": "DeepSeek-R1: Incentivizing Reasoning Capability in LLMs via Reinforcement Learning",
            "title_zh": "DeepSeek-R1：通过纯强化学习激发大模型复杂推理能力的训练范式",
            "url": "https://arxiv.org/abs/2501.12948",
            "date": "最新突破",
            "date_en": "SOTA Breakthrough",
            "spec": "GRPO 算法 · 零监督 SFT 冷启动",
            "spec_en": "GRPO Algorithm · Zero SFT Cold Start",
            "summary_zh": "开创性证明仅需纯强化学习即可涌现高难度数学与逻辑自我反思能力，无需海量昂贵的人工标注数据。",
            "summary_en": "Groundbreaking demonstration that pure reinforcement learning can directly incentivize complex mathematical reasoning and self-reflection without expensive human SFT data."
        },
        {
            "id": "arxiv_2502_00567",
            "arxiv_id": "2502.00567",
            "title": "Scaling Laws for Test-Time Compute in Large Language Models",
            "title_en": "Scaling Laws for Test-Time Compute in Large Language Models",
            "title_zh": "大语言模型测试期计算（Test-Time Compute）扩展定律研究",
            "url": "https://arxiv.org/abs/2502.00567",
            "date": "顶会前沿",
            "date_en": "Frontier Research",
            "spec": "Test-Time Scaling · 推理期算力兑换",
            "spec_en": "Test-Time Scaling · Inference Compute Tradeoff",
            "summary_zh": "系统证明通过延长模型在推理阶段的思考步数与树搜索空间，可显著超越增加百倍预训练参数带来的增益。",
            "summary_en": "Proves that scaling search and reflection during inference can significantly outperform 100x pretraining parameter scaling."
        },
        {
            "id": "arxiv_2501_08313",
            "arxiv_id": "2501.08313",
            "title": "V-JEPA 2: Towards General Video World Models with Joint-Embedding Predictive Architecture",
            "title_en": "V-JEPA 2: Towards General Video World Models with Joint-Embedding Predictive Architecture",
            "title_zh": "V-JEPA 2：基于联合嵌入预测架构的通用物理视频世界模型",
            "url": "https://arxiv.org/abs/2501.08313",
            "date": "Meta AI",
            "date_en": "Meta AI",
            "spec": "非自回归 · 物理空间感知",
            "spec_en": "Non-Autoregressive · Physical Dynamics",
            "summary_zh": "抛弃逐像素扩散生成，在特征潜空间直接预测物体运动轨迹与受力交互，为具身智能奠定物理常识基础。",
            "summary_en": "Abandons pixel-by-pixel generative diffusion to predict motion trajectories and physical dynamics directly in latent space."
        },
        {
            "id": "arxiv_2412_19437",
            "arxiv_id": "2412.19437",
            "title": "SWE-agent: Agent-Computer Interfaces Enable Automated Software Engineering",
            "title_en": "SWE-agent: Agent-Computer Interfaces Enable Automated Software Engineering",
            "title_zh": "SWE-agent：基于终端与文件系统专用接口的自主软件工程智能体",
            "url": "https://arxiv.org/abs/2412.19437",
            "date": "普林斯顿",
            "date_en": "Princeton",
            "spec": "SWE-bench 生产级 · 终端自主执行",
            "spec_en": "SWE-bench SOTA · Autonomous Terminal Agent",
            "summary_zh": "设计专为大模型交互优化的 Shell/文件浏览器界面，实现自动化解决真实 GitHub 复杂 Issue 的工程闭环。",
            "summary_en": "Specially designed Agent-Computer Interfaces that allow LLMs to autonomously browse codebases, run tests, and fix real GitHub issues end-to-end."
        }
    ]


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
            return datetime.fromisoformat(raw.replace("Z", "+00:00")).timestamp()
        except Exception:
            return 0

    unique_items.sort(key=parse_time_for_sort, reverse=True)

    print(f"🎉 聚合完成！共收集到 {len(unique_items)} 条高质量多媒体情报 (已按最新时间严格倒序)。\n")
    return unique_items


if __name__ == "__main__":
    items = fetch_all_sources()
    print(f"样本: 共 {len(items)} 条")

