# Blog posts

Each file here is one blog post, written in Markdown. On push (or when you run
`python build_blog.py` locally) the generator turns these into static HTML:

- one page per post in `../blog/<slug>.html`
- the news index at `../news.html`, rebuilt from every post's front matter

You only edit files in this folder. Never edit `../blog/*.html` or
`../news.html` by hand — they are generated and will be overwritten.

## Writing a post

Create a file named `YYYY-MM-DD-some-slug.md` (the date prefix sets ordering and
the publish date; the slug becomes the page filename). Start with front matter:

```markdown
---
title: Your post title
date: 2026-07-15
summary: One-line teaser shown on the news index.
status: published
---

# Your content in Markdown
```

### Front matter fields

| Field      | Required | Notes                                                            |
|------------|----------|------------------------------------------------------------------|
| `title`    | yes      | Shown as the page H1 and on the index.                           |
| `date`     | no\*     | `YYYY-MM-DD`. Falls back to the date in the filename.            |
| `summary`  | no       | Teaser on the index and the page meta description.               |
| `author`   | no       | Shown in the byline next to the date on the post page.           |
| `status`   | no       | `published` (default), `draft`, or `hidden`.                     |
| `external` | no       | A URL. The index links out to it and no local page is built.     |

\* A post with no date at all is treated as undated and sorts to the bottom
(useful for a "coming soon" draft).

### Status meanings

- **published** — on the index, page built.
- **draft** — on the index with a "Draft" badge and a *Preview* link; page built.
- **hidden** — page built (preview by direct URL) but kept off the index.

## Content

- **Code:** fenced ```` ```lang ```` blocks, highlighted at build time.
- **Images:** put files in `../assets/img/blog/` and reference them as
  `assets/img/blog/name.png` (the build fixes the relative path).
- **Video:** paste a raw `<iframe>` (YouTube/Vimeo) or `<video>` tag into the
  Markdown. Keep large self-hosted files out of git — prefer an embed or git-lfs.

See `2026-06-29-example-post.md` for a working example of all of the above.

## Building locally (optional)

Publishing happens automatically via GitHub Actions on push. To preview locally:

```bash
python -m venv venv
source venv/bin/activate
pip install -r ../blog-requirements.txt
python ../build_blog.py
```
