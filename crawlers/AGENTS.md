# Crawlers Directory Rules (信源爬虫隔离架构与固锁契约)

> 本文件为 `crawlers/` 目录作用域规则，与根目录 `AGENTS.md` 协同生效。
> 凡修改、排查或新增任何 `crawlers/*_crawler.py` 或 `crawlers/content_filters.py` 时必须严格遵守。

---

## 1. 全量独立信源通用契约 (Universal Isolated Crawler Contract)

1. **彻底隔离与统一导出**：
   - 每个权威媒体独占 `crawlers/<source>_crawler.py`，严禁在单个爬虫中耦合或污染其他信源逻辑。
   - 所有对外调度函数（`crawl_<source>`、`is_<source>_url`）必须在 `crawlers/__init__.py` 显式导入并加入 `__all__`。
   - 模块头部必须声明 `from __future__ import annotations`，所有类型标注显式从 `typing` 导入（兼容 CI Python 3.12）。
2. **标准返回字段与双轨兼容**：
   - 返回 `dict` 须包含清洗后的 `title`、`author`、`paragraphs`（实质报道段落 ≥ 3 段）、`paras_count`、`cover_image`（本地化 `/images/...` 或官方高清原图，禁止小尺寸头像/库存假图，无图回退 `/images/og-default.jpg`）。
   - 接收 `ArticleExtractor` 等第三方输出时必须双向兼容 `ext.get("cover_image") or ext.get("image_url")`。
3. **强制过滤与缓存防投毒**：
   - 必须接入 `crawlers/content_filters.py` 与段落清洗过滤：零配图注释（Caption）、零摄影署名、零邮件推广尾巴、零评论引导语、零付费墙试读文本。
   - 读取 `data/<source>_cache.json` 持久化缓存时必须校验 `has_paywall_or_truncation_noise`，命中试读或截断即强制废弃重抓。
   - 提取 URL slug 必须先 `re.sub(r'^-+|-+$', '', slug)` 净化，严禁带前导 `-` 拼入搜索引擎查询。
   - 二级电讯穿透候选文章必须执行标题/摘要语义关键词重合度校验（≥ 35%），严禁盲取首条结果。
4. **注册表同步与必跑验证**：
   - 新增或重命名爬虫后，必须同步更新 `crawlers/__init__.py`、`tools/audit_source_crawlers.py`、`tools/fast_index.py`（`SOURCE_REGISTRY`），并依次执行：
     ```bash
     python tools/audit_source_crawlers.py
     python tools/fast_index.py --sync
     python tools/verify_code_integrity.py
     ```

---

## 2. 福布斯信源固锁守则 (Forbes — Contract Frozen)

- **调度入口**：凡 `forbes.com` 统一经 `crawlers/forbes_crawler.py` 的 `crawl_forbes` 与 `is_forbes_url` 调度。
- **纯净标题与真实记者署名**：严禁 `Source: ... (Author/Forbes)` 等聚合前缀泄漏至标题，必须经 `clean_forbes_title` 剥离；记者署名优先从 `/sites/{author_slug}/` 或电讯网络解析，杜绝笼统标记为 `Forbes`。
- **真实配图与零版权锁盒**：官方配图（`imageio.forbes.com`）自动下载托管至 `/images/forbes_{slug}.jpg`，无图仅回退 `og-default.jpg`；落地页须具备 ≥ 3 段实质正文（`paragraphs` / `paragraphs_zh`），严禁出现 `Protected by source publisher copyright or login requirements...` 版权锁盒占位符。

---

## 3. 欧洲科技信源固锁守则 (Tech.eu — Contract Frozen)

- **调度入口**：凡 `tech.eu` 统一经 `crawlers/techeu_crawler.py` 的 `crawl_techeu` 与 `is_techeu_url` 调度。
- **纯净标题与真实记者署名**：严禁 `(John Reynolds/Tech.eu)`、` - Tech.eu` 等聚合后缀泄漏至标题，必须经 `clean_techeu_title` 剥离；记者署名优先从 JSON-LD `NewsArticle`（`author.name`）或标题后缀解析，杜绝笼统标记为 `Tech.eu`。
- **真实配图与零评论杂质**：官方高清配图（`cdn.tech.eu/uploads/`）自动下载托管至 `/images/techeu_{slug}.png/.jpg`，无图仅回退 `og-default.jpg`；正文须经 `clean_techeu_paragraphs` 过滤 `Would you like to write the first comment?` 等评论引导语及邮件订阅杂质，确保 ≥ 3 段实质正文。

---

## 4. 谷歌 DeepMind Institute 信源固锁守则 (DeepMind — Contract Frozen)

- **调度入口**：凡 `institute.deepmind.com` 与 `deepmind.google` 特稿/博文统一经 `crawlers/deepmind_crawler.py` 的 `crawl_deepmind` 与 `is_deepmind_url` 调度。
- **纯净标题与科学家署名**：严禁 Techmeme 等聚合前后缀泄漏，必须经 `clean_deepmind_title` 净化；署名优先从 JSON-LD `Article`（`author.name`、`author.jobTitle`）解析科学家姓名及官方研究职务（如 `Research Scientist at Google DeepMind`），杜绝笼统标记为 `DeepMind`。
- **真实配图与零版权锁盒**：官方高清大图（`lh3.googleusercontent.com`）自动下载托管至 `/images/deepmind_{slug}.jpg`，无图仅回退 `og-default.jpg`；须保留完整特稿正文，严禁版权锁盒占位符。
- **Sitemap 主动发现**：保留 `crawl_deepmind_sitemap` 巡检 `https://institute.deepmind.com/sitemap.xml` 的主动发现链路。

---

## 5. 彭博社信源固锁与电讯穿透守则 (Bloomberg — Contract Frozen)

- **调度入口**：凡 `bloomberg.com` 统一经 `crawlers/bloomberg_crawler.py` 的 `crawl_bloomberg` 与 `is_bloomberg_url` 调度。
- **双轨图片字段兼容**：接收 `ArticleExtractor` 结果时必须兼容 `ext.get("cover_image") or ext.get("image_url")`，严禁因字段名差异静默丢弃合法配图。
- **电讯加权评分与屏蔽金融垃圾爬虫**：
  - 二级电讯检索（Bing News RSS / open syndication）必须屏蔽无图、机翻、截断严重的金融评级爬虫：`marketscreener.com`、`zonebourse.com`、`streetinsider.com`、`investing.com`、`finviz.com` 等。
  - 遍历候选结果时严禁遇到首个 ≥ 3 段文本就盲目提前 `return`，必须执行多候选综合质量加权评分（高清原图 +100、权威电讯伙伴 +30、真实记者署名 +20），优先收录图文俱全报道。
  - 高清大图（1200×800 / 1200×628）经 `localize_bloomberg_image` 下载托管至 `/images/bloomberg_{slug}.jpg`，严禁无关库存假图或泛型头像。
- **零图注与社媒分享杂质**：正文须经 `_clean_paragraph` 熔断剥离前置图注（`... | Bloomberg`）与社媒分享栏（`SHARE/SAVE X Facebook LinkedIn ...`）；优先提取现场撰稿记者真名（如 `Saritha Rai`），杜绝笼统标记为 `Bloomberg News`。
- **头条链路字段透传**：`curator_engine.py` 组装 `data/curated_column_highlights.json` 时必须保留并透传 `cover_image`、`image_url` 与 `author`，严禁丢失导致前台回退品牌卡。
