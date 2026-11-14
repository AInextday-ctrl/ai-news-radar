import urllib.request
import json
import os
import sys
import time
import argparse
import subprocess
from datetime import datetime, timezone, timedelta

if sys.stdout.encoding.lower() != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

WORKSPACE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(WORKSPACE_DIR, "data")
PUBLIC_DATA_DIR = os.path.join(WORKSPACE_DIR, "public", "data")
ARENA_CACHE_FILE = os.path.join(DATA_DIR, "chatbot_arena_cache.json")
PUBLIC_ARENA_CACHE_FILE = os.path.join(PUBLIC_DATA_DIR, "chatbot_arena_cache.json")

ORG_MAP = {
    "google": "Google",
    "anthropic": "Anthropic",
    "meta": "Meta",
    "openai": "OpenAI",
    "alibaba": "Alibaba",
    "deepseek": "DeepSeek",
    "xiaomi": "Xiaomi",
    "xai": "xAI",
    "mistral": "Mistral",
    "microsoft": "Microsoft",
    "cohere": "Cohere",
    "01-ai": "01.AI",
    "zhipu": "Zhipu AI",
    "baichuan": "Baichuan",
    "nvidia": "NVIDIA",
    "tencent": "Tencent",
    "moonshot": "Moonshot",
    "thinky": "Thinky",
    "xhtoken": "XHToken",
    "bytedance": "ByteDance",
    "amazon": "Amazon"
}

