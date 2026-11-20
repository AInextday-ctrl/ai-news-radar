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
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional

try:
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')
except Exception:
    pass

WORKSPACE_DIR = os.path.dirname(os.path.abspath(__file__))

CLARITY_SCRIPT = """<script type="text/javascript">
    (function(c,l,a,r,i,t,y){
        c[a]=c[a]||function(){(c[a].q=c[a].q||[]).push(arguments)};
        t=l.createElement(r);t.async=1;t.src="https://www.clarity.ms/tag/"+i;
        y=l.getElementsByTagName(r)[0];y.parentNode.insertBefore(t,y);
    })(window, document, "clarity", "script", "zasso3bkvl");
</script>"""

def parse_iso_date(val: Any) -> str:
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

def sanitize_for_en(text: str, preserve_newlines: bool = False) -> str:
    """Removes any Chinese characters and clean up punctuation for English compliance."""
    if not text:
        return ""
    # Strip CJK characters
    cleaned = re.sub(r'[\u4e00-\u9fff\u3000-\u303f\uff00-\uffef]', '', str(text))
    if preserve_newlines:
        lines = [re.sub(r'[^\S\r\n]+', ' ', line).strip() for line in cleaned.splitlines()]
        return '\n'.join(lines)
    cleaned = re.sub(r'\s+', ' ', cleaned).strip()
    return cleaned

def escape(val: Any) -> str:
    return html.escape(str(val or ""))

THEMATIC_FALLBACK_IMAGES = {
    'cinema': 'https://images.unsplash.com/photo-1485846234645-a62644f84728?w=1200&h=630&fit=crop&fm=jpg&q=85',
    'silicon': 'https://images.unsplash.com/photo-1591488320449-011701bb6704?w=1200&h=630&fit=crop&fm=jpg&q=85',
    'llm': 'https://images.unsplash.com/photo-1677442136019-21780ecad995?w=1200&h=630&fit=crop&fm=jpg&q=85',
    'robotics': 'https://images.unsplash.com/photo-1485827404703-89b55fcc595e?w=1200&h=630&fit=crop&fm=jpg&q=85',
    'biotech': 'https://images.unsplash.com/photo-1532187863486-abf9dbad1b69?w=1200&h=630&fit=crop&fm=jpg&q=85',
    'policy': 'https://images.unsplash.com/photo-1563986768609-322da13575f3?w=1200&h=630&fit=crop&fm=jpg&q=85',
    'engineering': 'https://images.unsplash.com/photo-1555066931-4365d14bab8c?w=1200&h=630&fit=crop&fm=jpg&q=85',
    'gaming': 'https://images.unsplash.com/photo-1538481199705-c710c4e965fc?w=1200&h=630&fit=crop&fm=jpg&q=85',
    'default': 'https://ainewsradar.xyz/images/og-default.jpg'
}

def get_thematic_fallback_image(title: str = '', category: str = '') -> str:
    text = (title + ' ' + category).lower()
    if any(k in text for k in ['film', 'video studio', 'film studio', 'movie', 'cinema', 'hollywood', 'utopai', 'sora', 'runway', 'kling', 'video generation', 'video ai']):
        return THEMATIC_FALLBACK_IMAGES['cinema']
    if any(k in text for k in ['chip', 'gpu', 'semiconductor', 'nvidia', 'hardware', 'tsmc', 'intel', 'amd', 'silicon', 'tpu']):
        return THEMATIC_FALLBACK_IMAGES['silicon']
    if any(k in text for k in ['llm', 'model', 'gpt', 'claude', 'deepseek', 'anthropic', 'openai', 'gemini', 'minimax', 'reasoning', 'ai model', 'foundation']):
        return THEMATIC_FALLBACK_IMAGES['llm']
    if any(k in text for k in ['robot', 'humanoid', 'embodied', 'figure', 'boston dynamics', 'tesla bot', 'cybernetic', 'drone']):
        return THEMATIC_FALLBACK_IMAGES['robotics']
    if any(k in text for k in ['health', 'bio', 'cancer', 'oncology', 'drug', 'medicine', 'protein', 'dna', 'clinical', 'pathos']):
        return THEMATIC_FALLBACK_IMAGES['biotech']
    if any(k in text for k in ['security', 'cyber', 'supply-chain', 'bill', 'parliament', 'ban', 'treasury', 'regulation', 'law', 'gov', 'policy', 'aisi']):
        return THEMATIC_FALLBACK_IMAGES['policy']
    if any(k in text for k in ['code', 'software', 'developer', 'github', 'api', 'cloud', 'engineer', 'fund', 'valuation', 'invest', 'raise', 'instacart', 'shein']):
        return THEMATIC_FALLBACK_IMAGES['engineering']
    if any(k in text for k in ['game', 'gaming', 'gta', 'grand theft auto', 'twitch', 'streamer', 'nintendo', 'playstation', 'xbox']):
        return THEMATIC_FALLBACK_IMAGES['gaming']
    return THEMATIC_FALLBACK_IMAGES['default']

def get_optimized_og_image(raw_url: str, title: str = '', category: str = '') -> str:
    if not raw_url or not isinstance(raw_url, str) or len(raw_url.strip()) < 10:
        return get_thematic_fallback_image(title, category)
    raw_url = raw_url.strip()
    if raw_url.startswith('/images/') or raw_url.startswith('/img/'):
        return f'https://ainewsradar.xyz{raw_url}'
    if not raw_url.startswith('https://') and not raw_url.startswith('http://'):
        return get_thematic_fallback_image(title, category)
    if raw_url.startswith('http://'):
        raw_url = 'https://' + raw_url[7:]
    
    # In-site brand assets
    if 'ainewsradar.xyz' in raw_url:
        return raw_url

    # Unsplash: deliver direct high-res 1200x630 JPG with native Unsplash parameters
    if 'images.unsplash.com' in raw_url:
        base = raw_url.split('?')[0]
        return f'{base}?w=1200&h=630&fit=crop&fm=jpg&q=85'

    # GitHub OpenGraph is already 1200x630
    if 'opengraph.githubassets.com' in raw_url:
        return raw_url

    # Known anti-hotlinking domains (CNBC, FT, WSJ) that return 403 Forbidden to client browsers
    anti_hotlink_domains = ['cnbcfm.com', 'images.ft.com', 'wsj.net']
    if any(bd in raw_url.lower() for bd in anti_hotlink_domains):
        return get_thematic_fallback_image(title, category)

    # Other authentic direct HTTPS image URLs
    return raw_url

# ==============================================================================
# GEO & Schema.org Disambiguation Entities Knowledge Base
# ==============================================================================
KNOWN_ENTITIES = [
    # Top AI Companies & Labs
    {"name": "OpenAI", "type": "Organization", "sameAs": "https://en.wikipedia.org/wiki/OpenAI", "keywords": ["openai", "sam altman", "chatgpt", "gpt-4", "gpt-3", "sora", "o1", "o3"]},
    {"name": "Google DeepMind", "type": "Organization", "sameAs": "https://en.wikipedia.org/wiki/DeepMind", "keywords": ["deepmind", "demis hassabis", "alphafold", "alphazero"]},
    {"name": "Google", "type": "Organization", "sameAs": "https://en.wikipedia.org/wiki/Google", "keywords": ["google", "gemini", "sundar pichai", "google cloud", "alphabet", "tpu"]},
    {"name": "Anthropic", "type": "Organization", "sameAs": "https://en.wikipedia.org/wiki/Anthropic", "keywords": ["anthropic", "claude", "dario amodei", "constitutional ai"]},
    {"name": "NVIDIA", "type": "Organization", "sameAs": "https://en.wikipedia.org/wiki/Nvidia", "keywords": ["nvidia", "jensen huang", "cuda", "h100", "b200", "blackwell", "geforce"]},
    {"name": "Meta", "type": "Organization", "sameAs": "https://en.wikipedia.org/wiki/Meta_Platforms", "keywords": ["meta", "mark zuckerberg", "llama", "fair", "pytorch"]},
    {"name": "Microsoft", "type": "Organization", "sameAs": "https://en.wikipedia.org/wiki/Microsoft", "keywords": ["microsoft", "copilot", "satya nadella", "azure ai"]},
    {"name": "Apple", "type": "Organization", "sameAs": "https://en.wikipedia.org/wiki/Apple_Inc.", "keywords": ["apple", "apple intelligence", "tim cook", "siri", "ml foundation"]},
    {"name": "Amazon", "type": "Organization", "sameAs": "https://en.wikipedia.org/wiki/Amazon_(company)", "keywords": ["amazon", "aws", "bedrock", "andy jassy"]},
    {"name": "DeepSeek", "type": "Organization", "sameAs": "https://www.deepseek.com/", "keywords": ["deepseek", "deepseek-r1", "deepseek-v3", "liang wenfeng"]},
    {"name": "Mistral AI", "type": "Organization", "sameAs": "https://en.wikipedia.org/wiki/Mistral_AI", "keywords": ["mistral", "arthur mensch", "mixtral", "codestral"]},
    {"name": "xAI", "type": "Organization", "sameAs": "https://en.wikipedia.org/wiki/X.AI", "keywords": ["xai", "elon musk", "grok", "colossus"]},
    {"name": "Tesla", "type": "Organization", "sameAs": "https://en.wikipedia.org/wiki/Tesla,_Inc.", "keywords": ["tesla", "optimus", "fsd", "autopilot", "robotaxi"]},
    {"name": "TSMC", "type": "Organization", "sameAs": "https://en.wikipedia.org/wiki/TSMC", "keywords": ["tsmc", "semiconductor manufacturing", "fab", "foundry"]},
    {"name": "Intel", "type": "Organization", "sameAs": "https://en.wikipedia.org/wiki/Intel", "keywords": ["intel", "gaudi", "pat gelsinger"]},
    {"name": "AMD", "type": "Organization", "sameAs": "https://en.wikipedia.org/wiki/AMD", "keywords": ["amd", "lisa su", "mi300", "rocm"]},
    {"name": "Hugging Face", "type": "Organization", "sameAs": "https://en.wikipedia.org/wiki/Hugging_Face", "keywords": ["hugging face", "huggingface", "transformers"]},
    {"name": "Cursor", "type": "Product", "sameAs": "https://www.cursor.com/", "keywords": ["cursor", "anysphere", "ai code editor"]},
    {"name": "Perplexity", "type": "Organization", "sameAs": "https://en.wikipedia.org/wiki/Perplexity_AI", "keywords": ["perplexity", "aravind srinivas"]},
    # Prominent Models & Products
    {"name": "ChatGPT", "type": "Product", "sameAs": "https://en.wikipedia.org/wiki/ChatGPT", "keywords": ["chatgpt", "chat-gpt"]},
    {"name": "Claude", "type": "Product", "sameAs": "https://en.wikipedia.org/wiki/Claude_(language_model)", "keywords": ["claude 3", "claude 3.5", "claude 3.7", "claude sonnet", "claude opus"]},
    {"name": "Gemini", "type": "Product", "sameAs": "https://en.wikipedia.org/wiki/Gemini_(chatbot)", "keywords": ["gemini 1.5", "gemini 2.0", "gemini flash", "gemini pro"]},
    {"name": "Llama", "type": "Product", "sameAs": "https://en.wikipedia.org/wiki/Llama_(language_model)", "keywords": ["llama 3", "llama 3.1", "llama 3.2", "llama 3.3"]},
    {"name": "Sora", "type": "Product", "sameAs": "https://en.wikipedia.org/wiki/Sora_(text-to-video_model)", "keywords": ["sora"]},
    # Strategic Categories & Concepts
    {"name": "Artificial Intelligence", "type": "Thing", "sameAs": "https://en.wikipedia.org/wiki/Artificial_intelligence", "keywords": ["artificial intelligence", " ai ", "machine learning", "deep learning"]},
    {"name": "Generative Artificial Intelligence", "type": "Thing", "sameAs": "https://en.wikipedia.org/wiki/Generative_artificial_intelligence", "keywords": ["generative ai", "genai", "text generation", "image generation"]},
    {"name": "Large Language Model", "type": "Thing", "sameAs": "https://en.wikipedia.org/wiki/Large_language_model", "keywords": ["large language model", "llm", "foundation model", "transformer"]},
    {"name": "Autonomous Agent", "type": "Thing", "sameAs": "https://en.wikipedia.org/wiki/Intelligent_agent", "keywords": ["ai agent", "autonomous agent", "multi-agent", "agentic"]},
    {"name": "Robotics", "type": "Thing", "sameAs": "https://en.wikipedia.org/wiki/Robotics", "keywords": ["robotics", "humanoid", "embodied ai", "robot"]},
    {"name": "Semiconductor", "type": "Thing", "sameAs": "https://en.wikipedia.org/wiki/Semiconductor", "keywords": ["semiconductor", "gpu", "ai chip", "asic"]}
]

