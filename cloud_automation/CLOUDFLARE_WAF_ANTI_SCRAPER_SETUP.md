# 🛡️ Cloudflare 边缘反爬虫与 AI 智能体验真放行配置指南

针对域名：`ainewsradar.xyz`（当前已接入 Cloudflare 解析 `mariah.ns.cloudflare.com` / `graham.ns.cloudflare.com`）。

本方案基于 **Cloudflare 反向 DNS（rDNS）与 ASN 密码级验真**，彻底实现：
1. **只放行真正的正规 AI 爬虫**（ChatGPT / Google / Claude / 豆包 / DeepSeek 真实蜘蛛畅通无阻，获得优先索引与引用）。
2. **斩杀一切假冒 AI 的恶意脚本**（哪怕爬虫把 User-Agent 伪造成 `GPTBot` 或 `Googlebot`，没有官方反查 IP 直接 403 阻断）。
3. **保护深度知识文本**（阻止普通数据中心机房脚本一键拖走 `/llms-full.txt` 批量洗稿）。

---

## 🚀 方式一：在 Cloudflare 控制台直接配置 WAF 规则（最简单，2 分钟搞定，无需写代码）

登录 [Cloudflare 控制台](https://dash.cloudflare.com/)，选择域名 `ainewsradar.xyz`。

### 规则 1：开启 AI 语料爬虫阻断（一键防御）
1. 左侧菜单栏 -> **安全性 (Security)** -> **Bot (Bot 流量)**。
2. 找到 **“拦截 AI 爬虫和抓取工具 (Block AI Scrapers and Crawlers)”** 开关。
3. **点击开启**。
   > *作用*：Cloudflare 会自动拦截未给网站带来流量收益、仅纯粹批量提取数据的脱裤爬虫（如 CCBot 等），但不会误伤 ChatGPT Search、Googlebot 等正向引流爬虫。

---

### 规则 2：斩杀伪造 AI User-Agent 的黑产爬虫（关键防线）
1. 左侧菜单栏 -> **安全性 (Security)** -> **WAF** -> **自定义规则 (Custom Rules)**。
2. 点击 **创建规则 (Create Rule)**：
   - **规则名称 (Rule Name)**：`Block Spoofed AI Crawlers (Anti-Fake Bots)`
   - 点击右侧 **“编辑表达式 (Edit expression)”**，直接粘贴下方表达式：

```text
(http.user_agent contains "GPTBot" or http.user_agent contains "ChatGPT" or http.user_agent contains "ClaudeBot" or http.user_agent contains "Perplexity" or http.user_agent contains "Bytespider" or http.user_agent contains "Googlebot") and not cf.botManagement.verified_bot
```

   - **操作 (Action)**：选择 **“阻止 (Block)”**
3. 点击底部 **部署 (Deploy)**。

> 💡 **原理揭秘**：只要客户端声称自己是 ChatGPT/Google/Claude/豆包，但 IP 没有通过官方反向 DNS 解析验真（`cf.botManagement.verified_bot eq false`），瞬间判定为同行或第三方冒牌爬虫，直接在 Cloudflare 边缘层予以 403 斩杀！

---

### 规则 3：官方真 AI 爬虫与大模型搜索无条件白名单放行
1. 在 **WAF** -> **自定义规则 (Custom Rules)** -> 点击 **创建规则**：
   - **规则名称**：`Allow Verified AI Bots & Search Engines`
   - **编辑表达式**：
```text
cf.botManagement.verified_bot
```
   - **操作 (Action)**：选择 **“绕过 (Skip)”** -> 勾选所有安全功能（WAF、速率限制、Bot 质询全跳过，给官方真 AI 极速响应）。
2. 点击底部 **部署**。

---

### 规则 4：保护全量深度情报档案不被自动化批量提取
1. 在 **WAF** -> **自定义规则** -> 点击 **创建规则**：
   - **规则名称**：`Protect Full LLMs Archive From Scraping`
   - **编辑表达式**：
```text
(http.request.uri.path eq "/llms-full.txt" or http.request.uri.path eq "/zh/llms-full.txt") and not cf.botManagement.verified_bot and (http.user_agent contains "python" or http.user_agent contains "curl" or http.user_agent contains "scrapy" or http.user_agent contains "requests" or http.user_agent contains "Go-http-client" or http.user_agent contains "Wget")
```
   - **操作 (Action)**：选择 **“阻止 (Block)”** 或 **“托管质询 (Managed Challenge)”**。
2. 点击底部 **部署**。

---

## 🛠️ 方式二：使用 Cloudflare Worker 边缘网关脚本（代码级完整把控）

如果你希望将逻辑固化在代码中，可以直接部署本仓库内置的边缘网关：
- 代码文件：`cloud_automation/cloudflare_anti_scraper_edge.js`
- 具备自动化 rDNS 验真、假冒爬虫斩杀、全量情报保护与高优先级响应头注入能力。
