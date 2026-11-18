#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import unittest
from crawlers.openai_crawler import is_openai_url, crawl_openai


class TestOpenAICrawler(unittest.TestCase):
    def test_url_detection(self):
        self.assertTrue(is_openai_url("https://openai.com/index/introducing-gpt-6-2-astra-sol/"))
        self.assertTrue(is_openai_url("https://www.openai.com/business/customer-stories/revolut"))
        self.assertFalse(is_openai_url("https://the-decoder.com/openai-launches-gpt-6-2/"))

    def test_contentful_article_stop_at_keep_reading_and_clean_artifacts(self):
        html_doc = """
        <html>
        <head>
          <meta property="og:title" content="Astra for Law leads in legal intelligence | OpenAI" />
          <meta property="og:image" content="https://images.ctfassets.net/kftzwdyauwt9/cover/hero.png" />
          <meta property="article:published_time" content="2026-11-16T10:00:00Z" />
        </head>
        <body>
          <article>
            <h1>Astra for Law leads in legal intelligence</h1>
            <p>Today we are sharing benchmark results from Harvey LAB-AA (opens in a new window) showing major gains on complex contract analysis.</p>
            <h2>First in the Harvey LAB-AA</h2>
            <figure>
              <img src="https://images.ctfassets.net/kftzwdyauwt9/chart1/lab.png" alt="Bar chart comparing Harvey LAB-AA scores." />
            </figure>
            <img src="https://cdn.openai.com/mdx-assets/abc/harvey-quote-logo.png" alt="Harvey logo" />
            <p>Legal teams saw 95 percent fewer material hallucinations per assignment across multi-document review workflows, while cutting total turnaround time on due diligence memos by more than half across pilot partner firms.</p>
            <p>Astra for Law is rolling out today to enterprise legal teams with full citation verification, encrypted workspace isolation, and zero data retention enabled by default for regulated client matters.</p>
            <h2>Author</h2>
            <p>OpenAI Legal Team</p>
            <h2>Keep reading</h2>
            <figure><img src="https://images.ctfassets.net/kftzwdyauwt9/related/lvmh-cover.png" alt="LVMH Media Division partnership — cover" /></figure>
            <p>LVMH Media Division partnership with OpenAI brings generative tooling to editorial workflows.</p>
          </article>
        </body>
        </html>
        """
        res = crawl_openai("https://openai.com/index/astra-law-6-2/", html_text=html_doc, localize_cover=False, use_cache=False)
        self.assertEqual(res["status"], "success")
        self.assertEqual(res["title"], "Astra for Law leads in legal intelligence")
        self.assertEqual(res["author"], "OpenAI")
        self.assertIn("### First in the Harvey LAB-AA", res["paragraphs"])
        # UI suffix stripped
        self.assertNotIn("opens in a new window", res["full_text"])
        # Hard stop at Author / Keep reading prevented related card text & image leak
        self.assertNotIn("LVMH Media Division", res["full_text"])
        self.assertEqual(len(res["inline_images"]), 1)
        self.assertEqual(res["inline_images"][0]["url"], "https://images.ctfassets.net/kftzwdyauwt9/chart1/lab.png")
        self.assertEqual(res["inline_images"][0]["after_para"], 1)

    def test_mdx_rsc_vimeo_videos_and_portrait_aspect(self):
        import json as _json
        flight_lines = "\n".join([
            '10:["$","div",null,{"children":{"videoEmbedUrl":"https://player.vimeo.com/video/1244350136?h=abc","posterImageUrl":"https://cdn.openai.com/mdx-assets/p0.webp","altText":"Introducing GPT-6.2 Astra and Sol"}}]',
            '11:["$","div",null,{"children":{"videoEmbedUrl":"https://player.vimeo.com/video/1245939846?h=def","posterImageUrl":"https://cdn.openai.com/mdx-assets/p1.webp","altText":"Roadster demo"}}]',
            '12:["$","div",null,{"className":"aspect-9/16","children":{"videoEmbedUrl":"https://player.vimeo.com/video/1245920978?h=ghi","posterImageUrl":"https://cdn.openai.com/mdx-assets/p2.webp","altText":"Paper lamp portrait demo"}}]',
            '47:["$","article",null,{"children":[["$","p",null,{"children":"GPT-6.2 Astra sets a new frontier standard for scientific reasoning, engineering, and complex multi-step workflows across industries."}],"$10",["$","h2",null,{"children":"Driving simulation"}],["$","p",null,{"children":"Using computer use, Astra built a complete 3D vehicle scene and animated a roadster along a winding mountain highway."}],"$11",["$","h3",null,{"children":"From CAD to a paper lamp"}],["$","p",null,{"children":"In another workflow, Astra generated CAD geometry and step-by-step assembly instructions for a vertical paper lamp."}],"$12"]}]',
        ])
        rsc_literal = _json.dumps(flight_lines)[1:-1]
        html_doc = f"""
        <html>
        <head>
          <meta property="og:title" content="Introducing GPT-6.2 Astra and Sol" />
          <meta property="og:image" content="https://cdn.openai.com/mdx-assets/hero/cover.png" />
        </head>
        <body>
          <article>
            <h1>Introducing GPT-6.2 Astra and Sol</h1>
            <p>GPT-6.2 Astra sets a new frontier standard for scientific reasoning, engineering, and complex multi-step workflows across industries.</p>
            <h2>Driving simulation</h2>
            <p>Using computer use, Astra built a complete 3D vehicle scene and animated a roadster along a winding mountain highway.</p>
            <h3>From CAD to a paper lamp</h3>
            <p>In another workflow, Astra generated CAD geometry and step-by-step assembly instructions for a vertical paper lamp.</p>
          </article>
          <script>self.__next_f.push([1,"{rsc_literal}"])</script>
        </body>
        </html>
        """
        res = crawl_openai("https://openai.com/index/introducing-gpt-6-2-astra-sol/", html_text=html_doc, localize_cover=False, use_cache=False)
        self.assertEqual(res["status"], "success")
        self.assertEqual(len(res["inline_videos"]), 3)
        self.assertEqual(res["inline_videos"][0]["video_id"], "1244350136")
        self.assertEqual(res["inline_videos"][0]["after_para"], 0)
        self.assertEqual(res["inline_videos"][0]["aspect"], "16x9")
        self.assertEqual(res["inline_videos"][1]["video_id"], "1245939846")
        self.assertEqual(res["inline_videos"][1]["after_para"], 2)
        self.assertEqual(res["inline_videos"][2]["video_id"], "1245920978")
        self.assertEqual(res["inline_videos"][2]["after_para"], 4)
        self.assertEqual(res["inline_videos"][2]["aspect"], "9x16")


if __name__ == "__main__":
    unittest.main()
