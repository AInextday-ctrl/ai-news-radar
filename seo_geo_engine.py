#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
seo_geo_engine.py
-----------------
Core Engine for Advanced Search Engine Optimization (SEO) and 
Generative Engine Optimization (GEO) on AI News Radar (ainewsradar.xyz).

Capabilities:
1. LLMs.txt & LLMs-full.txt Generator (llms.txt standard for AI Agents & Search Engines like Perplexity, ChatGPT Search, Claude).
2. Dual-Language RSS 2.0 / Atom & JSON Feed (Real-time syndication feeds for fresh news discovery).
3. Google News Sitemap (xmlns:news="http://www.google.com/schemas/sitemap-news/0.9").
4. Comprehensive XML Sitemap Engine (Auto-indexing 350+ canonical URLs: Trust, Daily, Articles, Tools, News).
5. AI-First Robots.txt Generator (Welcomes GPTBot, PerplexityBot, ClaudeBot, Google-Extended, etc.).
"""

import os
import sys
import re
import json
import time
import html
from datetime import datetime, timezone
from email.utils import formatdate
from typing import Dict, Any, List, Optional

try:
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')
except Exception:
    pass

WORKSPACE_DIR = os.path.dirname(os.path.abspath(__file__))
PUBLIC_DIR = os.path.join(WORKSPACE_DIR, "public")
ZH_PUBLIC_DIR = os.path.join(PUBLIC_DIR, "zh")

BASE_URL = "https://ainewsradar.xyz"

def sanitize_for_en(text: str, preserve_newlines: bool = False) -> str:
    """Removes any CJK characters and normalizes whitespace for pure English compliance."""
    if not text:
        return ""
    cleaned = re.sub(r'[\u4e00-\u9fff\u3000-\u303f\uff00-\uffef]', '', str(text))
    if preserve_newlines:
        # Normalize each line individually while preserving newlines
        lines = [re.sub(r'[^\S\r\n]+', ' ', line).strip() for line in cleaned.splitlines()]
        return '\n'.join(lines)
    cleaned = re.sub(r'\s+', ' ', cleaned).strip()
    return cleaned

def xml_escape(val: Any) -> str:
    if val is None:
        return ""
    s = str(val)
    return (s.replace("&", "&amp;")
             .replace("<", "&lt;")
             .replace(">", "&gt;")
             .replace('"', "&quot;")
             .replace("'", "&apos;"))

def parse_iso_or_rfc(val: Any) -> str:
    """Returns ISO 8601 string (YYYY-MM-DDTHH:MM:SSZ)."""
    if not val:
        return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    s = str(val).strip()
    if re.match(r'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}', s):
        if not s.endswith("Z") and "+" not in s and "-" not in s[10:]:
            return s + "Z"
        return s
    if re.match(r'^\d{4}-\d{2}-\d{2}$', s):
        return f"{s}T08:00:00Z"
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

def parse_rfc822(val: Any) -> str:
    """Returns RFC 822 / 2822 date for RSS pubDate."""
    try:
        iso_str = parse_iso_or_rfc(val)
        dt = datetime.fromisoformat(iso_str.replace("Z", "+00:00"))
        return formatdate(dt.timestamp(), usegmt=True)
    except Exception:
        return formatdate(time.time(), usegmt=True)


# ==============================================================================
# 1. LLMs.txt & LLMs-full.txt Generator (GEO Standard)
# ==============================================================================
def generate_llms_manifests(news_items: List[Dict[str, Any]],
                            tools: List[Dict[str, Any]],
                            articles_meta: List[Dict[str, Any]]) -> None:
    """
    Generates /llms.txt and /llms-full.txt in English (public/llms.txt)
    and in Chinese (public/zh/llms.txt) following the official llms.txt standard.
    """
    now_iso = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%SZ")

    # ----------------------------------------------------
    # A. English llms.txt (Concise Map)
    # ----------------------------------------------------
    en_llms_lines = [
        "# AI News Radar",
        "",
        "> Real-time panoramic intelligence radar for global frontier AI breakthroughs, verified leader signals, hands-on tutorials, and vetted developer tools.",
        "",
        "AI News Radar (https://ainewsradar.xyz) provides verified, signal-dense updates on frontier large language models, agent architectures, developer tooling, and real-world implementations. All intelligence is vetted against primary sources, benchmark results, and production code repositories.",
        f"Last updated: {now_iso}",
        "",
        "## Core Platform Sections",
        "",
        f"- [Frontier AI News]({BASE_URL}/#news): Real-time vetted breakthroughs, model weights releases, and technical papers.",
        f"- [Applied AI Tools]({BASE_URL}/#tools): Curated developer utilities, agent runtimes, and local AI software.",
        f"- [Social Radar Signals]({BASE_URL}/#celebrity): Verified statements and technical debates from primary AI researchers and founders.",
        f"- [Hands-on Video Guides]({BASE_URL}/#videos): Verified developer tutorials and live workflow demos.",
        f"- [Engineering Deep-Dive Articles]({BASE_URL}/articles): In-depth architectural dissections of production AI systems.",
        f"- [Daily Briefing Archive]({BASE_URL}/daily): Chronological daily digests of global AI advancements.",
        "",
        "## Latest Breaking AI Intelligence",
        ""
    ]

    for item in news_items[:15]:
        nid = item.get("id")
        title = sanitize_for_en(item.get("title_en") or item.get("title") or "AI Breaking Update")
        summary = sanitize_for_en(item.get("summary_en") or item.get("content_snippet") or "")
        summary_short = summary[:160] + "..." if len(summary) > 160 else summary
        en_llms_lines.append(f"- [{title}]({BASE_URL}/news/{nid}): {summary_short}")

    en_llms_lines.extend([
        "",
        "## Curated Applied AI Tools",
        ""
    ])

    for tool in tools[:12]:
        tid = tool.get("id")
        name = sanitize_for_en(tool.get("app_name_en") or tool.get("app_name") or "AI Tool")
        hook = sanitize_for_en(tool.get("app_hook_en") or tool.get("title_en") or "")
        pricing = sanitize_for_en(tool.get("pricing_tag") or "Open Source")
        en_llms_lines.append(f"- [{name}]({BASE_URL}/tools/{tid}): ({pricing}) {hook}")

    en_llms_lines.extend([
        "",
        "## Flagship Engineering Guides",
        ""
    ])

    for art in articles_meta[:10]:
        slug = art.get("slug") or art.get("id")
        title = sanitize_for_en(art.get("title_en") or art.get("title") or "Engineering Guide")
        desc = sanitize_for_en(art.get("description_en") or art.get("summary_en") or "")
        en_llms_lines.append(f"- [{title}]({BASE_URL}/articles/{slug}): {desc[:140]}")

    en_llms_lines.extend([
        "",
        "## Machine-Readable Resources",
        "",
        f"- [Full Intelligence Ingestion (llms-full.txt)]({BASE_URL}/llms-full.txt): Comprehensive multi-page content for deep context window ingestion.",
        f"- [Chinese Edition (Simplified Chinese)]({BASE_URL}/zh): Complete bilingual intelligence mirror.",
        f"- [RSS 2.0 Feed]({BASE_URL}/feed.xml): Machine-readable syndicate feed updated in real time.",
        f"- [JSON Feed v1.1]({BASE_URL}/feed.json): Standardized JSON format feed.",
        f"- [XML Sitemap]({BASE_URL}/sitemap.xml): Complete URL index.",
        f"- [Google News Sitemap]({BASE_URL}/news-sitemap.xml): High-freshness 48-hour news index."
    ])

    en_llms_content = "\n".join(en_llms_lines)
    # Guarantee zero Chinese characters in English file while preserving clean markdown structure
    en_llms_content = sanitize_for_en(en_llms_content, preserve_newlines=True)
    with open(os.path.join(PUBLIC_DIR, "llms.txt"), "w", encoding="utf-8") as f:
        f.write(en_llms_content.strip() + "\n")

    # ----------------------------------------------------
    # B. English llms-full.txt (Comprehensive Knowledge Context)
    # ----------------------------------------------------
    en_full_lines = [
        "# AI News Radar - Comprehensive Intelligence Document",
        "",
        "> Complete text and structured briefings of latest frontier AI intelligence, applied tools, and engineering architectures.",
        f"Generated: {now_iso}",
        f"Canonical: {BASE_URL}",
        "",
        "---",
        "",
        "## Section 1: Breaking AI Intelligence Briefings",
        ""
    ]

    for item in news_items[:30]:
        nid = item.get("id")
        title = sanitize_for_en(item.get("title_en") or item.get("title") or "AI Update")
        summary = sanitize_for_en(item.get("summary_en") or item.get("content_snippet") or "")
        source = sanitize_for_en(item.get("source") or "Tech Source")
        url = item.get("url") or f"{BASE_URL}/news/{nid}"
        bullets = [sanitize_for_en(b) for b in (item.get("fact_bullets_en") or [])]
        bullets = [b for b in bullets if b]

        en_full_lines.append(f"### {title}")
        en_full_lines.append(f"- URL: {BASE_URL}/news/{nid}")
        en_full_lines.append(f"- Source: {source} ({url})")
        en_full_lines.append(f"- Executive Summary: {summary}")
        if bullets:
            en_full_lines.append("- Key Verified Facts:")
            for b in bullets:
                en_full_lines.append(f"  * {b}")
        analysis = sanitize_for_en(item.get("ai_analysis_en") or item.get("ai_analysis") or "")
        if analysis:
            en_full_lines.append(f"- Strategic AI Analysis: {analysis}")
        en_full_lines.append("")

    en_full_lines.extend([
        "---",
        "",
        "## Section 2: Applied AI Developer Tools",
        ""
    ])

    for tool in tools[:25]:
        tid = tool.get("id")
        name = sanitize_for_en(tool.get("app_name_en") or tool.get("app_name") or "Tool")
        hook = sanitize_for_en(tool.get("app_hook_en") or tool.get("title_en") or "")
        overview = sanitize_for_en(tool.get("overview_en") or tool.get("summary_en") or hook)
        features = sanitize_for_en(tool.get("features_en") or "")
        best_for = sanitize_for_en(tool.get("best_for_en") or "")
        cmd = sanitize_for_en(tool.get("quickstart_cmd") or "")
        official_url = tool.get("official_url") or tool.get("url") or "#"

        en_full_lines.append(f"### {name}")
        en_full_lines.append(f"- URL: {BASE_URL}/tools/{tid}")
        en_full_lines.append(f"- Official Source: {official_url}")
        en_full_lines.append(f"- Headline: {hook}")
        en_full_lines.append(f"- Overview: {overview}")
        if features:
            en_full_lines.append(f"- Features: {features}")
        if best_for:
            en_full_lines.append(f"- Best For: {best_for}")
        if cmd:
            en_full_lines.append(f"- Quickstart: `{cmd}`")
        en_full_lines.append("")

    en_full_lines.extend([
        "---",
        "",
        "## Section 3: Flagship Technical Dissections",
        ""
    ])

    for art in articles_meta:
        slug = art.get("slug") or art.get("id")
        title = sanitize_for_en(art.get("title_en") or art.get("title") or "Technical Guide")
        desc = sanitize_for_en(art.get("description_en") or art.get("summary_en") or "")
        en_full_lines.append(f"### {title}")
        en_full_lines.append(f"- URL: {BASE_URL}/articles/{slug}")
        en_full_lines.append(f"- Abstract: {desc}")
        en_full_lines.append("")

    en_full_content = sanitize_for_en("\n".join(en_full_lines), preserve_newlines=True)
    with open(os.path.join(PUBLIC_DIR, "llms-full.txt"), "w", encoding="utf-8") as f:
        f.write(en_full_content.strip() + "\n")

    # ----------------------------------------------------
    # C. Chinese llms.txt (中文专版精炼地图)
    # ----------------------------------------------------
    os.makedirs(ZH_PUBLIC_DIR, exist_ok=True)
    zh_llms_lines = [
        "# AI 资讯雷达 (AI News Radar - 中文专版)",
        "",
        "> 面向全球开发者与技术决策者的独立前沿 AI 工程观察站与技术研报平台，全天候实时追踪全球大模型突破、行业领袖社交动态、深度实操教程与高频生产力工具库。",
        "",
        "AI 资讯雷达 (https://ainewsradar.xyz/zh) 坚持一手源头事实核验、零伪造时钟、零机器水词摘要。全站支持中英双轨同构与深度语义结构化数据。",
        f"最新构建时间: {now_iso}",
        "",
        "## 核心板块导航",
        "",
        f"- [行业快讯]({BASE_URL}/zh#news): 24h 全球大模型重磅突破、权威发布与论文研析。",
        f"- [落地工具]({BASE_URL}/zh#tools): 高频生产力 AI 工具、开源 Agent 框架与开发者 CLI。",
        f"- [社交雷达]({BASE_URL}/zh#celebrity): 行业领袖与首席架构师一手推文与深度技术争鸣。",
        f"- [实操精选]({BASE_URL}/zh#videos): 真实时效核验的技术实操教程与工作流演示。",
        f"- [深度研报专栏]({BASE_URL}/zh/articles): 生产级系统架构拆解与大模型工程化实操长文。",
        f"- [每日简报归档]({BASE_URL}/zh/daily): 历史每日情报全量归档大厅。",
        "",
        "## 最新重点 AI 情报摘要",
        ""
    ]

    for item in news_items[:15]:
        nid = item.get("id")
        title = item.get("title_zh") or item.get("title") or "AI 突发动态"
        summary = item.get("summary_zh") or item.get("content_snippet") or ""
        summary_short = summary[:160] + "..." if len(summary) > 160 else summary
        zh_llms_lines.append(f"- [{title}]({BASE_URL}/zh/news/{nid}): {summary_short}")

    zh_llms_lines.extend([
        "",
        "## 精选开发者实用工具",
        ""
    ])

    for tool in tools[:12]:
        tid = tool.get("id")
        name = tool.get("app_name") or tool.get("title") or "AI 工具"
        hook = tool.get("app_hook") or tool.get("title_zh") or ""
        pricing = tool.get("pricing_tag") or "开源免费"
        zh_llms_lines.append(f"- [{name}]({BASE_URL}/zh/tools/{tid}): ({pricing}) {hook}")

    zh_llms_lines.extend([
        "",
        "## 深度技术专栏研报",
        ""
    ])

    for art in articles_meta[:10]:
        slug = art.get("slug") or art.get("id")
        title = art.get("title_zh") or art.get("title") or "技术专栏"
        desc = art.get("description_zh") or art.get("summary_zh") or ""
        zh_llms_lines.append(f"- [{title}]({BASE_URL}/zh/articles/{slug}): {desc[:140]}")

    zh_llms_lines.extend([
        "",
        "## 机器可读与订阅接口",
        "",
        f"- [全量情报上下文 (zh/llms-full.txt)]({BASE_URL}/zh/llms-full.txt): 供 AI 大上下文窗口一次性读取的全量中文事实与长文。",
        f"- [英文国际版 (English Edition)]({BASE_URL}/): 纯正英文首屏与落地页。",
        f"- [中文 RSS 2.0 订阅]({BASE_URL}/zh/feed.xml): 实时聚合提要。",
        f"- [站点全量 Sitemap]({BASE_URL}/sitemap.xml): 完整索引地图。",
        f"- [Google 突发新闻 Sitemap]({BASE_URL}/news-sitemap.xml): 48 小时高频突发快讯专用地图。"
    ])

    zh_llms_content = "\n".join(zh_llms_lines)
    with open(os.path.join(ZH_PUBLIC_DIR, "llms.txt"), "w", encoding="utf-8") as f:
        f.write(zh_llms_content + "\n")

    # ----------------------------------------------------
    # D. Chinese llms-full.txt (中文全量深度知识库)
    # ----------------------------------------------------
    zh_full_lines = [
        "# AI 资讯雷达 - 全量深度情报与技术档案",
        "",
        "> 汇聚最新突发快讯要点、落地开发工具深度评测与旗舰技术长文全量文本。",
        f"生成时间: {now_iso}",
        f"权威网址: {BASE_URL}/zh",
        "",
        "---",
        "",
        "## 第一部分：突发 AI 快讯与结构化事实研判",
        ""
    ]

    for item in news_items[:30]:
        nid = item.get("id")
        title = item.get("title_zh") or item.get("title") or "AI 动态"
        summary = item.get("summary_zh") or item.get("content_snippet") or ""
        source = item.get("source") or "权威信源"
        url = item.get("url") or f"{BASE_URL}/zh/news/{nid}"
        bullets = item.get("fact_bullets_zh") or []

        zh_full_lines.append(f"### {title}")
        zh_full_lines.append(f"- 落地页链接: {BASE_URL}/zh/news/{nid}")
        zh_full_lines.append(f"- 原始信源: {source} ({url})")
        zh_full_lines.append(f"- 核心摘要: {summary}")
        if bullets:
            zh_full_lines.append("- 核验事实清单:")
            for b in bullets:
                zh_full_lines.append(f"  * {b}")
        analysis = item.get("ai_analysis_zh") or item.get("ai_analysis") or ""
        if analysis:
            zh_full_lines.append(f"- 独家研判与技术透视: {analysis}")
        zh_full_lines.append("")

    zh_full_lines.extend([
        "---",
        "",
        "## 第二部分：开发者落地工具全量评测",
        ""
    ])

    for tool in tools[:25]:
        tid = tool.get("id")
        name = tool.get("app_name") or tool.get("title") or "工具"
        hook = tool.get("app_hook") or tool.get("title_zh") or ""
        overview = tool.get("overview_zh") or tool.get("summary_zh") or hook
        features = tool.get("features_zh") or ""
        best_for = tool.get("best_for_zh") or ""
        cmd = tool.get("quickstart_cmd") or ""
        official_url = tool.get("official_url") or tool.get("url") or "#"

        zh_full_lines.append(f"### {name}")
        zh_full_lines.append(f"- 落地页链接: {BASE_URL}/zh/tools/{tid}")
        zh_full_lines.append(f"- 官方/开源地址: {official_url}")
        zh_full_lines.append(f"- 一句话亮点: {hook}")
        zh_full_lines.append(f"- 核心概览: {overview}")
        if features:
            zh_full_lines.append(f"- 功能矩阵: {features}")
        if best_for:
            zh_full_lines.append(f"- 适用人群与场景: {best_for}")
        if cmd:
            zh_full_lines.append(f"- 快速启动指令: `{cmd}`")
        zh_full_lines.append("")

    zh_full_lines.extend([
        "---",
        "",
        "## 第三部分：旗舰工程架构研报",
        ""
    ])

    for art in articles_meta:
        slug = art.get("slug") or art.get("id")
        title = art.get("title_zh") or art.get("title") or "技术研报"
        desc = art.get("description_zh") or art.get("summary_zh") or ""
        zh_full_lines.append(f"### {title}")
        zh_full_lines.append(f"- 研报链接: {BASE_URL}/zh/articles/{slug}")
        zh_full_lines.append(f"- 核心导引: {desc}")
        zh_full_lines.append("")

    zh_full_content = "\n".join(zh_full_lines)
    with open(os.path.join(ZH_PUBLIC_DIR, "llms-full.txt"), "w", encoding="utf-8") as f:
        f.write(zh_full_content + "\n")

    print(f"🤖 [GEO Engine] llms.txt & llms-full.txt 已成功生成 (EN: {os.path.getsize(os.path.join(PUBLIC_DIR, 'llms.txt'))} B, ZH: {os.path.getsize(os.path.join(ZH_PUBLIC_DIR, 'llms.txt'))} B)")


# ==============================================================================
# 2. Dual-Language RSS 2.0 & JSON Feed Generator
# ==============================================================================
def generate_rss_and_json_feeds(news_items: List[Dict[str, Any]],
                                tools: List[Dict[str, Any]],
                                articles_meta: List[Dict[str, Any]]) -> None:
    """
    Generates standard RSS 2.0 (feed.xml, rss.xml, zh/feed.xml, zh/rss.xml)
    and JSON Feed v1.1 (feed.json).
    """
    build_date = formatdate(time.time(), usegmt=True)

    # ----------------------------------------------------
    # A. English RSS 2.0 (feed.xml & rss.xml)
    # ----------------------------------------------------
    en_items_xml = []
    
    # News items
    for item in news_items[:30]:
        nid = item.get("id")
        title = sanitize_for_en(item.get("title_en") or item.get("title") or "AI Breaking Update")
        summary = sanitize_for_en(item.get("summary_en") or item.get("content_snippet") or "")
        url = f"{BASE_URL}/news/{nid}"
        pub_date = parse_rfc822(item.get("published_at") or item.get("raw_published_at") or item.get("date"))
        source = sanitize_for_en(item.get("source") or "Tech Source")
        
        en_items_xml.append(f"""    <item>
      <title>{xml_escape(title)}</title>
      <link>{url}</link>
      <guid isPermaLink="true">{url}</guid>
      <description>{xml_escape(summary)}</description>
      <category>Breaking AI News</category>
      <source url="{xml_escape(item.get('url') or url)}">{xml_escape(source)}</source>
      <pubDate>{pub_date}</pubDate>
    </item>""")

    # Flagship Articles
    for art in articles_meta[:10]:
        slug = art.get("slug") or art.get("id")
        title = sanitize_for_en(art.get("title_en") or art.get("title") or "Engineering Guide")
        desc = sanitize_for_en(art.get("description_en") or art.get("summary_en") or "")
        url = f"{BASE_URL}/articles/{slug}"
        pub_date = parse_rfc822(art.get("date"))
        
        en_items_xml.append(f"""    <item>
      <title>{xml_escape(title)}</title>
      <link>{url}</link>
      <guid isPermaLink="true">{url}</guid>
      <description>{xml_escape(desc)}</description>
      <category>Engineering Deep-Dive</category>
      <pubDate>{pub_date}</pubDate>
    </item>""")

    en_rss_body = "\n".join(en_items_xml)
    en_rss_full = f"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom">
  <channel>
    <title>AI News Radar - Frontier AI Intel, Social Signals &amp; Tools</title>
    <link>{BASE_URL}</link>
    <description>Real-time panoramic intelligence radar for global frontier AI breakthroughs, verified leader signals, hands-on tutorials, and applied developer tools.</description>
    <language>en-us</language>
    <lastBuildDate>{build_date}</lastBuildDate>
    <atom:link href="{BASE_URL}/feed.xml" rel="self" type="application/rss+xml"/>
    <image>
      <url>{BASE_URL}/images/og-default.jpg</url>
      <title>AI News Radar</title>
      <link>{BASE_URL}</link>
    </image>
{en_rss_body}
  </channel>
</rss>
"""
    # Guarantee zero Chinese characters in English RSS while preserving XML line breaks
    en_rss_full = sanitize_for_en(en_rss_full, preserve_newlines=True)
    for p in [os.path.join(PUBLIC_DIR, "feed.xml"), os.path.join(PUBLIC_DIR, "rss.xml")]:
        with open(p, "wb") as f:
            f.write(en_rss_full.strip().encode("utf-8") + b"\n")

    # ----------------------------------------------------
    # B. Chinese RSS 2.0 (zh/feed.xml & zh/rss.xml)
    # ----------------------------------------------------
    zh_items_xml = []
    for item in news_items[:30]:
        nid = item.get("id")
        title = item.get("title_zh") or item.get("title") or "AI 突发情报"
        summary = item.get("summary_zh") or item.get("content_snippet") or ""
        url = f"{BASE_URL}/zh/news/{nid}"
        pub_date = parse_rfc822(item.get("published_at") or item.get("raw_published_at") or item.get("date"))
        source = item.get("source") or "权威信源"
        
        zh_items_xml.append(f"""    <item>
      <title>{xml_escape(title)}</title>
      <link>{url}</link>
      <guid isPermaLink="true">{url}</guid>
      <description>{xml_escape(summary)}</description>
      <category>行业快讯</category>
      <source url="{xml_escape(item.get('url') or url)}">{xml_escape(source)}</source>
      <pubDate>{pub_date}</pubDate>
    </item>""")

    for art in articles_meta[:10]:
        slug = art.get("slug") or art.get("id")
        title = art.get("title_zh") or art.get("title") or "深度技术研报"
        desc = art.get("description_zh") or art.get("summary_zh") or ""
        url = f"{BASE_URL}/zh/articles/{slug}"
        pub_date = parse_rfc822(art.get("date"))
        
        zh_items_xml.append(f"""    <item>
      <title>{xml_escape(title)}</title>
      <link>{url}</link>
      <guid isPermaLink="true">{url}</guid>
      <description>{xml_escape(desc)}</description>
      <category>深度专栏</category>
      <pubDate>{pub_date}</pubDate>
    </item>""")

    zh_rss_body = "\n".join(zh_items_xml)
    zh_rss_full = f"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom">
  <channel>
    <title>AI 资讯雷达 - 全球前沿 AI 情报与实用工具库</title>
    <link>{BASE_URL}/zh</link>
    <description>面向全球开发者与技术决策者的独立前沿 AI 工程观察站与技术研报平台。</description>
    <language>zh-cn</language>
    <lastBuildDate>{build_date}</lastBuildDate>
    <atom:link href="{BASE_URL}/zh/feed.xml" rel="self" type="application/rss+xml"/>
    <image>
      <url>{BASE_URL}/images/og-default.jpg</url>
      <title>AI 资讯雷达</title>
      <link>{BASE_URL}/zh</link>
    </image>
{zh_rss_body}
  </channel>
