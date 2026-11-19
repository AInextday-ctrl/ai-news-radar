#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
=============================================================================
Anthropic Official News & Frontier Research Dedicated Crawler (`anthropic.com`)
=============================================================================
Source: Anthropic (`anthropic.com/news/...`, `anthropic.com/research/...`, etc.)
Scope: Handles all anthropic.com official announcements, product roadmaps,
       frontier safety research, and technical papers:
       - Authentic headline resolution (`<h1>` / `og:title` / JSON-LD `headline`,
         stripping trailing ` — Anthropic` / ` | Anthropic`), clean author
         resolution via header metalist (`Frontier Red Team`, `Alignment Team`,
         research scientists, or `Anthropic` — preventing Chinglish
         `Anthropic 官方动态` leaks on EN pages), and exact publication dates.
       - Dedicated `div[class*='_body']` single-pass DOM extraction:
         * Preserves primary section subheadings (`### `) and secondary headings
           (`#### `), stripping leading TOC index digits (e.g. `01`, `02`).
         * Extracts authentic inline scientific figures, charts, and diagrams
           hosted on `assets.claude.com` with rich `<figcaption>` text anchored
           at exact `after_para` + `dom_order`.
         * Extracts native HTML5 MP4 demo videos (`<video src="...">` on
           `assets.claude.com`) with captions and exact DOM anchoring.
         * Hard-stops at footnotes, references, and related-article constellation
           panels (`[class*='ConstellationPanel']`, `[class*='Related']`).
       - Hero cover photo localization to `public/images/anthropic_<hash>.jpg`.

Separation of Concerns:
- Completely isolated from all 27 locked crawlers (Reuters, Bloomberg, Fortune,
  WSJ, The Verge, NYT, Washington Post, Washington Sun, Financial Times, WIRED,
  MIT Technology Review, TechCrunch, Ars Technica, CNBC, THE DECODER, OpenAI,
  SiliconANGLE, Semafor, CoinDesk, CBS News, iFixit News, 9to5Mac, Tom's
  Hardware, BBC News, New York Post, Tech Funding News, IGN).
