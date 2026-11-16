import json

real_title = "US Moves to Curb Remote Access to Nvidia's Advanced AI Chips"
real_author = "Maggie Eastland and Magan Crane"
real_img = "https://ainewsradar.xyz/images/bloomberg_73a3b9085b60c810.jpg"
real_caption = "US Moves to Restrict Remote Access to Advanced AI Chips (Bloomberg TV)"

def update_item(item):
    if item.get("id") == "73a3b9085b60c810":
        item["title"] = real_title
        item["title_en"] = real_title
        item["author"] = real_author
        item["image_url"] = real_img
        item["image_caption"] = real_caption
        item["has_video"] = True
        item["video_title"] = "US Moves to Restrict Remote Access to Advanced AI Chips"
        return True
    return False

def update_container(obj):
    cnt = 0
    if isinstance(obj, list):
        for it in obj:
            if isinstance(it, dict):
                if update_item(it):
                    cnt += 1
                else:
                    cnt += update_container(it)
    elif isinstance(obj, dict):
        for k, v in obj.items():
            if isinstance(v, (dict, list)):
                cnt += update_container(v)
    return cnt

for p in ["data/latest_news.json", "data/archive_news.json", "public/data/latest_news.json", "public/data/archive_news.json"]:
    with open(p, "r", encoding="utf-8") as f:
        data = json.load(f)
    c = update_container(data)
    with open(p, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(p, "updated:", c)

print("Done updating datasets!")
