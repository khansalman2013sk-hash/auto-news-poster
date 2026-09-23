"""
fetch_news.py
Fetches top news headlines from configured RSS feeds. RSS is the site's own
legal syndication feed (meant to be consumed by other tools) — this does NOT
scrape article pages or copy full article text, only the headline + a short
snippet that the publisher already put in the feed for this purpose.

Returns headline + short summary + source + link for each item, ready to be
turned into an ORIGINAL narration (see generate_script.py) — the article body
itself is never copied.
"""
import re
from datetime import datetime
from email.utils import parsedate_to_datetime

import feedparser


def _parse_date(entry):
    for key in ("published", "updated"):
        val = entry.get(key)
        if val:
            try:
                return parsedate_to_datetime(val)
            except Exception:
                pass
    return datetime.min


def fetch_top_news(feeds, top_n=10):
    """
    feeds: list of {"name": str, "url": str}   (from config.yaml)

    Returns: list of dicts, most recent first, length <= top_n:
        {"title": str, "summary": str, "source": str, "link": str, "published": datetime}
    """
    items = []
    seen_titles = set()

    for feed in feeds:
        parsed = feedparser.parse(feed["url"])
        for entry in parsed.entries:
            title = (entry.get("title") or "").strip()
            if not title:
                continue
            key = title.lower()[:60]
            if key in seen_titles:
                continue
            seen_titles.add(key)

            summary = (entry.get("summary") or "").strip()
            summary = re.sub("<[^<]+?>", "", summary).strip()  # strip any HTML tags

            items.append({
                "title": title,
                "summary": summary[:280],
                "source": feed.get("name", "News"),
                "link": entry.get("link", ""),
                "published": _parse_date(entry),
            })

    items.sort(key=lambda x: x["published"], reverse=True)
    return items[:top_n]


if __name__ == "__main__":
    # Quick manual test: python src/fetch_news.py
    sample_feeds = [{
        "name": "Google News India",
        "url": "https://news.google.com/rss?hl=en-IN&gl=IN&ceid=IN:en",
    }]
    for i, n in enumerate(fetch_top_news(sample_feeds, top_n=5), 1):
        print(i, "-", n["title"], "|", n["source"])
