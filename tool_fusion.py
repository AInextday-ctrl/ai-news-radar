# -*- coding: utf-8 -*-
"""
tool_fusion.py
Industrial-grade Triple-Fingerprint Deduplication & Multi-Source Smart Fusion Engine
for AI Radar News & Tools.

Eliminates cross-source duplicates between GitHub Trending, Product Hunt, Hugging Face,
and Curated Baseline libraries through 3 complementary fingerprints:
1. Normalized Name Fingerprint (name_fp)
2. Repository Fingerprint (repo_fp)
3. Apex Domain Fingerprint (domain_fp)

Performs intelligent attribute fusion (best-of-both-worlds) rather than naive dropping.
"""

import re
import urllib.parse
from typing import Dict, Any, List, Optional, Tuple, Set

# Non-tool repository names and prefixes
BAD_TOOL_REPO_NAMES = {
    "free-for-dev", "free-programming-books", "build-your-own-x",
    "awesome-python", "awesome-machine-learning", "awesome-deep-learning",
    "developer-roadmap", "coding-interview-university", "system-design-primer",
    "public-apis", "awesome-go", "awesome-rust", "awesome-react",
    "freeCodeCamp", "papers-we-love", "Web-Dev-For-Beginners",
    "ML-For-Beginners", "Data-Science-For-Beginners", "Generative-AI-For-Beginners",
    "huggingface/transformers", "pytorch/pytorch", "tensorflow/tensorflow",
    "f/awesome-chatgpt-prompts", "PlexPt/awesome-chatgpt-prompts-zh",
    "linexjlin/GPTs", "ai-boost/awesome-prompts", "instructlab/instructlab",
    "cursor/plugins", "heretic", "p-e-w/heretic", "diagram-design"
}

# Domains that represent generic hosting, communities, or aggregators (cannot be used as apex identity)
GENERIC_PLATFORM_DOMAINS = {
    "github.com", "github.io", "gitlab.com", "gitee.com",
    "huggingface.co", "hf.space",
    "producthunt.com",
    "x.com", "twitter.com",
    "youtube.com", "youtu.be",
    "bilibili.com",
    "reddit.com", "discord.gg", "discord.com", "t.me", "telegram.org",
    "medium.com", "substack.com", "notion.site", "notion.so",
    "arxiv.org", "wikipedia.org", "google.com", "apple.com"
}

GENERIC_NAMES = {
    "ai", "agent", "agents", "tool", "tools", "assistant", "model", "models",
    "search", "editor", "app", "workspace", "platform", "studio", "chat",
    "bot", "copilot", "cli", "sdk", "api", "framework", "library"
}

def clean_app_name(raw_name: str) -> str:
    """Strip bracketed tags, subtitles, and trailing category descriptors from raw titles/names."""
    if not raw_name:
        return ""
    s = str(raw_name).strip()
    s = re.sub(r'^[【\[].*?[】\]]\s*', '', s).strip()
    # If it contains subtitle like 'Name: Tagline' or 'Name - Tagline', take first segment
    if ' - ' in s and len(s.split(' - ')[0]) <= 25:
        s = s.split(' - ')[0].strip()
    elif ': ' in s and len(s.split(': ')[0]) <= 25:
        s = s.split(': ')[0].strip()
    elif '：' in s and len(s.split('：')[0]) <= 25:
        s = s.split('：')[0].strip()

    # Strip common descriptive suffixes often appended on Product Hunt / directories
    s = re.sub(r'\s+(?:video editor|ai editor|code editor|desktop client|desktop app|web app|ai assistant|assistant|generator|workflow)\b.*$', '', s, flags=re.I).strip()
    return s.strip()

def normalize_name_fingerprint(name: str) -> Optional[str]:
    """
    Fingerprint 1: Normalized Name Fingerprint
    Removes all non-alphanumeric characters, converts to lowercase.
    'Claude-Code', 'Claude Code', 'claude_code' all map to 'claudecode'.
    """
    cleaned = clean_app_name(name)
    norm = re.sub(r'[^a-z0-9]', '', cleaned.lower())
    if not norm or len(norm) < 2:
        return None
    if norm in GENERIC_NAMES and len(norm) <= 5:
        return None
    return f"nm:{norm}"

