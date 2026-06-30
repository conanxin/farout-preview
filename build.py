#!/usr/bin/env python3
"""Build Far Out Company P5 Preview Site"""
import os
import re
import html
import shutil
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
SRC = BASE / "content"
OUT = BASE / "preview_site"

def md_to_html(text):
    """Minimal Markdown to HTML using only stdlib. Supports headers, paragraphs,
    lists, bold, italic, code inline/blocks, blockquotes, horizontal rules."""
    text = text.replace('\r\n', '\n')
    lines = text.split('\n')
    out = []
    i = 0
    in_code = False
    code_lines = []
    in_list = False
    list_items = []
    list_ordered = False

    def flush_list():
        nonlocal in_list, list_items, list_ordered
        if in_list and list_items:
            tag = "ol" if list_ordered else "ul"
            out.append(f"<{tag}>")
            for item in list_items:
                out.append(f"<li>{item}</li>")
            out.append(f"</{tag}>")
            list_items = []
            in_list = False
            list_ordered = False

    def inline_fmt(s):
        # code inline
        s = re.sub(r'`([^`]+)`', r'<code>\1</code>', s)
        # bold
        s = re.sub(r'\*\*([^*]+)\*\*', r'<strong>\1</strong>', s)
        s = re.sub(r'__([^_]+)__', r'<strong>\1</strong>', s)
        # italic
        s = re.sub(r'\*([^*]+)\*', r'<em>\1</em>', s)
        s = re.sub(r'_([^_]+)_', r'<em>\1</em>', s)
        return s

    while i < len(lines):
        line = lines[i]
        stripped = line.strip()

        # Code block
        if stripped.startswith('```'):
            if not in_code:
                in_code = True
                code_lines = []
            else:
                in_code = False
                code_body = '\n'.join(code_lines)
                code_body_escaped = html.escape(code_body)
                out.append(f'<pre><code>{code_body_escaped}</code></pre>')
            i += 1
            continue

        if in_code:
            code_lines.append(line)
            i += 1
            continue

        # Horizontal rule
        if re.match(r'^(---|___|\*\*\*)\s*$', stripped):
            flush_list()
            out.append('<hr>')
            i += 1
            continue

        # Headers
        m = re.match(r'^(#{1,6})\s+(.*)$', stripped)
        if m:
            flush_list()
            level = len(m.group(1))
            title = inline_fmt(html.escape(m.group(2)))
            out.append(f'<h{level}>{title}</h{level}>')
            i += 1
            continue

        # Ordered list
        m = re.match(r'^(\d+)\.\s+(.*)$', stripped)
        if m:
            if not in_list or not list_ordered:
                flush_list()
                in_list = True
                list_ordered = True
            list_items.append(inline_fmt(html.escape(m.group(2))))
            i += 1
            continue

        # Unordered list
        m = re.match(r'^[-*+]\s+(.*)$', stripped)
        if m:
            if not in_list or list_ordered:
                flush_list()
                in_list = True
                list_ordered = False
            list_items.append(inline_fmt(html.escape(m.group(1))))
            i += 1
            continue

        # Blockquote
        if stripped.startswith('>'):
            flush_list()
            quote_content = stripped[1:].strip()
            # Multi-line blockquote
            j = i + 1
            while j < len(lines) and lines[j].strip().startswith('>'):
                quote_content += '\n' + lines[j].strip()[1:].strip()
                j += 1
            # Process quote content as mini-md
            quote_html = inline_fmt(html.escape(quote_content))
            quote_html = quote_html.replace('\n', '<br>')
            out.append(f'<blockquote>{quote_html}</blockquote>')
            i = j
            continue

        # Empty line
        if not stripped:
            flush_list()
            i += 1
            continue

        # Paragraph (accumulate until blank line)
        flush_list()
        para_lines = [stripped]
        j = i + 1
        while j < len(lines):
            if lines[j].strip() == '' or lines[j].strip().startswith('#') or lines[j].strip().startswith('-') or lines[j].strip().startswith('*') or re.match(r'^\d+\.', lines[j].strip()) or lines[j].strip().startswith('>') or lines[j].strip().startswith('```'):
                break
            para_lines.append(lines[j].strip())
            j += 1
        para = ' '.join(para_lines)
        para = inline_fmt(html.escape(para))
        out.append(f'<p>{para}</p>')
        i = j

    flush_list()
    return '\n'.join(out)


