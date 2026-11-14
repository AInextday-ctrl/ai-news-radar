#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
scripts/localize_tool_images.py
--------------------------------
Batch processes all AI tools across the entire platform:
1. Discards WordPress "Generating Preview..." placeholders (hash & size matching).
2. For GitHub projects: Prioritizes README architecture/UI screenshots & official GitHub OpenGraph cards.
3. For Web Apps: Uses high-res ProductHunt screenshots or validated website mshots.
4. Smart 16:9 Canvas Fitting (960x540):
   - Perfect 16:9 images are resized cleanly.
   - Banners and tall screenshots are centered on a subtle ambient blurred backdrop,
     ensuring ZERO text clipping, ZERO stretching, and 100% border-to-border alignment in the 16:9 card window.
5. Saves WebP locally at `public/assets/tool-previews/{tool_id}.webp`.
6. Updates data/latest_news.json, public/data/latest_news.json, archive_news.json, and master_archive.json.
"""

import os
import sys
import json
import re
import io
import time
import hashlib
import urllib.request
import urllib.parse
from concurrent.futures import ThreadPoolExecutor, as_completed
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageStat

try:
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')
except Exception:
    pass

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTPUT_DIR = os.path.join(ROOT_DIR, 'public', 'assets', 'tool-previews')
os.makedirs(OUTPUT_DIR, exist_ok=True)

PROXIES = {
    'http': 'http://127.0.0.1:7897',
    'https': 'http://127.0.0.1:7897'
}

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36',
    'Accept': 'image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8'
}

WP_PLACEHOLDER_HASH = 'c8914d4e2f06c574c382a47b1f2dbc12'

IGNORE_DOMAINS = [
    'shields.io', 'badgen.net', 'badge', 'travis-ci', 'hellogithub',
    'star-history', 'trendshift', 'producthunt', 'contrib.rocks',
    'discord', 'twitter', 'visitor-badge', 'buymeacoffee',
    'opencollective', 'repobeats.axiom.co', 'github-actions'
]

def clean_url(u: str) -> str:
    if not u or not isinstance(u, str):
        return ""
    u = u.split('#')[0]
    u = re.sub(r'[\?&](ref|utm_[^&=]+)=[^&]*', '', u)
    if u.endswith('?') or u.endswith('&'):
        u = u[:-1]
    return u.strip()

def is_bad_placeholder(data: bytes) -> bool:
    if not data or len(data) < 500:
        return True
    if len(data) == 2830 or hashlib.md5(data).hexdigest() == WP_PLACEHOLDER_HASH:
        return True
    return False

def _check_local_proxy():
    import socket
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(0.5)
    try:
        s.connect(('127.0.0.1', 7897))
        s.close()
        return True
    except Exception:
        return False

HAS_LOCAL_PROXY = _check_local_proxy()

def fetch_url_bytes(url: str, timeout: int = 12) -> bytes:
    """Try fetching through proxy if available, then direct."""
    # Attempt 1: Via proxy (only if proxy is actually alive)
    if HAS_LOCAL_PROXY:
        try:
            proxy_handler = urllib.request.ProxyHandler(PROXIES)
            opener = urllib.request.build_opener(proxy_handler)
            req = urllib.request.Request(url, headers=HEADERS)
            with opener.open(req, timeout=timeout) as res:
                if res.status == 200:
                    b = res.read()
                    if not is_bad_placeholder(b):
                        return b
        except Exception:
            pass

    # Attempt 2: Direct
    try:
        direct_opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
        req = urllib.request.Request(url, headers=HEADERS)
        with direct_opener.open(req, timeout=timeout) as res:
            if res.status == 200:
                b = res.read()
                if not is_bad_placeholder(b):
                    return b
    except Exception:
        pass

    return b""

def extract_github_readme_images(owner: str, repo: str) -> list:
    branches = ['main', 'master']
    found_imgs = []
    for branch in branches:
        url = f"https://raw.githubusercontent.com/{owner}/{repo}/{branch}/README.md"
        raw_text = fetch_url_bytes(url, timeout=6)
        if not raw_text:
            continue
        try:
            text = raw_text.decode('utf-8', errors='ignore')
            md_imgs = re.findall(r'!\[.*?\]\((.*?)\)', text)
            html_imgs = re.findall(r'<img[^>]+src=[\'"]([^\'"]+)[\'"]', text)
            all_raw = md_imgs + html_imgs
            for raw_img in all_raw:
                img_path = raw_img.split()[0].split('?')[0].strip('()\'"')
                if not img_path:
                    continue
                if any(ig in img_path.lower() for ig in IGNORE_DOMAINS):
                    continue
                if img_path.lower().endswith('.svg'):
                    if not any(k in img_path.lower() for k in ['architecture', 'flow', 'banner', 'overview', 'diagram']):
                        continue
                if img_path.startswith(('http://', 'https://')):
                    full_img = img_path
                elif img_path.startswith('/'):
                    full_img = f"https://raw.githubusercontent.com/{owner}/{repo}/{branch}{img_path}"
                elif not img_path.startswith('#'):
                    norm_path = img_path.lstrip('./')
                    full_img = f"https://raw.githubusercontent.com/{owner}/{repo}/{branch}/{norm_path}"
                else:
                    continue
                if full_img not in found_imgs:
                    found_imgs.append(full_img)
            if found_imgs:
                break
        except Exception:
            continue
    return found_imgs

def make_smart_16_9(im: Image.Image) -> Image.Image:
    """Adapts any image into a pixel-perfect 960x540 (16:9) frame without text clipping."""
    target_w, target_h = 960, 540
    if im.mode in ('RGBA', 'LA', 'P'):
        alpha = im.convert('RGBA')
        bg = Image.new('RGB', alpha.size, (11, 15, 25))
        bg.paste(alpha, mask=alpha.split()[3])
        im = bg
    elif im.mode != 'RGB':
        im = im.convert('RGB')

    w, h = im.size
    ratio = w / max(h, 1)

    # If already close to 16:9 (between 1.70 and 1.85), direct resize
    if 1.70 <= ratio <= 1.85:
        return im.resize((target_w, target_h), Image.Resampling.LANCZOS)

    # Ambient blurred background
    bg = im.resize((target_w, target_h), Image.Resampling.BILINEAR)
    bg = bg.filter(ImageFilter.GaussianBlur(radius=28))
    # Dim background slightly so the crisp foreground stands out
    darken = Image.new('RGB', (target_w, target_h), (11, 15, 25))
    bg = Image.blend(bg, darken, 0.40)

    # Fit foreground inside (960, 540)
    fg = im.copy()
    fg.thumbnail((target_w, target_h), Image.Resampling.LANCZOS)
    fg_w, fg_h = fg.size
    offset_x = (target_w - fg_w) // 2
    offset_y = (target_h - fg_h) // 2

    bg.paste(fg, (offset_x, offset_y))
    return bg

def is_meaningful_image(im: Image.Image) -> bool:
    """Rejects pitch black, solid color, or blank white frames."""
    stat = ImageStat.Stat(im.convert('RGB'))
    mean_val = sum(stat.mean) / len(stat.mean)
    std_val = sum(stat.stddev) / len(stat.stddev)
    if mean_val < 35 and std_val < 25:
        return False  # Pitch black / empty window
    if mean_val > 248 and std_val < 15:
        return False  # Blank white
    return True

def process_image_to_webp(raw_bytes: bytes, dest_path: str) -> bool:
    if is_bad_placeholder(raw_bytes):
        return False
    try:
        img = Image.open(io.BytesIO(raw_bytes))
        # Handle animated GIF: find the frame with highest contrast/action
        if getattr(img, 'is_animated', False):
            best_frame_idx = 0
            best_std = 0
            frames_to_check = min(img.n_frames, 25)
            for i in range(frames_to_check):
                img.seek(i)
                st = ImageStat.Stat(img.convert('RGB'))
                cur_std = sum(st.stddev)
                if cur_std > best_std:
                    best_std = cur_std
                    best_frame_idx = i
            img.seek(best_frame_idx)

        # Check entropy & quality
        if not is_meaningful_image(img):
            return False

        # Fit onto smart 16:9 canvas
        final_img = make_smart_16_9(img)
        final_img.save(dest_path, 'WEBP', quality=85, method=6)
        return True
    except Exception:
        return False

def generate_fallback_banner(app_name: str, scenario: str, dest_path: str):
    """Generate an elegant dark tech card when no visual is available."""
    w, h = 960, 540
    base = Image.new('RGB', (w, h), (11, 15, 25))
    draw = ImageDraw.Draw(base)

    for i in range(h):
        r = int(11 + (18 - 11) * (i / h))
        g = int(24 + (38 - 24) * (i / h))
        b = int(40 + (55 - 40) * (i / h))
        draw.line([(0, i), (w, i)], fill=(r, g, b))

    draw.rectangle([20, 20, w - 20, h - 20], outline=(16, 185, 129), width=2)
    draw.rectangle([26, 26, w - 26, h - 26], outline=(30, 41, 59), width=1)

    title = app_name or "AI Tool"
    draw.text((60, 180), "AI RADAR · TOOL PREVIEW", fill=(16, 185, 129))
    draw.text((60, 240), title, fill=(248, 250, 252))
    sub = scenario or "High Impact AI Application"
    draw.text((60, 320), sub, fill=(148, 163, 184))

    base.save(dest_path, 'WEBP', quality=85)

def get_tool_candidate_urls(tool: dict) -> list:
    candidates = []
    u_comb = f"{tool.get('url', '')} {tool.get('official_url', '')} {tool.get('source_url', '')}"
    is_gh = tool.get('tool_origin') == 'github' or 'github.com' in u_comb

    # Extract GitHub owner & repo
    gh_match = re.search(r'github\.com/([a-zA-Z0-9_\-\.]+)/([a-zA-Z0-9_\-\.]+)', u_comb, re.IGNORECASE)
    gh_owner, gh_repo = None, None
    if gh_match:
        gh_owner = gh_match.group(1)
        gh_repo = gh_match.group(2).rstrip('.git')
        if gh_repo.endswith(('.png', '.jpg', '.svg', '.json')):
            gh_owner, gh_repo = None, None

    # Priority 1 for GitHub tools: README UI / architecture visuals
    if is_gh and gh_owner and gh_repo:
        readme_imgs = extract_github_readme_images(gh_owner, gh_repo)
        for r_img in readme_imgs:
            if r_img not in candidates:
                candidates.append(r_img)

    # Priority 2: Existing preview_images (excluding placeholders & dead urls)
    existing = tool.get('preview_images') or []
    for p in existing:
        if not p or not isinstance(p, str):
            continue
        if any(bad in p for bad in ['photo-1618005182384-a83a8bd57fbe', 'microlink.io', '3CyW24Pkz4o', 'feeb7666']):
            continue
        if p.startswith('http') and p not in candidates:
            candidates.append(p)

    # Existing image_url
    img = tool.get('image_url') or ""
    if img and isinstance(img, str) and img.startswith('http') and img not in candidates:
        if not any(bad in img for bad in ['photo-1618005182384-a83a8bd57fbe', 'microlink.io']):
            candidates.append(img)

    # Priority for GitHub tools: GitHub OpenGraph Social Preview (informative, official, never broken)
    if is_gh and gh_owner and gh_repo:
        og = f"https://opengraph.githubassets.com/1/{gh_owner}/{gh_repo}"
        if og not in candidates:
            candidates.append(og)

    # Priority for Web Apps: Official website mshot (only if independent domain)
    off = clean_url(tool.get('official_url') or "")
    if not off or 'github.com' in off or 'huggingface.co' in off:
        u = clean_url(tool.get('url') or "")
        if u and 'github.com' not in u and 'huggingface.co' not in u:
            off = u
        else:
            off = ""

    if off and not is_gh:
        encoded = urllib.parse.quote(off, safe='')
        mshot = f"https://s0.wp.com/mshots/v1/{encoded}?w=1280&h=720"
        if mshot not in candidates:
            candidates.append(mshot)

    return candidates

def localize_single_tool(tool: dict) -> tuple:
    tid = str(tool.get('id') or '').strip()
    app_name = tool.get('app_name') or tool.get('title') or tid
    scenario = tool.get('scenario_tag') or "🤖 场景落地"
    if not tid:
        return tid, False, "no_id"

    dest_file = f"{tid}.webp"
    dest_path = os.path.join(OUTPUT_DIR, dest_file)

    # If file exists, check if it's the bad WordPress placeholder (2830 bytes)
    if os.path.exists(dest_path):
        sz = os.path.getsize(dest_path)
        if sz == 2830 or sz < 3500:
            raw_check = open(dest_path, 'rb').read()
            if is_bad_placeholder(raw_check):
                try:
                    os.remove(dest_path)
                except Exception:
                    pass
        elif sz > 3500:
            # Check if image is valid and meaningful
            try:
                im = Image.open(dest_path)
                if is_meaningful_image(im):
                    return tid, True, "already_exists"
                else:
                    os.remove(dest_path)
            except Exception:
                try:
                    os.remove(dest_path)
                except Exception:
                    pass

    candidates = get_tool_candidate_urls(tool)
    for cand in candidates:
        raw_b = fetch_url_bytes(cand, timeout=10)
        if raw_b and not is_bad_placeholder(raw_b):
            success = process_image_to_webp(raw_b, dest_path)
            if success and os.path.exists(dest_path) and os.path.getsize(dest_path) > 3500:
                return tid, True, f"saved_from_{cand[:40]}"

    # Fallback to high quality branded banner
    generate_fallback_banner(app_name, scenario, dest_path)
    return tid, True, "generated_fallback"

def main():
    print(f"=== Starting Smart 16:9 Tool Image Localization to {OUTPUT_DIR} ===")
    start_time = time.time()

    # Step 0: Purge any known WordPress placeholders
    purged = 0
    for f in os.listdir(OUTPUT_DIR):
        if f.endswith('.webp'):
            fp = os.path.join(OUTPUT_DIR, f)
            sz = os.path.getsize(fp)
            if sz == 2830 or sz < 3500:
                b = open(fp, 'rb').read()
                if is_bad_placeholder(b):
                    try:
                        os.remove(fp)
                        purged += 1
                    except Exception:
                        pass
    print(f"Purged {purged} bad WordPress placeholder files from cache.")

    # Load master files
    data_path = os.path.join(ROOT_DIR, 'data', 'latest_news.json')
    archive_path = os.path.join(ROOT_DIR, 'data', 'archive_news.json')
    master_path = os.path.join(ROOT_DIR, 'data', 'master_archive.json')

    latest_data = json.load(open(data_path, 'r', encoding='utf-8'))
    archive_data = json.load(open(archive_path, 'r', encoding='utf-8')) if os.path.exists(archive_path) else {'items': []}
    master_data = json.load(open(master_path, 'r', encoding='utf-8')) if os.path.exists(master_path) else {'items': []}

    latest_tools = latest_data.get('grouped', {}).get('tools') or []
    archive_tools = [i for i in archive_data.get('items', []) if i.get('category') in ('tools', 'applied_tools')]
    master_tools = [i for i in master_data.get('items', []) if i.get('category') in ('tools', 'applied_tools')]

    all_tools_map = {}
    for t in master_tools + archive_tools + latest_tools:
        tid = t.get('id')
        if tid:
            all_tools_map[tid] = t

    total_tools = len(all_tools_map)
    print(f"Total unique tools across datasets: {total_tools}")

    success_count = 0
    fail_count = 0

    with ThreadPoolExecutor(max_workers=16) as executor:
        futures = {executor.submit(localize_single_tool, tool): tool for tool in all_tools_map.values()}
        completed = 0
        for future in as_completed(futures):
            completed += 1
            tid, ok, reason = future.result()
            if ok:
                success_count += 1
            else:
                fail_count += 1
            if completed % 25 == 0 or completed == total_tools:
                print(f"[{completed}/{total_tools}] Success: {success_count}, Fail: {fail_count} (Last: {tid} - {reason})")

    # Update tool records across all files
    def update_tools_list(tools_list):
        if not isinstance(tools_list, list):
            return
        for t in tools_list:
            if not isinstance(t, dict):
                continue
            tid = str(t.get('id') or '').strip()
            dest_file = f"{tid}.webp"
            dest_path = os.path.join(OUTPUT_DIR, dest_file)
            if os.path.exists(dest_path) and os.path.getsize(dest_path) > 3500:
                local_url = f"/assets/tool-previews/{dest_file}"
                t['image_url'] = local_url
                cur_previews = t.get('preview_images') or []
                filtered = [p for p in cur_previews if p != local_url and 'photo-1618005182384-a83a8bd57fbe' not in p]
                t['preview_images'] = [local_url] + filtered

    if 'tools' in latest_data.get('grouped', {}):
        update_tools_list(latest_data['grouped']['tools'])
    if 'items' in latest_data:
        update_tools_list([i for i in latest_data['items'] if i.get('category') in ('tools', 'applied_tools')])

    with open(data_path, 'w', encoding='utf-8') as f:
        json.dump(latest_data, f, ensure_ascii=False, separators=(',', ':'))

    public_latest = os.path.join(ROOT_DIR, 'public', 'data', 'latest_news.json')
    if os.path.exists(public_latest):
        try:
            with open(public_latest, 'r', encoding='utf-8') as f:
                pub_data = json.load(f)
            if 'grouped' in pub_data and 'tools' in pub_data['grouped']:
                update_tools_list(pub_data['grouped']['tools'])
            if 'items' in pub_data:
                update_tools_list([i for i in pub_data['items'] if i.get('category') in ('tools', 'applied_tools')])
            with open(public_latest, 'w', encoding='utf-8') as f:
                json.dump(pub_data, f, ensure_ascii=False, separators=(',', ':'))
        except Exception as e:
            print(f"Warning updating public latest: {e}")

    if os.path.exists(archive_path):
        update_tools_list(archive_data.get('items', []))
        with open(archive_path, 'w', encoding='utf-8') as f:
            json.dump(archive_data, f, ensure_ascii=False, separators=(',', ':'))
        public_archive = os.path.join(ROOT_DIR, 'public', 'data', 'archive_news.json')
        if os.path.exists(public_archive):
            try:
                with open(public_archive, 'r', encoding='utf-8') as f:
                    pub_arch = json.load(f)
                arch_items = pub_arch if isinstance(pub_arch, list) else pub_arch.get('items', [])
                update_tools_list([i for i in arch_items if i.get('category') in ('tools', 'applied_tools')])
                with open(public_archive, 'w', encoding='utf-8') as f:
                    json.dump(pub_arch, f, ensure_ascii=False, separators=(',', ':'))
            except Exception as e:
                print(f"Warning updating public archive: {e}")

    if os.path.exists(master_path):
        update_tools_list(master_data.get('items', []))
        with open(master_path, 'w', encoding='utf-8') as f:
            json.dump(master_data, f, ensure_ascii=False, indent=2)

    elapsed = time.time() - start_time
    total_files = len(os.listdir(OUTPUT_DIR))
    total_size_mb = sum(os.path.getsize(os.path.join(OUTPUT_DIR, f)) for f in os.listdir(OUTPUT_DIR)) / (1024 * 1024)

    print(f"\n=== Localization Complete in {elapsed:.1f}s ===")
    print(f"Total WebP Images in {OUTPUT_DIR}: {total_files}")
    print(f"Total Local Storage Size: {total_size_mb:.2f} MB")
    print("All datasets updated successfully!")

if __name__ == '__main__':
    main()