def extract_repo_fingerprint(item: Dict[str, Any]) -> Optional[str]:
    """
    Fingerprint 2: Repository Fingerprint
    Deep scans url, official_url, demo_url, source_url, homepage for GitHub / HuggingFace repos.
    """
    urls_to_check = [
        str(item.get("url") or ""),
        str(item.get("official_url") or ""),
        str(item.get("demo_url") or ""),
        str(item.get("source_url") or ""),
        str(item.get("homepage") or ""),
        str(item.get("github_url") or "")
    ]
    combined_urls = " ".join(urls_to_check)

    # 1. GitHub repo check
    gh_match = re.search(r'github\.com/([a-zA-Z0-9_\-\.]+)/([a-zA-Z0-9_\-\.]+)', combined_urls, re.IGNORECASE)
    if gh_match:
        owner = gh_match.group(1).lower()
        repo = gh_match.group(2).lower().rstrip('.git')
        # Filter out non-repo routes
        if owner not in {"features", "topics", "trending", "explore", "search", "settings", "site", "about"}:
            if not repo.endswith((".png", ".jpg", ".jpeg", ".svg", ".json")):
                return f"gh:{owner}/{repo}"

    # 2. Hugging Face Space check
    hf_match = re.search(r'huggingface\.co/spaces/([a-zA-Z0-9_\-\.]+)/([a-zA-Z0-9_\-\.]+)', combined_urls, re.IGNORECASE)
    if hf_match:
        return f"hf:{hf_match.group(1).lower()}/{hf_match.group(2).lower()}"

    return None

def extract_apex_domain_fingerprint(item: Dict[str, Any]) -> Optional[str]:
    """
    Fingerprint 3: Apex Domain Fingerprint
    Extracts the root domain of the tool's official website/landing page.
    Filters out generic hosting platforms (github.com, producthunt.com, etc.).
    """
    urls_to_check = [
        str(item.get("official_url") or ""),
        str(item.get("demo_url") or ""),
        str(item.get("homepage") or ""),
        str(item.get("url") or "")
    ]
    for u in urls_to_check:
        if not u or u == "#" or not u.startswith("http"):
            continue
        try:
            parsed = urllib.parse.urlparse(u)
            host = (parsed.hostname or "").lower()
            if not host:
                continue
            # Strip leading www.
            if host.startswith("www."):
                host = host[4:]
            if host in GENERIC_PLATFORM_DOMAINS or any(host.endswith(f".{p}") for p in GENERIC_PLATFORM_DOMAINS):
                continue
            # Basic apex domain extraction: e.g. 'app.cursor.com' -> 'cursor.com'
            parts = host.split('.')
            if len(parts) >= 2:
                apex = ".".join(parts[-2:]) if len(parts[-1]) >= 2 else host
                return f"dom:{apex}"
        except Exception:
            continue
    return None

def extract_tool_fingerprints(item: Dict[str, Any]) -> Set[str]:
    """Extract all valid fingerprints for a candidate tool."""
    fps = set()
    name = item.get("app_name") or item.get("title") or ""
    n_fp = normalize_name_fingerprint(name)
    if n_fp:
        fps.add(n_fp)

    r_fp = extract_repo_fingerprint(item)
    if r_fp:
        fps.add(r_fp)

    d_fp = extract_apex_domain_fingerprint(item)
    if d_fp:
        fps.add(d_fp)

    return fps

HOUSEHOLD_LEGACY_TOOLS = {
    "cursor", "bolt.new", "bolt", "claude code", "claude-code",
    "ollama", "perplexity", "lm studio", "lmstudio", "whisper",
    "whisper webgpu", "vllm", "comfyui", "dify", "n8n", "gamma",
    "excalidraw", "open-webui", "openwebui", "jan", "kokoro",
    "liveportrait", "mineru", "aider", "openhands", "tripo3d", "triposr"
}