def read_md(path):
    if not path.exists():
        return ""
    return path.read_text(encoding='utf-8')


def page(title, body, nav_extra="", base_path=""):
    """Wrap body in a full HTML page. base_path is relative prefix for links."""
    css_path = base_path + "css/style.css"
    return f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{html.escape(title)}</title>
<link rel="stylesheet" href="{css_path}">
</head>
<body>
<header>
  <div class="container nav">
    <a href="{base_path}index.html" class="logo">Far Out Research</a>
    <nav>
      <a href="{base_path}index.html">首页</a>
      <a href="{base_path}radical-software/index.html">首篇发布</a>
      <a href="{base_path}knowledge-base/index.html">知识库</a>
    </nav>
  </div>
</header>
<main>
  <div class="container">
    {nav_extra}
    {body}
  </div>
</main>
<footer>
  <div class="container">
    <p>Far Out Research Preview · 非正式归档站 · 仅供远程审阅</p>
  </div>
</footer>
</body>
</html>'''


def build_css():
    css = '''/* Far Out Research Preview Site */
*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

:root {
  --bg: #f7f5f0;
  --fg: #2a2a2a;
  --muted: #6b6b6b;
  --accent: #8b4513;
  --accent-light: #b87333;
  --border: #d4cfc7;
  --card-bg: #ffffff;
  --code-bg: #f0ece4;
  --header-bg: #2a2a2a;
  --header-fg: #f7f5f0;
  --max-width: 760px;
  --nav-max: 900px;
}

body {
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Noto Sans SC", "PingFang SC", "Microsoft YaHei", sans-serif;
  background: var(--bg);
  color: var(--fg);
  line-height: 1.75;
  font-size: 16px;
}

.container {
  max-width: var(--max-width);
  margin: 0 auto;
  padding: 0 20px;
}

header {
  background: var(--header-bg);
  color: var(--header-fg);
  padding: 12px 0;
  position: sticky;
  top: 0;
  z-index: 100;
}

.nav {
  display: flex;
  justify-content: space-between;
  align-items: center;
  max-width: var(--nav-max);
}

.logo {
  font-weight: 700;
  font-size: 1.1rem;
  color: var(--header-fg);
  text-decoration: none;
  letter-spacing: 0.5px;
}

nav a {
  color: var(--header-fg);
  text-decoration: none;
  margin-left: 20px;
  font-size: 0.9rem;
  opacity: 0.85;
  transition: opacity 0.2s;
}

nav a:hover { opacity: 1; text-decoration: underline; }

main { padding: 40px 0 60px; }

h1, h2, h3, h4 {
  font-weight: 700;
  line-height: 1.3;
  margin-bottom: 0.6em;
  margin-top: 1.4em;
}

h1 { font-size: 1.8rem; margin-top: 0; }
h2 { font-size: 1.4rem; border-bottom: 1px solid var(--border); padding-bottom: 0.3em; }
h3 { font-size: 1.15rem; }

p { margin-bottom: 1em; }

a { color: var(--accent); text-decoration: none; }
a:hover { text-decoration: underline; }

ul, ol { margin-bottom: 1em; padding-left: 1.5em; }
li { margin-bottom: 0.3em; }

blockquote {
  border-left: 3px solid var(--accent-light);
  padding-left: 1em;
  margin: 1em 0;
  color: var(--muted);
  font-style: italic;
}

code {
  background: var(--code-bg);
  padding: 2px 5px;
  border-radius: 3px;
  font-family: "SF Mono", Monaco, "Courier New", monospace;
  font-size: 0.9em;
}

pre {
  background: var(--code-bg);
  padding: 12px 16px;
  border-radius: 6px;
  overflow-x: auto;
  margin-bottom: 1em;
}

pre code { background: none; padding: 0; }

hr {
  border: none;
  border-top: 1px solid var(--border);
  margin: 1.5em 0;
}

/* Cards */
.card-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(260px, 1fr));
  gap: 16px;
  margin: 1.5em 0;
}

