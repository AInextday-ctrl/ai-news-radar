import json
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

with open("data/latest_news.json", "r", encoding="utf-8") as f:
    data = json.load(f)

items = data.get("items", [])
empty_shells = []
for it in items:
    cat = it.get("category", "news")
    if cat != "news":
        continue
    snip = (it.get("content_snippet") or "").strip()
    sum_zh = (it.get("summary_zh") or "").strip()
    img = (it.get("image_url") or "").strip()
    title = (it.get("title") or it.get("title_zh") or "").strip()

    is_ge_logo = "lh3.googleusercontent.com/J6_coFbog" in img
    is_empty_text = (len(snip) < 20 and len(sum_zh) < 15) or sum_zh in ["来源", "官方快讯", "今日要闻"] or "聚焦该事件的最新进展" in sum_zh
    is_title_repeat = (title in sum_zh and len(sum_zh) <= len(title) + 10)

    if is_ge_logo or (is_empty_text and is_title_repeat):
        empty_shells.append({
            "id": it.get("id"),
            "title": it.get("title_zh") or it.get("title"),
            "source": it.get("source"),
            "image": img[:60],
            "summary": sum_zh[:40]
        })

print(f"在 latest_news.json (共 {len(items)} 条) 中发现了 {len(empty_shells)} 条空壳/GE图标条目:")
for s in empty_shells[:15]:
    print(f" - [{s['source']}] {s['title']} | 摘要: {s['summary']}")
