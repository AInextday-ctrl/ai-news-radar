import glob
import os
import re

def verify():
    root_pages = [
        "public/index.html",
        "public/zh/index.html",
        "public/404.html",
        "public/zh/404.html",
        "public/about.html",
        "public/zh/about.html",
        "public/contact.html",
        "public/zh/contact.html",
        "public/privacy.html",
        "public/zh/privacy.html",
        "public/terms.html",
        "public/zh/terms.html",
        "public/dmca.html",
        "public/zh/dmca.html",
        "public/editorial-policy.html",
        "public/zh/editorial-policy.html",
        "public/wechat.html",
        "public/zh/wechat.html",
        "public/go.html",
        "public/zh/go.html",
        "public/m/index.html",
        "public/zh/m/index.html",
        "public/news/index.html",
        "public/zh/news/index.html",
        "public/tools/index.html",
        "public/zh/tools/index.html",
        "public/daily/index.html",
        "public/zh/daily/index.html",
        "public/articles/index.html",
        "public/zh/articles/index.html",
    ]
    
    desc_regex = re.compile(r'<meta[^>]+(?:name=["\']description["\'][^>]+content=["\']([^"\']*)["\']|content=["\']([^"\']*)["\'][^>]+name=["\']description["\'])', re.IGNORECASE)
    
    print("=== ROOT & HUB PAGES AUDIT ===")
    short_count = 0
    for p in root_pages:
        if not os.path.exists(p):
            print(f"❌ Missing file: {p}")
            continue
        with open(p, "r", encoding="utf-8", errors="ignore") as f:
            chunk = f.read(3000)
        m = desc_regex.search(chunk)
        if not m:
            print(f"❌ Missing meta description: {p}")
            short_count += 1
            continue
        d = (m.group(1) or m.group(2) or "").strip()
        l = len(d)
        status = "✅ PASS" if 70 <= l <= 170 else "⚠️ WARN"
        if l < 70:
            short_count += 1
        print(f"{status} [{l:3d} chars] {p}\n    -> {d[:90]}...")
        
    print(f"\nRoot audit finished. Pages under 70 chars: {short_count}")

    # Check sample of generated news & tools
    print("\n=== SAMPLE GENERATED NEWS & TOOLS PAGES ===")
    sample_news = glob.glob("public/news/*.html")[:5] + glob.glob("public/zh/news/*.html")[:5]
    sample_tools = glob.glob("public/tools/*.html")[:5] + glob.glob("public/zh/tools/*.html")[:5]
    for p in sample_news + sample_tools:
        if p.endswith("index.html"): continue
        with open(p, "r", encoding="utf-8", errors="ignore") as f:
            chunk = f.read(3000)
        m = desc_regex.search(chunk)
        if m:
            d = (m.group(1) or m.group(2) or "").strip()
            l = len(d)
            status = "✅ PASS" if 70 <= l <= 170 else "⚠️ WARN"
            print(f"{status} [{l:3d} chars] {p} -> {d[:70]}...")
        else:
            print(f"❌ Missing meta description: {p}")

if __name__ == "__main__":
    verify()
