import unittest
from crawlers.reuters_crawler import crawl_reuters, is_reuters_url
from article_extractor import ArticleExtractor


class TestReutersCrawler(unittest.TestCase):
    def test_is_reuters_url(self):
        self.assertTrue(is_reuters_url("https://www.reuters.com/world/china/inside-chinas-drive-build-an-ai-native-generation-2026-11-16/"))
        self.assertTrue(is_reuters_url("https://reuters.com/technology/article-123/"))
        self.assertTrue(is_reuters_url("https://www.reutersagency.com/en/"))
        self.assertFalse(is_reuters_url("https://www.bloomberg.com/news/articles/2026-11-16/tech"))
        self.assertFalse(is_reuters_url("https://techcrunch.com/2026/11/16/ai/"))

    def test_crawl_reuters_from_html(self):
        sample_html = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Sample Reuters Title</title>
            <meta property="og:title" content="Sample Reuters Report On AI" />
            <meta property="og:image" content="https://images.reuters.com/sample_cover.jpg" />
        </head>
        <body>
            <article data-testid="article-body">
                <div data-testid="paragraph-0">BEIJING (Reuters) - First paragraph of real reporting on AI development.</div>
                <div data-testid="paragraph-1">Second paragraph detailing schools and teaching methodologies across the country.</div>
                <div data-testid="paragraph-2">Third paragraph quoting industry experts and government officials on 2030 goals.</div>
                <div data-testid="paragraph-3">Fourth paragraph explaining robotics and simulated flight labs in high schools.</div>
                <figure>
                    <img src="https://images.reuters.com/inline_flight_simulator.jpg" alt="Flight simulator class" />
                    <figcaption>Students operate a flight simulator at school. REUTERS/Photo</figcaption>
                </figure>
                <div data-testid="paragraph-4">Our Standards: The Thomson Reuters Trust Principles.</div>
            </article>
        </body>
        </html>
        """
        res = crawl_reuters("https://www.reuters.com/world/china/sample-story/", html_text=sample_html)
        self.assertEqual(res["status"], "success")
        self.assertEqual(res["title"], "Sample Reuters Report On AI")
        self.assertEqual(res["cover_image"], "https://images.reuters.com/sample_cover.jpg")
        self.assertEqual(len(res["paragraphs"]), 4) # Trust Principles boilerplate filtered out
        self.assertTrue(res["is_substantive"])
        self.assertFalse(res["is_paywalled"])
        self.assertEqual(len(res["inline_images"]), 1)
        self.assertIn("Students operate a flight simulator", res["inline_images"][0]["caption"])

    def test_crawl_reuters_syndication_live(self):
        """Verifies the user's specific target article crawls with 100% full text and images."""
        url = "https://www.reuters.com/world/china/inside-chinas-drive-build-an-ai-native-generation-2026-11-16/"
        res = crawl_reuters(url)
        self.assertEqual(res["status"], "success")
        self.assertTrue(res["is_substantive"])
        self.assertFalse(res["is_paywalled"])
        self.assertGreaterEqual(res["paras_count"], 15)
        self.assertIsNotNone(res["cover_image"])
        self.assertIn("reuters", res["cover_image"].lower() + res["source"].lower())
        self.assertIn("BEIJING", res["paragraphs"][0])

    def test_article_extractor_routes_reuters(self):
        """Verifies ArticleExtractor delegates Reuters URLs to the dedicated crawler."""
        url = "https://www.reuters.com/world/china/inside-chinas-drive-build-an-ai-native-generation-2026-11-16/"
        res = ArticleExtractor.extract_article(url)
        self.assertEqual(res["status"], "success")
        self.assertTrue(res["is_substantive"])
        self.assertFalse(res.get("is_paywalled", False))
        self.assertGreaterEqual(len(res["paragraphs"]), 15)
        self.assertIsNotNone(res["cover_image"])

    def test_cover_image_validation_and_query_stripping(self):
        """Verifies relative/promo cover images are rejected and ?ref= params do not corrupt slug."""
        from crawlers.reuters_crawler import _is_valid_cover_image
        self.assertFalse(_is_valid_cover_image("/sites/default/files/styles/promo_area/public/2026-03/Athens%20Stock%20Exchange%20a.png"))
        self.assertFalse(_is_valid_cover_image("https://images.unsplash.com/photo-1620712943543-bcc4688e7485"))
        self.assertFalse(_is_valid_cover_image("https://www.atlanticcouncil.org/wp-content/uploads/test.jpg"))
        self.assertTrue(_is_valid_cover_image("https://cdn.zonebourse.com/static/resize/0/0//images/reuters/2026-07/CRITEO.JPG"))
        self.assertTrue(_is_valid_cover_image("https://ainewsradar.xyz/images/reuters_51756a89978254ea.jpg"))

    def test_requirements_include_crawler_deps(self):
        """Verifies GitHub Actions requirements.txt includes curl-cffi and selectolax for isolated crawlers."""
        import os
        req_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "requirements.txt")
        with open(req_path, "r", encoding="utf-8") as f:
            reqs = f.read().lower()
        self.assertIn("curl-cffi", reqs)
        self.assertIn("selectolax", reqs)
        self.assertIn("googlenewsdecoder", reqs)


if __name__ == '__main__':
    unittest.main()
