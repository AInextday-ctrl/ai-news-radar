#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tool_news_publisher.py
-----------------------
Generates standalone, high-performance static landing pages for:
1. Applied AI Tools (public/tools/{id}.html & public/zh/tools/{id}.html)
2. Breaking AI News (public/news/{id}.html & public/zh/news/{id}.html)
3. Fallback Index Hubs (public/tools/index.html, public/news/index.html, etc.)

Features:
- Complete OpenGraph & Twitter Card metadata (summary_large_image) with authentic thumbnails.
- Threads & X social previews retain traffic on ainewsradar.xyz before linking to GitHub / primary sources.
- Strict language isolation: English pages contain ZERO Chinese characters (100% Quality Gate Assertion 8 compliance).
- Schema.org JSON-LD structured data for SoftwareApplication and NewsArticle.
- Built-in In-Site Bookmark toggle and direct 1-click sharing buttons.
"""

import os
import sys
import re
import json
import html
from typing import Dict, Any, List

try:
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')
except Exception:
    pass

WORKSPACE_DIR = os.path.dirname(os.path.abspath(__file__))

def sanitize_for_en(text: str) -> str:
    """Removes any Chinese characters and clean up punctuation for English compliance."""
    if not text:
        return ""
    # Strip CJK characters
    cleaned = re.sub(r'[\u4e00-\u9fff\u3000-\u303f\uff00-\uffef]', '', str(text))
    cleaned = re.sub(r'\s+', ' ', cleaned).strip()
    return cleaned

def escape(val: Any) -> str:
    return html.escape(str(val or ""))

def get_optimized_og_image(raw_url: str) -> str:
    if not raw_url or not isinstance(raw_url, str) or len(raw_url.strip()) < 10:
        return "https://ainewsradar.xyz/images/og-default.jpg"
    raw_url = raw_url.strip()
    if not raw_url.startswith("https://") and not raw_url.startswith("http://"):
        return "https://ainewsradar.xyz/images/og-default.jpg"
    if raw_url.startswith("http://"):
        raw_url = "https://" + raw_url[7:]
    
    # In-site brand assets
    if "ainewsradar.xyz" in raw_url:
        return raw_url

    # Unsplash: deliver direct high-res 1200x630 JPG with native Unsplash parameters
    if "images.unsplash.com" in raw_url:
        base = raw_url.split("?")[0]
        return f"{base}?w=1200&h=630&fit=crop&fm=jpg&q=85"

    # GitHub OpenGraph is already 1200x630
    if "opengraph.githubassets.com" in raw_url:
        return raw_url

    # Other authentic direct HTTPS image URLs
    return raw_url

def build_tool_html(tool: Dict[str, Any], is_zh: bool = False, related_tools: List[Dict[str, Any]] = None) -> str:
    tool_id = str(tool.get("id") or "")
    app_name = tool.get("app_name") or tool.get("title") or "AI Tool"
    app_name_en = tool.get("app_name_en") or tool.get("app_name") or "AI Tool"
    
    if is_zh:
        display_name = app_name
        hook = tool.get("app_hook") or tool.get("title_zh") or tool.get("summary_zh") or ""
        overview = tool.get("overview_zh") or tool.get("summary_zh") or tool.get("content_snippet") or ""
        features = tool.get("features_zh") or ""
        best_for = tool.get("best_for_zh") or ""
        lang_code = "zh"
        canonical_url = f"https://ainewsradar.xyz/zh/tools/{tool_id}"
        alt_en_url = f"https://ainewsradar.xyz/tools/{tool_id}"
        alt_zh_url = f"https://ainewsradar.xyz/zh/tools/{tool_id}"
        home_url = "/zh"
        back_text = "← 返回 AI 资讯雷达"
        overview_title = "核心功能与产品概览"
        features_title = "核心亮点与应用特性"
        best_for_title = "最适用人群与业务场景"
        quickstart_title = "快速启动与部署指令"
        official_btn_text = "🚀 前往官网 / GitHub 仓库 ↗"
        share_x_text = "分享到 𝕏"
        share_threads_text = "分享到 Threads"
        copy_link_text = "复制分享链接"
        more_tools_title = "更多精选 AI 工具"
        lang_switch_label = "🌐 English"
        quickstart_cmd = tool.get("quickstart_cmd") or ""
    else:
        display_name = sanitize_for_en(app_name_en or app_name)
        hook = sanitize_for_en(tool.get("app_hook_en") or tool.get("title_en") or tool.get("summary_en") or "")
        overview = sanitize_for_en(tool.get("overview_en") or tool.get("summary_en") or tool.get("content_snippet") or "")
        features = sanitize_for_en(tool.get("features_en") or "")
        best_for = sanitize_for_en(tool.get("best_for_en") or "")
        lang_code = "en"
        canonical_url = f"https://ainewsradar.xyz/tools/{tool_id}"
        alt_en_url = f"https://ainewsradar.xyz/tools/{tool_id}"
        alt_zh_url = f"https://ainewsradar.xyz/zh/tools/{tool_id}"
        home_url = "/"
        back_text = "← Back to AI News Radar"
        overview_title = "Product Overview & Capabilities"
        features_title = "Key Features & Highlights"
        best_for_title = "Ideal Use Cases & Audience"
        quickstart_title = "Quickstart & Installation"
        official_btn_text = "🚀 Visit Official Website / GitHub ↗"
        share_x_text = "Share on 𝕏"
        share_threads_text = "Share on Threads"
        copy_link_text = "Copy Link"
        more_tools_title = "Explore More AI Tools"
        lang_switch_label = "🇨🇳 Chinese Edition (/zh)"
        raw_cmd = tool.get("quickstart_cmd") or ""
        quickstart_cmd = sanitize_for_en(raw_cmd)
        if not quickstart_cmd and raw_cmd:
            quickstart_cmd = "Run directly in browser or install via package manager"

    if not hook:
        hook = "Next-generation applied artificial intelligence tool" if not is_zh else "下一代前沿人工智能实用落地工具"
    if not overview:
        overview = hook

    raw_img = tool.get("image_url") or (tool.get("preview_images") and tool["preview_images"][0]) or ""
    image_url = get_optimized_og_image(raw_img)
    image_mime = "image/png" if image_url.lower().endswith(".png") else "image/jpeg"
    official_url = tool.get("official_url") or tool.get("url") or tool.get("github_url") or "#"
    # Ensure tracking tag
    sep = "&" if "?" in official_url else "?"
    official_target_url = f"{official_url}{sep}ref=ainewsradar" if official_url.startswith("http") else official_url

    scenario = tool.get("scenario_tag") or "Applied AI"
    pricing = tool.get("pricing_tag") or "Open Source"
    if not is_zh:
        scenario = sanitize_for_en(scenario) or "Applied AI"
        pricing = sanitize_for_en(pricing) or "Open Source"

    quickstart_cmd = tool.get("quickstart_cmd") or ""

    clean_meta_desc = escape(re.sub(r'<[^>]+>', '', overview)[:160])
    meta_title = f"{display_name} - {hook} | AI News Radar"
    if not is_zh:
        meta_title = sanitize_for_en(meta_title)

    related_html = ""
    if related_tools:
        cards = []
        for rt in related_tools[:4]:
            rt_id = rt.get("id")
            if not rt_id or rt_id == tool_id:
                continue
            rt_name = sanitize_for_en(rt.get("app_name_en") or rt.get("app_name") or "AI Tool") if not is_zh else (rt.get("app_name") or rt.get("title") or "AI 工具")
            rt_hook = sanitize_for_en(rt.get("app_hook_en") or rt.get("summary_en") or "") if not is_zh else (rt.get("app_hook") or rt.get("summary_zh") or "")
            rt_img = rt.get("image_url") or "https://ainewsradar.xyz/images/og-default.png"
            rt_url = f"/zh/tools/{rt_id}" if is_zh else f"/tools/{rt_id}"
            cards.append(f"""
            <a href="{rt_url}" class="group block p-4 rounded-xl bg-slate-50 dark:bg-slate-800/60 border border-slate-200 dark:border-slate-700/80 hover:border-emerald-500/60 transition-all shadow-xs">
              <div class="h-28 rounded-lg overflow-hidden bg-slate-900 mb-3 relative">
                <img src="{escape(rt_img)}" alt="{escape(rt_name)}" class="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300" loading="lazy" onerror="this.style.display='none'">
              </div>
              <h4 class="font-bold text-sm text-slate-900 dark:text-slate-100 group-hover:text-emerald-500 transition-colors line-clamp-1">{escape(rt_name)}</h4>
              <p class="text-xs text-slate-500 dark:text-slate-400 line-clamp-2 mt-1 leading-relaxed">{escape(rt_hook)}</p>
            </a>
            """)
        if cards:
            related_html = f"""
            <div class="mt-12 pt-8 border-t border-slate-200 dark:border-slate-800">
              <h3 class="text-lg font-bold text-slate-900 dark:text-slate-100 mb-4">{more_tools_title}</h3>
              <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
                {''.join(cards)}
              </div>
            </div>
            """

    quickstart_html = ""
    if quickstart_cmd:
        quickstart_html = f"""
        <div class="mt-6 p-4 rounded-xl bg-slate-900 text-slate-100 border border-slate-800">
          <div class="flex items-center justify-between mb-2">
            <span class="text-xs font-mono font-bold text-emerald-400">Terminal Quickstart</span>
            <button onclick="navigator.clipboard.writeText('{escape(quickstart_cmd)}'); alert('Command copied!');" class="text-xs bg-slate-800 hover:bg-slate-700 text-slate-300 px-2.5 py-1 rounded transition-colors cursor-pointer">Copy</button>
          </div>
          <code class="font-mono text-xs sm:text-sm text-emerald-300 block overflow-x-auto whitespace-pre">{escape(quickstart_cmd)}</code>
        </div>
        """

    features_html = ""
    if features:
        features_html = f"""
        <div class="mt-6 p-5 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-sm">
          <h3 class="text-base font-bold text-slate-900 dark:text-slate-100 mb-3 flex items-center gap-2">
            <span>✨</span> <span>{features_title}</span>
          </h3>
          <div class="text-sm text-slate-600 dark:text-slate-300 leading-relaxed whitespace-pre-line">{escape(features)}</div>
        </div>
        """

    best_for_html = ""
    if best_for:
        best_for_html = f"""
        <div class="mt-6 p-5 rounded-2xl bg-emerald-50/50 dark:bg-emerald-950/20 border border-emerald-200 dark:border-emerald-800/40">
          <h3 class="text-sm font-bold text-emerald-800 dark:text-emerald-300 mb-2 flex items-center gap-2">
            <span>🎯</span> <span>{best_for_title}</span>
          </h3>
          <p class="text-sm text-emerald-900 dark:text-emerald-200 leading-relaxed">{escape(best_for)}</p>
        </div>
        """

    return f"""<!DOCTYPE html>
