"""
Test script to independently verify each public data source.
"""

import sys

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

from fetcher import (

    fetch_hacker_news,
    fetch_reddit,
    fetch_hf_trending,
    fetch_github_trending,
    fetch_youtube_channels
)

def test_all():
    print("🧪 开始单独测试每个数据源的连通性...\n")

    print("[1/5] 测试 Hacker News API...")
    hn = fetch_hacker_news()
    print(f"  -> 获取成功: {len(hn)} 条\n")

    print("[2/5] 测试 Reddit (LocalLLaMA & Singularity)...")
    rd_llm = fetch_reddit("reddit_localllama")
    print(f"  -> LocalLLaMA: {len(rd_llm)} 条")
    rd_sing = fetch_reddit("reddit_singularity")
    print(f"  -> Singularity: {len(rd_sing)} 条\n")

    print("[3/5] 测试 Hugging Face Trending...")
    hf = fetch_hf_trending()
    print(f"  -> 获取成功: {len(hf)} 条\n")

    print("[4/5] 测试 GitHub Trending AI...")
    gh = fetch_github_trending()
    print(f"  -> 获取成功: {len(gh)} 条\n")

    print("[5/5] 测试 YouTube AI 频道 RSS...")
    yt = fetch_youtube_channels()
    print(f"  -> 获取成功: {len(yt)} 条\n")

    total = len(hn) + len(rd_llm) + len(rd_sing) + len(hf) + len(gh) + len(yt)
    print(f"✅ 测试完成！所有源合计单次可抓取: {total} 条最新资讯。")

if __name__ == "__main__":
    test_all()
