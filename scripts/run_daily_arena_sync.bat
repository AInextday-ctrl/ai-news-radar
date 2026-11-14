@echo off
chcp 65001 >nul
cd /d "%~dp0\.."
echo [LMSYS Arena] 正在执行每日天梯榜自动抓取...
python scripts\update_arena_leaderboard.py
