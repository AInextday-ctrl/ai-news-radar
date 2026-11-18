import os
import unittest
from crawlers.fortune_crawler import crawl_fortune, is_fortune_url
from article_extractor import ArticleExtractor


class TestFortuneCrawler(unittest.TestCase):
    def test_is_fortune_url(self):
        self.assertTrue(is_fortune_url("https://fortune.com/2026/11/16/ai-startup-numa-45-million-car-dealerships-paperwork/"))
        self.assertTrue(is_fortune_url("https://fortune.com/article/123/"))
        self.assertTrue(is_fortune_url("https://fortune.net/story/"))
        self.assertFalse(is_fortune_url("https://www.reuters.com/technology/ai-report/"))
        self.assertFalse(is_fortune_url("https://www.bloomberg.com/news/articles/2026-11-16/tech/"))
        self.assertFalse(is_fortune_url("https://techcrunch.com/2026/11/16/ai/"))

    def test_crawl_fortune_from_html(self):
        sample_html = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>AI Startup Raises Millions to Modernize Auto Retail | Fortune</title>
            <meta property="og:title" content="AI Startup Raises Millions to Modernize Auto Retail | Fortune" />
            <meta property="og:image" content="https://fortune.com/img-assets/wp-content/uploads/2026/11/test-founders.png?resize=1200,600" />
            <meta name="author" content="Jane Doe" />
            <script type="application/ld+json">
            {
                "@context": "https://schema.org",
                "@type": "NewsArticle",
                "headline": "AI Startup Raises Millions to Modernize Auto Retail",
                "author": [{"@type": "Person", "name": "Jane Doe"}],
                "datePublished": "2026-11-16T14:00:00-00:00",
                "image": "https://fortune.com/img-assets/wp-content/uploads/2026/11/test-founders.png"
            }
            </script>
        </head>
        <body>
            <div id="related-video">
                <div class="aspect-video"></div>
            </div>
            <script>
            self.__next_f.push([1, "{\\"relatedVideoId\\":\\"SM900242588-900242588-14497\\"}"]);
            </script>
            <article class="article-content">
                <p>Artificial intelligence is transforming traditional car dealerships by automating complex customer workflows.</p>
                <div class="paywall">
                    <p>The startup connects directly to dealership dealer management software to handle appointments and trade-ins.</p>
                    <h2>Expansion into new territory</h2>
                    <p>Investors led by major venture funds poured substantial capital into the company's expansion plans.</p>
                    <p>With hundreds of dealerships signed up, the platform continues to streamline service lane operations.</p>
                </div>
                <div class="description-parser">
                    <p>© 2026 Fortune Media IP Limited. All Rights Reserved. Use of this site constitutes acceptance of our terms.</p>
                </div>
            </article>
        </body>
        </html>
        """
        res = crawl_fortune("https://fortune.com/2026/11/16/test-story/", html_text=sample_html)
        self.assertEqual(res["status"], "success")
        self.assertEqual(res["title"], "AI Startup Raises Millions to Modernize Auto Retail")
        self.assertEqual(res["author"], "Jane Doe")
        self.assertTrue(res["has_video"])
        self.assertEqual(res["video_id"], "SM900242588-900242588-14497")
        self.assertEqual(res["video_provider"], "stn")
        self.assertIn("embed.sendtonews.com/player3/embedcode.js?SC=", res["video_url"])
        self.assertNotIn("embedcode.3.1.1.php", res["video_url"])
        self.assertEqual(len(res["paragraphs"]), 4)  # Copyright footer excluded
        self.assertEqual(res["article_content"], res["full_text"])
        self.assertEqual(res["article_content_en"], res["full_text"])
        self.assertEqual(res["image_url"], res["cover_image"])
        self.assertTrue(res["is_substantive"])
        self.assertFalse(res["is_paywalled"])
        self.assertEqual(res["subheadings"], ["Expansion into new territory"])
        self.assertIn("test-founders.png", res["original_image_url"])

    def test_crawl_fortune_numa_target(self):
        """Verifies the user's specific target Numa article extracts 100% full text, video and images."""
        sample_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "scratch", "fortune_numa.html")
        if not os.path.exists(sample_path):
            self.skipTest("Sample fortune_numa.html not present on disk")

        with open(sample_path, "r", encoding="utf-8") as f:
            html_text = f.read()

        url = "https://fortune.com/2026/11/16/ai-startup-numa-45-million-car-dealerships-paperwork/"
        res = crawl_fortune(url, html_text=html_text)
        self.assertEqual(res["status"], "success")
        self.assertEqual(res["title"], "AI startup Numa raises $45 million to help car dealerships leave the paperwork behind")
        self.assertEqual(res["author"], "Camila Grigera Naón")
        self.assertEqual(res["paras_count"], 13)
        self.assertTrue(res["is_substantive"])
        self.assertFalse(res["is_paywalled"])
        self.assertTrue(res["has_video"])
        self.assertEqual(res["video_id"], "SM900242588-900242588-14497")
        self.assertIn("numa-founders.png", res["original_image_url"])
        self.assertIn("Finding a ‘massive niche’", res["subheadings"])

    def test_article_extractor_routes_fortune(self):
        """Tests that ArticleExtractor automatically routes fortune.com domains to crawl_fortune."""
        url = "https://fortune.com/2026/11/16/ai-startup-numa-45-million-car-dealerships-paperwork/"
        sample_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "scratch", "fortune_numa.html")
        if not os.path.exists(sample_path):
            self.skipTest("Sample fortune_numa.html not present on disk")

        with open(sample_path, "r", encoding="utf-8") as f:
            html_text = f.read()

        res = ArticleExtractor.extract_article(url, html_text=html_text)
        self.assertEqual(res["status"], "success")
        self.assertEqual(res["author"], "Camila Grigera Naón")
        self.assertEqual(res["paras_count"], 13)
        self.assertTrue(res["has_video"])
        self.assertFalse(res["is_paywalled"])
        self.assertTrue(res["is_substantive"])


if __name__ == "__main__":
    unittest.main()