def sync_arena_leaderboard(trigger_render: bool = True) -> bool:
    """
    从官方权威源实时抓取 Arena 'Best Overall Agents' (综合最佳智能体) 榜单。
    包含胜率得分 (Score %)、评测会话数、归属组织与专属代际技术徽章。
    """
    print("\n" + "=" * 65)
    print("🏆 [LMSYS Arena] 正在同步官方权威源【综合最佳智能体 (Best Overall)】天梯榜...")
    print("=" * 65)

    # 官方 LMSYS Arena 综合最佳智能体榜单 (agent / overall)
    url = "https://datasets-server.huggingface.co/rows?dataset=lmarena-ai%2Fleaderboard-dataset&config=agent&split=latest"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36",
        "Accept": "application/json"
    }
    
    rows = []
    max_retries = 3
    for attempt in range(1, max_retries + 1):
        try:
            import requests
            resp = requests.get(url, headers=headers, timeout=15)
            if resp.status_code == 200:
                payload = resp.json()
                rows = payload.get("rows", [])
                if rows:
                    print(f"  ✓ 成功通过 requests 拉取最新【综合最佳智能体】数据，共 {len(rows)} 款模型参评 (尝试 {attempt}/{max_retries})")
                    break
        except Exception as e_req:
            try:
                req = urllib.request.Request(url, headers=headers)
                with urllib.request.urlopen(req, timeout=15) as r:
                    payload = json.loads(r.read().decode('utf-8'))
                    rows = payload.get("rows", [])
                    if rows:
                        print(f"  ✓ 成功通过 urllib 拉取最新【综合最佳智能体】数据，共 {len(rows)} 款模型参评 (尝试 {attempt}/{max_retries})")
                        break
            except Exception as e_url:
                print(f"  ⚠️ 第 {attempt}/{max_retries} 次抓取异常: req: {e_req} | url: {e_url}")
                if attempt < max_retries:
                    time.sleep(2 * attempt)
    
    models = []
    if rows:
        for idx, item in enumerate(rows[:25]):
            row = item.get("row", {})
            rank = int(row.get("rank") or (idx + 1))
            name = str(row.get("model_name") or "AI Model").strip()
            raw_org = str(row.get("organization") or "").lower().strip()
            org = ORG_MAP.get(raw_org, raw_org.title() or "AI Lab")
            
            # 读取胜率净分 (score) 并格式化为百分比，如 +30.35%
            score = row.get("score")
            if score is not None:
                score_val = float(score)
                elo_str = f"{score_val * 100:+.2f}%"
                rating = round(score_val * 100, 2)
            else:
                rating = float(row.get("rating") or 0.0)
                elo_str = str(int(round(rating)))

            votes = int(row.get("session_count") or row.get("observation_count") or row.get("vote_count") or 0)
            
            # 智能根据排名与模型品牌生成专属中英文徽章
            if rank == 1:
                badge_zh = f"👑 全球综合榜首 · {org} 旗舰智能体基座"
                badge_en = f"👑 #1 Best Overall · {org} Flagship Agent SOTA"
            elif rank == 2:
                badge_zh = f"🔥 全球第二 · {org} 极高阶智能体基座"
                badge_en = f"🔥 #2 Overall · {org} Frontier Agent SOTA"
            elif rank == 3:
                badge_zh = f"🔥 全球前三 · {org} 顶级认知推理智能体"
                badge_en = f"🔥 Top 3 Overall · {org} Frontier Reasoning SOTA"
            elif rank <= 5:
                badge_zh = f"⚡ 全球Top 5 · {org} 顶级Agent认知基座"
                badge_en = f"⚡ Top 5 Overall · {org} Frontier Agent SOTA"
            elif "deepseek" in name.lower() or "qwen" in name.lower():
                badge_zh = f"🌐 顶尖开源基座 · {org} 标杆模型"
                badge_en = f"🌐 Open-Weights SOTA · {org} Flagship"
            elif rank <= 10:
                badge_zh = f"💎 全球Top 10 · {org} 顶尖生产力智能体"
                badge_en = f"💎 Top 10 Overall · {org} Production Agent SOTA"
            else:
                badge_zh = f"🚀 全球前沿 · {org} 高性能智能体"
                badge_en = f"🚀 Frontier SOTA · {org} High-Performance Agent"
            
            # 模型官方落地链接映射
            if "gemini" in name.lower():
                model_url = "https://deepmind.google/technologies/gemini/"
            elif "claude" in name.lower():
                model_url = "https://www.anthropic.com/claude"
            elif "gpt" in name.lower() or "o1" in name.lower() or "o3" in name.lower() or "openai" in org.lower():
                model_url = "https://openai.com/"
            elif "deepseek" in name.lower():
                model_url = "https://www.deepseek.com/"
            elif "qwen" in name.lower():
                model_url = "https://qwenlm.github.io/"
            elif "mimo" in name.lower():
                model_url = "https://mimo.xiaomi.com/"
            elif "kimi" in name.lower() or "moonshot" in name.lower():
                model_url = "https://kimi.moonshot.cn/"
            elif "grok" in name.lower():
                model_url = "https://x.ai/"
            elif "hy" in name.lower():
                model_url = "https://hunyuan.tencent.com/"
            elif "muse" in name.lower() or "llama" in name.lower():
                model_url = "https://ai.meta.com/"
            else:
                model_url = "https://arena.ai/"
            
            models.append({
                "rank": rank,
                "model": name,
                "raw_model": row.get("model_name") or name,
                "elo": elo_str,
                "rating": rating,
                "org": org,
                "badge": badge_zh,
                "badge_en": badge_en,
                "votes": votes,
                "url": model_url,
                "arena_url": "https://arena.ai/"
            })

    if not models:
        print("  ⚠️ 在线解析未获取到新模型，尝试回退检查现有本地缓存...")
        for p in [ARENA_CACHE_FILE, PUBLIC_ARENA_CACHE_FILE]:
            if os.path.exists(p):
                try:
                    with open(p, "r", encoding="utf-8") as f:
                        cdata = json.load(f)
                        if cdata.get("models"):
                            models = cdata["models"]
                            print(f"  ✓ 成功从本地缓存恢复 {len(models)} 款模型数据")
                            break
                except Exception:
                    pass

    if not models:
        print("  ❌ 未能获取到任何可用天梯榜数据！")
        return False

    cache_data = {
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "source": "https://arena.ai/",
        "leaderboard_category": "Best Overall Agents (Agent | Overall)",
        "models": models
    }
    
    # 写入缓存
    for p in [ARENA_CACHE_FILE, PUBLIC_ARENA_CACHE_FILE]:
        os.makedirs(os.path.dirname(p), exist_ok=True)
        with open(p, "w", encoding="utf-8") as f:
            json.dump(cache_data, f, ensure_ascii=False, indent=2)
    print(f"  ✓ 缓存写入完成: {ARENA_CACHE_FILE} (收录 {len(models)} 款模型)")
    
    # 同步写入 latest_news.json
    for ln_path in [
        os.path.join(DATA_DIR, "latest_news.json"),
        os.path.join(PUBLIC_DATA_DIR, "latest_news.json")
    ]:
        if os.path.exists(ln_path):
            try:
                with open(ln_path, "r", encoding="utf-8") as f:
                    d = json.load(f)
                d["chatbot_arena"] = models
                with open(ln_path, "w", encoding="utf-8") as f:
                    json.dump(d, f, ensure_ascii=False, indent=2)
                print(f"  ✓ 已同步更新: {ln_path} 中的 chatbot_arena")
            except Exception as e:
                print(f"  ❌ 写入 {ln_path} 失败: {e}")

    print("\n" + "-" * 50)
    print("📋 当前最新【综合最佳】天梯榜前五名:")
    for m in models[:5]:
        print(f"  #{m['rank']} {m['model']} ({m['org']}) - 得分: {m['elo']} | {m['badge']}")
    print("-" * 50)

    # 触发 content_publisher 重新预渲染静态页面
    if trigger_render:
        try:
            pub_script = os.path.join(WORKSPACE_DIR, "content_publisher.py")
            if os.path.exists(pub_script):
                print("🔄 正在触发静态页面预渲染流水线 (content_publisher.py)...")
                subprocess.run([sys.executable, pub_script], cwd=WORKSPACE_DIR, check=True)
                print("  ✓ 静态页面已刷新并同步最新综合最佳天梯榜！")
        except Exception as e:
            print(f"  ⚠️ 静态预渲染调用异常: {e}")

    return True

