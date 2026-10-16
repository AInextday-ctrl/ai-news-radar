import os
import sys
import glob
import re

sys.stdout.reconfigure(encoding='utf-8')

print("=== ADSENSE ACCURATE DIAGNOSTIC SCAN ===")

def get_html_lang(txt):
    m = re.search(r'<html[^>]*lang=["\']([^"\']+)["\']', txt, re.IGNORECASE)
    return m.group(1) if m else "unknown"

# 1. Compliance pages (English and Chinese)
print("\n[Compliance Pages - English]")
compliance_files = ['about.html', 'contact.html', 'privacy.html', 'terms.html', 'editorial-policy.html']
for f in compliance_files:
    p = os.path.join('public', f)
    if os.path.exists(p):
        content = open(p, encoding='utf-8').read()
        lang = get_html_lang(content)
        has_adsense = 'ca-pub-' in content
        title = content[content.find('<title>'):content.find('</title>')+8] if '<title>' in content else 'none'
        print(f"  {f:22} | html lang: {lang:6} | size: {len(content):6} | ad: {has_adsense} | title: {title[:45]}")
    else:
        print(f"  {f:22} | MISSING!")

print("\n[Compliance Pages - Chinese (/zh)]")
for f in compliance_files:
    p = os.path.join('public', 'zh', f)
    if os.path.exists(p):
        content = open(p, encoding='utf-8').read()
        lang = get_html_lang(content)
        has_adsense = 'ca-pub-' in content
        title = content[content.find('<title>'):content.find('</title>')+8] if '<title>' in content else 'none'
        print(f"  zh/{f:19} | html lang: {lang:6} | size: {len(content):6} | ad: {has_adsense} | title: {title[:45]}")
    else:
        print(f"  zh/{f:19} | MISSING!")

# 2. Articles (English & Chinese)
en_arts = [a for a in glob.glob('public/articles/*.html') if not a.endswith('index.html')]
zh_arts = [a for a in glob.glob('public/zh/articles/*.html') if not a.endswith('index.html')]
print(f"\n[Articles] English: {len(en_arts)} | Chinese: {len(zh_arts)}")
if en_arts:
    sample_en = en_arts[0]
    c_en = open(sample_en, encoding='utf-8').read()
    print(f"  Sample EN article: {os.path.basename(sample_en)} | html lang: {get_html_lang(c_en)} | words: {len(c_en.split())}")
if zh_arts:
    sample_zh = zh_arts[0]
    c_zh = open(sample_zh, encoding='utf-8').read()
    print(f"  Sample ZH article: {os.path.basename(sample_zh)} | html lang: {get_html_lang(c_zh)} | words: {len(c_zh.split())}")

# 3. Daily pages (English & Chinese)
daily_en = [d for d in glob.glob('public/daily/*.html') if not d.endswith('index.html')]
daily_zh = [d for d in glob.glob('public/zh/daily/*.html') if not d.endswith('index.html')]
print(f"\n[Daily Briefings] English: {len(daily_en)} | Chinese: {len(daily_zh)}")
if daily_en:
    d = daily_en[0]
    content = open(d, encoding='utf-8').read()
    print(f"  Sample EN daily: {os.path.basename(d)} | noindex: {'noindex' in content} | ad: {'ca-pub-' in content} | html lang: {get_html_lang(content)}")
if daily_zh:
    d = daily_zh[0]
    content = open(d, encoding='utf-8').read()
    print(f"  Sample ZH daily: {os.path.basename(d)} | noindex: {'noindex' in content} | ad: {'ca-pub-' in content} | html lang: {get_html_lang(content)}")

# 4. Robots.txt
print("\n[Robots.txt Content]:")
if os.path.exists('public/robots.txt'):
    print(open('public/robots.txt', encoding='utf-8').read().strip())

# 5. Sitemap.xml count
if os.path.exists('public/sitemap.xml'):
    sitemap_txt = open('public/sitemap.xml', encoding='utf-8').read()
    urls = re.findall(r'<loc>(.*?)</loc>', sitemap_txt)
    print(f"\n[Sitemap.xml] Total URLs indexed: {len(urls)}")
    print(f"  Sample URLs: {urls[:3]} ... {urls[-3:]}")