</rss>
"""
    for p in [os.path.join(ZH_PUBLIC_DIR, "feed.xml"), os.path.join(ZH_PUBLIC_DIR, "rss.xml")]:
        with open(p, "wb") as f:
            f.write(zh_rss_full.strip().encode("utf-8") + b"\n")

    # ----------------------------------------------------
    # C. JSON Feed v1.1 (public/feed.json)
    # ----------------------------------------------------
    json_feed_items = []
    for item in news_items[:30]:
        nid = item.get("id")
        json_feed_items.append({
            "id": f"{BASE_URL}/news/{nid}",
            "url": f"{BASE_URL}/news/{nid}",
            "external_url": item.get("url") or f"{BASE_URL}/news/{nid}",
            "title": sanitize_for_en(item.get("title_en") or item.get("title") or "AI Breaking Update"),
            "content_text": sanitize_for_en(item.get("summary_en") or item.get("content_snippet") or ""),
            "date_published": parse_iso_or_rfc(item.get("published_at") or item.get("raw_published_at") or item.get("date")),
            "tags": ["AI News", "Frontier LLM"]
        })

    json_feed = {
        "version": "https://jsonfeed.org/version/1.1",
        "title": "AI News Radar",
        "home_page_url": BASE_URL,
        "feed_url": f"{BASE_URL}/feed.json",
        "description": "Real-time panoramic intelligence radar for global frontier AI breakthroughs.",
        "icon": f"{BASE_URL}/images/og-default.jpg",
        "favicon": f"{BASE_URL}/favicon.ico",
        "items": json_feed_items
    }

    with open(os.path.join(PUBLIC_DIR, "feed.json"), "w", encoding="utf-8") as f:
        json.dump(json_feed, f, ensure_ascii=False, indent=2)

    print(f"📡 [Feed Engine] RSS 2.0 & JSON Feed 已全量构建 (EN: {len(en_items_xml)} 条, ZH: {len(zh_items_xml)} 条)")


# ==============================================================================
# 3. Google News Sitemap Generator (news-sitemap.xml)
# ==============================================================================
def generate_google_news_sitemap(news_items: List[Dict[str, Any]]) -> None:
    """
    Generates public/news-sitemap.xml compliant with Google News standards.
    Contains high-freshness breaking news published within the past 48 hours.
    """
    now = datetime.now(timezone.utc)
    entries = []

    for item in news_items:
        nid = item.get("id")
        if not nid:
            continue
        
        raw_pub = item.get("published_at") or item.get("raw_published_at") or item.get("date")
        iso_pub = parse_iso_or_rfc(raw_pub)
        
        # English News Entry
        en_title = sanitize_for_en(item.get("title_en") or item.get("title") or "AI Breaking Update")
        entries.append(f"""  <url>
    <loc>{BASE_URL}/news/{nid}</loc>
    <news:news>
      <news:publication>
        <news:name>AI News Radar</news:name>
        <news:language>en</news:language>
      </news:publication>
      <news:publication_date>{iso_pub}</news:publication_date>
      <news:title>{xml_escape(en_title)}</news:title>
    </news:news>
  </url>""")

        # Chinese News Entry
        zh_title = item.get("title_zh") or item.get("title") or "AI 突发快讯"
        entries.append(f"""  <url>
    <loc>{BASE_URL}/zh/news/{nid}</loc>
    <news:news>
      <news:publication>
        <news:name>AI 资讯雷达</news:name>
        <news:language>zh-cn</news:language>
      </news:publication>
      <news:publication_date>{iso_pub}</news:publication_date>
      <news:title>{xml_escape(zh_title)}</news:title>
    </news:news>
  </url>""")

    xml_body = "\n".join(entries)
    full_xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"
        xmlns:news="http://www.google.com/schemas/sitemap-news/0.9">
{xml_body}
</urlset>
"""
    with open(os.path.join(PUBLIC_DIR, "news-sitemap.xml"), "wb") as f:
        f.write(full_xml.strip().encode("utf-8") + b"\n")

    print(f"📰 [Google News Sitemap] 突发快讯地图已构建: 共收录 {len(entries)} 个实时新闻条目！")


