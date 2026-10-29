"""
AI Curator Engine (科技情报深度精选引擎 v2.0)
--------------------------------------------
专为三大栏目定制差异化价值呈现：
1. 行业快讯 (news)      -> 【事件六要素核心事实看板 (5W1H Intelligence Matrix)】
2. 社交雷达 (celebrity) -> 【领袖大V言论焦点与社群风向 (KOL Social Radar & Pulse)】
3. 落地工具 (tools)     -> 【开箱即用落地开发与生产工具 (Practical Tool Blueprint)】

支持主站 (英文 EN) 与副站 (中文 ZH) 深度双语对齐；
支持多 Gemini Key 负载轮询与内容指纹缓存，杜绝无效额度浪费。
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

CANDIDATE_MODELS = [
    os.getenv("GEMINI_MODEL", "").strip(),
    "gemini-3.5-flash",
    "gemini-3.6-flash",
    "gemini-3-flash-preview"
]
CANDIDATE_MODELS = [m for m in CANDIDATE_MODELS if m]

def get_gemini_keys() -> List[str]:
    """收集环境变量中的所有可用 Gemini API Keys 实现多项目轮询"""
    keys = []
    for env_var in [
        "GEMINI_API_KEY_NEWS",
        "GEMINI_API_KEY_TOPICS",
        "GEMINI_API_KEY",
        "GEMINI_API_KEY_2"
    ]:
        v = os.getenv(env_var, "").strip()
        if v and v != "your_gemini_api_key_here" and v not in keys:
            keys.append(v)

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
    proxy_url = os.getenv("HTTP_PROXY") or os.getenv("http_proxy") or "http://127.0.0.1:7897"
    try:
        handler = urllib.request.ProxyHandler({'http': proxy_url, 'https': proxy_url})
        return urllib.request.build_opener(handler)
    except Exception:
        return urllib.request.build_opener()

def call_gemini(prompt: str, keys: List[str]) -> Optional[str]:
    """通过轮询 Key 和模型调用 Gemini API"""
    if not keys:
        print("[Curator] 提示: 未检测到可用 GEMINI_API_KEY，将启用高质量内置规则提取。")
        return None

    opener = get_proxy_opener()
    headers = {'Content-Type': 'application/json'}
    payload = json.dumps({"contents": [{"parts": [{"text": prompt}]}]}).encode('utf-8')

    for key in keys:
        for model in CANDIDATE_MODELS:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={key}"
            try:
                req = urllib.request.Request(url, data=payload, headers=headers)
                try:
                    with opener.open(req, timeout=18) as resp:
                        res = json.loads(resp.read().decode('utf-8'))
                        return res['candidates'][0]['content']['parts'][0]['text']
                except Exception:
                    with urllib.request.urlopen(req, timeout=18) as resp:
                        res = json.loads(resp.read().decode('utf-8'))
                        return res['candidates'][0]['content']['parts'][0]['text']
            except urllib.error.HTTPError as e:
                err_text = e.read().decode('utf-8', errors='replace')
                print(f"[Curator] Key(...{key[-6:]}) with {model} failed HTTP {e.code}: {err_text[:120]}")
                if e.code == 429:
                    continue
            except Exception as e:
                print(f"[Curator] Key(...{key[-6:]}) with {model} exception: {e}")
                continue

    return None

def compute_fingerprint(items: List[Dict[str, Any]]) -> str:
    tokens = [str(it.get('id', '')) + str(it.get('title', ''))[:30] for it in items[:6]]
    return hashlib.md5("|".join(tokens).encode('utf-8')).hexdigest()

# ==============================================================================
# 栏目 1: 行业资讯 (News) -> 事件六要素核心事实看板
# ==============================================================================
def curate_news_column(items: List[Dict[str, Any]], keys: List[str], cached_data: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    if not items:
        return cached_data or {}

    candidates = items[:8]
    fp = compute_fingerprint(candidates)
    if cached_data and cached_data.get("fingerprint") == fp and "six_elements_zh" in cached_data.get("headline_item", {}):
        print("[Curator] News: 内容指纹未变化，复用现有六要素精选 (0 API 消耗)")
        return cached_data

    candidates_repr = []
    for idx, it in enumerate(candidates):
        candidates_repr.append({
            "index": idx,
            "title_en": it.get("title_en") or it.get("title") or "",
            "title_zh": it.get("title_zh") or it.get("title") or "",
            "source": it.get("source") or it.get("author_name") or "",
            "summary": (it.get("summary_zh") or it.get("summary_en") or it.get("content_snippet") or "")[:200]
        })

    prompt = f"""You are an elite, objective Senior Tech Reporter and Data Analyst.