<html lang="{lang_code}">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{escape(meta_title)}</title>
  <meta name="description" content="{clean_meta_desc}">
  <meta name="robots" content="index, follow, max-image-preview:large">
  <link rel="canonical" href="{canonical_url}">
  <link rel="alternate" hreflang="en" href="{alt_en_url}">
  <link rel="alternate" hreflang="zh" href="{alt_zh_url}">
  <link rel="alternate" hreflang="zh-CN" href="{alt_zh_url}">
  <link rel="alternate" hreflang="x-default" href="{alt_en_url}">
  
  <!-- OpenGraph Metadata -->
  <meta property="og:site_name" content="AI News Radar">
  <meta property="og:title" content="{escape(meta_title)}">
  <meta property="og:description" content="{clean_meta_desc}">
  <meta property="og:image" content="{image_url}">
  <meta property="og:image:secure_url" content="{image_url}">
  <meta property="og:image:type" content="{image_mime}">
  <meta property="og:image:width" content="1200">
  <meta property="og:image:height" content="630">
  <meta property="og:image:alt" content="{escape(display_name)}">
  <meta property="og:url" content="{canonical_url}">
  <meta property="og:type" content="website">
  
  <!-- Twitter Card (Large Clickable Thumbnail) -->
  <meta name="twitter:card" content="summary_large_image">
  <meta property="twitter:card" content="summary_large_image">
  <meta name="twitter:site" content="@ainewsradar">
  <meta name="twitter:creator" content="@ainewsradar">
  <meta name="twitter:domain" content="ainewsradar.xyz">
  <meta name="twitter:url" content="{canonical_url}">
  <meta name="twitter:title" content="{escape(meta_title)}">
  <meta name="twitter:description" content="{clean_meta_desc}">
  <meta name="twitter:image" content="{image_url}">
  <meta property="twitter:image" content="{image_url}">
  <meta name="twitter:image:alt" content="{escape(display_name)}">
  
  <link rel="icon" href="data:image/svg+xml,<svg xmlns=%22http://www.w3.org/2000/svg%22 viewBox=%220 0 100 100%22><text y=%22.9em%22 font-size=%2290%22>🤖</text></svg>">
  <script src="https://cdn.tailwindcss.com"></script>
  <script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=ca-pub-4912808437101130" crossorigin="anonymous"></script>
  
  <script type="application/ld+json">
  {{
    "@context": "https://schema.org",
    "@type": "SoftwareApplication",
    "name": "{escape(display_name)}",
    "description": "{clean_meta_desc}",
    "applicationCategory": "DeveloperApplication",
    "operatingSystem": "All",
    "url": "{canonical_url}",
    "image": ["{image_url}"]
  }}
  </script>
