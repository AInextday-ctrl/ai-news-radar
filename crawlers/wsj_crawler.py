#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
=============================================================================
WSJ Dedicated Crawler & Editorial / Wayback / Syndication Penetration Engine
=============================================================================
Source: The Wall Street Journal (华尔街日报 / wsj.com)
Scope: Handles all wsj.com article extraction, authentic WSJ editorial headline
       resolution, journalist byline attribution, official images.wsj.net HD
       photography localization, and multi-tier full-text reporting penetration.

Architecture & Penetration Strategy:
1. Tier 1 — Direct / Supplied HTML DOM Extractor:
   - Parses supplied or unblocked WSJ HTML, strips inline <style>/<script> nodes,
     removes Dow Jones ticker widget text ("NVDA -0.44%decrease; down pointing triangle")
     and Dow Jones copyright footers.
2. Tier 2 — Official WSJ Headline, Author & Wayback Master Photography Resolver:
   - Resolves exact authentic WSJ headlines via Google News RSS (`site:wsj.com "<slug>"`),
     eliminating synthetic Techmeme headlines and stripping "Exclusive | " / " - WSJ" tags.
   - Extracts journalist bylines from JSON-LD, Wayback snapshots, or Techmeme attribution.
   - Queries Wayback Machine availability to recover authentic 1280px `images.wsj.net`
     master photography (requested as native JPEG) and verbatim WSJ lead paragraphs.
3. Tier 3 — Strict Entity-Verified Corroborated Full-Text Penetration:
   - When WSJ's hard subscriber paywall truncates the body (< 5 paragraphs), resolves
     authoritative open reporting (MarketScreener, TechCrunch, CNBC, Axios, Yahoo Finance,
     Crunchbase News, Quartz, BBC, The Verge, SiliconANGLE, Reuters syndications) with
     strict entity overlap checks so unrelated articles can never contaminate the story.
4. Substantive Quality Contract:
   - Populates `full_text`, `article_content`, `article_content_en`, `paragraphs`,
     `cover_image`, `image_url`, `is_substantive = True`, `is_paywalled = False`.
   - Persists verified results in `data/wsj_cache.json`.

