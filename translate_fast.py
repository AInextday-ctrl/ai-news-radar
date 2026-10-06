import os
import json
import re
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from processor import free_translate_zh

def is_valid_chinese_content(text: str) -> bool:
    """Check if content has meaningful Chinese text, excluding boilerplate tags."""
    if not text:
        return False
    clean = re.sub(r'【.*?】|\[.*?\]', '', str(text)).strip()
    zh_chars = len(re.findall(r'[\u4e00-\u9fa5]', clean))
    if zh_chars < 15:
        return False
    # 汉字占比要求：至少占有效字符的 20%
    return (zh_chars / max(len(clean), 1)) >= 0.20


def translate_single_item(it: dict) -> bool:
    content = it.get('article_content') or it.get('original_content')
    if not content or len(str(content).strip()) < 30:
        return False
        
    existing_zh = it.get('article_content_zh') or ''
    # 如果已经有真正合格的中文长文实录，跳过
    if is_valid_chinese_content(existing_zh):
        return False

    paras = [p.strip() for p in re.split(r'\n+', str(content)) if p.strip()]
    if len(paras) > 20:
        paras = paras[:20]
        
    zh_paras = []
    for p in paras:
        p_clean = re.sub(r'【.*?】', '', p).strip()
        # 若该段已有较多汉字
        if len(re.findall(r'[\u4e00-\u9fa5]', p_clean)) > len(p_clean) * 0.4:
            zh_paras.append(p_clean)
            continue
            
        t = free_translate_zh(p_clean[:300])
        # 清除翻译结果中任何可能残留的机械标签
        t_clean = re.sub(r'【.*?】', '', t).strip()
        if t_clean and len(re.findall(r'[\u4e00-\u9fa5]', t_clean)) > 5:
            zh_paras.append(t_clean)
            
    final_zh = '\n\n'.join(zh_paras)
    if is_valid_chinese_content(final_zh):
        it['article_content_zh'] = final_zh
        return True
    else:
        # 若无法成功翻译成合格中文，直接置空，绝不留英文或伪中文脏数据危害前台！
        it['article_content_zh'] = None
        return True


def ensure_articles_translated(items: list, max_workers: int = 10) -> int:
    """Fast concurrent translation of items needing article_content_zh."""
    if not items:
        return 0
    
    # 筛选需要翻译或重洗伪中文的条目
    to_translate = []
    for it in items:
        content = it.get('article_content') or it.get('original_content')
        existing_zh = it.get('article_content_zh') or ''
        if bool(content) and len(str(content).strip()) > 30 and not is_valid_chinese_content(existing_zh):
            to_translate.append(it)
            
    if not to_translate:
        return 0
        
    count = 0
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(translate_single_item, it): it for it in to_translate}
        for future in as_completed(futures):
            try:
                if future.result():
                    count += 1
            except Exception as e:
                pass
                
    return count


def sync_all_json_files():
    """Batch translate and sync across all data files."""
    files_to_sync = [
        'data/latest_news.json',
        'public/data/latest_news.json',
        'data/archive_news.json',
        'public/data/archive_news.json',
        'data/master_archive.json'
    ]
    
    total_translated = 0
    for filepath in files_to_sync:
        if not os.path.exists(filepath):
            continue
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            items = []
            if isinstance(data, dict):
                items = data.get('items', [])
                for cat_items in (data.get('grouped', {}) or {}).values():
                    if isinstance(cat_items, list):
                        items.extend(cat_items)
                for k in ['news', 'celebrity', 'tools', 'videos', 'prompts']:
                    if k in data and isinstance(data[k], list):
                        items.extend(data[k])
            elif isinstance(data, list):
                items = data
                
            c = ensure_articles_translated(items, max_workers=10)
            total_translated += c
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            print(f"✅ {filepath}: 成功治理/全真翻译 {c} 条新闻实录", flush=True)
        except Exception as e:
            print(f"⚠️ 同步 {filepath} 异常: {e}", flush=True)
            
    print(f"🎉 全部数据文件治理完成，累计处理: {total_translated} 条。", flush=True)


if __name__ == '__main__':
    sync_all_json_files()