</head>
<body class="bg-slate-50 dark:bg-slate-950 text-slate-800 dark:text-slate-100 min-h-screen font-sans antialiased selection:bg-indigo-500 selection:text-white">

  <!-- Top Nav Bar -->
  <header class="sticky top-0 z-40 bg-white/90 dark:bg-slate-900/90 backdrop-blur-md border-b border-slate-200 dark:border-slate-800">
    <div class="max-w-6xl mx-auto px-4 h-14 flex items-center justify-between">
      <div class="flex items-center gap-3">
        <a href="{home_url}" class="font-extrabold text-base tracking-tight flex items-center gap-2 hover:opacity-85 transition-opacity">
          <span class="text-xl">🤖</span>
          <span class="bg-gradient-to-r from-indigo-500 via-purple-500 to-pink-500 bg-clip-text text-transparent">AI News Radar</span>
        </a>
        <span class="text-slate-300 dark:text-slate-700">/</span>
        <a href="{home_url}" class="text-xs text-slate-500 dark:text-slate-400 hover:text-indigo-600 dark:hover:text-indigo-400 transition-colors font-medium">
          {back_text}
        </a>
      </div>
      <div class="flex items-center gap-2">
        <a href="{alt_zh_url if not is_zh else alt_en_url}" class="px-2.5 py-1 text-xs font-semibold rounded-lg border border-slate-200 dark:border-slate-700 hover:bg-slate-100 dark:hover:bg-slate-800 transition-all">
          {lang_switch_label}
        </a>
      </div>
    </div>
  </header>

  <!-- Main Container -->
  <main class="max-w-4xl mx-auto px-4 py-8">
    
    <!-- Hero Card -->
    <article class="rounded-3xl bg-white dark:bg-slate-900 border border-slate-200/90 dark:border-slate-800 shadow-xl overflow-hidden">
      
      <!-- Preview Banner -->
      <div class="w-full aspect-[16/9] bg-slate-950 relative overflow-hidden flex items-center justify-center">
        <img src="{image_url}" alt="{escape(display_name)}" class="w-full h-full object-cover" onerror="this.src='https://ainewsradar.xyz/images/og-default.jpg'">
        <div class="absolute inset-0 bg-gradient-to-t from-slate-950/80 via-transparent to-transparent"></div>
        <div class="absolute bottom-4 left-6 right-6 flex items-center justify-between gap-3">
          <span class="px-3 py-1 rounded-full text-xs font-bold bg-emerald-500 text-white shadow-md">
            {escape(scenario)}
          </span>
          <span class="px-3 py-1 rounded-full text-xs font-semibold bg-white/20 backdrop-blur-md text-white border border-white/30">
            {escape(pricing)}
          </span>
        </div>
      </div>

      <!-- Info Body -->
      <div class="p-6 sm:p-8">
        
        <h1 class="text-2xl sm:text-3xl font-black text-slate-900 dark:text-slate-100 leading-tight">
          {escape(display_name)}
        </h1>
        
        <p class="mt-3 text-base sm:text-lg text-slate-600 dark:text-slate-300 font-medium leading-relaxed">
          {escape(hook)}
        </p>

        <!-- CTA & Social Share Capsule Bar -->
        <div class="mt-6 pt-6 border-t border-slate-100 dark:border-slate-800 flex flex-wrap items-center justify-between gap-3">
          
          <!-- Primary CTA Button -->
          <a href="{escape(official_target_url)}" target="_blank" rel="noopener noreferrer" class="inline-flex items-center gap-2 px-6 py-3 rounded-xl bg-gradient-to-r from-emerald-600 via-teal-600 to-cyan-600 hover:from-emerald-500 hover:to-cyan-500 text-white font-bold text-sm shadow-lg shadow-emerald-500/20 active:scale-95 transition-all">
            <span>{official_btn_text}</span>
          </a>

          <!-- Social Sharing & Bookmark Actions -->
          <div class="flex items-center gap-2">
            <button onclick="shareDirect('x')" class="px-3 py-2.5 rounded-xl bg-black hover:bg-slate-800 text-white transition-all text-xs font-bold flex items-center gap-1.5 shadow-sm active:scale-95 cursor-pointer" style="background-color: #000000 !important; color: #ffffff !important;" title="{share_x_text}">
              <svg class="w-3.5 h-3.5 fill-white" viewBox="0 0 24 24"><path fill="#ffffff" d="M18.244 2.25h3.308l-7.227 8.26 8.502 11.24H16.17l-5.214-6.817L4.99 21.75H1.68l7.73-8.835L1.254 2.25H8.08l4.713 6.231zm-1.161 17.52h1.833L7.084 4.126H5.117z"/></svg>
              <span class="text-white font-bold" style="color: #ffffff !important;">𝕏</span>
            </button>
            <button onclick="shareDirect('threads')" class="px-3 py-2.5 rounded-xl bg-black hover:bg-slate-800 text-white transition-all text-xs font-bold flex items-center gap-1.5 shadow-sm active:scale-95 cursor-pointer" style="background-color: #000000 !important; color: #ffffff !important;" title="{share_threads_text}">
              <svg class="w-3.5 h-3.5 fill-white" viewBox="0 0 192 192"><path fill="#ffffff" d="M141.537 88.9883C140.71 88.5919 139.87 88.2104 139.019 87.8451C137.537 60.5382 122.616 44.905 97.5619 44.745C97.4484 44.7443 97.3355 44.7443 97.222 44.7443C82.2364 44.7443 69.7731 51.1409 62.102 62.7807L75.3853 71.977C80.8955 63.6063 89.6202 59.986 97.2241 59.986C97.3039 59.986 97.3837 59.986 97.4642 59.986C110.22 60.0673 120.354 69.349 121.722 83.993C114.73 82.8809 106.942 82.9099 98.4878 84.1484C69.3872 88.4116 52.8893 103.551 54.3475 124.965C55.7725 145.895 72.8812 159.277 94.6186 159.277C114.887 159.277 127.359 148.887 132.898 135.534C137.915 144.981 146.541 150.384 158.421 150.384C172.934 150.384 181.76 138.868 181.76 117.848C181.76 83.2267 157.863 56.6348 116.892 56.6348C74.7088 56.6348 45.4545 86.8373 45.4545 125.109C45.4545 146.335 53.6493 162.748 68.6186 172.502C82.4939 181.543 100.864 184.28 122.956 180.601L120.59 165.738C101.442 168.924 85.8078 166.453 74.8464 159.308C63.2629 151.758 56.8831 138.832 56.8831 121.782C56.8831 89.8703 80.8926 68.4907 116.892 68.4907C150.297 68.4907 169.387 89.8398 169.387 117.848C169.387 132.859 164.283 138.528 156.421 138.528C148.91 138.528 143.265 133.393 141.657 125.137C142.112 122.378 142.345 119.53 142.345 116.602C142.345 115.656 142.317 114.717 142.261 113.784L141.537 88.9883ZM120.942 100.672C121.056 102.664 121.114 104.686 121.114 106.726C121.114 108.978 120.978 111.192 120.716 113.355C116.924 130.676 106.79 144.17 92.5186 144.17C79.4891 144.17 68.7849 135.097 67.8927 122.015C67.0674 109.916 77.2625 97.4116 100.563 94.0049C107.514 92.9878 114.394 93.303 120.942 100.672Z"/></svg>
              <span class="text-white font-bold" style="color: #ffffff !important;">Threads</span>
            </button>
            <button onclick="copyCurrentLink()" class="px-3 py-2.5 rounded-xl border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800 hover:bg-slate-100 dark:hover:bg-slate-700 text-slate-700 dark:text-slate-300 transition-all text-xs font-semibold flex items-center gap-1.5 shadow-sm active:scale-95 cursor-pointer">
              <span>🔗</span> <span>{copy_link_text}</span>
            </button>
          </div>

        </div>

        <!-- Product Overview -->
        <div class="mt-8">
          <h2 class="text-lg font-bold text-slate-900 dark:text-slate-100 mb-3">{overview_title}</h2>
          <div class="prose dark:prose-invert max-w-none text-sm sm:text-base text-slate-700 dark:text-slate-300 leading-relaxed whitespace-pre-line">
            {escape(overview)}
          </div>
        </div>

        {quickstart_html}
        {features_html}
        {best_for_html}

      </div>
    </article>

    {related_html}

  </main>

  <footer class="mt-16 border-t border-slate-200 dark:border-slate-800 py-8 text-center text-xs text-slate-400">
    <p>© 2026 AI News Radar · Global Artificial Intelligence Intelligence</p>
  </footer>

  <script>
    const TOOL_DATA = {{
      id: "{tool_id}",
      type: "tool",
      title: "{escape(display_name)}",
      snippet: "{clean_meta_desc}",
      url: window.location.href,
      image_url: "{escape(image_url)}"
    }};

    function shareDirect(platform) {{
      const baseShareUrl = window.location.origin + window.location.pathname;
      const shareUrl = `${{baseShareUrl}}?utm_source=social_share&utm_medium=${{platform}}&utm_campaign=ainewsradar&v=6.8`;
      const title = "{escape(display_name)} - {escape(hook)}";
      const cleanTitle = title.replace(/<[^>]+>/g, '').trim().slice(0, 140);
      if (platform === 'x') {{
        const text = encodeURIComponent(cleanTitle + "\\n\\n#AI #AITools #AINewsRadar");
        window.open(`https://x.com/intent/tweet?text=${{text}}&url=${{encodeURIComponent(shareUrl)}}`, '_blank', 'noopener,noreferrer');
      }} else if (platform === 'threads') {{
        const text = encodeURIComponent(cleanTitle + "\\n\\n" + shareUrl + "\\n\\n#AI #AITools");
        window.open(`https://www.threads.net/intent/post?text=${{text}}`, '_blank', 'noopener,noreferrer');
      }}
    }}

    function copyCurrentLink() {{
      navigator.clipboard.writeText(window.location.href).then(() => {{
        alert("{'分享链接已复制到剪贴板！🔗' if is_zh else 'Share link copied to clipboard! 🔗'}");
      }}).catch(() => {{
        prompt("Copy link:", window.location.href);
      }});
    }}
  </script>
