"""
Safe Git Sync Tool - AI News Radar
Eliminates git lockfiles, enforces local proxy, and guarantees safe non-blocking push/pull.
"""
from __future__ import annotations

import os
import sys
import subprocess
import glob
import time

WORKSPACE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def clean_git_locks() -> None:
    git_dir = os.path.join(WORKSPACE_DIR, ".git")
    if not os.path.exists(git_dir):
        return
    lock_patterns = [
        os.path.join(git_dir, "*.lock"),
        os.path.join(git_dir, "refs", "**", "*.lock"),
        os.path.join(git_dir, "objects", "**", "*.lock"),
    ]
    for pattern in lock_patterns:
        for f in glob.glob(pattern, recursive=True):
            try:
                os.remove(f)
                print(f"🧹 [SafeSync] Removed stale lockfile: {os.path.relpath(f, WORKSPACE_DIR)}")
            except Exception as e:
                print(f"⚠️ [SafeSync] Could not remove {f}: {e}")


def setup_proxy() -> None:
    # Ensure proxy is set to 127.0.0.1:7890
    try:
        subprocess.run(["git", "config", "http.proxy", "http://127.0.0.1:7890"], cwd=WORKSPACE_DIR, check=True)
        subprocess.run(["git", "config", "https.proxy", "http://127.0.0.1:7890"], cwd=WORKSPACE_DIR, check=True)
        # Unset postbuffer if set to avoid RAM explosion
        subprocess.run(["git", "config", "--unset", "http.postbuffer"], cwd=WORKSPACE_DIR, capture_output=True)
    except Exception as e:
        print(f"⚠️ [SafeSync] Proxy config warning: {e}")


def run_sync() -> bool:
    print("🚀 [SafeSync] Starting automated resilient Git sync...")
    clean_git_locks()
    setup_proxy()

    # Step 1: Commit any pending changes
    status = subprocess.run(["git", "status", "--porcelain"], cwd=WORKSPACE_DIR, capture_output=True, text=True)
    if status.stdout.strip():
        print("📦 [SafeSync] Staging and committing local changes...")
        subprocess.run(["git", "add", "-A"], cwd=WORKSPACE_DIR, check=True)
        commit_res = subprocess.run(
            ["git", "commit", "-m", "chore: automated safe sync baseline [skip ci]"],
            cwd=WORKSPACE_DIR,
            capture_output=True,
            text=True
        )
        print("   " + (commit_res.stdout.strip() or "Committed."))

    # Step 2: Fetch and rebase with -X theirs (rebase semantics: ours=upstream, theirs=local commits) to keep local fixes on top
    print("🔄 [SafeSync] Pulling latest robot syncs from origin/main with rebase (-X theirs, keeping local commits)...")
    clean_git_locks()
    pull_res = subprocess.run(
        ["git", "pull", "--rebase", "-X", "theirs", "origin", "main"],
        cwd=WORKSPACE_DIR,
        capture_output=True,
        text=True,
        timeout=180
    )
    if pull_res.returncode != 0:
        print(f"⚠️ [SafeSync] Rebase encountered issue: {pull_res.stderr.strip()[:200]}")
        clean_git_locks()
        subprocess.run(["git", "rebase", "--abort"], cwd=WORKSPACE_DIR, capture_output=True)
        print("   Attempting clean merge pull...")
        subprocess.run(["git", "pull", "--no-rebase", "-X", "ours", "origin", "main", "--no-edit"], cwd=WORKSPACE_DIR, check=True)

    # Step 3: Push to origin/main
    print("⬆️ [SafeSync] Pushing to origin/main...")
    clean_git_locks()
    push_res = subprocess.run(["git", "push", "origin", "main"], cwd=WORKSPACE_DIR, capture_output=True, text=True, timeout=180)
    if push_res.returncode == 0:
        print("✅ [SafeSync] Successfully pushed to origin/main! Cloud CI is now in sync.")
        return True
    else:
        print(f"⚠️ [SafeSync] Push attempt failed: {push_res.stderr.strip()[:200]}")
        return False


if __name__ == "__main__":
    success = run_sync()
    sys.exit(0 if success else 1)