=============================================================================
"""

import os
import re
import html
import json
import hashlib
from urllib.parse import urlparse
from typing import Dict, Any, List, Optional, Tuple
from .content_filters import detect_low_value_roundup_or_promo

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


_ANTHROPIC_CACHE: Dict[str, Dict[str, Any]] = {}
_DISK_CACHE_FILE = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "data",
    "anthropic_cache.json",
)

DEFAULT_PROXIES = ["http://127.0.0.1:7890", "http://127.0.0.1:7897"]

STOP_SECTION_HEADINGS = {
    "footnotes",
    "footnote",
    "references",
    "related articles",
    "related research",
    "more from anthropic",
    "acknowledgments",
    "acknowledgements",
    "share this article",
}

ANTHROPIC_NOISE_PHRASES = (
    "all rights reserved",
    "subscribe to our newsletter",
    "sign up to receive updates",
    "try claude",
)

BAD_IMAGE_TOKENS = (
    "/avatars/",
    "site-logo",
    "brand-logo",
    "wordmark",
    "favicon",
    "sprite",
    "pixel",
    "tracker",
    "placeholder",
    "1x1",
)


def is_anthropic_url(url: str) -> bool:
    """Returns True if URL belongs to Anthropic (`anthropic.com` or `claude.com`)."""
    if not url or not isinstance(url, str):
        return False
    try:
        host = (urlparse(url).netloc or "").lower().split(":")[0]
    except Exception:
        return False
    return (
        host == "anthropic.com"
        or host.endswith(".anthropic.com")
        or host == "claude.com"
        or host.endswith(".claude.com")
    )


def _canonical_anthropic_key(url: str) -> str:
    return (url or "").split("?")[0].split("#")[0].strip().rstrip("/").lower()


def _get_proxies() -> Optional[Dict[str, str]]:
    if os.environ.get("GITHUB_ACTIONS", "").lower() == "true":
        return None
    for env_key in ("HTTPS_PROXY", "HTTP_PROXY", "https_proxy", "http_proxy"):
        val = os.environ.get(env_key)
        if val:
            return {"http": val, "https": val}
    import socket
    for p in DEFAULT_PROXIES:
        try:
            host_port = p.replace("http://", "").replace("https://", "")
            host, port_s = host_port.split(":")
            s = socket.create_connection((host, int(port_s)), timeout=0.4)
            s.close()
            return {"http": p, "https": p}
        except Exception:
            continue
    return None


def _clean_text(text: str) -> str:
    if not text:
        return ""
    t = html.unescape(str(text))
    t = t.replace("\u00a0", " ").replace("\u200b", "").replace("\ufeff", "").replace("\u2060", "")
    t = re.sub(r"\s+", " ", t).strip()
    t = re.sub(r"\s+([,.;:!?%)\]}])", r"\1", t)
    t = re.sub(r"([(\[{“‘\$£€])\s+", r"\1", t)
    t = re.sub(r"\s+([’'](?:s|t|re|ve|ll|d|m)\b)", r"\1", t, flags=re.I)
    t = re.sub(r"\s+([”’])", r"\1", t)
    t = re.sub(r"\s{2,}", " ", t)
    return t.strip()


def _clean_anthropic_title(title: str) -> str:
    t = _clean_text(re.sub(r"<[^>]+>", "", title or ""))
    t = re.sub(r"\s*[\|\-–—]\s*Anthropic\s*$", "", t, flags=re.I)
    return t.strip()


def _clean_anthropic_author(raw: str) -> str:
    t = _clean_text(raw or "")
    t = re.sub(r"^by\s+", "", t, flags=re.I).strip(" ,|·")
    if not t or t.lower() in ("anthropic", "anthropic news", "anthropic research", "staff", "editors"):
        return "Anthropic"
    return t


def _clean_heading(h: str) -> str:
    t = _clean_text(h)
    t = re.sub(r"^\d{1,2}\s*", "", t).strip()
    return t


def _media_stem(url: str) -> str:
    u = html.unescape((url or "").strip()).split("?")[0].split("#")[0].strip().lower()
    return u


def _is_valid_anthropic_image(url: str) -> bool:
    u = html.unescape((url or "").strip())
    if u.startswith("//"):
        u = "https:" + u
    if not u or not u.startswith(("http://", "https://")):
        return False
    low = u.lower()
    if low.startswith("data:"):
        return False
    if any(tok in low for tok in BAD_IMAGE_TOKENS):
        return False
    clean_path = low.split("?")[0].split("#")[0]
    if clean_path.endswith((".svg", ".ico")):
        return False
    return True


def _load_disk_cache() -> None:
    if _ANTHROPIC_CACHE:
        return
    try:
        if os.path.exists(_DISK_CACHE_FILE):
            with open(_DISK_CACHE_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, dict):
                    _ANTHROPIC_CACHE.update(data)
    except Exception:
        pass


def _save_disk_cache() -> None:
    try:
        os.makedirs(os.path.dirname(_DISK_CACHE_FILE), exist_ok=True)
        tmp = _DISK_CACHE_FILE + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(_ANTHROPIC_CACHE, f, ensure_ascii=False, indent=2)
        os.replace(tmp, _DISK_CACHE_FILE)
    except Exception:
        pass


def _localize_anthropic_image(img_url: str, proxies: Optional[Dict[str, str]] = None) -> str:
    """Downloads Anthropic cover image to `public/images/anthropic_<hash>.jpg`."""
    if not img_url or not img_url.startswith(("http://", "https://")):
        return img_url
    if "ainewsradar.xyz/images/" in img_url:
        return img_url
    try:
        root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        img_dir = os.path.join(root_dir, "public", "images")
        os.makedirs(img_dir, exist_ok=True)
        h = hashlib.md5(_media_stem(img_url).encode("utf-8")).hexdigest()[:16]
        fname = f"anthropic_{h}.jpg"
        fpath = os.path.join(img_dir, fname)
        public_url = f"https://ainewsradar.xyz/images/{fname}"
        if os.path.exists(fpath) and os.path.getsize(fpath) > 4000:
            return public_url

        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
            "Referer": "https://www.anthropic.com/",
            "Accept": "image/jpeg,image/png,image/webp,image/*;q=0.8,*/*;q=0.5",
        }
        content = None
        if HAS_CURL_CFFI:
            for _ in range(2):
                try:
                    r = cffi_requests.get(img_url, impersonate="chrome131", headers=headers, proxies=proxies, timeout=18)
                    if r.status_code == 200 and len(r.content) > 4000:
                        ct = r.headers.get("content-type", "").lower()
                        if "image/" in ct or r.content[:2] in (b"\xff\xd8", b"\x89P") or r.content[:4] == b"RIFF":
                            content = r.content
                            break
                except Exception:
                    pass
        if content is None and HAS_REQUESTS:
            try:
                r = requests.get(img_url, headers=headers, proxies=proxies, timeout=18)
                if r.status_code == 200 and len(r.content) > 4000:
                    ct = r.headers.get("content-type", "").lower()
                    if "image/" in ct or r.content[:2] in (b"\xff\xd8", b"\x89P") or r.content[:4] == b"RIFF":
                        content = r.content
            except Exception:
                pass

        if content:
            if content[:2] != b"\xff\xd8":
                try:
                    from io import BytesIO
                    from PIL import Image
                    im = Image.open(BytesIO(content))
                    if im.width > 1600:
                        ratio = 1600 / float(im.width)
                        im = im.resize((1600, max(1, int(im.height * ratio))), Image.LANCZOS)
                    if im.mode in ("RGBA", "P", "LA"):
                        im = im.convert("RGB")
                    buf = BytesIO()
                    im.save(buf, format="JPEG", quality=88, optimize=True)
                    content = buf.getvalue()
                except Exception:
                    pass
            tmp_path = fpath + ".tmp"
            with open(tmp_path, "wb") as f:
                f.write(content)
            os.replace(tmp_path, fpath)
            return public_url
    except Exception:
        pass
    return img_url


def _fetch_anthropic_html(url: str, proxies: Optional[Dict[str, str]] = None, timeout: int = 20) -> Tuple[Optional[str], str]:
    headers = {
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
        "Referer": "https://www.anthropic.com/",
    }
    if HAS_CURL_CFFI:
        for profile in ("chrome131", "chrome124"):
            try:
                r = cffi_requests.get(
                    url,
                    impersonate=profile,
                    headers=headers,
                    proxies=proxies,
                    timeout=timeout,
                    allow_redirects=True,
                )
                if r.status_code == 200 and len(r.text or "") > 5000:
                    return r.text, f"anthropic_live_{profile}"
            except Exception:
                continue

    if HAS_REQUESTS:
        try:
            r = requests.get(
                url,
                headers={
                    **headers,
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
                },
                proxies=proxies,
                timeout=timeout,
            )
            if r.status_code == 200 and len(r.text or "") > 5000:
                return r.text, "anthropic_live_requests"
        except Exception:
            pass

    return None, "failed"


def _extract_jsonld_meta(tree) -> Dict[str, Any]:
    meta: Dict[str, Any] = {"title": "", "summary": "", "author": "", "published_at": "", "cover_image": ""}
    for script in tree.css('script[type="application/ld+json"]'):
        raw = (script.text() or "").strip()
        if not raw:
            continue
        try:
            obj = json.loads(raw)
        except Exception:
            continue
        nodes = obj if isinstance(obj, list) else [obj]
        for node in nodes:
            if not isinstance(node, dict):
                continue
            atype = node.get("@type")
            types = atype if isinstance(atype, list) else [atype]
            if not any(t in ("Article", "NewsArticle", "ReportageNewsArticle", "BlogPosting") for t in types):
                continue
            if not meta["title"] and node.get("headline"):
                meta["title"] = _clean_anthropic_title(str(node["headline"]))
            if not meta["summary"] and node.get("description"):
                meta["summary"] = _clean_text(str(node["description"]))
            if not meta["published_at"] and node.get("datePublished"):
                meta["published_at"] = str(node["datePublished"]).strip()
            if not meta["author"] and node.get("author"):
                auth = node["author"]
                if isinstance(auth, dict) and auth.get("name"):
                    meta["author"] = _clean_anthropic_author(str(auth["name"]))
                elif isinstance(auth, str):
                    meta["author"] = _clean_anthropic_author(auth)
            if not meta["cover_image"] and node.get("image"):
                im = node["image"]
                if isinstance(im, str):
                    meta["cover_image"] = im
                elif isinstance(im, dict) and im.get("url"):
                    meta["cover_image"] = str(im["url"])
    return meta


def _parse_anthropic_html(html_text: str) -> Optional[Dict[str, Any]]:
    if not html_text or not HAS_SELECTOLAX:
        return None

    tree = LexborHTMLParser(html_text)
    ld_meta = _extract_jsonld_meta(tree)

    # 1. Headline
    title = ""
    h1 = tree.css_first("header h1") or tree.css_first("h1")
    if h1:
        try:
            raw_h1 = h1.text(separator=" ", strip=True)
        except Exception:
            raw_h1 = h1.text(strip=True)
        title = _clean_anthropic_title(raw_h1)

    m_ogt = tree.css_first('meta[property="og:title"]')
    og_title = _clean_anthropic_title(m_ogt.attributes.get("content", "")) if m_ogt else ""

    # Fallback or correction if h1 jammed words together without spaces
    if not title or (any(len(w) > 28 for w in title.split()) and og_title):
        title = og_title
    if not title:
        title = ld_meta["title"]

    # 2. Author / Team
    author = ""
    for item in tree.css("header div[class*='item']"):
        txt = _clean_text(item.text())
        if txt.startswith("Team"):
            author = _clean_anthropic_author(txt.replace("Team", "", 1).strip())
            break
        elif txt.startswith("Author"):
            author = _clean_anthropic_author(txt.replace("Author", "", 1).strip())
            break
        elif txt.startswith("By"):
            author = _clean_anthropic_author(txt.replace("By", "", 1).strip())
            break
    if not author:
        author = ld_meta["author"]
    if not author or author.lower() in ("anthropic", "anthropic research", "anthropic news"):
        author = "Anthropic"

    # 3. Publication Date
    published_at = ""
    time_el = tree.css_first("header time") or tree.css_first("time")
    if time_el:
        published_at = _clean_text(time_el.text())
    if not published_at:
        m_pub = tree.css_first('meta[property="article:published_time"]')
        if m_pub and m_pub.attributes.get("content"):
            published_at = m_pub.attributes["content"].strip()
    if not published_at:
        published_at = ld_meta["published_at"]

    # 4. Cover Image
    cover_image = ""
    m_ogi = tree.css_first('meta[property="og:image"]')
    if m_ogi and m_ogi.attributes.get("content"):
        cover_image = m_ogi.attributes["content"].strip()
    if not cover_image:
        cover_image = ld_meta["cover_image"]

    # 5. Summary
    summary = ""
    m_ogd = tree.css_first('meta[property="og:description"]') or tree.css_first('meta[name="description"]')
    if m_ogd and m_ogd.attributes.get("content"):
        summary = _clean_text(m_ogd.attributes["content"])
    if not summary:
        summary = ld_meta["summary"]

    # 6. Body Container
    body = None
    for sel in [
        "div[class*='_body']",
        "div[class*='bodyWrap']",
        "div[class*='text-rich-text--article']",
        "div.w-richtext",
        "div[class*='ContentWrapper']",
        "article",
        "main",
    ]:
        for node in tree.css(sel):
            cls = (node.attributes.get("class") or "").lower()
            if "dropdown" in cls or "nav" in cls or "menu" in cls:
                continue
            if len(node.css("p")) >= 2:
                body = node
                break
        if body:
            break

    if not body:
        body = tree.css_first("article") or tree.css_first("main")
    if not body:
        return None

    # Remove noise elements without decomposing body itself
    for sel in ("script", "style", "noscript", "aside", "nav", "form", "[class*='ConstellationPanel']", "[class*='TableOfContents']", "header"):
        for n in body.css(sel):
            if n != body:
                n.decompose()

    paragraphs: List[str] = []
    subheadings: List[str] = []
    inline_images: List[Dict[str, Any]] = []
    inline_videos: List[Dict[str, Any]] = []
    seen_stems = set()
    if cover_image:
        seen_stems.add(_media_stem(cover_image))
    seen_vid_urls = set()
    dom_order = 0

    def _add_img(img_url: str, caption: str, alt: str, after_para: int) -> None:
        nonlocal dom_order
        if not _is_valid_anthropic_image(img_url):
            return
        stem = _media_stem(img_url)
        if stem in seen_stems:
            return
        seen_stems.add(stem)
        clean_cap = _clean_text(caption or alt or "")
        inline_images.append({
            "url": img_url,
            "alt": clean_cap or "Anthropic Research Figure",
            "caption_en": clean_cap,
            "caption": clean_cap,
            "after_para": after_para,
            "dom_order": dom_order,
        })
        dom_order += 1

    def _add_vid(vid_url: str, caption: str, after_para: int) -> None:
        nonlocal dom_order
        if not vid_url or vid_url in seen_vid_urls:
            return
        seen_vid_urls.add(vid_url)
        clean_cap = _clean_text(caption or "Anthropic Video Demonstration")
        inline_videos.append({
            "url": vid_url,
            "provider": "mp4",
            "title": clean_cap,
            "caption": clean_cap,
            "aspect": "16:9",
            "after_para": after_para,
            "dom_order": dom_order,
        })
        dom_order += 1

    for node in body.css("h2, h3, h4, p, ul, ol, blockquote, figure, video"):
        tag = (node.tag or "").lower()
        cls = (node.attributes.get("class") or "").lower()

        # Hard stops
        if "constellation" in cls or "related" in cls:
            break

        cur_ap = len(paragraphs) - 1

        # Headings
        if tag in ("h2", "h3", "h4"):
            raw_h = _clean_text(node.text())
            low_h = raw_h.lower()
            if low_h in STOP_SECTION_HEADINGS:
                break
            ch = _clean_heading(raw_h)
            if ch and len(ch) <= 140:
                if tag == "h2":
                    paragraphs.append(f"### {ch}")
                else:
                    paragraphs.append(f"#### {ch}")
                subheadings.append(ch)
            continue

        # Bullet / numbered lists
        if tag in ("ul", "ol"):
            if "toc" in cls or "contents" in cls:
                continue
            for li in node.css("li"):
                ltxt = _clean_text(li.text())
                if ltxt and len(ltxt) >= 3 and not any(phrase in ltxt.lower() for phrase in ANTHROPIC_NOISE_PHRASES):
                    paragraphs.append(f"• {ltxt}")
            continue

        # Blockquotes
        if tag == "blockquote":
            btxt = _clean_text(node.text())
            if btxt and len(btxt) >= 10:
                if not (btxt.startswith(("“", '"')) and btxt.endswith(("”", '"'))):
                    btxt = f"“{btxt}”"
                paragraphs.append(btxt)
            continue

        # Paragraphs
        if tag == "p":
            ptxt = _clean_text(node.text())
            if ptxt and len(ptxt) >= 10:
                if not any(phrase in ptxt.lower() for phrase in ANTHROPIC_NOISE_PHRASES):
                    if ptxt.lower() in ("contents", "table of contents"):
                        continue
                    paragraphs.append(ptxt)
            continue

        # Standalone video
        if tag == "video":
            v_src = node.attributes.get("src", "").strip()
            if v_src:
                _add_vid(v_src, "Anthropic Video Demonstration", cur_ap)
            continue

        # Figures (Images or Videos with captions)
        if tag == "figure":
            # Check video first
            v = node.css_first("video")
            if v and v.attributes.get("src"):
                v_src = v.attributes.get("src").strip()
                fc = node.css_first("figcaption")
                v_cap = _clean_text(fc.text() if fc else "")
                _add_vid(v_src, v_cap, cur_ap)

            # Check image
            im = node.css_first("img")
            if im:
                i_src = im.attributes.get("src") or im.attributes.get("data-src") or ""
                # Also check srcset for highest quality
                ss = im.attributes.get("srcset") or ""
                if ss:
                    parts = [p.strip().split(" ")[0] for p in ss.split(",") if p.strip()]
                    if parts:
                        i_src = parts[-1]
                if i_src:
                    fc = node.css_first("figcaption")
                    cap = _clean_text((fc.text() if fc else "") or im.attributes.get("alt") or "")
                    alt = _clean_text(im.attributes.get("alt") or "")
                    _add_img(i_src, cap, alt, cur_ap)
            continue

    # Deduplicate consecutive identical paragraphs
    deduped_paras: List[str] = []
    for p in paragraphs:
        if not deduped_paras or deduped_paras[-1] != p:
            deduped_paras.append(p)

    has_video = bool(inline_videos)
    first_vid = inline_videos[0] if inline_videos else None

    return {
        "title": title,
        "summary": summary,
        "author": author,
        "published_at": published_at,
        "cover_image": cover_image,
        "paragraphs": deduped_paras,
        "subheadings": subheadings,
        "raw_content_text": "\n\n".join(deduped_paras),
        "inline_images": inline_images,
        "inline_videos": inline_videos,
        "has_video": has_video,
        "video_url": first_vid.get("url") if first_vid else None,
        "video_provider": first_vid.get("provider") if first_vid else None,
        "video_title": first_vid.get("title") if first_vid else None,
    }


def extract_anthropic_article(
    url: str,
    title: str = "",
    use_cache: bool = True,
    localize_cover: bool = True,
    html_text: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Dedicated Anthropic article extractor.
    Returns a standardized dict compatible with article_extractor.py / processor.py / main.py.
    """
    result: Dict[str, Any] = {
        "url": url,
        "source": "Anthropic",
        "title": _clean_anthropic_title(title) if title else "",
        "summary": "",
        "author": "Anthropic",
        "published_at": "",
        "cover_image": None,
        "image_url": None,
        "inline_images": [],
        "inline_videos": [],
        "subheadings": [],
        "paragraphs": [],
        "paras_count": 0,
        "lead_paragraph": "",
        "full_text": "",
        "article_content": "",
        "article_content_en": "",
        "has_video": False,
        "video_url": None,
        "video_provider": None,
        "status": "failed",
        "is_substantive": False,
        "is_paywalled": False,
        "is_filtered_out": False,
        "filter_reason": "",
        "extraction_tier": "none",
    }

    if not is_anthropic_url(url):
        return result

    pre_flagged, pre_reason = detect_low_value_roundup_or_promo(title=title, url=url)
    if pre_flagged:
        result["status"] = "filtered_promo_or_roundup"
        result["is_filtered_out"] = True
        result["filter_reason"] = pre_reason
        return result

    cache_key = _canonical_anthropic_key(url)
    if use_cache and html_text is None:
        _load_disk_cache()
        cached = _ANTHROPIC_CACHE.get(cache_key)
        if isinstance(cached, dict) and cached.get("is_filtered_out"):
            merged = dict(result)
            merged.update(cached)
            merged["url"] = url
            return merged
        if isinstance(cached, dict) and cached.get("is_substantive") and len(cached.get("full_text", "")) >= 300:
            merged = dict(result)
            merged.update(cached)
            merged["url"] = url
            return merged

    proxies = _get_proxies() if html_text is None else None
    raw_html = html_text
    tier = "anthropic_injected_html"
    if raw_html is None:
        raw_html, tier = _fetch_anthropic_html(url, proxies=proxies)

    if not raw_html:
        return result

    parsed = _parse_anthropic_html(raw_html)
    if not parsed:
        return result

    post_flagged, post_reason = detect_low_value_roundup_or_promo(
        title=parsed.get("title") or title,
        url=url,
        body=parsed.get("raw_content_text") or "",
        summary=parsed.get("summary") or "",
    )
    if post_flagged:
        result["status"] = "filtered_promo_or_roundup"
        result["is_filtered_out"] = True
        result["filter_reason"] = post_reason
        if use_cache and html_text is None:
            _load_disk_cache()
            _ANTHROPIC_CACHE[cache_key] = dict(result)
            _save_disk_cache()
        return result

    cover = parsed.get("cover_image")
    inlines = list(parsed.get("inline_images") or [])
    if cover and not _is_valid_anthropic_image(cover):
        cover = None
    if cover:
        c_stem = _media_stem(cover)
        inlines = [
            e for e in inlines
            if _media_stem(e["url"] if isinstance(e, dict) else str(e)) != c_stem
        ]
        if localize_cover and html_text is None:
            cover = _localize_anthropic_image(cover, proxies=proxies)

    paras = parsed.get("paragraphs") or []
    full_text = "\n\n".join(paras).strip()

    if parsed.get("title"):
        result["title"] = parsed["title"]
    if parsed.get("summary"):
        result["summary"] = parsed["summary"]
    if parsed.get("author"):
        result["author"] = parsed["author"]
    if parsed.get("published_at"):
        result["published_at"] = parsed["published_at"]
    if cover:
        result["cover_image"] = cover
        result["image_url"] = cover
    result["inline_images"] = inlines
    result["inline_videos"] = list(parsed.get("inline_videos") or [])
    if parsed.get("subheadings"):
        result["subheadings"] = parsed["subheadings"]
    if parsed.get("has_video") and parsed.get("video_url"):
        result["has_video"] = True
        result["video_url"] = parsed["video_url"]
        result["video_provider"] = parsed.get("video_provider") or "mp4"
        for vk in ("video_aspect", "video_poster", "video_title"):
            if parsed.get(vk):
                result[vk] = parsed[vk]

    result["paragraphs"] = paras
    result["paras_count"] = len(paras)
    result["lead_paragraph"] = paras[0] if paras else ""
    result["full_text"] = full_text
    result["article_content"] = full_text
    result["article_content_en"] = full_text
    result["extraction_tier"] = tier

    if len(paras) >= 2 and len(full_text) >= 300:
        result["status"] = "success"
        result["is_substantive"] = True
        result["is_paywalled"] = False
        if use_cache and html_text is None:
            _load_disk_cache()
            _ANTHROPIC_CACHE[cache_key] = dict(result)
            _save_disk_cache()
    elif result["title"] or cover:
        result["status"] = "metadata_only"

    return result


crawl_anthropic = extract_anthropic_article
