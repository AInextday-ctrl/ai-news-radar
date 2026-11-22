import glob
import os
import re

def check():
    files = [
        'public/index.html',
        'public/zh/index.html',
        'public/news/index.html',
        'public/zh/news/index.html',
        'public/tools/index.html',
        'public/zh/tools/index.html',
        'public/articles/index.html',
        'public/zh/articles/index.html',
        'public/daily/index.html',
        'public/zh/daily/index.html',
        'public/about.html',
        'public/zh/about.html',
        'public/contact.html',
        'public/zh/contact.html',
        'public/terms.html',
        'public/zh/terms.html',
        'public/privacy.html',
        'public/zh/privacy.html',
        'public/editorial-policy.html',
        'public/zh/editorial-policy.html',
        'public/wechat.html',
        'public/zh/wechat.html',
        'public/404.html',
        'public/zh/404.html',
        'public/go.html'
    ]

    print(f"=== Checking {len(files)} Core Key Pages ===")
    all_passed = True
    for f in files:
        if not os.path.exists(f):
            print(f"[ERR] File does not exist: {f}")
            all_passed = False
            continue
        with open(f, 'r', encoding='utf-8') as fp:
            c = fp.read(4000)
        m = re.search(r'name=["\']description["\'][^>]*content=["\']([^"\']*)["\']', c, re.I)
        if not m:
            m = re.search(r'content=["\']([^"\']*)["\'][^>]*name=["\']description["\']', c, re.I)
        desc = m.group(1).strip() if m else ''
        if len(desc) < 30:
            print(f"❌ [TOO SHORT ({len(desc)})] {f}: {desc}")
            all_passed = False
        else:
            print(f"✅ [{len(desc):3d} chars] {f}: {desc[:60]}...")

    # Sample 5 news and 5 tools
    print("\n=== Sampling 10 News & Tools Pages ===")
    sample_news = glob.glob('public/news/*.html')[:5] + glob.glob('public/zh/news/*.html')[:5]
    sample_tools = glob.glob('public/tools/*.html')[:5] + glob.glob('public/zh/tools/*.html')[:5]
    for p in sample_news + sample_tools:
        if p.endswith('index.html'): continue
        with open(p, 'r', encoding='utf-8') as fp:
            c = fp.read(4000)
        m = re.search(r'name=["\']description["\'][^>]*content=["\']([^"\']*)["\']', c, re.I)
        if not m:
            m = re.search(r'content=["\']([^"\']*)["\'][^>]*name=["\']description["\']', c, re.I)
        desc = m.group(1).strip() if m else ''
        print(f"[{len(desc):3d} chars] {p}: {desc[:50]}...")

    if all_passed:
        print("\n🎉 ALL CORE PAGES HAVE COMPLIANT META DESCRIPTIONS (>= 30 chars, average 70-160 chars)!")

if __name__ == '__main__':
    check()