# ==============================================================================
# 4. Comprehensive Full-Site Sitemap Generator
# ==============================================================================
def update_complete_sitemap(daily_dates: List[str],
                            articles_meta: List[Dict[str, Any]],
                            tools: Optional[List[Dict[str, Any]]] = None,
                            news_items: Optional[List[Dict[str, Any]]] = None) -> None:
    """
    Builds the ultimate 350+ URL sitemap.xml with full xhtml:link hreflang cross-referencing:
    - Root and Core Legal/Trust Pages
    - Daily Briefings (15+ days)
    - Flagship Articles (30+ articles)
    - Curated AI Tools (25+ tools)
    - Breaking AI News (30+ news items)
    """
    now_date = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    entries = []

    # Helper function for adding bilingual URL pairs
    def add_bilingual_url(en_path: str, zh_path: str, priority: str, freq: str, lastmod: str):
        en_url = f"{BASE_URL}{en_path}"
        zh_url = f"{BASE_URL}{zh_path}"
        
        entries.append(f"""  <url>
    <loc>{en_url}</loc>
    <xhtml:link rel="alternate" hreflang="en" href="{en_url}"/>
    <xhtml:link rel="alternate" hreflang="zh-CN" href="{zh_url}"/>
    <xhtml:link rel="alternate" hreflang="zh" href="{zh_url}"/>
    <xhtml:link rel="alternate" hreflang="x-default" href="{en_url}"/>
    <lastmod>{lastmod}</lastmod>
    <changefreq>{freq}</changefreq>
    <priority>{priority}</priority>
  </url>""")

        entries.append(f"""  <url>
    <loc>{zh_url}</loc>
    <xhtml:link rel="alternate" hreflang="zh-CN" href="{zh_url}"/>
    <xhtml:link rel="alternate" hreflang="zh" href="{zh_url}"/>
    <xhtml:link rel="alternate" hreflang="en" href="{en_url}"/>
    <xhtml:link rel="alternate" hreflang="x-default" href="{en_url}"/>
    <lastmod>{lastmod}</lastmod>
    <changefreq>{freq}</changefreq>
    <priority>{float(priority) - 0.05:.2f}</priority>
  </url>""")

    # 1. Root Pages
    add_bilingual_url("/", "/zh", "1.0", "hourly", now_date)

    # 2. Trust and Legal Pages
    for tp in ["about", "editorial-policy", "contact", "privacy", "terms"]:
        add_bilingual_url(f"/{tp}", f"/zh/{tp}", "0.75", "monthly", now_date)

    # 3. Daily Briefing Hub and Archives
    add_bilingual_url("/daily", "/zh/daily", "0.85", "daily", now_date)
    for d in daily_dates:
        add_bilingual_url(f"/daily/{d}", f"/zh/daily/{d}", "0.75", "never", d)

    # 4. Flagship Articles Hub and Articles
    add_bilingual_url("/articles", "/zh/articles", "0.90", "daily", now_date)
    for art in articles_meta:
        slug = art.get("slug") or art.get("id")
        art_date = art.get("date") or now_date
        add_bilingual_url(f"/articles/{slug}", f"/zh/articles/{slug}", "0.90", "monthly", art_date)

    # 5. Applied AI Tools Hub and Individual Tool Landing Pages
    if tools:
        for t in tools:
            tid = t.get("id")
            if not tid:
                continue
            add_bilingual_url(f"/tools/{tid}", f"/zh/tools/{tid}", "0.85", "weekly", now_date)

    # 6. Breaking AI News Landing Pages
    if news_items:
        for n in news_items:
            nid = n.get("id")
            if not nid:
                continue
            n_date = n.get("date") or n.get("published_at")
            if n_date:
                n_date = str(n_date)[:10]
            else:
                n_date = now_date
            add_bilingual_url(f"/news/{nid}", f"/zh/news/{nid}", "0.85", "daily", n_date)

    xml_body = "\n".join(entries)
    full_xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"
        xmlns:xhtml="http://www.w3.org/1999/xhtml">
{xml_body}
</urlset>
"""
    sitemap_path = os.path.join(PUBLIC_DIR, "sitemap.xml")
    with open(sitemap_path, "wb") as f:
        f.write(full_xml.strip().encode("utf-8") + b"\n")

    print(f"🗺️ [Sitemap Engine] 全量高权重站点地图已更新: 共计收录 {len(entries)} 个双语对齐页面 URL！")


# ==============================================================================
# 5. AI-First Robots.txt Generator
# ==============================================================================
def generate_robots_txt() -> None:
    """
    Generates a world-class, AI-friendly robots.txt that grants explicit access
    to prominent AI search and synthesis crawlers (GPTBot, PerplexityBot, ClaudeBot, etc.)
    while protecting private redirect pathways.
    """
    content = """# AI News Radar (https://ainewsradar.xyz) - Robots.txt
