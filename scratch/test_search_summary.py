import urllib.request
import urllib.parse
import re
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

title = "An AI Slowdown Has To Happen Regardless of Safety"
query = urllib.parse.quote(title)
url = f"https://html.duckduckgo.com/html/?q={query}"
req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"})

try:
    with urllib.request.urlopen(req, timeout=10) as r:
        html_data = r.read().decode("utf-8", errors="ignore")
        snippets = re.findall(r'<a class="result__snippet"[^>]*>(.*?)</a>', html_data)
        print(f"找到 {len(snippets)} 个结果：")
        for idx, s in enumerate(snippets[:3], 1):
            clean = re.sub(r'<[^>]+>', '', s).strip()
            print(f"[{idx}] {clean}")
except Exception as e:
    print(f"异常: {e}")