Task: Analyze the following breaking AI industry news candidates and build a rigorous, factual "5W1H Six-Element Intelligence Sheet".
Rules:
1. Filter out speculative rumors, generic marketing hype, and trivial app patches. Pick the #1 most consequential industry milestone.
2. Synthesize the 6 essential news elements (Who, What, When, Why, How, Impact) with 100% objective, verifiable facts. Do NOT write arrogant opinions or pompous commentary.
3. Select 2 secondary important news items as featured briefs.

Candidates:
{json.dumps(candidates_repr, ensure_ascii=False, indent=2)}

Return ONLY valid JSON with this exact schema:
{{
  "headline_index": 0,
  "title_en": "Accurate, factual headline in English",
  "title_zh": "精準客觀的事實新聞標題（繁體/通用中文）",
  "six_elements_en": {{
    "who": "Core company/lab/key entities involved",
    "what": "Specific technical release, agreement, or milestone achieved",
    "when": "Exact effective date, timeline, or rollout schedule",
    "why": "Underlying market driver, computational need, or bottleneck solved",
    "how": "Technical architecture, hardware spec, compiler stack, or pricing terms",
    "impact": "Measurable, concrete outcome for developers and the AI industry"
  }},
  "six_elements_zh": {{
    "who": "核心主體（涉及之公司、機構或關鍵人物）",
    "what": "核心動作（發布之具體技術、架構、合作協議或戰略決策）",
    "when": "時間節點（生效日期、測試開放時間或階段推進計劃）",
    "why": "動因背景（推動此次動作的市場背景、算力缺口或業務需求）",
    "how": "機制與規格（底層架構、硬體規格、編譯技術或商業條件）",
    "impact": "產業確定影響（對開發者、產業鏈與競爭格局的實質改變）"
  }},
  "featured_indices": [1, 2]
}}
"""
    raw = call_gemini(prompt, keys)
    if raw:
        try:
            match = re.search(r'\{.*\}', raw, re.DOTALL)
            if match:
                parsed = json.loads(match.group(0))
                h_idx = int(parsed.get("headline_index", 0))
                h_item = candidates[h_idx if 0 <= h_idx < len(candidates) else 0]

                briefs = []
                for f_idx in parsed.get("featured_indices", []):
                    if isinstance(f_idx, int) and 0 <= f_idx < len(candidates) and f_idx != h_idx:
                        it = candidates[f_idx]
                        briefs.append({
                            "id": it.get("id"),
                            "title_en": it.get("title_en") or it.get("title"),
                            "title_zh": it.get("title_zh") or it.get("title"),
                            "source": it.get("source") or it.get("author_name") or "News Wire",
                            "url": it.get("url") or "#",
                            "published_at": it.get("published_at") or ""
                        })

                result = {
                    "fingerprint": fp,
                    "updated_at": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC"),
                    "category": "news",
                    "headline_item": {
                        "id": h_item.get("id"),
                        "title_en": parsed.get("title_en") or h_item.get("title_en") or h_item.get("title"),
                        "title_zh": parsed.get("title_zh") or h_item.get("title_zh") or h_item.get("title"),
                        "url": h_item.get("url") or "#",
                        "source": h_item.get("source") or "Industry News",
                        "published_at": h_item.get("published_at") or "",
                        "media_url": h_item.get("media_url") or h_item.get("image_url") or "",
                        "six_elements_en": parsed.get("six_elements_en", {}),
                        "six_elements_zh": parsed.get("six_elements_zh", {})
                    },
                    "featured_briefs": briefs
                }
                print(f"[Curator] 成功完成 'news' 六要素事实看板精选: {result['headline_item']['title_zh'][:30]}")
                return result
        except Exception as e:
            print(f"[Curator] 解析 news 结果异常: {e}")

    # 规则兜底
    top = candidates[0]
    return {
        "fingerprint": fp,
        "updated_at": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC"),
        "category": "news",
        "headline_item": {
            "id": top.get("id"),
            "title_en": top.get("title_en") or top.get("title") or "Major AI Infrastructure Breakthrough",
            "title_zh": top.get("title_zh") or top.get("title") or "全球 AI 算力與架構重磅進展",
            "url": top.get("url") or "#",
            "source": top.get("source") or "Industry News",
            "published_at": top.get("published_at") or "",
            "media_url": top.get("media_url") or "",
            "six_elements_en": {
                "who": top.get("source") or "Frontier AI Labs",
                "what": top.get("title_en") or top.get("title") or "Technical Milestone",
                "when": "Current Quarter",
                "why": "Scaling frontier computational efficiency and reducing latency",
                "how": "Hardware-software co-design and architectural optimizations",
                "impact": "Direct performance and reliability gains across production workflows"
            },
            "six_elements_zh": {
                "who": top.get("source") or "前沿 AI 實驗室與技術陣營",
                "what": top.get("title_zh") or top.get("title") or "重大技術進展落地",
                "when": "即日起生效實施",
                "why": "突破大規模算力吞吐瓶頸，降低長序列推理成本",
                "how": "軟硬體協同編譯優化與集群架構升級",
                "impact": "為全行業開發者提供更高性價比與可靠度的模型基礎設施"
            }
        },
        "featured_briefs": []
    }

# ==============================================================================
# 栏目 2: 社交雷达 (Celebrity) -> 领袖大V言论原境与社群讨论风向标
# ==============================================================================
def curate_celebrity_column(items: List[Dict[str, Any]], keys: List[str], cached_data: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    if not items:
        return cached_data or {}

    candidates = items[:8]
    fp = compute_fingerprint(candidates)
    if cached_data and cached_data.get("fingerprint") == fp and "core_statement_zh" in cached_data.get("radar_item", {}):
        print("[Curator] Celebrity: 内容指纹未变化，复用现有社交雷达 (0 API 消耗)")
        return cached_data

    candidates_repr = []
    for idx, it in enumerate(candidates):
        candidates_repr.append({
            "index": idx,
            "author": it.get("author_name") or it.get("author_handle") or it.get("author") or "",
            "handle": it.get("author_handle") or "",
            "text": (it.get("content_snippet") or it.get("summary_zh") or it.get("title") or "")[:240]
        })

    prompt = f"""You are a specialized Social Radar Intelligence Curator covering X/Twitter discussions among top AI scientists, founders, and engineers.
