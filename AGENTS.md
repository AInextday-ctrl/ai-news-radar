# AI News Radar - 核心架构与质量工程守则 (Engineering & Quality Gate Rules)

> 本文件为 Antigravity Agent 在本仓库执行任何代码编写、抓取爬虫开发、数据处理或前端维护时的**最高质量准则**。
> 所有开发、自动化流水线与数据生成必须严格遵循以下硬性原则，避免历史偶发缺陷重复出现。

---

## 1. 信源隔离与真品保真原则 (Source Integrity & Anti-Pollution)

1. **零异源通讯社污染**：
   - 严禁将第三方通讯社（如 Reuters）的电讯稿摘要直接拼接到另一家主流媒体（如 Bloomberg）的正文中。
   - 在跨信源兜底事实提取（`fetch_cross_grounding_facts`）中，必须通过正则彻底切除 `By ... (Reuters) -`、`BEIJING (Reuters) -` 等通讯社外电署名前缀。
2. **零悬空截断杂质**：
   - 正文段落末尾严禁出现 `such as ...`、`including ...`、`and other ...` 或无止境的省略号 `...`。
   - 任何提取到的段落必须为标点完整的独立事实表述。
3. **真实原厂配图，拒绝无关联库存图**：
   - 权威财经/技术报道（如联想 AI 服务器财报）严禁被关键词误判打上无关的库存无人机（drone）图片。
   - 优先提取并本地化托管源站真实的官方大图（如 `assets.bwbx.io`、ThinkSystem 算力集群大图）；若无合适图片，优雅降级为文字排版卡片（`feed-card-editorial`），绝不滥用假图。

---

## 2. 单页看板（SPA）交互与导航原则 (SPA Navigation & Zero 404)

1. **弹窗优先，保持用户阅读上下文**：
   - 在全站各分类页签（`#news`, `#celebrity`, `#tools`, `#videos`, `#prompts`）中，用户点击卡片必须**优先呼出站内极速 AI 分析弹窗**（`openAiNewsModal` / `openToolDetailModal`）。
   - 严禁在切换页签时将卡片点击强制硬重定向至未静态化的单篇落地页，避免打断用户的滚动位置与翻页进度。
2. **全量历史穿透，消除弹窗查找盲区**：
   - `openAiNewsModal` 与 `openToolDetailModal` 的数据检索池必须同时包含 `cachedData`、`_volumeCache`（所有已加载历史分卷）和 `cachedArchiveData`。
   - 确保用户翻到第 20 页、第 50 页的历史资讯时，点击卡片依然能 0ms 秒开深度研判与 5W1H 事实，杜绝“找不到数据直接跳 404”。
3. **404 智能救赎兜底**：
   - [public/404.html](file:///e:/AI/Antigravity/AI%20News/public/404.html) 必须常驻路径捕获脚本。当外部直链访问了未预生成的静态落地页时，自动将用户平滑重定向至看板对应的 `/#news?open={id}`，确保访客永不碰壁。

---

## 3. 静态分卷架构与数据轻量化守则 (Static Volume Chunking & Weight Control)

1. **严格坚持分卷按需加载（On-Demand Chunking）**：
   - 历史内容按分类切片为 96 条/卷（`vol_{N}.json`，体积仅 15-20 KB gzip），翻到哪页加载哪卷，严禁回退为单体 6MB 归档大文件拉取。
   - 首页 Page 1 必须使用 `cachedData.grouped[tab]` 秒级直出（0ms 零网络等待）。
2. **公共数据体积红线守门**：
   - `public/data/latest_news.json` 体积必须**严格控制在 850 KB 以内**（CI 断言 14 硬性阻断）。
   - 公共 JSON 中剔除 `article_content_en` 等与 `paragraphs` 重复的冗余大文本，保持轻量高效传输。
3. **服务端静态编译与前端轻量化彻底解耦原则 (Backend Source-of-Truth)**：
   - **严禁数据源倒挂**：服务端静态单篇页面生成脚本（如 `tool_news_publisher.py`、`content_publisher.py`）必须以完整的后端主库（`data/latest_news.json` 与 `master_archive.json`）为第一数据源；严禁将面向浏览器精简后的 `public/data/latest_news.json` 作为静态构建的主输入源。
   - **双轨健壮兜底渲染**：正文排版逻辑必须实施多层回退机制——优先读取完整长文字符串，若字段为空则**必须无缝降级读取 `paragraphs` / `paragraphs_zh` 数组**自动拼接还原全景正文，严禁因单一字段缺失导致有数据却渲染出正文空白的落地页。

---

## 4. 前端图片直连与破损自愈 (Direct CDN & Graceful Fallback)

1. **自托管直连，禁用海外代理抖动**：
   - 站内图片一律通过 Firebase CDN 自身域名（`/images/...`）加载，严禁使用 `wsrv.nl` 等第三方海外反代工具，避免因网络抖动或墙体屏蔽导致缩略图大面积变白框。
2. **图片失败容器彻底隐藏**：
   - 所有 `<img>` 标签的 `onerror` 必须保证在图片加载失败时隐藏整个父容器（`this.closest('a')?.style.display='none'`），严禁留下无内容的发白、空置占位框。

---

## 5. 质量门禁一票否决制 (CI Quality Gate Hard Enforcement)

- 任何功能开发与数据变更必须 100% 通过 `python tests/test_data_quality_gate.py` 的所有断言（目前共 20 项硬性断言），任何断言失败均视为不可发布缺陷，自动化部署将自动拦截并回退。
