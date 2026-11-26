# Public Frontend & Static Assets Rules (前端交互、渲染与静态资产守则)

> 本文件为 `public/` 目录作用域规则，与根目录 `AGENTS.md` 协同生效。
> 凡修改 `public/js/*.js`、`public/m/js/*.js`、`public/404.html`、静态 HTML 模板或 CSS/媒体资产时必须严格遵守。

---

## 1. SPA 弹窗导航与三池历史穿透

1. **弹窗优先不跳离上下文**：`#news`、`#celebrity`、`#tools`、`#videos`、`#prompts` 页签卡片点击须优先打开站内分析弹窗（`openAiNewsModal` / `openToolDetailModal`），严禁硬重定向打断分页与滚动位置。
2. **全量历史三池查找**：弹窗查找池必须同时覆盖 `cachedData`、`_volumeCache` 与 `cachedArchiveData`，确保深层历史分卷 0ms 秒开。
3. **按需分卷与 404 救赎**：翻页按需拉取 `vol_{N}.json`（96 条/卷），严禁拉取单体大归档；`public/404.html` 保持路径捕获，将未静态化单篇链接重定向至 `/#news?open={id}`。

---

## 2. SSR / CSR 双轨渲染同构与防伪红线

1. **水合时间戳强校验**：`public/js/app.js` 复用首页静态 SSR DOM 前，必须校验 `ssrUpdated && data.updated_at && ssrUpdated === data.updated_at`；不一致时强制执行 `renderUI()` 重新渲染。
2. **视频时效双轨对齐**：
   - `public/js/app.js` 必须保留 `formatVideoTime` 及历史时间防伪拦截关键词（`year`、`month`、`week`、`年前`、`月前`），严禁给历史视频伪造 `TODAY` / `24h 飙升` 标签。
   - 凡改动卡片渲染规则，须同步检查 `content_publisher.py`（SSR）、`public/js/app.js`（桌面 CSR）与 `public/m/js/mobile.js`（移动 CSR）。
3. **DOM 降级正文提取卫语句**：弹窗降级解析正文时，若目标节点为纯列表（`UL`/`OL`）或内部缺少 `<p>` 段落，严禁渲染为“深度报道原文实录”，防止要点列表冒充正文。
4. **严禁语言泄漏与半截括号**：英文版（`/en/`）及 `_en` 渲染零中文字符；模型适配范围按 `AGENTS.md` §8 使用通用能力梯队，严禁硬编码过时微版本号。

---

## 3. 图片直连、破损自愈与零 Monetag 资产锁

1. **CDN 直连 (AGENTS.md Rule 4.1)**：图片统一走自托管 `/images/...` 或官方直链（如 `i.ytimg.com`），严禁 `wsrv.nl` 代理；缺省仅回退 `/images/og-default.jpg`。
2. **加载失败隐藏父容器**：`<img>` 的 `onerror` 须隐藏整个父链接/媒体容器（`this.closest('a')?.style.display='none'`），绝不残留空白占位框。
3. **零 Monetag 与静态资产完整性**：严禁引入任何 Monetag 脚本、跳转或验证 meta；核心版本化 CSS/JS（如 `/css/style-v735.min.css`、`/js/app-v746.min.js`）必须完整存在且非空（受 `tests/test_data_quality_gate.py` 断言 22 硬校验）。
4. **联盟展示与静态主题同步**：修改 `public/js/monetization.js`、`public/js/page_theme.js` 或商品图时，必须遵循 `.agents/skills/affiliate-ui-and-theming/SKILL.md` 与 `.agents/skills/firebase-deploy-and-cache/SKILL.md`（同步更新 `PHOTO_VER` / `?v=<N>` 缓存破坏参数）。

---

## 4. 变更交付与双端复核

1. 修改 `public/js/*.js` 等前端源文件后，同步刷新压缩/版本化产物（如适用）、重跑静态发布器与双门禁（`python tools/verify_code_integrity.py` + `python tests/test_data_quality_gate.py`）。
2. 通过 `python tools/safe_sync.py` 推送上线后，必须对 `https://ainewsradar.xyz` 与 `https://ai-radar-news.web.app` 真实抓包确认 HTTP 200 及静态资源生效。