def run_daily_scheduler(target_hour: int = 8, target_minute: int = 0):
    """
    常驻守护进程：每天固定时间 (默认每天 08:00) 自动执行抓取与页面更新
    """
    print(f"⏰ [Daily Scheduler] 启动每天自动同步守护进程 (设定时间: 每天 {target_hour:02d}:{target_minute:02d})...")
    # 启动时首先执行一次同步
    sync_arena_leaderboard(trigger_render=True)
    
    while True:
        now = datetime.now()
        target = now.replace(hour=target_hour, minute=target_minute, second=0, microsecond=0)
        if target <= now:
            target += timedelta(days=1)
        wait_seconds = (target - now).total_seconds()
        next_str = target.strftime('%Y-%m-%d %H:%M:%S')
        print(f"\n💤 [Daily Scheduler] 待命中... 下次自动抓取时间为: {next_str} (约 {wait_seconds/3600:.1f} 小时后)")
        try:
            time.sleep(wait_seconds)
            print(f"\n⏰ [Daily Scheduler] 到达预定时间 ({next_str})，正在执行每日天梯榜抓取...")
            sync_arena_leaderboard(trigger_render=True)
        except KeyboardInterrupt:
            print("\n👋 [Daily Scheduler] 用户已手动退出守护进程。")
            break

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="LMSYS Arena 综合最佳天梯榜同步引擎")
    parser.add_argument("--daily", action="store_true", help="以守护进程模式运行，每天自动定时抓取")
    parser.add_argument("--hour", type=int, default=8, help="每日定时执行的小时 (0-23，默认 8 点)")
    parser.add_argument("--minute", type=int, default=0, help="每日定时执行的分钟 (0-59，默认 0 分)")
    parser.add_argument("--no-render", action="store_true", help="不自动触发 content_publisher.py 预渲染")
    args = parser.parse_args()

    if args.daily:
        run_daily_scheduler(target_hour=args.hour, target_minute=args.minute)
    else:
        sync_arena_leaderboard(trigger_render=not args.no_render)