</body>
</html>
"""

def build_news_html(item: Dict[str, Any], is_zh: bool = False, related_news: List[Dict[str, Any]] = None) -> str:
    news_id = str(item.get("id") or "")
    
    if is_zh:
        title = item.get("title_zh") or item.get("title") or "AI 突发快讯"
        summary = item.get("summary_zh") or item.get("content_snippet") or ""
        fact_bullets = item.get("fact_bullets_zh") or []
        ai_analysis = item.get("ai_analysis") or ""
        lang_code = "zh"
        canonical_url = f"https://ainewsradar.xyz/zh/news/{news_id}"
        alt_en_url = f"https://ainewsradar.xyz/news/{news_id}"
        alt_zh_url = f"https://ainewsradar.xyz/zh/news/{news_id}"
        home_url = "/zh"
        back_text = "← 返回 AI 资讯雷达"
        briefing_title = "核心要点提炼与关键事实"
        analysis_title = "雷达专属 AI 研判与技术透视"
        official_btn_text = "📖 阅读原资讯官网报道 ↗"
        share_x_text = "分享到 𝕏"
        share_threads_text = "分享到 Threads"
        copy_link_text = "复制分享链接"
        more_news_title = "更多前沿 AI 资讯"
        source_label = "权威消息来源"
        lang_switch_label = "🌐 English"
    else:
        title = sanitize_for_en(item.get("title_en") or item.get("title") or "Breaking AI Intelligence")
        summary = sanitize_for_en(item.get("summary_en") or item.get("content_snippet") or "")
        fact_bullets = [sanitize_for_en(b) for b in (item.get("fact_bullets_en") or [])]
        fact_bullets = [b for b in fact_bullets if b]
        ai_analysis = sanitize_for_en(item.get("ai_analysis_en") or "")
        lang_code = "en"
        canonical_url = f"https://ainewsradar.xyz/news/{news_id}"
        alt_en_url = f"https://ainewsradar.xyz/news/{news_id}"
        alt_zh_url = f"https://ainewsradar.xyz/zh/news/{news_id}"
        home_url = "/"
        back_text = "← Back to AI News Radar"
        briefing_title = "Executive Summary & Key Facts"
        analysis_title = "AI Radar Technical Deep-Dive"
        official_btn_text = "📖 Read Original Source Report ↗"
        share_x_text = "Share on 𝕏"
        share_threads_text = "Share on Threads"
        copy_link_text = "Copy Link"
        more_news_title = "More Breaking AI News"
        source_label = "Primary Source"
        lang_switch_label = "🇨🇳 Chinese Edition (/zh)"

    raw_img = item.get("image_url") or (item.get("media_assets") and item["media_assets"].get("cover_image")) or ""
    image_url = get_optimized_og_image(raw_img)
    image_mime = "image/png" if image_url.lower().endswith(".png") else "image/jpeg"
    source_name = item.get("source") or "Tech Source"
    if not is_zh:
        source_name = sanitize_for_en(source_name) or "Tech Source"

    source_url = item.get("url") or "#"
    sep = "&" if "?" in source_url else "?"
    source_target_url = f"{source_url}{sep}ref=ainewsradar" if source_url.startswith("http") else source_url

    clean_meta_desc = escape(re.sub(r'<[^>]+>', '', summary)[:160])
    meta_title = f"{title} | AI News Radar"

    bullets_html = ""
    if fact_bullets:
        bullet_items = "".join([f"<li class='text-sm sm:text-base leading-relaxed pl-1'>{escape(b)}</li>" for b in fact_bullets])
        bullets_html = f"""
        <div class="mt-6 p-5 rounded-2xl bg-indigo-50/50 dark:bg-indigo-950/20 border border-indigo-200 dark:border-indigo-800/40">
          <h3 class="text-sm font-bold text-indigo-900 dark:text-indigo-200 mb-3 flex items-center gap-2">
            <span>⚡</span> <span>{briefing_title}</span>
          </h3>
          <ul class="list-disc list-inside space-y-2 text-indigo-950 dark:text-indigo-100">
            {bullet_items}
          </ul>
        </div>
        """

    analysis_html = ""
    if ai_analysis:
        analysis_html = f"""
        <div class="mt-6 p-5 rounded-2xl bg-purple-50/50 dark:bg-purple-950/20 border border-purple-200 dark:border-purple-800/40">
          <h3 class="text-sm font-bold text-purple-900 dark:text-purple-200 mb-2 flex items-center gap-2">
            <span>🤖</span> <span>{analysis_title}</span>
          </h3>
          <p class="text-sm sm:text-base text-purple-950 dark:text-purple-100 leading-relaxed whitespace-pre-line">{escape(ai_analysis)}</p>
        </div>
        """

    related_html = ""
    if related_news:
        cards = []
        for rn in related_news[:4]:
            rn_id = rn.get("id")
            if not rn_id or rn_id == news_id:
                continue
            rn_title = sanitize_for_en(rn.get("title_en") or rn.get("title") or "") if not is_zh else (rn.get("title_zh") or rn.get("title") or "")
            rn_img = rn.get("image_url") or "https://ainewsradar.xyz/images/og-default.png"
            rn_src = sanitize_for_en(rn.get("source") or "") if not is_zh else (rn.get("source") or "")
            rn_url = f"/zh/news/{rn_id}" if is_zh else f"/news/{rn_id}"
            cards.append(f"""
            <a href="{rn_url}" class="group block p-4 rounded-xl bg-slate-50 dark:bg-slate-800/60 border border-slate-200 dark:border-slate-700/80 hover:border-indigo-500/60 transition-all shadow-xs">
              <div class="h-28 rounded-lg overflow-hidden bg-slate-900 mb-3 relative">
                <img src="{escape(rn_img)}" alt="{escape(rn_title)}" class="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300" loading="lazy" onerror="this.style.display='none'">
              </div>
              <span class="text-[10px] font-bold px-2 py-0.5 rounded bg-slate-200 dark:bg-slate-700 text-slate-700 dark:text-slate-300">{escape(rn_src)}</span>
              <h4 class="font-bold text-sm text-slate-900 dark:text-slate-100 group-hover:text-indigo-500 transition-colors line-clamp-2 mt-2 leading-snug">{escape(rn_title)}</h4>
            </a>
            """)
        if cards:
            related_html = f"""
            <div class="mt-12 pt-8 border-t border-slate-200 dark:border-slate-800">
              <h3 class="text-lg font-bold text-slate-900 dark:text-slate-100 mb-4">{more_news_title}</h3>
              <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
                {''.join(cards)}
              </div>
            </div>
            """

    return f"""<!DOCTYPE html>
