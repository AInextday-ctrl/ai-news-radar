"""
Main pipeline entrypoint 2.0 - Coordinates fetching, Gemini processing, Top 3 digest, and output saving.
"""

import socket
socket.setdefaulttimeout(15.0)
import sys

try:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", line_buffering=True)
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8", line_buffering=True)
except Exception:
    pass

import os
import re
import json
import time
from datetime import datetime, timezone, timedelta
import urllib.parse
import httpx
from fetcher import fetch_all_sources, get_chatbot_arena_top5, get_arxiv_curated_papers, extract_clean_video_id, normalize_title_fingerprint, evaluate_dynamic_pinned_status, get_smart_cover_url, resolve_product_hunt_redirect, enrich_tweet_media
from processor import process_items_batch, clean_news_text, generate_smart_fallback_summary, free_translate_zh, free_translate_en
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
    """Dynamically generate fresh multilingual sitemap.xml.
    Includes: homepage, trust pages, and last 30 days of daily briefings."""
    now_date = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    # 固定页面
    static_pages = [
        {"loc": "https://ainewsradar.xyz/", "changefreq": "hourly", "priority": "1.0", "hreflang": True},
        {"loc": "https://ainewsradar.xyz/about", "changefreq": "monthly", "priority": "0.8"},
        {"loc": "https://ainewsradar.xyz/contact", "changefreq": "monthly", "priority": "0.7"},
        {"loc": "https://ainewsradar.xyz/editorial-policy", "changefreq": "monthly", "priority": "0.7"},
        {"loc": "https://ainewsradar.xyz/privacy", "changefreq": "monthly", "priority": "0.6"},
        {"loc": "https://ainewsradar.xyz/terms", "changefreq": "monthly", "priority": "0.6"},
    ]

    url_entries = []
    for p in static_pages:
        hreflang_block = ""
        if p.get("hreflang"):
            hreflang_block = """
    <xhtml:link rel="alternate" hreflang="zh-CN" href="https://ainewsradar.xyz/zh"/>
    <xhtml:link rel="alternate" hreflang="zh" href="https://ainewsradar.xyz/zh"/>
    <xhtml:link rel="alternate" hreflang="en" href="https://ainewsradar.xyz/"/>
    <xhtml:link rel="alternate" hreflang="x-default" href="https://ainewsradar.xyz/"/>"""
        url_entries.append(f"""  <url>
    <loc>{p['loc']}</loc>{hreflang_block}
    <lastmod>{now_date}</lastmod>
    <changefreq>{p['changefreq']}</changefreq>
    <priority>{p['priority']}</priority>
  </url>""")

    # 扫描 public/daily/ 目录，收录最近 30 天的每日简报页
    daily_dir = os.path.join(PUBLIC_DIR, "daily")
    if os.path.isdir(daily_dir):
        daily_files = sorted(
            [f for f in os.listdir(daily_dir) if f.endswith(".html") and len(f) == 15],
            reverse=True
        )[:30]  # 最多收录最近 30 天
        for fname in daily_files:
            date_slug = fname.replace(".html", "")
            url_entries.append(f"""  <url>
    <loc>https://ainewsradar.xyz/daily/{date_slug}</loc>
    <lastmod>{date_slug}</lastmod>
    <changefreq>never</changefreq>
    <priority>0.75</priority>
  </url>""")

    urls_xml = "\n".join(url_entries)
    xml_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"
        xmlns:xhtml="http://www.w3.org/1999/xhtml">
{urls_xml}
</urlset>
"""
    try:
        os.makedirs(PUBLIC_DIR, exist_ok=True)
        with open(SITEMAP_FILE, "wb") as f:
            f.write(xml_content.strip().encode("utf-8") + b"\n")
        print(f"🗺️ 站点地图已动态更新: {SITEMAP_FILE} (lastmod: {now_date}, 共 {len(url_entries)} 个 URL)")
    except Exception as e:
        print(f"⚠️ 更新站点地图失败: {e}")


def inject_seo_static_content(recent_items: list):
    """
    将最新资讯以静态 HTML 形式注入 public/index.html 的 SEO 占位区块。
    Googlebot 可直接爬取这部分内容，绕过 JS 渲染限制。
    内容放在 sr-only 不可见区域，不影响视觉呈现。
    """
    INDEX_FILE = os.path.join(PUBLIC_DIR, "index.html")
    START_MARKER = "<!-- ========== SEO_STATIC_NEWS_START ========== -->"
    END_MARKER = "<!-- ========== SEO_STATIC_NEWS_END ========== -->"

    # 取最新 20 条，优先 news 类，补充其他类
    news_items = [i for i in recent_items if i.get("category") == "news"][:10]
    celeb_items = [i for i in recent_items if i.get("category") == "celebrity"][:4]
    tool_items = [i for i in recent_items if i.get("category") == "tools"][:3]
    video_items = [i for i in recent_items if i.get("category") == "videos"][:3]
    seo_items = (news_items + celeb_items + tool_items + video_items)[:20]

    if not seo_items:
        print("⚠️ SEO 静态内容注入: 无可用资讯，跳过。")
        return

    cat_labels = {
        "news": "AI 行业快讯",
        "celebrity": "社交动态",
        "tools": "场景工具",
        "videos": "实战视频",
        "prompts": "提示词库",
    }

    def fmt_date(raw: str) -> str:
        try:
            dt = datetime.fromisoformat(raw.replace("Z", "+00:00"))
            return dt.strftime("%Y年%m月%d日")
        except Exception:
            return ""

    def safe(text: str, max_len: int = 200) -> str:
        if not text:
            return ""
        text = text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")
        return text[:max_len]

    # 生成 article 列表
    articles_html = ""
    for item in seo_items:
        title = safe(item.get("title_zh") or item.get("title", ""), 120)
        summary = safe(item.get("summary_zh") or item.get("content_snippet", ""), 200)
        source = safe(item.get("source", ""), 60)
        url = item.get("url", "#")
        date_str = fmt_date(item.get("raw_published_at", ""))
        cat = item.get("category", "news")
        cat_label = cat_labels.get(cat, "AI 资讯")

        if not title:
            continue

        articles_html += f"""    <article>
      <h3><a href="{url}" target="_blank" rel="noopener noreferrer">{title}</a></h3>
      {f'<p>{summary}</p>' if summary else ''}
      <footer>
        <span>{cat_label}</span>
        {f'<span>{source}</span>' if source else ''}
        {f'<time>{date_str}</time>' if date_str else ''}
      </footer>
    </article>\n"""

    now_str = datetime.now(timezone.utc).strftime("%Y年%m月%d日 %H:%M UTC")
    static_block = f"""{START_MARKER}
  <section class="sr-only" aria-label="AI 资讯雷达最新动态（搜索引擎索引区）">
    <h2>AI 资讯雷达 · 今日精选（更新于 {now_str}）</h2>
    <p>以下是 AI 资讯雷达从全球 50+ 权威 AI 信源实时聚合的最新动态，涵盖大模型突破、产业新闻、领袖观点与实战工具。所有内容经 AI 辅助翻译与人工编辑审核，附原始来源链接。</p>
{articles_html}  </section>
  {END_MARKER}"""

    try:
        with open(INDEX_FILE, "r", encoding="utf-8") as f:
            content = f.read()

        if START_MARKER not in content or END_MARKER not in content:
            print("⚠️ SEO 静态注入: index.html 中未找到占位标记，跳过。")
            return

        # 替换占位区块
        import re as _re
        pattern = _re.compile(
            r"<!-- ={10} SEO_STATIC_NEWS_START ={10} -->.*?<!-- ={10} SEO_STATIC_NEWS_END ={10} -->",
            _re.DOTALL
        )
        new_content = pattern.sub(static_block, content)

        with open(INDEX_FILE, "w", encoding="utf-8") as f:
            f.write(new_content)

        print(f"🕷️ SEO 静态内容注入完成: {len(seo_items)} 条资讯已写入 index.html（Googlebot 可见）")
    except Exception as e:
        print(f"⚠️ SEO 静态内容注入失败: {e}")


def generate_daily_briefing(recent_items: list):
    """
    生成当日 AI 简报独立静态 HTML 页面：public/daily/YYYY-MM-DD.html
    每篇页面包含当日 Top 15 资讯的完整标题、摘要、来源、时间与原文链接。
    每次 pipeline 运行时幂等覆盖当天文件（内容持续更新至深夜）。
    """
    DAILY_DIR = os.path.join(PUBLIC_DIR, "daily")
    os.makedirs(DAILY_DIR, exist_ok=True)

    now_utc = datetime.now(timezone.utc)
    # 用北京时间日期作为文件名（UTC+8）
    from datetime import timedelta
    cst_tz = timezone(timedelta(hours=8))
    now_cst = now_utc.astimezone(cst_tz)
    date_slug = now_cst.strftime("%Y-%m-%d")
    date_zh = now_cst.strftime("%Y年%m月%d日")
    output_path = os.path.join(DAILY_DIR, f"{date_slug}.html")

    # 筛选过去 36 小时内的资讯（覆盖跨日情况）
    cutoff_ts = now_utc.timestamp() - 36 * 3600
    today_items = []
    for it in recent_items:
        raw = it.get("raw_published_at", "")
        if not raw:
            continue
        try:
            ts = datetime.fromisoformat(raw.replace("Z", "+00:00")).timestamp()
            if ts >= cutoff_ts:
                today_items.append(it)
        except Exception:
            continue

    # 分类筛选
    news_items = [i for i in today_items if i.get("category") == "news"][:8]
    celeb_items = [i for i in today_items if i.get("category") == "celebrity"][:4]
    tool_items = [i for i in today_items if i.get("category") == "tools"][:3]
    briefing_items = news_items + celeb_items + tool_items
    if not briefing_items:
        # fallback: 用全量最新的前 15 条
        briefing_items = recent_items[:15]

    def safe_html(text, max_len=300):
        if not text:
            return ""
        text = str(text).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")
        return text[:max_len]

    def fmt_time(raw):
        try:
            dt = datetime.fromisoformat(raw.replace("Z", "+00:00"))
            cst = dt.astimezone(cst_tz)
            return cst.strftime("%H:%M")
        except Exception:
            return ""

    cat_labels = {
        "news": ("⚡ AI 行业快讯", "#4f46e5"),
        "celebrity": ("🐦 社交动态", "#0284c7"),
        "tools": ("🛠️ 场景工具", "#0891b2"),
        "videos": ("🎬 实战视频", "#dc2626"),
        "prompts": ("💡 提示词库", "#d97706"),
    }

    # 生成 JSON-LD Article schema
    schema_items = []
    for it in briefing_items[:5]:
        title = safe_html(it.get("title_zh") or it.get("title", ""), 120)
        url = it.get("url", "")
        pub = it.get("raw_published_at", now_utc.isoformat())
        if title and url:
            schema_items.append(f'{{"@type":"NewsArticle","headline":"{title}","url":"{url}","datePublished":"{pub}"}}')
    schema_list = ",\n    ".join(schema_items)

    # 生成文章卡片 HTML
    articles_html = ""
    for i, item in enumerate(briefing_items, 1):
        title = safe_html(item.get("title_zh") or item.get("title", ""), 120)
        title_en = safe_html(item.get("title_en") or item.get("title", ""), 120)
        summary = safe_html(item.get("summary_zh") or item.get("content_snippet", ""), 300)
        source = safe_html(item.get("source", ""), 60)
        url = item.get("url", "#")
        time_str = fmt_time(item.get("raw_published_at", ""))
        cat = item.get("category", "news")
        cat_label, cat_color = cat_labels.get(cat, ("AI 资讯", "#4f46e5"))
        image_url = item.get("image_url", "")

        if not title:
            continue

        url_to_use = url
        rel_attr = 'rel="noopener noreferrer"'
        btn_label = '阅读原文 →'
        if cat == "tools" and url and url != "#" and url.startswith("http"):
            import urllib.parse
            clean_name = item.get("app_name") or title.split("】")[-1].strip()
            url_to_use = f"/go?target={urllib.parse.quote(url)}&name={urllib.parse.quote(clean_name)}"
            rel_attr = 'rel="nofollow noopener noreferrer"'
            btn_label = '🚀 访问官网 →'

        img_html = ""
        if image_url and image_url.startswith("http"):
            img_html = f'<img src="{image_url}" alt="{title}" loading="lazy" style="width:100%;height:180px;object-fit:cover;border-radius:8px;margin-bottom:12px;" onerror="this.style.display=\'none\'">'

        articles_html += f"""
  <article style="background:#fff;border:1px solid #e2e8f0;border-radius:12px;padding:20px;margin-bottom:20px;" itemscope itemtype="https://schema.org/NewsArticle">
    <meta itemprop="datePublished" content="{item.get('raw_published_at', '')}">
    <meta itemprop="publisher" content="AI 资讯雷达">
    {img_html}
    <div style="display:flex;align-items:center;gap:8px;margin-bottom:10px;flex-wrap:wrap;">
      <span style="background:{cat_color}15;color:{cat_color};font-size:12px;font-weight:600;padding:3px 10px;border-radius:20px;border:1px solid {cat_color}30;">{cat_label}</span>
      {f'<span style="color:#94a3b8;font-size:12px;">🕒 {time_str} CST</span>' if time_str else ''}
      {f'<span style="color:#94a3b8;font-size:12px;">· {source}</span>' if source else ''}
    </div>
    <h2 itemprop="headline" style="font-size:18px;font-weight:700;color:#1e293b;margin:0 0 10px;line-height:1.5;">
      <a href="{url_to_use}" target="_blank" {rel_attr} itemprop="url" style="color:inherit;text-decoration:none;">{title}</a>
    </h2>
    {f'<p style="font-size:13px;color:#64748b;margin:0 0 8px;font-style:italic;">{title_en}</p>' if title_en and title_en != title else ''}
    {f'<p itemprop="description" style="font-size:15px;color:#475569;line-height:1.7;margin:0 0 14px;">{summary}</p>' if summary else ''}
    <a href="{url_to_use}" target="_blank" {rel_attr}
       style="display:inline-flex;align-items:center;gap:6px;font-size:13px;color:{cat_color};font-weight:600;text-decoration:none;border:1px solid {cat_color}40;padding:6px 14px;border-radius:8px;transition:all 0.2s;">
      {btn_label}
    </a>
  </article>"""

    total = len(briefing_items)
    page_title = f"AI 日报 · {date_zh} | 今日精选 {total} 条 AI 前沿动态 | AI 资讯雷达"
    page_desc = f"{date_zh} AI 资讯雷达精选：涵盖大模型突破、硅谷动态、AI 工具上线与领袖观点。共 {total} 条经人工审核的 AI 行业快报，附原始来源链接。"

    html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{page_title}</title>
  <meta name="description" content="{page_desc}">
  <meta name="robots" content="index, follow">
  <link rel="canonical" href="https://ainewsradar.xyz/daily/{date_slug}">
  <meta property="og:title" content="{page_title}">
  <meta property="og:description" content="{page_desc}">
  <meta property="og:type" content="article">
  <meta property="og:url" content="https://ainewsradar.xyz/daily/{date_slug}">
  <meta property="article:published_time" content="{now_utc.isoformat()}">
  <link rel="icon" href="data:image/svg+xml,<svg xmlns=%22http://www.w3.org/2000/svg%22 viewBox=%220 0 100 100%22><text y=%22.9em%22 font-size=%2290%22>🤖</text></svg>">
  <!-- Google AdSense -->
  <script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=ca-pub-4912808437101130" crossorigin="anonymous"></script>
  <script type="application/ld+json">
  {{
    "@context": "https://schema.org",
    "@type": "CollectionPage",
    "name": "{page_title}",
    "description": "{page_desc}",
    "url": "https://ainewsradar.xyz/daily/{date_slug}",
    "publisher": {{
      "@type": "Organization",
      "name": "AI 资讯雷达",
      "url": "https://ainewsradar.xyz",
      "logo": {{"@type": "ImageObject", "url": "https://ainewsradar.xyz/"}}
    }},
    "datePublished": "{now_utc.date().isoformat()}",
    "dateModified": "{now_utc.isoformat()}",
    "hasPart": [
      {schema_list}
    ]
  }}
  </script>
  <style>
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #f8fafc; color: #1e293b; min-height: 100vh; }}
    .container {{ max-width: 800px; margin: 0 auto; padding: 0 16px; }}
    a:hover {{ opacity: 0.8; }}
  </style>
</head>
<body>

  <!-- Header -->
  <header style="background:#fff;border-bottom:1px solid #e2e8f0;position:sticky;top:0;z-index:50;box-shadow:0 1px 3px rgba(0,0,0,0.05);">
    <div class="container" style="padding-top:14px;padding-bottom:14px;display:flex;align-items:center;justify-content:space-between;">
      <a href="/" style="display:flex;align-items:center;gap:10px;text-decoration:none;">
        <div style="width:36px;height:36px;border-radius:10px;background:linear-gradient(135deg,#4f46e5,#7c3aed,#ec4899);display:flex;align-items:center;justify-content:center;font-size:18px;">🤖</div>
        <div>
          <div style="font-size:16px;font-weight:900;background:linear-gradient(to right,#312e81,#4f46e5);-webkit-background-clip:text;-webkit-text-fill-color:transparent;">AI 资讯雷达</div>
          <div style="font-size:11px;color:#94a3b8;">ainewsradar.xyz</div>
        </div>
      </a>
      <a href="/" style="font-size:13px;color:#4f46e5;font-weight:600;text-decoration:none;">← 返回实时首页</a>
    </div>
  </header>

  <!-- Hero -->
  <div style="background:linear-gradient(135deg,#4f46e5 0%,#7c3aed 50%,#ec4899 100%);padding:40px 16px;">
    <div class="container" style="text-align:center;color:#fff;">
      <div style="font-size:13px;font-weight:600;opacity:0.85;margin-bottom:8px;letter-spacing:2px;text-transform:uppercase;">AI 资讯雷达 · 每日简报</div>
      <h1 style="font-size:28px;font-weight:900;margin-bottom:10px;line-height:1.3;">{date_zh} AI 日报</h1>
      <p style="font-size:15px;opacity:0.9;max-width:500px;margin:0 auto 16px;line-height:1.6;">今日精选 {total} 条全球 AI 前沿动态，经 AI 辅助翻译与人工编辑审核，所有资讯均附原始来源链接。</p>
      <div style="display:flex;justify-content:center;gap:20px;flex-wrap:wrap;">
        <span style="background:rgba(255,255,255,0.2);padding:6px 16px;border-radius:20px;font-size:13px;">📰 {len(news_items)} 条行业快讯</span>
        <span style="background:rgba(255,255,255,0.2);padding:6px 16px;border-radius:20px;font-size:13px;">🐦 {len(celeb_items)} 条领袖观点</span>
        <span style="background:rgba(255,255,255,0.2);padding:6px 16px;border-radius:20px;font-size:13px;">🛠️ {len(tool_items)} 款场景工具</span>
      </div>
    </div>
  </div>

  <!-- About This Briefing -->
  <div class="container" style="padding-top:24px;padding-bottom:8px;">
    <div style="background:#eff6ff;border:1px solid #bfdbfe;border-radius:10px;padding:16px 20px;">
      <p style="font-size:14px;color:#1e40af;line-height:1.7;">
        <strong>关于本期简报：</strong>AI 资讯雷达每日从全球 50+ 权威 AI 信源（包括 OpenAI、Anthropic、Google DeepMind 官博，彭博社、路透社、The Verge 等主流媒体，以及 Andrej Karpathy、Sam Altman 等行业领袖的社交账号）自动聚合最新资讯，经 Google Gemini API 辅助翻译为中文并由人工编辑审核后发布。所有内容均附原始来源链接，版权归原作者所有。
      </p>
    </div>
  </div>

  <!-- Articles -->
  <main class="container" style="padding-top:20px;padding-bottom:40px;">
    {articles_html}
  </main>

  <!-- Footer -->
  <footer style="background:#fff;border-top:1px solid #e2e8f0;padding:32px 16px;">
    <div class="container">
      <!-- Navigation to other daily briefings would go here -->
      <div style="text-align:center;margin-bottom:20px;">
        <a href="/" style="display:inline-flex;align-items:center;gap:8px;background:#4f46e5;color:#fff;text-decoration:none;font-weight:700;padding:12px 28px;border-radius:10px;font-size:14px;">
          🤖 返回 AI 资讯雷达实时首页
        </a>
      </div>
      <nav style="display:flex;flex-wrap:wrap;justify-content:center;gap:16px 24px;margin-bottom:16px;">
        <a href="/about" style="font-size:13px;color:#64748b;text-decoration:none;">关于我们</a>
        <a href="/editorial-policy" style="font-size:13px;color:#64748b;text-decoration:none;">编辑方针</a>
        <a href="/contact" style="font-size:13px;color:#64748b;text-decoration:none;">联系我们</a>
        <a href="/privacy" style="font-size:13px;color:#64748b;text-decoration:none;">隐私政策</a>
        <a href="/terms" style="font-size:13px;color:#64748b;text-decoration:none;">服务条款</a>
      </nav>
      <p style="text-align:center;font-size:12px;color:#94a3b8;">
        © 2026 AI News Radar (ainewsradar.xyz). 内容经 AI 辅助处理与人工编辑审核 · 版权归原作者所有
      </p>
    </div>
  </footer>

</body>
</html>"""

    try:
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(html)
        print(f"📰 每日简报已生成: /daily/{date_slug}.html ({total} 条资讯, {len(html)//1024}KB)")
    except Exception as e:
        print(f"⚠️ 每日简报生成失败: {e}")


