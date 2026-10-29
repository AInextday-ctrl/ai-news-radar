"""
AI Curator Engine (科技主编深度精选引擎)
--------------------------------------------
专为各栏目（社交雷达、行业资讯、落地工具）进行高标准价值筛选、去噪与【主编言下之意】双语提炼。
支持主站（英文 EN）与副站（中文 ZH）双语同步构建。
支持多 Key 自动轮询与模型故障自愈降级，内置内容指纹指纹增量缓存，极大节省免费 API 配额。
"""

import os
import sys
import json
import hashlib
import re
import urllib.request
import urllib.error
from typing import Dict, Any, List, Optional
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
PUBLIC_DATA_DIR = os.path.join(BASE_DIR, "public", "data")
OUTPUT_FILE = os.path.join(DATA_DIR, "curated_column_highlights.json")
PUBLIC_OUTPUT_FILE = os.path.join(PUBLIC_DATA_DIR, "curated_column_highlights.json")
CACHE_FILE = os.path.join(DATA_DIR, "curator_fingerprints.json")

# 候选模型按优先级排序 (3.5-flash / 3.6-flash / 3-flash-preview)
CANDIDATE_MODELS = [
    os.getenv("GEMINI_MODEL", "").strip(),
    "gemini-3.5-flash",
    "gemini-3.6-flash",
    "gemini-3-flash-preview"
]
CANDIDATE_MODELS = [m for m in CANDIDATE_MODELS if m]