# Optimized for Web Indexing & Generative Engine Optimization (GEO)

User-agent: *
Allow: /
Disallow: /cdn-cgi/
Disallow: /go
Disallow: /go/
Disallow: /go?*
Disallow: /r/
Disallow: /r?*

# --- Modern Generative AI Search & Answer Engine Crawlers ---
User-agent: GPTBot
Allow: /
Disallow: /cdn-cgi/

User-agent: OAI-SearchBot
Allow: /
Disallow: /cdn-cgi/

User-agent: ChatGPT-User
Allow: /
Disallow: /cdn-cgi/

User-agent: PerplexityBot
Allow: /
Disallow: /cdn-cgi/

User-agent: ClaudeBot
Allow: /
Disallow: /cdn-cgi/

User-agent: anthropic-ai
Allow: /
Disallow: /cdn-cgi/

User-agent: Google-Extended
Allow: /
Disallow: /cdn-cgi/

User-agent: Applebot-Extended
Allow: /
Disallow: /cdn-cgi/

User-agent: Applebot
Allow: /
Disallow: /cdn-cgi/

User-agent: DuckAssistBot
Allow: /
Disallow: /cdn-cgi/

User-agent: Amazonbot
Allow: /
Disallow: /cdn-cgi/

User-agent: Bytespider
Allow: /
Disallow: /cdn-cgi/

