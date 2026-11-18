#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
=============================================================================
SiliconANGLE Dedicated Crawler (`siliconangle.com`)
=============================================================================
Source: SiliconANGLE (`siliconangle.com`)
Scope: Handles all siliconangle.com enterprise AI / cloud / infrastructure
       articles via WordPress REST API primary (`/wp-json/wp/v2/posts?slug=&_embed=1`)
       with HTML `.entry-content` fallback:
       - Authentic headline, real journalist byline (`_embedded.author` / scoped
         header byline), and ISO publication timestamp.
       - Single-pass DOM-order parser preserving inline `### ` subheadings,
         exact `after_para` + `dom_order` inline images (uncapped up to 24),
         and inline YouTube/Vimeo/MP4 videos (`inline_videos`).
       - Hard-stop & noise stripping for SiliconANGLE's recurring tail donation
         / AWS Marketplace / theCUBE community / John Furrier & Dave Vellante
         boilerplate (`Support our mission`, `Are you an AWS customer?`, etc.)
         and inline promo banners.
       - Site-wide editorial purity filter (`detect_low_value_roundup_or_promo`).
       - Hero cover localization from `_embedded.wp:featuredmedia` / `og:image`
         to `public/images/siliconangle_<hash>.jpg`.

Separation of Concerns:
- Completely isolated from all 16 locked crawlers (Reuters, Bloomberg, Fortune,
  WSJ, The Verge, NYT, Washington Post, Washington Sun, Financial Times, WIRED,
  MIT Technology Review, TechCrunch, Ars Technica, CNBC, THE DECODER, OpenAI).
