import json
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

files = [
    'data/latest_news.json',
    'public/data/latest_news.json',
    'data/archive_news.json',
    'public/data/archive_news.json',
    'data/master_archive.json',
    'public/daily/2026-09-23.html',
    'public/index.html'
]

bad_words = [
    '全面的最新新闻报道',
    '谷歌新闻聚合来源',
    'Google新闻汇总',
    '来自世界各地的来源汇总',
    '加速推进关键技术攻坚与工程落地',
    '正在加速布局以构筑关键护城河',
    '经受住效率与成本的双重检验'
]

total_found = 0
for fpath in files:
    try:
        with open(fpath, 'r', encoding='utf-8') as f:
            content = f.read()
        for bw in bad_words:
            cnt = content.count(bw)
            if cnt > 0:
                print(f'❌ {fpath} 仍包含: "{bw}" ({cnt} 次)')
                total_found += cnt
    except Exception as e:
        print(f"读取 {fpath} 失败: {e}")

if total_found == 0:
    print('✅ 验证通过！全部 7 个核心产物中 0 个脏词/模版废话残留！')
else:
    print(f'⚠️ 共发现 {total_found} 处残留！')