.card {
  background: var(--card-bg);
  border: 1px solid var(--border);
  border-radius: 8px;
  padding: 16px;
  transition: box-shadow 0.2s, transform 0.2s;
}

.card:hover {
  box-shadow: 0 4px 12px rgba(0,0,0,0.08);
  transform: translateY(-2px);
}

.card h3 {
  font-size: 1rem;
  margin-top: 0;
  margin-bottom: 0.4em;
}

.card p {
  font-size: 0.9rem;
  color: var(--muted);
  margin-bottom: 0;
}

.card a { display: block; }

/* Cover placeholder */
.cover-placeholder {
  background: #e0ddd5;
  border: 2px dashed var(--border);
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--muted);
  font-size: 0.9rem;
  min-height: 180px;
  margin: 1em 0;
}

.cover-img {
  max-width: 100%;
  border-radius: 8px;
  margin: 1em 0;
}

/* Platform links */
.platform-links {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  margin: 1em 0;
}

.platform-links a {
  display: inline-block;
  padding: 6px 14px;
  background: var(--card-bg);
  border: 1px solid var(--border);
  border-radius: 20px;
  font-size: 0.9rem;
}

.platform-links a:hover {
  background: var(--accent);
  color: #fff;
  border-color: var(--accent);
  text-decoration: none;
}

/* Status badges */
.status-list {
  list-style: none;
  padding-left: 0;
}

.status-list li {
  padding: 6px 0;
  border-bottom: 1px solid var(--border);
}

.status-list li::before {
  content: "✓ ";
  color: #2e7d32;
  font-weight: bold;
}

.status-list li.current::before {
  content: "▶ ";
  color: var(--accent);
}

/* Notice */
.notice {
  background: #fff8e1;
  border-left: 3px solid #f9a825;
  padding: 12px 16px;
  margin: 1em 0;
  border-radius: 0 6px 6px 0;
  font-size: 0.9rem;
}

/* Table of contents */
.toc {
  background: var(--card-bg);
  border: 1px solid var(--border);
  border-radius: 8px;
  padding: 16px 20px;
  margin: 1em 0;
}

.toc h3 { margin-top: 0; font-size: 1rem; }

/* Breadcrumb */
.breadcrumb {
  font-size: 0.85rem;
  color: var(--muted);
  margin-bottom: 1em;
}

.breadcrumb a { color: var(--muted); }

/* Article list */
.article-list { list-style: none; padding-left: 0; }
.article-list li {
  padding: 10px 0;
  border-bottom: 1px solid var(--border);
}
.article-list a { font-weight: 500; }
.article-list span { color: var(--muted); font-size: 0.85rem; }

/* Footer */
footer {
  background: var(--header-bg);
  color: var(--header-fg);
  padding: 20px 0;
  text-align: center;
  font-size: 0.85rem;
  opacity: 0.7;
}

/* Mobile */
@media (max-width: 600px) {
  body { font-size: 15px; }
  h1 { font-size: 1.5rem; }
  h2 { font-size: 1.2rem; }
  .nav { flex-direction: column; gap: 8px; }
  nav a { margin: 0 10px; }
  .card-grid { grid-template-columns: 1fr; }
}

/* Summary box */
.summary-box {
  background: var(--card-bg);
  border: 1px solid var(--border);
  border-radius: 8px;
  padding: 16px 20px;
  margin: 1em 0;
}

.summary-box h4 {
  margin-top: 0;
  font-size: 1rem;
  color: var(--accent);
}
'''
    (OUT / "css/style.css").write_text(css, encoding='utf-8')


def build_home():
    body = '''
<h1>Far Out Research Preview</h1>

<div class="notice">
  <strong>当前状态：</strong>这是 preview site，不是正式归档站。用于远程审阅和分享。
</div>

<h2>项目简介</h2>
<p>这是一个基于 <strong>Far Out Company</strong> 的 1960/70 年代反主流文化视觉研究与中文内容生产项目。我们从 Far Out Company 的图像资料出发，挖掘档案背后的故事，并将它们转化为当代中文读者可理解的深度内容。</p>