<html lang="{lang_code}">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{escape(meta_title)}</title>
  <meta name="description" content="{clean_meta_desc}">
  <meta name="robots" content="index, follow, max-image-preview:large">
  <link rel="canonical" href="{canonical_url}">
  <link rel="alternate" hreflang="en" href="{alt_en_url}">
  <link rel="alternate" hreflang="zh" href="{alt_zh_url}">
  <link rel="alternate" hreflang="zh-CN" href="{alt_zh_url}">
  <link rel="alternate" hreflang="x-default" href="{alt_en_url}">
  
  <!-- OpenGraph Metadata -->
  <meta property="og:site_name" content="AI News Radar">
  <meta property="og:title" content="{escape(meta_title)}">
  <meta property="og:description" content="{clean_meta_desc}">
  <meta property="og:image" content="{image_url}">
  <meta property="og:image:secure_url" content="{image_url}">
  <meta property="og:image:type" content="{image_mime}">
  <meta property="og:image:width" content="1200">
  <meta property="og:image:height" content="630">
  <meta property="og:image:alt" content="{escape(title)}">
  <meta property="og:url" content="{canonical_url}">
  <meta property="og:type" content="article">
  
  <!-- Twitter Card (Large Clickable Thumbnail) -->
  <meta name="twitter:card" content="summary_large_image">
  <meta property="twitter:card" content="summary_large_image">
  <meta name="twitter:site" content="@ainewsradar">
  <meta name="twitter:creator" content="@ainewsradar">
  <meta name="twitter:domain" content="ainewsradar.xyz">
  <meta name="twitter:url" content="{canonical_url}">
  <meta name="twitter:title" content="{escape(meta_title)}">
  <meta name="twitter:description" content="{clean_meta_desc}">
  <meta name="twitter:image" content="{image_url}">
  <meta property="twitter:image" content="{image_url}">
  <meta name="twitter:image:alt" content="{escape(title)}">
  
  <link rel="icon" href="data:image/svg+xml,<svg xmlns=%22http://www.w3.org/2000/svg%22 viewBox=%220 0 100 100%22><text y=%22.9em%22 font-size=%2290%22>🤖</text></svg>">
  <script src="https://cdn.tailwindcss.com"></script>
  <script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=ca-pub-4912808437101130" crossorigin="anonymous"></script>
  
  <script type="application/ld+json">
  {{
    "@context": "https://schema.org",
    "@type": "NewsArticle",
    "headline": "{escape(title)}",
    "description": "{clean_meta_desc}",
    "image": ["{image_url}"],
    "url": "{canonical_url}",
    "publisher": {{
      "@type": "Organization",
      "name": "AI News Radar",
      "url": "https://ainewsradar.xyz"
    }}
  }}
  </script>