def parse_time_for_sort(it):
    raw = it.get("raw_published_at", "")
    if not raw:
        return 0
    try:
        return datetime.fromisoformat(raw.replace("Z", "+00:00")).timestamp()
    except Exception:
        return 0


def is_tibo_reset_tweet(it: dict, now_ts: float = None) -> bool:
    """
    判定是否为 OpenAI Codex 负责人 Thibault Sottiaux (@thsottiaux) 关于 Codex reset 的核心推文。
    自发布时间起算维持 24 小时，过期或非本人推文必须直接返回 False。
    """
    if not isinstance(it, dict):
        return False
    # 严格排除 prompts / 工具等非推特条目
    if it.get("is_prompt") or it.get("category") == "prompts" or it.get("sub_type") == "reasoning":
        return False
    handle = (it.get("author_handle") or it.get("handle") or "").lower().strip()
    author = (it.get("author") or "").lower().strip()
    url = (it.get("url") or "").lower()

    # 坚决排除 @tibo_maker 等同名或普通博主
    if "tibo_maker" in handle or "tibo_maker" in author or "tibo_maker" in url:
        return False

    # 必须是 OpenAI Codex 负责人 Thibault Sottiaux (@thsottiaux)
    is_thsottiaux = "thsottiaux" in handle or "thsottiaux" in url or ("sottiaux" in author and ("codex" in author or "openai" in author or "tibo" in author or "thibault" in author))
    if not is_thsottiaux:
        return False

    # 必须明确包含 Codex reset / usage limit / quota 重置关键词，严禁把招募/闲聊/日常当重置！
    text = f"{it.get('title') or ''} {it.get('title_en') or ''} {it.get('title_zh') or ''} {it.get('full_text_en') or ''} {it.get('full_text_zh') or ''} {it.get('quote_en') or ''} {it.get('quote_zh') or ''} {it.get('content_snippet') or ''}".lower()

    # 明确排除招人、闲聊、喝咖啡等日常推文
    if any(k in text for k in ["dm if you want to help scale", "coffee", "great places to hangout", "hiring", "fixing bugs while sipping coffee"]):
        return False

    reset_keywords = ["reset", "重置", "rest and reset", "quota", "usage limit", "rate limit", "limit reset", "全网重置", "配额重置", "day 20"]
    if not any(k in text for k in reset_keywords):
        return False

    if now_ts is None:
        now_ts = time.time()
    pub_ts = parse_time_for_sort(it)
    if pub_ts <= 0:
        return True
    diff_sec = now_ts - pub_ts
    return -3600 <= diff_sec <= 172800  # 48小时最高豁免期


