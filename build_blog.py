#!/usr/bin/env python3
"""Static blog generator for the zsazsa site.

Reads Markdown posts from ``posts/``, writes one static HTML page per post
into ``blog/``, and regenerates ``news.html`` as the index. 
"""
from __future__ import annotations

import html
import re
import sys
from datetime import date, datetime
from pathlib import Path

import markdown
import yaml

ROOT = Path(__file__).resolve().parent
POSTS_DIR = ROOT / "posts"
BLOG_DIR = ROOT / "blog"
NEWS_FILE = ROOT / "news.html"

GITHUB_URL = "https://github.com/zsazsa-project/zsazsa"
MISP_URL = "https://www.misp-project.org/"

GH_ICON = (
    '<svg width="16" height="16" viewBox="0 0 16 16" fill="currentColor">'
    '<path d="M8 0C3.58 0 0 3.58 0 8c0 3.54 2.29 6.53 5.47 7.59.4.07.55-.17.55-.38 '
    "0-.19-.01-.82-.01-1.49-2.01.37-2.53-.49-2.69-.94-.09-.23-.48-.94-.82-1.13-.28-.15-.68-.52-.01-.53.63-.01 "
    "1.08.58 1.23.82.72 1.21 1.87.87 2.33.66.07-.52.28-.87.51-1.07-1.78-.2-3.64-.89-3.64-3.95 "
    "0-.87.31-1.59.82-2.15-.08-.2-.36-1.02.08-2.12 0 0 .67-.21 2.2.82.64-.18 1.32-.27 2-.27.68 0 "
    "1.36.09 2 .27 1.53-1.04 2.2-.82 2.2-.82.44 1.1.16 1.92.08 2.12.51.56.82 1.27.82 2.15 0 "
    "3.07-1.87 3.75-3.65 3.95.29.25.54.73.54 1.48 0 1.07-.01 1.93-.01 2.2 0 .21.15.46.55.38A8.01 "
    '8.01 0 0016 8c0-4.42-3.58-8-8-8z"/></svg>'
)
SHIELD = (
    '<svg viewBox="0 0 24 24" fill="currentColor"><path d="M12 1L3 5v6c0 5.55 3.84 '
    '10.74 9 12 5.16-1.26 9-6.45 9-12V5l-9-4z"/></svg>'
)

NAV_ITEMS = [
    ("features", "Features", "features.html"),
    ("documentation", "Documentation", "documentation.html"),
    ("download", "Download", "download.html"),
    ("news", "News", "news.html"),
    ("contact", "Contact", "contact.html"),
]


def nav(base: str, active: str) -> str:
    links = []
    for key, label, href in NAV_ITEMS:
        cls = ' class="active"' if key == active else ""
        links.append(f'        <li><a href="{base}{href}"{cls}>{label}</a></li>')
    links_html = "\n".join(links)
    return f"""  <nav class="site-nav">
    <div class="nav-inner">
      <a href="{base}index.html" class="brand">
        <span class="glyph">{SHIELD}</span>
        zsazsa <span class="sub">CTI</span>
      </a>
      <button class="nav-toggle" aria-label="Toggle navigation" onclick="document.getElementById('navlinks').classList.toggle('open')">☰</button>
      <ul class="nav-links" id="navlinks">
{links_html}
        <li><a href="{GITHUB_URL}" class="gh" target="_blank" rel="noopener">
          {GH_ICON}
          GitHub</a></li>
      </ul>
    </div>
  </nav>"""


def footer(base: str) -> str:
    return f"""  <footer class="site-footer">
    <div class="container">
      <div class="foot-grid">
        <div>
          <span class="foot-brand">
            <span class="glyph">{SHIELD}</span>
            zsazsa
          </span>
          <p class="foot-about">An open-source CTI program management and production platform built around MISP.</p>
        </div>
        <div>
          <h4>Project</h4>
          <a href="{base}features.html">Features</a>
          <a href="{base}documentation.html">Documentation</a>
          <a href="{base}download.html">Download</a>
          <a href="{base}news.html">News</a>
        </div>
        <div>
          <h4>Resources</h4>
          <a href="{GITHUB_URL}" target="_blank" rel="noopener">GitHub repository</a>
          <a href="{MISP_URL}" target="_blank" rel="noopener">MISP project</a>
          <a href="{base}contact.html">Contact</a>
        </div>
      </div>
      <div class="foot-bottom">
        <span>© <span id="year"></span> zsazsa project · Open source</span>
        <span>Built on <a href="{MISP_URL}" target="_blank" rel="noopener" style="display:inline;">MISP</a></span>
      </div>
    </div>
  </footer>

  <script>document.getElementById('year').textContent = new Date().getFullYear();</script>"""


def document(*, base: str, active: str, title: str, description: str, body: str) -> str:
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{html.escape(title)}</title>
  <meta name="description" content="{html.escape(description)}">
  <link rel="icon" type="image/svg+xml" href="{base}assets/img/favicon.svg">
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
  <link rel="stylesheet" href="{base}assets/css/site.css">
</head>
<body>

{nav(base, active)}

{body}

