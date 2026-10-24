from __future__ import annotations

import os
import sys
import json
import re

# Ensure workspace root is in sys.path
WORKSPACE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if WORKSPACE_DIR not in sys.path:
    sys.path.insert(0, WORKSPACE_DIR)

from processor import has_chinglish_seams


def run_quality_gate_assertions(payload: dict) -> bool:
    """Run 7 hard assertions against the latest news payload."""
    grouped = payload.get("grouped", {})

    print("\n" + "=" * 60)
    print("🛡️  [CI Quality Gate] 自动化数据质量门禁硬性审计")
    print("=" * 60)

    # 断言 1（零 Chinglish 散装机翻）
    chinglish_hits = []
    for cat_name, items in grouped.items():
        if not isinstance(items, list):
            continue
        for it in items:
            for field in ("title_zh", "summary_zh", "app_hook", "overview_zh"):
                val = str(it.get(field) or "")
                if val and has_chinglish_seams(val):
                    chinglish_hits.append((cat_name, it.get("id"), field, val[:60]))
    
    assert len(chinglish_hits) == 0, f"断言 1 失败：检测到 {len(chinglish_hits)} 处 Chinglish 机翻拼接缝痕迹: {chinglish_hits[:3]}"
    print("✅ 断言 1 通过: 零 Chinglish 散装机翻 (0 / 全量字段)")

    # 断言 2（零 +525 ★ 机械常数）
    tools = grouped.get("tools", [])
    flat_525_hits = []
    gh_tools = [t for t in tools if t.get("tool_origin") == "github"]
    weekly_stars_values = []
    for t in gh_tools:
        wk = int(t.get("weekly_stars") or 0)
        badge = str(t.get("growth_badge_zh") or "")
        if wk == 525 or "+525" in badge:
            flat_525_hits.append((t.get("id"), t.get("app_name"), wk, badge))
        if wk > 0:
            weekly_stars_values.append(wk)

    assert len(flat_525_hits) == 0, f"断言 2 失败：检测到 {len(flat_525_hits)} 处固定 +525 ★ 假数据: {flat_525_hits}"
    
    if len(gh_tools) >= 5:
        dispersion = len(set(weekly_stars_values)) / float(len(gh_tools))
        assert dispersion >= 0.70, f"断言 2 失败：周增星离散度不足 {dispersion:.1%} (< 70%)"
    print(f"✅ 断言 2 通过: 零 +525 ★ 机械常数 (GitHub 工具周增星离散度 {len(set(weekly_stars_values))}/{len(gh_tools)})")

    # 断言 3（零伪造 GitHub 提示词空壳）
    prompts = grouped.get("prompts", [])
    fake_prompts = []
    for p in prompts:
        pid = str(p.get("id") or "")
        p_zh = str(p.get("prompt_content_zh") or "")
        if pid.startswith("prompt_gh_") or ("{{核心任务目标}}" in p_zh):
            fake_prompts.append((pid, p.get("title_zh") or p.get("title")))
    assert len(fake_prompts) == 0, f"断言 3 失败：检测到 {len(fake_prompts)} 条伪造 GitHub 提示词空壳: {fake_prompts}"
    print(f"✅ 断言 3 通过: 零伪造 GitHub 提示词空壳 (共 {len(prompts)} 条完整实战提示词)")

    # 断言 4（零非 AI 视频与套壳前缀）
    videos = grouped.get("videos", [])
    bad_videos = []
    for v in videos:
        v_title = str(v.get("title_zh") or v.get("title") or "").lower()
        if any(bad in v_title for bad in ["(not ai)", "[not ai]", "not ai", "node won"]):
            bad_videos.append((v.get("id"), v_title))
        if "最新 ai 前沿解析：" in v_title or "最新 ai 前沿解析:" in v_title:
            bad_videos.append((v.get("id"), v_title))
    assert len(bad_videos) == 0, f"断言 4 失败：检测到 {len(bad_videos)} 个非 AI 视频或套壳假标题: {bad_videos}"
    print(f"✅ 断言 4 通过: 零非 AI 视频与套壳前缀 (共 {len(videos)} 个优质视频)")

    # 断言 5（零低熵/币圈垃圾推文）
    from main import is_meaningful_tweet
    celebrities = grouped.get("celebrity", [])
    viral_tickers = payload.get("viral_ticker_tweets", [])
    spam_tweets = []
    for tw in (celebrities + viral_tickers):
        if not is_meaningful_tweet(tw):
            spam_tweets.append((tw.get("id"), tw.get("author"), str(tw.get("content_zh") or tw.get("content_snippet"))[:40]))
    assert len(spam_tweets) == 0, f"断言 5 失败：检测到 {len(spam_tweets)} 条无实质价值或垃圾推文: {spam_tweets}"
    print(f"✅ 断言 5 通过: 零低熵/币圈垃圾推文 (大V发言 {len(celebrities)} 条，走马灯 {len(viral_tickers)} 条)")

    # 断言 6（零万金油水词摘要）
    news = grouped.get("news", [])
    filler_news = []
    filler_phrases = [
        "相关动态引发全球产业界广泛讨论与技术跟踪",
        "该动态引发了产业界与前沿开发者的广泛讨论与技术跟踪",
        "该事件反映了当前技术演进与落地实践中的关键考量",
        "聚焦该事件的最新进展",
        "全面的最新新闻报道"
    ]
    for n in news:
        s_zh = str(n.get("summary_zh") or "")
        if any(f in s_zh for f in filler_phrases):
            filler_news.append((n.get("id"), n.get("title_zh"), s_zh[:50]))
    assert len(filler_news) == 0, f"断言 6 失败：检测到 {len(filler_news)} 条含万金油废话的摘要: {filler_news}"
    print(f"✅ 断言 6 通过: 零万金油水词摘要 (共 {len(news)} 条新闻全部为纯正增量事实)")

    # 断言 7（核心模块非空水位线保障）
    min_watermarks = {
        "news": 15,
        "celebrity": 15,
        "tools": 12,
        "videos": 3,
        "prompts": 8
    }
    watermark_fails = []
    for cat_k, min_cnt in min_watermarks.items():
        actual_cnt = len(grouped.get(cat_k, []))
        if actual_cnt < min_cnt:
            watermark_fails.append(f"{cat_k}: 实际 {actual_cnt} < 最小水位线 {min_cnt}")
    assert len(watermark_fails) == 0, f"断言 7 失败：部分核心模块数据量过低: {watermark_fails}"
    print(f"✅ 断言 7 通过: 核心模块非空水位线全量达标 ({', '.join(f'{k}={len(grouped.get(k, []))}' for k in min_watermarks)})")

    # 断言 8（严格中英文隔离与零跨语言泄漏）
    import glob
    all_en_html = [f for f in glob.glob(os.path.join(WORKSPACE_DIR, "public", "**", "*.html"), recursive=True)
                   if not f.replace(os.sep, "/").startswith(os.path.join(WORKSPACE_DIR, "public", "zh").replace(os.sep, "/"))]
    en_leak_files = []
    for en_f in all_en_html:
        with open(en_f, "r", encoding="utf-8") as ef:
            c = ef.read()
        zh_chars = re.findall(r'[\u4e00-\u9fff]', c)
        if zh_chars:
            en_leak_files.append((os.path.relpath(en_f, WORKSPACE_DIR), len(zh_chars)))
    assert len(en_leak_files) == 0, f"断言 8 失败：检测到 {len(en_leak_files)} 个英文页面存在中文字符残留: {en_leak_files}"

    # 校验所有 _en 字段绝不含中文字符
    en_field_leaks = []
    for cat_name, items in grouped.items():
        if not isinstance(items, list):
            continue
        for it in items:
            for field in ("title_en", "summary_en", "author_en", "author_role_en", "best_for_en"):
                val = str(it.get(field) or "")
                if val and re.search(r'[\u4e00-\u9fff]', val):
                    en_field_leaks.append((cat_name, it.get("id"), field, val[:40]))
    assert len(en_field_leaks) == 0, f"断言 8 失败：检测到 {len(en_field_leaks)} 处英文数据字段包含中文字符: {en_field_leaks[:3]}"
    print(f"✅ 断言 8 通过: 严格中英文语言纯度全量达标 (全网 {len(all_en_html)} 个英文页面及所有 _en 字段零中文)")

    # 断言 9（零 Git 冲突与脏文本污染）
    conflict_pattern = re.compile(r'^(<{7}\s|={7}$|>{7}\s)', re.MULTILINE)
    conflict_files = []
    
    target_exts = {".html", ".js", ".css", ".json"}
    for root, dirs, files in os.walk(os.path.join(WORKSPACE_DIR, "public")):
        for fname in files:
            ext = os.path.splitext(fname)[1].lower()
            if ext in target_exts:
                fpath = os.path.join(root, fname)
                try:
                    with open(fpath, "r", encoding="utf-8", errors="ignore") as f_in:
                        fc = f_in.read()
                    if conflict_pattern.search(fc) or ("<<<<<<< HEAD" in fc) or ("=======" in fc and ">>>>>>> " in fc):
                        conflict_files.append(os.path.relpath(fpath, WORKSPACE_DIR))
                except Exception:
                    pass

    data_dir = os.path.join(WORKSPACE_DIR, "data")
    if os.path.exists(data_dir):
        for fname in os.listdir(data_dir):
            if fname.endswith(".json"):
                fpath = os.path.join(data_dir, fname)
                try:
                    with open(fpath, "r", encoding="utf-8", errors="ignore") as f_in:
                        fc = f_in.read()
                    if conflict_pattern.search(fc) or ("<<<<<<< HEAD" in fc) or ("=======" in fc and ">>>>>>> " in fc):
                        conflict_files.append(os.path.relpath(fpath, WORKSPACE_DIR))
                except Exception:
                    pass

    assert len(conflict_files) == 0, f"断言 9 失败：检测到 {len(conflict_files)} 个文件含有 Git 冲突标记: {conflict_files}"
    print(f"✅ 断言 9 通过: 零 Git 冲突与脏文本污染 (全站 public 与 data 文件零冲突标记)")

    print("=" * 60)
    print("🏆 【质量门禁 100% 审计通过】全站数据满足零垃圾、高价值上线标准！")
    print("=" * 60 + "\n")
    return True


if __name__ == "__main__":
    latest_file = os.path.join(WORKSPACE_DIR, "public", "data", "latest_news.json")
    if not os.path.exists(latest_file):
        latest_file = os.path.join(WORKSPACE_DIR, "data", "latest_news.json")
    
    with open(latest_file, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    success = run_quality_gate_assertions(data)
    sys.exit(0 if success else 1)
