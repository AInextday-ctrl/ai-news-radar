import json
import re
from processor import free_translate_zh

def main():
    data = json.load(open('public/data/latest_news.json', encoding='utf-8'))
    items = data.get('items', [])
    translated_count = 0

    for it in items:
        content = it.get('article_content') or it.get('original_content')
        if content and len(content) > 50 and not it.get('article_content_zh'):
            paras = [p.strip() for p in content.split('\n\n') if p.strip()]
            if len(paras) > 15:
                paras = paras[:15]
            zh_paras = []
            for p in paras:
                t = free_translate_zh(p[:260])
                if t:
                    zh_paras.append(t)
            it['article_content_zh'] = '\n\n'.join(zh_paras)
            translated_count += 1
            print(f"Done {it.get('id')}: {len(zh_paras)} paras")

    grouped_news = data.get('grouped', {}).get('news', [])
    item_map = {it.get('id'): it for it in items if it.get('id')}
    for gn in grouped_news:
        gid = gn.get('id')
        if gid in item_map and item_map[gid].get('article_content_zh'):
            gn['article_content_zh'] = item_map[gid]['article_content_zh']

    with open('public/data/latest_news.json', 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"ALL DONE! Translated {translated_count} items.")

if __name__ == '__main__':
    main()