Separation of Concerns:
- Completely isolated from locked Reuters, Bloomberg, and Fortune crawlers.
=============================================================================
"""

import os
import re
import html
import json
import hashlib
import urllib.request
import urllib.parse
import xml.etree.ElementTree as ET
from typing import Dict, Any, List, Optional

try:
    from curl_cffi import requests as cffi_requests
    HAS_CURL_CFFI = True
except ImportError:
    cffi_requests = None
    HAS_CURL_CFFI = False

try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    requests = None
    HAS_REQUESTS = False

try:
    from selectolax.lexbor import LexborHTMLParser
    HAS_SELECTOLAX = True
except ImportError:
    LexborHTMLParser = None
    HAS_SELECTOLAX = False

try:
    import googlenewsdecoder
    HAS_GNEWS_DECODER = True
except ImportError:
    googlenewsdecoder = None
    HAS_GNEWS_DECODER = False


_WSJ_CACHE: Dict[str, Dict[str, Any]] = {}
_DISK_CACHE_FILE = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "data",
    "wsj_cache.json"
)

DEFAULT_PROXIES = ["http://127.0.0.1:7890", "http://127.0.0.1:7897"]

STOPWORDS = {
    "the", "and", "for", "with", "from", "into", "over", "amid", "after", "that",
    "this", "says", "said", "will", "plans", "plan", "about", "more", "than",
    "have", "been", "being", "their", "they", "what", "when", "where", "how",
    "why", "new", "its", "are", "was", "were", "has", "had", "not", "but", "all",
    "out", "can", "could", "would", "should", "may", "might", "also", "other",
    "exclusive", "sources", "wsj", "wall", "street", "journal", "startup", "company"
}


def is_wsj_url(url: str) -> bool:
    """Checks whether the given URL belongs to The Wall Street Journal."""
    if not url:
        return False
    u = url.lower()
    return "wsj.com" in u or "dowjones.com" in u


def _get_proxies() -> Optional[Dict[str, str]]:
    """Detects available environment or local network proxy (7890/7897)."""
    env_https = os.environ.get("HTTPS_PROXY") or os.environ.get("https_proxy")
    env_http = os.environ.get("HTTP_PROXY") or os.environ.get("http_proxy")
    if env_https or env_http:
        return {"http": env_http or env_https, "https": env_https or env_http}
    for p in DEFAULT_PROXIES:
        try:
            import socket
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(0.3)
            host, port = p.replace("http://", "").split(":")
            if sock.connect_ex((host, int(port))) == 0:
                sock.close()
                return {"http": p, "https": p}
            sock.close()
        except Exception:
            pass
    return None


def _is_valid_wsj_image(img_url: Optional[str]) -> bool:
    """Validates that a cover image URL is absolute and non-placeholder."""
    if not img_url or not isinstance(img_url, str):
        return False
    u = img_url.strip()
    if not (u.startswith("http://") or u.startswith("https://")):
        return False
    low = u.lower()
    bad_tokens = [
        "unsplash.com", "placeholder", "logo", "icon", "pixel", "avatar",
        "banner", "favicon", "default-share", "og-default", "news-story",
        "tradingview.com/static", "promo_area", "wsj-logo", "dj_logo",
        "1x1", "spacer", "fallback/", "twitter_ms_", "web-assets/images/editorial"
    ]
    return not any(b in low for b in bad_tokens)


def _strip_wayback_prefix(url: str) -> str:
    """Strips web.archive.org/web/<ts>im_/ prefix to recover original CDN URL."""
    if not url:
        return ""
    m = re.search(r'web\.archive\.org/web/\d+[a-z_]*/(https?://.+)$', url)
    if m:
        return m.group(1)
    return url


def _clean_wsj_title(raw_title: str) -> str:
    """Cleans WSJ editorial headlines (removes 'Exclusive | ', ' - WSJ', etc.)."""
    if not raw_title:
        return ""
    t = html.unescape(raw_title).strip()
    t = re.sub(r'^(?:Exclusive|EXCLUSIVE|WSJ Exclusive|Opinion|Heard on the Street)\s*[|:\-]\s*', '', t, flags=re.I)
    t = re.sub(r'\s*[-|]\s*(?:WSJ|The Wall Street Journal|Wall Street Journal)\s*$', '', t, flags=re.I)
    t = re.sub(r'\s+', ' ', t).strip()
    return t


def _clean_wsj_paragraph(text: str) -> str:
    """Cleans WSJ/syndicated paragraph text and removes Dow Jones ticker & boilerplate noise."""
    if not text:
        return ""
    t = html.unescape(text)
    t = re.sub(r'<style[^>]*>.*?</style>', ' ', t, flags=re.DOTALL | re.I)
    t = re.sub(r'<script[^>]*>.*?</script>', ' ', t, flags=re.DOTALL | re.I)
    t = re.sub(r'<[^>]+>', ' ', t)
    t = re.sub(r'[\u200b\u200c\u200d\u2060\ufeff\xa0]', ' ', t)
    # Strip WSJ inline CSS/ticker artifacts e.g. "NVDA -0.44%decrease; down pointing triangle"
    t = re.sub(r'\.css-[a-z0-9\-_]+\{[^}]*\}', ' ', t, flags=re.I)
    t = re.sub(r'\s+[A-Z]{1,5}\s*[+-]?\d+(?:\.\d+)?%\s*(?:increase|decrease);\s*(?:up|down)\s+pointing\s+triangle', '', t, flags=re.I)
    t = re.sub(r'\s+', ' ', t).strip()

    low = t.lower()
    noise_phrases = [
        "copyright ©", "dow jones & company", "all rights reserved",
        "subscribe to wsj", "sign in to read", "continue reading your article",
        "already a subscriber", "what to read next", "more from the wall street journal",
        "write to ", "newsletter sign-up", "get the latest", "listen to article",
        "terms of use", "privacy notice", "cookie notice", "do not sell",
        "advertisement", "sponsored content", "our standards: the thomson reuters",
        "want more tech news", "sign up for", "techcrunch event", "disrupt 2026"
    ]
    if any(np in low for np in noise_phrases):
        if len(t) < 350:
            return ""
    if t.startswith("FILE PHOTO:") or t.startswith("Photo:"):
        return ""
    return t


def _get_from_disk_cache(canonical_url: str) -> Optional[Dict[str, Any]]:
    if os.path.exists(_DISK_CACHE_FILE):
        try:
            with open(_DISK_CACHE_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data.get(canonical_url)
        except Exception:
            pass
    return None


def _save_to_disk_cache(canonical_url: str, data: Dict[str, Any]) -> None:
    try:
        os.makedirs(os.path.dirname(_DISK_CACHE_FILE), exist_ok=True)
        current = {}
        if os.path.exists(_DISK_CACHE_FILE):
            with open(_DISK_CACHE_FILE, "r", encoding="utf-8") as f:
                current = json.load(f)
        current[canonical_url] = data
        with open(_DISK_CACHE_FILE, "w", encoding="utf-8") as f:
            json.dump(current, f, ensure_ascii=False, indent=2)
    except Exception:
        pass


def _localize_wsj_image(img_url: str, canonical_url: str, proxies: Optional[Dict[str, str]] = None) -> str:
    """Downloads authentic WSJ/editorial photography locally as JPEG to public/images/wsj_<hash>.jpg."""
    clean_img = _strip_wayback_prefix(img_url)
    if not _is_valid_wsj_image(clean_img):
        return clean_img
    if "ainewsradar.xyz/images/" in clean_img or "images.wsj.net/sample_" in clean_img:
        return clean_img

    # Upgrade images.wsj.net social image to 1280px width
    download_url = clean_img
    if "images.wsj.net/im-" in download_url and "width=" not in download_url:
        sep = "&" if "?" in download_url else "?"
        download_url = f"{download_url}{sep}width=1280"

    try:
        img_id = hashlib.md5(canonical_url.encode("utf-8")).hexdigest()[:16]
        filename = f"wsj_{img_id}.jpg"
        local_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "public", "images", filename
        )
        cdn_url = f"https://ainewsradar.xyz/images/{filename}"
        if os.path.exists(local_path) and os.path.getsize(local_path) > 5000:
            return cdn_url

        # Request JPEG/PNG explicitly (avoid AVIF so social OG crawlers and all browsers render cleanly)
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
            "Accept": "image/jpeg,image/png,image/webp,*/*;q=0.8",
            "Referer": "https://www.wsj.com/"
        }
        content = None
        if HAS_CURL_CFFI:
            try:
                r = cffi_requests.get(download_url, impersonate="chrome120", headers=headers, proxies=proxies, timeout=12)
                if r.status_code == 200 and len(r.content) > 5000 and r.headers.get("content-type", "").startswith("image/"):
                    content = r.content
            except Exception:
                pass
        if not content and HAS_REQUESTS:
            try:
                r = requests.get(download_url, headers=headers, proxies=proxies, timeout=12)
                if r.status_code == 200 and len(r.content) > 5000 and r.headers.get("content-type", "").startswith("image/"):
                    content = r.content
            except Exception:
                pass
        if content:
            os.makedirs(os.path.dirname(local_path), exist_ok=True)
            with open(local_path, "wb") as f:
                f.write(content)
            return cdn_url
    except Exception:
        pass
    return clean_img


def _extract_wsj_dom(html_text: str) -> Dict[str, Any]:
    """Extracts headline, author, og:image, and clean paragraphs from WSJ HTML (direct or Wayback)."""
    out: Dict[str, Any] = {"title": "", "author": "", "cover_image": None, "paragraphs": []}
    if not html_text:
        return out

    # JSON-LD check
    for ld_raw in re.findall(r'<script[^>]+type=["\']application/ld\+json["\'][^>]*>(.*?)</script>', html_text, re.DOTALL | re.I):
        try:
            ld = json.loads(ld_raw)
            objs = ld if isinstance(ld, list) else [ld]
            for obj in objs:
                if isinstance(obj, dict) and obj.get("@type") in ("NewsArticle", "Article"):
                    if obj.get("headline") and not out["title"]:
                        out["title"] = _clean_wsj_title(str(obj["headline"]))
                    auth = obj.get("author")
                    if auth and not out["author"]:
                        if isinstance(auth, list):
                            names = [a.get("name") for a in auth if isinstance(a, dict) and a.get("name")]
                            if names:
                                out["author"] = " and ".join(names)
                        elif isinstance(auth, dict) and auth.get("name"):
                            out["author"] = str(auth["name"])
                        elif isinstance(auth, str):
                            out["author"] = auth
                    img = obj.get("image")
                    if img and not out["cover_image"]:
                        cand = img[0] if isinstance(img, list) and img else (img.get("url") if isinstance(img, dict) else img)
                        if isinstance(cand, dict):
                            cand = cand.get("url")
                        cand = _strip_wayback_prefix(str(cand or ""))
                        if _is_valid_wsj_image(cand):
                            out["cover_image"] = cand
        except Exception:
            continue

    if HAS_SELECTOLAX:
        tree = LexborHTMLParser(html_text)
        if not out["title"]:
            h1 = tree.css_first("h1")
            if h1 and len(h1.text().strip()) > 10:
                out["title"] = _clean_wsj_title(h1.text().strip())
        if not out["title"]:
            og_t = tree.css_first('meta[property="og:title"]')
            if og_t and og_t.attributes.get("content"):
                out["title"] = _clean_wsj_title(og_t.attributes["content"])
        if not out["cover_image"]:
            og_i = tree.css_first('meta[property="og:image"]') or tree.css_first('meta[name="twitter:image"]')
            if og_i and og_i.attributes.get("content"):
                cand = _strip_wayback_prefix(og_i.attributes["content"].strip())
                if _is_valid_wsj_image(cand):
                    out["cover_image"] = cand

        # Remove style/script before extracting paragraph text
        for bad in tree.css("style, script, noscript, nav, footer, aside"):
            bad.decompose()
        paras = []
        nodes = tree.css('article p, p[data-type="paragraph"], section[data-type="article-body"] p')
        for p in nodes:
            cp = _clean_wsj_paragraph(p.text())
            if cp and len(cp) >= 35 and cp not in paras:
                paras.append(cp)
        out["paragraphs"] = paras
    else:
        if not out["title"]:
            m_t = re.search(r'<meta[^>]+property=["\']og:title["\'][^>]+content=["\']([^"\']+)["\']', html_text, re.I)
            if m_t:
                out["title"] = _clean_wsj_title(m_t.group(1))
        if not out["cover_image"]:
            m_i = re.search(r'<meta[^>]+(?:property|name)=["\'](?:og:image|twitter:image)["\'][^>]+content=["\']([^"\']+)["\']', html_text, re.I)
            if m_i:
                cand = _strip_wayback_prefix(html.unescape(m_i.group(1)).strip())
                if _is_valid_wsj_image(cand):
                    out["cover_image"] = cand
        paras = []
        for pm in re.findall(r'<p[^>]*>(.*?)</p>', html_text, re.DOTALL | re.I):
            cp = _clean_wsj_paragraph(pm)
            if cp and len(cp) >= 35 and cp not in paras:
                paras.append(cp)
        out["paragraphs"] = paras

    return out


def _extract_techmeme_author(raw_title: Optional[str]) -> str:
    """Extracts WSJ author from Techmeme parenthetical e.g. '(Robbie Whelan/Wall Street Journal)'."""
    if not raw_title:
        return ""
    m = re.search(r'\(([^()/]+?)/(?:Wall Street Journal|WSJ)\)\s*$', raw_title, re.I)
    if m:
        cand = m.group(1).strip()
        if cand and len(cand) < 60 and "journal" not in cand.lower():
            return cand
    return ""


def _resolve_wsj_gnews_and_syndication(slug_clean: str, proxies: Optional[Dict[str, str]]) -> Dict[str, Any]:
    """
    Queries Google News RSS for:
    1. Official WSJ headline (`site:wsj.com "<slug>"`)
    2. High-trust open corroborating/syndicated full-text reporting with strict entity overlap.
    """
    out: Dict[str, Any] = {"wsj_title": "", "paragraphs": [], "cover_image": None, "synd_source": ""}
    if not slug_clean:
        return out

    opener = urllib.request.build_opener(urllib.request.ProxyHandler(proxies)) if proxies else urllib.request.build_opener()
    search_phrase = slug_clean.replace("-", " ")
    slug_tokens = [w.lower() for w in re.findall(r'[a-z0-9]+', search_phrase) if len(w) > 2 and w.lower() not in STOPWORDS]

    all_items = []
    # Fast 2-stage RSS lookup: general phrase first (often includes both [WSJ] & open coverage), only add site:wsj.com if [WSJ] not found
    primary_rss = f"https://news.google.com/rss/search?q={urllib.parse.quote(search_phrase)}&hl=en-US&gl=US&ceid=US:en"
    try:
        req = urllib.request.Request(primary_rss, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/124.0.0.0"})
        xml_d = opener.open(req, timeout=5).read()
        all_items.extend(ET.fromstring(xml_d).findall(".//item"))
    except Exception:
        pass

    has_wsj_in_primary = any("wsj" in (it.findtext("source") or "").lower() or "wall street journal" in (it.findtext("source") or "").lower() for it in all_items)
    if not has_wsj_in_primary:
        wsj_rss = f"https://news.google.com/rss/search?q={urllib.parse.quote(f'site:wsj.com {search_phrase}')}&hl=en-US&gl=US&ceid=US:en"
        try:
            req = urllib.request.Request(wsj_rss, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/124.0.0.0"})
            xml_d = opener.open(req, timeout=5).read()
            all_items.extend(ET.fromstring(xml_d).findall(".//item"))
        except Exception:
            pass

    # 1. Resolve authentic WSJ editorial headline
    best_wsj_score = 0
    for it in all_items:
        src = (it.findtext("source") or "").lower()
        t_raw = it.findtext("title") or ""
        if "wsj" in src or "wall street journal" in src:
            t_clean = _clean_wsj_title(t_raw)
            if not t_clean or "breaking news, business" in t_clean.lower():
                continue
            t_words = set(re.findall(r'[a-z0-9]+', t_clean.lower()))
            overlap = sum(1 for w in slug_tokens if w in t_words)
            if overlap > best_wsj_score and overlap >= max(2, min(3, len(slug_tokens) // 2)):
                best_wsj_score = overlap
                out["wsj_title"] = t_clean

    # 2. Extract corroborated full-text from open high-trust tech/finance outlets (strict entity match)
    if not HAS_GNEWS_DECODER:
        return out

    PAYWALLED_DOMAINS = (
        "wsj.com", "ft.com", "bloomberg.com", "theinformation.com", "barrons.com",
        "nytimes.com", "washingtonpost.com", "economist.com", "businessinsider.com"
    )
    TRUSTED_OPEN_SOURCES = {
        "marketscreener": 100, "yahoo": 95, "techcrunch": 92, "cnbc": 90,
        "axios": 88, "crunchbase": 85, "siliconangle": 85, "the verge": 84,
        "ars technica": 84, "venturebeat": 82, "bbc": 80, "quartz": 78,
        "pymnts": 76, "the decoder": 75, "9to5mac": 75, "srn news": 74,
        "crypto briefing": 72, "techradar": 70, "engadget": 70, "zdnet": 70,
        "reuters": 65, "msn": 60
    }

    # Build strong entity set from official WSJ title + slug
    ref_text = f"{out['wsj_title']} {search_phrase}".lower()
    ref_tokens = list(dict.fromkeys(
        w for w in re.findall(r'[a-z0-9]+', ref_text)
        if len(w) > 2 and w not in STOPWORDS
    ))
    min_overlap = max(2, min(4, (len(ref_tokens) + 1) // 2))

    scored_candidates = []
    seen_links = set()
    for it in all_items:
        src = (it.findtext("source") or "").lower()
        t_raw = (it.findtext("title") or "").strip()
        link = (it.findtext("link") or "").strip()
        if not link or link in seen_links:
            continue
        seen_links.add(link)
        if any(pw in src for pw in ("wsj", "wall street journal", "bloomberg", "financial times", "barron", "new york times", "the information")):
            continue
        t_words = set(re.findall(r'[a-z0-9]+', t_raw.lower()))
        overlap = sum(1 for w in ref_tokens if w in t_words)
        if overlap < min_overlap:
            continue
        base_score = 40
        for k, sc in TRUSTED_OPEN_SOURCES.items():
            if k in src:
                base_score = sc
                break
        scored_candidates.append((overlap * 20 + base_score, src, t_raw, link))

    scored_candidates.sort(key=lambda x: x[0], reverse=True)

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9"
    }

    for _, src, t_raw, link in scored_candidates[:8]:
        try:
            dec = googlenewsdecoder.gnewsdecoder(link)
            dec_url = dec.get("decoded_url") if isinstance(dec, dict) else dec
        except Exception:
            continue
        if not dec_url or any(pw in dec_url.lower() for pw in PAYWALLED_DOMAINS):
            continue

        page_html = None
        if HAS_CURL_CFFI:
            try:
                r = cffi_requests.get(dec_url, impersonate="chrome120", headers=headers, proxies=proxies, timeout=8)
                if r.status_code == 200 and len(r.text) > 2500:
                    page_html = r.text
            except Exception:
                pass
        if not page_html and HAS_REQUESTS:
            try:
                r = requests.get(dec_url, headers=headers, proxies=proxies, timeout=8)
                if r.status_code == 200 and len(r.text) > 2500:
                    page_html = r.text
            except Exception:
                pass
        if not page_html:
            continue

        paras = []
        cand_img = None
        if HAS_SELECTOLAX:
            tree = LexborHTMLParser(page_html)
            og_i = tree.css_first('meta[property="og:image"]') or tree.css_first('meta[name="twitter:image"]')
            if og_i and og_i.attributes.get("content"):
                ci = og_i.attributes["content"].strip()
                if _is_valid_wsj_image(ci):
                    cand_img = ci
            for bad in tree.css("style, script, noscript, nav, footer, aside, .related, .newsletter"):
                bad.decompose()
            container = tree.css_first("article") or tree.css_first("main") or tree.body
            if container:
                for p_node in container.css("p"):
                    cp = _clean_wsj_paragraph(p_node.text())
                    if cp and len(cp) >= 35 and cp not in paras:
                        paras.append(cp)
        else:
            m_i = re.search(r'<meta[^>]+(?:property|name)=["\'](?:og:image|twitter:image)["\'][^>]+content=["\']([^"\']+)["\']', page_html, re.I)
            if m_i:
                ci = html.unescape(m_i.group(1)).strip()
                if _is_valid_wsj_image(ci):
                    cand_img = ci
            for pm in re.findall(r'<p[^>]*>(.*?)</p>', page_html, re.DOTALL | re.I):
                cp = _clean_wsj_paragraph(pm)
                if cp and len(cp) >= 35 and cp not in paras:
                    paras.append(cp)

        # Verify body relevance against ref_tokens
        body_low = " ".join(paras).lower()
        body_hits = sum(1 for w in ref_tokens if w in body_low)
        if len(paras) >= 5 and body_hits >= min(3, len(ref_tokens)):
            out["paragraphs"] = paras
            out["cover_image"] = cand_img
            out["synd_source"] = src
            break

    return out


def _fetch_wayback_wsj(canonical_url: str, original_url: str, proxies: Optional[Dict[str, str]]) -> Dict[str, Any]:
    """Fetches Wayback Machine snapshot of a WSJ URL to recover official images.wsj.net photo and lead text."""
    out: Dict[str, Any] = {"title": "", "author": "", "cover_image": None, "paragraphs": []}
    if not canonical_url:
        return out
    opener = urllib.request.build_opener(urllib.request.ProxyHandler(proxies)) if proxies else urllib.request.build_opener()
    wb_api = f"https://archive.org/wayback/available?url={urllib.parse.quote(canonical_url)}"
    try:
        raw = opener.open(urllib.request.Request(wb_api, headers={"User-Agent": "Mozilla/5.0"}), timeout=4).read().decode("utf-8")
        snap_url = json.loads(raw).get("archived_snapshots", {}).get("closest", {}).get("url")
        if not snap_url:
            return out
        snap_url = snap_url.replace("http://", "https://", 1)
        snap_html = None
        if HAS_CURL_CFFI:
            r = cffi_requests.get(snap_url, impersonate="chrome120", proxies=proxies, timeout=8)
            if r.status_code == 200 and len(r.text) > 5000:
                snap_html = r.text
        elif HAS_REQUESTS:
            r = requests.get(snap_url, proxies=proxies, timeout=8)
            if r.status_code == 200 and len(r.text) > 5000:
                snap_html = r.text
        if snap_html:
            parsed = _extract_wsj_dom(snap_html)
            if parsed.get("title") or parsed.get("cover_image") or parsed.get("paragraphs"):
                return parsed
    except Exception:
        pass
    return out


def crawl_wsj(url: str, title: Optional[str] = None, html_text: Optional[str] = None, force_refresh: bool = False) -> Dict[str, Any]:
    """
    Dedicated Wall Street Journal (WSJ) Crawler.
    Extracts authentic WSJ headline, journalist byline, official images.wsj.net HD photography,
    and substantive full-text reporting with strict entity verification.
    """
    clean_url = url.split("#")[0].split("?")[0].strip() if url else ""
    clean_id = hashlib.md5(clean_url.encode("utf-8")).hexdigest()[:16] if clean_url else ""

    result: Dict[str, Any] = {
        "id": clean_id,
        "url": clean_url,
        "source": "Wall Street Journal",
        "domain": "wsj.com",
        "title": "",
        "author": "Wall Street Journal",
        "published_at": None,
        "cover_image": None,
        "image_url": None,
        "inline_images": [],
        "paragraphs": [],
        "subheadings": [],
        "full_text": "",
        "article_content": "",
        "article_content_en": "",
        "lead_paragraph": "",
        "paras_count": 0,
        "is_substantive": False,
        "is_paywalled": False,
        "status": "failed"
    }

    if not clean_url:
        return result

    # 1. Check memory & disk cache
    if not html_text and not force_refresh:
        for cached in (_WSJ_CACHE.get(clean_url), _get_from_disk_cache(clean_url)):
            if cached and cached.get("status") == "success" and cached.get("is_substantive") and _is_valid_wsj_image(cached.get("cover_image")):
                _WSJ_CACHE[clean_url] = dict(cached)
                return dict(cached)

    proxies = _get_proxies()

    # Extract Techmeme author attribution if present in caller's title
    tm_author = _extract_techmeme_author(title)
    if tm_author:
        result["author"] = tm_author

    # Extract article slug (strip WSJ 8-char hex suffix e.g. -ee7643f8)
    slug = clean_url.rstrip("/").split("/")[-1]
    slug_clean = re.sub(r'-[0-9a-f]{6,}$', '', slug)

    # -------------------------------------------------------------------------
    # Tier 1: Direct / Supplied HTML DOM Extraction
    # -------------------------------------------------------------------------
    if html_text:
        dom = _extract_wsj_dom(html_text)
        if dom["title"]:
            result["title"] = dom["title"]
        if dom["author"]:
            result["author"] = dom["author"]
        if dom["cover_image"]:
            result["cover_image"] = dom["cover_image"]
            result["image_url"] = dom["cover_image"]
        if len(dom["paragraphs"]) >= 3:
            full_body = "\n\n".join(dom["paragraphs"])
            result["paragraphs"] = dom["paragraphs"]
            result["paras_count"] = len(dom["paragraphs"])
            result["full_text"] = full_body
            result["article_content"] = full_body
            result["article_content_en"] = full_body
            result["lead_paragraph"] = dom["paragraphs"][0]
            result["is_substantive"] = True
            result["is_paywalled"] = False
            result["status"] = "success"
            return result

    # -------------------------------------------------------------------------
    # Tier 2: Wayback Machine Snapshot (Official images.wsj.net photo + lead text)
    # -------------------------------------------------------------------------
    wb_data = _fetch_wayback_wsj(clean_url, url, proxies)
    if wb_data.get("title"):
        result["title"] = wb_data["title"]
    if wb_data.get("author"):
        result["author"] = wb_data["author"]
    if wb_data.get("cover_image"):
        hosted = _localize_wsj_image(wb_data["cover_image"], clean_url, proxies=proxies)
        result["cover_image"] = hosted
        result["image_url"] = hosted

    wb_paras = wb_data.get("paragraphs", [])

    # -------------------------------------------------------------------------
    # Tier 3: Official WSJ Headline + Strict Entity-Verified Full-Text Penetration
    # -------------------------------------------------------------------------
    synd = _resolve_wsj_gnews_and_syndication(slug_clean, proxies)
    if synd.get("wsj_title"):
        result["title"] = synd["wsj_title"]
    elif not result["title"] and slug_clean:
        result["title"] = slug_clean.replace("-", " ").title()

    if not result["cover_image"] and synd.get("cover_image"):
        hosted = _localize_wsj_image(synd["cover_image"], clean_url, proxies=proxies)
        result["cover_image"] = hosted
        result["image_url"] = hosted

    merged_paras: List[str] = []
    if len(wb_paras) >= 5:
        merged_paras = wb_paras
    else:
        # Combine authentic WSJ lead paragraphs (if any) + verified full-text reporting
        for p in wb_paras:
            if p not in merged_paras:
                merged_paras.append(p)
        for p in synd.get("paragraphs", []):
            if p not in merged_paras and not any(p[:60].lower() in ep.lower() for ep in merged_paras):
                merged_paras.append(p)

    if merged_paras:
        full_body = "\n\n".join(merged_paras)
        result["paragraphs"] = merged_paras
        result["paras_count"] = len(merged_paras)
        result["full_text"] = full_body
        result["article_content"] = full_body
        result["article_content_en"] = full_body
        result["lead_paragraph"] = merged_paras[0]
        result["is_substantive"] = len(merged_paras) >= 3 or len(full_body) >= 300
        result["is_paywalled"] = False
        result["status"] = "success"

        if result.get("cover_image"):
            cap_en = f"{result['title']} (Source: Wall Street Journal)"
            cap_zh = f"{result['title']} (来源：华尔街日报)"
            result["inline_images"] = [{
                "url": result["cover_image"],
                "caption": cap_en,
                "caption_en": cap_en,
                "caption_zh": cap_zh,
                "alt": result["title"]
            }]

    if result["is_substantive"] and "sample-story" not in clean_url:
        _WSJ_CACHE[clean_url] = dict(result)
        _save_to_disk_cache(clean_url, dict(result))

    return result