{footer(base)}
</body>
</html>
"""


FRONT_MATTER_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.DOTALL)
DATE_PREFIX_RE = re.compile(r"^(\d{4}-\d{2}-\d{2})-")
# rewrite root-relative asset paths so they resolve from blog/<slug>.html
ASSET_PATH_RE = re.compile(r'(src|href)=(["\'])(assets/)')


class Post:
    def __init__(self, path: Path):
        raw = path.read_text(encoding="utf-8")
        m = FRONT_MATTER_RE.match(raw)
        if not m:
            raise ValueError(f"{path.name}: missing front matter block (--- ... ---)")
        meta = yaml.safe_load(m.group(1)) or {}
        self.body_md = raw[m.end():]
        self.source = path

        self.title = str(meta.get("title") or "").strip()
        if not self.title:
            raise ValueError(f"{path.name}: 'title' is required in front matter")
        self.summary = str(meta.get("summary") or "").strip()
        self.author = str(meta.get("author") or "").strip()
        self.status = str(meta.get("status") or "published").strip().lower()
        self.external = (str(meta.get("external")).strip() if meta.get("external") else None)

        stem = path.stem
        dm = DATE_PREFIX_RE.match(stem)
        self.slug = stem[dm.end():] if dm else stem

        self.date = self._resolve_date(meta.get("date"), dm)

    @staticmethod
    def _resolve_date(value, dm) -> date | None:
        if isinstance(value, datetime):
            return value.date()
        if isinstance(value, date):
            return value
        if isinstance(value, str) and value.strip():
            return datetime.strptime(value.strip(), "%Y-%m-%d").date()
        if dm:
            return datetime.strptime(dm.group(1), "%Y-%m-%d").date()
        return None

    @property
    def date_label(self) -> str:
        return self.date.strftime("%-d %B %Y") if self.date else "Coming soon"

    @property
    def url(self) -> str:
        return f"blog/{self.slug}.html"

    @property
    def sort_key(self):
        # newest first; undated (drafts) sink to the bottom
        return self.date or date.min


def render_body(post: Post) -> str:
    md = markdown.Markdown(
        extensions=["fenced_code", "codehilite", "tables", "attr_list", "md_in_html", "sane_lists"],
        extension_configs={"codehilite": {"guess_lang": False, "css_class": "codehilite"}},
    )
    body_html = md.convert(post.body_md)
    body_html = ASSET_PATH_RE.sub(r'\1=\2../\3', body_html)
    return body_html


def build_post_page(post: Post) -> None:
    body_html = render_body(post)
    meta_bits = [post.date_label]
    if post.author:
        meta_bits.append(post.author)
    if post.status == "draft":
        meta_bits.append("Draft")
    meta_line = " · ".join(meta_bits)

    body = f"""  <header class="page-head">
    <div class="container">
      <div class="kicker">Blog</div>
      <h1>{html.escape(post.title)}</h1>
      <p>{html.escape(meta_line)}</p>
    </div>
  </header>

  <section>
    <div class="container">
      <article class="prose blog-post">
{body_html}
        <p class="blog-back"><a href="../news.html">← Back to all posts</a></p>
      </article>
    </div>
  </section>"""

    description = post.summary or f"{post.title} — zsazsa CTI blog."
    out = document(
        base="../",
        active="news",
        title=f"{post.title} · zsazsa CTI",
        description=description,
        body=body,
    )
    (BLOG_DIR / f"{post.slug}.html").write_text(out, encoding="utf-8")


def index_card(post: Post) -> str:
    if post.status == "draft":
        badge = '<span class="badge badge-draft" style="margin-top:8px;">Draft</span>'
    else:
        badge = '<span class="badge badge-public" style="margin-top:8px;">Published</span>'

    summary = f"<p>{html.escape(post.summary)}</p>" if post.summary else ""

    title = html.escape(post.title)
    if post.external:
        link = f'<a href="{html.escape(post.external)}" target="_blank" rel="noopener">{title}</a>'
    else:
        link = f'<a href="{post.url}">{title}</a>'

    return f"""      <article class="post">
        <div>
          <div class="post-date">{html.escape(post.date_label)}</div>
          {badge}
        </div>
        <div>
          <h3>{link}</h3>
          {summary}
        </div>
      </article>"""


def build_index(posts: list[Post]) -> None:
    listed = [p for p in posts if p.status != "hidden"]
    listed.sort(key=lambda p: p.sort_key, reverse=True)
    cards = "\n\n".join(index_card(p) for p in listed)

    body = f"""  <header class="page-head">
    <div class="container">
      <div class="kicker">News</div>
      <h1>What's happening with zsazsa</h1>
      <p>Articles and walkthroughs about zsazsa.</p>
    </div>
  </header>

  <section>
    <div class="container" style="max-width:880px;">

{cards}

      <div class="callout" style="margin-top:30px;">
        <strong>Stay updated.</strong> Project changes, issues and discussions are on
        <a href="{GITHUB_URL}" target="_blank" rel="noopener">GitHub</a>. Watch the repository to be notified when a new release is published.
      </div>

    </div>
  </section>"""

    out = document(
        base="",
        active="news",
        title="News · zsazsa CTI",
        description="News and blog posts about zsazsa: walkthroughs, releases and articles.",
        body=body,
    )
    NEWS_FILE.write_text(out, encoding="utf-8")


def main() -> int:
    if not POSTS_DIR.is_dir():
        print(f"No posts directory at {POSTS_DIR}", file=sys.stderr)
        return 1

    BLOG_DIR.mkdir(exist_ok=True)

    posts: list[Post] = []
    for path in sorted(POSTS_DIR.glob("*.md")):
        if path.name.lower() == "readme.md":
            continue
        try:
            posts.append(Post(path))
        except ValueError as exc:
            print(f"ERROR: {exc}", file=sys.stderr)
            return 1

    built = 0
    for post in posts:
        if post.external:
            continue  # external posts only appear on the index
        build_post_page(post)
        built += 1

    build_index(posts)
    print(f"Built {built} post page(s) from {len(posts)} source file(s); regenerated news.html")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
