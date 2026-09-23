import os
import sys
import json
import re

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(ROOT_DIR, "data")
PUBLIC_DATA_DIR = os.path.join(ROOT_DIR, "public", "data")
PUBLIC_DIR = os.path.join(ROOT_DIR, "public")

PATTERNS_TO_REMOVE = [
    re.compile(r'全面的最新新闻报道[，,]?\s*(?:从|由)?\s*(?:Google|谷歌|b谷歌)\s*新闻(?:汇总|聚合)?[^。！]*[。！]?', re.IGNORECASE),
    re.compile(r'(?:从|由)\s*(?:世界各地的|Google|谷歌|b谷歌)\s*(?:新闻|来源)?[^。！]*?(?:汇总|聚合)[^。！]*?[。！]?', re.IGNORECASE),
    re.compile(r'Comprehensive up-to-date news coverage, aggregated from sources all over the world by Google News\.?', re.IGNORECASE),
    re.compile(r'A comprehensive overview of the latest news stories from around the world aggregated from Google News sources\.?', re.IGNORECASE),
    re.compile(r'aggregated from sources all over the world by Google News', re.IGNORECASE),
    re.compile(r'全面的最新新闻报道[。！]?'),
    re.compile(r'行业核心力量围绕[“"\'「][^”"\'」]*?[”"\'」]\s*加速推进关键技术攻坚与工程落地[，,]?\s*力求在激烈的产业竞赛中确立先发优势[。！]?'),
    re.compile(r'.*?加速推进关键技术攻坚与工程落地.*?'),
]

TEMPLATE_INSIGHT_KEYWORDS = [
    "正在加速布局以构筑关键护城河",
    "正在加速技术卡位",
    "经受住效率与成本的双重检验",
    "经受住算力成本与用户留存的双重检验",
    "【行业研判】该动态折射出当前AI产业链",
    "科技圈的公关通稿向来习惯把精打细算",
    "剥开宣传层面的光环",
    "商业世界的法则向来残酷",
    "行业各方正在加速技术卡位"
]

def clean_string_content(s: str) -> str:
    if not isinstance(s, str) or not s:
        return s
    res = s
    if "加速推进关键技术攻坚与工程落地" in res:
        res = re.sub(r'Context:\s*行业核心力量围绕.*?加速推进关键技术攻坚与工程落地[，,]?力求在激烈的产业竞赛中确立先发优势[。！]?', '', res)
        res = re.sub(r'行业核心力量围绕.*?加速推进关键技术攻坚与工程落地[，,]?力求在激烈的产业竞赛中确立先发优势[。！]?', '', res)
        res = re.sub(r'Motivation:\s*行业核心力量围绕.*?加速推进关键技术攻坚与工程落地.*?', '', res)
    for p in PATTERNS_TO_REMOVE:
        res = p.sub('', res)
    res = re.sub(r'([。！？；，、])\1+', r'\1', res).strip(' ，,：:·-')
    return res

def clean_item_deep(item: dict) -> dict:
    if not isinstance(item, dict):
        return item
    
    for field in ["title_zh", "summary_zh", "content_snippet", "full_text_zh", "quote_zh"]:
        if item.get(field):
            item[field] = clean_string_content(item[field])
            
    if item.get("ai_analysis") and isinstance(item["ai_analysis"], dict):
        ana = item["ai_analysis"]
        for b_field in ["briefing_zh", "digest_zh", "briefing_en", "digest_en"]:
            if ana.get(b_field):
                ana[b_field] = clean_string_content(ana[b_field])
                if not ana[b_field] or len(ana[b_field]) < 6:
                    ana[b_field] = item.get("summary_zh") or item.get("title_zh", "")

        for i_field in ["insight_zh", "takeaway_zh"]:
            raw_ins = str(ana.get(i_field) or "")
            if any(k in raw_ins for k in TEMPLATE_INSIGHT_KEYWORDS) or len(raw_ins.strip()) < 10:
                ana[i_field] = ""
            else:
                ana[i_field] = clean_string_content(raw_ins)

        for kp_field in ["key_points_zh", "key_points_en"]:
            if ana.get(kp_field) and isinstance(ana[kp_field], list):
                new_kp = []
                for kp in ana[kp_field]:
                    ckp = clean_string_content(kp)
                    if ckp and not any(k in ckp for k in TEMPLATE_INSIGHT_KEYWORDS) and "加速推进关键技术攻坚与工程落地" not in ckp:
                        new_kp.append(ckp)
                ana[kp_field] = new_kp

        for elem_field in ["elements_zh", "elements_en"]:
            if ana.get(elem_field) and isinstance(ana[elem_field], dict):
                for k, v in list(ana[elem_field].items()):
                    if isinstance(v, str):
                        cv = clean_string_content(v)
                        if "加速推进关键技术攻坚与工程落地" in cv:
                            cv = ""
                        ana[elem_field][k] = cv

    return item

def clean_data_structure(data):
    if isinstance(data, dict):
        if "title" in data or "id" in data or "url" in data:
            data = clean_item_deep(data)
        for k, v in list(data.items()):
            if isinstance(v, (dict, list)):
                data[k] = clean_data_structure(v)
            elif isinstance(v, str):
                if k in ["summary_zh", "briefing_zh", "digest_zh", "content_snippet", "briefing_en", "digest_en"]:
                    data[k] = clean_string_content(v)
                elif k in ["insight_zh", "takeaway_zh"]:
                    if any(bad in v for bad in TEMPLATE_INSIGHT_KEYWORDS):
                        data[k] = ""
                    else:
                        data[k] = clean_string_content(v)
                elif "加速推进关键技术攻坚与工程落地" in v:
                    data[k] = clean_string_content(v)
    elif isinstance(data, list):
        data = [clean_data_structure(x) for x in data]
    return data

def process_file(filepath):
    if not os.path.exists(filepath):
        print(f"文件不存在跳过: {filepath}")
        return
    print(f"正在深度递归清洗: {filepath} ...")
    with open(filepath, "r", encoding="utf-8") as f:
        data = json.load(f)
    cleaned = clean_data_structure(data)
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(cleaned, f, ensure_ascii=False, indent=2)
    print(f"✓ 清洗完成: {filepath}")

if __name__ == "__main__":
    targets = [
        os.path.join(DATA_DIR, "master_archive.json"),
        os.path.join(DATA_DIR, "archive_news.json"),
        os.path.join(PUBLIC_DATA_DIR, "archive_news.json"),
        os.path.join(DATA_DIR, "latest_news.json"),
        os.path.join(PUBLIC_DATA_DIR, "latest_news.json"),
    ]
    for t in targets:
        process_file(t)

    # 重新生成 daily briefing 和 index.html SEO 快照
    sys.path.insert(0, ROOT_DIR)
    from main import generate_daily_briefing, inject_seo_static_content, generate_sitemap
    with open(os.path.join(DATA_DIR, "latest_news.json"), "r", encoding="utf-8") as f:
        latest_data = json.load(f)
    items = latest_data.get("items", [])
    print(f"正在根据清洗后的 {len(items)} 条数据重新生成每日简报与 SEO 静态快照...")
    inject_seo_static_content(items)
    generate_daily_briefing(items)
    generate_sitemap()
    print("✨ 全部清洗与静态页面重建完成！")