def is_valid_tool_candidate(it: Dict[str, Any]) -> bool:
    """Strict filtering gate: reject non-tools, prompt lists, tutorials, plugins repos, and stale household tools."""
    app_nm = str(it.get("app_name") or it.get("title") or "").strip().lower()
    u_str = (str(it.get("url") or "") + " " + str(it.get("official_url") or "")).lower()

    if not app_nm:
        return False

    # 0. Reject well-known household tools (烂大街的成熟旧工具坚决不入雷达流)
    if app_nm in HOUSEHOLD_LEGACY_TOOLS or any(legacy in app_nm for legacy in ["bolt.new", "claude code", "lm studio", "whisper web"]):
        return False
    if str(it.get("id", "")).startswith("tool-") or it.get("is_curated_base"):
        return False

    # 1. Blacklist check
    if app_nm in BAD_TOOL_REPO_NAMES or any(bad == app_nm for bad in BAD_TOOL_REPO_NAMES):
        return False
    if any(f"/{bad}?" in u_str or f"/{bad}/" in u_str or u_str.endswith(f"/{bad}") for bad in BAD_TOOL_REPO_NAMES):
        return False

    # 2. Keyword/Regex gate for non-tool repositories
    banned_kw = [
        "awesome-", "interview", "roadmap", "tutorial", "papers-with",
        "-skills", "prompts-", "prompt-", "cheatsheet", "free-api",
        "plugins", "-plugins", "collection", "starter-kit", "course",
        "boilerplate"
    ]
    if any(bad in app_nm for bad in banned_kw):
        return False
    # Check url tail
    last_seg = u_str.split('/')[-1].split('?')[0]
    if any(bad in last_seg for bad in banned_kw):
        return False

    # 3. Minimum stars check for GitHub tools
    if it.get("tool_origin") == "github":
        stars = int(it.get("stars") or (it.get("metrics") or {}).get("stars") or 0)
        wk_stars = int(it.get("weekly_stars") or (it.get("metrics") or {}).get("weekly_stars") or 0)
        if stars < 200 and wk_stars < 200:
            return False

    return True

def sanitize_tool_media(it: Dict[str, Any]) -> Dict[str, Any]:
    """Sanitize images, strip fragile microlink and unsplash placeholders, ensure GitHub OpenGraph."""
    u_combined = f"{it.get('url', '')} {it.get('official_url', '')} {it.get('demo_url', '')}"
    gh_match = re.search(r'github\.com/([a-zA-Z0-9_\-\.]+)/([a-zA-Z0-9_\-\.]+)', u_combined, re.IGNORECASE)

    raw_previews = it.get("preview_images") or []
    clean_previews = []
    for img in raw_previews:
        if not img or "microlink.io" in img or "photo-1618005182384-a83a8bd57fbe" in img:
            continue
        clean_previews.append(img)

    cur_img = str(it.get("image_url") or "")
    if "microlink.io" in cur_img or "photo-1618005182384-a83a8bd57fbe" in cur_img:
        cur_img = ""

    if gh_match and not gh_match.group(2).endswith(('.png', '.jpg', '.jpeg', '.svg', '.json', '.')):
        gh_repo = f"{gh_match.group(1)}/{gh_match.group(2).rstrip('.git')}"
        og_url = f"https://opengraph.githubassets.com/1/{gh_repo}"
        if not clean_previews:
            clean_previews = [og_url]
        if not cur_img:
            cur_img = og_url

    it["preview_images"] = clean_previews
    it["image_url"] = cur_img
    return it