<h2>首篇发布</h2>
<div class="card">
  <h3>📹 在 Sora 之前，他们想重新发明电视</h3>
  <p><strong>一本 1970 年代的杂志，和 AI 时代仍没回答的问题</strong></p>
  <p>1970 年代初，一群美国艺术家和媒介行动者创办了《Radical Software》杂志。他们不问怎么拍出好视频，而问"谁有权拍、谁有权播"……</p>
  <div class="platform-links">
    <a href="radical-software/index.html">进入首篇发布页</a>
    <a href="radical-software/wechat.html">公众号长文</a>
    <a href="radical-software/x-thread.html">X Thread</a>
    <a href="radical-software/jike.html">即刻版</a>
    <a href="radical-software/xiaohongshu.html">小红书版</a>
  </div>
</div>

<h2>知识库入口</h2>
<div class="card-grid">
  <div class="card">
    <a href="knowledge-base/index.html">
      <h3>📚 知识库总览</h3>
      <p>本地知识库 HTML 预览 · 主题索引 · 数据概况</p>
    </a>
  </div>
  <div class="card">
    <a href="knowledge-base/articles/index.html">
      <h3>📝 文章草稿</h3>
      <p>5 篇长文草稿，涵盖地下报纸、Portable Video、公社期刊等主题</p>
    </a>
  </div>
  <div class="card">
    <a href="knowledge-base/cards/index.html">
      <h3>🎴 知识卡</h3>
      <p>10 篇中文知识卡，精选 Top10 主题速览</p>
    </a>
  </div>
  <div class="card">
    <a href="knowledge-base/prompts/index.html">
      <h3>🎨 Prompt 包</h3>
      <p>20 组精选视觉 Prompt，按主题分组</p>
    </a>
  </div>
</div>

<h2>项目进度</h2>
<ul class="status-list">
  <li>P1 索引抓取完成</li>
  <li>P2 知识库增强完成</li>
  <li>P3 周更监控完成</li>
  <li>P4 内容生产完成</li>
  <li>P4.10 发布交付完成</li>
  <li class="current">P5 线上预览站 — 当前</li>
</ul>

<h2>发布说明</h2>
<ul>
  <li>当前为 <strong>preview site</strong>，仅供远程审阅和分享</li>
  <li>不是正式归档站，内容可能继续迭代</li>
  <li>所有内容基于 Far Out Company 公开图像资料整理</li>
  <li>不包含任何外部下载资源或第三方 CDN 依赖</li>
</ul>
'''
    (OUT / "index.html").write_text(page("Far Out Research Preview", body, base_path=""), encoding='utf-8')


def build_radical_software_index():
    # Check for cover assets
    assets_dir = SRC / "final_handoff/radical-software-v2/assets"
    has_wechat = (assets_dir / "cover-wechat-16x9.png").exists()
    has_x = (assets_dir / "cover-x-16x9.png").exists()
    has_xhs = (assets_dir / "cover-xiaohongshu-3x4.png").exists()

    cover_html = ""
    if has_wechat or has_x or has_xhs:
        cover_html += '<div style="display:flex;flex-wrap:wrap;gap:12px;margin:1em 0;">'
        if has_wechat:
            shutil.copy(assets_dir / "cover-wechat-16x9.png", OUT / "assets/cover-wechat-16x9.png")
            cover_html += '<img src="../assets/cover-wechat-16x9.png" alt="公众号封面" class="cover-img" style="max-width:320px;">'
        if has_x:
            shutil.copy(assets_dir / "cover-x-16x9.png", OUT / "assets/cover-x-16x9.png")
            cover_html += '<img src="../assets/cover-x-16x9.png" alt="X 封面" class="cover-img" style="max-width:320px;">'
        if has_xhs:
            shutil.copy(assets_dir / "cover-xiaohongshu-3x4.png", OUT / "assets/cover-xiaohongshu-3x4.png")
            cover_html += '<img src="../assets/cover-xiaohongshu-3x4.png" alt="小红书封面" class="cover-img" style="max-width:200px;">'
        cover_html += '</div>'
    else:
        cover_html = '<div class="cover-placeholder">cover asset pending</div>'

    body = f'''
