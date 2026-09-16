<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet version="2.0" 
                xmlns:html="http://www.w3.org/TR/REC-html40"
                xmlns:sitemap="http://www.sitemaps.org/schemas/sitemap/0.9"
                xmlns:xhtml="http://www.w3.org/1999/xhtml"
                xmlns:xsl="http://www.w3.org/1999/XSL/Transform">
  <xsl:output method="html" version="1.0" encoding="UTF-8" indent="yes"/>
  <xsl:template match="/">
    <html xmlns="http://www.w3.org/1999/xhtml" lang="zh-CN">
      <head>
        <title>XML Sitemap · AI 资讯雷达 (AI News Radar)</title>
        <meta http-equiv="Content-Type" content="text/html; charset=utf-8" />
        <meta name="viewport" content="width=device-width, initial-scale=1.0" />
        <style type="text/css">
          body {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
            background-color: #0f172a;
            color: #e2e8f0;
            margin: 0;
            padding: 30px 20px;
          }
          .container {
            max-width: 960px;
            margin: 0 auto;
            background: rgba(30, 41, 59, 0.7);
            border: 1px solid rgba(56, 189, 248, 0.2);
            border-radius: 16px;
            padding: 28px;
            box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.5);
            backdrop-filter: blur(12px);
          }
          h1 {
            color: #38bdf8;
            font-size: 22px;
            margin-top: 0;
            margin-bottom: 8px;
            display: flex;
            align-items: center;
            gap: 10px;
          }
          p.intro {
            color: #94a3b8;
            font-size: 13px;
            margin-bottom: 24px;
            line-height: 1.6;
          }
          table {
            width: 100%;
            border-collapse: collapse;
            font-size: 13px;
            margin-top: 10px;
          }
          th {
            background-color: rgba(15, 23, 42, 0.8);
            color: #38bdf8;
            text-align: left;
            padding: 12px 14px;
            font-weight: 600;
            border-bottom: 2px solid rgba(56, 189, 248, 0.3);
          }
          td {
            padding: 12px 14px;
            border-bottom: 1px solid rgba(51, 65, 85, 0.5);
            word-break: break-all;
          }
          tr:hover td {
            background-color: rgba(56, 189, 248, 0.05);
          }
          a {
            color: #38bdf8;
            text-decoration: none;
          }
          a:hover {
            text-decoration: underline;
          }
          .badge {
            display: inline-block;
            padding: 2px 8px;
            border-radius: 9999px;
            font-size: 11px;
            font-family: monospace;
            background: rgba(56, 189, 248, 0.15);
            color: #38bdf8;
            border: 1px solid rgba(56, 189, 248, 0.3);
          }
          .footer {
            margin-top: 24px;
            padding-top: 16px;
            border-top: 1px solid rgba(51, 65, 85, 0.5);
            color: #64748b;
            font-size: 11px;
            display: flex;
            justify-content: space-between;
          }
        </style>
      </head>
      <body>
        <div class="container">
          <h1>
            <span>🗺️</span>
            <span>XML Sitemap · AI 资讯雷达</span>
          </h1>
          <p class="intro">
            此文件是遵循 <a href="https://www.sitemaps.org/" target="_blank">sitemaps.org</a> 标准的官方 XML 站点地图，专供 Googlebot 等搜索引擎抓取索引。本站包含中英双语 hreflang 规范定义，共收录 <xsl:value-of select="count(sitemap:urlset/sitemap:url)"/> 个 URL。
          </p>
          <table>
            <thead>
              <tr>
                <th>#</th>
                <th>URL 网址</th>
                <th>多语言版本 (Hreflang)</th>
                <th>最后更新 (Lastmod)</th>
                <th>更新频次</th>
                <th>权重 (Priority)</th>
              </tr>
            </thead>
            <tbody>
              <xsl:for-each select="sitemap:urlset/sitemap:url">
                <tr>
                  <td><xsl:value-of select="position()"/></td>
                  <td>
                    <a href="{sitemap:loc}" target="_blank">
                      <xsl:value-of select="sitemap:loc"/>
                    </a>
                  </td>
                  <td>
                    <xsl:for-each select="xhtml:link">
                      <span class="badge" style="margin-right: 4px; margin-bottom: 2px;"><xsl:value-of select="@hreflang"/></span>
                    </xsl:for-each>
                  </td>
                  <td><xsl:value-of select="sitemap:lastmod"/></td>
                  <td><xsl:value-of select="sitemap:changefreq"/></td>
                  <td>
                    <span class="badge"><xsl:value-of select="sitemap:priority"/></span>
                  </td>
                </tr>
              </xsl:for-each>
            </tbody>
          </table>
          <div class="footer">
            <span>AI News Radar · https://ainewsradar.xyz</span>
            <span>Generated according to Google Sitemap &amp; Hreflang Standards</span>
          </div>
        </div>
      </body>
    </html>
  </xsl:template>
</xsl:stylesheet>
