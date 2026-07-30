# Source Acquisition Policy

## Default Strategy

URL acquisition uses a hybrid strategy, but not a free-for-all scraper.

Primary path:

```text
httpx fetch -> Beautiful Soup parse -> deterministic article text extraction -> source spans
```

Fallback / helper path:

```text
OpenAI web search or GPT-assisted extraction -> citations -> source card warnings
```

The deterministic path is the source of truth when it can extract usable text. GPT-assisted web retrieval is allowed only when:

- the static HTML path is too noisy or too thin,
- current information is required,
- the result needs source citations,
- or the user explicitly requests web search.

GPT must not be used to bypass robots.txt, login walls, paywalls, blocked APIs, or site access restrictions.

## Robots and Terms

Before adding site-specific extraction, check:

- `robots.txt`
- site terms or platform rules when available
- whether the URL is public and intended to be read without login

If access is restricted or unclear, stop with a source-readiness warning instead of trying alternate endpoints.

## note and Hatena Blog Target

Target platforms:

- note-style article output
- Hatena Blog-style article output

These are output style targets, not permission to crawl the platforms broadly.

For note URLs:

- Use public article pages only.
- Do not use `/api/*` endpoints.
- Do not fetch login, preview, PDF, search, archive, follower, following, like, magazine, or message pages.
- Respect the current `note.com/robots.txt` restrictions.

For Hatena Blog URLs:

- Use public article pages only.
- Respect Hatena policies and robots restrictions.
- Do not use authenticated pages, admin pages, private feeds, or unofficial internal APIs.

## Extraction Confidence

Each URL extraction result should record:

- `fetch_status`
- `canonical_url`
- `title`
- `published_or_updated_at`
- `extracted_text`
- `source_spans`
- `extraction_method`
- `extraction_confidence`
- `warnings`

Confidence guidance:

- `high`: title, main body, and date are cleanly extracted from public HTML.
- `medium`: body is usable but includes some boilerplate or uncertain date.
- `low`: text is thin, noisy, blocked, or likely incomplete.

Low-confidence URL extraction must not proceed silently into article generation.

## Source Length Limit for Generation Preprocessing

Each extracted source is capped before it enters generation preprocessing:

- default maximum: `12000` characters per source,
- limit target: extracted readable text, not raw HTML,
- over-limit sources must receive a `source_over_limit` warning,
- truncation must not be silent,
- chunks must preserve source span IDs and source locations,
- generation-facing packets should carry `original_text_chars`, `included_text_chars`, and `excluded_text_chars`.

The first implementation uses deterministic chunking. It does not summarize, rewrite, or call an LLM.

## note / Hatena Natural Blog Target

note and Hatena Blog remain output-style targets, not crawling targets.

Web research on 2026-05-08 confirmed these platform-relevant structure signals:

- note official guidance treats headings as a way to make articles easier for readers to understand.
- note's creator guidance groups writing around theme, title, readability, and delivery to readers.
- Hatena Blog supports heading-based table-of-contents behavior for longer structured articles.
- Hatena Blog supports visible editing modes and simple heading/list markup.

Generation preprocessing should therefore preserve heading-like source structure and carry a `note_hatena_natural_blog` style target into later LLM phases. It must not convert platform guidance into unsupported source facts.

## Source Priority

Use this initial priority when sources conflict:

1. user-provided manual text
2. user-uploaded PDF or Word
3. official public URL
4. external public URL
5. GPT/web-search summary with citations

GPT/web-search-derived material should be treated as lower priority than directly extracted user-provided source material unless the user explicitly states otherwise.