def get_gemini_keys() -> List[str]:
    """按优先级收集所有可用 Gemini API Keys，实现多 Key 轮询"""
    keys = []
    # 优先环境变量
    for env_var in [
        "GEMINI_API_KEY_NEWS",
        "GEMINI_API_KEY_TOPICS",
        "GEMINI_API_KEY",
        "GEMINI_API_KEY_2"
    ]:
        v = os.getenv(env_var, "").strip()
        if v and v != "your_gemini_api_key_here" and v not in keys:
            keys.append(v)

    # 兜底读取本地 .env
    env_file = os.path.join(BASE_DIR, ".env")
    if os.path.exists(env_file):
        try:
            with open(env_file, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line.startswith("GEMINI_API_KEY=") or line.startswith("GEMINI_API_KEY_NEWS="):
                        k = line.split("=", 1)[1].strip()
                        if k and k not in keys:
                            keys.append(k)
        except Exception:
            pass

    return keys

def get_proxy_opener():
    """在有本地代理时自动配置代理"""
    proxy_url = os.getenv("HTTP_PROXY") or os.getenv("http_proxy") or "http://127.0.0.1:7897"
    try:
        handler = urllib.request.ProxyHandler({'http': proxy_url, 'https': proxy_url})
        return urllib.request.build_opener(handler)
    except Exception:
        return urllib.request.build_opener()

def call_gemini(prompt: str, keys: List[str]) -> Optional[str]:
    """通过轮询 Key 和模型调用 Gemini API"""
    opener = get_proxy_opener()
    headers = {'Content-Type': 'application/json'}
    payload = json.dumps({"contents": [{"parts": [{"text": prompt}]}]}).encode('utf-8')

    for key in keys:
        for model in CANDIDATE_MODELS:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={key}"
            try:
                req = urllib.request.Request(url, data=payload, headers=headers)
                # 尝试直连或代理
                try:
                    with opener.open(req, timeout=18) as resp:
                        res = json.loads(resp.read().decode('utf-8'))
                        return res['candidates'][0]['content']['parts'][0]['text']
                except Exception:
                    # 回退到无代理直连 (适用于 GitHub Actions 生产云端)
                    with urllib.request.urlopen(req, timeout=18) as resp:
                        res = json.loads(resp.read().decode('utf-8'))
                        return res['candidates'][0]['content']['parts'][0]['text']
            except urllib.error.HTTPError as e:
                err_text = e.read().decode('utf-8', errors='replace')
                print(f"[Curator] Key(...{key[-6:]}) with {model} failed HTTP {e.code}: {err_text[:120]}")
                if e.code == 429:
                    continue  # 配额超限尝试下一个 Key
            except Exception as e:
                print(f"[Curator] Key(...{key[-6:]}) with {model} exception: {e}")
                continue

    return None

def compute_fingerprint(items: List[Dict[str, Any]]) -> str:
    """计算候选条目的内容指纹"""
    tokens = [str(it.get('id', '')) + str(it.get('title', ''))[:30] for it in items[:6]]
    return hashlib.md5("|".join(tokens).encode('utf-8')).hexdigest()

def curate_column(
    category_name: str,
    items: List[Dict[str, Any]],
    keys: List[str],
    cached_column_data: Optional[Dict[str, Any]]
) -> Dict[str, Any]:
    """对单个栏目进行 AI 主编级精选与言下之意提炼"""
    if not items:
        return cached_column_data or {}

    candidates = items[:8]
    current_fp = compute_fingerprint(candidates)

    # 命中指纹缓存且已有精选结果，则直接复用
    if cached_column_data and cached_column_data.get("fingerprint") == current_fp:
        print(f"[Curator] {category_name}: 内容指纹未变化，复用现有精选结果 (0 API 消耗)")
        return cached_column_data

    # 构造精炼 Prompt
    candidates_repr = []
    for idx, it in enumerate(candidates):
        candidates_repr.append({
            "index": idx,
            "title": it.get("title") or it.get("title_zh") or "",
            "author": it.get("author_name") or it.get("author_handle") or it.get("source") or "",
            "snippet": (it.get("summary_zh") or it.get("content_snippet") or it.get("description") or "")[:120]
        })

    cat_descriptors = {
        "celebrity": "Global AI Lab Heads, Core Architects, and Influential Geek Voices (Twitter/𝕏 Native Posts)",
        "news": "Breaking AI Industry Milestones, Strategic Compute Investments, M&A, and Regulatory Shifts",
        "tools": "Applied 10x Developer Productivity Tools, Local AI Workflows, and Practical Open-Source Engines"
    }

    prompt = f"""You are a veteran Chief Tech Editor at a top-tier bilingual global AI publication.
Task: Perform authoritative editorial curation on candidate items from the '{cat_descriptors.get(category_name, category_name)}' column.

1. Filter out PR marketing fluff, superficial product spam, routine small patches, and speculative echo chambers.
2. Select EXACTLY ONE #1 "S-Tier Spotlight" (Breakthrough that shifts paradigms or unlocks massive practical value).
3. Select UP TO TWO "A-Tier Featured Highlights" (Solid practical utilities or noteworthy technical insights).
4. For the S-Tier Spotlight, craft a piercing, bilingual "Editor's Strategic Takeaway" (言下之意) under 50 words. Do NOT summarize or repeat the headline; directly explain the underlying business moat, architectural shift, or industry power dynamic that people miss.

Candidates:
{json.dumps(candidates_repr, ensure_ascii=False, indent=2)}

Return ONLY a strictly valid JSON object matching this schema without markdown codeblocks or extra text:
{{
  "spotlight_index": 0,
  "title_en": "Punchy, authoritative headline in English",
  "title_zh": "繁體/通用中文權威焦點標題（精準有力）",
  "tier_label_en": "S-Tier · Industry Paradigm Shift",
  "tier_label_zh": "S級·行業破局焦點",
  "insight_en": "Under 45 words: Piercing strategic takeaway revealing the commercial moat or technical disruption.",
  "insight_zh": "45字以內：一針見血戳破公關表象，直擊底層商業模式或技術架構本質的主編言下之意。",
  "takeaways_en": ["Core implication 1", "Core implication 2"],
  "takeaways_zh": ["核心影響點 1", "核心影響點 2"],
  "featured_indices": [1, 2]
}}
"""

    print(f"[Curator] 正在为栏目 '{category_name}' 运行 AI 价值甄别...")
    raw_response = call_gemini(prompt, keys)
    if not raw_response:
        print(f"[Curator] 警告：'{category_name}' AI 调用未返回，保留历史缓存或使用首条备用。")
        return cached_column_data or _fallback_curation(category_name, candidates, current_fp)

    try:
        # 提取并解析 JSON
        match = re.search(r'\{.*\}', raw_response, re.DOTALL)
        if not match:
            raise ValueError("No JSON object found in response")
        parsed = json.loads(match.group(0))

        s_idx = int(parsed.get("spotlight_index", 0))
        if s_idx >= len(candidates) or s_idx < 0:
            s_idx = 0
        s_item = candidates[s_idx]

        featured_items = []
        for f_idx in parsed.get("featured_indices", []):
            if isinstance(f_idx, int) and 0 <= f_idx < len(candidates) and f_idx != s_idx:
                it = candidates[f_idx]
                featured_items.append({
                    "id": it.get("id"),
                    "title_en": it.get("title") or it.get("title_zh") or "",
                    "title_zh": it.get("title_zh") or it.get("title") or "",
                    "url": it.get("url") or "#",
                    "author": it.get("author_name") or it.get("author_handle") or it.get("source") or "",
                    "tag_en": "A-Tier Highlight",
                    "tag_zh": "A級精選"
                })

        curated = {
            "fingerprint": current_fp,
            "updated_at": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC"),
            "category": category_name,
            "spotlight": {
                "id": s_item.get("id"),
                "title_en": parsed.get("title_en") or s_item.get("title"),
                "title_zh": parsed.get("title_zh") or s_item.get("title_zh") or s_item.get("title"),
                "tier_label_en": parsed.get("tier_label_en", "S-Tier Spotlight"),
                "tier_label_zh": parsed.get("tier_label_zh", "S級·破局焦點"),
                "insight_en": parsed.get("insight_en", ""),
                "insight_zh": parsed.get("insight_zh", ""),
                "takeaways_en": parsed.get("takeaways_en", []),
                "takeaways_zh": parsed.get("takeaways_zh", []),
                "author_name": s_item.get("author_name") or "",
                "author_handle": s_item.get("author_handle") or "",
                "source": s_item.get("source") or ("𝕏 / Twitter" if category_name == "celebrity" else "Industry Wire"),
                "url": s_item.get("url") or "#",
                "published_at": s_item.get("published_at") or s_item.get("date") or "",
                "media_url": s_item.get("media_url") or s_item.get("image_url") or ""
            },
            "featured": featured_items
        }
        print(f"[Curator] 成功完成 '{category_name}' 双语精选！Spotlight: {curated['spotlight']['title_zh'][:30]}...")
        return curated

    except Exception as e:
        print(f"[Curator] 解析 AI 精选结果异常: {e}，启用安全保底。")
        return cached_column_data or _fallback_curation(category_name, candidates, current_fp)

def _fallback_curation(category_name: str, candidates: List[Dict[str, Any]], fp: str) -> Dict[str, Any]:
    """无 API 响应时的安全静态保底"""
    if not candidates:
        return {}
    top = candidates[0]
    return {
        "fingerprint": fp,
        "updated_at": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC"),
        "category": category_name,
        "spotlight": {
            "id": top.get("id"),
            "title_en": top.get("title") or "Top Frontier Development",
            "title_zh": top.get("title_zh") or top.get("title") or "前沿重磅動態",
            "tier_label_en": "S-Tier Spotlight",
            "tier_label_zh": "S級·精選推薦",
            "insight_en": "Key paradigm advancement identified by algorithmic priority tracking across global frontier AI networks.",
            "insight_zh": "依託算法優先級監控系統甄別出的全球前沿 AI 網絡重點演進動態。",
            "takeaways_en": [],
            "takeaways_zh": [],
            "author_name": top.get("author_name") or "",
            "author_handle": top.get("author_handle") or "",
            "source": top.get("source") or "AI Radar",
            "url": top.get("url") or "#",
            "published_at": top.get("published_at") or "",
            "media_url": top.get("media_url") or ""
        },
        "featured": []
    }

def run_curator():
    """主执行入口：对社交雷达、行业资讯、落地工具进行全量双语精选"""
    print("=== [Curator Engine] 启动 AI 科技主编双语精选引擎 ===")
    keys = get_gemini_keys()
    print(f"[Curator] 检出可用 API Key 数量: {len(keys)}")

    # 载入已有缓存
    existing_curations = {}
    if os.path.exists(OUTPUT_FILE):
        try:
            with open(OUTPUT_FILE, "r", encoding="utf-8") as f:
                existing_curations = json.load(f)
        except Exception:
            existing_curations = {}

    # 1. 载入原始候选池
    news_items = []
    celebrity_items = []
    tools_items = []

    # 优先从 latest_news.json 读取
    latest_news_file = os.path.join(DATA_DIR, "latest_news.json")
    if os.path.exists(latest_news_file):
        try:
            with open(latest_news_file, "r", encoding="utf-8") as f:
                raw_data = json.load(f)
                all_items = raw_data if isinstance(raw_data, list) else raw_data.get("items", [])
                for it in all_items:
                    cat = it.get("category", "")
                    if cat == "news":
                        news_items.append(it)
                    elif cat == "celebrity":
                        celebrity_items.append(it)
                    elif cat == "tools":
                        tools_items.append(it)
        except Exception as e:
            print(f"[Curator] 读取 latest_news.json 异常: {e}")

    # 补充读取 archive_celebrity.json 中的推文数据
    celeb_archive_file = os.path.join(DATA_DIR, "archive_celebrity.json")
    if os.path.exists(celeb_archive_file):
        try:
            with open(celeb_archive_file, "r", encoding="utf-8") as f:
                raw_celeb = json.load(f)
                c_items = raw_celeb if isinstance(raw_celeb, list) else raw_celeb.get("items", [])
                # 合并并去重
                seen_ids = set(it.get("id") for it in celebrity_items if it.get("id"))
                for c in c_items:
                    cid = c.get("id")
                    if cid and cid not in seen_ids:
                        celebrity_items.append(c)
                        seen_ids.add(cid)
        except Exception as e:
            print(f"[Curator] 读取 archive_celebrity.json 异常: {e}")

    print(f"[Curator] 候选池规模 -> 社交雷达: {len(celebrity_items)} 篇, 行业资讯: {len(news_items)} 篇, 落地工具: {len(tools_items)} 款")

    # 2. 执行三大栏目精选
    results = {
        "version": "1.0",
        "generated_at": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC"),
        "columns": {}
    }

    # 栏目 1: 社交雷达 (celebrity)
    results["columns"]["celebrity"] = curate_column(
        "celebrity",
        celebrity_items,
        keys,
        existing_curations.get("columns", {}).get("celebrity")
    )

    # 栏目 2: 行业资讯 (news)
    results["columns"]["news"] = curate_column(
        "news",
        news_items,
        keys,
        existing_curations.get("columns", {}).get("news")
    )

    # 栏目 3: 落地工具 (tools)
    results["columns"]["tools"] = curate_column(
        "tools",
        tools_items,
        keys,
        existing_curations.get("columns", {}).get("tools")
    )

    # 3. 持久化到数据目录和公开目录
    os.makedirs(DATA_DIR, exist_ok=True)
    os.makedirs(PUBLIC_DATA_DIR, exist_ok=True)

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    with open(PUBLIC_OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    print(f"=== [Curator Engine] 双语精选数据成功输出至: {PUBLIC_OUTPUT_FILE} ===")
    return results

if __name__ == "__main__":
    run_curator()

def build_spotlight_html(column_data: Dict[str, Any], is_zh: bool = False, tab: str = "celebrity") -> str:
    """生成用于服务端预渲染的 Spotlight Hero Card HTML"""
    if not column_data or not column_data.get("spotlight"):
        return ""
    
    sp = column_data["spotlight"]
    ft = column_data.get("featured", [])
    
    title = sp.get("title_zh") if is_zh else sp.get("title_en")
    title = title or sp.get("title_en") or sp.get("title_zh") or ""
    
    tier_label = sp.get("tier_label_zh") if is_zh else sp.get("tier_label_en")
    tier_label = tier_label or ("S級·行業破局焦點" if is_zh else "S-Tier Strategic Spotlight")
    
    insight = sp.get("insight_zh") if is_zh else sp.get("insight_en")
    author = sp.get("author_name") or sp.get("author_handle") or sp.get("source") or "Frontier AI Wire"
    if sp.get("author_name") and sp.get("author_handle"):
        author = f"{sp['author_name']} {sp['author_handle']}"
        
    url = sp.get("url") or "#"
    takeaways = sp.get("takeaways_zh") if is_zh else sp.get("takeaways_en")
    takeaways = takeaways or []
    
    cat_badges = {
        "celebrity": "🐦 社交雷達精選" if is_zh else "🐦 Social Radar Spotlight",
        "news": "⚡ 重大戰略突發" if is_zh else "⚡ Strategic Milestone",
        "tools": "🛠️ 生產力破局神器" if is_zh else "🛠️ 10x Productivity Engine"
    }
    cat_badge_text = cat_badges.get(tab, "🌟 破局精選" if is_zh else "🌟 Spotlight")
    
    insight_header = "💡 科技主編 · 言下之意 (直擊底層商業與技術本質)" if is_zh else "💡 EDITOR'S STRATEGIC TAKEAWAY (READ BETWEEN THE LINES)"
    source_btn_text = "查看官方信源 ↗" if is_zh else "View Source ↗"
    featured_header = "🔥 A級核心看點" if is_zh else "🔥 A-Tier Key Developments"
    
    featured_pills_html = ""
    if ft:
        pills = []
        for f in ft:
            f_title = f.get("title_zh") if is_zh else f.get("title_en")
            f_title = f_title or f.get("title_en") or ""
            f_tag = f.get("tag_zh") if is_zh else f.get("tag_en")
            f_tag = f_tag or ("A級精選" if is_zh else "Featured")
            f_url = f.get("url") or "#"
            pills.append(f"""
                <a href="{f_url}" target="_blank" rel="noopener noreferrer" class="inline-flex items-center space-x-1.5 px-3 py-1 rounded-xl bg-white/90 dark:bg-slate-800/90 hover:bg-amber-500/10 dark:hover:bg-slate-700/80 border border-slate-200 dark:border-slate-700/80 text-xs text-slate-800 dark:text-slate-200 transition-all hover:scale-[1.02] shadow-xs">
                  <span class="px-1.5 py-0.2 rounded bg-indigo-500/15 text-indigo-700 dark:text-indigo-300 font-bold text-[10px]">{f_tag}</span>
                  <span class="font-medium truncate max-w-[240px] sm:max-w-[360px]">{f_title}</span>
                  <span class="text-slate-400 text-[10px]">↗</span>
                </a>
            """)
        featured_pills_html = f"""
          <div class="mt-4 pt-3.5 border-t border-slate-200/80 dark:border-slate-800/80 flex items-center gap-2.5 flex-wrap">
            <span class="text-[11px] font-bold text-slate-500 dark:text-slate-400 shrink-0 flex items-center space-x-1">
              <span>{featured_header}</span>
            </span>
            {"".join(pills)}
          </div>
        """
        
    takeaways_html = ""
    if takeaways:
        bullets = [f'<span class="inline-flex items-center px-2 py-0.5 rounded-lg bg-amber-500/10 dark:bg-amber-400/10 text-amber-900 dark:text-amber-200 border border-amber-500/20 text-[11px] font-medium">• {t}</span>' for t in takeaways]
        takeaways_html = f'<div class="mt-2.5 flex items-center gap-2 flex-wrap text-xs text-slate-600 dark:text-slate-300">{"".join(bullets)}</div>'
        
    insight_block = ""
    if insight:
        insight_block = f"""
        <div class="p-4 sm:p-4.5 rounded-2xl bg-gradient-to-r from-amber-500/15 via-orange-500/10 to-indigo-500/10 dark:from-amber-950/40 dark:via-slate-900/60 dark:to-indigo-950/30 border-l-4 border-amber-500 dark:border-amber-400 border-t border-r border-b border-amber-500/25 dark:border-amber-500/20 shadow-sm backdrop-blur-xs">
          <div class="flex items-center space-x-2 mb-1.5">
            <span class="text-xs font-extrabold uppercase tracking-wider text-amber-800 dark:text-amber-300 flex items-center gap-1.5">
              <span>{insight_header}</span>
            </span>
          </div>
          <p class="text-xs sm:text-sm text-slate-800 dark:text-slate-200 font-medium leading-relaxed italic">
            "{insight}"
          </p>
          {takeaways_html}
        </div>
        """
        
    return f"""
    <div class="relative overflow-hidden rounded-3xl p-5 sm:p-6 border-2 border-amber-500/50 dark:border-amber-400/40 bg-gradient-to-br from-amber-50/90 via-slate-50 to-indigo-50/70 dark:from-slate-900/95 dark:via-slate-900 dark:to-indigo-950/40 shadow-2xl shadow-amber-500/10 transition-all">
      <div class="flex items-center justify-between pb-3.5 mb-3 border-b border-amber-500/20 dark:border-slate-800 flex-wrap gap-2">
        <div class="flex items-center space-x-2.5 flex-wrap gap-y-1">
          <span class="relative flex h-3 w-3">
            <span class="animate-ping absolute inline-flex h-full w-full rounded-full bg-amber-400 opacity-75"></span>
            <span class="relative inline-flex rounded-full h-3 w-3 bg-amber-500"></span>
          </span>
          <span class="px-3 py-1 rounded-full text-xs font-black bg-gradient-to-r from-amber-500 via-orange-500 to-rose-500 text-slate-950 shadow-md shadow-amber-500/20 tracking-wide uppercase">
            {tier_label}
          </span>
          <span class="px-2.5 py-0.5 rounded-full text-[11px] font-bold bg-slate-900 text-amber-300 dark:bg-slate-800 dark:text-amber-300 border border-amber-500/30">
            {cat_badge_text}
          </span>
          <span class="text-xs font-semibold text-slate-500 dark:text-slate-400 flex items-center space-x-1">
            <span>by</span>
            <span class="font-bold text-slate-700 dark:text-slate-200">{author}</span>
          </span>
        </div>
        <a href="{url}" target="_blank" rel="noopener noreferrer" class="inline-flex items-center space-x-1 px-3.5 py-1.5 rounded-xl bg-slate-900 dark:bg-slate-100 hover:bg-slate-800 dark:hover:bg-white text-white dark:text-slate-950 text-xs font-bold transition-all shadow-md hover:scale-105 cursor-pointer">
          <span>{source_btn_text}</span>
        </a>
      </div>

      <h2 class="text-lg sm:text-2xl font-black text-slate-900 dark:text-slate-50 tracking-tight leading-snug mb-3.5">
        <a href="{url}" target="_blank" rel="noopener noreferrer" class="hover:text-amber-600 dark:hover:text-amber-400 transition-colors">
          {title}
        </a>
      </h2>

      {insight_block}

      {featured_pills_html}
    </div>
    """