def merge_tool_attributes(base: Dict[str, Any], incoming: Dict[str, Any]) -> Dict[str, Any]:
    """
    Smart Multi-Source Fusion:
    Merges two tools that matched on fingerprints into a single best-of-both-worlds card.
    """
    merged = dict(base)

    # 1. App name: prefer properly-cased title over kebab-case repo name
    b_name = base.get("app_name") or ""
    i_name = incoming.get("app_name") or ""
    if '-' in b_name and ' ' in i_name:
        merged["app_name"] = i_name
        merged["app_name_en"] = incoming.get("app_name_en") or i_name
    elif not b_name and i_name:
        merged["app_name"] = i_name

    # 2. URLs & Live Demo: preserve live demo links and GitHub repository
    b_off = base.get("official_url") or ""
    i_off = incoming.get("official_url") or ""
    b_demo = base.get("demo_url") or ""
    i_demo = incoming.get("demo_url") or ""

    # Live demo priority: non-github homepage preferred for live demo
    live_demo_url = None
    for cand in [b_demo, i_demo, b_off, i_off]:
        if cand and cand != "#" and cand.startswith("http") and "github.com" not in cand.lower() and "producthunt.com" not in cand.lower():
            live_demo_url = cand
            break

    if live_demo_url:
        merged["demo_url"] = live_demo_url
        merged["official_url"] = live_demo_url
        merged["has_live_demo"] = True
    else:
        merged["has_live_demo"] = base.get("has_live_demo") or incoming.get("has_live_demo", False)

    # GitHub URL linkage
    for cand in [base.get("url"), incoming.get("url"), base.get("github_url"), incoming.get("github_url")]:
        if cand and "github.com/" in str(cand):
            merged["github_url"] = cand
            break

    # 3. Metrics Fusion: take maximum stars & preserve weekly star surges
    b_stars = int(base.get("stars") or (base.get("metrics") or {}).get("stars") or 0)
    i_stars = int(incoming.get("stars") or (incoming.get("metrics") or {}).get("stars") or 0)
    max_stars = max(b_stars, i_stars)

    b_wk = int(base.get("weekly_stars") or (base.get("metrics") or {}).get("weekly_stars") or 0)
    i_wk = int(incoming.get("weekly_stars") or (incoming.get("metrics") or {}).get("weekly_stars") or 0)
    max_wk = max(b_wk, i_wk)

    if max_stars > 0 or max_wk > 0:
        metrics = merged.get("metrics") or {}
        if max_stars > 0:
            metrics["stars"] = max_stars
            merged["stars"] = max_stars
        if max_wk > 0:
            metrics["weekly_stars"] = max_wk
            merged["weekly_stars"] = max_wk
        merged["metrics"] = metrics

    if max_wk >= 250 or base.get("is_breakout") or incoming.get("is_breakout"):
        merged["is_breakout"] = True

    # 4. Badges: prioritize breakout surge badge if available
    if max_wk >= 250:
        if not merged.get("growth_badge_zh") or "热门" in merged["growth_badge_zh"]:
            merged["growth_badge_zh"] = f"📈 本周飙升 +{max_wk:,} ★"
            merged["growth_badge_en"] = f"📈 +{max_wk:,} ★/wk"

    # 5. Media Assets: combine previews, deduplicate, avoid loss
    b_previews = base.get("preview_images") or []
    i_previews = incoming.get("preview_images") or []
    combined_previews = []
    seen_imgs = set()
    for img in b_previews + i_previews:
        if img and img not in seen_imgs and "microlink.io" not in img and "photo-1618005182384-a83a8bd57fbe" not in img:
            seen_imgs.add(img)
            combined_previews.append(img)
    merged["preview_images"] = combined_previews
    if not merged.get("image_url") and combined_previews:
        merged["image_url"] = combined_previews[0]

    # Logo
    if not merged.get("logo_url") and incoming.get("logo_url"):
        merged["logo_url"] = incoming["logo_url"]

    # 6. Localization & Text Copy: prefer richer Chinese text
    b_zh = base.get("overview_zh") or base.get("summary_zh") or ""
    i_zh = incoming.get("overview_zh") or incoming.get("summary_zh") or ""
    if len(i_zh) > len(b_zh) + 20 and not base.get("is_curated_base"):
        merged["overview_zh"] = incoming.get("overview_zh") or merged.get("overview_zh")
        merged["summary_zh"] = incoming.get("summary_zh") or merged.get("summary_zh")
        merged["features_zh"] = incoming.get("features_zh") or merged.get("features_zh")

    # 7. Curated Baseline flag
    if base.get("is_curated_base") or incoming.get("is_curated_base"):
        merged["is_curated_base"] = True

    return sanitize_tool_media(merged)

