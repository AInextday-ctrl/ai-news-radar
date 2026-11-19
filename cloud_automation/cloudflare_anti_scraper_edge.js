/**
 * Cloudflare Edge Worker: AI-Verified Intelligent Anti-Scraper Gateway
 * 域名: ainewsradar.xyz
 * 
 * 核心目的：
 * 1. 优先放行正规 AI 搜索与大模型索引（OpenAI, Google, Anthropic, 豆包, DeepSeek）
 * 2. 严厉封杀伪造 AI User-Agent 的第三方恶意爬虫（基于 Cloudflare rDNS 反向 DNS 验真）
 * 3. 保护 /llms-full.txt 与落地页结构化全文不被通用机房脚本批量提取
 */

export default {
  async fetch(request, env, ctx) {
    const url = new URL(request.url);
    const path = url.pathname;
    const ua = (request.headers.get("user-agent") || "").toLowerCase();
    
    // Cloudflare 注入的官方认证 Bot 标记（由反向 DNS rDNS 与 ASN 机构双重验真，伪造无效）
    const isVerifiedBot = Boolean(request.cf && request.cf.botManagement && request.cf.botManagement.verifiedBot);
    
    // 敏感前沿 AI 引擎的常见 User-Agent 标识
    const isClaimingAIBot = (
      ua.includes("gptbot") ||
      ua.includes("oai-searchbot") ||
      ua.includes("chatgpt") ||
      ua.includes("perplexity") ||
      ua.includes("claudebot") ||
      ua.includes("claude-web") ||
      ua.includes("anthropic") ||
      ua.includes("googlebot") ||
      ua.includes("google-extended") ||
      ua.includes("googleother") ||
      ua.includes("bytespider") ||
      ua.includes("bytedance") ||
      ua.includes("doubao") ||
      ua.includes("deepseek") ||
      ua.includes("youbot") ||
      ua.includes("tavily") ||
      ua.includes("exabot")
    );

    // ------------------------------------------------------------------------
    // 规则 1：严厉拦截伪造 AI 爬虫身份的恶意脚本 (Spoofed AI Bots)
    // ------------------------------------------------------------------------
    // 如果 User-Agent 声称自己是 GPTBot / Googlebot / ClaudeBot，但无法通过 Cloudflare 反向 DNS 验真
    if (isClaimingAIBot && !isVerifiedBot) {
      return new Response(JSON.stringify({
        error: "Forbidden: Spoofed AI Crawler Detected",
        message: "Your client claims to be an authorized AI Crawler, but failed Reverse DNS (rDNS) cryptographic verification at Cloudflare edge.",
        client_ip: request.headers.get("cf-connecting-ip") || "unknown",
        code: 403
      }, null, 2), {
        status: 403,
        headers: { "Content-Type": "application/json; charset=utf-8" }
      });
    }

    // ------------------------------------------------------------------------
    // 规则 2：保护全量深度情报档案 (/llms-full.txt & /zh/llms-full.txt)
    // ------------------------------------------------------------------------
    // 官方认证 AI 搜索引擎可以直接获取全文，普通匿名机房爬虫予以拦截，普通浏览器可直接阅读
    if (path === "/llms-full.txt" || path === "/zh/llms-full.txt") {
      const isBrowser = (
        request.headers.get("sec-ch-ua") ||
        (ua.includes("mozilla") && !ua.includes("python") && !ua.includes("curl") && !ua.includes("scrapy") && !ua.includes("requests"))
      );

      // 仅允许官方验证过的 AI 爬虫与常规浏览器访客，拦截匿名机房爬虫脚本
      if (!isVerifiedBot && !isBrowser) {
        return new Response("Access Denied: Full intelligence context is restricted to verified AI search engines and authenticated humans.\nPlease access the concise manifest at /llms.txt.", {
          status: 403,
          headers: { "Content-Type": "text/plain; charset=utf-8" }
        });
      }
    }

    // ------------------------------------------------------------------------
    // 规则 3：透传正常请求至源站 (Firebase Hosting / GitHub Pages)
    // ------------------------------------------------------------------------
    // 对官方认证的 AI 爬虫添加高优先级缓存与特定响应头
    const response = await fetch(request);
    
    if (isVerifiedBot) {
      const newHeaders = new Headers(response.headers);
      newHeaders.set("X-AI-Priority-Ingest", "authorized-verified-bot");
      return new Response(response.body, {
        status: response.status,
        statusText: response.statusText,
        headers: newHeaders
      });
    }

    return response;
  }
};
