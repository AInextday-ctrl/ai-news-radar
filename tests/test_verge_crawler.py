import json
import unittest
from crawlers.verge_crawler import crawl_verge, is_verge_url, _is_verge_noise, _clean_verge_title
from article_extractor import ArticleExtractor


class TestVergeCrawler(unittest.TestCase):
    def test_is_verge_url(self):
        self.assertTrue(is_verge_url("https://www.theverge.com/tech/1036111/satya-nadella-says-hes-agi-pilled-now"))
        self.assertTrue(is_verge_url("https://theverge.com/report/1035465/nvidia-says-it-will-not-reinstate-jensen-huang-as-ceo?view_token=abc"))
        self.assertFalse(is_verge_url("https://www.wsj.com/business/test"))
        self.assertFalse(is_verge_url("https://www.reuters.com/tech/test"))
        self.assertFalse(is_verge_url("https://fortune.com/2026/11/16/test"))

    def test_noise_and_entity_cleaning(self):
        self.assertTrue(_is_verge_noise("Posts from this topic will be added to your daily email digest and your homepage feed."))
        self.assertTrue(_is_verge_noise("Follow topics and authors from this story to see more like this."))
        self.assertFalse(_is_verge_noise("Microsoft confirmed the Exchange Online outage originated from a configuration change in Switzerland."))
        self.assertEqual(
            _clean_verge_title("The OpenAI board member says we still can&#8217;t trust him | The Verge"),
            "The OpenAI board member says we still can’t trust him"
        )

    def test_crawl_verge_next_data_and_routing(self):
        next_payload = {
            "props": {
                "pageProps": {
                    "hydration": {
                        "responses": [
                            {
                                "data": {
                                    "node": {
                                        "title": "Inside Microsoft&#8217;s giant Outlook outage",
                                        "authors": [{"name": "Tom Warren"}],
                                        "publishedAt": "2026-11-17T17:00:00+00:00",
                                        "featuredImage": {
                                            "thumbnails": {
                                                "horizontal": {"url": "https://platform.theverge.com/sample_outlook.jpg"}
                                            }
                                        },
                                        "blocks": [
                                            {"__typename": "CoreParagraphBlockType", "paragraphContents": [{"html": "At 9AM last Thursday, everything seemed normal across Microsoft’s cloud fleet."}]},
                                            {"__typename": "CoreParagraphBlockType", "paragraphContents": [{"html": "Posts from this topic will be added to your daily email digest and your homepage feed."}]},
                                            {"__typename": "CoreHeadingBlockType", "contents": [{"html": "How the outage unfolded"}]},
                                            {"__typename": "CoreParagraphBlockType", "paragraphContents": [{"html": "It all started in Switzerland, according to internal incident logs reviewed by The Verge."}]},
                                            {"__typename": "CoreParagraphBlockType", "paragraphContents": [{"html": "Engineers scrambled to recover Exchange servers after the network boot sequence failed."}]},
                                            {"__typename": "CoreEmbedBlockType", "url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ"}
                                        ]
                                    }
                                }
                            }
                        ]
                    }
                }
            }
        }
        sample_html = f"""
        <!DOCTYPE html>
        <html>
        <head><title>Inside Microsoft's giant Outlook outage | The Verge</title></head>
        <body>
            <script id="__NEXT_DATA__" type="application/json">{json.dumps(next_payload)}</script>
        </body>
        </html>
        """
        url = "https://www.theverge.com/tech/1035364/sample-story?view_token=xyz"
        res = ArticleExtractor.extract_article(url, html_text=sample_html)
        self.assertEqual(res["status"], "success")
        self.assertEqual(res["title"], "Inside Microsoft’s giant Outlook outage")
        self.assertEqual(res["author"], "Tom Warren")
        self.assertEqual(res["cover_image"], "https://platform.theverge.com/sample_outlook.jpg")
        self.assertEqual(res["image_url"], "https://platform.theverge.com/sample_outlook.jpg")
        self.assertEqual(res["paras_count"], 3)  # UI digest prompt filtered out
        self.assertEqual(res["subheadings"], ["How the outage unfolded"])
        self.assertEqual(res["article_content"], res["full_text"])
        self.assertEqual(res["article_content_en"], res["full_text"])
        self.assertTrue(res["has_video"])
        self.assertEqual(res["video_url"], "https://www.youtube.com/embed/dQw4w9WgXcQ")
        self.assertTrue(res["is_substantive"])
        self.assertFalse(res["is_paywalled"])


if __name__ == "__main__":
    unittest.main()