<div class="breadcrumb"><a href="../index.html">首页</a> / Radical Software</div>

<h1>在 Sora 之前，他们想重新发明电视</h1>
<p style="color:var(--muted);font-size:1.05rem;"><strong>一本 1970 年代的杂志，和 AI 时代仍没回答的问题</strong></p>

{cover_html}

<h2>摘要</h2>
<div class="summary-box">
<p>1970 年代初，一群美国艺术家和媒介行动者创办了《Radical Software》杂志。他们不问怎么拍出好视频，而问"谁有权拍、谁有权播"。便携摄像机让普通人第一次拥有独立拍摄能力，他们想象的不是更大的广播，而是更小的网络。五十多年后，AI 视频工具再次降低了影像生产门槛，但同样的追问回来了：工具变轻之后，谁来组织观看？</p>
</div>

<h2>各平台版本</h2>
<div class="platform-links">
  <a href="wechat.html">📄 公众号长文</a>
  <a href="x-thread.html">🐦 X Thread</a>
  <a href="jike.html">⚡ 即刻版</a>
  <a href="xiaohongshu.html">📕 小红书版</a>
</div>

<h2>发布摘要</h2>
<div class="summary-box">
<h4>最终推荐标题</h4>
<p>在 Sora 之前，他们想重新发明电视</p>
<h4>推荐副标题</h4>
<p>一本 1970 年代的杂志，和 AI 时代仍没回答的问题</p>
<h4>字数统计</h4>
<ul>
  <li>公众号长文：约 3,200 字</li>
  <li>X Thread：12 条 tweet</li>
  <li>即刻短帖：约 700 字</li>
  <li>小红书发现型笔记：约 700 字</li>
</ul>
<h4>推荐发布顺序</h4>
<ol>
  <li>公众号 / Substack 长文（核心内容）</li>
  <li>X thread（同步或稍晚，配合引流）</li>
  <li>即刻短帖（预热/讨论引爆）</li>
  <li>小红书发现型笔记（预热或后续）</li>
</ol>
</div>

<h2>来源说明</h2>
<p>本文基于 Far Out Company 对《Radical Software, 1973》的图像资料整理，并结合当代 AI 视频与 Agent 内容生产进行分析。本文为当代分析视角，不构成历史定论。</p>
'''
    (OUT / "radical-software/index.html").write_text(page("Radical Software — Far Out Research", body, base_path="../"), encoding='utf-8')


def build_platform_page(md_path, out_name, title, breadcrumb_label):
    md_text = read_md(md_path)
    html_body = md_to_html(md_text)
    breadcrumb = f'<div class="breadcrumb"><a href="../index.html">首页</a> / <a href="index.html">Radical Software</a> / {breadcrumb_label}</div>'
    full = page(title, breadcrumb + html_body, base_path="../")
    (OUT / f"radical-software/{out_name}").write_text(full, encoding='utf-8')


def build_kb_index():
    # Check for articles/cards/prompts
    articles = sorted((SRC / "articles").glob("*.md")) if (SRC / "articles").exists() else []
    cards = sorted((SRC / "cards").glob("*.md")) if (SRC / "cards").exists() else []
    prompts_file = SRC / "prompts/farout-p4-selected-prompts.md"
    x_threads = sorted((SRC / "x_threads").glob("*.md")) if (SRC / "x_threads").exists() else []
    podcasts = sorted((SRC / "podcast").glob("*.md")) if (SRC / "podcast").exists() else []

    body = '''
<div class="breadcrumb"><a href="../index.html">首页</a> / 知识库</div>

<h1>知识库</h1>
<p>Far Out Company 本地知识库与 P4 内容生产成果索引。</p>

<h2>📚 知识库总览</h2>
<div class="card-grid">
  <div class="card">
    <a href="articles/index.html">
      <h3>📝 文章草稿</h3>
      <p>''' + str(len(articles)) + ''' 篇长文草稿</p>
    </a>
  </div>
  <div class="card">
    <a href="cards/index.html">
      <h3>🎴 知识卡</h3>
      <p>''' + str(len(cards)) + ''' 篇中文知识卡</p>
    </a>
  </div>
  <div class="card">
    <a href="prompts/index.html">
      <h3>🎨 Prompt 包</h3>
      <p>精选视觉 Prompt</p>
    </a>
  </div>