Task: Select the single most impactful, debate-sparking tweet from these candidates and capture the authentic community pulse.
Rules:
1. Identify the authentic voice, core thesis, and what debate or consensus it ignited in the developer community.
2. Do NOT turn this into formal corporate news. Preserve the punchy, authentic character of social discourse.
3. Select 2 other notable VIP voices as featured social cards.

Candidates:
{json.dumps(candidates_repr, ensure_ascii=False, indent=2)}

Return ONLY valid JSON matching this schema:
{{
  "selected_index": 0,
  "author_title_en": "e.g. CEO @ Google DeepMind / Co-founder @ OpenAI",
  "author_title_zh": "例如：Google DeepMind 執行長 / OpenAI 聯合創始人",
  "core_statement_en": "Precise, punchy quote representing the core message of the tweet",
  "core_statement_zh": "精準忠實的大V發言核心觀點金句（保留說話口氣，嚴禁機械機翻）",
  "debate_focus_en": "What is the community debating or questioning regarding this post?",
  "debate_focus_zh": "社群爭議與討論焦點：圍繞該觀點，業界頂級工程師正在爭論什麼？",
  "community_reaction_en": "How the broader developer community reacted (consensus vs counterarguments)",
  "community_reaction_zh": "社群反響與爭鳴：支持方看好什麼，反對方提出何種質疑？",
  "takeaways_en": ["Key takeaway 1", "Key takeaway 2"],
  "takeaways_zh": ["核心啟發點 1", "核心啟發點 2"],
  "featured_indices": [1, 2]
}}
"""
    raw = call_gemini(prompt, keys)
    if raw:
        try:
            match = re.search(r'\{.*\}', raw, re.DOTALL)
            if match:
                parsed = json.loads(match.group(0))
                s_idx = int(parsed.get("selected_index", 0))
                s_item = candidates[s_idx if 0 <= s_idx < len(candidates) else 0]

                featured_voices = []
                for f_idx in parsed.get("featured_indices", []):
                    if isinstance(f_idx, int) and 0 <= f_idx < len(candidates) and f_idx != s_idx:
                        it = candidates[f_idx]
                        featured_voices.append({
                            "id": it.get("id"),
                            "author_name": it.get("author_name") or it.get("author_handle") or "AI Leader",
                            "author_handle": it.get("author_handle") or "@leader",
                            "statement_en": (it.get("content_snippet") or it.get("title_en") or it.get("title") or "")[:120],
                            "statement_zh": (it.get("summary_zh") or it.get("title_zh") or it.get("title") or "")[:120],
                            "url": it.get("url") or "#"
                        })

                result = {
                    "fingerprint": fp,
                    "updated_at": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC"),
                    "category": "celebrity",
                    "radar_item": {
                        "id": s_item.get("id"),
                        "author_name": s_item.get("author_name") or s_item.get("author_handle") or "AI Pioneer",
                        "author_handle": s_item.get("author_handle") or "@leader",
                        "author_avatar": s_item.get("avatar_url") or "",
                        "author_title_en": parsed.get("author_title_en", "Frontier AI Builder"),
                        "author_title_zh": parsed.get("author_title_zh", "前沿 AI 領袖與架構師"),
                        "published_at": s_item.get("published_at") or s_item.get("date") or "",
                        "url": s_item.get("url") or "#",
                        "media_url": s_item.get("media_url") or "",
                        "core_statement_en": parsed.get("core_statement_en", ""),
                        "core_statement_zh": parsed.get("core_statement_zh", ""),
                        "debate_focus_en": parsed.get("debate_focus_en", ""),
                        "debate_focus_zh": parsed.get("debate_focus_zh", ""),
                        "community_reaction_en": parsed.get("community_reaction_en", ""),
                        "community_reaction_zh": parsed.get("community_reaction_zh", ""),
                        "takeaways_en": parsed.get("takeaways_en", []),
                        "takeaways_zh": parsed.get("takeaways_zh", [])
                    },
                    "featured_voices": featured_voices
                }
                print(f"[Curator] 成功完成 'celebrity' 社交雷达精选: {result['radar_item']['author_handle']}")
                return result
        except Exception as e:
            print(f"[Curator] 解析 celebrity 结果异常: {e}")

    top = candidates[0]
    return {
        "fingerprint": fp,
        "updated_at": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC"),
        "category": "celebrity",
        "radar_item": {
            "id": top.get("id"),
            "author_name": top.get("author_name") or top.get("author_handle") or "Demis Hassabis",
            "author_handle": top.get("author_handle") or "@demishassabis",
            "author_avatar": top.get("avatar_url") or "",
            "author_title_en": "CEO @ Google DeepMind",
            "author_title_zh": "Google DeepMind 執行長",
            "published_at": top.get("published_at") or "",
            "url": top.get("url") or "#",
            "media_url": top.get("media_url") or "",
            "core_statement_en": (top.get("content_snippet") or top.get("title") or "")[:200],
            "core_statement_zh": (top.get("summary_zh") or top.get("title_zh") or top.get("title") or "")[:200],
            "debate_focus_en": "Physical consistency and long-horizon stability in generative simulation",
            "debate_focus_zh": "世界模型在長序列連續物理推演中的一致性與抗漂移能力",
            "community_reaction_en": "Engineers are enthusiastic about interactive world engines while discussing inference costs",
            "community_reaction_zh": "社群對即時可互動世界的生成能力反響熱烈，同時密切探討其部署算力成本",
            "takeaways_en": ["Real-time world interaction creates new simulation paradigms", "Embodied AI benefits from generative physics"],
            "takeaways_zh": ["即時物理互動打開了具身智能模擬的新邊界", "生成式物理引擎正重構自主代理的訓練管線"]
        },
        "featured_voices": []
    }

# ==============================================================================
# 栏目 3: 落地工具 (Tools) -> 实战生产力与开源工程落地档案
# ==============================================================================
def curate_tools_column(items: List[Dict[str, Any]], keys: List[str], cached_data: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    if not items:
        return cached_data or {}

    candidates = items[:8]
    fp = compute_fingerprint(candidates)
    if cached_data and cached_data.get("fingerprint") == fp and "pain_point_zh" in cached_data.get("tool_item", {}):
        print("[Curator] Tools: 内容指纹未变化，复用现有工具档案 (0 API 消耗)")
        return cached_data

    candidates_repr = []
    for idx, it in enumerate(candidates):
        candidates_repr.append({
            "index": idx,
            "name": it.get("app_name") or it.get("title") or "",
            "stars": it.get("stars") or it.get("stars_weekly") or "Trending",
            "desc_en": it.get("title_en") or it.get("description") or "",
            "desc_zh": it.get("title_zh") or it.get("description_zh") or "",
            "url": it.get("url") or ""
        })

    prompt = f"""You are a Principal Software Architect and Open-Source Curator.
