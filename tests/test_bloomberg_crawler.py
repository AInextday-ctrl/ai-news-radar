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

    def test_crawl_bloomberg_gta6_story(self):
        """Verifies GTA VI Bloomberg scoop crawls with authentic headline, author, photo, and paragraphs."""
        url = "https://www.bloomberg.com/news/articles/2026-11-19/-grand-theft-auto-vi-debut-spurs-livestream-influencer-marathons"
        res = crawl_bloomberg(url)
        self.assertEqual(res["status"], "success")
        self.assertEqual(res["author"], "Cecilia D'Anastasio")
        self.assertIn("bloomberg_gta6_vicecity.jpg", res.get("cover_image", ""))
        self.assertTrue(res["is_substantive"])
        self.assertFalse(res.get("is_paywalled", False))
        self.assertGreaterEqual(len(res["paragraphs"]), 5)
        self.assertTrue(res["paragraphs"][0].startswith("The launch Thursday of Grand Theft Auto VI"))
        self.assertIn("Joe Raedle", res.get("image_caption", ""))

    def test_generic_bloomberg_title_and_contamination_guards(self):
        """Verifies generic Bloomberg section titles, Reuters wire contamination, paywall noise, and bad images are rejected."""
        from crawlers.bloomberg_crawler import (
            _is_generic_bloomberg_title,
            _has_reuters_contamination,
            _is_invalid_bloomberg_image,
            _upgrade_image_url,
            _clean_paragraph,
        )
        from crawlers.content_filters import has_paywall_or_truncation_noise

        self.assertTrue(_is_generic_bloomberg_title("Bloomberg Asia"))
        self.assertTrue(_is_generic_bloomberg_title("Bloomberg Canada"))
        self.assertTrue(_is_generic_bloomberg_title("Rates & Bonds"))
        self.assertTrue(_is_generic_bloomberg_title("https://www.bloomberg.com/sitemaps/news/latest.xml"))
        self.assertFalse(_is_generic_bloomberg_title("HP Gives Profit Forecast Signaling Better Handle on Memory Costs"))

        self.assertTrue(_has_reuters_contamination(["Nov 23 (Reuters) - CrowdStrike said on Monday it would buy Zscaler."]))
        self.assertFalse(_has_reuters_contamination(["HP gave a profit forecast for the current year that will exceed estimates."]))

        self.assertTrue(has_paywall_or_truncation_noise(["You have reached your maximum number of saved items."]))
        self.assertEqual(_clean_paragraph("Nov 23 (Reuters) - CrowdStrike said on Monday it would buy Zscaler."), "")

        self.assertTrue(_is_invalid_bloomberg_image("https://s.yimg.com/eo/images/347aaaafea52bb4acdd656237d94a6818bd79750218634d4294e992da3c3e373.png"))
        self.assertTrue(_is_invalid_bloomberg_image("https://cdn.zonebourse.com/static/web-assets/images/services/charts/chart3.png"))
        self.assertTrue(_is_invalid_bloomberg_image("https://images.unsplash.com/photo-1518770660439-4636190af475?q=80&w=1200"))
        self.assertTrue(_is_invalid_bloomberg_image("https://g.ibtimes.co.uk/img/home/men.png"))
        self.assertFalse(_is_invalid_bloomberg_image("https://ainewsradar.xyz/images/bloomberg_hp.jpg"))

        upgraded = _upgrade_image_url("https://cassette.sphdigital.com.sg/image/businesstimes/abc?t=og&f=webp&w=240")
        self.assertIn("w=1200", upgraded)
        self.assertIn("f=jpg", upgraded)

    def test_bloomberg_hp_syndication_and_image(self):
        """Verifies the previously failing HP Bloomberg article resolves full text and localized image."""
        url = "https://www.bloomberg.com/news/articles/2026-11-24/hp-gives-profit-forecast-signaling-better-handle-on-memory-costs"
        res = crawl_bloomberg(url)
        self.assertEqual(res["status"], "success")
        self.assertIn("HP Gives Profit Forecast", res["title"])
        self.assertTrue(res["is_substantive"])
        self.assertFalse(res.get("is_paywalled", False))
        self.assertGreaterEqual(len(res["paragraphs"]), 5)
        self.assertTrue(str(res.get("cover_image") or "").startswith("https://ainewsradar.xyz/images/bloomberg_"))


if __name__ == '__main__':
    unittest.main()
