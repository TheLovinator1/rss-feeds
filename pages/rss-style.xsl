<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform">
  <xsl:output method="html" encoding="UTF-8" indent="yes"/>

  <xsl:template match="/">
    <html>
      <head>
        <title><xsl:value-of select="rss/channel/title"/></title>
        <meta charset="UTF-8"/>
        <meta name="viewport" content="width=device-width, initial-scale=1.0"/>
        <style>
          * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
          }

          body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
            line-height: 1.6;
            color: #333;
            background: #f5f5f5;
            padding: 20px;
          }

          .container {
            max-width: 800px;
            margin: 0 auto;
            background: white;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            overflow: hidden;
          }

          .header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            text-align: center;
          }

          .header h1 {
            font-size: 2em;
            margin-bottom: 10px;
          }

          .header p {
            opacity: 0.9;
            font-size: 1.1em;
          }

          .info-box {
            background: #fff3cd;
            border-left: 4px solid #ffc107;
            padding: 15px;
            margin: 20px;
            border-radius: 4px;
          }

          .info-box strong {
            color: #856404;
          }

          .info-box code {
            background: #fff;
            padding: 2px 6px;
            border-radius: 3px;
            font-family: 'Courier New', monospace;
            font-size: 0.9em;
          }

          .feed-info {
            padding: 20px;
            border-bottom: 1px solid #eee;
          }

          .feed-info p {
            margin: 5px 0;
            color: #666;
          }

          .items {
            padding: 20px;
          }

          .item {
            padding: 20px;
            border-bottom: 1px solid #eee;
            transition: background 0.2s;
          }

          .item:hover {
            background: #f9f9f9;
          }

          .item:last-child {
            border-bottom: none;
          }

          .item h2 {
            font-size: 1.5em;
            margin-bottom: 10px;
          }

          .item h2 a {
            color: #667eea;
            text-decoration: none;
            transition: color 0.2s;
          }

          .item h2 a:hover {
            color: #764ba2;
          }

          .item-meta {
            color: #999;
            font-size: 0.9em;
            margin-bottom: 15px;
          }

          .item-meta span {
            margin-right: 15px;
          }

          .category {
            display: inline-block;
            background: #e3f2fd;
            color: #1976d2;
            padding: 3px 10px;
            border-radius: 12px;
            font-size: 0.85em;
            font-weight: 500;
          }

          .description {
            color: #555;
            line-height: 1.8;
          }

          .description img {
            max-width: 100%;
            height: auto;
            border-radius: 4px;
            margin: 10px 0;
          }

          .description p {
            margin: 10px 0;
          }

          .description a {
            color: #667eea;
            text-decoration: none;
            font-weight: 500;
          }

          .description a:hover {
            text-decoration: underline;
          }

          footer {
            text-align: center;
            padding: 20px;
            color: #999;
            font-size: 0.9em;
          }

          @media (max-width: 600px) {
            body {
              padding: 10px;
            }

            .header {
              padding: 20px;
            }

            .header h1 {
              font-size: 1.5em;
            }

            .item {
              padding: 15px;
            }
          }
        </style>
      </head>
      <body>
        <div class="container">
          <div class="header">
            <h1><xsl:value-of select="rss/channel/title"/></h1>
            <p><xsl:value-of select="rss/channel/description"/></p>
          </div>

          <div class="info-box">
            <strong>📰 This is an RSS Feed</strong>
            <p>Subscribe to this feed in your RSS reader to get automatic updates.</p>
          </div>

          <div class="feed-info">
            <p><strong>Feed URL:</strong> <xsl:value-of select="rss/channel/link"/></p>
            <p><strong>Last Updated:</strong> <xsl:value-of select="rss/channel/lastBuildDate"/></p>
            <p><strong>Total Items:</strong> <xsl:value-of select="count(rss/channel/item)"/></p>
          </div>

          <div class="items">
            <xsl:for-each select="rss/channel/item">
              <div class="item">
                <h2>
                  <a href="{link}" target="_blank">
                    <xsl:value-of select="title"/>
                  </a>
                </h2>

                <div class="item-meta">
                  <span>📅 <xsl:value-of select="pubDate"/></span>
                  <xsl:if test="category">
                    <span class="category">
                      <xsl:value-of select="category"/>
                    </span>
                  </xsl:if>
                </div>

                <div class="description">
                  <xsl:value-of select="description" disable-output-escaping="yes"/>
                </div>
              </div>
            </xsl:for-each>
          </div>

          <footer>
            <p><a href="https://github.com/TheLovinator1/rss-feeds">GitHub Repository</a></p>
          </footer>
        </div>
      </body>
    </html>
  </xsl:template>
</xsl:stylesheet>