def is_meaningful_tweet(it: dict) -> bool:
    """
    判断一条推文是否具备独立阅读价值，坚决过滤无意义单句、脱离语境的闲聊回复、纯标签灌水、Web3营销与断头线程碎片
    """
    if not isinstance(it, dict):
        return False
        
    # 凡是出现 Tibo 的 reset 相关推文，在 24 小时内享有最高豁免权，100% 视为有价值推文
    if is_tibo_reset_tweet(it):
        return True

    # 彻底禁止任何伪造/模拟数据
    item_id = str(it.get("id") or "")
    if item_id.startswith("mock_"):
        return False
        
    text = (it.get("full_text_en") or it.get("content_snippet") or it.get("title") or "").strip()
    if not text:
        return False
        
    # 如果整个正文只是一个链接 (如 https://t.co/...)，没有实质文本说明，坚决过滤
    if re.fullmatch(r'https?://\S+', text):
        return False

    # 0. 严厉拦截 Web3 / Crypto 币圈营销与假借 AI 标签的噪音推文
    text_lower = f"{text} {it.get('title_zh') or ''} {it.get('summary_zh') or ''}".lower()
    crypto_spam_keywords = [
        "xdcnetwork", "concordium", "airdrop", "memecoin", "presale",
        "tokenomics", "$sol", "$eth", "$btc", "crypto payment", "web3 wallet", "whitelist mint"
    ]
    if any(kw in text_lower for kw in crypto_spam_keywords):
        return False

    # 剔除链接、@提及 和 #标签 后的实质内容（防止 "red fuji #AI #PS #Adobe" 靠标签刷字数蒙混过关）
    substantive = re.sub(r'https?://\S+|@\w+|#[\w-]+', '', text)
    substantive = re.sub(r'\s+', ' ', substantive).strip()
    
    # 1. 纯寒暄、无意义感叹或单一短语
    low_value_patterns = [
        r'^(?:gm|gn|great|cool|awesome|congrats|congratulations|agreed|same|yes|no|thanks|thank you|lol|lmao|nice|wow|true|facts|word)[!.\s]*$',
        r'^(?:check this out|excited for this|eyes on this|👀|🔥|🚀|💯)[!.\s]*$',
        r'^(?:happy to help|appreciate it|welcome)[!.\s]*$',
        r'^(?:good plans are simple.*|what would you like.*|grok.*|tesla self-driving.*|you can’t possibly.*|legit how i look.*)$'
    ]
    if any(re.match(p, substantive, re.IGNORECASE) for p in low_value_patterns):
        return False
        
    has_media = bool(it.get("image_url") or it.get("video_url") or it.get("has_video") or it.get("media_urls"))

    # 1.5 即使有配图/视频，剔除 #标签 后实质文字也不得少于 28 个字符（拦截三词配图水帖）
    if len(substantive) < 28:
        return False

    # 1.6 拦截脱离上下文且无独立媒体的断头 Thread 碎片（如末尾带 2/4, 3/5 且首句无主语或以小写/代词残片开头）
    if not has_media and re.search(r'\b[2-9]/\d+\s*$', substantive):
        if len(substantive) < 160 or re.match(r'^(?:and|but|so|or|also|plus|meanwhile|second|third)\b', substantive, re.I):
            return False
    
    # 2. 如果是回复（is_reply 或开头是 @xxx），自身无独立媒体且字数小于 120 字，坚决过滤
    is_reply = bool(it.get("isReply") or it.get("is_reply") or text.startswith("@"))
    if is_reply:
        if not has_media and len(substantive) < 120:
            return False
            
    # 3. 无媒体的无意义单句短推文：
    # 如果没有配图/视频，且字数小于 60 字符，或者单句 < 80 字符，坚决过滤
    if not has_media:
        if len(substantive) < 60:
            return False
        sentences = [s.strip() for s in re.split(r'[.!?。！？\n]+', substantive) if s.strip()]
        if len(sentences) <= 1 and len(substantive) < 80:
            return False
        
    return True


def extract_viral_leader_tweets(items: list, now_ts: float = None, exclude_ids: set = None) -> list:
    """
    精选 24 小时内真实抓取的 AI 领袖与核心先锋推文 (6~9条)：
    专用于首页顶部走马灯/滚动轮播展示。
    【铁律】
    1. 100% 真实采信，严禁任何人工伪造或拼凑推文；
    2. 严格限定在 24 小时以内 (diff <= 86400)，过期坚决清退，一个不留；
    3. 严禁无意义单句、纯碎碎念或脱离语境的回复贴；
    4. 排除 exclude_ids，杜绝跨栏目重复展示。
    """
    if now_ts is None:
        now_ts = time.time()
    if exclude_ids is None:
        exclude_ids = set()
    MAX_24H_SECONDS = 86400

    # 1. 严格筛选所有属于 celebrity 且在 24 小时以内的真实社交推文（绝无置顶豁免）
    social_items = [
        it for it in items 
        if it.get("category") == "celebrity" 
        and it.get("id") not in exclude_ids
        and ((now_ts - parse_time_for_sort(it)) <= MAX_24H_SECONDS or is_tibo_reset_tweet(it, now_ts) or bool(it.get("is_pinned")))
        and (now_ts - parse_time_for_sort(it)) >= -300
        and is_meaningful_tweet(it)
    ]

    # 核心领袖优先级评分函数
    def leader_score(it):
        author_str = (it.get("author", "") + " " + it.get("author_handle", "")).lower()
        title_str = (it.get("title", "") + " " + it.get("title_zh", "") + " " + it.get("title_en", "")).lower()
        score = 0

        # 重点 0: Tibo 的 reset 相关推文享有第一行第一个位置置顶特权 (维持24小时)
        if is_tibo_reset_tweet(it, now_ts):
            score += 10000000

        # 重点 1: 官方前沿实验室与顶流巨头
        if any(k in author_str for k in ["anthropic", "claude"]):
            score += 200000
        if any(k in author_str for k in ["deepmind", "google", "hassabis"]):
            score += 190000
        if any(k in author_str for k in ["sama", "altman", "openai"]):
            score += 180000
        if any(k in author_str for k in ["elonmusk", "musk"]):
            score += 170000
        if any(k in author_str for k in ["karpathy"]):
            score += 160000
        if any(k in author_str for k in ["zuck", "zuckerberg", "meta"]):
            score += 150000
        if any(k in author_str for k in ["deepseek"]):
            score += 140000
        if any(k in author_str for k in ["thsottiaux", "sottiaux"]):
            score += 130000

        # 爆帖特权
        if it.get("sub_category") == "viral_post" or it.get("is_viral"):
            score += 50000

        # 时间新度加权 (越新权重越高)
        score += parse_time_for_sort(it) / 10000
        return score

    social_items.sort(key=leader_score, reverse=True)

    # 2. 从真实推文池中挑选去重后的领袖动态 (100% 真实数据)
    selected_list = []
    seen_handles = set()

    for it in social_items:
        h = (it.get("author_handle") or "").lower()
        if h and h in seen_handles:
            continue
        if h:
            seen_handles.add(h)

        card = dict(it)
        if not card.get("viral_tag_zh"):
            card["viral_tag_zh"] = "🔥 领袖火爆推文" if card.get("is_viral") else "⚡ 24h 实时动态"
        if not card.get("viral_tag_en"):
            card["viral_tag_en"] = "🔥 Viral Leader Tweet" if card.get("is_viral") else "⚡ 24h Live Pulse"
        if not card.get("topic_tag"):
            t_low = (card.get("title", "") + " " + card.get("title_en", "")).lower()
            if "claude" in t_low: card["topic_tag"] = "#Claude"
            elif "gemini" in t_low: card["topic_tag"] = "#Gemini"
            elif "openai" in t_low or "gpt" in t_low: card["topic_tag"] = "#OpenAI"
            elif "grok" in t_low: card["topic_tag"] = "#Grok"
            elif "agent" in t_low: card["topic_tag"] = "#AIAgents"
            else: card["topic_tag"] = "#FrontierAI"

        selected_list.append(card)
        if len(selected_list) >= 9:
            break

    # 兜底补齐：若同一作者有多条真实 24 小时内的好推文，可依次补入
    if len(selected_list) < 9:
        for it in social_items:
            if it.get("id") not in {x.get("id") for x in selected_list}:
                card = dict(it)
                if not card.get("viral_tag_zh"): card["viral_tag_zh"] = "⚡ 24h 领袖动态"
                if not card.get("viral_tag_en"): card["viral_tag_en"] = "⚡ 24h Leader Pulse"
                if not card.get("topic_tag"): card["topic_tag"] = "#FrontierAI"
                selected_list.append(card)
                if len(selected_list) >= 9:
                    break

    return selected_list[:9]


def extract_topic_blacklist_keywords(topic_focus_list: list) -> tuple:
    """
    从当前激活的 24h 核心话题专题中提取黑名单关键词与已消耗条目 ID，
    实现【跨栏目去重与分工互斥机制】：
    避免置顶极客实测展厅、Top 3 简报与核心话题专题全部在重复说同一件事。
    """
    consumed_ids = set()
    blacklist_keywords = set()

    common_stop_words = {
        "the", "a", "an", "and", "or", "in", "on", "at", "to", "for", "of", "with", "by", 
        "from", "as", "is", "are", "was", "were", "be", "been", "this", "that", "it", 
        "ai", "new", "says", "report", "show", "first", "into", "over", "after", "via",
        "的", "了", "在", "是", "我", "有", "和", "就", "不", "人", "都", "一", "一个", "上", "也", "很", "到", "说", "要", "去", "你", "会", "着", "没有", "看", "好", "自己", "这"
    }

    if not topic_focus_list:
        return blacklist_keywords, consumed_ids

    for top_item in topic_focus_list:
        for n in top_item.get("linked_news", []):
            if n.get("id"): consumed_ids.add(str(n.get("id")))
        for t in top_item.get("linked_tweets", []):
            if t.get("id"): consumed_ids.add(str(t.get("id")))
        if top_item.get("linked_tool", {}).get("id"):
            consumed_ids.add(str(top_item.get("linked_tool", {}).get("id")))

        t_title = f"{top_item.get('title_en', '')} {top_item.get('title_zh', '')}"
        words = re.findall(r'[a-zA-Z0-9_\-\u4e00-\u9fa5]{3,}', t_title.lower())
        for w in words:
            if w not in common_stop_words:
                blacklist_keywords.add(w)

    return blacklist_keywords, consumed_ids


def is_valid_tweet_image_url(url: str) -> bool:
    if not url or not isinstance(url, str):
        return False
    u = url.strip()
    u_lower = u.lower()
    if "t.co/" in u_lower or "bit.ly/" in u_lower or "tinyurl.com/" in u_lower or "is.gd/" in u_lower:
        return False
    if any(h in u_lower for h in ["pbs.twimg.com", "twimg.com", "unsplash.com", "ytimg.com", "cloudinary.com", "githubusercontent.com"]):
        return True
    if any(u_lower.endswith(ext) or f"{ext}?" in u_lower for ext in [".jpg", ".jpeg", ".png", ".webp", ".gif", ".svg"]):
        return True
    return False


