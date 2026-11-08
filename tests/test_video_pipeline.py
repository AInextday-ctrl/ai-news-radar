from __future__ import annotations

import os
import sys
import unittest
from datetime import datetime, timezone, timedelta

# Ensure project root is in sys.path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from viral_video_engine import parse_relative_time_info, sanitize_video_title_zh


class TestVideoPipeline(unittest.TestCase):
    """
    针对视频时效性解析与防伪造标签的单元回归测试集。
    确保无论后续代码如何重构，历史视频绝不被贴上 TODAY、24h飙升或 5m ago 假时间。
    """

    def test_parse_relative_time_info_historical(self):
        """测试历史视频（月、年、周前）绝不判定为 24h / 48h 新视频"""
        historical_cases = [
            "1 year ago",
            "1 yr ago",
            "2 years ago",
            "Streamed 1 year ago",
            "8 months ago",
            "8 mo ago",
            "3 months ago",
            "2 weeks ago",
            "3 wks ago",
            "5 days ago",
            "1年前",
            "8个月前",
            "3周前",
            "5天前",
        ]
        now = datetime.now(timezone.utc)
        for text in historical_cases:
            iso_str, is_24h, is_48h = parse_relative_time_info(text)
            self.assertFalse(
                is_24h,
                f"历史文本 '{text}' 被错误判定为 24h 内发布 (is_24h=True)"
            )
            self.assertFalse(
                is_48h,
                f"历史文本 '{text}' 被错误判定为 48h 内发布 (is_48h=True)"
            )
            parsed_dt = datetime.fromisoformat(iso_str)
            age_days = (now - parsed_dt).total_seconds() / 86400.0
            self.assertGreaterEqual(
                age_days,
                2.0,
                f"历史文本 '{text}' 解析出的时间差不足 2 天 (age_days={age_days})"
            )

    def test_parse_relative_time_info_recent(self):
        """测试近期真正发布的视频（小时、分钟前）能准确识别时效"""
        recent_cases = [
            ("17 minutes ago", True, True),
            ("35 mins ago", True, True),
            ("2 hours ago", True, True),
            ("14 hrs ago", True, True),
            ("20 hours ago", True, True),
            ("30 hours ago", False, True),  # > 24h, <= 48h
            ("36h ago", False, True),
            ("刚刚", True, True),
            ("15分钟前", True, True),
            ("3小时前", True, True),
        ]
        for text, expected_24h, expected_48h in recent_cases:
            iso_str, is_24h, is_48h = parse_relative_time_info(text)
            self.assertEqual(
                is_24h,
                expected_24h,
                f"文本 '{text}' 期望 24h={expected_24h}，实际={is_24h}"
            )
            self.assertEqual(
                is_48h,
                expected_48h,
                f"文本 '{text}' 期望 48h={expected_48h}，实际={is_48h}"
            )

    def test_sanitize_video_title_zh_prefix_isolation(self):
        """测试中文标题前缀隔离：历史视频严禁打上【48h 极客实测】前缀"""
        title = "How to Build AI Agents with Claude"
        author = "Liam Ottley"

        # 历史长视频 -> 必须是【实战精讲】
        historical_title = sanitize_video_title_zh(title, author, is_viral=False, is_short=False, is_recent=False)
        self.assertNotIn("48h 极客实测", historical_title)
        self.assertNotIn("24h 飙升", historical_title)
        self.assertIn("实战精讲", historical_title)

        # 真正近期视频 -> 允许【48h 极客实测】
        recent_title = sanitize_video_title_zh(title, author, is_viral=False, is_short=False, is_recent=True)
        self.assertIn("48h 极客实测", recent_title)

        # 历史 Shorts -> 必须是【Shorts 精选】而非【Shorts 极客】
        short_historical = sanitize_video_title_zh(title, author, is_viral=False, is_short=True, is_recent=False)
        self.assertIn("Shorts 精选", short_historical)
        self.assertNotIn("Shorts 极客", short_historical)


if __name__ == "__main__":
    unittest.main()