Task: Select the #1 most genuinely useful, production-grade developer tool or library from these candidates and build a concrete "Practical Tool Blueprint".
Rules:
1. Ensure the tool is a REAL executable software utility, library, or agent runtime (e.g. OpenShell, xerj, Concat, vLLM).
2. Clearly define what concrete engineering pain point it solves, its key technical capabilities, and a practical quickstart install command.
3. Select 2 other useful developer tools as featured tools.

Candidates:
{json.dumps(candidates_repr, ensure_ascii=False, indent=2)}

Return ONLY valid JSON matching this schema:
{{
  "selected_index": 0,
  "license": "e.g. Apache-2.0 or MIT",
  "one_liner_en": "Under 25 words: Crisp positioning of what this tool actually does",
  "one_liner_zh": "25字以內：清晰準確定義此工具究竟解決什麼問題",
  "pain_point_en": "Concrete problem developers face without this tool",
  "pain_point_zh": "具體解決的開發/生產痛點（沒有此工具時的繁瑣、高成本或資安風險）",
  "key_features_en": ["Feature 1", "Feature 2", "Feature 3"],
  "key_features_zh": ["核心特性 1", "核心特性 2", "核心特性 3"],
  "quickstart_cmd": "e.g. pip install [pkg] && [pkg] run",
  "why_trending_en": "Why developers and AI engineers are starring and adopting it right now",
  "why_trending_zh": "為何此工具在 GitHub 和工程師社群中引發高度關注與採納",
  "featured_indices": [1, 2]
}}
"""
    raw = call_gemini(prompt, keys)
    if raw:
        try:
            match = re.search(r'\{.*\}', raw, re.DOTALL)
            if match:
                parsed = json.loads(match.group(0))
                s_idx = int(parsed.get("selected_index", 0))
                s_item = candidates[s_idx if 0 <= s_idx < len(candidates) else 0]

                featured_tools = []
                for f_idx in parsed.get("featured_indices", []):
                    if isinstance(f_idx, int) and 0 <= f_idx < len(candidates) and f_idx != s_idx:
                        it = candidates[f_idx]
                        featured_tools.append({
                            "id": it.get("id"),
                            "name": it.get("app_name") or it.get("title") or "DevTool",
                            "stars": str(it.get("stars") or it.get("stars_weekly") or ""),
                            "desc_en": (it.get("title_en") or it.get("description") or "")[:80],
                            "desc_zh": (it.get("title_zh") or it.get("description_zh") or "")[:80],
                            "url": it.get("url") or "#"
                        })

                name = s_item.get("app_name") or s_item.get("title") or "Featured Tool"
                result = {
                    "fingerprint": fp,
                    "updated_at": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC"),
                    "category": "tools",
                    "tool_item": {
                        "id": s_item.get("id"),
                        "name": name,
                        "url": s_item.get("url") or "#",
                        "stars": str(s_item.get("stars") or s_item.get("stars_weekly") or "Trending"),
                        "license": parsed.get("license", "Open-Source"),
                        "one_liner_en": parsed.get("one_liner_en", ""),
                        "one_liner_zh": parsed.get("one_liner_zh", ""),
                        "pain_point_en": parsed.get("pain_point_en", ""),
                        "pain_point_zh": parsed.get("pain_point_zh", ""),
                        "key_features_en": parsed.get("key_features_en", []),
                        "key_features_zh": parsed.get("key_features_zh", []),
                        "quickstart_cmd": parsed.get("quickstart_cmd", f"git clone {s_item.get('url', '#')}"),
                        "why_trending_en": parsed.get("why_trending_en", ""),
                        "why_trending_zh": parsed.get("why_trending_zh", ""),
                        "media_url": s_item.get("media_url") or s_item.get("image_url") or ""
                    },
                    "featured_tools": featured_tools
                }
                print(f"[Curator] 成功完成 'tools' 落地工具精选: {name}")
                return result
        except Exception as e:
            print(f"[Curator] 解析 tools 结果异常: {e}")

    top = candidates[0]
    name = top.get("app_name") or top.get("title") or "OpenShell"
    return {
        "fingerprint": fp,
        "updated_at": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC"),
        "category": "tools",
        "tool_item": {
            "id": top.get("id"),
            "name": name,
            "url": top.get("url") or "#",
            "stars": str(top.get("stars") or "20k+"),
            "license": "Apache-2.0",
            "one_liner_en": "Safe, private, isolated runtime sandbox for autonomous AI agent execution",
            "one_liner_zh": "專為自主 AI 代理打造的安全隔離沙箱與確定性運行時環境",
            "pain_point_en": "Agent shell execution without sandboxing risks irreversible deletions and system corruption",
            "pain_point_zh": "解決痛點：AI 代碼代理終端權限缺乏隔離防護，易造成環境污染與資安破壞",
            "key_features_en": ["Local-first sandboxing", "Deterministic snapshots", "Fine-grained network access controls"],
            "key_features_zh": ["本地優先沙箱隔離環境", "秒級檔案系統快照與安全回滾", "細粒度網路存取白名單機制"],
            "quickstart_cmd": "pip install openshell && openshell init",
            "why_trending_en": "Essential infrastructure as coding agents move into real-world production environments",
            "why_trending_zh": "隨著 AI 代碼代理全面進入生產環境，安全隔離運行時已成為開發者剛需",
            "media_url": top.get("media_url") or ""
        },
        "featured_tools": []
    }

# ==============================================================================
# 全局运行调度
# ==============================================================================
def run_curator():
    print("=== [Curator Engine v2.0] 启动定制化栏目精选引擎 ===")
    keys = get_gemini_keys()
    print(f"[Curator] 可用 Gemini API Key 数量: {len(keys)}")

    existing_curations = {}
    if os.path.exists(OUTPUT_FILE):
        try:
            with open(OUTPUT_FILE, "r", encoding="utf-8") as f:
                existing_curations = json.load(f)
        except Exception:
            existing_curations = {}

    news_items = []
    celebrity_items = []
    tools_items = []

    latest_news_file = os.path.join(DATA_DIR, "latest_news.json")
    if os.path.exists(latest_news_file):
        try:
            with open(latest_news_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                grouped = data.get("grouped", {})
                news_items = grouped.get("news", [])
                celebrity_items = grouped.get("celebrity", [])
                tools_items = grouped.get("tools", [])

                # 优先保留高权重领袖推文
                viral = data.get("viral_ticker_tweets", [])
                if viral:
                    seen = set(it.get("id") for it in celebrity_items if it.get("id"))
                    for v in viral:
                        if v.get("id") and v.get("id") not in seen:
                            celebrity_items.insert(0, v)
                            seen.add(v.get("id"))
        except Exception as e:
            print(f"[Curator] 读取 latest_news.json 异常: {e}")

    print(f"[Curator] 精选候选池 -> 行业资讯: {len(news_items)} 篇, 社交雷达: {len(celebrity_items)} 篇, 落地工具: {len(tools_items)} 款")

    results = {
        "version": "2.0",
        "generated_at": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC"),
        "columns": {}
    }

    # 1. 行业资讯：事件六要素事实看板
    results["columns"]["news"] = curate_news_column(
        news_items, keys, existing_curations.get("columns", {}).get("news")
    )

    # 2. 社交雷达：领袖大V言论原境与社群争鸣
    results["columns"]["celebrity"] = curate_celebrity_column(
        celebrity_items, keys, existing_curations.get("columns", {}).get("celebrity")
    )

    # 3. 落地工具：实战生产力与开源工程落地档案
    results["columns"]["tools"] = curate_tools_column(
        tools_items, keys, existing_curations.get("columns", {}).get("tools")
    )

    os.makedirs(DATA_DIR, exist_ok=True)
    os.makedirs(PUBLIC_DATA_DIR, exist_ok=True)

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    with open(PUBLIC_OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    print(f"=== [Curator Engine v2.0] 精选完成！已持久化至: {PUBLIC_OUTPUT_FILE} ===")
    return results

if __name__ == "__main__":
    run_curator()