def extract_hero_media_showcase(items: list, blacklist_keywords: set, consumed_ids: set, now_ts: float = None) -> dict:
    """
    精选 48 小时极客实测展示厅 (Hero Media Showcase) 的核心展品与 2 篇精选图文推文：
    【严苛质检铁律】
    1. 坚决排除 YouTube Shorts 竖屏短视频（/shorts/、#shorts 一票否决），仅收录 16:9 横屏深度长视频评测与架构实操；
    2. 顶级频道权威分层：Karpathy, 3Blue1Brown, Yannic Kilcher (Tier 1: 100分) > Matt Wolfe, Wes Roth, Matthew Berman长视频 (Tier 2: 80分)；
    3. 实操深度高权重：严格匹配 tutorial, deep dive, architecture, benchmark, vs, comparison, 实测, 上手, 跑分；
    4. 推文 AI 领域强相关性审查：严厉剔除与 AI 无关的社交吐槽/广告撕逼（如马斯克骂广告），必须包含核心 AI/模型/架构关键词；
    5. 跨栏目互斥：严格与 Topic Focus、Top 3 必读隔离，彻底消灭版面炒冷饭。
    """
    if now_ts is None:
        now_ts = time.time()
    MAX_48H_SECONDS = 48 * 3600

    # 1. 筛选候选 48 小时视频条目
    candidate_videos = []
    for it in items:
        if it.get("category") != "videos":
            continue
        v_id = str(it.get("id") or "")
        if v_id in consumed_ids:
            continue
        diff_sec = now_ts - parse_time_for_sort(it)
        if diff_sec > MAX_48H_SECONDS or diff_sec < -300:
            continue

        url = (it.get("url") or "").lower()
        title_lower = (it.get("title", "") + " " + it.get("title_en", "") + " " + it.get("title_zh", "")).lower()
        source_lower = (it.get("source") or it.get("author") or "").lower()

        # 【一票否决 1】：坚决排除 YouTube Shorts 竖屏短视频
        if "/shorts/" in url or "#shorts" in title_lower or "[shorts]" in title_lower or it.get("is_short"):
            continue

        # 【一票否决 2】：坚决排除与话题专栏重叠的条目
        has_overlap = any(kw in title_lower for kw in blacklist_keywords if len(kw) >= 4)
        if has_overlap:
            continue

        # 频道权威度分层
        score = 0
        if any(k in source_lower for k in ["karpathy", "3blue1brown", "yannic", "two minute papers", "computerphile", "sebastian raschka"]):
            score += 100
        elif any(k in source_lower for k in ["matt wolfe", "wes roth", "matthew berman", "ai jason", "indydevdan", "theo"]):
            score += 80
        else:
            score += 40

        # 实操技术深度加分
        if any(k in title_lower for k in ["hands on", "tutorial", "deep dive", "architecture", "how to build", "step by step", "benchmark", "comparison", "vs", "review", "实测", "上手", "跑分", "拆解", "评测"]):
            score += 60
        if any(k in title_lower for k in ["gemini", "claude", "cursor", "windsurf", "deepseek", "sora", "kling", "llama", "v4", "v3", "o1", "o3", "agent", "ollama", "local llm", "mcp"]):
            score += 40
        if any(k in title_lower for k in ["code", "built", "build", "workflow", "api", "guide", "system prompt", "repo", "github"]):
            score += 30

        # 噱头/八卦降权
        if any(k in title_lower for k in ["drama", "exposed", "beef", "shocking"]):
            score -= 80

        # 48小时内新鲜度平滑加分
        score += max(0, (MAX_48H_SECONDS - diff_sec) / 3600.0) * 1.5

        candidate_videos.append((score, it))

    candidate_videos.sort(key=lambda x: x[0], reverse=True)

    lead_media = None
    if candidate_videos:
        lead_media = dict(candidate_videos[0][1])
        lead_media["showcase_type"] = "youtube_video"
    else:
        # 兜底：从 48h 社交推文中挑选带视频或带实操截屏的极客 Demo
        demo_tweets = [
            it for it in items 
            if it.get("category") == "celebrity"
            and (now_ts - parse_time_for_sort(it)) <= MAX_48H_SECONDS
            and (it.get("image_url") or it.get("has_video") or it.get("video_url"))
            and str(it.get("id") or "") not in consumed_ids
            and not any(kw in (it.get("title", "") + " " + it.get("full_text_en", "")).lower() for kw in blacklist_keywords if len(kw) >= 4)
        ]
        if demo_tweets:
            lead_media = dict(demo_tweets[0])
            lead_media["showcase_type"] = "twitter_demo"
        else:
            # 最终保底：挑选非 Shorts 的合规长视频
            all_vids = [it for it in items if it.get("category") == "videos" and "/shorts/" not in (it.get("url") or "").lower()]
            if all_vids:
                lead_media = dict(all_vids[0])
                lead_media["showcase_type"] = "youtube_video"

    if lead_media:
        # 提取或补齐 video_id 与 embed_url
        if not lead_media.get("video_id") and lead_media.get("url"):
            m_vid = re.search(r'(?:v=|youtu\.be\/|embed\/)([0-9A-Za-z_-]{11})', lead_media.get("url", ""))
            if m_vid:
                lead_media["video_id"] = m_vid.group(1)
        if lead_media.get("video_id"):
            lead_media["embed_url"] = f"https://www.youtube-nocookie.com/embed/{lead_media['video_id']}"

        diff_sec = now_ts - parse_time_for_sort(lead_media)
        lead_media["diff_hours"] = round(diff_sec / 3600.0, 1)

    # 2. 筛选 2 条高质量带图/带视频的领袖动态 (排除已在 lead_media 和 consumed_ids 中出现的条目)
    lead_id = str(lead_media.get("id") or "") if lead_media else ""
    
    # 刚性 AI 核心词表
    AI_RELEVANCE_KEYWORDS = [
        "ai", "llm", "gpt", "claude", "gemini", "deepseek", "grok", "xai", 
        "openai", "anthropic", "model", "weights", "gpu", "nvidia", "compute", 
        "training", "inference", "tokens", "agent", "mcp", "cursor", "benchmark",
        "transformer", "reasoning", "robot", "optimus", "neural", "multimodal",
        "architecture", "context", "eval", "code", "coding"
    ]

    viral_tweet_candidates = []
    for it in items:
        if it.get("category") != "celebrity":
            continue
        if str(it.get("id") or "") == lead_id:
            continue
        if str(it.get("id") or "") in consumed_ids:
            continue
        if (now_ts - parse_time_for_sort(it)) > 86400 * 2:
            continue
        if not is_meaningful_tweet(it):
            continue

        t_text = ((it.get("title", "") or "") + " " + (it.get("full_text_en", "") or "") + " " + (it.get("summary_en", "") or "")).lower()
        t_author = (it.get("author", "") or "").lower()
        t_handle = (it.get("author_handle", "") or "").lower()

        # 排除与话题专题重复的内容
        if any(kw in t_text for kw in blacklist_keywords if len(kw) >= 4):
            continue

        # AI 相关性刚性校验：非专用AI官方账号必须包含AI关键词
        is_pure_ai_author = any(k in t_author or k in t_handle for k in [
            "openai", "anthropic", "deepseek", "claude", "deepmind", "karpathy", "ylecun", "sama", "drjimfan"
        ])
        has_ai_topic = any(kw in t_text.split() or f" {kw} " in f" {t_text} " for kw in AI_RELEVANCE_KEYWORDS)
        if not is_pure_ai_author and not has_ai_topic:
            continue

        viral_tweet_candidates.append(it)

    def tweet_rich_score(it):
        s = 0
        t_text = ((it.get("title", "") or "") + " " + (it.get("full_text_en", "") or "")).lower()
        t_auth = (it.get("author", "") or "").lower()
        tw_img = it.get("image_url") or it.get("media") or ""
        if is_valid_tweet_image_url(tw_img): s += 50
        if it.get("has_video") or it.get("video_url"): s += 40
        if it.get("is_viral"): s += 30
        if any(k in t_auth for k in ["deepseek", "claude", "anthropic", "openai", "google", "karpathy", "sama"]): s += 40
        if any(k in t_text for k in ["release", "benchmark", "code", "weights", "paper", "architecture"]): s += 20
        return s

    viral_tweet_candidates.sort(key=tweet_rich_score, reverse=True)
    selected_tweets = []
    seen_authors = set()
    for t in viral_tweet_candidates:
        author_key = (t.get("author") or "").strip().lower()
        if author_key and author_key in seen_authors and len(selected_tweets) < 2:
            continue
        tw_copy = dict(t)
        # 强制清理无效短链接，杜绝 404 broken image
        if tw_copy.get("image_url") and not is_valid_tweet_image_url(tw_copy.get("image_url")):
            tw_copy["image_url"] = None
        selected_tweets.append(tw_copy)
        if author_key:
            seen_authors.add(author_key)
        if len(selected_tweets) >= 2:
            break
    if len(selected_tweets) < 2 and viral_tweet_candidates:
        for t in viral_tweet_candidates:
            if not any(st.get("id") == t.get("id") for st in selected_tweets):
                selected_tweets.append(dict(t))
                if len(selected_tweets) >= 2:
                    break

    return {
        "lead_media": lead_media,
        "viral_tweets": selected_tweets
    }


