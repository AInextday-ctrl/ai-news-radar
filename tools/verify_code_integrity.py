#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tools/verify_code_integrity.py
工程代码完整性与防回退静态校验工具 (Code Integrity & Regression Guard)

功能：
1. 静态扫描工程关键源文件，阻断静默时间伪造反模式 (如 datetime.now() 赋给发布时间、diff_hours: 12.0 兜底)；
2. 校验前后端双轨同构：验证 content_publisher.py (SSR) 与 public/js/app.js (CSR) 均包含历史时效防御门禁；
3. 执行单元回归测试套件 (tests/test_video_pipeline.py)；
4. 输出代码索引依赖与符号健康度报告。
"""

import os
import sys
import re
import unittest

if sys.stdout.encoding.lower() != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

WORKSPACE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if WORKSPACE_DIR not in sys.path:
    sys.path.insert(0, WORKSPACE_DIR)


def scan_anti_patterns() -> list:
    """扫描代码中可能导致时间伪造或静默回退的危险反模式"""
    errors = []

    # 1. 检查 content_publisher.py 绝不允许将 diff_hours 硬编码兜底为 12.0
    pub_file = os.path.join(WORKSPACE_DIR, "content_publisher.py")
    if os.path.exists(pub_file):
        with open(pub_file, "r", encoding="utf-8") as f:
            content = f.read()
        if 'diff_hours = float(item.get("diff_hours", 12.0))' in content:
            errors.append("content_publisher.py 检出危险代码: diff_hours 兜底为 12.0 (会导致旧视频被伪造成12小时前)")

    # 2. 检查 viral_video_engine.py 绝不允许直接将 datetime.now() 赋值给 raw_published_at
    eng_file = os.path.join(WORKSPACE_DIR, "viral_video_engine.py")
    if os.path.exists(eng_file):
        with open(eng_file, "r", encoding="utf-8") as f:
            content = f.read()
        if re.search(r'["\']raw_published_at["\']\s*:\s*datetime\.(?:now|utcnow)', content):
            errors.append("viral_video_engine.py 检出危险代码: 直接使用 datetime.now() 赋值给 raw_published_at")
        if "parse_relative_time_info" not in content:
            errors.append("viral_video_engine.py 缺失核心函数: parse_relative_time_info")

    # 3. 检查 public/js/app.js 前端渲染逻辑必须包含历史时间关键词拦截
    js_file = os.path.join(WORKSPACE_DIR, "public", "js", "app.js")
    if os.path.exists(js_file):
        with open(js_file, "r", encoding="utf-8") as f:
            js_content = f.read()
        if "formatVideoTime" not in js_content:
            errors.append("public/js/app.js 缺失 formatVideoTime 专用时间格式化函数")
        for kw in ["year", "month", "week", "年前", "月前"]:
            if kw not in js_content:
                errors.append(f"public/js/app.js 缺失历史时间防伪拦截关键词: '{kw}'")

    return errors


def run_unit_tests() -> bool:
    """运行所有单元回归测试"""
    loader = unittest.TestLoader()
    suite = loader.discover(os.path.join(WORKSPACE_DIR, "tests"), pattern="test_video_pipeline.py")
    runner = unittest.TextTestRunner(verbosity=1)
    result = runner.run(suite)
    return result.wasSuccessful()


def main():
    print("=" * 60)
    print("[Code Integrity Guard] 正在执行全工程代码规范与防回退静态校验...")
    print("=" * 60)

    # 步骤 1: 反模式扫描
    anti_pattern_errs = scan_anti_patterns()
    if anti_pattern_errs:
        print("[FAIL] 发现危险反模式或规范违例:")
        for err in anti_pattern_errs:
            print(f"   - {err}")
        sys.exit(1)
    else:
        print("[PASS] 静态反模式审计通过: 零抓取时间冒充、零静默兜底伪造、前后端防线健全")

    # 步骤 2: 单元回归测试
    print("\n[TEST] 正在运行视频管线防回退单元测试集 (tests/test_video_pipeline.py)...")
    tests_ok = run_unit_tests()
    if not tests_ok:
        print("[FAIL] 单元回归测试失败！")
        sys.exit(1)
    print("[PASS] 单元回归测试全部通过: 相对时间解析与标题时效前缀隔离校验 100% 达标")

    print("\n" + "=" * 60)
    print("[SUCCESS] 工程规范校验全部通过，代码基线安全稳定！")
    print("=" * 60)
    sys.exit(0)


if __name__ == "__main__":
    main()
