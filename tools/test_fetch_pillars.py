# -*- coding: utf-8 -*-
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_pillars():
    print("============================================================")
    print("🔍 [CRAWLER AUDIT] 正在逐项检测 AI News Radar 全网各抓取机制")
    print("============================================================")
    
    results = {}

    # 1. Hacker News
    t0 = time.time()
    try:
        from fetcher import fetch_hacker_news
        items = fetch_hacker_news(max_items=3)
        dt = time.time() - t0
        results['Hacker News API'] = {'status': 'PASS', 'count': len(items), 'time': f"{dt:.2f}s", 'sample': items[0].get('title', '') if items else 'None'}
    except Exception as e:
        results['Hacker News API'] = {'status': 'FAIL', 'error': str(e)}

    # 2. Product Hunt
    t0 = time.time()
    try:
        from fetcher import fetch_product_hunt_tools
        items = fetch_product_hunt_tools(max_items=3)
        dt = time.time() - t0
        results['Product Hunt RSS'] = {'status': 'PASS', 'count': len(items), 'time': f"{dt:.2f}s", 'sample': items[0].get('title', '') if items else 'None'}
    except Exception as e:
        results['Product Hunt RSS'] = {'status': 'FAIL', 'error': str(e)}

    # 3. GitHub Applied Tools
    t0 = time.time()
    try:
        from fetcher import fetch_github_applied_tools
        items = fetch_github_applied_tools()
        dt = time.time() - t0
        results['GitHub Applied Tools'] = {'status': 'PASS', 'count': len(items), 'time': f"{dt:.2f}s", 'sample': items[0].get('title', '') if items else 'None'}
    except Exception as e:
        results['GitHub Applied Tools'] = {'status': 'FAIL', 'error': str(e)}

    # 4. HuggingFace Spaces
    t0 = time.time()
    try:
        from fetcher import fetch_hf_spaces
        items = fetch_hf_spaces(max_items=3)
        dt = time.time() - t0
        results['HuggingFace Spaces'] = {'status': 'PASS', 'count': len(items), 'time': f"{dt:.2f}s", 'sample': items[0].get('title', '') if items else 'None'}
    except Exception as e:
        results['HuggingFace Spaces'] = {'status': 'FAIL', 'error': str(e)}

    # 5. YouTube Videos
    t0 = time.time()
    try:
        from fetcher import fetch_youtube_videos
        items = fetch_youtube_videos(max_per_channel=1)
        dt = time.time() - t0
        results['YouTube Videos RSS'] = {'status': 'PASS', 'count': len(items), 'time': f"{dt:.2f}s", 'sample': items[0].get('title', '') if items else 'None'}
    except Exception as e:
        results['YouTube Videos RSS'] = {'status': 'FAIL', 'error': str(e)}

    # 6. TikTok Trending Videos
    t0 = time.time()
    try:
        from fetcher import fetch_tiktok_trending_videos
        items = fetch_tiktok_trending_videos()
        dt = time.time() - t0
        results['TikTok Trending Videos'] = {'status': 'PASS', 'count': len(items), 'time': f"{dt:.2f}s", 'sample': items[0].get('title', '') if items else 'None'}
    except Exception as e:
        results['TikTok Trending Videos'] = {'status': 'FAIL', 'error': str(e)}

    # 7. GitHub Prompts
    t0 = time.time()
    try:
        from fetcher import fetch_daily_github_prompts
        items = fetch_daily_github_prompts(max_items=3)
        dt = time.time() - t0
        results['GitHub Daily Prompts'] = {'status': 'PASS', 'count': len(items), 'time': f"{dt:.2f}s", 'sample': items[0].get('title_zh', '') if items else 'None'}
    except Exception as e:
        results['GitHub Daily Prompts'] = {'status': 'FAIL', 'error': str(e)}

    # 8. LMSYS Chatbot Arena
    t0 = time.time()
    try:
        from fetcher import get_chatbot_arena_top5
        items = get_chatbot_arena_top5()
        dt = time.time() - t0
        results['LMSYS Chatbot Arena'] = {'status': 'PASS', 'count': len(items), 'time': f"{dt:.2f}s", 'sample': items[0].get('model', '') if items else 'None'}
    except Exception as e:
        results['LMSYS Chatbot Arena'] = {'status': 'FAIL', 'error': str(e)}

    # 9. ArXiv AI Papers
    t0 = time.time()
    try:
        from fetcher import get_arxiv_curated_papers
        items = get_arxiv_curated_papers()
        dt = time.time() - t0
        results['ArXiv AI Papers'] = {'status': 'PASS', 'count': len(items), 'time': f"{dt:.2f}s", 'sample': items[0].get('title', '') if items else 'None'}
    except Exception as e:
        results['ArXiv AI Papers'] = {'status': 'FAIL', 'error': str(e)}

    # 10. Twitter / X Leaders & Viral Posts
    t0 = time.time()
    try:
        from fetcher import fetch_live_trending_x_posts
        items = fetch_live_trending_x_posts(max_items=3)
        dt = time.time() - t0
        results['X / Twitter Live Trending'] = {'status': 'PASS', 'count': len(items), 'time': f"{dt:.2f}s", 'sample': items[0].get('title', '')[:50] if items else 'None'}
    except Exception as e:
        results['X / Twitter Live Trending'] = {'status': 'FAIL', 'error': str(e)}

    t0 = time.time()
    try:
        from fetcher import fetch_x_leader_posts
        items = fetch_x_leader_posts(max_items=3)
        dt = time.time() - t0
        results['X / Twitter Leader Matrix'] = {'status': 'PASS', 'count': len(items), 'time': f"{dt:.2f}s", 'sample': items[0].get('title', '')[:50] if items else 'None'}
    except Exception as e:
        results['X / Twitter Leader Matrix'] = {'status': 'FAIL', 'error': str(e)}

    print("\n--- 抓取机制测试结果清单 ---")
    for name, r in results.items():
        if r['status'] == 'PASS':
            print(f"✅ {name:30s} | {r['status']} | 耗时: {r['time']:>6s} | 条数: {r['count']:2d} | 样例: {r['sample']}")
        else:
            print(f"❌ {name:30s} | {r['status']} | 错误: {r.get('error')}")

if __name__ == '__main__':
    test_pillars()