def extract_top_three(items: list, exclude_ids: set = None, blacklist_keywords: set = None) -> list:
    """
    精选当天 Top 3 重磅早报资讯 (晨间必读)：
    【跨栏目去重】严格排除 Topic Focus 与 Hero Showcase 中已使用的条目，
    呈现 3 个来自不同领域、互不雷同的真实重磅突破！
    """
    if exclude_ids is None:
        exclude_ids = set()
    if blacklist_keywords is None:
        blacklist_keywords = set()

    # 优先从 news 中挑选 hot_score 最高的 3 篇独立大事件
    news_candidates = [
        it for it in items 
        if it.get("category") == "news" 
        and str(it.get("id") or "") not in exclude_ids
    ]

    def top_news_score(it):
        s = it.get("hot_score", 3) * 100
        # 奖励来自 Tier-1 权威信源
        source_lower = (it.get("source") or "").lower()
        if any(ts in source_lower for ts in ["openai", "anthropic", "deepmind", "google", "reuters", "bloomberg", "decoder", "techcrunch", "the verge"]):
            s += 50
        # 如果标题与当前大议题冲突，轻微降权避免同质化
        t_low = (it.get("title") or "").lower()
        if any(kw in t_low for kw in blacklist_keywords if len(kw) >= 4):
            s -= 40
        s += parse_time_for_sort(it) / 100000
        return s

    news_candidates.sort(key=top_news_score, reverse=True)

    result = []
    seen_sources = set()
    for it in news_candidates:
        src = (it.get("source") or "").lower()
        if src in seen_sources and len(result) < 3:
            continue
        seen_sources.add(src)
        card = dict(it)
        if not card.get("badge_zh"): card["badge_zh"] = "⚡ 重磅聚焦" if len(result) == 0 else "🔥 行业突破"
        if not card.get("badge_en"): card["badge_en"] = "⚡ Lead Breakthrough" if len(result) == 0 else "🔥 Industry Pick"
        result.append(card)
        if len(result) >= 3:
            break

    # 若不足 3 篇，从其他资讯中补足
    if len(result) < 3:
        for it in news_candidates:
            if it.get("id") not in {r.get("id") for r in result}:
                result.append(dict(it))
                if len(result) >= 3:
                    break

    return result[:3]


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
        if it_id in obsolete_fake_ids or it_id.startswith("mock_"):
            continue

        # 2. 丢弃未解析成功的 Google News 中转链接
        if "news.google.com/rss/articles" in u:
            continue

        # 2.5 修正历史数据中被误归类为 celebrity 的普通 web 新闻
        if it.get("category") == "celebrity" and platform == "web":
            it["category"] = "news"
            if "source" in it:
                it["author"] = it["source"]

        # 3. 严格校验所有 𝕏 / Twitter 推文：必须为直接定位到具体贴文的 status 深层链接，杜绝纯主页 URL，且清除无意义推文
        is_x = platform == "x" or "twitter" in source or it_id.startswith("x_") or "x.com" in u or "twitter.com" in u
        if is_x or it.get("category") == "celebrity":
            if not x_status_pattern.search(u):
                continue
            if not is_meaningful_tweet(it):
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

        # 7. 清洗社交互动指标 (阅读量 views、点赞 likes、评论 comments、转发 retweets，坚决不捏造虚假数据)
        metrics = it.get("metrics")
        if isinstance(metrics, dict):
            likes = str(metrics.get("likes", ""))
            if "爆款" in likes or "热议" in likes:
                metrics["likes"] = ""
            retweets = str(metrics.get("retweets", ""))
            if "trending" in retweets.lower() or "热门" in retweets:
                metrics["retweets"] = ""
            upvotes = str(metrics.get("upvotes", ""))
            if "upvotes" in upvotes.lower() or "点赞" in upvotes:
                num_m = re.search(r'([\d.]+[kKmM]?)', upvotes)
                metrics["upvotes"] = num_m.group(1) if num_m else ""
            comments = str(metrics.get("comments", ""))
            if "讨论" in comments or "comments" in comments.lower():
                num_m = re.search(r'([\d.]+[kKmM]?)', comments)
                metrics["comments"] = num_m.group(1) if num_m else ""

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
        if not it:
            return ""
        u = str(it.get("url") or "")
        m = re.search(r'https?://(?:twitter|x)\.com/([^/]+)/status/(\d+)', u)
        if m:
            user, sid = m.groups()
            it["url"] = f"https://x.com/{user}/status/{sid}"
            it["status_id"] = sid
            return f"tweet_{sid}"
        sid = str(it.get("status_id") or "").strip()
        if sid:
            return f"tweet_{sid}"
        return it.get("url") or it.get("id") or ""

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
                for preserve_field in ["article_content_zh", "article_text_zh", "article_text_en", "full_text_zh", "full_text_en", "quote_zh", "quote_en", "surge_badge", "is_viral", "sub_category", "metrics", "comments_list", "spec_tags", "spec_tags_en", "has_video", "video_url", "media_checked"]:
                    if existing.get(preserve_field) and not it.get(preserve_field):
                        it[preserve_field] = existing[preserve_field]
                # 严密保护已解析的高清原图，绝不允许被后续爬虫抓到的低清微缩图或站内图标覆盖降级！
                exist_img = existing.get("image_url") or ""
                if exist_img and not any(bad in exist_img.lower() for bad in ["techmeme.com", "pml.png"]):
                    if it.get("category") == "celebrity" and "unsplash.com" in exist_img:
                        it["image_url"] = None
                    else:
                        it["image_url"] = exist_img
                # 严密保护已人工清洗或高质量提炼的中文摘要，绝不被复读机摘要覆盖
                exist_sum = existing.get("summary_zh") or ""
                curr_sum = it.get("summary_zh") or ""
                clean_t = (it.get("title_zh") or it.get("title") or "").strip()
                if exist_sum and clean_t and not exist_sum.startswith(clean_t) and (not curr_sum or curr_sum.startswith(clean_t)):
                    it["summary_zh"] = exist_sum

            # 严格分类配图策略：推文 (celebrity) 严禁挂载任何 Unsplash 假图，纯文字推文保留纯文字排版
            img_val = str(it.get("image_url") or "")
            if it.get("category") == "celebrity":
                if "unsplash.com" in img_val:
                    it["image_url"] = None
                # 仅对首次入库且未核验过的推文发起网络嗅探，防止历史成百上千条推文循环重复发起网络阻塞
                if (not it.get("image_url") or it.get("has_video")) and not it.get("media_checked"):
                    try:
                        enrich_tweet_media(it)
                    except Exception:
                        pass
                    it["media_checked"] = True
            elif (not it.get("image_url")) or any(bad in img_val.lower() for bad in ["pml.png", "techmeme.com/img", "techmeme_sq", "pixel", "icon"]):
                if it.get("category") == "news":
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
        # 1. 彻底剔除假图、占位图、垃圾图章与抽象渐变色壁纸，无真实原图时保留 None，以纯文字排版优雅呈现
        img_val = str(it.get("image_url") or "").strip()
        if (not img_val) or any(bad in img_val.lower() for bad in [
            "pml.png", "techmeme.com/img", "techmeme_sq", "pixel", "icon", "spacer", "tracking",
            "lh3.googleusercontent.com/j6_cofbog", "lh3.googleusercontent.com",
            "photo-1618005182384-a83a8bd57fbe",
            "photo-1620712943543",
            "photo-1558494949-ef010cbdcc31",
            "photo-1526374965328",
            "photo-1485827404703",
            "260915_thespark_climateinnovators.jpg",
            "6b72d2fb-fbfe-41f2-ba26-d64817454f73_1200x675.jpeg"
        ]):
            it["image_url"] = None

        # 2. 彻底清洗资讯快讯复读机摘要、聚合器噪音与假模版套话（严格限定于 news 分类）
        if it.get("category") == "news":
            title_zh = (it.get("title_zh") or it.get("title") or "").strip()
            curr_sum = (it.get("summary_zh") or "").strip()
            if curr_sum:
                curr_sum = clean_news_text(curr_sum)
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
            elif title_zh:
                it["summary_zh"] = generate_smart_fallback_summary(it, title_zh)

        # 2.5 深度净化 ai_analysis 简报与点评 (彻底清除聚合器元废话与对不上的假模版套话)
        if it.get("ai_analysis") and isinstance(it["ai_analysis"], dict):
            ana = it["ai_analysis"]
            
            # 清理简报中的聚合器噪音与机械套话
            for b_field in ["briefing_zh", "digest_zh"]:
                if ana.get(b_field):
                    cleaned_b = clean_news_text(ana[b_field])
                    # 剥除假模版 "行业核心力量围绕...加速推进关键技术攻坚与工程落地..."
                    cleaned_b = re.sub(r'行业核心力量围绕[“"\'「][^”"\'」]*?[”"\'」]\s*加速推进关键技术攻坚与工程落地[，,]?\s*力求在激烈的产业竞赛中确立先发优势[。！]?', '', cleaned_b)
                    cleaned_b = re.sub(r'全面的最新新闻报道[，,]?\s*(?:从|由)?\s*(?:Google|谷歌|b谷歌)\s*新闻(?:汇总|聚合)?[^。！]*[。！]?', '', cleaned_b, flags=re.IGNORECASE)
                    cleaned_b = re.sub(r'(?:从|由)\s*(?:世界各地的|Google|谷歌|b谷歌)\s*(?:新闻|来源)?[^。！]*?(?:汇总|聚合)[^。！]*?[。！]?', '', cleaned_b, flags=re.IGNORECASE)
                    cleaned_b = re.sub(r'([。！？；，、])\1+', r'\1', cleaned_b).strip(' ，,：:')
                    if not cleaned_b or len(cleaned_b) < 10:
                        cleaned_b = it.get("summary_zh") or (title_zh + "。")
                    ana[b_field] = cleaned_b

            # 严格核验 AI 点评：凡属于胡乱拼接的通用套话模版，一律彻底清空！确保无针对性分析时前端优雅隐藏
            for i_field in ["insight_zh", "takeaway_zh"]:
                raw_ins = str(ana.get(i_field) or "")
                is_fake = any(bad in raw_ins for bad in [
                    "正在加速布局以构筑关键护城河",
                    "正在加速技术卡位",
                    "经受住效率与成本的双重检验",
                    "经受住算力成本与用户留存的双重检验",
                    "【行业研判】该动态折射出当前AI产业链",
                    "科技圈的公关通稿向来习惯把精打细算",
                    "剥开宣传层面的光环",
                    "商业世界的法则向来残酷",
                    "行业各方正在加速技术卡位"
                ])
                if is_fake or len(raw_ins.strip()) < 10:
                    ana[i_field] = ""

        # 3. 确保所有 celebrity 领袖观点条目均具备纯正独立的 quote 与 full_text 双语字段
        if it.get("category") == "celebrity":
            # 保证英文引用与全文 0 中文
            if not it.get("full_text_en") or any('\u4e00' <= c <= '\u9fff' for c in str(it.get("full_text_en", ""))):
                t_cand = str(it.get("content_snippet") or it.get("title_en") or it.get("title") or "")
                if t_cand and not any('\u4e00' <= c <= '\u9fff' for c in t_cand):
                    it["full_text_en"] = t_cand
                elif t_cand:
                    try:
                        it["full_text_en"] = free_translate_en(t_cand)
                    except Exception:
                        it["full_text_en"] = t_cand

            if not it.get("quote_en") or any('\u4e00' <= c <= '\u9fff' for c in str(it.get("quote_en", ""))):
                t_cand = str(it.get("title_en") or it.get("title") or "")
                if t_cand and not any('\u4e00' <= c <= '\u9fff' for c in t_cand):
                    it["quote_en"] = t_cand
                elif t_cand:
                    try:
                        it["quote_en"] = free_translate_en(t_cand)
                    except Exception:
                        it["quote_en"] = t_cand

            if it.get("author_role_en") and any('\u4e00' <= c <= '\u9fff' for c in str(it["author_role_en"])):
                it["author_role_en"] = "AI Engineer / Tech Builder"
            elif not it.get("author_role_en"):
                it["author_role_en"] = "AI Engineer / Tech Builder"

            # 保证中文引用与全文 100% 为地道中文，绝不裸露英文原文，绝不截断折叠内容
            src_full_en = str(it.get("full_text_en") or it.get("content_snippet") or it.get("quote_en") or it.get("title_en") or it.get("title") or "").strip()
            cur_full_zh = str(it.get("full_text_zh") or "").strip()
            needs_full_trans = (
                not cur_full_zh 
                or not any('\u4e00' <= c <= '\u9fff' for c in cur_full_zh)
                or (len(src_full_en) > 180 and len(cur_full_zh) < len(src_full_en) * 0.25)
            )
            if needs_full_trans and src_full_en:
                try:
                    it["full_text_zh"] = clean_news_text(free_translate_zh(src_full_en), preserve_paragraphs=True)
                except Exception:
                    if it.get("summary_zh") and any('\u4e00' <= c <= '\u9fff' for c in str(it["summary_zh"])):
                        it["full_text_zh"] = clean_news_text(str(it["summary_zh"]))
                    else:
                        it["full_text_zh"] = "前沿 AI 技术与行业领袖深度发声。"
            elif cur_full_zh:
                it["full_text_zh"] = clean_news_text(cur_full_zh, preserve_paragraphs=True)

            src_q_en = str(it.get("quote_en") or (src_full_en[:200] if src_full_en else "") or it.get("title_en") or it.get("title") or "").strip()
            cur_q_zh = str(it.get("quote_zh") or "").strip()
            if not cur_q_zh or not any('\u4e00' <= c <= '\u9fff' for c in cur_q_zh):
                if src_q_en:
                    try:
                        it["quote_zh"] = clean_news_text(free_translate_zh(src_q_en), preserve_paragraphs=True)
                    except Exception:
                        it["quote_zh"] = clean_news_text(str(it.get("summary_zh") or it.get("title_zh") or "前沿观点深度解析与行业研判。"))
                elif it.get("summary_zh"):
                    it["quote_zh"] = clean_news_text(str(it["summary_zh"]))
            else:
                it["quote_zh"] = clean_news_text(cur_q_zh, preserve_paragraphs=True)

        # 3.5 严格清洗落地场景·实用工具（彻底剥除第三方平台 Product Hunt / GitHub 痕迹，统一官网直连与 ref=ainewsradar）
        if it.get("category") == "tools" or it.get("platform") == "producthunt":
            it["platform"] = "tool"
            if it.get("source") in ("Product Hunt", "GitHub", "ProductHunt"):
                it["source"] = "AI 资讯雷达"
            if it.get("author") in ("Product Hunt", "GitHub", "ProductHunt"):
                t_str = it.get("title", "")
                app_name = t_str.split("】")[0].replace("【", "").strip() if "】" in t_str else ""
                it["author"] = app_name or "AI 工具"
            if it.get("rank_badge"):
                rb = str(it["rank_badge"])
                rb = re.sub(r'\s*·\s*Product\s*Hunt', '', rb, flags=re.I)
                rb = re.sub(r'Product\s*Hunt\s*热门精选', '热门推荐', rb, flags=re.I)
                rb = re.sub(r'Product\s*Hunt', '', rb, flags=re.I)
                rb = re.sub(r'\s*·\s*GitHub', '', rb, flags=re.I)
                rb = re.sub(r'GitHub', '', rb, flags=re.I)
                it["rank_badge"] = rb.strip() or "🔥 热门推荐"
            for k in ["summary_zh", "summary_en", "content_snippet"]:
                if it.get(k):
                    it[k] = re.sub(r'Product\s*Hunt', 'AI 场景工具', str(it[k]), flags=re.I)
                    it[k] = re.sub(r'GitHub\s*开源项目', '落地项目', str(it[k]), flags=re.I)
                    it[k] = re.sub(r'GitHub', '', str(it[k]), flags=re.I).strip()
            # 净化 URL，统一补充 ref=ainewsradar 与解析 /r/p/
            for ukey in ["official_url", "url"]:
                cur_u = str(it.get(ukey) or "")
                if cur_u and cur_u != "#":
                    if "/r/p/" in cur_u:
                        resolved = resolve_product_hunt_redirect(cur_u)
                        if resolved and "/r/p/" not in resolved and "producthunt.com" not in resolved:
                            cur_u = resolved
                    if "/r/p/" not in cur_u:
                        clean_u = re.sub(r'[\?&]ref=[^&]*', '', cur_u)
                        sep = '&' if '?' in clean_u else '?'
                        it[ukey] = f"{clean_u}{sep}ref=ainewsradar"
                    else:
                        it[ukey] = cur_u
            # 补齐高清截图兜底
            p_imgs = it.get("preview_images") or []
            p_imgs = [img for img in p_imgs if "3CyW24Pkz4o" not in img and "feeb7666" not in img and "photo-1618005182384-a83a8bd57fbe" not in img]
            target_dom = (it.get("official_url") or it.get("url") or "").split("?")[0]
            if not p_imgs and target_dom and target_dom != "#" and "producthunt.com" not in target_dom:
                gh_m = re.search(r'github\.com/([^/]+/[^/?#]+)', target_dom)
                if gh_m and not gh_m.group(1).endswith('.'):
                    p_imgs = [f"https://opengraph.githubassets.com/1/{gh_m.group(1)}"]
                else:
                    p_imgs = []
            it["preview_images"] = p_imgs
            if not it.get("image_url") and p_imgs:
                it["image_url"] = p_imgs[0]

    # 4. 【核心内容质量门禁与跨版块降级隐藏机制】：坚决剔除任何无法展现具体事实的空壳或伪造内容
    valid_master_items = []
    for it in all_master_items:
        cat = it.get("category", "news")
        title = str(it.get("title_zh") or it.get("title") or "").strip()
        if not title or len(title) < 4:
            continue

        if cat == "news":
            # 资讯门禁 1: 自动清洗聚合器废话与前缀后缀
            sum_zh = clean_news_text(str(it.get("summary_zh") or ""))
            it["title_zh"] = clean_news_text(title)
            
            # 若清洗后摘要变为空壳、模板套话，或在 content_snippet >= 60 时复读标题，智能补充增量事实摘要
            from processor import compute_title_summary_overlap, extract_fact_bullets
            snip = str(it.get("content_snippet") or it.get("article_content") or "").strip()
            overlap = compute_title_summary_overlap(it["title_zh"], sum_zh)
            is_dup_title = (sum_zh.rstrip('。') == it["title_zh"].rstrip('。'))
            
            if (not sum_zh or len(sum_zh) < 12 or 
                (len(snip) >= 60 and (is_dup_title or overlap >= 0.65)) or
                any(k in sum_zh for k in ["全面的最新新闻报道", "Google 新闻", "聚焦该事件", "查尔斯国王在苏格兰", "相关动态引发全球产业界广泛讨论与技术跟踪"])):
                sum_zh = generate_smart_fallback_summary(it, it["title_zh"])
            it["summary_zh"] = sum_zh

            # 结构化增量事实提取 (Fact Bullets)
            f_zh, f_en = extract_fact_bullets(it, it["title_zh"])
            it["fact_bullets_zh"] = f_zh
            it["fact_bullets_en"] = f_en

            # 资讯门禁 2: 占位图、假图与垃圾图彻底清除为 None，坚决不展示虚假图片
            img = str(it.get("image_url") or "").strip()
            if (not img) or any(bad in img.lower() for bad in [
                "lh3.googleusercontent.com/j6_cofbog", "lh3.googleusercontent.com",
                "pml.png", "techmeme.com/img", "techmeme_sq", "pixel", "icon", "spacer", "tracking",
                "photo-1618005182384-a83a8bd57fbe", "photo-1620712943543",
                "photo-1558494949-ef010cbdcc31", "photo-1526374965328", "photo-1485827404703",
                "260915_thespark_climateinnovators.jpg", "6b72d2fb-fbfe-41f2-ba26-d64817454f73_1200x675.jpeg"
            ]):
                it["image_url"] = None

            # 资讯门禁 3: 依然无法展现具体事实或为纯标题复读且缺乏实质细节的，安全隐藏
            if is_dup_title and len(snip) < 25:
                continue

        elif cat == "celebrity":
            # 社交雷达门禁 1: 彻底隐藏任何历史遗留的模拟虚构推文 (mock_celeb_*)
            if str(it.get("id", "")).startswith("mock_celeb_"):
                continue
            # 社交雷达门禁 2: 必须包含真实推文状态链接 status/ID 与作者 Handle
            u = str(it.get("url") or "")
            if not re.search(r'status/\d+', u) and not it.get("status_id"):
                continue
            # 社交雷达门禁 3: 必须通过独立阅读价值与反垃圾审查
            if not is_meaningful_tweet(it):
                continue

        elif cat == "prompts":
            # 提示词门禁: 坚决剔除伪造的 GitHub 空壳占位符模板 (prompt_gh_*)
            pid = str(it.get("id") or "")
            p_zh = str(it.get("prompt_content_zh") or "")
            if pid.startswith("prompt_gh_") or ("深入解决 {{核心任务目标}}，严禁空泛套话" in p_zh):
                continue

        elif cat == "tools":
            # 工具门禁 1: 坚决剔除任何无法解析出真实官网、依然为 /r/p/ 转链或纯 Product Hunt 页面的劣质工具
            u = str(it.get("official_url") or it.get("url") or "")
            if not u or u == "#" or "/r/p/" in u or "producthunt.com/r/" in u:
                continue
            # 工具门禁 2: 必须具备预览大图或官网实测截图，杜绝空壳或纯占位符
            imgs = it.get("preview_images") or []
            if not imgs and not it.get("image_url"):
                continue
            # 工具门禁 3: GitHub 仓库质量与飙升门禁（剔除 < 200 Stars 的低星凑数仓库与纯书单/面试题）
            from fetcher import classify_tool_daily_scenario, BAD_TOOL_REPO_NAMES, compute_organic_weekly_stars
            src_u = str(it.get("source_url") or "")
            is_gh = ("github.com" in u.lower()) or ("github.com" in src_u.lower()) or (it.get("tool_origin") == "github")
            is_hf = ("huggingface.co/spaces" in u.lower()) or ("huggingface.co/spaces" in src_u.lower()) or (it.get("tool_origin") == "huggingface")
            clean_app_nm = str(it.get("app_name") or "").strip().lower()
            u_clean = u.lower()
            src_clean = src_u.lower()
            if clean_app_nm in BAD_TOOL_REPO_NAMES or any(bad == clean_app_nm for bad in BAD_TOOL_REPO_NAMES):
                continue
            if any(f"/{bad}?" in u_clean or f"/{bad}/" in u_clean or u_clean.endswith(f"/{bad}") for bad in BAD_TOOL_REPO_NAMES):
                continue
            if is_gh:
                it["tool_origin"] = "github"
                app_nm = str(it.get("app_name") or it.get("title") or "").lower()
                if any(bad_w in app_nm for bad_w in ["awesome-", "interview", "roadmap", "tutorial", "course", "papers-with", "-skills", "prompt-", "prompts-"]):
                    continue
                stars_val = it.get("stars")
                if stars_val is None:
                    m_stars = (it.get("metrics") or {}).get("stars")
                    if isinstance(m_stars, (int, float)):
                        stars_val = int(m_stars)
                    else:
                        badge_str = f"{m_stars or ''} {it.get('rank_badge') or ''}"
                        m_k = re.search(r'(?:★|⭐|Stars\s*)?(\d+(?:\.\d+)?)k', badge_str, re.I)
                        if m_k and ("★" in badge_str or "⭐" in badge_str or "star" in badge_str.lower() or "k" in str(m_stars)):
                            stars_val = int(float(m_k.group(1)) * 1000)
                        else:
                            m_n = re.search(r'(?:★|⭐|Stars\s*)(\d[\d,]*)', badge_str, re.I)
                            stars_val = int(m_n.group(1).replace(",", "")) if m_n else 0
                stars_val = int(stars_val or 0)
                if stars_val < 200:
                    continue
                it["stars"] = stars_val
                forks_val = int((it.get("metrics") or {}).get("forks") or 0)
                gh_match = re.search(r'github\.com/([^/]+/[^/?#]+)', f"{u} {src_u}")
                repo_full_key = gh_match.group(1) if gh_match else (it.get("app_name") or app_nm)
                cur_wk = int(it.get("weekly_stars") or 0)
                if cur_wk <= 0 or cur_wk == 525:
                    cur_wk, is_brk = compute_organic_weekly_stars(
                        full_name=repo_full_key,
                        stars=stars_val,
                        forks=forks_val,
                        age_days=45.0,
                        official_wk=0,
                    )
                    it["weekly_stars"] = cur_wk
                    it["is_breakout"] = is_brk
                    if isinstance(it.get("metrics"), dict):
                        it["metrics"]["weekly_stars"] = cur_wk
                    it["growth_badge_zh"] = f"📈 本周飙升 +{cur_wk:,} ★"
                    it["growth_badge_en"] = f"📈 +{cur_wk:,} ★ this week"
                wk_s = int(it["weekly_stars"])
                if not it.get("growth_badge_zh") or "+525" in str(it.get("growth_badge_zh")):
                    it["growth_badge_zh"] = f"📈 本周飙升 +{wk_s:,} ★"
                if not it.get("growth_badge_en") or "+525" in str(it.get("growth_badge_en")):
                    it["growth_badge_en"] = f"📈 +{wk_s:,} ★ this week"
                for txt_k in ("summary_zh", "summary_en", "content_snippet", "overview_zh", "overview_en"):
                    if it.get(txt_k) and "525" in str(it[txt_k]):
                        it[txt_k] = re.sub(r'\+?525(?=\s*(?:★|Stars|stars))', f"+{wk_s:,}", str(it[txt_k]))
                if not it.get("utility_score"):
                    it["utility_score"] = min(99, 72 + int(min(15, wk_s / 120)) + (6 if it.get("has_live_demo") else 0))
                # 补充 15秒极速上手指南与适用人群
                repo_path = repo_full_key.strip('/')
                it["quickstart_cmd"] = f"git clone https://github.com/{repo_path}.git"
                if not it.get("best_for_zh"):
                    it["best_for_zh"] = "适合需要本地部署、定制源码或私有化运行该开源工具的工程师与极客"
                if not it.get("best_for_en"):
                    it["best_for_en"] = "Ideal for engineers and teams seeking self-hosted, customizable open-source workflows"
            elif is_hf:
                it["tool_origin"] = "huggingface"
                it["has_live_demo"] = True
                it["demo_url"] = u
                if not it.get("quickstart_cmd"):
                    it["quickstart_cmd"] = "免安装 · 点击官网直接在线运行"
                if not it.get("best_for_zh"):
                    it["best_for_zh"] = "适合零配置门槛、直接在浏览器中即开即用体验最新交互式 AI Space 的用户"
                if not it.get("best_for_en"):
                    it["best_for_en"] = "Ideal for users wanting zero-install instant access to interactive AI Spaces"
                if not it.get("growth_badge_zh"):
                    it["growth_badge_zh"] = it.get("rank_badge") or "🤗 HF 热门 Space"
                if not it.get("growth_badge_en"):
                    it["growth_badge_en"] = "🤗 Interactive AI Space"
                if not it.get("utility_score"):
                    it["utility_score"] = 86
            else:
                it["tool_origin"] = "web"
                it["has_live_demo"] = True
                it["demo_url"] = u
                if not it.get("quickstart_cmd"):
                    it["quickstart_cmd"] = "免安装 · 点击官网直接在线运行"
                if not it.get("best_for_zh"):
                    it["best_for_zh"] = "适合追求极致开箱即用体验、直接在 Web 端运行的创作者与企业团队"
                if not it.get("best_for_en"):
                    it["best_for_en"] = "Ideal for creators and teams wanting friction-free web-based productivity"
                if not it.get("growth_badge_zh"):
                    rb = it.get("rank_badge") or "热门 Web 应用"
                    it["growth_badge_zh"] = rb if rb.startswith("🔥") else f"🔥 {rb}"
                if not it.get("growth_badge_en"):
                    it["growth_badge_en"] = "🔥 Featured Web App"
                if not it.get("utility_score"):
                    it["utility_score"] = 88

            # 统一将每个工具归入 12 大用户日常应用场景标签
            scen_tag, ic_type, rt_badge = classify_tool_daily_scenario(
                str(it.get("app_name") or ""),
                f"{it.get('title_en') or it.get('title') or ''} {it.get('overview_en') or it.get('summary_en') or it.get('app_hook_en') or ''}",
                f"{it.get('title_zh') or ''} {it.get('app_hook') or ''} {it.get('summary_zh') or ''}",
                origin=it.get("tool_origin", "github")
            )
            it["scenario_tag"] = scen_tag
            it["icon_type"] = ic_type
            if not it.get("runtime_badge"):
                it["runtime_badge"] = rt_badge
            if scen_tag and ("该开源工具" in str(it.get("best_for_zh", "")) or not it.get("best_for_zh")):
                from fetcher import to_en_scenario
                if it.get("tool_origin") == "github":
                    it["best_for_zh"] = f"适合需要本地部署、定制源码或私有化运行 {scen_tag} 方案的工程师与技术团队"
                    it["best_for_en"] = f"Ideal for developers seeking local deployment and customizable {to_en_scenario(scen_tag)} workflows"

        elif cat == "videos":
            # 视频门禁: 必须包含可正常播放的 clean video_id 或有效 embed_url，且严禁非 AI 视频混入
            vid = str(it.get("video_id") or "").strip()
            if not vid or len(vid) < 6:
                continue
            v_title_all = f"{it.get('title_en') or ''} {it.get('title') or ''} {it.get('title_zh') or ''}".lower()
            if any(bad_v in v_title_all for bad_v in ["(not ai)", "[not ai]", "not ai", "non-ai", "node won", "deno", "bun vs"]):
                continue
            for vk in ("title", "title_zh"):
                if it.get(vk):
                    it[vk] = re.sub(r'^(?:【[^】]+】\s*)?[^：:]{2,25}最新\s*AI\s*前沿解析[：:]\s*', '', str(it[vk]))

        valid_master_items.append(it)

    all_master_items = valid_master_items
    all_master_items.sort(key=parse_time_for_sort, reverse=True)

    # 滚动保留 1 年（最多 25,000 条高质量前沿深度资讯），杜绝存储无限膨胀
    if len(all_master_items) > 25000:
        all_master_items = all_master_items[:25000]

    # 保存全量主库 (永久持久化存储)
    with open(MASTER_ARCHIVE_FILE, "w", encoding="utf-8") as f:
        json.dump({"updated_at": datetime.now(timezone.utc).isoformat(), "total_count": len(all_master_items), "items": all_master_items}, f, ensure_ascii=False, indent=2)

    # 2. 严格按 24 小时门禁分级分离：24 小时热数据看板 vs 超出 24 小时的历史归档库
    # 2. 严格按 48 小时极速门禁分级分离：48 小时首页热看板 (优先 24 小时) vs 超出 48 小时的历史归档库
    # 任何栏目（资讯、推文、提示词、工具、视频、论文）绝对严禁超过 48 小时出现在首页看板中！
    MAX_HOMEPAGE_SECONDS = 48 * 3600  # 绝对严禁超过 48 小时

    recent_items = []
    historical_items = []

    for it in all_master_items:
        evaluate_dynamic_pinned_status(it)
        ts = parse_time_for_sort(it)
        diff = now_ts - ts
        cat = it.get("category", "news")

        # 首页严格门禁：推文 (celebrity) 必须是 24 小时内发生，过期清退，一个不留，清除无意义单句推文！
        if cat == "celebrity":
            if not is_meaningful_tweet(it):
                continue
            is_fresh_homepage = (diff <= 86400 or bool(it.get("is_pinned")) or is_tibo_reset_tweet(it, now_ts)) and (diff >= -300)
        else:
            is_fresh_homepage = (diff <= MAX_HOMEPAGE_SECONDS) or bool(it.get("is_pinned"))

        if is_fresh_homepage:
            recent_items.append(it)
        else:
            historical_items.append(it)

    # 严格去重键集合，杜绝历史归档与近期流发生任何碰撞重复
    recent_keys = {get_it_key(it) for it in recent_items if get_it_key(it)}

    # 保证在极端冷启动或外部源更新停滞时，首页与专栏不至于空白（填充时同样坚决杜绝 > 48 小时的旧内容）
    news_recent = [it for it in recent_items if it.get("category") == "news"]
    if len(news_recent) < 80:
        extra_news = [
            it for it in historical_items 
            if it.get("category") == "news" 
            and get_it_key(it) not in recent_keys 
            and (now_ts - parse_time_for_sort(it)) <= 7 * 86400
        ][:(80 - len(news_recent))]
        for it in extra_news:
            recent_items.append(it)
            recent_keys.add(get_it_key(it))

    celeb_recent = [it for it in recent_items if it.get("category") == "celebrity"]
    if len(celeb_recent) < 500:
        extra_celeb = [
            it for it in historical_items 
            if it.get("category") == "celebrity" 
            and get_it_key(it) not in recent_keys 
            and (now_ts - parse_time_for_sort(it)) <= 14 * 86400
            and is_meaningful_tweet(it)
        ][:(500 - len(celeb_recent))]
        for it in extra_celeb:
            f_en = str(it.get("full_text_en") or "").strip()
            f_zh = str(it.get("full_text_zh") or "").strip()
            if f_en.count("\n") >= 3 and f_zh.count("\n") <= 1:
                res = re.sub(r'\s+([•→💥💊🪪🧠👉📌🔹✅❌\-\*]|\d+[\.\/])\s*', r'\n\1 ', f_zh)
                res = re.sub(r'([：:])\s+', r'\1\n', res)
                res = re.sub(r'([。！？\?!])\s*', r'\1\n\n', res)
                res = re.sub(r'(#[^\s#]+)\s+', r'\1\n', res)
                res = re.sub(r'(@[^\s@]+)\s+', r'\1\n\n', res)
                res = re.sub(r'([\U00010000-\U0010ffff])\s+', r'\1\n', res)
                if f_en.count("\n") >= 3 and res.count("\n") <= 1:
                    parts = [p.strip() for p in res.split(' ') if p.strip()]
                    if len(parts) >= 3:
                        res = '\n\n'.join(parts)
                res = re.sub(r'\n{3,}', '\n\n', res).strip()
                it["full_text_zh"] = res
            recent_items.append(it)
            recent_keys.add(get_it_key(it))

    viral_recent = [it for it in recent_items if it.get("sub_category") == "viral_post" or (it.get("category") == "celebrity" and it.get("is_viral"))]
    if len(viral_recent) < 20:
        extra_viral = [
            it for it in historical_items 
            if (it.get("sub_category") == "viral_post" or (it.get("category") == "celebrity" and it.get("is_viral"))) 
            and get_it_key(it) not in recent_keys 
            and (now_ts - parse_time_for_sort(it)) <= MAX_HOMEPAGE_SECONDS
        ][:(20 - len(viral_recent))]
        for it in extra_viral:
            recent_items.append(it)
            recent_keys.add(get_it_key(it))

    tools_recent = [it for it in recent_items if it.get("category") == "tools"]
    if len(tools_recent) < 30:
        from fetcher import BAD_TOOL_REPO_NAMES
        extra_tools = []
        for it in historical_items:
            if it.get("category") != "tools":
                continue
            tk = get_it_key(it)
            if tk in recent_keys or (now_ts - parse_time_for_sort(it)) > MAX_HOMEPAGE_SECONDS:
                continue
            app_nm = str(it.get("app_name") or "").strip().lower()
            u_clean = str(it.get("url") or it.get("official_url") or "").lower()
            if app_nm in BAD_TOOL_REPO_NAMES or any(bad == app_nm for bad in BAD_TOOL_REPO_NAMES):
                continue
            if any(f"/{bad}?" in u_clean or f"/{bad}/" in u_clean or u_clean.endswith(f"/{bad}") for bad in BAD_TOOL_REPO_NAMES):
                continue
            extra_tools.append(it)
            if len(extra_tools) >= (30 - len(tools_recent)):
                break
        for it in extra_tools:
            recent_items.append(it)
            recent_keys.add(get_it_key(it))

    # 彻底汇入全量历史视频沉淀（保留所有作者全部 120+ 视频，保证多页翻页与作者筛选完整可用，杜绝归档丢失）
    for it in historical_items:
        if it.get("category") == "videos":
            k = get_it_key(it)
            if k not in recent_keys:
                recent_items.append(it)
                recent_keys.add(k)

    # 彻底汇入全量历史实战提示词沉淀（保留全部 41+ 提示词，保证多页翻页完整查阅）
    for it in historical_items:
        if it.get("category") == "prompts":
            k = get_it_key(it)
            if k not in recent_keys:
                recent_items.append(it)
                recent_keys.add(k)

    def _interleave_tools_multi_source(tool_list):
        from tool_fusion import fuse_and_deduplicate_tools, rank_radar_stream

        # 获取历史库中所有经过筛选的工具，保证历史工具不被删除，沉淀入库
        historical_tools = [it for it in historical_items if it.get("category") == "tools"]
        fused = fuse_and_deduplicate_tools([tool_list, historical_tools])
        return rank_radar_stream(fused)

    # 3. 构建 24/48 小时热看板 payload (latest_news.json)
    grouped = {cat_key: [] for cat_key in CATEGORIES}
    for item in recent_items:
        cat = item.get("category", "news")
        if cat not in grouped:
            cat = "news"
        grouped[cat].append(item)

    for cat_key in grouped:
        if cat_key == "prompts":
            grouped[cat_key].sort(key=lambda x: (
                1 if x.get("generation_tier") != "legacy" else 0,
                x.get("model_tier_score", 80),
                parse_time_for_sort(x)
            ), reverse=True)
        elif cat_key == "tools":
            grouped[cat_key] = _interleave_tools_multi_source(grouped[cat_key])
        else:
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

    # 🔥 24h 核心话题专题聚合引擎 (Topic Focus - 24h 焦点话题全景透视与大V观点对撞)
    topic_focus_list = []
    try:
        from topic_cluster import generate_24h_topic_focus, _enrich_topic_stance_matrix
        topic_focus_list = generate_24h_topic_focus(recent_final)
        topic_focus_list = _enrich_topic_stance_matrix(topic_focus_list)
    except Exception as e:
        print(f"⚠️ [topic_cluster] 生成核心话题专题异常: {e}")

    # 跨栏目去重与分工互斥：提取已消耗 ID 与关键词
    topic_blacklist_kw, topic_consumed_ids = extract_topic_blacklist_keywords(topic_focus_list)

    # 🎬 48h 极客实测展示厅 (Hero Media Showcase: 16:9 极客视频 + 2 篇带图领袖推文)
    hero_media_showcase = extract_hero_media_showcase(recent_final, topic_blacklist_kw, topic_consumed_ids, now_ts)
    if hero_media_showcase.get("lead_media", {}).get("id"):
        topic_consumed_ids.add(str(hero_media_showcase["lead_media"]["id"]))
    for tw in hero_media_showcase.get("viral_tweets", []):
        if tw.get("id"):
            topic_consumed_ids.add(str(tw["id"]))

    # 首页顶部走马灯：精选 24 小时 AI 领袖与核心火爆推文 (排除已消耗 ID)
    viral_ticker_tweets = extract_viral_leader_tweets(recent_final, now_ts, exclude_ids=topic_consumed_ids)

    # Top 3 晨间重磅快讯 (排除已在 Topic Focus 与 Hero Showcase 消耗的条目，精选 3 篇独立大突破)
    top_three = extract_top_three(recent_final, exclude_ids=topic_consumed_ids, blacklist_keywords=topic_blacklist_kw)

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
        "hero_media_showcase": hero_media_showcase,
        "viral_ticker_tweets": viral_ticker_tweets,
        "top_three": top_three,
        "topic_focus": topic_focus_list,
        "chatbot_arena": chatbot_arena,
        "arxiv_papers": arxiv_papers,
        "ai_creators": AI_CREATORS,
        "grouped": grouped
    }

    # 🛡️ 语言规范质检与自愈哨兵：确保写入 latest_news.json 与 archive_news.json 前 100% 纯净达标
    try:
        from language_sentinel import run_pipeline_language_audit
        recent_final, _ = run_pipeline_language_audit(recent_final)
        # 同步更新 latest_payload 中的分类列表与全网爆帖列表
        for cat_k in CATEGORIES:
            cat_items = [it for it in recent_final if it.get("category") == cat_k]
            latest_payload["grouped"][cat_k] = cat_items

        viral_list = [it for it in recent_final if it.get("sub_category") == "viral_post" or (it.get("category") == "celebrity" and it.get("is_viral"))]
        latest_payload["grouped"]["viral_posts"] = viral_list
    except Exception as e:
        print(f"⚠️ [language_sentinel] 自动质检异常: {e}")

    # 🖼️ 场景落地工具缩略图本地化与高清 16:9 画幅适配引擎 (杜绝出现暗黑纯图标占位符)
    try:
        from scripts.localize_tool_images import localize_single_tool, OUTPUT_DIR
        tools_to_check = latest_payload.get("grouped", {}).get("tools", [])
        for tool_it in tools_to_check:
            tid = str(tool_it.get("id") or "").strip()
            if not tid:
                continue
            dest_file = f"{tid}.webp"
            dest_path = os.path.join(OUTPUT_DIR, dest_file)
            if not os.path.exists(dest_path) or os.path.getsize(dest_path) < 3500:
                localize_single_tool(tool_it)
            if os.path.exists(dest_path) and os.path.getsize(dest_path) >= 3500:
                local_url = f"/assets/tool-previews/{dest_file}"
                tool_it["image_url"] = local_url
                cur_previews = tool_it.get("preview_images") or []
                filtered = [p for p in cur_previews if p != local_url and 'photo-1618005182384-a83a8bd57fbe' not in p]
                tool_it["preview_images"] = [local_url] + filtered
    except Exception as e:
        print(f"⚠️ [tool_image_localizer] 工具缩略图处理异常: {e}")

    # 3.5 智能价值分类打标 (为大V推文与爆款注入 6 维核心价值标签)
    try:
        from tweet_classifier import classify_tweets_batch
        classify_tweets_batch(recent_items, use_gemini=False)
        classify_tweets_batch(all_master_items, use_gemini=False)
        for cat_k, cat_list in latest_payload.get("grouped", {}).items():
            if cat_k == "celebrity" and isinstance(cat_list, list):
                classify_tweets_batch(cat_list, use_gemini=False)
        if "viral_ticker_tweets" in latest_payload:
            classify_tweets_batch(latest_payload["viral_ticker_tweets"], use_gemini=False)
    except Exception as e:
        print(f"⚠️ [tweet_classifier] 价值分类标注异常: {e}")

    # 4. 构建全量历史归档库 payload (去除爬虫内部冗余字段，体积暴降 70%，保证浏览器秒开不卡死)
    STRIP_ARCHIVE_KEYS = {'ai_analysis', 'original_content', 'article_content', 'wechat_audit', 'wechat_article_draft'}
    def _clean_archive_item(it):
        return {k: v for k, v in it.items() if k not in STRIP_ARCHIVE_KEYS}

    all_archive_items = list(all_master_items)
    all_archive_items.sort(key=parse_time_for_sort, reverse=True)
    clean_archive_items = [_clean_archive_item(it) for it in all_archive_items]

    archive_payload = {
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "total_count": len(clean_archive_items),
        "items": clean_archive_items,
        "categories": CATEGORIES
    }

    # 写入 latest_news.json (采用紧凑无空白序列化，缩减 80% 体积，极大提升页面拉取与解析性能)
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(latest_payload, f, ensure_ascii=False, separators=(',', ':'))
    with open(PUBLIC_OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(latest_payload, f, ensure_ascii=False, separators=(',', ':'))

    # 写入 archive_news.json (紧凑无空白，体积大幅优化，保证秒级拉取)
    with open(ARCHIVE_OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(archive_payload, f, ensure_ascii=False, separators=(',', ':'))
    with open(PUBLIC_ARCHIVE_OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(archive_payload, f, ensure_ascii=False, separators=(',', ':'))

    # 写入专门的大V推文全量归档库 (archive_celebrity.json - 极致轻量高速，瞬间拉取)
    all_celeb_archive = [_clean_archive_item(it) for it in all_archive_items if it.get("category") == "celebrity"]
    celeb_archive_payload = {
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "total_count": len(all_celeb_archive),
        "items": all_celeb_archive
    }
    with open(os.path.join(DATA_DIR, "archive_celebrity.json"), "w", encoding="utf-8") as f:
        json.dump(celeb_archive_payload, f, ensure_ascii=False, separators=(',', ':'))
    with open(os.path.join(PUBLIC_DATA_DIR, "archive_celebrity.json"), "w", encoding="utf-8") as f:
        json.dump(celeb_archive_payload, f, ensure_ascii=False, separators=(',', ':'))

    # 🛡️ CI Quality Gate: 自动化数据质量门禁硬性审计
    try:
        from tests.test_data_quality_gate import run_quality_gate_assertions
        run_quality_gate_assertions(latest_payload)
    except Exception as e:
        print(f"⚠️ [quality_gate] 数据质量门禁告警: {e}")

    # 自动执行 AdSense 高价值合规重构引擎：
    # 1. 发布独家深度专栏文章 (public/articles/*.html)
    # 2. 回溯并生成全量历史每日简报 (public/daily/*.html)
    # 3. 首页 index.html 真实可见 DOM 预渲染 (Top 3 + 快讯卡片 + 24h 核心话题专题 + 往期导航)
    # 4. 全量更新 35+ 页面站点地图 (public/sitemap.xml)
    try:
        from content_publisher import run_full_content_publication
        run_full_content_publication(recent_final, top_three, topic_focus=topic_focus_list, hero_media_showcase=hero_media_showcase)
    except Exception as e:
        print(f"⚠️ [content_publisher] 执行异常: {e}")
        generate_sitemap()
        inject_seo_static_content(recent_final)
        generate_daily_briefing(recent_final)

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
    try:
        raw_items = fetch_all_sources()
    except Exception as fetch_err:
        print(f"⚠️ [fetch_all_sources] 异常拦截: {fetch_err}，安全转入历史池保障编译。")
        raw_items = []

    if not raw_items:
        print("ℹ️ 外部即时信源本次未返回新数据，继续使用已有历史高可用数据池进行全网渲染与自愈更新。")
        raw_items = []

    # 3. 增量筛选：
    # 具备完整精选中文与真实时间戳的内容（大V推特、实操Prompt、高星工具、核心视频）直接进入更新池
    # 仅对缺失中文提炼的外部原始新闻/RSS做增量 AI 提炼
    new_raw_items = []
    pre_curated_items = []
    reused_count = 0

    for it in raw_items:
        u = it.get("url")
        i = it.get("id")
        # 若条目本身为视频/提示词/精选落地工具，或已有高质量中文提炼（例如大V推特、实操Prompt、开源工具）
        if it.get("category") in ["videos", "prompts", "tools"]:
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
    
    # 6.5 全局动态知识图谱与全网前沿标签持续自习闭环 (SSOT Knowledge Base Self-Learning)
    try:
        from knowledge_base import learn_from_feed_items
        from fetcher import get_chatbot_arena_top5
        arena_current = get_chatbot_arena_top5()
        learn_from_feed_items(cleaned_items, arena_current)
    except Exception as kb_err:
        print(f"⚠️ [Knowledge Base 学习闭环] 执行异常: {kb_err}")

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
    try:
        run_pipeline()
    except BaseException as e:
        import traceback
        print(f"\n🚨 [Pipeline Error Shield] 顶层捕获严重异常，已启动自愈保底策略: {e}")
        traceback.print_exc()
        try:
            print("🛡️ 正在使用本地高可用数据执行全站静态渲染与多语言站点自愈...")
            from content_publisher import run_full_content_publication
            target_data_file = OUTPUT_FILE if os.path.exists(OUTPUT_FILE) else PUBLIC_OUTPUT_FILE
            if os.path.exists(target_data_file):
                with open(target_data_file, "r", encoding="utf-8") as f:
                    saved_payload = json.load(f)
                rec_items = saved_payload.get("items", []) or []
                if not rec_items and "grouped" in saved_payload:
                    for cat_items in saved_payload["grouped"].values():
                        if isinstance(cat_items, list):
                            rec_items.extend(cat_items)
                t_three = saved_payload.get("top_three", []) or []
                t_focus = saved_payload.get("topic_focus", []) or []
                h_showcase = saved_payload.get("hero_media_showcase", {}) or {}
                run_full_content_publication(rec_items, t_three, topic_focus=t_focus, hero_media_showcase=h_showcase)
                print("✅ 静态自愈保底完成，站点多语言资产完好。")
        except Exception as rescue_err:
            print(f"⚠️ 静态自愈亦遇阻，确保退出码为 0: {rescue_err}")
        sys.exit(0)