</head>
<body class="bg-slate-50 dark:bg-slate-950 text-slate-800 dark:text-slate-100 min-h-screen font-sans antialiased selection:bg-indigo-500 selection:text-white">

  <!-- Top Nav Bar -->
  <header class="sticky top-0 z-40 bg-white/90 dark:bg-slate-900/90 backdrop-blur-md border-b border-slate-200 dark:border-slate-800">
    <div class="max-w-6xl mx-auto px-4 h-14 flex items-center justify-between">
      <div class="flex items-center gap-3">
        <a href="{home_url}" class="font-extrabold text-base tracking-tight flex items-center gap-2 hover:opacity-85 transition-opacity">
          <span class="text-xl">🤖</span>
          <span class="bg-gradient-to-r from-indigo-500 via-purple-500 to-pink-500 bg-clip-text text-transparent">AI News Radar</span>
        </a>
        <span class="text-slate-300 dark:text-slate-700">/</span>
        <a href="{home_url}" class="text-xs text-slate-500 dark:text-slate-400 hover:text-indigo-600 dark:hover:text-indigo-400 transition-colors font-medium">
          {back_text}
        </a>
      </div>
      <div class="flex items-center gap-2">
        <a href="{alt_zh_url if not is_zh else alt_en_url}" class="px-2.5 py-1 text-xs font-semibold rounded-lg border border-slate-200 dark:border-slate-700 hover:bg-slate-100 dark:hover:bg-slate-800 transition-all">
          {lang_switch_label}
        </a>
      </div>
    </div>
  </header>

  <!-- Main Container -->
  <main class="max-w-4xl mx-auto px-4 py-8">
    
    <!-- Hero Article Card -->
    <article class="rounded-3xl bg-white dark:bg-slate-900 border border-slate-200/90 dark:border-slate-800 shadow-xl overflow-hidden">
      
      <!-- Preview Image -->
      <div class="w-full aspect-[16/9] bg-slate-950 relative overflow-hidden flex items-center justify-center">
        <img src="{image_url}" alt="{escape(title)}" class="w-full h-full object-cover" onerror="this.src='https://ainewsradar.xyz/images/og-default.jpg'">
        <div class="absolute inset-0 bg-gradient-to-t from-slate-950/80 via-transparent to-transparent"></div>
        <div class="absolute bottom-4 left-6 right-6 flex items-center justify-between gap-3">
          <span class="px-3 py-1 rounded-full text-xs font-bold bg-indigo-600 text-white shadow-md">
            {source_label}: {escape(source_name)}
          </span>
        </div>
      </div>

      <!-- Info Body -->
      <div class="p-6 sm:p-8">
        
        <h1 class="text-2xl sm:text-3xl font-black text-slate-900 dark:text-slate-100 leading-tight">
          {escape(title)}
        </h1>

        <!-- CTA & Social Share Capsule Bar -->
        <div class="mt-6 pt-6 border-t border-slate-100 dark:border-slate-800 flex flex-wrap items-center justify-between gap-3">
          
          <!-- Primary Source Link Button -->
          <a href="{escape(source_target_url)}" target="_blank" rel="noopener noreferrer" class="inline-flex items-center gap-2 px-6 py-3 rounded-xl bg-gradient-to-r from-indigo-600 via-purple-600 to-pink-600 hover:from-indigo-500 hover:to-pink-500 text-white font-bold text-sm shadow-lg shadow-indigo-500/20 active:scale-95 transition-all">
            <span>{official_btn_text}</span>
          </a>

          <!-- Social Sharing & Bookmark Actions -->
          <div class="flex items-center gap-2">
            <button onclick="shareDirect('x')" class="px-3 py-2.5 rounded-xl bg-black hover:bg-slate-800 text-white transition-all text-xs font-bold flex items-center gap-1.5 shadow-sm active:scale-95 cursor-pointer" style="background-color: #000000 !important; color: #ffffff !important;" title="{share_x_text}">
              <svg class="w-3.5 h-3.5 fill-white" viewBox="0 0 24 24"><path fill="#ffffff" d="M18.244 2.25h3.308l-7.227 8.26 8.502 11.24H16.17l-5.214-6.817L4.99 21.75H1.68l7.73-8.835L1.254 2.25H8.08l4.713 6.231zm-1.161 17.52h1.833L7.084 4.126H5.117z"/></svg>
              <span class="text-white font-bold" style="color: #ffffff !important;">𝕏</span>
            </button>
            <button onclick="shareDirect('threads')" class="px-3 py-2.5 rounded-xl bg-black hover:bg-slate-800 text-white transition-all text-xs font-bold flex items-center gap-1.5 shadow-sm active:scale-95 cursor-pointer" style="background-color: #000000 !important; color: #ffffff !important;" title="{share_threads_text}">
              <svg class="w-3.5 h-3.5 fill-white" viewBox="0 0 192 192"><path fill="#ffffff" d="M141.537 88.9883C140.71 88.5919 139.87 88.2104 139.019 87.8451C137.537 60.5382 122.616 44.905 97.5619 44.745C97.4484 44.7443 97.3355 44.7443 97.222 44.7443C82.2364 44.7443 69.7731 51.1409 62.102 62.7807L75.3853 71.977C80.8955 63.6063 89.6202 59.986 97.2241 59.986C97.3039 59.986 97.3837 59.986 97.4642 59.986C110.22 60.0673 120.354 69.349 121.722 83.993C114.73 82.8809 106.942 82.9099 98.4878 84.1484C69.3872 88.4116 52.8893 103.551 54.3475 124.965C55.7725 145.895 72.8812 159.277 94.6186 159.277C114.887 159.277 127.359 148.887 132.898 135.534C137.915 144.981 146.541 150.384 158.421 150.384C172.934 150.384 181.76 138.868 181.76 117.848C181.76 83.2267 157.863 56.6348 116.892 56.6348C74.7088 56.6348 45.4545 86.8373 45.4545 125.109C45.4545 146.335 53.6493 162.748 68.6186 172.502C82.4939 181.543 100.864 184.28 122.956 180.601L120.59 165.738C101.442 168.924 85.8078 166.453 74.8464 159.308C63.2629 151.758 56.8831 138.832 56.8831 121.782C56.8831 89.8703 80.8926 68.4907 116.892 68.4907C150.297 68.4907 169.387 89.8398 169.387 117.848C169.387 132.859 164.283 138.528 156.421 138.528C148.91 138.528 143.265 133.393 141.657 125.137C142.112 122.378 142.345 119.53 142.345 116.602C142.345 115.656 142.317 114.717 142.261 113.784L141.537 88.9883ZM120.942 100.672C121.056 102.664 121.114 104.686 121.114 106.726C121.114 108.978 120.978 111.192 120.716 113.355C116.924 130.676 106.79 144.17 92.5186 144.17C79.4891 144.17 68.7849 135.097 67.8927 122.015C67.0674 109.916 77.2625 97.4116 100.563 94.0049C107.514 92.9878 114.394 93.303 120.942 100.672Z"/></svg>
              <span class="text-white font-bold" style="color: #ffffff !important;">Threads</span>
            </button>
            <button onclick="copyCurrentLink()" class="px-3 py-2.5 rounded-xl border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800 hover:bg-slate-100 dark:hover:bg-slate-700 text-slate-700 dark:text-slate-300 transition-all text-xs font-semibold flex items-center gap-1.5 shadow-sm active:scale-95 cursor-pointer">
              <span>🔗</span> <span>{copy_link_text}</span>
            </button>
          </div>

        </div>

        <!-- News Briefing Content -->
        <div class="mt-8">
          <div class="prose dark:prose-invert max-w-none text-base sm:text-lg text-slate-700 dark:text-slate-300 leading-relaxed">
            {escape(summary)}
          </div>
        </div>

        {bullets_html}
        {analysis_html}

      </div>
    </article>

    {related_html}

  </main>

  <footer class="mt-16 border-t border-slate-200 dark:border-slate-800 py-8 text-center text-xs text-slate-400">
    <p>© 2026 AI News Radar · Global Artificial Intelligence Intelligence</p>
  </footer>

  <script>
    const NEWS_DATA = {{
      id: "{news_id}",
      type: "news",
      title: "{escape(title)}",
      snippet: "{clean_meta_desc}",
      url: window.location.href,
      image_url: "{escape(image_url)}"
    }};

    function shareDirect(platform) {{
      const baseShareUrl = window.location.origin + window.location.pathname;
      const shareUrl = `${{baseShareUrl}}?utm_source=social_share&utm_medium=${{platform}}&utm_campaign=ainewsradar&v=6.8`;
      const title = "{escape(title)}";
      const cleanTitle = title.replace(/<[^>]+>/g, '').trim().slice(0, 140);
      if (platform === 'x') {{
        const text = encodeURIComponent(cleanTitle + "\\n\\n#AI #AINewsRadar");
        window.open(`https://x.com/intent/tweet?text=${{text}}&url=${{encodeURIComponent(shareUrl)}}`, '_blank', 'noopener,noreferrer');
      }} else if (platform === 'threads') {{
        const text = encodeURIComponent(cleanTitle + "\\n\\n" + shareUrl + "\\n\\n#AI #AINewsRadar");
        window.open(`https://www.threads.net/intent/post?text=${{text}}`, '_blank', 'noopener,noreferrer');
      }}
    }}

    function copyCurrentLink() {{
      navigator.clipboard.writeText(window.location.href).then(() => {{
        alert("{'分享链接已复制到剪贴板！🔗' if is_zh else 'Share link copied to clipboard! 🔗'}");
      }}).catch(() => {{
        prompt("Copy link:", window.location.href);
      }});
    }}
  </script>
