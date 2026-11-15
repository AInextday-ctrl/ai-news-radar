import os
import glob
import re

def clean_title_for_seo(raw_title: str, is_zh: bool = False) -> str:
    """
    Cleans and intelligently truncates an HTML title so it strictly conforms
    to Bing Webmaster and Google SERP guidelines (<= 65 characters, never > 70).
    """
    t = ' '.join(raw_title.strip().split())
    if len(t) <= 65:
        return t

    # Determine brand
    brand = 'AI 资讯雷达' if is_zh else 'AI News Radar'
    
    # Strip known verbose suffixes
    patterns = [
        r'\s*\|\s*Frontier AI Engineering Deep-Dive\s*\|\s*AI News Radar$',
        r'\s*\|\s*AI 深度智库 · 独家实操专栏\s*\|\s*AI 资讯雷达$',
        r'\s*\|\s*AI 深度智库 · 专题特稿\s*\|\s*AI 资讯雷达$',
        r'\s*\|\s*AI 深度智库 · 独家技术专题与产业研报全景库\s*\|\s*AI 资讯雷达$',
        r'\s*\|\s*Top \d+ AI Breakthroughs & Frontier News\s*\|\s*AI News Radar$',
        r'\s*\|\s*当日精选 \d+ 条 AI 重磅前沿快报\s*\|\s*AI 资讯雷达$',
        r'\s*\|\s*Comprehensive Daily AI Radar Briefings\s*\|\s*AI News Radar$',
        r'\s*\|\s*每日资讯雷达合集\s*\|\s*AI 资讯雷达$',
        r'\s*\|\s*AI News Radar$',
        r'\s*\|\s*AI 资讯雷达$',
        r'\s*\|\s*ainewsradar\.xyz$'
    ]
    body = t
    for p in patterns:
        m = re.search(p, body, re.IGNORECASE)
        if m:
            matched_str = m.group(0)
            if 'AI 资讯雷达' in matched_str:
                brand = 'AI 资讯雷达'
            elif 'AI News Radar' in matched_str or 'ainewsradar' in matched_str:
                brand = 'AI News Radar'
            body = body[:m.start()].strip()
            break
            
    suffix = f" | {brand}"
    avail = 65 - len(suffix)  # e.g. 49 chars for EN, 52 for ZH
    
    if ' - ' in body:
        parts = body.split(' - ', 1)
        name, hook = parts[0].strip(), parts[1].strip()
        if len(body) <= avail:
            return f"{body}{suffix}"
        avail_hook = avail - len(name) - 3  # for " - "
        if avail_hook >= 10:
            hook_clean = re.sub(r'^(?:is|an|a)\s+', '', hook, flags=re.I).strip()
            cut = hook_clean[:avail_hook].rstrip(" ,-—:|/·;")
            last_space = cut.rfind(' ')
            if not is_zh and last_space > 8:
                cut = cut[:last_space].rstrip(" ,-—:|/·;")
            return f"{name} - {cut}…{suffix}"
        else:
            name_cut = name[:avail].rstrip(" ,-—:|/·;")
            return f"{name_cut}{suffix}"
    else:
        if len(body) <= avail:
            return f"{body}{suffix}"
        cut = body[:avail].rstrip(" ,-—:|/·;")
        last_space = cut.rfind(' ')
        if not is_zh and last_space > avail // 2:
            cut = cut[:last_space].rstrip(" ,-—:|/·;")
        return f"{cut}…{suffix}"


def batch_clean_html_files():
    html_files = glob.glob('public/**/*.html', recursive=True)
    modified_count = 0
    
    for p in html_files:
        norm_p = p.replace('\\', '/')
        is_zh = '/zh/' in norm_p
        
        with open(p, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
            
        m = re.search(r'<title>(.*?)</title>', content, re.DOTALL | re.IGNORECASE)
        if not m:
            continue
            
        orig_title = m.group(1).strip()
        if len(orig_title) > 65:
            new_title = clean_title_for_seo(orig_title, is_zh=is_zh)
            # Ensure strictly <= 65 chars
            if len(new_title) > 65:
                # Fallback emergency clamp
                brand = 'AI 资讯雷达' if is_zh else 'AI News Radar'
                suf = f" | {brand}"
                new_title = new_title[:65 - len(suf)].rstrip(" ,-—:|/·;") + suf
                
            new_content = content[:m.start(1)] + new_title + content[m.end(1):]
            with open(p, 'w', encoding='utf-8') as f:
                f.write(new_content)
            modified_count += 1

    print(f"✅ Successfully sanitized {modified_count} HTML files in public/ to <= 65 chars!")


if __name__ == '__main__':
    batch_clean_html_files()