def fuse_and_deduplicate_tools(sources_lists: List[List[Dict[str, Any]]]) -> List[Dict[str, Any]]:
    """
    Main entry point for multi-source tool aggregation.
    Takes arbitrary lists of tool candidates (e.g. [curated_tools, crawled_github, crawled_ph, existing_tools]),
    detects collisions across (name_fp, repo_fp, domain_fp),
    and executes smart attribute fusion.
    """
    clean_pool: List[Dict[str, Any]] = []
    
    # Indexes pointing to index in clean_pool
    name_index: Dict[str, int] = {}
    repo_index: Dict[str, int] = {}
    domain_index: Dict[str, int] = {}

    for source in sources_lists:
        for raw_item in source:
            if not is_valid_tool_candidate(raw_item):
                continue

            item = sanitize_tool_media(dict(raw_item))
            fps = extract_tool_fingerprints(item)
            if not fps:
                continue

            # Check if any fingerprint collides with an existing item in clean_pool
            matched_idx: Optional[int] = None
            for fp in fps:
                if fp.startswith("gh:") or fp.startswith("hf:"):
                    if fp in repo_index:
                        matched_idx = repo_index[fp]
                        break
                elif fp.startswith("dom:"):
                    if fp in domain_index:
                        matched_idx = domain_index[fp]
                        break
                elif fp.startswith("nm:"):
                    if fp in name_index:
                        matched_idx = name_index[fp]
                        break

            if matched_idx is not None:
                # Collision detected -> Smart attribute fusion!
                existing_item = clean_pool[matched_idx]
                fused_item = merge_tool_attributes(existing_item, item)
                clean_pool[matched_idx] = fused_item

                # Register any new fingerprints discovered on fused_item
                new_fps = extract_tool_fingerprints(fused_item)
                for nfp in new_fps:
                    if nfp.startswith("gh:") or nfp.startswith("hf:"):
                        repo_index[nfp] = matched_idx
                    elif nfp.startswith("dom:"):
                        domain_index[nfp] = matched_idx
                    elif nfp.startswith("nm:"):
                        name_index[nfp] = matched_idx
            else:
                # Brand new item -> register in pool and indexes
                new_idx = len(clean_pool)
                clean_pool.append(item)
                for fp in fps:
                    if fp.startswith("gh:") or fp.startswith("hf:"):
                        repo_index[fp] = new_idx
                    elif fp.startswith("dom:"):
                        domain_index[fp] = new_idx
                    elif fp.startswith("nm:"):
                        name_index[fp] = new_idx

    return clean_pool

def rank_radar_stream(fused_tools: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Ranks the fused tools according to Radar First policy:
    1. Fresh Breakout Discoveries (weekly_stars >= 250 or is_breakout, non-static) placed at the top!
    2. Rich Scenario Foundation Library (curated standards & steady tools) interleaved below.
    """
    breakout_tools = []
    regular_tools = []

    for x in fused_tools:
        wk = int(x.get("weekly_stars") or (x.get("metrics") or {}).get("weekly_stars") or 0)
        is_bo = bool(x.get("is_breakout"))
        is_curated_base = bool(x.get("is_curated_base") or str(x.get("id", "")).startswith("tool-"))

        if (wk >= 250 or is_bo) and not is_curated_base:
            breakout_tools.append(x)
        else:
            regular_tools.append(x)

    # Sort breakout tools by weekly star surge descending
    breakout_tools.sort(key=lambda x: (
        int(x.get("weekly_stars") or (x.get("metrics") or {}).get("weekly_stars") or 0),
        int(x.get("utility_score") or 80)
    ), reverse=True)

    # Categorize regular tools by origin and interleave
    web_r = [x for x in regular_tools if x.get("tool_origin") == "web"]
    gh_r = [x for x in regular_tools if x.get("tool_origin") == "github"]
    hf_r = [x for x in regular_tools if x.get("tool_origin") == "huggingface"]
    other_r = [x for x in regular_tools if x.get("tool_origin") not in ("web", "github", "huggingface")]

    web_r.sort(key=lambda x: int(x.get("utility_score") or 85), reverse=True)
    gh_r.sort(key=lambda x: (
        int(x.get("weekly_stars") or (x.get("metrics") or {}).get("weekly_stars") or 0),
        int(x.get("utility_score") or 80),
        int(x.get("stars") or (x.get("metrics") or {}).get("stars") or 0)
    ), reverse=True)
    hf_r.sort(key=lambda x: int(x.get("utility_score") or 85), reverse=True)

    interleaved_reg = []
    wi, gi, hi = 0, 0, 0
    while wi < len(web_r) or gi < len(gh_r) or hi < len(hf_r):
        for _ in range(2):
            if wi < len(web_r):
                interleaved_reg.append(web_r[wi])
                wi += 1
        for _ in range(2):
            if gi < len(gh_r):
                interleaved_reg.append(gh_r[gi])
                gi += 1
        if hi < len(hf_r):
            interleaved_reg.append(hf_r[hi])
            hi += 1
    interleaved_reg.extend(other_r)

    return breakout_tools + interleaved_reg
