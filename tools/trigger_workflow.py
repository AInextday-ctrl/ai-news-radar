# -*- coding: utf-8 -*-
"""
GitHub Actions Workflow Dispatch Trigger Tool
用于通过外部 Webhook / 定时服务（如 cron-job.org / Cloudflare Worker / 本地定时任务）
调用 GitHub API 触发 workflow_dispatch，绕过 GitHub Actions schedule 延时机制，实现真正的准点高频更新。
"""
import os
import sys
import json
import urllib.request
import urllib.error

GITHUB_REPO = "AInextday-ctrl/ai-news-radar"
WORKFLOW_FILE = "update_and_deploy.yml"

def trigger_dispatch(token=None, ref="main"):
    token = token or os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_PAT")
    if not token:
        print("❌ Error: GITHUB_TOKEN or GH_PAT environment variable is required.")
        print("💡 Usage: python tools/trigger_workflow.py <YOUR_GITHUB_TOKEN>")
        return False

    url = f"https://api.github.com/repos/{GITHUB_REPO}/actions/workflows/{WORKFLOW_FILE}/dispatches"
    payload = json.dumps({"ref": ref}).encode("utf-8")
    req = urllib.request.Request(url, data=payload, headers={
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github.v3+json",
        "User-Agent": "AI-News-Radar-Dispatcher",
        "Content-Type": "application/json"
    }, method="POST")

    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            if resp.status in [204, 200, 201]:
                print(f"✅ Successfully triggered workflow_dispatch for {GITHUB_REPO} ({WORKFLOW_FILE}) on ref '{ref}'.")
                return True
            else:
                print(f"⚠️ Response status: {resp.status}")
                return False
    except urllib.error.HTTPError as e:
        print(f"❌ HTTP Error {e.code}: {e.read().decode('utf-8', errors='ignore')}")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    t = sys.argv[1] if len(sys.argv) > 1 else None
    trigger_dispatch(t)