User-agent: cohere-ai
Allow: /
Disallow: /cdn-cgi/

User-agent: Meta-ExternalAgent
Allow: /
Disallow: /cdn-cgi/

User-agent: FacebookBot
Allow: /
Disallow: /cdn-cgi/

User-agent: Diffbot
Allow: /
Disallow: /cdn-cgi/

User-agent: CCBot
Allow: /
Disallow: /cdn-cgi/

# --- Traditional Major Search Engines ---
User-agent: Googlebot
Allow: /
Disallow: /cdn-cgi/
Disallow: /go
Disallow: /go/
Disallow: /r/

User-agent: bingbot
Allow: /
Disallow: /cdn-cgi/
Disallow: /go
Disallow: /go/
Disallow: /r/

User-agent: BingPreview
Allow: /
Disallow: /cdn-cgi/
Disallow: /go
Disallow: /go/
Disallow: /r/

User-agent: Baiduspider
Allow: /
Disallow: /cdn-cgi/

User-agent: YandexBot
Allow: /
Disallow: /cdn-cgi/

User-agent: DuckDuckBot
Allow: /
Disallow: /cdn-cgi/

User-agent: Mediapartners-Google
Allow: /
Disallow: /cdn-cgi/

User-agent: Google-Display-AdsBot
Allow: /
Disallow: /cdn-cgi/

# --- Sitemaps & AI Context Endpoints ---
# LLMs.txt AI Manifests (llmstxt.org)
# Discoverable AI knowledge context manifests:
# https://ainewsradar.xyz/llms.txt
# https://ainewsradar.xyz/llms-full.txt
# https://ainewsradar.xyz/zh/llms.txt
# https://ainewsradar.xyz/zh/llms-full.txt
Sitemap: https://ainewsradar.xyz/sitemap.xml
Sitemap: https://ainewsradar.xyz/news-sitemap.xml
Sitemap: https://ainewsradar.xyz/feed.xml
Sitemap: https://ainewsradar.xyz/zh/feed.xml
"""
    robots_path = os.path.join(PUBLIC_DIR, "robots.txt")
    with open(robots_path, "w", encoding="utf-8") as f:
        f.write(content.strip() + "\n")

    print("🤖 [Robots Engine] public/robots.txt 已全面升级，显式支持所有主流 GEO 智能体爬虫与双站点地图！")