</div>

<h2>📊 P4 内容总览</h2>
<table style="width:100%;border-collapse:collapse;margin:1em 0;">
<tr style="border-bottom:2px solid var(--border);">
  <th style="text-align:left;padding:8px;">内容类型</th>
  <th style="text-align:left;padding:8px;">数量</th>
</tr>
<tr style="border-bottom:1px solid var(--border);"><td style="padding:8px;">精选主题</td><td style="padding:8px;">10 个</td></tr>
<tr style="border-bottom:1px solid var(--border);"><td style="padding:8px;">中文知识卡</td><td style="padding:8px;">''' + str(len(cards)) + ''' 篇</td></tr>
<tr style="border-bottom:1px solid var(--border);"><td style="padding:8px;">长文草稿</td><td style="padding:8px;">''' + str(len(articles)) + ''' 篇</td></tr>
<tr style="border-bottom:1px solid var(--border);"><td style="padding:8px;">X thread 草稿</td><td style="padding:8px;">''' + str(len(x_threads)) + ''' 条</td></tr>
<tr style="border-bottom:1px solid var(--border);"><td style="padding:8px;">播客选题脚本</td><td style="padding:8px;">''' + str(len(podcasts)) + ''' 期</td></tr>
<tr style="border-bottom:1px solid var(--border);"><td style="padding:8px;">精选视觉 prompt</td><td style="padding:8px;">20 组</td></tr>
</table>

<h2>Top 10 主题</h2>
<ol>
  <li>约翰·威尔科克的地下报纸网络 — 从《村声》到《Other Scenes》</li>
  <li>Portable Video — 1970年代的 TikTok 前身与今天的 AI 生成</li>
  <li>《Communities》期刊 — 公社运动如何印刷自己的乌托邦</li>
  <li>Total Loss Farm — 一个公社的完整生命周期</li>
  <li>Trina Robbins — 地下漫画界的女性先锋</li>
  <li>科罗拉多自由电台 — 迷幻海报如何成为声音的视觉</li>
  <li>The True Light Beavers — 嬉皮商业化的早期样本</li>
  <li>Kaliflower — 一本杂志如何成为一个公社的日记</li>
  <li>Paperbag — 最简陋的印刷如何传递最强烈的信息</li>
  <li>Brotherhood of the Spirit — 迷幻海报中的宗教与商业</li>
