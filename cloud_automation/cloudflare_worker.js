/**
 * Cloudflare Worker: 24x7 纯云端免本地自动触发器
 * 
 * 作用：部署在 Cloudflare 全球边缘网络，通过 Cloudflare 免费 Cron Trigger
 * 每 15~20 分钟向 GitHub Actions 发送一次 Webhook 请求，实现 100% 脱离本地电脑的自动抓取与发布。
 * 
 * 成本：$0 / 月（Cloudflare Workers 免费额度每日 100,000 次请求，本任务仅需约 72 次/天）
 */

export default {
  // 1. 定时触发模式（由 Cloudflare Cron Trigger 每 15 或 20 分钟自动调度）
  async scheduled(event, env, ctx) {
    ctx.waitUntil(triggerGitHubSync(env));
  },

  // 2. HTTP 触发模式（访问 Worker 网址即可在手机或浏览器上一键手动触发云端同步）
  async fetch(request, env, ctx) {
    const result = await triggerGitHubSync(env);
    return new Response(JSON.stringify(result, null, 2), {
      status: result.success ? 200 : 500,
      headers: { "Content-Type": "application/json; charset=utf-8" },
    });
  },
};

async function triggerGitHubSync(env) {
  const GITHUB_REPO = env.GITHUB_REPO || "AInextday-ctrl/ai-news-radar";
  const GITHUB_PAT = env.GITHUB_PAT; // 在 Cloudflare Worker 设置中添加的环境变量密钥

  if (!GITHUB_PAT) {
    return {
      success: false,
      message: "缺少 GITHUB_PAT 环境变量，请在 Cloudflare Worker -> Settings -> Variables 中添加您的 GitHub Personal Access Token",
    };
  }

  // 同时支持 repository_dispatch 与 workflow_dispatch
  const url = `https://api.github.com/repos/${GITHUB_REPO}/dispatches`;

  try {
    const res = await fetch(url, {
      method: "POST",
      headers: {
        "Authorization": `Bearer ${GITHUB_PAT}`,
        "Accept": "application/vnd.github.v3+json",
        "User-Agent": "Cloudflare-Worker-AutoSync",
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        event_type: "auto-sync",
        client_payload: {
          source: "cloudflare-worker-cron",
          timestamp: new Date().toISOString(),
        },
      }),
    });

    if (res.status === 204 || res.status === 200) {
      return {
        success: true,
        message: `✅ 已成功向 GitHub Actions 发送云端部署指令 (${GITHUB_REPO})`,
        timestamp: new Date().toISOString(),
      };
    } else {
      const errorText = await res.text();
      return {
        success: false,
        status: res.status,
        error: errorText,
      };
    }
  } catch (err) {
    return {
      success: false,
      error: err.message,
    };
  }
}