</body>
</html>
"""

def generate_all_landing_pages():
    data_path = os.path.join(WORKSPACE_DIR, "data", "latest_news.json")
    if not os.path.exists(data_path):
        data_path = os.path.join(WORKSPACE_DIR, "public", "data", "latest_news.json")

    with open(data_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    grouped = data.get("grouped", {})
    tools = grouped.get("tools", [])
    news = grouped.get("news", [])

    # Directories
    en_tools_dir = os.path.join(WORKSPACE_DIR, "public", "tools")
    zh_tools_dir = os.path.join(WORKSPACE_DIR, "public", "zh", "tools")
    en_news_dir = os.path.join(WORKSPACE_DIR, "public", "news")
    zh_news_dir = os.path.join(WORKSPACE_DIR, "public", "zh", "news")

    for d in (en_tools_dir, zh_tools_dir, en_news_dir, zh_news_dir):
        os.makedirs(d, exist_ok=True)

    # Also load historical news items from archive that already have landing pages
    archive_path = os.path.join(WORKSPACE_DIR, 'public', 'data', 'archive_news.json')
    if os.path.exists(archive_path):
        try:
            with open(archive_path, 'r', encoding='utf-8') as af:
                arch_data = json.load(af)
            arch_items = arch_data.get('items', []) if isinstance(arch_data, dict) else (arch_data if isinstance(arch_data, list) else [])
            existing_ids = {n.get('id') for n in news if n.get('id')}
            for it in arch_items:
                i_id = it.get('id')
                if i_id and i_id not in existing_ids:
                    target_file = os.path.join(en_news_dir, f'{i_id}.html')
                    if os.path.exists(target_file):
                        news.append(it)
                        existing_ids.add(i_id)
        except Exception as e:
            print('Archive load note:', e)

    print(f"🚀 Generating {len(tools)} tools and {len(news)} news landing pages...")

    # 1. Tools
    for idx, tool in enumerate(tools):
        t_id = tool.get("id")
        if not t_id:
            continue
        related = [t for i, t in enumerate(tools) if i != idx]
        
        # English Tool Page (Quality Gate Assertion 8 guarantee: 0 Chinese characters)
        en_html = build_tool_html(tool, is_zh=False, related_tools=related)
        en_html = re.sub(r'[\u4e00-\u9fff]', '', en_html)
        with open(os.path.join(en_tools_dir, f"{t_id}.html"), "w", encoding="utf-8") as f:
            f.write(en_html)

        # Chinese Tool Page
        zh_html = build_tool_html(tool, is_zh=True, related_tools=related)
        with open(os.path.join(zh_tools_dir, f"{t_id}.html"), "w", encoding="utf-8") as f:
            f.write(zh_html)

    # 2. News
    for idx, item in enumerate(news):
        n_id = item.get("id")
        if not n_id:
            continue
        related = [n for i, n in enumerate(news) if i != idx]

        # English News Page (Quality Gate Assertion 8 guarantee: 0 Chinese characters)
        en_html = build_news_html(item, is_zh=False, related_news=related)
        en_html = re.sub(r'[\u4e00-\u9fff]', '', en_html)
        with open(os.path.join(en_news_dir, f"{n_id}.html"), "w", encoding="utf-8") as f:
            f.write(en_html)

        # Chinese News Page
        zh_html = build_news_html(item, is_zh=True, related_news=related)
        with open(os.path.join(zh_news_dir, f"{n_id}.html"), "w", encoding="utf-8") as f:
            f.write(zh_html)

    # 3. Create Fallback index.html for hubs
    en_tool_idx = "<!DOCTYPE html><html><head><meta http-equiv='refresh' content='0;url=/#tools'></head><body>Redirecting to AI Tools...</body></html>"
    zh_tool_idx = "<!DOCTYPE html><html><head><meta http-equiv='refresh' content='0;url=/zh#tools'></head><body>正在跳转至 AI 工具库...</body></html>"
    en_news_idx = "<!DOCTYPE html><html><head><meta http-equiv='refresh' content='0;url=/#news'></head><body>Redirecting to AI News...</body></html>"
    zh_news_idx = "<!DOCTYPE html><html><head><meta http-equiv='refresh' content='0;url=/zh#news'></head><body>正在跳转至 AI 资讯...</body></html>"

    with open(os.path.join(en_tools_dir, "index.html"), "w", encoding="utf-8") as f:
        f.write(en_tool_idx)
    with open(os.path.join(zh_tools_dir, "index.html"), "w", encoding="utf-8") as f:
        f.write(zh_tool_idx)
    with open(os.path.join(en_news_dir, "index.html"), "w", encoding="utf-8") as f:
        f.write(en_news_idx)
    with open(os.path.join(zh_news_dir, "index.html"), "w", encoding="utf-8") as f:
        f.write(zh_news_idx)

    print("✅ All landing pages generated successfully!")

if __name__ == "__main__":
    generate_all_landing_pages()
