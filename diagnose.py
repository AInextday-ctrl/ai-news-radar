import sys
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

import httpx
import feedparser

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
}

# 1. Test Reddit
print("Testing Reddit directly...")
try:
    with httpx.Client(headers=headers, follow_redirects=True, timeout=10) as client:
        resp = client.get("https://www.reddit.com/r/LocalLLaMA/hot.json?limit=5")
        print(f"Reddit Status: {resp.status_code}")
        if resp.status_code == 200:
            posts = resp.json().get("data", {}).get("children", [])
            print(f"Reddit posts found: {len(posts)}")
        else:
            print(f"Reddit response snippet: {resp.text[:200]}")
except Exception as e:
    print(f"Reddit exception: {e}")

# 2. Test YouTube RSS
print("\nTesting YouTube RSS directly...")
yt_url = "https://www.youtube.com/feeds/videos.xml?channel_id=UCsBjURrPoezykLs9EqgamOA"
try:
    with httpx.Client(headers=headers, follow_redirects=True, timeout=10) as client:
        resp = client.get(yt_url)
        print(f"YouTube HTTP Status: {resp.status_code}")
        if resp.status_code == 200:
            feed = feedparser.parse(resp.text)
            print(f"YouTube parsed entries: {len(feed.entries)}")
            if feed.entries:
                print(f"Sample: {feed.entries[0].title}")
except Exception as e:
    print(f"YouTube exception: {e}")