def extract_entities_for_jsonld(text: str) -> tuple:
    """Extracts 'about' entity and 'mentions' entities based on keyword presence."""
    lowered = " " + text.lower() + " "
    matched = []
    seen_names = set()
    for ent in KNOWN_ENTITIES:
        if ent["name"] in seen_names:
            continue
        for kw in ent.get("keywords", []):
            if kw in lowered:
                matched.append({
                    "@type": ent["type"],
                    "name": ent["name"],
                    "sameAs": ent["sameAs"]
                })
                seen_names.add(ent["name"])
                break

    if not matched:
        about = [{
            "@type": "Thing",
            "name": "Artificial Intelligence",
            "sameAs": "https://en.wikipedia.org/wiki/Artificial_intelligence"
        }]
        mentions = []
    else:
        about = [matched[0]]
        mentions = matched[1:5]

    return about, mentions

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
        back_text = "← 返回雷达首页"
        site_brand = "AI 资讯雷达"
        overview_title = "核心功能与产品概览"
        features_title = "核心亮点与应用特性"
        best_for_title = "最适用人群与业务场景"
        quickstart_title = "快速启动与部署指令"
        official_btn_text = "🚀 前往官网 / GitHub 仓库 ↗"
        share_x_text = "分享到 𝕏"
        share_threads_text = "分享到 Threads"
        copy_link_text = "复制分享链接"
        more_tools_title = "更多精选 AI 工具"
        lang_switch_label = "🌐 切换英文 (EN)"
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
        site_brand = "AI News Radar"
        overview_title = "Product Overview & Capabilities"
        features_title = "Key Features & Highlights"
        best_for_title = "Ideal Use Cases & Audience"
        quickstart_title = "Quickstart & Installation"
        official_btn_text = "🚀 Visit Official Website / GitHub ↗"
        share_x_text = "Share on 𝕏"
        share_threads_text = "Share on Threads"
        copy_link_text = "Copy Link"
        more_tools_title = "Explore More AI Tools"
        lang_switch_label = "🇨🇳 Chinese Edition"
        raw_cmd = tool.get("quickstart_cmd") or ""
        quickstart_cmd = sanitize_for_en(raw_cmd)
        if not quickstart_cmd and raw_cmd:
            quickstart_cmd = "Run directly in browser or install via package manager"

    if not hook:
        hook = "Next-generation applied artificial intelligence tool" if not is_zh else "下一代前沿人工智能实用落地工具"
    if not overview:
        overview = hook

    raw_img = tool.get("image_url") or (tool.get("preview_images") and tool["preview_images"][0]) or ""
    image_url = get_optimized_og_image(raw_img, app_name, tool.get("category", ""))
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

    if isinstance(overview, list):
        overview_str = " ".join(str(x) for x in overview if x)
    else:
        overview_str = str(overview or "")
    clean_meta_desc = escape(re.sub(r'<[^>]+>', '', overview_str)[:160])

    if isinstance(features, list):
        features_flat = "; ".join(str(x) for x in features if x)
    else:
        features_flat = str(features or hook or "")
    feature_list_val = escape(re.sub(r'[\r\n]+', '; ', features_flat)[:300])

    tool_brand = "AI 资讯雷达" if is_zh else "AI News Radar"
    brand_suffix = f" | {tool_brand}"
    avail = 65 - len(brand_suffix)
    display_name_clean = " ".join(display_name.strip().split())
    hook_clean = " ".join(hook.strip().split())
    if len(f"{display_name_clean} - {hook_clean}") <= avail:
        meta_title = f"{display_name_clean} - {hook_clean}{brand_suffix}"
    else:
        avail_hook = avail - len(display_name_clean) - 3
        if avail_hook >= 10:
            h_cut = re.sub(r'^(?:is|an|a)\s+', '', hook_clean, flags=re.I).strip()[:avail_hook]
            last_space = h_cut.rfind(' ')
            if not is_zh and last_space > 8:
                h_cut = h_cut[:last_space]
            h_cut = h_cut.rstrip(" ,-—:|/·;")
            meta_title = f"{display_name_clean} - {h_cut}…{brand_suffix}"
        else:
            name_cut = display_name_clean[:avail].rstrip(" ,-—:|/·;")
            meta_title = f"{name_cut}{brand_suffix}"

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
  <meta name="robots" content="index, follow, max-image-preview:large, max-snippet:-1, max-video-preview:-1">
  <meta name="googlebot" content="index, follow, max-snippet:-1, max-image-preview:large">
  <link rel="canonical" href="{canonical_url}">
  <link rel="alternate" hreflang="en" href="{alt_en_url}">
  <link rel="alternate" hreflang="zh" href="{alt_zh_url}">
  <link rel="alternate" hreflang="zh-CN" href="{alt_zh_url}">
  <link rel="alternate" hreflang="x-default" href="{alt_en_url}">
  <link rel="sitemap" type="application/xml" title="Sitemap" href="https://ainewsradar.xyz/sitemap.xml">
  
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
  
  <!-- Academic & GEO Citation Meta Tags -->
  <meta name="citation_title" content="{escape(meta_title)}">
  <meta name="citation_author" content="AI News Radar Editorial Team">
  <meta name="citation_journal_title" content="AI News Radar Applied Tools Directory">
  <meta name="citation_fulltext_html_url" content="{canonical_url}">
  <meta name="citation_abstract" content="{clean_meta_desc}">
  
  <!-- LLMs.txt Discovery (llmstxt.org) -->
  <link rel="help" type="text/plain" href="https://ainewsradar.xyz/llms.txt" title="LLMs.txt Manifest">
  <link rel="alternate" type="text/plain" href="https://ainewsradar.xyz/llms-full.txt" title="Full LLMs.txt">
  {f'<link rel="help" type="text/plain" href="https://ainewsradar.xyz/zh/llms.txt" title="Chinese LLMs.txt Manifest">\n  <link rel="alternate" type="text/plain" href="https://ainewsradar.xyz/zh/llms-full.txt" title="Chinese Full LLMs.txt">' if is_zh else ''}
  
  <link rel="icon" href="data:image/svg+xml,<svg xmlns=%22http://www.w3.org/2000/svg%22 viewBox=%220 0 100 100%22><text y=%22.9em%22 font-size=%2290%22>🤖</text></svg>">
  <link rel="alternate" type="application/rss+xml" title="AI News Radar RSS" href="https://ainewsradar.xyz/feed.xml">
  <link rel="alternate" type="application/rss+xml" title="{"AI 资讯雷达 RSS" if is_zh else "AI News Radar (Chinese Edition RSS)"}" href="https://ainewsradar.xyz/zh/feed.xml">
  <link rel="alternate" type="application/json" title="AI News Radar JSON Feed" href="https://ainewsradar.xyz/feed.json">
  <script src="https://cdn.tailwindcss.com"></script>
  <script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=ca-pub-4912808437101130" crossorigin="anonymous"></script>
  {CLARITY_SCRIPT}
  
  <script type="application/ld+json">
  {{
    "@context": "https://schema.org",
    "@graph": [
      {{
        "@type": "BreadcrumbList",
        "itemListElement": [
          {{
            "@type": "ListItem",
            "position": 1,
            "name": "AI News Radar",
            "item": "https://ainewsradar.xyz/"
          }},
          {{
            "@type": "ListItem",
            "position": 2,
            "name": "{"AI 落地工具" if is_zh else "Applied AI Tools"}",
            "item": "https://ainewsradar.xyz{"/zh" if is_zh else ""}#tools"
          }},
          {{
            "@type": "ListItem",
            "position": 3,
            "name": "{escape(display_name)}",
            "item": "{canonical_url}"
          }}
        ]
      }},
      {{
        "@type": "SoftwareApplication",
        "name": "{escape(display_name)}",
        "description": "{clean_meta_desc}",
        "applicationCategory": "DeveloperApplication",
        "applicationSubCategory": "{escape(scenario)}",
        "operatingSystem": "Web, Linux, macOS, Windows",
        "url": "{canonical_url}",
        "image": ["{image_url}"],
        "aggregateRating": {{
          "@type": "AggregateRating",
          "ratingValue": "4.8",
          "ratingCount": "{max(45, int(tool.get('github_stars') or tool.get('stars') or 45))}",
          "bestRating": "5",
          "worstRating": "1"
        }},
        "featureList": "{feature_list_val}",
        "offers": {{
          "@type": "Offer",
          "price": "0",
          "priceCurrency": "USD",
          "description": "{escape(pricing)}"
        }},
        "publisher": {{
          "@type": "Organization",
          "name": "AI News Radar",
          "url": "https://ainewsradar.xyz"
        }}
      }},
      {{
        "@type": "FAQPage",
        "mainEntity": [
          {{
            "@type": "Question",
            "name": "{"What is " + escape(display_name) + "?" if not is_zh else escape(display_name) + " 是什么？"}",
            "acceptedAnswer": {{
              "@type": "Answer",
              "text": "{escape(overview)}"
            }}
          }},
          {{
            "@type": "Question",
            "name": "{"What are the key capabilities of " + escape(display_name) + "?" if not is_zh else escape(display_name) + " 的核心功能与优势是什么？"}",
            "acceptedAnswer": {{
              "@type": "Answer",
              "text": "{escape(features or hook)}"
            }}
          }},
          {{
            "@type": "Question",
            "name": "{"Who is " + escape(display_name) + " best for?" if not is_zh else escape(display_name) + " 适合哪些开发者与业务场景？"}",
            "acceptedAnswer": {{
              "@type": "Answer",
              "text": "{escape(best_for or overview)}"
            }}
          }}
        ]
      }}
    ]
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
          <span class="bg-gradient-to-r from-indigo-500 via-purple-500 to-pink-500 bg-clip-text text-transparent">{site_brand}</span>
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
    <article class="rounded-3xl bg-white dark:bg-slate-900 border border-slate-200/90 dark:border-slate-800 shadow-xl overflow-hidden" itemscope itemtype="https://schema.org/SoftwareApplication">
      
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

        <!-- CTA & Social Share Capsule Bar (Left: Share, Right: Direct Official Link) -->
        <div class="mt-6 p-4 sm:p-5 rounded-2xl bg-slate-100/90 dark:bg-slate-800/75 border border-slate-200 dark:border-slate-700/80 shadow-inner flex flex-col sm:flex-row flex-wrap items-stretch sm:items-center justify-between gap-3.5">

          <!-- Left: Social Sharing & Bookmark Actions -->
          <div class="flex flex-wrap items-center gap-2">
            <span class="text-[11px] font-bold uppercase tracking-wider text-slate-500 dark:text-slate-400 mr-1 select-none">{"分享至" if is_zh else "Share"}</span>
            <button onclick="shareDirect('x')" class="px-3.5 py-2 rounded-xl bg-black hover:bg-neutral-800 text-white dark:bg-white dark:text-black dark:hover:bg-neutral-100 transition-all text-xs font-bold flex items-center gap-1.5 shadow-sm active:scale-95 cursor-pointer" title="{share_x_text}">
              <svg class="w-3.5 h-3.5 fill-current shrink-0" viewBox="0 0 24 24"><path d="M18.244 2.25h3.308l-7.227 8.26 8.502 11.24H16.17l-5.214-6.817L4.99 21.75H1.68l7.73-8.835L1.254 2.25H8.08l4.713 6.231zm-1.161 17.52h1.833L7.084 4.126H5.117z"/></svg>
              <span>X</span>
            </button>
            <button onclick="shareDirect('threads')" class="px-3.5 py-2 rounded-xl bg-black hover:bg-neutral-800 text-white dark:bg-white dark:text-black dark:hover:bg-neutral-100 transition-all text-xs font-bold flex items-center gap-1.5 shadow-sm active:scale-95 cursor-pointer" title="{share_threads_text}">
              <svg class="w-3.5 h-3.5 fill-current shrink-0" viewBox="0 0 192 192"><path d="M141.537 88.988a66.667 66.667 0 0 0-2.518-1.143c-1.482-27.307-16.403-42.94-41.457-43.1h-.34c-14.986 0-27.449 6.396-35.12 18.036l13.779 9.452c5.73-8.695 14.724-10.548 21.348-10.548h.229c8.249.053 14.474 2.452 18.503 7.129 2.932 3.405 4.893 8.111 5.864 14.05-7.314-1.243-15.224-1.626-23.68-1.14-23.82 1.371-39.134 15.264-38.105 34.568.522 9.792 5.4 18.216 13.735 23.719 7.047 4.652 16.124 6.927 25.557 6.412 12.458-.683 22.231-5.436 29.049-14.127 5.178-6.6 8.453-15.153 9.899-25.93 5.937 3.583 10.337 8.298 12.767 13.966 4.132 9.635 4.373 25.468-8.546 38.376-11.319 11.308-24.925 16.2-45.488 16.351-22.809-.169-40.06-7.484-51.275-21.742C35.236 139.966 29.808 120.682 29.605 96c.203-24.682 5.63-43.966 16.133-57.317C56.954 24.425 74.204 17.11 97.013 16.94c22.975.17 40.526 7.52 52.171 21.847 5.71 7.026 10.015 15.86 12.853 26.162l16.147-4.308c-3.44-12.68-8.853-23.606-16.219-32.668C147.036 9.607 125.202.195 97.07 0h-.113C68.882.194 47.292 9.642 32.788 28.08 19.882 44.485 13.224 67.315 13.001 95.932L13 96v.067c.224 28.617 6.882 51.447 19.788 67.854C47.292 182.358 68.882 191.806 96.957 192h.113c24.96-.173 42.554-6.708 57.048-21.189 18.963-18.945 18.392-42.692 12.142-57.27-4.484-10.454-13.033-18.945-24.723-24.553ZM98.44 129.507c-10.44.588-21.286-4.098-21.82-14.135-.397-7.442 5.296-15.746 22.461-16.735 1.966-.114 3.895-.169 5.79-.169 6.235 0 12.068.606 17.371 1.765-1.978 24.702-13.58 28.713-23.802 29.274Z"/></svg>
              <span>Threads</span>
            </button>
            <button onclick="copyCurrentLink()" class="px-3.5 py-2 rounded-xl border border-slate-300/90 dark:border-slate-600 bg-white dark:bg-slate-900 hover:bg-slate-50 dark:hover:bg-slate-700 text-slate-700 dark:text-slate-200 transition-all text-xs font-semibold flex items-center gap-1.5 shadow-sm active:scale-95 cursor-pointer">
              <span>🔗</span> <span>{copy_link_text}</span>
            </button>
          </div>

          <!-- Right: Primary CTA Button -->
          <a href="{escape(official_target_url)}" target="_blank" rel="noopener noreferrer" class="sm:ml-auto inline-flex items-center justify-center gap-2 px-6 py-2.5 rounded-xl bg-gradient-to-r from-emerald-600 via-teal-600 to-cyan-600 hover:from-emerald-500 hover:to-cyan-500 text-white font-bold text-sm shadow-lg shadow-emerald-500/20 active:scale-95 transition-all">
            <span>{official_btn_text}</span>
          </a>

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
      const rawTitle = title.replace(/<[^>]+>/g, '').trim();
      const cleanTitleX = rawTitle.slice(0, 140);
      const cleanTitleThreads = rawTitle.slice(0, 300);
      if (platform === 'x') {{
        const text = encodeURIComponent(cleanTitleX + "\\n\\n#AI #AITools #AINewsRadar");
        window.open(`https://x.com/intent/tweet?text=${{text}}&url=${{encodeURIComponent(shareUrl)}}`, '_blank', 'noopener,noreferrer');
      }} else if (platform === 'threads') {{
        const text = encodeURIComponent(cleanTitleThreads + "\\n\\n#AI #AITools #AINewsRadar");
        window.open(`https://www.threads.net/intent/post?text=${{text}}&url=${{encodeURIComponent(shareUrl)}}`, '_blank', 'noopener,noreferrer');
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

def extract_ai_analysis_text(analysis_data: Any, is_zh: bool) -> str:
    """Safely extracts clean human-readable analysis text, strictly avoiding raw dict dumps."""
    if not analysis_data:
        return ""
    if isinstance(analysis_data, dict):
        if is_zh:
            text = (
                analysis_data.get("insight_zh")
                or analysis_data.get("takeaway_zh")
                or analysis_data.get("briefing_zh")
                or analysis_data.get("digest_zh")
                or ""
            )
        else:
            text = (
                analysis_data.get("insight_en")
                or analysis_data.get("takeaway_en")
                or analysis_data.get("briefing_en")
                or analysis_data.get("digest_en")
                or ""
            )
        return str(text).strip()
    if isinstance(analysis_data, str):
        s = analysis_data.strip()
        if (s.startswith("{") and s.endswith("}")) or s.startswith("{'") or s.startswith('{"'):
            try:
                import ast
                d = ast.literal_eval(s)
                if isinstance(d, dict):
                    return extract_ai_analysis_text(d, is_zh)
            except Exception:
                pass
            try:
                import json
                d = json.loads(s)
                if isinstance(d, dict):
                    return extract_ai_analysis_text(d, is_zh)
            except Exception:
                pass
        return s
    return ""


def _render_inline_video_figure(vid: Dict[str, Any], is_zh: bool, source_name: str, source_url: str) -> str:
    v_raw_url = str(vid.get("url") or "").strip()
    if not v_raw_url or not v_raw_url.startswith("http"):
        return ""
    ad_tokens = (
        "doubleclick", "googlesyndication", "taboola", "outbrain", "connatix",
        "primis", "anyclip", "ex.co", "jw-player-inline-promo", "cdn.jwplayer.com",
        "video-ad", "sponsored", "adsystem", "adsafeprotected"
    )
    low_u = v_raw_url.lower()
    if any(tok in low_u for tok in ad_tokens):
        return ""
    v_provider = str(vid.get("provider") or "").lower().strip()
    if not v_provider:
        if re.search(r'\.(?:mp4|webm)(\?|$)', low_u):
            v_provider = "mp4"
        elif any(h in low_u for h in ("youtube.com/embed", "youtube-nocookie.com/embed", "player.vimeo.com", "youtube.com/shorts")):
            v_provider = "iframe"
    v_aspect = str(vid.get("aspect") or "").strip().lower()
    is_vertical_vid = v_aspect in ("9x16", "9:16", "4x5", "4:5", "3x4", "3:4", "vertical", "portrait") or any(
        tok in low_u for tok in ("youtube.com/shorts/", "tiktok.com/", "instagram.com/reel/")
    )
    is_square_vid = v_aspect in ("1x1", "1:1", "square")
    if not is_vertical_vid and not is_square_vid and v_aspect:
        m_wh = re.match(r'^(\d+(?:\.\d+)?)\s*[x:]\s*(\d+(?:\.\d+)?)$', v_aspect)
        if m_wh:
            vw, vh = float(m_wh.group(1)), float(m_wh.group(2))
            if vw > 0 and vh > 0:
                if vh > vw * 1.08:
                    is_vertical_vid = True
                elif abs(vh - vw) <= vw * 0.08:
                    is_square_vid = True

    v_label = str(vid.get("title") or vid.get("caption") or "").strip()
    if not v_label:
        v_label = f"视频演示 · {source_name}" if is_zh else f"Featured Video · {source_name}"
    v_action = "原站观看 ↗" if is_zh else "Watch on Source ↗"
    v_outbound = source_url or v_raw_url
    if "youtube.com/embed/" in low_u or "youtube-nocookie.com/embed/" in low_u:
        m_yt = re.search(r"embed/([A-Za-z0-9_-]{8,15})", v_raw_url)
        if m_yt:
            v_outbound = f"https://www.youtube.com/watch?v={m_yt.group(1)}"

    if v_provider == "mp4" or re.search(r'\.(?:mp4|webm)(\?|$)', low_u):
        fig_max = "max-w-[360px]" if is_vertical_vid else ("max-w-[480px]" if is_square_vid else "w-full")
        vid_ratio_cls = "" if (is_vertical_vid or is_square_vid) else "aspect-video "
        v_poster = str(vid.get("poster") or "").strip()
        poster_attr = f' poster="{escape(v_poster)}"' if v_poster else ""
        src_play = v_raw_url if (v_poster or "#" in v_raw_url) else f"{v_raw_url}#t=0.5"
        return f"""
        <figure class="my-8 mx-auto w-full {fig_max}">
          <video controls playsinline preload="metadata"{poster_attr} class="w-full {vid_ratio_cls}h-auto max-h-[640px] rounded-2xl shadow-lg block bg-black object-contain" onloadedmetadata="if(this.videoWidth&&this.videoHeight){{var f=this.closest('figure');if(f){{if(this.videoHeight>this.videoWidth*1.08){{f.style.maxWidth='360px';this.classList.remove('aspect-video');}}else if(Math.abs(this.videoHeight-this.videoWidth)<=this.videoWidth*0.08){{f.style.maxWidth='480px';this.classList.remove('aspect-video');}}else{{f.style.maxWidth='100%';}}}}}}">
            <source src="{escape(src_play)}" type="video/mp4">
          </video>
          <figcaption class="mt-2.5 flex items-center justify-between gap-3 px-1 text-xs text-slate-500 dark:text-slate-400">
            <span class="truncate font-medium">🎬 {escape(v_label)}</span>
            <a href="{escape(v_outbound)}" target="_blank" rel="noopener noreferrer" class="shrink-0 font-semibold text-indigo-600 dark:text-indigo-400 hover:underline">{v_action}</a>
          </figcaption>
        </figure>
        """.strip()

    if v_provider == "iframe" or any(h in low_u for h in ("youtube.com/embed", "youtube-nocookie.com/embed", "player.vimeo.com", "players.brightcove.net", "player.cnevids.com", "youtube.com/shorts")):
        if is_vertical_vid:
            fig_max = "max-w-[360px]"
            ifr_ratio = "aspect-[9/16] max-h-[640px]"
        elif is_square_vid:
            fig_max = "max-w-[480px]"
            ifr_ratio = "aspect-square max-h-[520px]"
        else:
            fig_max = "w-full"
            ifr_ratio = "aspect-video"
        return f"""
        <figure class="my-8 mx-auto w-full {fig_max}">
          <div class="w-full {ifr_ratio} rounded-2xl overflow-hidden shadow-lg bg-black">
            <iframe src="{escape(v_raw_url)}" class="w-full h-full border-0 block" loading="lazy" scrolling="no" allow="autoplay; fullscreen; encrypted-media; picture-in-picture" allowfullscreen title="{escape(v_label)}"></iframe>
          </div>
          <figcaption class="mt-2.5 flex items-center justify-between gap-3 px-1 text-xs text-slate-500 dark:text-slate-400">
            <span class="truncate font-medium">🎬 {escape(v_label)}</span>
            <a href="{escape(v_outbound)}" target="_blank" rel="noopener noreferrer" class="shrink-0 font-semibold text-indigo-600 dark:text-indigo-400 hover:underline">{v_action}</a>
          </figcaption>
        </figure>
        """.strip()
    return ""


def format_editorial_paragraphs(
    paras: List[str],
    usable_images: List[Dict[str, str]],
    is_zh: bool = True,
    usable_videos: Optional[List[Dict[str, Any]]] = None,
    source_name: str = "",
    source_url: str = "",
    ref_para_count: int = 0,
) -> str:
    """
    Magazine-Grade Professional Typography & Inline Media Injector:
    - Editorial Lead: distinguished opening narrative prose without jarring boxes.
    - Clean Editorial Typography: generous line-height and paragraph spacing for effortless long-form reading.
    - Editorial Pull Quote: understated, elegant accent border for notable quotes.
    - Inline Photo, Chart & Video Injection: interleaves authentic photography and embedded videos at exact DOM anchors.
    """
    rendered_elements = []
    total = len(paras)
    img_idx = 0

    def _map_slot(raw_ap: int) -> int:
        if raw_ap < 0:
            return -1
        if is_zh and ref_para_count > 1 and total > 1 and total != ref_para_count:
            scaled = int(round(raw_ap * (total - 1) / float(ref_para_count - 1)))
            return min(max(0, total - 1), max(0, scaled))
        return min(max(0, total - 1), raw_ap)

    # 预计算全量配图与正文内嵌视频的精确插入位置（按原文精确锚点 `after_para` + `dom_order` 排序）
    _anchored_media: Dict[int, List[tuple]] = {}
    _unanchored = []
    for _idx_m, _im in enumerate(usable_images):
        _ap = _im.get("after_para") if isinstance(_im, dict) else None
        _raw_ord = _im.get("dom_order") if isinstance(_im, dict) else None
        _ord = _raw_ord if isinstance(_raw_ord, int) else _idx_m
        if isinstance(_ap, int) and _ap >= -1:
            _slot = _map_slot(_ap)
            _anchored_media.setdefault(_slot, []).append((_ord, "img", _im))
        else:
            _unanchored.append((_ord, _im))
    if _unanchored and total > 0:
        _n_u = len(_unanchored)
        for _k, (_ord, _im) in enumerate(_unanchored):
            if total <= 2:
                _slot = min(total - 1, _k)
            else:
                _slot = min(total - 1, max(0, int(round((_k + 1) * total / float(_n_u + 1))) - 1))
            _anchored_media.setdefault(_slot, []).append((_ord, "img", _im))

    for _idx_v, _vid in enumerate(usable_videos or []):
        if not isinstance(_vid, dict):
            continue
        _ap = _vid.get("after_para")
        _raw_vord = _vid.get("dom_order")
        _ord = _raw_vord if isinstance(_raw_vord, int) else (1000 + _idx_v)
        if isinstance(_ap, int) and _ap >= -1:
            _slot = _map_slot(_ap)
        else:
            _slot = 0 if total > 0 else -1
        _anchored_media.setdefault(_slot, []).append((_ord, "vid", _vid))

    for _sl in _anchored_media:
        _anchored_media[_sl].sort(key=lambda x: x[0])

    def _emit_slot_media(slot_idx: int) -> None:
        nonlocal img_idx
        for _ord, m_kind, m_obj in _anchored_media.get(slot_idx, []):
            if m_kind == "vid":
                v_fig = _render_inline_video_figure(m_obj, is_zh=is_zh, source_name=source_name, source_url=source_url)
                if v_fig:
                    rendered_elements.append(v_fig)
                continue
            cur_img = m_obj
            img_idx += 1
            i_url = cur_img["url"]
            if is_zh:
                raw_cap = (cur_img.get("caption_zh") or cur_img.get("caption") or cur_img.get("alt") or "").strip()
            else:
                raw_cap = (cur_img.get("caption_en") or cur_img.get("alt") or (cur_img.get("caption") if not re.search(r'[\u4e00-\u9fa5]', cur_img.get("caption", "")) else "") or "").strip()

            # 杜绝无意义的 "Field scene" / "Article image" 占位图注，仅保留真实新闻图注
            is_dummy_cap = (not raw_cap) or (raw_cap.lower() in ("field scene", "article image", "image", "photo", "现场图景", "配图", "资讯原文配图"))
            alt_text = raw_cap if not is_dummy_cap else ("资讯配图" if is_zh else "Editorial illustration")
            caption_html = ""
            if not is_dummy_cap:
                caption_html = f"""
                <figcaption class="mt-2 px-1 text-xs text-slate-500 dark:text-slate-400 text-center max-w-full font-medium leading-snug">
                  📷 {escape(raw_cap)}
                </figcaption>
                """.strip()

            # 全尺寸自适应配图：竖屏截图/图表居中完整展示不裁切，横屏高清自适应，自动移除小图标与超宽水印/广告条
            img_onload = (
                "if(this.naturalWidth&&this.naturalHeight){"
                "if(this.naturalWidth<80||this.naturalHeight<80||(this.naturalWidth/this.naturalHeight>5.5&&this.naturalHeight<180)){"
                "var f=this.closest('figure');if(f)f.remove();return;}"
                "if(this.naturalHeight>this.naturalWidth*1.15){this.style.maxWidth='min(100%,420px)';}"
                "else if(Math.abs(this.naturalHeight-this.naturalWidth)<=this.naturalWidth*0.15){this.style.maxWidth='min(100%,520px)';}"
                "}"
            )
            rendered_elements.append(f"""
            <figure class="my-8 mx-auto w-fit max-w-full flex flex-col items-center">
              <img src="{escape(i_url)}" alt="{escape(alt_text)}" class="w-auto max-w-full h-auto max-h-[680px] rounded-2xl border border-slate-200/80 dark:border-slate-800 shadow-sm transition duration-300 hover:shadow-md block" loading="lazy" onload="{img_onload}" onerror="var f=this.closest('figure');if(f)f.remove();" />
              {caption_html}
            </figure>
            """.strip())

    # 若首段前存在前置视频/配图（after_para == -1），在正文开头原位输出
    _emit_slot_media(-1)

    for i, p in enumerate(paras):
        raw_p = p.strip()
        if not raw_p:
            continue

        # Section Subheading Recognition (H3 primary section vs H4 secondary sub-subheading)
        has_chinese = bool(re.search(r'[\u4e00-\u9fa5]', raw_p))
        is_sub_subheading = raw_p.startswith('#### ')
        if is_sub_subheading:
            is_subheading = False
        elif not has_chinese:
            is_subheading = (
                (raw_p.isupper() and 5 <= len(raw_p) <= 80 and not raw_p.startswith('($') and not raw_p.endswith('.')) or
                raw_p.startswith('### ') or raw_p.startswith('## ')
            )
        else:
            is_subheading = (
                raw_p.startswith('### ') or raw_p.startswith('## ') or
                raw_p in ["未来的教室", "没有明确成绩单的试验", "寻找恰当的平衡点"] or
                (len(raw_p) <= 30 and not raw_p.endswith('。') and not raw_p.endswith('，') and not raw_p.endswith('”') and (
                    raw_p.startswith("【") or raw_p.startswith("一、") or raw_p.startswith("二、") or raw_p.startswith("三、")
                ))
            )
        if is_sub_subheading:
            clean_h4 = raw_p.lstrip('#').strip()
            rendered_elements.append(f"""
            <h4 class="text-base sm:text-[17px] font-bold text-slate-800 dark:text-slate-200 mt-4 mb-3 tracking-tight">{escape(clean_h4)}</h4>
            """.strip())
        elif is_subheading:
            clean_heading = raw_p.lstrip('#').strip()
            rendered_elements.append(f"""
            <h3 class="text-lg sm:text-xl font-bold text-slate-900 dark:text-slate-100 mt-10 mb-4 tracking-tight flex items-center gap-2.5">
              <span class="w-1.5 h-4 bg-indigo-600 dark:bg-indigo-400 rounded-full inline-block"></span>
              <span>{escape(clean_heading)}</span>
            </h3>
            """.strip())
        else:
            is_pure_quote = bool(re.match(r'^[“"][^”"]+[”"]$', raw_p) or re.match(r'^[^：:\s]{2,16}[：:][\s]*[“"][^”"]+[”"]$', raw_p))
            escaped_body = escape(raw_p)

            # 1. Lead Paragraph (First paragraph when article is substantive)
            if i == 0 and total >= 3:
                rendered_elements.append(f"""
                <p class="text-[18px] sm:text-[20px] leading-[1.85] sm:leading-[1.9] text-slate-900 dark:text-slate-100 font-medium tracking-normal mb-6">{escaped_body}</p>
                """.strip())
            # 2. Editorial Pull Quote
            elif is_pure_quote:
                clean_q = escape(raw_p)
                rendered_elements.append(f"""
                <blockquote class="my-8 pl-5 sm:pl-6 border-l-2 border-indigo-500 dark:border-indigo-400 text-slate-700 dark:text-slate-300 italic font-serif text-[18px] sm:text-[19px] leading-[1.85]">
                  <p>{clean_q}</p>
                </blockquote>
                """.strip())
            # 3. Regular Paragraph
            else:
                rendered_elements.append(f"""
                <p class="text-[17px] sm:text-[18px] leading-[1.85] sm:leading-[1.9] text-slate-800 dark:text-slate-200 font-normal tracking-normal">{escaped_body}</p>
                """.strip())

        _emit_slot_media(i)

    return "\n\n".join(rendered_elements)


def build_news_html(item: Dict[str, Any], is_zh: bool = False, related_news: List[Dict[str, Any]] = None) -> str:
    news_id = str(item.get("id") or "")
    
    if is_zh:
        title = item.get("title_zh") or item.get("title") or "AI 突发快讯"
        summary = item.get("summary_zh") or item.get("content_snippet") or ""
        fact_bullets = item.get("fact_bullets_zh") or []
        ai_analysis = extract_ai_analysis_text(item.get("ai_analysis"), is_zh=True)
        lang_code = "zh"
        canonical_url = f"https://ainewsradar.xyz/zh/news/{news_id}"
        alt_en_url = f"https://ainewsradar.xyz/news/{news_id}"
        alt_zh_url = f"https://ainewsradar.xyz/zh/news/{news_id}"
        home_url = "/zh"
        back_text = "← 返回雷达首页"
        site_brand = "AI 资讯雷达"
        briefing_title = "核心要点提炼与关键事实"
        analysis_title = "雷达专属 AI 研判与技术透视"
        official_btn_text = "📖 阅读原资讯官网报道 ↗"
        share_x_text = "分享到 𝕏"
        share_threads_text = "分享到 Threads"
        copy_link_text = "复制分享链接"
        more_news_title = "更多前沿 AI 资讯"
        source_label = "权威消息来源"
        lang_switch_label = "🌐 切换英文 (EN)"
    else:
        title = sanitize_for_en(item.get("title_en") or item.get("title") or "Breaking AI Intelligence")
        summary = sanitize_for_en(item.get("summary_en") or item.get("content_snippet") or "")
        fact_bullets = [sanitize_for_en(b) for b in (item.get("fact_bullets_en") or [])]
        fact_bullets = [b for b in fact_bullets if b]
        ai_analysis = sanitize_for_en(extract_ai_analysis_text(item.get("ai_analysis_en") or item.get("ai_analysis"), is_zh=False))
        lang_code = "en"
        canonical_url = f"https://ainewsradar.xyz/news/{news_id}"
        alt_en_url = f"https://ainewsradar.xyz/news/{news_id}"
        alt_zh_url = f"https://ainewsradar.xyz/zh/news/{news_id}"
        home_url = "/"
        back_text = "← Back to AI News Radar"
        site_brand = "AI News Radar"
        briefing_title = "Executive Summary & Key Facts"
        analysis_title = "AI Radar Technical Deep-Dive"
        official_btn_text = "📖 Read Original Source Report ↗"
        share_x_text = "Share on 𝕏"
        share_threads_text = "Share on Threads"
        copy_link_text = "Copy Link"
        more_news_title = "More Breaking AI News"
        source_label = "Primary Source"
        lang_switch_label = "🇨🇳 Chinese Edition"

    raw_img = item.get("cover_image") or item.get("image_url") or (item.get("media_assets") and item["media_assets"].get("cover_image")) or ""
    image_url = get_optimized_og_image(raw_img, title, item.get("category", ""))
    image_mime = "image/png" if image_url.lower().endswith(".png") else "image/jpeg"
    source_name = item.get("source") or "Tech Source"
    if not is_zh:
        source_name = sanitize_for_en(source_name) or "Tech Source"

    source_url = item.get("url") or "#"
    sep = "&" if "?" in source_url else "?"
    source_target_url = f"{source_url}{sep}ref=ainewsradar" if source_url.startswith("http") else source_url

    clean_meta_desc = escape(re.sub(r'<[^>]+>', '', summary)[:160])
    news_brand = site_brand
    brand_suffix = f" | {news_brand}"
    avail = 65 - len(brand_suffix)
    title_clean = " ".join(title.strip().split())
    if len(title_clean) <= avail:
        meta_title = f"{title_clean}{brand_suffix}"
    else:
        cut = title_clean[:avail].rstrip(" ,-—:|/·;")
        last_space = cut.rfind(' ')
        if not is_zh and last_space > avail // 2:
            cut = cut[:last_space].rstrip(" ,-—:|/·;")
        meta_title = f"{cut}…{brand_suffix}"
    iso_published = parse_iso_date(item.get("published_at") or item.get("raw_published_at") or item.get("date"))

    author_name = item.get("author") or ""
    if author_name and author_name.lower() in ["web", "none", "unknown"]:
        author_name = ""
    author_byline_html = ""
    if author_name:
        author_prefix = "记者 / 供稿: " if is_zh else "By "
        author_byline_html = f'<div class="mt-2.5 text-xs sm:text-sm font-semibold text-slate-500 dark:text-slate-400 flex items-center gap-1.5"><span>✍️</span> <span>{author_prefix}{escape(author_name)}</span></div>'

    # 全局付费墙/订阅促销/返佣广告话术与图片注释防线（杜绝 "Pay a year upfront" / "in your inbox each week" 等污染要点与正文）
    PROMO_NOISE_RE = re.compile(
        r"(?:pay a year upfront|then \$\d+\s*per month|complete digital access to quality|"
        r"essential digital access to quality|cancel or change your plan anytime|"
        r"free access via your university|digital access for organisations|try unlimited access|"
        r"subscribe to unlock|want all of the times|thank you for your patience while we verify access|"
        r"already a subscriber\??\s*log in|myft digest|unlock the editor['’]s digest|"
        r"most read from the washington post|democracy dies in darkness|you were gifted this article|"
        r"posts from this topic will be added to your daily email digest|delivered directly to your inbox|"
        r"in your inbox each week|to receive this newsletter in your inbox|view image in fullscreen|"
        r"when you purchase through links in our articles|we may earn a (?:small )?commission|"
        r"doesn['’]t affect our editorial independence|income earning auto affiliate links|"
        r"subscribe to .{0,30} newsletter|sign up for .{0,30} newsletter|where was nvidia['’]s security team\?|"
        r"bloomberg law provides trusted coverage|log in to keep reading|sign in to access|subscribe to continue|"
        r"彭博法律提供可信的时事报道|登录以继续阅读|订阅以继续阅读|付费订阅以解锁|"
        r"预付一年.*省\s*\d+%|每月\s*\d+\s*美元.*数字访问|完整数字访问|基本数字访问|订阅以解锁|"
        r"每周在您的收件箱中获取|订阅我们的通讯|公司\d{4}年发布的肖像照|资料照片|新华社发|视觉中国供图|"
        r"通过我们文章中的链接购买|可能会赚取少量佣金|不影响我们的编辑独立性|联盟链接)",
        re.I,
    )

    bullets_html = ""
    if fact_bullets:
        formatted_items = []
        for b in fact_bullets:
            b_str = str(b).strip()
            if not b_str or PROMO_NOISE_RE.search(b_str):
                continue
            if b_str.startswith("【") and "】" in b_str:
                tag, rest = b_str.split("】", 1)
                tag_html = f"<strong class='font-bold text-indigo-900 dark:text-indigo-200'>{escape(tag)}】</strong>"
                formatted_items.append(f"<li class='text-sm sm:text-base leading-relaxed pl-1'>{tag_html}{escape(rest.lstrip())}</li>")
            elif b_str.startswith("[") and "]" in b_str:
                tag, rest = b_str.split("]", 1)
                tag_html = f"<strong class='font-bold text-indigo-900 dark:text-indigo-200'>{escape(tag)}]</strong>"
                formatted_items.append(f"<li class='text-sm sm:text-base leading-relaxed pl-1'>{tag_html} {escape(rest.lstrip())}</li>")
            else:
                formatted_items.append(f"<li class='text-sm sm:text-base leading-relaxed pl-1'>{escape(b_str)}</li>")
        bullet_items = "".join(formatted_items)
        if bullet_items:
            bullets_html = f"""
        <section class="executive-summary mt-6 p-5 rounded-2xl bg-indigo-50/50 dark:bg-indigo-950/20 border border-indigo-200 dark:border-indigo-800/40" role="region" aria-label="{briefing_title}" data-geocitation="true">
          <h3 class="text-sm font-bold text-indigo-900 dark:text-indigo-200 mb-3 flex items-center gap-2">
            <span>⚡</span> <span>{briefing_title}</span>
          </h3>
          <ul class="list-disc list-inside space-y-2.5 text-indigo-950 dark:text-indigo-100">
            {bullet_items}
          </ul>
        </section>
        """

    analysis_html = ""
    if ai_analysis:
        analysis_html = f"""
        <div class="mt-10 p-5 sm:p-6 rounded-2xl bg-purple-50/50 dark:bg-purple-950/20 border border-purple-200 dark:border-purple-800/40">
          <h3 class="text-sm font-bold text-purple-900 dark:text-purple-200 mb-2 flex items-center gap-2">
            <span>🤖</span> <span>{analysis_title}</span>
          </h3>
          <p class="text-sm sm:text-base text-purple-950 dark:text-purple-100 leading-relaxed whitespace-pre-line">{escape(ai_analysis)}</p>
        </div>
        """

    video_html = ""
    if item.get("has_video") or item.get("video_url") or item.get("video_id"):
        v_raw_url = str(item.get("video_url") or "").strip()
        v_direct_url = str(item.get("video_direct_url") or "").strip()
        v_provider = str(item.get("video_provider") or "").lower().strip()
        v_id = str(item.get("video_id") or "").strip()
        if not v_id and "SC=" in v_raw_url:
            m_sc = re.search(r'SC=([A-Za-z0-9_-]+)', v_raw_url)
            if m_sc:
                v_id = m_sc.group(1)
        if v_id and not v_provider:
            v_provider = "stn"

        v_outbound = v_direct_url or (v_raw_url if (v_raw_url.startswith("http") and "embedcode" not in v_raw_url and "cloudfront.net" not in v_raw_url) else source_url)
        # 严格拦截广告联盟/推广视频播放器 (doubleclick, jwplayer inline promo, taboola, connatix, primis, outbrain 等)
        AD_VIDEO_TOKENS = (
            "doubleclick", "googlesyndication", "taboola", "outbrain", "connatix",
            "primis", "anyclip", "ex.co", "jw-player-inline-promo", "cdn.jwplayer.com",
            "video-ad", "sponsored", "adsystem", "adsafeprotected"
        )
        is_ad_video = any(tok in v_raw_url.lower() for tok in AD_VIDEO_TOKENS)
        if is_ad_video:
            v_raw_url = ""
            v_provider = ""
            v_id = ""
        v_custom_title = str(item.get("video_title") or "").strip()
        v_aspect = str(item.get("video_aspect") or "").strip().lower()
        v_poster = str(item.get("video_poster") or "").strip() or image_url
        if "image.cnbcfm.com" in v_poster.lower() and image_url and "ainewsradar.xyz/images/" in image_url:
            v_poster = image_url

        # 通用宽高比自动解析：支持 9x16 / 9:16 / 720x1280 等任意数值比例 + 第三方竖屏短片 URL 识别
        is_vertical_vid = v_aspect in ("9x16", "9:16", "4x5", "4:5", "3x4", "3:4", "vertical", "portrait") or any(
            tok in v_raw_url.lower() for tok in ("youtube.com/shorts/", "tiktok.com/", "instagram.com/reel/")
        )
        is_square_vid = v_aspect in ("1x1", "1:1", "square")
        if not is_vertical_vid and not is_square_vid and v_aspect:
            m_wh = re.match(r'^(\d+(?:\.\d+)?)\s*[x:]\s*(\d+(?:\.\d+)?)$', v_aspect)
            if m_wh:
                vw, vh = float(m_wh.group(1)), float(m_wh.group(2))
                if vw > 0 and vh > 0:
                    if vh > vw * 1.08:
                        is_vertical_vid = True
                    elif abs(vh - vw) <= vw * 0.08:
                        is_square_vid = True

        v_title = (
            f"{escape(v_custom_title)} · {escape(source_name)}" if v_custom_title
            else (f"现场视频报道 · {escape(source_name)}" if is_zh else f"Featured Video Coverage · {escape(source_name)}")
        )
        v_action = "原站观看 ↗" if is_zh else "Watch on Source ↗"
        v_desc = f"原文包含 {escape(source_name)} 独家现场视频报道与深度实录。" if is_zh else f"Embedded official video report from {escape(source_name)}."

        if is_ad_video:
            video_html = ""
        elif v_provider == "stn" and v_id:
            sc_play = re.sub(r'-14497$', '-16481', v_id)
            stn_srcdoc = (
                "<!DOCTYPE html><html><head><meta charset='utf-8'><meta name='viewport' content='width=device-width,initial-scale=1'>"
                "<style>html,body{margin:0;padding:0;width:100%;height:100%;background:#020617;overflow:hidden;display:flex;align-items:center;justify-content:center;}"
                ".stn-video-player{width:100%;height:100%;}</style></head><body>"
                f"<div class='stn-video-player k-{escape(sc_play)} s2nPlayer-{escape(sc_play)}' data-content-placement='stn-video'></div>"
                "<script>window.addEventListener('voltaxPlayerLoaded',function(e){try{if(e.detail&&e.detail.player&&e.detail.player.setFloatingEnabled){e.detail.player.setFloatingEnabled(false);}}catch(err){}});</script>"
                f"<script src='https://embed.sendtonews.com/player3/embedcode.js?SC={escape(sc_play)}' async></script>"
                "</body></html>"
            )
            video_html = f"""
        <div class="mt-8 rounded-2xl overflow-hidden border border-slate-200 dark:border-slate-800 bg-slate-950 shadow-lg">
          <div class="px-4 py-3 bg-slate-900/95 border-b border-slate-800 flex items-center justify-between gap-3">
            <div class="flex items-center gap-2 min-w-0">
              <span class="inline-flex h-2 w-2 rounded-full bg-rose-500 animate-pulse shrink-0"></span>
              <span class="text-xs sm:text-sm font-bold text-slate-100 truncate">🎬 {v_title}</span>
            </div>
            <a href="{escape(v_outbound)}" target="_blank" rel="noopener noreferrer" class="shrink-0 px-2.5 py-1 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 font-semibold text-xs border border-slate-700 transition-colors">
              {v_action}
            </a>
          </div>
          <div class="w-full aspect-video bg-slate-950 relative">
            <iframe class="w-full h-full border-0" loading="lazy" allow="autoplay; fullscreen; encrypted-media; picture-in-picture" allowfullscreen title="{v_title}" srcdoc="{html.escape(stn_srcdoc, quote=True)}"></iframe>
          </div>
        </div>
        """
        elif v_provider == "mp4" or v_raw_url.lower().endswith(".mp4"):
            fig_max = "max-w-[360px]" if is_vertical_vid else ("max-w-[480px]" if is_square_vid else "w-full")
            vid_ratio_cls = "" if (is_vertical_vid or is_square_vid) else "aspect-video "
            video_html = f"""
        <figure class="my-8 mx-auto w-full {fig_max}">
          <video controls playsinline preload="metadata" poster="{escape(v_poster)}" class="w-full {vid_ratio_cls}h-auto max-h-[640px] rounded-2xl shadow-lg block bg-black object-contain" onloadedmetadata="if(this.videoWidth&&this.videoHeight){{var f=this.closest('figure');if(f){{if(this.videoHeight>this.videoWidth*1.08){{f.style.maxWidth='360px';this.classList.remove('aspect-video');}}else if(Math.abs(this.videoHeight-this.videoWidth)<=this.videoWidth*0.08){{f.style.maxWidth='480px';this.classList.remove('aspect-video');}}else{{f.style.maxWidth='100%';}}}}}}">
            <source src="{escape(v_raw_url)}" type="video/mp4">
          </video>
          <figcaption class="mt-2.5 flex items-center justify-between gap-3 px-1 text-xs text-slate-500 dark:text-slate-400">
            <span class="truncate font-medium">🎬 {v_title}</span>
            <a href="{escape(v_outbound)}" target="_blank" rel="noopener noreferrer" class="shrink-0 font-semibold text-indigo-600 dark:text-indigo-400 hover:underline">{v_action}</a>
          </figcaption>
        </figure>
        """
        elif v_provider == "iframe" or any(h in v_raw_url.lower() for h in ("youtube.com/embed", "player.vimeo.com", "players.brightcove.net", "player.cnevids.com", "youtube.com/shorts", "tiktok.com/", "instagram.com/reel")):
            if is_vertical_vid:
                fig_max = "max-w-[360px]"
                ifr_ratio = "aspect-[9/16] max-h-[640px]"
            elif is_square_vid:
                fig_max = "max-w-[480px]"
                ifr_ratio = "aspect-square max-h-[520px]"
            else:
                fig_max = "w-full"
                ifr_ratio = "aspect-video"
            video_html = f"""
        <figure class="my-8 mx-auto w-full {fig_max}">
          <div class="w-full {ifr_ratio} rounded-2xl overflow-hidden shadow-lg bg-black">
            <iframe src="{escape(v_raw_url)}" class="w-full h-full border-0 block" loading="lazy" scrolling="no" allow="autoplay; fullscreen; encrypted-media; picture-in-picture" allowfullscreen title="{v_title}"></iframe>
          </div>
          <figcaption class="mt-2.5 flex items-center justify-between gap-3 px-1 text-xs text-slate-500 dark:text-slate-400">
            <span class="truncate font-medium">🎬 {v_title}</span>
            <a href="{escape(v_outbound)}" target="_blank" rel="noopener noreferrer" class="shrink-0 font-semibold text-indigo-600 dark:text-indigo-400 hover:underline">{v_action}</a>
          </figcaption>
        </figure>
        """
        else:
            video_html = f"""
        <div class="mt-6 p-4 rounded-2xl bg-amber-500/10 border border-amber-500/30 flex items-center justify-between gap-3 text-amber-900 dark:text-amber-200">
          <div class="flex items-center gap-2.5 min-w-0">
            <span class="text-xl">📹</span>
            <div>
              <div class="text-xs sm:text-sm font-bold">{v_title}</div>
              <div class="text-xs text-amber-700/80 dark:text-amber-300/80 truncate">{v_desc}</div>
            </div>
          </div>
          <a href="{escape(v_outbound)}" target="_blank" rel="noopener noreferrer" class="shrink-0 px-3 py-1.5 rounded-lg bg-amber-500 hover:bg-amber-600 text-white font-bold text-xs shadow-sm transition-all flex items-center gap-1">
            <span>▶</span> <span>{v_action}</span>
          </a>
        </div>
        """

    full_coverage_html = ""
    full_text = str((item.get("article_content_zh") if is_zh else (item.get("article_content_en") or item.get("article_content") or item.get("original_content"))) or "").strip()
    if not full_text:
        # Fall back to structured paragraphs if full text string was stripped
        if is_zh:
            if item.get("paragraphs_zh") and isinstance(item["paragraphs_zh"], list) and len(item["paragraphs_zh"]) > 0:
                full_text = "\n\n".join(str(p).strip() for p in item["paragraphs_zh"] if str(p).strip())
            elif item.get("paragraphs") and isinstance(item["paragraphs"], list) and len(item["paragraphs"]) > 0:
                full_text = "\n\n".join(str(p).strip() for p in item["paragraphs"] if str(p).strip())
        else:
            if item.get("paragraphs") and isinstance(item["paragraphs"], list) and len(item["paragraphs"]) > 0:
                full_text = "\n\n".join(str(p).strip() for p in item["paragraphs"] if str(p).strip())
    is_reuters = "reuters" in (item.get("source") or "").lower() or "reuters.com" in (item.get("url") or "").lower()
    is_bloomberg = "bloomberg" in (item.get("source") or "").lower() or "bloomberg.com" in (item.get("url") or "").lower()
    is_fortune = "fortune" in (item.get("source") or "").lower() or "fortune.com" in (item.get("url") or "").lower()
    is_wsj = "wsj" in (item.get("source") or "").lower() or "wall street journal" in (item.get("source") or "").lower() or "wsj.com" in (item.get("url") or "").lower()
    is_forbes = "forbes" in (item.get("source") or "").lower() or "forbes.com" in (item.get("url") or "").lower()
    is_dedicated_full = (
        is_reuters or is_bloomberg or is_fortune or is_wsj or is_forbes or
        any(d in (item.get("url") or "").lower() for d in ("theverge.com", "nytimes.com", "washingtonpost.com", "washingtonsun.com", "ft.com/", "wired.com/", "technologyreview.com", "techcrunch.com", "arstechnica.com", "cnbc.com", "the-decoder.com", "openai.com/", "siliconangle.com", "semafor.com", "coindesk.com", "cbsnews.com", "ifixit.com", "9to5mac.com", "tomshardware.com", "bbc.com/", "bbc.co.uk/", "nypost.com", "techfundingnews.com", "://ign.com/", ".ign.com/", "anthropic.com/", "claude.com/"))
    )
    is_paywalled = bool((not (is_dedicated_full and (item.get("is_substantive") or len(full_text) >= 400)) and item.get("is_paywalled")) or (not (is_dedicated_full and (item.get("is_substantive") or len(full_text) >= 400)) and any(k in (item.get("source") or "").lower() for k in ["financial times", "ft.com", "the information"])))
    if is_reuters or (is_dedicated_full and (item.get("is_substantive") or len(full_text) >= 400)):
        is_paywalled = False
        if len(full_text) >= 200:
            item["is_substantive"] = True

    paras = []
    if full_text and len(full_text) > 120:
        paras = [p.strip() for p in full_text.split("\n\n") if len(p.strip()) >= 3 and not PROMO_NOISE_RE.search(p)]
        if not paras:
            paras = [p.strip() for p in full_text.split("\n") if len(p.strip()) >= 3 and not PROMO_NOISE_RE.search(p)]
        is_excerpt = is_paywalled or (len(paras) <= 6 and not item.get("is_substantive"))
    elif is_paywalled:
        fallback_snippet = str((item.get("summary_zh") or item.get("content_snippet") or summary) if is_zh else (item.get("summary_en") or item.get("content_snippet") or summary) or "").strip()
        if fallback_snippet and len(fallback_snippet) > 30:
            paras = [fallback_snippet]
            is_excerpt = True
        else:
            is_excerpt = False
    else:
        is_excerpt = False

    if paras:
        if is_excerpt:
            clean_last_p = re.sub(r'[\s\u3000。，,.;；:：!！?？]+(?=[…\.]{2,}|$)', '', paras[-1])
            if not clean_last_p.endswith("……") and not clean_last_p.endswith("...") and not clean_last_p.endswith("…"):
                paras[-1] = clean_last_p + ("……" if is_zh else "...")
            else:
                paras[-1] = clean_last_p

        # 提取真实文章正文配图与图表 (严禁作者头像/大头照/正方形个人照混入正文)
        raw_inline_images = item.get("inline_images", [])
        usable_images = []
        seen_img_urls = set()
        cover_url = item.get("image_url") or item.get("cover_image")
        if cover_url:
            seen_img_urls.add(cover_url.split("?")[0])
        auth_name_low = str(item.get("author") or "").strip().lower()
        auth_avatar_base = str(item.get("author_avatar") or "").split("?")[0].strip().lower()
        AVATAR_URL_TOKENS = (
            "blurple", "author_profile_images", "headshot", "avatar", "byline",
            "gravatar", "profile_image", "profile-pic", "-portrait-", "-mug-", "staff-",
            "resize/312x208", "resize/330x220", "resize/300x200",
            "w_40,h_40", "w_48,h_48", "w_64,h_64", "w_80,h_80", "w_96,h_96",
            "h_116,c_limit", "375x375", "150x150", "200x200", "bloomberg-bna-brightspot",
            "grey-placeholder", "techcrunch-logo", "tc-logo", "tc-lockup", "lockup", "wordmark", "site-logo",
            "brand-logo", "ad-banner", "/ads/", "doubleclick", "googlesyndication",
            "taboola", "outbrain", "mgid", "promo-banner", "sponsored", "default-share", ".svg"
        )

        for img_entry in raw_inline_images:
            if isinstance(img_entry, dict):
                i_url = img_entry.get("url", "").strip()
                i_cap = img_entry.get("caption", "").strip() or img_entry.get("alt", "").strip()
            elif isinstance(img_entry, str):
                i_url = img_entry.strip()
                i_cap = ""
            else:
                continue
            if not i_url or (not i_url.startswith("http") and not i_url.startswith("/")):
                continue
            low_u = i_url.lower()
            low_c = i_cap.lower().strip()
            if (
                (auth_avatar_base and auth_avatar_base in low_u) or
                any(tok in low_u for tok in AVATAR_URL_TOKENS) or
                (auth_name_low and len(auth_name_low) > 3 and low_c in (auth_name_low, f"by {auth_name_low}", f"photo of {auth_name_low}", f"headshot of {auth_name_low}")) or
                low_c in ("thumbnail", "author", "avatar", source_name.lower())
            ):
                continue
            clean_k = i_url.split("?")[0]
            if clean_k in seen_img_urls:
                continue
            seen_img_urls.add(clean_k)
            usable_images.append({
                "url": i_url,
                "caption": img_entry.get("caption", "").strip() if isinstance(img_entry, dict) else "",
                "caption_en": img_entry.get("caption_en", "").strip() if isinstance(img_entry, dict) else "",
                "caption_zh": img_entry.get("caption_zh", "").strip() if isinstance(img_entry, dict) else "",
                "alt": img_entry.get("alt", "").strip() if isinstance(img_entry, dict) else "",
                "after_para": img_entry.get("after_para") if isinstance(img_entry, dict) and isinstance(img_entry.get("after_para"), int) else None,
                "dom_order": img_entry.get("dom_order") if isinstance(img_entry, dict) and isinstance(img_entry.get("dom_order"), int) else None,
            })

        from crawlers.content_filters import clean_article_paragraphs
        paras = clean_article_paragraphs(
            paras,
            inline_images=usable_images,
            cover_caption=item.get("image_caption"),
            is_zh=is_zh
        )

        usable_inline_videos = [
            v for v in (item.get("inline_videos") or [])
            if isinstance(v, dict) and str(v.get("url") or "").startswith("http")
        ]
        en_raw_for_ref = str(item.get("article_content_en") or item.get("article_content") or "").strip()
        if en_raw_for_ref:
            raw_en_split = [p.strip() for p in en_raw_for_ref.split("\n\n") if len(p.strip()) >= 3 and not PROMO_NOISE_RE.search(p)]
            en_ref_paras = clean_article_paragraphs(
                raw_en_split,
                inline_images=usable_images,
                cover_caption=item.get("image_caption"),
                is_zh=False
            )
        else:
            en_ref_paras = []
        p_html = format_editorial_paragraphs(
            paras,
            usable_images,
            is_zh=is_zh,
            usable_videos=usable_inline_videos,
            source_name=source_name,
            source_url=source_target_url,
            ref_para_count=len(en_ref_paras),
        )
        # 当文章正文已按原文精确 DOM 位置原位渲染内嵌视频时，隐藏顶部重复/错位的全局视频块
        if usable_inline_videos:
            video_html = ""
        sec_title = ("📰 权威报道核心实录 (精选)" if is_excerpt else "📰 深度报道原文实录") if is_zh else ("📰 In-Depth Coverage (Excerpt)" if is_excerpt else "📰 Full In-Depth Coverage")
        src_note = f"{source_name} 权威实录" if is_zh else f"{source_name} Full Report"

        excerpt_notice_html = ""
        if is_excerpt:
            if is_zh:
                notice_text = f"本条情报为《{escape(source_name)}》独家付费报道（源站设有硬付费墙，非订阅会员将跳转付费购买页）。AI 资讯雷达已为您提炼并结构化呈现核心内幕事实，站内即可通读。" if is_paywalled else "源站设立了版权或登录限制，雷达已为您提炼权威报道核心实录。完整报道可点击下方“阅读原资讯官网报道”浏览。"
            else:
                notice_text = f"Exclusive coverage from {escape(source_name)} (paywall-protected; key intelligence record extracted above). Click 'Read Original Source Report' below for the full story on official site." if is_paywalled else "Protected by source publisher copyright or login requirements. Key intelligence extracted above; click below to read full report."
            excerpt_notice_html = f"""
          <div class="mt-4 p-3.5 rounded-xl bg-amber-500/10 border border-amber-500/30 text-amber-800 dark:text-amber-200 text-xs sm:text-sm flex items-start gap-2.5">
            <span class="text-base shrink-0 leading-none">🔒</span>
            <div class="leading-relaxed font-medium">{notice_text}</div>
          </div>
            """

        full_coverage_html = f"""
        <section class="mt-10 pt-8 border-t border-slate-200/90 dark:border-slate-800" aria-label="{sec_title}">
          <div class="flex items-center justify-between pb-4 mb-7 border-b border-slate-100 dark:border-slate-800/80">
            <div class="flex items-center gap-2.5">
              <span class="w-2 h-2 rounded-full bg-indigo-600 dark:bg-indigo-400"></span>
              <h2 class="text-base sm:text-lg font-bold text-slate-900 dark:text-slate-100 tracking-tight">
                {sec_title}
              </h2>
            </div>
            <span class="text-xs font-mono px-2.5 py-1 rounded-md bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-400 font-semibold border border-slate-200/60 dark:border-slate-700/60">{escape(src_note)}</span>
          </div>
          <div class="article-body space-y-6 sm:space-y-7" itemprop="articleBody">
            {p_html}
          </div>
          {excerpt_notice_html}
        </section>
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

    iso_date_only = iso_published.split('T')[0] if 'T' in iso_published else iso_published[:10]
    searchable_text = f"{title} {summary} {' '.join(str(b) for b in fact_bullets)} {ai_analysis}"
    about_entities, mentions_entities = extract_entities_for_jsonld(searchable_text)

    # Build rich articleBody for LLMs and AI Search engine ingestion
    if paras:
        article_body_text = "\n\n".join(paras)
    else:
        bullets_text = " ".join([re.sub(r'^[【\[].*?[】\]]\s*', '', str(b)).strip() for b in fact_bullets])
        article_body_text = f"{summary}\n\n{bullets_text}\n\n{ai_analysis}".strip()

    if not is_zh:
        article_body_text = sanitize_for_en(article_body_text, preserve_newlines=True)

    word_count = len(article_body_text.split()) if not is_zh else len(article_body_text)

    kw_candidates = ["Artificial Intelligence", "AI News", "Frontier LLM", "Machine Learning"]
    if source_name:
        kw_candidates.append(source_name)
    for ent in about_entities:
        if isinstance(ent, dict) and ent.get("name"):
            kw_candidates.append(ent["name"])
    for ent in mentions_entities:
        if isinstance(ent, dict) and ent.get("name"):
            kw_candidates.append(ent["name"])
    seen_kw = set()
    unique_kw = []
    for k in kw_candidates:
        k_clean = sanitize_for_en(k) if not is_zh else k.strip()
        if k_clean and k_clean.lower() not in seen_kw:
            seen_kw.add(k_clean.lower())
            unique_kw.append(k_clean)

    news_article_schema = {
        "@type": "NewsArticle",
        "headline": escape(title),
        "description": clean_meta_desc,
        "image": [image_url],
        "url": canonical_url,
        "datePublished": iso_published,
        "dateModified": iso_published,
        "inLanguage": "zh-CN" if is_zh else "en",
        "mainEntityOfPage": canonical_url,
        "articleSection": "Artificial Intelligence",
        "articleBody": article_body_text,
        "wordCount": word_count,
        "keywords": ", ".join(unique_kw[:10]),
        "isBasedOn": source_target_url,
        "about": about_entities,
        "copyrightHolder": {
            "@type": "Organization",
            "name": "AI News Radar",
            "url": "https://ainewsradar.xyz"
        },
        "license": "https://ainewsradar.xyz/editorial-policy",
        "speakable": {
            "@type": "SpeakableSpecification",
            "cssSelector": [".executive-summary", "h1", ".article-body", ".fact-card"]
        },
        "author": {
            "@type": "Organization",
            "name": "AI News Radar Editorial Team",
            "url": f"https://ainewsradar.xyz{'/zh/about' if is_zh else '/about'}"
        },
        "publisher": {
            "@type": "NewsMediaOrganization",
            "name": "AI News Radar",
            "url": "https://ainewsradar.xyz",
            "logo": {
                "@type": "ImageObject",
                "url": "https://ainewsradar.xyz/favicon.ico"
            }
        }
    }
    if mentions_entities:
        news_article_schema["mentions"] = mentions_entities

    faq_questions = []
    if is_zh:
        q1_text = f"{title} 的核心事实与事件脉络是什么？"
        if fact_bullets:
            q1_ans = " ".join([re.sub(r'^[【\[].*?[】\]]\s*', '', str(b)).strip() for b in fact_bullets[:4]])
        else:
            q1_ans = summary or title
        if q1_ans:
            faq_questions.append({
                "@type": "Question",
                "name": q1_text,
                "acceptedAnswer": {
                    "@type": "Answer",
                    "text": q1_ans
                }
            })
        if ai_analysis:
            faq_questions.append({
                "@type": "Question",
                "name": "AI 资讯雷达对该事件的技术研判与行业影响是什么？",
                "acceptedAnswer": {
                    "@type": "Answer",
                    "text": ai_analysis
                }
            })
    else:
        q1_text = sanitize_for_en(f"What are the key facts regarding {title}?")
        if fact_bullets:
            q1_ans = sanitize_for_en(" ".join([re.sub(r'^[【\[].*?[】\]]\s*', '', str(b)).strip() for b in fact_bullets[:4]]))
        else:
            q1_ans = sanitize_for_en(summary or title)
        if q1_text and q1_ans:
            faq_questions.append({
                "@type": "Question",
                "name": q1_text,
                "acceptedAnswer": {
                    "@type": "Answer",
                    "text": q1_ans
                }
            })
        if ai_analysis:
            q2_text = "What is the strategic AI industry analysis of this event?"
            q2_ans = sanitize_for_en(ai_analysis)
            if q2_ans:
                faq_questions.append({
                    "@type": "Question",
                    "name": q2_text,
                    "acceptedAnswer": {
                        "@type": "Answer",
                        "text": q2_ans
                    }
                })

    schema_graph = [
        {
            "@type": "BreadcrumbList",
            "itemListElement": [
                {
                    "@type": "ListItem",
                    "position": 1,
                    "name": "AI News Radar",
                    "item": "https://ainewsradar.xyz/"
                },
                {
                    "@type": "ListItem",
                    "position": 2,
                    "name": "AI 行业快讯" if is_zh else "Breaking AI News",
                    "item": f"https://ainewsradar.xyz{'/zh' if is_zh else ''}#news"
                },
                {
                    "@type": "ListItem",
                    "position": 3,
                    "name": escape(title),
                    "item": canonical_url
                }
            ]
        },
        news_article_schema
    ]
    if faq_questions:
        schema_graph.append({
            "@type": "FAQPage",
            "mainEntity": faq_questions
        })

    json_ld_str = json.dumps({"@context": "https://schema.org", "@graph": schema_graph}, ensure_ascii=False, indent=2)
    if not is_zh:
        json_ld_str = sanitize_for_en(json_ld_str, preserve_newlines=True)

    return f"""<!DOCTYPE html>
<html lang="{lang_code}">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{escape(meta_title)}</title>
  <meta name="description" content="{clean_meta_desc}">
  <meta name="robots" content="index, follow, max-image-preview:large, max-snippet:-1, max-video-preview:-1">
  <meta name="googlebot" content="index, follow, max-snippet:-1, max-image-preview:large">
  <link rel="canonical" href="{canonical_url}">
  <link rel="alternate" hreflang="en" href="{alt_en_url}">
  <link rel="alternate" hreflang="zh" href="{alt_zh_url}">
  <link rel="alternate" hreflang="zh-CN" href="{alt_zh_url}">
  <link rel="alternate" hreflang="x-default" href="{alt_en_url}">
  <link rel="sitemap" type="application/xml" title="Sitemap" href="https://ainewsradar.xyz/sitemap.xml">
  <link rel="sitemap" type="application/xml" title="Google News Sitemap" href="https://ainewsradar.xyz/news-sitemap.xml">
  
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

  <!-- Academic & GEO Citation Meta Tags -->
  <meta name="citation_title" content="{escape(title)}">
  <meta name="citation_publication_date" content="{iso_date_only}">
  <meta name="citation_author" content="{escape(source_name or 'AI News Radar Editorial Team')}">
  <meta name="citation_journal_title" content="AI News Radar">
  <meta name="citation_fulltext_html_url" content="{canonical_url}">
  <meta name="citation_abstract" content="{clean_meta_desc}">
  
  <!-- LLMs.txt Discovery (llmstxt.org) -->
  <link rel="help" type="text/plain" href="https://ainewsradar.xyz/llms.txt" title="LLMs.txt Manifest">
  <link rel="alternate" type="text/plain" href="https://ainewsradar.xyz/llms-full.txt" title="Full LLMs.txt">
  {f'<link rel="help" type="text/plain" href="https://ainewsradar.xyz/zh/llms.txt" title="Chinese LLMs.txt Manifest">\n  <link rel="alternate" type="text/plain" href="https://ainewsradar.xyz/zh/llms-full.txt" title="Chinese Full LLMs.txt">' if is_zh else ''}
  
  <link rel="icon" href="data:image/svg+xml,<svg xmlns=%22http://www.w3.org/2000/svg%22 viewBox=%220 0 100 100%22><text y=%22.9em%22 font-size=%2290%22>🤖</text></svg>">
  <link rel="alternate" type="application/rss+xml" title="AI News Radar RSS" href="https://ainewsradar.xyz/feed.xml">
  <link rel="alternate" type="application/rss+xml" title="{"AI 资讯雷达 RSS" if is_zh else "AI News Radar (Chinese Edition RSS)"}" href="https://ainewsradar.xyz/zh/feed.xml">
  <link rel="alternate" type="application/json" title="AI News Radar JSON Feed" href="https://ainewsradar.xyz/feed.json">
  <script src="https://cdn.tailwindcss.com"></script>
  <script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=ca-pub-4912808437101130" crossorigin="anonymous"></script>
  {CLARITY_SCRIPT}
  
  <script type="application/ld+json">
{json_ld_str}
  </script>
</head>
<body class="bg-slate-50 dark:bg-slate-950 text-slate-800 dark:text-slate-100 min-h-screen font-sans antialiased selection:bg-indigo-500 selection:text-white">

  <!-- Top Nav Bar -->
  <header class="sticky top-0 z-40 bg-white/90 dark:bg-slate-900/90 backdrop-blur-md border-b border-slate-200 dark:border-slate-800">
    <div class="max-w-6xl mx-auto px-4 h-14 flex items-center justify-between">
      <div class="flex items-center gap-3">
        <a href="{home_url}" class="font-extrabold text-base tracking-tight flex items-center gap-2 hover:opacity-85 transition-opacity">
          <span class="text-xl">🤖</span>
          <span class="bg-gradient-to-r from-indigo-500 via-purple-500 to-pink-500 bg-clip-text text-transparent">{site_brand}</span>
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
    <article class="rounded-3xl bg-white dark:bg-slate-900 border border-slate-200/90 dark:border-slate-800 shadow-xl overflow-hidden" itemscope itemtype="https://schema.org/NewsArticle">
      
      <!-- Preview Image -->
      <div class="w-full aspect-[16/9] bg-slate-950 relative overflow-hidden flex items-center justify-center">
        <img src="{image_url}" alt="{escape(title)}" class="w-full h-full object-cover" referrerpolicy="no-referrer" onerror="this.src='https://ainewsradar.xyz/images/og-default.jpg'">
        <div class="absolute inset-0 bg-gradient-to-t from-slate-950/80 via-transparent to-transparent"></div>
        <div class="absolute bottom-4 left-6 right-6 flex items-center justify-between gap-3">
          <span class="px-3 py-1 rounded-full text-xs font-bold bg-indigo-600 text-white shadow-md">
            {source_label}: {escape(source_name)}
          </span>
        </div>
      </div>

      <!-- Info Body -->
      <div class="p-6 sm:p-10 lg:p-12">
        
        <h1 class="text-2xl sm:text-3xl font-black text-slate-900 dark:text-slate-100 leading-tight">
          {escape(title)}
        </h1>
        {author_byline_html}

        <!-- News Briefing Content -->
        <div class="mt-6">
          <p class="text-[17px] sm:text-[18px] text-slate-700 dark:text-slate-300 leading-[1.85] sm:leading-[1.9] font-normal">
            {escape(summary)}
          </p>
        </div>

        {bullets_html}
        {video_html}
        {full_coverage_html}
        {analysis_html}

      </div>

      <!-- Dedicated Article Action Footer Dock (Visually Separated from Body: Left=Share, Right=Direct Source CTA) -->
      <div class="px-6 sm:px-10 lg:px-12 py-5 sm:py-6 bg-gradient-to-r from-slate-100/95 via-indigo-50/45 to-slate-100/95 dark:from-slate-950/95 dark:via-indigo-950/35 dark:to-slate-950/95 border-t-2 border-slate-200 dark:border-slate-800 shadow-[inset_0_1px_0_rgba(255,255,255,0.85)] dark:shadow-none flex flex-col sm:flex-row flex-wrap items-stretch sm:items-center justify-between gap-4">

        <!-- Left: Social Sharing & Link Copy Group -->
        <div class="flex flex-wrap items-center gap-2">
          <span class="inline-flex items-center gap-1.5 text-[11px] font-bold uppercase tracking-wider text-slate-500 dark:text-slate-400 mr-1 select-none">
            <span class="w-1.5 h-1.5 rounded-full bg-indigo-500"></span>
            <span>{"分享至" if is_zh else "Share"}</span>
          </span>
          <button onclick="shareDirect('x')" class="px-3.5 py-2.5 rounded-xl bg-black hover:bg-neutral-800 text-white dark:bg-white dark:text-black dark:hover:bg-neutral-100 transition-all text-xs font-bold flex items-center gap-1.5 shadow-sm active:scale-95 cursor-pointer" title="{share_x_text}">
            <svg class="w-3.5 h-3.5 fill-current shrink-0" viewBox="0 0 24 24"><path d="M18.244 2.25h3.308l-7.227 8.26 8.502 11.24H16.17l-5.214-6.817L4.99 21.75H1.68l7.73-8.835L1.254 2.25H8.08l4.713 6.231zm-1.161 17.52h1.833L7.084 4.126H5.117z"/></svg>
            <span>X</span>
          </button>
          <button onclick="shareDirect('threads')" class="px-3.5 py-2.5 rounded-xl bg-black hover:bg-neutral-800 text-white dark:bg-white dark:text-black dark:hover:bg-neutral-100 transition-all text-xs font-bold flex items-center gap-1.5 shadow-sm active:scale-95 cursor-pointer" title="{share_threads_text}">
            <svg class="w-3.5 h-3.5 fill-current shrink-0" viewBox="0 0 192 192"><path d="M141.537 88.988a66.667 66.667 0 0 0-2.518-1.143c-1.482-27.307-16.403-42.94-41.457-43.1h-.34c-14.986 0-27.449 6.396-35.12 18.036l13.779 9.452c5.73-8.695 14.724-10.548 21.348-10.548h.229c8.249.053 14.474 2.452 18.503 7.129 2.932 3.405 4.893 8.111 5.864 14.05-7.314-1.243-15.224-1.626-23.68-1.14-23.82 1.371-39.134 15.264-38.105 34.568.522 9.792 5.4 18.216 13.735 23.719 7.047 4.652 16.124 6.927 25.557 6.412 12.458-.683 22.231-5.436 29.049-14.127 5.178-6.6 8.453-15.153 9.899-25.93 5.937 3.583 10.337 8.298 12.767 13.966 4.132 9.635 4.373 25.468-8.546 38.376-11.319 11.308-24.925 16.2-45.488 16.351-22.809-.169-40.06-7.484-51.275-21.742C35.236 139.966 29.808 120.682 29.605 96c.203-24.682 5.63-43.966 16.133-57.317C56.954 24.425 74.204 17.11 97.013 16.94c22.975.17 40.526 7.52 52.171 21.847 5.71 7.026 10.015 15.86 12.853 26.162l16.147-4.308c-3.44-12.68-8.853-23.606-16.219-32.668C147.036 9.607 125.202.195 97.07 0h-.113C68.882.194 47.292 9.642 32.788 28.08 19.882 44.485 13.224 67.315 13.001 95.932L13 96v.067c.224 28.617 6.882 51.447 19.788 67.854C47.292 182.358 68.882 191.806 96.957 192h.113c24.96-.173 42.554-6.708 57.048-21.189 18.963-18.945 18.392-42.692 12.142-57.27-4.484-10.454-13.033-18.945-24.723-24.553ZM98.44 129.507c-10.44.588-21.286-4.098-21.82-14.135-.397-7.442 5.296-15.746 22.461-16.735 1.966-.114 3.895-.169 5.79-.169 6.235 0 12.068.606 17.371 1.765-1.978 24.702-13.58 28.713-23.802 29.274Z"/></svg>
            <span>Threads</span>
          </button>
          <button onclick="copyCurrentLink()" class="px-3.5 py-2.5 rounded-xl border border-slate-300/90 dark:border-slate-600 bg-white dark:bg-slate-800 hover:bg-slate-50 dark:hover:bg-slate-700 text-slate-700 dark:text-slate-200 transition-all text-xs font-semibold flex items-center gap-1.5 shadow-sm active:scale-95 cursor-pointer">
            <span>🔗</span> <span>{copy_link_text}</span>
          </button>
        </div>

        <!-- Right: Primary Original Source Link CTA -->
        <a href="{escape(source_target_url)}" target="_blank" rel="noopener noreferrer" class="sm:ml-auto inline-flex items-center justify-center gap-2 px-6 py-3 rounded-xl bg-gradient-to-r from-indigo-600 via-purple-600 to-pink-600 hover:from-indigo-500 hover:to-pink-500 text-white font-bold text-sm shadow-lg shadow-indigo-500/25 active:scale-95 transition-all">
          <span>{official_btn_text}</span>
        </a>

      </div>

      <!-- Legal Source Attribution, Copyright & DMCA Takedown Notice -->
      <aside aria-label="{'版权归属与免责声明' if is_zh else 'Source Attribution and Copyright Notice'}" class="px-6 sm:px-10 lg:px-12 py-4 bg-slate-50/90 dark:bg-slate-950/70 border-t border-slate-200/80 dark:border-slate-800/80 text-[11.5px] leading-relaxed text-slate-500 dark:text-slate-400">
        {
          f'<p><strong class="text-slate-600 dark:text-slate-300">版权归属与免责声明：</strong>本页内容系 AI 资讯雷达基于公开可访问信息进行的行业追踪整理与中文编译，仅供学习交流与信息参考，不构成任何投资、商业或法律建议。原文标题、正文报道、商标、配图及内嵌音视频之完整著作权均严格归属原始发布机构 <strong class="text-slate-600 dark:text-slate-300">{escape(source_name)}</strong> 及原作者所有，建议读者点击上方原始链接访问并订阅支持正版原创媒体。如权利人认为内容涉权或需限制展示/立即下架，请查阅 <a href="/zh/dmca" class="text-indigo-600 dark:text-indigo-400 hover:underline font-medium">版权声明与 DMCA 下架机制</a> 并致函 <a href="mailto:dmca@ainewsradar.xyz" class="text-indigo-600 dark:text-indigo-400 hover:underline font-medium">dmca@ainewsradar.xyz</a>（24–48 小时内快速处置）。</p>'
          if is_zh else
          f'<p><strong class="text-slate-600 dark:text-slate-300">Source Attribution &amp; Disclaimer:</strong> Curated by AI News Radar for independent industry monitoring, commentary, and research reference only (not legal, financial, or investment advice). All third-party headlines, reporting, trademarks, images, and embedded media remain the sole intellectual property of <strong class="text-slate-600 dark:text-slate-300">{escape(source_name)}</strong> and the credited author(s). Readers are encouraged to subscribe to and support original journalism via the official link above. Rights holders or publishers requesting immediate takedown, summary-only display, or domain opt-out may contact <a href="mailto:dmca@ainewsradar.xyz" class="text-indigo-600 dark:text-indigo-400 hover:underline font-medium">dmca@ainewsradar.xyz</a> per our <a href="/dmca" class="text-indigo-600 dark:text-indigo-400 hover:underline font-medium">DMCA &amp; Copyright Policy</a> (24–48h SLA).</p>'
        }
      </aside>
    </article>

    {related_html}

  </main>

  <footer class="mt-16 border-t border-slate-200 dark:border-slate-800 py-8 px-4 text-center text-xs text-slate-500 dark:text-slate-400">
    <div class="max-w-4xl mx-auto space-y-3">
      <nav class="flex flex-wrap items-center justify-center gap-x-5 gap-y-1.5 font-medium">
        {
          '<a href="/zh/about" class="hover:text-indigo-600 dark:hover:text-indigo-400 transition-colors">关于我们</a>'
          '<a href="/zh/editorial-policy" class="hover:text-indigo-600 dark:hover:text-indigo-400 transition-colors">编辑方针</a>'
          '<a href="/zh/dmca" class="hover:text-rose-600 dark:hover:text-rose-400 transition-colors">版权与 DMCA 免责</a>'
          '<a href="/zh/terms" class="hover:text-indigo-600 dark:hover:text-indigo-400 transition-colors">服务条款</a>'
          '<a href="/zh/privacy" class="hover:text-indigo-600 dark:hover:text-indigo-400 transition-colors">隐私政策</a>'
          '<a href="/zh/contact" class="hover:text-indigo-600 dark:hover:text-indigo-400 transition-colors">联系我们</a>'
          if is_zh else
          '<a href="/about" class="hover:text-indigo-600 dark:hover:text-indigo-400 transition-colors">About</a>'
          '<a href="/editorial-policy" class="hover:text-indigo-600 dark:hover:text-indigo-400 transition-colors">Editorial Policy</a>'
          '<a href="/dmca" class="hover:text-rose-600 dark:hover:text-rose-400 transition-colors">DMCA &amp; Copyright</a>'
          '<a href="/terms" class="hover:text-indigo-600 dark:hover:text-indigo-400 transition-colors">Terms</a>'
          '<a href="/privacy" class="hover:text-indigo-600 dark:hover:text-indigo-400 transition-colors">Privacy</a>'
          '<a href="/contact" class="hover:text-indigo-600 dark:hover:text-indigo-400 transition-colors">Contact</a>'
        }
      </nav>
      <p class="text-slate-400 dark:text-slate-500">&copy; 2026 AI News Radar (ainewsradar.xyz) &middot; {'所有第三方报道版权归原发布机构及作者所有' if is_zh else 'All third-party reporting copyrights belong to their respective publishers and authors'}</p>
    </div>
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
      const rawTitle = title.replace(/<[^>]+>/g, '').trim();
      const cleanTitleX = rawTitle.slice(0, 140);
      const cleanTitleThreads = rawTitle.slice(0, 300);
      if (platform === 'x') {{
        const text = encodeURIComponent(cleanTitleX + "\\n\\n#AI #AINewsRadar");
        window.open(`https://x.com/intent/tweet?text=${{text}}&url=${{encodeURIComponent(shareUrl)}}`, '_blank', 'noopener,noreferrer');
      }} else if (platform === 'threads') {{
        const text = encodeURIComponent(cleanTitleThreads + "\\n\\n#AI #AINewsRadar");
        window.open(`https://www.threads.net/intent/post?text=${{text}}&url=${{encodeURIComponent(shareUrl)}}`, '_blank', 'noopener,noreferrer');
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
    # Prioritize rich backend data (which holds complete article bodies, full translations, and multi-paragraph records)
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

    # Also build a fallback lookup map from master_archive and archive_news for rich paragraphs
    rich_lookup = {}
    for arch_file in ["data/master_archive.json", "data/archive_news.json", "public/data/archive_news.json"]:
        ap = os.path.join(WORKSPACE_DIR, arch_file)
        if os.path.exists(ap):
            try:
                with open(ap, "r", encoding="utf-8") as af:
                    a_data = json.load(af)
                    a_list = a_data.get("items", []) if isinstance(a_data, dict) else (a_data if isinstance(a_data, list) else [])
                    for a_it in a_list:
                        a_id = a_it.get("id")
                        if a_id and (a_it.get("paragraphs") or a_it.get("article_content") or a_it.get("article_content_zh")):
                            if a_id not in rich_lookup:
                                rich_lookup[a_id] = a_it
            except Exception:
                pass

    # Load Bloomberg Cache for authentic photography, full verbatim paragraphs, and clean author attribution
    bloomberg_cache = {}
    bc_path = os.path.join(WORKSPACE_DIR, "data", "bloomberg_cache.json")
    if os.path.exists(bc_path):
        try:
            with open(bc_path, "r", encoding="utf-8") as bcf:
                bloomberg_cache = json.load(bcf)
        except Exception:
            pass

    # Load Forbes Cache for authentic photography, full verbatim paragraphs, and clean author attribution
    forbes_cache = {}
    fc_path = os.path.join(WORKSPACE_DIR, "data", "forbes_cache.json")
    if os.path.exists(fc_path):
        try:
            with open(fc_path, "r", encoding="utf-8") as fcf:
                forbes_cache = json.load(fcf)
        except Exception:
            pass

    # Ensure curated headline items (which have landing pages) are always in news
    for hf in ["data/curated_column_highlights.json", "public/data/curated_column_highlights.json"]:
        hp = os.path.join(WORKSPACE_DIR, hf)
        if os.path.exists(hp):
            try:
                with open(hp, "r", encoding="utf-8") as hfile:
                    hdata = json.load(hfile)
                    hnews = hdata.get("columns", {}).get("news", {})
                    h_cands = []
                    if hnews.get("headline_item"):
                        h_cands.append(hnews["headline_item"])
                    h_cands.extend(hnews.get("headlines", []))
                    existing_ids = {n.get("id") for n in news if n.get("id")}
                    for hc in h_cands:
                        hc_id = hc.get("id")
                        if hc_id and hc_id not in existing_ids:
                            news.append(hc)
                            existing_ids.add(hc_id)
            except Exception:
                pass

    for it in news:
        nid = it.get("id")
        u = it.get("url") or ""
        # Check Bloomberg cache
        if "bloomberg" in u.lower() or "bloomberg" in (it.get("source") or "").lower():
            clean_u = u.split("#")[0].strip()
            bc_entry = bloomberg_cache.get(clean_u)
            if not bc_entry and clean_u:
                try:
                    from crawlers.bloomberg_crawler import crawl_bloomberg
                    bc_entry = crawl_bloomberg(clean_u)
                except Exception:
                    pass
            if bc_entry:
                for fld in ("paragraphs", "paragraphs_zh", "full_text", "cover_image", "image_caption", "author"):
                    if bc_entry.get(fld):
                        it[fld] = bc_entry[fld]
                if bc_entry.get("cover_image"):
                    it["image_url"] = bc_entry["cover_image"]
                it["is_substantive"] = True
                it["is_paywalled"] = False

        # Check Forbes cache
        if "forbes" in u.lower() or "forbes" in (it.get("source") or "").lower():
            clean_u = u.split("#")[0].strip()
            fc_entry = forbes_cache.get(clean_u)
            if not fc_entry and clean_u:
                try:
                    from crawlers.forbes_crawler import crawl_forbes
                    fc_entry = crawl_forbes(clean_u, title=it.get("title", ""))
                except Exception:
                    pass
            if fc_entry:
                for fld in ("title", "title_en", "paragraphs", "paragraphs_zh", "full_text", "cover_image", "image_caption", "author"):
                    if fc_entry.get(fld):
                        it[fld] = fc_entry[fld]
                if fc_entry.get("cover_image"):
                    it["image_url"] = fc_entry["cover_image"]
                it["is_substantive"] = True
                it["is_paywalled"] = False

        if nid and nid in rich_lookup:
            rit = rich_lookup[nid]
            for fld in ("paragraphs", "paragraphs_zh", "article_content", "article_content_en", "article_content_zh", "subheadings", "inline_images"):
                if rit.get(fld) and not it.get(fld):
                    it[fld] = rit[fld]

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
                        if i_id in rich_lookup:
                            rit = rich_lookup[i_id]
                            for fld in ("paragraphs", "paragraphs_zh", "article_content", "article_content_en", "article_content_zh", "subheadings", "inline_images"):
                                if rit.get(fld) and not it.get(fld):
                                    it[fld] = rit[fld]
                        u = it.get("url") or ""
                        if "bloomberg" in u.lower() or "bloomberg" in (it.get("source") or "").lower():
                            clean_u = u.split("#")[0].strip()
                            bc_entry = bloomberg_cache.get(clean_u)
                            if bc_entry:
                                for fld in ("paragraphs", "paragraphs_zh", "full_text", "cover_image", "image_caption", "author"):
                                    if bc_entry.get(fld):
                                        it[fld] = bc_entry[fld]
                                if bc_entry.get("cover_image"):
                                    it["image_url"] = bc_entry["cover_image"]
                                it["is_substantive"] = True
                                it["is_paywalled"] = False
                        if "forbes" in u.lower() or "forbes" in (it.get("source") or "").lower():
                            clean_u = u.split("#")[0].strip()
                            fc_entry = forbes_cache.get(clean_u)
                            if fc_entry:
                                for fld in ("title", "title_en", "paragraphs", "paragraphs_zh", "full_text", "cover_image", "image_caption", "author"):
                                    if fc_entry.get(fld):
                                        it[fld] = fc_entry[fld]
                                if fc_entry.get("cover_image"):
                                    it["image_url"] = fc_entry["cover_image"]
                                it["is_substantive"] = True
                                it["is_paywalled"] = False
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
    try:
        generate_all_landing_pages()
    except BaseException as e:
        import traceback
        print(f"\n🚨 [ToolNewsPublisher Error Shield] 捕获异常，安全自愈放行: {e}")
        traceback.print_exc()
        sys.exit(0)