</ol>
'''
    (OUT / "knowledge-base/index.html").write_text(page("知识库 — Far Out Research", body, base_path="../"), encoding='utf-8')


def build_kb_articles():
    articles_dir = SRC / "articles"
    articles = sorted(articles_dir.glob("*.md")) if articles_dir.exists() else []

    body = '<div class="breadcrumb"><a href="../index.html">首页</a> / <a href="index.html">知识库</a> / 文章草稿</div>\n'
    body += '<h1>文章草稿</h1>\n'
    body += '<p>共 ' + str(len(articles)) + ' 篇长文草稿。</p>\n'
    body += '<ul class="article-list">\n'

    for a in articles:
        name = a.stem
        title_text = name.replace('article-', '').replace('-', ' ').title()
        # Try to get first h1 from md
        md = read_md(a)
        m = re.search(r'^#\s+(.+)$', md, re.MULTILINE)
        if m:
            title_text = m.group(1).strip()
        html_name = name + '.html'
        # Generate individual article page
        article_body = md_to_html(md)
        article_page = page(title_text, '<div class="breadcrumb"><a href="../index.html">首页</a> / <a href="index.html">知识库</a> / <a href="index.html">文章草稿</a></div>\n' + article_body, base_path="../../")
        (OUT / "knowledge-base/articles" / html_name).write_text(article_page, encoding='utf-8')
        body += f'<li><a href="articles/{html_name}">{html.escape(title_text)}</a></li>\n'

    body += '</ul>\n'
    (OUT / "knowledge-base/articles/index.html").write_text(page("文章草稿 — Far Out Research", body, base_path="../"), encoding='utf-8')


def build_kb_cards():
    cards_dir = SRC / "cards"
    cards = sorted(cards_dir.glob("*.md")) if cards_dir.exists() else []

    body = '<div class="breadcrumb"><a href="../index.html">首页</a> / <a href="index.html">知识库</a> / 知识卡</div>\n'
    body += '<h1>知识卡</h1>\n'
    body += '<p>共 ' + str(len(cards)) + ' 篇中文知识卡。</p>\n'
    body += '<ul class="article-list">\n'

    for c in cards:
        name = c.stem
        title_text = name.replace('card-', '').replace('-', ' ').title()
        md = read_md(c)
        m = re.search(r'^#\s+(.+)$', md, re.MULTILINE)
        if m:
            title_text = m.group(1).strip()
        html_name = name + '.html'
        card_body = md_to_html(md)
        card_page = page(title_text, '<div class="breadcrumb"><a href="../index.html">首页</a> / <a href="index.html">知识库</a> / <a href="index.html">知识卡</a></div>\n' + card_body, base_path="../../")
        (OUT / "knowledge-base/cards" / html_name).write_text(card_page, encoding='utf-8')
        body += f'<li><a href="cards/{html_name}">{html.escape(title_text)}</a></li>\n'

    body += '</ul>\n'
    (OUT / "knowledge-base/cards/index.html").write_text(page("知识卡 — Far Out Research", body, base_path="../"), encoding='utf-8')


def build_kb_prompts():
    prompts_file = SRC / "prompts/farout-p4-selected-prompts.md"
    body = '<div class="breadcrumb"><a href="../index.html">首页</a> / <a href="index.html">知识库</a> / Prompt 包</div>\n'
    body += '<h1>精选视觉 Prompt</h1>\n'

    if prompts_file.exists():
        md = read_md(prompts_file)
        body += md_to_html(md)
    else:
        body += '<p>Prompt 包文件未找到。</p>\n'

    (OUT / "knowledge-base/prompts/index.html").write_text(page("Prompt 包 — Far Out Research", body, base_path="../"), encoding='utf-8')


def build_readme():
    readme = '''# Far Out Research Preview Site

线上预览站，基于 Far Out Company 本地知识库与 Radical Software 首篇发布包构建。

## 线上地址

https://conanxin.github.io/farout-preview/

## 目录结构

- `index.html` — 首页
- `radical-software/` — 首篇发布（Radical Software）
  - `index.html` — 发布总览
  - `wechat.html` — 公众号长文
  - `x-thread.html` — X Thread
  - `jike.html` — 即刻版
  - `xiaohongshu.html` — 小红书版
- `knowledge-base/` — 知识库
  - `articles/` — 长文草稿（5 篇）
  - `cards/` — 知识卡（10 篇）
  - `prompts/` — 精选视觉 Prompt（20 组）
- `assets/` — 封面图片资源
- `css/style.css` — 样式表

## 说明

- 纯静态 HTML/CSS，无外部 CDN 依赖
- 不访问外部图片
- 当前为 preview site，非正式归档站
- 仅供远程审阅和分享
'''
    (OUT / "README.md").write_text(readme, encoding='utf-8')


def main():
    print("Building Far Out Preview Site...")
    build_css()
    build_home()
    build_radical_software_index()
    build_platform_page(SRC / "final_handoff/radical-software-v2/final-wechat.md", "wechat.html", "公众号长文 — Radical Software", "公众号长文")
    build_platform_page(SRC / "final_handoff/radical-software-v2/final-x-thread.md", "x-thread.html", "X Thread — Radical Software", "X Thread")
    build_platform_page(SRC / "final_handoff/radical-software-v2/final-jike.md", "jike.html", "即刻版 — Radical Software", "即刻版")
    build_platform_page(SRC / "final_handoff/radical-software-v2/final-xiaohongshu.md", "xiaohongshu.html", "小红书版 — Radical Software", "小红书版")
    build_kb_index()
    build_kb_articles()
    build_kb_cards()
    build_kb_prompts()
    build_readme()

    # Count files
    total = sum(1 for _ in OUT.rglob("*") if _.is_file())
    print(f"Done. {total} files written to {OUT}")


if __name__ == "__main__":
    main()
