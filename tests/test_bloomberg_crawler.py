import unittest
from crawlers.bloomberg_crawler import (
    crawl_bloomberg,
    is_bloomberg_url,
    extract_bloomberg_slug,
    clean_title_to_slug_title
)
from article_extractor import ArticleExtractor


class TestBloombergCrawler(unittest.TestCase):
    def test_is_bloomberg_url(self):
        self.assertTrue(is_bloomberg_url("https://www.bloomberg.com/news/articles/2026-11-16/us-moves-to-limit-remote-access-to-advanced-ai-chips"))
        self.assertTrue(is_bloomberg_url("https://bloomberg.com/news/articles/2026-11-15/nvidia-sought-taipei-s-help-over-employee-s-chip-smuggling-case"))
        self.assertTrue(is_bloomberg_url("https://www.bloomberg.net/news/article-123"))
        self.assertFalse(is_bloomberg_url("https://www.reuters.com/world/china/article/"))
        self.assertFalse(is_bloomberg_url("https://techcrunch.com/2026/11/16/ai/"))

    def test_extract_bloomberg_slug(self):
        slug1 = extract_bloomberg_slug("https://www.bloomberg.com/news/articles/2026-11-16/us-moves-to-limit-remote-access-to-advanced-ai-chips?ref=rss")
        self.assertEqual(slug1, "us-moves-to-limit-remote-access-to-advanced-ai-chips")
        slug2 = extract_bloomberg_slug("https://www.bloomberg.com/news/features/2026-11-15/anthropic-s-ipo-makes-dario-amodei-the-new-face-of-the-ai-boom")
        self.assertEqual(slug2, "anthropic-s-ipo-makes-dario-amodei-the-new-face-of-the-ai-boom")

    def test_clean_title_to_slug_title(self):
        t1 = clean_title_to_slug_title("us-moves-to-limit-remote-access-to-advanced-ai-chips")
        self.assertIn("US", t1)
        self.assertIn("AI", t1)
        self.assertEqual(t1, "US Moves To Limit Remote Access To Advanced AI Chips")

    def test_crawl_bloomberg_from_html(self):
        sample_html = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>US Moves to Curb Remote Access to Nvidia's Advanced AI Chips - Bloomberg</title>
            <meta property="og:title" content="US Moves to Curb Remote Access to Nvidia's Advanced AI Chips" />
            <meta property="og:image" content="https://assets.bwbx.io/images/users/iqjWHBFdfxIU/sample/v1/1200x800.jpg" />
        </head>
        <body>
            <div class="article-body">
                <p>The US Commerce Department moved on Monday to limit several countries from providing Chinese companies remote access to advanced artificial intelligence chips.</p>
                <p>Under the interim final rule issued by the Bureau of Industry and Security, licenses are now required for Singapore, Malaysia, Thailand, Indonesia, and Brazil.</p>
                <p>The new regulation directly targets data centers and neocloud operators globally that provide high aggregate compute power to Chinese labs.</p>
                <p>Lawmakers on Capitol Hill welcomed the measure as an essential step toward hardening the semiconductor perimeter.</p>
                <p>Bloomberg The Company & Its Products: Terms of Service apply.</p>
            </div>
        </body>
        </html>
        """
        res = crawl_bloomberg(
            "https://www.bloomberg.com/news/articles/2026-11-16/us-moves-to-limit-remote-access-to-advanced-ai-chips",
            html_text=sample_html
        )
        self.assertEqual(res["status"], "success")
        self.assertEqual(res["title"], "US Moves to Curb Remote Access to Nvidia's Advanced AI Chips")
        self.assertTrue(res["is_substantive"])
        self.assertFalse(res["is_paywalled"])
        self.assertGreaterEqual(len(res["paragraphs"]), 4)
        # Check that boilerplate was filtered
        self.assertFalse(any("Terms of Service" in p for p in res["paragraphs"]))

    def test_crawl_bloomberg_target_article(self):
        """Verifies the target article crawls with authentic headline, authors, and 1200x800 bwbx photo."""
        url = "https://www.bloomberg.com/news/articles/2026-11-16/us-moves-to-limit-remote-access-to-advanced-ai-chips"
        res = crawl_bloomberg(url)
        self.assertEqual(res["status"], "success")
        self.assertEqual(res["title"], "US Moves to Curb Remote Access to Nvidia's Advanced AI Chips")
        self.assertEqual(res["author"], "Maggie Eastland and Magan Crane")
        self.assertEqual(res["cover_image"], "https://ainewsradar.xyz/images/bloomberg_73a3b9085b60c810_master.jpg")
        self.assertTrue(res.get("has_video", False))

    def test_resolve_bloomberg_broadcast_media(self):
        """Verifies broadcast media resolver identifies Bloomberg TV video segments."""
        from crawlers.bloomberg_crawler import resolve_bloomberg_broadcast_media
        slug = "us-moves-to-limit-remote-access-to-advanced-ai-chips"
        media = resolve_bloomberg_broadcast_media(slug)
        self.assertIsNotNone(media)
        self.assertTrue(media.get("has_video"))
        self.assertEqual(media.get("anchor"), "Ed Ludlow")
        self.assertIn("bloomberg_73a3b9085b60c810_master.jpg", media.get("cover_image", ""))
        self.assertTrue(res["is_substantive"])
        self.assertFalse(res["is_paywalled"])
        self.assertGreaterEqual(res["paras_count"], 5)
        self.assertIn("Commerce Department", res["paragraphs"][0])

    def test_article_extractor_routes_bloomberg(self):
        """Verifies ArticleExtractor delegates Bloomberg URLs to crawl_bloomberg."""
        url = "https://www.bloomberg.com/news/articles/2026-11-16/us-moves-to-limit-remote-access-to-advanced-ai-chips"
        res = ArticleExtractor.extract_article(url)
        self.assertEqual(res["status"], "success")
        self.assertEqual(res["title"], "US Moves to Curb Remote Access to Nvidia's Advanced AI Chips")
        self.assertEqual(res["author"], "Maggie Eastland and Magan Crane")
        self.assertTrue(res["is_substantive"])
        self.assertFalse(res.get("is_paywalled", False))
        self.assertGreaterEqual(len(res["paragraphs"]), 5)
        self.assertEqual(res["cover_image"], "https://ainewsradar.xyz/images/bloomberg_73a3b9085b60c810_master.jpg")
        self.assertTrue(res.get("has_video", False))

    def test_resolve_bloomberg_broadcast_media(self):
        """Verifies broadcast media resolver identifies Bloomberg TV video segments."""
        from crawlers.bloomberg_crawler import resolve_bloomberg_broadcast_media
        slug = "us-moves-to-limit-remote-access-to-advanced-ai-chips"
        media = resolve_bloomberg_broadcast_media(slug)
        self.assertIsNotNone(media)
        self.assertTrue(media.get("has_video"))
        self.assertEqual(media.get("anchor"), "Ed Ludlow")
        self.assertIn("bloomberg_73a3b9085b60c810_master.jpg", media.get("cover_image", ""))


if __name__ == '__main__':
    unittest.main()
