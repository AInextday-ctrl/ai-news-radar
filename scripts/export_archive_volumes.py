#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
export_archive_volumes.py
======================================================================
将底层 master_archive.json (9,000+ 条全量历史数据)
按照工业级静态分卷架构 (Volume Chunking)
切片输出至 public/data/archive/{category}/:
  - meta.json: 包含 total_items, total_pages, page_size, volume_size, total_volumes
  - vol_1.json, vol_2.json ... (每卷 96 条纯卡片元数据，涵盖 4 个页面，单文件约 60-90 KB，gzip 后仅 15-20 KB)

让前端在纯静态 CDN 环境下，完美实现真正的【翻到哪一页就加载哪一页】，彻底解锁全量历史！
======================================================================
"""

import os
import json
from datetime import datetime, timezone

WORKSPACE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MASTER_ARCHIVE_FILE = os.path.join(WORKSPACE_DIR, "data", "master_archive.json")
PUBLIC_ARCHIVE_DIR = os.path.join(WORKSPACE_DIR, "public", "data", "archive")

PAGE_SIZE = 24
VOLUME_SIZE = 96  # 每卷 96 条，恰好对应 4 页 (96 / 24 = 4)

STRIP_HEAVY_KEYS = {
    'original_content', 'paragraphs', 'article_content', 'article_content_en',
    'article_content_zh', 'raw_payload', 'raw_content', 'full_raw_text',
    'wechat_audit', 'wechat_article_draft', 'wechat_published_draft',
    'processed_mark', 'processed_status', 'processed_at', 'media_checked'
}

def parse_time_for_sort(it):
    raw = it.get("raw_published_at") or it.get("published_at") or ""
    if not raw:
        return 0
    try:
        return datetime.fromisoformat(str(raw).replace("Z", "+00:00")).timestamp()
    except Exception:
        return 0

def clean_item_for_volume(item, cat):
    cleaned = {k: v for k, v in item.items() if k not in STRIP_HEAVY_KEYS and v is not None}
    
    # 针对各分类精细化剔除大字段
    if cat == 'news':
        # 移除过大的内联多图/视频原始数组，仅保留头图
        if 'inline_images' in cleaned and isinstance(cleaned['inline_images'], list) and len(cleaned['inline_images']) > 1:
            cleaned['inline_images'] = cleaned['inline_images'][:1]
        if 'inline_videos' in cleaned:
            del cleaned['inline_videos']
        # 深度研判保留结构化关键字段，剔除冗长分析原稿
        if 'ai_analysis' in cleaned and isinstance(cleaned['ai_analysis'], dict):
            analysis = cleaned['ai_analysis']
            cleaned['ai_analysis'] = {
                'core_event_zh': analysis.get('core_event_zh'),
                'core_event_en': analysis.get('core_event_en'),
                'root_cause_zh': analysis.get('root_cause_zh'),
                'root_cause_en': analysis.get('root_cause_en'),
                'key_metrics_zh': analysis.get('key_metrics_zh'),
                'key_metrics_en': analysis.get('key_metrics_en'),
                'impact_outlook_zh': analysis.get('impact_outlook_zh'),
                'impact_outlook_en': analysis.get('impact_outlook_en'),
                'strategic_impact_zh': analysis.get('strategic_impact_zh'),
                'strategic_impact_en': analysis.get('strategic_impact_en'),
                'briefing_zh': analysis.get('briefing_zh'),
                'briefing_en': analysis.get('briefing_en'),
            }
            cleaned['ai_analysis'] = {k: v for k, v in cleaned['ai_analysis'].items() if v}
    elif cat in ('celebrity', 'viral_posts'):
        # 剔除重复的推文字段
        fte = cleaned.get('full_text_en') or cleaned.get('title_en') or ''
        if fte:
            for k in ['quote_en', 'summary_en', 'content_snippet']:
                if cleaned.get(k) == fte:
                    del cleaned[k]
        ftz = cleaned.get('full_text_zh') or cleaned.get('title_zh') or ''
        if ftz:
            for k in ['quote_zh', 'summary_zh']:
                if cleaned.get(k) == ftz:
                    del cleaned[k]
    return cleaned

def export_all_archive_volumes():
    if not os.path.exists(MASTER_ARCHIVE_FILE):
        print(f"❌ Master archive file not found: {MASTER_ARCHIVE_FILE}")
        return

    with open(MASTER_ARCHIVE_FILE, "r", encoding="utf-8") as f:
        master_data = json.load(f)

    all_items = master_data.get("items", []) if isinstance(master_data, dict) else master_data
    if not isinstance(all_items, list):
        print("❌ Invalid items list in master_archive.json")
        return

    print(f"🚀 开始全量历史分卷切片导出 (总条数: {len(all_items)})...")

    categories = ['news', 'celebrity', 'tools', 'videos', 'prompts']
    now_iso = datetime.now(timezone.utc).isoformat()

    summary_stats = {}

    for cat in categories:
        cat_dir = os.path.join(PUBLIC_ARCHIVE_DIR, cat)
        os.makedirs(cat_dir, exist_ok=True)

        # 筛选归类
        if cat == 'news':
            cat_items = [it for it in all_items if it.get("category") == 'news' or it.get("category") not in ['celebrity', 'tools', 'videos', 'prompts']]
        else:
            cat_items = [it for it in all_items if it.get("category") == cat]

        # 严格按时间倒序排列 (最新在前)
        cat_items.sort(key=parse_time_for_sort, reverse=True)

        total_items = len(cat_items)
        total_pages = (total_items + PAGE_SIZE - 1) // PAGE_SIZE if total_items > 0 else 0
        total_volumes = (total_items + VOLUME_SIZE - 1) // VOLUME_SIZE if total_items > 0 else 0

        # 写入 meta.json
        meta_data = {
            "category": cat,
            "total_items": total_items,
            "total_pages": total_pages,
            "page_size": PAGE_SIZE,
            "volume_size": VOLUME_SIZE,
            "total_volumes": total_volumes,
            "updated_at": now_iso
        }
        with open(os.path.join(cat_dir, "meta.json"), "w", encoding="utf-8") as f:
            json.dump(meta_data, f, ensure_ascii=False, indent=2)

        # 切片写入分卷 vol_1.json, vol_2.json ...
        for vol_idx in range(total_volumes):
            vol_num = vol_idx + 1
            start_i = vol_idx * VOLUME_SIZE
            end_i = min(start_i + VOLUME_SIZE, total_items)
            vol_raw_slice = cat_items[start_i:end_i]

            vol_cleaned_slice = [clean_item_for_volume(it, cat) for it in vol_raw_slice]

            vol_path = os.path.join(cat_dir, f"vol_{vol_num}.json")
            with open(vol_path, "w", encoding="utf-8") as f:
                json.dump(vol_cleaned_slice, f, ensure_ascii=False, separators=(',', ':'))

        summary_stats[cat] = {
            "total_items": total_items,
            "total_pages": total_pages,
            "total_volumes": total_volumes
        }
        print(f"  ✅ [{cat}] 成功生成: {total_items} 条内容 / {total_pages} 页 / 共 {total_volumes} 卷 (已写入 {cat_dir})")

    print(f"🎉 全量历史分卷切片导出完毕！统计总览: {summary_stats}")
    return summary_stats

if __name__ == "__main__":
    export_all_archive_volumes()