=============================================================================
"""

import os
import re
import html
import json
import hashlib
from urllib.parse import quote, urlparse
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


_SILICONANGLE_CACHE: Dict[str, Dict[str, Any]] = {}
_DISK_CACHE_FILE = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "data",
    "siliconangle_cache.json",
)

DEFAULT_PROXIES = ["http://127.0.0.1:7890", "http://127.0.0.1:7897"]

STOP_TAIL_PHRASES = (
    "support our mission to keep content open and free",
    "are you an aws customer",
    "support siliconangle financially",
    "engaging with thecube community",
    "join thecube",
    "founded by tech visionaries john furrier",
    "siliconangle media has built a dynamic ecosystem",
    "show your support for our mission",
    "thanks for reading siliconangle",
)

SILICONANGLE_NOISE_PHRASES = [
    "support our mission",
    "are you an aws customer",
    "support siliconangle",
    "thecube community",
    "alumni trust network",
    "founded by tech visionaries",
    "siliconangle media has built",
    "sign up for our",
    "subscribe to our",
    "delivered to your inbox",
    "when you purchase through links",
    "we may earn a small commission",
    "affect our editorial independence",
    "all rights reserved",
    "advertisement",
    "sponsored content",
    "disclosure:",
]

AUDIO_ONLY_IFRAME_DOMAINS = (
    "simplecast.com",
    "open.spotify.com",
    "megaphone.fm",
    "omny.fm",
    "podcasts.apple.com",
    "soundcloud.com",
)

BAD_IMAGE_TOKENS = (
    "siliconangle-logo",
    "thecube-logo",
    "aws-marketplace",
    "site-logo",
    "brand-logo",
    "wordmark",
    "lockup",
    "avatar",
    "gravatar",
    "headshot",
    "author",
    "profile",
    "/icon",
    "-icon.",
    "_icon.",
    "badge",
    "favicon",
    "sprite",
    "pixel",
    "tracker",
    "doubleclick",
    "googlesyndication",
    "taboola",
    "outbrain",
    "unsplash.com",
    "placeholder",
    "ad-banner",
    "/ads/",
    "1x1",
)


def is_siliconangle_url(url: str) -> bool:
    """Returns True if URL belongs to SiliconANGLE (`siliconangle.com`)."""
    if not url or not isinstance(url, str):
        return False
    return "siliconangle.com" in url.lower()


def _canonical_sa_key(url: str) -> str:
    return (url or "").split("?")[0].split("#")[0].strip().rstrip("/").lower()


def _extract_sa_slug(url: str) -> Optional[str]:
    path = urlparse(url or "").path.strip("/")
    if not path:
        return None
    parts = [p for p in path.split("/") if p]
    return parts[-1] if parts else None


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
    t = t.replace("\u00a0", " ").replace("\u200b", "").replace("\ufeff", "")
    t = re.sub(r"\s+", " ", t).strip()
    t = re.sub(r"\s+([,.;:!?])", r"\1", t)
    t = re.sub(r"([(“\"])\s+", r"\1", t)
    t = re.sub(r"\s+([)”])", r"\1", t)
    return t.strip()


def _clean_sa_title(title: str) -> str:
    t = _clean_text(re.sub(r"<[^>]+>", "", title or ""))
    t = re.sub(r"\s*[\|\-–—]\s*SiliconANGLE\s*$", "", t, flags=re.I)
    return t.strip()


def _clean_sa_author(raw: str) -> str:
    t = _clean_text(raw or "")
    t = re.sub(r"^by\s+", "", t, flags=re.I).strip(" ,|·")
    if not t or t.lower() in ("siliconangle", "siliconangle staff", "staff", "editors"):
        return ""
    return t


def _is_stop_tail(text: str) -> bool:
    low = _clean_text(text).lower()
    return any(p in low for p in STOP_TAIL_PHRASES)


def _is_noise_heading(h: str) -> bool:
    if not h:
        return True
    t = _clean_text(h)
    if len(t) < 4 or len(t) > 150:
        return True
    low = t.lower()
    if _is_stop_tail(t) or any(p in low for p in SILICONANGLE_NOISE_PHRASES):
        return True
    if low.startswith(("image:", "photo:", "source:", "credit:")):
        return True
    if low in ("related", "related stories", "recommended", "comments", "subscribe", "share"):
        return True
    return False


def _is_noise_paragraph(p: str) -> bool:
    if not p:
        return True
    t = _clean_text(p)
    if len(t) < 22:
        return True
    low = t.lower()
    if low.startswith(("image:", "photo:", "featured image:")) and len(t) < 120:
        return True
    if _is_stop_tail(t) or any(phrase in low for phrase in SILICONANGLE_NOISE_PHRASES):
        return True
    return False


def _media_stem(url: str) -> str:
    if not url:
        return ""
    base = html.unescape(url).split("?")[0].split("#")[0].strip().lower()
    base = re.sub(r"-\d{2,4}x\d{2,4}(?=\.(?:jpe?g|png|webp|gif)$)", "", base)
    base = re.sub(r"-scaled(?=\.(?:jpe?g|png|webp|gif)$)", "", base)
    return base


def _is_valid_sa_image(url: str) -> bool:
    if not url or not isinstance(url, str):
        return False
    u = html.unescape(url.strip())
    if not u.startswith(("http://", "https://")):
        return False
    low = u.lower()
    if any(tok in low for tok in BAD_IMAGE_TOKENS):
        return False
    clean_path = low.split("?")[0].split("#")[0]
    if clean_path.endswith((".svg", ".ico", ".mp4", ".webm", ".mov", ".m4v", ".m3u8")):
        return False
    return True


def _load_disk_cache() -> None:
    if _SILICONANGLE_CACHE:
        return
    try:
        if os.path.exists(_DISK_CACHE_FILE):
            with open(_DISK_CACHE_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, dict):
                    _SILICONANGLE_CACHE.update(data)
    except Exception:
        pass


def _save_disk_cache() -> None:
    try:
        os.makedirs(os.path.dirname(_DISK_CACHE_FILE), exist_ok=True)
        tmp = _DISK_CACHE_FILE + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(_SILICONANGLE_CACHE, f, ensure_ascii=False, indent=2)
        os.replace(tmp, _DISK_CACHE_FILE)
    except Exception:
        pass


def _localize_sa_image(img_url: str, proxies: Optional[Dict[str, str]] = None) -> str:
    """Downloads SiliconANGLE cover image to `public/images/siliconangle_<hash>.jpg`."""
    img_url = html.unescape((img_url or "").strip())
    if not _is_valid_sa_image(img_url):
        return img_url
    if "ainewsradar.xyz/images/" in img_url:
        return img_url
    try:
        root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        img_dir = os.path.join(root_dir, "public", "images")
        os.makedirs(img_dir, exist_ok=True)
        h = hashlib.md5(_media_stem(img_url).encode("utf-8")).hexdigest()[:16]
        fname = f"sa_{h}.jpg"
        fpath = os.path.join(img_dir, fname)
        public_url = f"https://ainewsradar.xyz/images/{fname}"
        if os.path.exists(fpath) and os.path.getsize(fpath) > 5000:
            return public_url

        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
            "Referer": "https://siliconangle.com/",
            "Accept": "image/jpeg,image/png,image/webp,image/*;q=0.8,*/*;q=0.5",
        }
        content = None
        if HAS_CURL_CFFI:
            for _ in range(2):
                try:
                    r = cffi_requests.get(img_url, impersonate="chrome124", headers=headers, proxies=proxies, timeout=16)
                    if r.status_code == 200 and len(r.content) > 5000:
                        ct = r.headers.get("content-type", "").lower()
                        if "image/" in ct or r.content[:2] in (b"\xff\xd8", b"\x89P") or r.content[:4] == b"RIFF":
                            content = r.content
                            break
                except Exception:
                    pass
        if content is None and HAS_REQUESTS:
            try:
                r = requests.get(img_url, headers=headers, proxies=proxies, timeout=16)
                if r.status_code == 200 and len(r.content) > 5000:
                    ct = r.headers.get("content-type", "").lower()
                    if "image/" in ct or r.content[:2] in (b"\xff\xd8", b"\x89P") or r.content[:4] == b"RIFF":
                        content = r.content
            except Exception:
                pass
        if content:
            try:
                from io import BytesIO
                from PIL import Image
                im = Image.open(BytesIO(content))
                need_convert = (
                    len(content) > 1_200_000
                    or im.width > 1600
                    or (im.format or "").upper() not in ("JPEG", "JPG")
                )
                if need_convert:
                    if im.width > 1600:
                        ratio = 1600 / float(im.width)
                        im = im.resize((1600, max(1, int(im.height * ratio))), Image.LANCZOS)
                    if im.mode in ("RGBA", "P", "LA"):
                        im = im.convert("RGB")
                    buf = BytesIO()
                    im.save(buf, format="JPEG", quality=86, optimize=True)
                    content = buf.getvalue()
            except Exception:
                pass
            with open(fpath, "wb") as f:
                f.write(content)
            return public_url
    except Exception:
        pass
    return img_url


def _parse_content_dom(content_html: str, cover_image: Optional[str] = None) -> Tuple[List[str], List[str], List[Any], List[Dict[str, Any]], Dict[str, Any]]:
    """Single-pass DOM-order parser with hard-stop at SiliconANGLE donation/theCUBE tail."""
    paragraphs: List[str] = []
    subheadings: List[str] = []
    inline_images: List[Any] = []
    inline_videos: List[Dict[str, Any]] = []
    vmeta: Dict[str, Any] = {
        "has_video": False,
        "video_url": None,
        "video_id": None,
        "video_provider": None,
        "video_aspect": "",
        "video_poster": None,
        "video_title": "",
    }
    seen_p = set()
    seen_stems = set()
    seen_vids = set()
    dom_seq = 0
    if cover_image:
        seen_stems.add(_media_stem(cover_image))

    if not content_html or not (HAS_SELECTOLAX and LexborHTMLParser is not None):
        return paragraphs, subheadings, inline_images, inline_videos, vmeta

    def _record_video(v_url: str, provider: str, vid_id: Optional[str] = None, v_title: str = "", aspect: str = "16x9", poster: str = "", caption: str = "") -> None:
        nonlocal dom_seq
        u = html.unescape((v_url or "").strip())
        if not u.startswith(("http://", "https://")):
            return
        low = u.lower()
        if any(aud in low for aud in AUDIO_ONLY_IFRAME_DOMAINS):
            return
        if any(ad in low for ad in ("doubleclick", "googlesyndication", "taboola", "outbrain", "connatix", "primis", "jw-player-inline-promo")):
            return
        dk = (provider, vid_id or u.split("?")[0].lower())
        if dk in seen_vids:
            return
        seen_vids.add(dk)
        dom_seq += 1
        obj: Dict[str, Any] = {
            "url": u,
            "provider": provider,
            "after_para": max(-1, len(paragraphs) - 1),
            "aspect": aspect or "16x9",
            "dom_order": dom_seq,
        }
        if vid_id:
            obj["video_id"] = vid_id
        ct = _clean_text(v_title)
        if ct:
            obj["title"] = ct[:200]
        cc = _clean_text(caption)
        if cc and len(cc) >= 5:
            obj["caption"] = cc[:240]
        if poster and _is_valid_sa_image(poster):
            obj["poster"] = poster
        inline_videos.append(obj)

    tree = LexborHTMLParser(content_html)
    for sel in (
        "script", "style", "noscript", "form", "svg", "aside",
        "[class*='newsletter']", "[class*='subscribe']", "[class*='promo']",
        "[class*='related']", "[class*='advert']", "[class*='sponsor']",
        "[class*='thecube-cta']", "[class*='support-box']", ".screen-reader-text",
    ):
        for n in tree.css(sel):
            n.decompose()

    for node in tree.css("h2, h3, h4, figure, video, iframe, p, blockquote, li"):
        tag = (node.tag or "").lower()
        if tag in ("p", "li", "blockquote"):
            p_anc = node.parent
            in_fig = False
            while p_anc is not None:
                if (p_anc.tag or "").lower() in ("figure", "figcaption"):
                    in_fig = True
                    break
                p_anc = p_anc.parent
            if in_fig:
                continue

        if tag == "figure":
            cap_el = node.css_first("figcaption")
            cap_txt = _clean_text(cap_el.text(separator=" ") if cap_el else "")
            vid_el = node.css_first("video")
            if vid_el:
                v_src = (vid_el.attributes.get("src") or "").strip()
                if not v_src:
                    s_el = vid_el.css_first("source")
                    if s_el:
                        v_src = (s_el.attributes.get("src") or "").strip()
                if v_src:
                    _record_video(v_src, "mp4", poster=(vid_el.attributes.get("poster") or "").strip(), caption=cap_txt)
                    continue
            ifr_el = node.css_first("iframe")
            if ifr_el:
                src = html.unescape((ifr_el.attributes.get("src") or ifr_el.attributes.get("data-src") or "").strip())
                low = src.lower()
                if "youtube.com/embed/" in low or "youtube-nocookie.com/embed/" in low:
                    m_yt = re.search(r"embed/([A-Za-z0-9_-]{8,15})", src)
                    _record_video(src, "iframe", vid_id=(m_yt.group(1) if m_yt else None), v_title=(ifr_el.attributes.get("title") or ""), caption=cap_txt)
                    continue
                if "player.vimeo.com/video/" in low:
                    m_vm = re.search(r"player\.vimeo\.com/video/(\d+)", src, re.I)
                    _record_video(src, "iframe", vid_id=(m_vm.group(1) if m_vm else None), v_title=(ifr_el.attributes.get("title") or ""), caption=cap_txt)
                    continue
            img_el = node.css_first("img")
            if img_el:
                src = html.unescape((img_el.attributes.get("data-src") or img_el.attributes.get("src") or "").strip())
                if _is_valid_sa_image(src):
                    stem = _media_stem(src)
                    if stem and stem not in seen_stems:
                        seen_stems.add(stem)
                        dom_seq += 1
                        final_cap = cap_txt or _clean_text(img_el.attributes.get("alt") or "")
                        im_obj: Dict[str, Any] = {
                            "url": src,
                            "after_para": max(-1, len(paragraphs) - 1),
                            "dom_order": dom_seq,
                        }
                        if final_cap and len(final_cap) >= 5:
                            im_obj["caption"] = final_cap[:240]
                            im_obj["caption_en"] = final_cap[:240]
                        inline_images.append(im_obj)
            continue

        if tag == "video":
            v_src = (node.attributes.get("src") or "").strip()
            if not v_src:
                s_el = node.css_first("source")
                if s_el:
                    v_src = (s_el.attributes.get("src") or "").strip()
            if v_src:
                _record_video(v_src, "mp4", poster=(node.attributes.get("poster") or "").strip())
            continue

        if tag == "iframe":
            src = html.unescape((node.attributes.get("src") or node.attributes.get("data-src") or "").strip())
            low = src.lower()
            v_title = (node.attributes.get("title") or "").strip()
            if "youtube.com/embed/" in low or "youtube-nocookie.com/embed/" in low:
                m_yt = re.search(r"embed/([A-Za-z0-9_-]{8,15})", src)
                _record_video(src, "iframe", vid_id=(m_yt.group(1) if m_yt else None), v_title=v_title)
            elif "player.vimeo.com/video/" in low:
                m_vm = re.search(r"player\.vimeo\.com/video/(\d+)", src, re.I)
                _record_video(src, "iframe", vid_id=(m_vm.group(1) if m_vm else None), v_title=v_title)
            continue

        txt = _clean_text(node.text(separator=" "))
        if not txt:
            continue

        # Hard-stop at SiliconANGLE donation / AWS Marketplace / theCUBE tail boilerplate
        if _is_stop_tail(txt):
            break

        if tag in ("h2", "h3", "h4"):
            if not _is_noise_heading(txt):
                subheadings.append(txt)
                hk = f"h:{txt.lower()}"
                if hk not in seen_p:
                    seen_p.add(hk)
                    paragraphs.append(f"### {txt}")
            continue

        if tag == "li" and len(txt) < 35:
            continue
        if _is_noise_paragraph(txt):
            continue
        key = txt.lower()[:120]
        if key not in seen_p:
            seen_p.add(key)
            paragraphs.append(txt)

    if inline_videos:
        fv = inline_videos[0]
        vmeta = {
            "has_video": True,
            "video_url": fv["url"],
            "video_id": fv.get("video_id"),
            "video_provider": fv.get("provider") or "iframe",
            "video_aspect": fv.get("aspect") or "16x9",
            "video_poster": fv.get("poster"),
            "video_title": fv.get("title") or fv.get("caption") or "",
        }

    return paragraphs, subheadings, inline_images[:24], inline_videos[:10], vmeta


def _parse_sa_wp_post(post: Dict[str, Any]) -> Dict[str, Any]:
    out: Dict[str, Any] = {
        "title": "",
        "summary": "",
        "author": "",
        "published_at": post.get("date_gmt") or post.get("date"),
        "cover_image": None,
        "paragraphs": [],
        "subheadings": [],
        "inline_images": [],
        "inline_videos": [],
        "has_video": False,
        "video_url": None,
        "video_id": None,
        "video_provider": None,
        "video_aspect": "",
        "video_poster": None,
        "video_title": "",
        "class_list": post.get("class_list") if isinstance(post.get("class_list"), list) else [],
        "raw_content_text": "",
    }
    raw_t = (post.get("title") or {}).get("rendered") if isinstance(post.get("title"), dict) else post.get("title")
    if raw_t:
        out["title"] = _clean_sa_title(str(raw_t))

    raw_ex = (post.get("excerpt") or {}).get("rendered") if isinstance(post.get("excerpt"), dict) else ""
    if raw_ex:
        out["summary"] = _clean_text(re.sub(r"<[^>]+>", " ", raw_ex))

    emb = post.get("_embedded") if isinstance(post.get("_embedded"), dict) else {}
    authors: List[str] = []
    for a in (emb.get("author") or []):
        if isinstance(a, dict) and a.get("name"):
            nm = _clean_sa_author(str(a["name"]))
            if nm and nm not in authors:
                authors.append(nm)
    if authors:
        out["author"] = " and ".join(authors) if len(authors) <= 2 else ", ".join(authors[:-1]) + f", and {authors[-1]}"

    cand_cover = post.get("jetpack_featured_media_url") or ""
    if not cand_cover and emb.get("wp:featuredmedia"):
        fm = emb["wp:featuredmedia"][0]
        if isinstance(fm, dict):
            cand_cover = fm.get("source_url") or ""
    if cand_cover and _is_valid_sa_image(str(cand_cover)):
        out["cover_image"] = html.unescape(str(cand_cover).strip())

    c_html = (post.get("content") or {}).get("rendered") if isinstance(post.get("content"), dict) else ""
    out["raw_content_text"] = _clean_text(re.sub(r"<[^>]+>", " ", c_html))
    paras, subs, inls, inl_vids, vmeta = _parse_content_dom(c_html, cover_image=out["cover_image"])
    out["paragraphs"] = paras
    out["subheadings"] = subs
    out["inline_images"] = inls
    out["inline_videos"] = inl_vids
    if vmeta.get("has_video"):
        out.update(vmeta)
    return out


def _parse_sa_html(html_text: str) -> Dict[str, Any]:
    out: Dict[str, Any] = {
        "title": "",
        "summary": "",
        "author": "",
        "published_at": None,
        "cover_image": None,
        "paragraphs": [],
        "subheadings": [],
        "inline_images": [],
        "inline_videos": [],
        "has_video": False,
        "video_url": None,
        "video_id": None,
        "video_provider": None,
        "video_aspect": "",
        "video_poster": None,
        "video_title": "",
        "class_list": [],
        "raw_content_text": "",
    }
    if not html_text:
        return out

    m_og_t = re.search(r'<meta[^>]+property=["\']og:title["\'][^>]+content=["\']([^"\']+)["\']', html_text, re.I)
    if m_og_t:
        out["title"] = _clean_sa_title(m_og_t.group(1))
    m_og_d = re.search(r'<meta[^>]+property=["\']og:description["\'][^>]+content=["\']([^"\']+)["\']', html_text, re.I)
    if m_og_d:
        out["summary"] = _clean_text(m_og_d.group(1))
    m_og_i = re.search(r'<meta[^>]+property=["\']og:image["\'][^>]+content=["\']([^"\']+)["\']', html_text, re.I)
    if m_og_i and _is_valid_sa_image(m_og_i.group(1)):
        out["cover_image"] = html.unescape(m_og_i.group(1).strip())
    m_pub = re.search(r'<meta[^>]+property=["\']article:published_time["\'][^>]+content=["\']([^"\']+)["\']', html_text, re.I)
    if m_pub:
        out["published_at"] = m_pub.group(1).strip()

    if HAS_SELECTOLAX and LexborHTMLParser is not None:
        tree = LexborHTMLParser(html_text)
        h1 = tree.css_first("h1")
        if h1:
            h1_t = _clean_sa_title(h1.text(separator=" "))
            if len(h1_t) >= 10:
                out["title"] = h1_t

        header = tree.css_first("article header") or tree.css_first(".single-post-header") or tree.css_first("header")
        if header:
            for a in header.css('a[rel="author"], a[href*="/author/"]'):
                nm = _clean_sa_author(a.text(separator=" "))
                if nm:
                    out["author"] = nm
                    break

        body = tree.css_first(".single-post-content") or tree.css_first(".entry-content") or tree.css_first("article")
        if body:
            out["raw_content_text"] = _clean_text(body.text(separator=" "))
            paras, subs, inls, inl_vids, vmeta = _parse_content_dom(body.html or "", cover_image=out["cover_image"])
            out["paragraphs"] = paras
            out["subheadings"] = subs
            out["inline_images"] = inls
            out["inline_videos"] = inl_vids
            if vmeta.get("has_video"):
                out.update(vmeta)
    return out


def _fetch_sa_wp_post(url: str, proxies: Optional[Dict[str, str]] = None) -> Tuple[Optional[Dict[str, Any]], str]:
    slug = _extract_sa_slug(url)
    if not slug:
        return None, "failed"
    api_url = f"https://siliconangle.com/wp-json/wp/v2/posts?slug={quote(slug)}&_embed=1"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Accept": "application/json,text/plain,*/*",
    }
    data = None
    if HAS_CURL_CFFI:
        for _ in range(2):
            try:
                r = cffi_requests.get(api_url, impersonate="chrome124", headers=headers, proxies=proxies, timeout=15)
                if r.status_code == 200:
                    data = r.json()
                    break
            except Exception:
                pass
    if data is None and HAS_REQUESTS:
        try:
            r = requests.get(api_url, headers=headers, proxies=proxies, timeout=15)
            if r.status_code == 200:
                data = r.json()
        except Exception:
            pass
    if isinstance(data, list) and data and isinstance(data[0], dict):
        return data[0], "siliconangle_wp_slug"
    return None, "failed"


def _fetch_sa_html(url: str, proxies: Optional[Dict[str, str]] = None) -> Tuple[Optional[str], str]:
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
    }
    if HAS_CURL_CFFI:
        for _ in range(2):
            try:
                r = cffi_requests.get(url, impersonate="chrome124", headers=headers, proxies=proxies, timeout=16)
                if r.status_code == 200 and len(r.text) > 10000:
                    return r.text, "siliconangle_html_cffi"
            except Exception:
                pass
    if HAS_REQUESTS:
        try:
            r = requests.get(url, headers=headers, proxies=proxies, timeout=16)
            if r.status_code == 200 and len(r.text) > 10000:
                return r.text, "siliconangle_html_requests"
        except Exception:
            pass
    return None, "failed"


def crawl_siliconangle(
    url: str,
    title: str = "",
    html_text: Optional[str] = None,
    wp_post: Optional[Dict[str, Any]] = None,
    localize_cover: bool = True,
    use_cache: bool = True,
) -> Dict[str, Any]:
    """Main isolated entrypoint for SiliconANGLE (`siliconangle.com`)."""
    result: Dict[str, Any] = {
        "url": url,
        "status": "failed",
        "domain": "siliconangle.com",
        "source": "SiliconANGLE",
        "title": _clean_sa_title(title) if title else "",
        "summary": "",
        "author": "SiliconANGLE",
        "published_at": None,
        "cover_image": None,
        "image_url": None,
        "inline_images": [],
        "inline_videos": [],
        "lead_paragraph": "",
        "paragraphs": [],
        "full_text": "",
        "article_content": "",
        "article_content_en": "",
        "subheadings": [],
        "key_metrics": [],
        "quotes": [],
        "paras_count": 0,
        "is_substantive": False,
        "is_paywalled": False,
        "has_video": False,
        "video_url": None,
        "video_id": None,
        "video_provider": None,
        "video_aspect": "",
        "video_poster": None,
        "video_title": "",
        "is_filtered_out": False,
        "filter_reason": "",
        "extraction_tier": "failed",
    }

    if not url or not is_siliconangle_url(url):
        return result

    pre_flagged, pre_reason = detect_low_value_roundup_or_promo(title=title, url=url)
    if pre_flagged:
        result["status"] = "filtered_promo_or_roundup"
        result["is_filtered_out"] = True
        result["filter_reason"] = pre_reason
        return result

    cache_key = _canonical_sa_key(url)
    if use_cache and html_text is None and wp_post is None:
        _load_disk_cache()
        cached = _SILICONANGLE_CACHE.get(cache_key)
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

    proxies = _get_proxies() if (html_text is None and wp_post is None) else None
    parsed: Dict[str, Any] = {}
    tier = "failed"

    if wp_post is not None:
        parsed = _parse_sa_wp_post(wp_post)
        tier = "siliconangle_injected_wp"
    elif html_text is None:
        post_obj, wp_tier = _fetch_sa_wp_post(url, proxies=proxies)
        if post_obj:
            parsed = _parse_sa_wp_post(post_obj)
            tier = wp_tier

    if parsed:
        post_flagged, post_reason = detect_low_value_roundup_or_promo(
            title=parsed.get("title") or title,
            url=url,
            body=parsed.get("raw_content_text") or "\n\n".join(parsed.get("paragraphs") or []),
            summary=parsed.get("summary") or "",
            classes=parsed.get("class_list"),
        )
        if post_flagged:
            result["status"] = "filtered_promo_or_roundup"
            result["is_filtered_out"] = True
            result["filter_reason"] = post_reason
            if use_cache and html_text is None and wp_post is None:
                _load_disk_cache()
                _SILICONANGLE_CACHE[cache_key] = dict(result)
                _save_disk_cache()
            return result

    need_html = (
        html_text is not None
        or (
            wp_post is None
            and (
                not parsed
                or not parsed.get("cover_image")
                or not parsed.get("author")
                or len("\n\n".join(parsed.get("paragraphs") or [])) < 400
            )
        )
    )
    if need_html:
        raw_html = html_text
        html_tier = "siliconangle_injected_html"
        if raw_html is None:
            raw_html, html_tier = _fetch_sa_html(url, proxies=proxies)
        if raw_html:
            hp = _parse_sa_html(raw_html)
            if not parsed:
                parsed = hp
                tier = html_tier
            else:
                for fk in ("title", "summary", "author", "cover_image", "published_at"):
                    if not parsed.get(fk) and hp.get(fk):
                        parsed[fk] = hp[fk]
                wp_len = len("\n\n".join(parsed.get("paragraphs") or []))
                hp_len = len("\n\n".join(hp.get("paragraphs") or []))
                if wp_len < 400 and hp_len > wp_len:
                    parsed["paragraphs"] = hp["paragraphs"]
                    parsed["subheadings"] = hp.get("subheadings") or parsed.get("subheadings") or []
                    parsed["inline_images"] = hp.get("inline_images") or parsed.get("inline_images") or []
                    parsed["inline_videos"] = hp.get("inline_videos") or parsed.get("inline_videos") or []
                    tier = f"{tier}+{html_tier}"

    if not parsed:
        return result

    cover = parsed.get("cover_image")
    inlines = list(parsed.get("inline_images") or [])
    if cover and not _is_valid_sa_image(cover):
        cover = None
    if not cover and inlines:
        first_cand = inlines[0]["url"] if isinstance(inlines[0], dict) else str(inlines[0])
        if _is_valid_sa_image(first_cand):
            cover = first_cand
    if cover:
        c_stem = _media_stem(cover)
        inlines = [
            e for e in inlines
            if _media_stem(e["url"] if isinstance(e, dict) else str(e)) != c_stem
        ]
        if localize_cover and html_text is None and wp_post is None:
            cover = _localize_sa_image(cover, proxies=proxies)

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
        result["video_id"] = parsed.get("video_id")
        result["video_provider"] = parsed.get("video_provider") or "iframe"
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

    if len(paras) >= 2 and len(full_text) >= 400:
        result["status"] = "success"
        result["is_substantive"] = True
        result["is_paywalled"] = False
        if use_cache and html_text is None and wp_post is None:
            _load_disk_cache()
            _SILICONANGLE_CACHE[cache_key] = dict(result)
            _save_disk_cache()
    elif result["title"] or cover:
        result["status"] = "metadata_only"

    return result
