"""
news_feed.py — Feed de notícias financeiras via RSS.
Fontes: InfoMoney, Valor Econômico, Exame, G1 Economia, Yahoo Finance, CNBC, MarketWatch, Reuters.
"""

import streamlit as st
import feedparser
from datetime import datetime, timezone
import time as _time


FEEDS_BR = [
    {"name": "InfoMoney",       "url": "https://www.infomoney.com.br/feed/",           "icon": "📰"},
    {"name": "Valor Econômico", "url": "https://pox.globo.com/rss/valor/",             "icon": "📰"},
    {"name": "Exame",           "url": "https://exame.com/feed/",                      "icon": "📰"},
    {"name": "G1 Economia",     "url": "https://g1.globo.com/rss/g1/economia/",        "icon": "📰"},
]

FEEDS_WORLD = [
    {"name": "Yahoo Finance",   "url": "https://feeds.finance.yahoo.com/rss/2.0/headline?s=^GSPC&region=US&lang=en-US", "icon": "🌎"},
    {"name": "CNBC",            "url": "https://search.cnbc.com/rs/search/combinedcms/view.xml?partnerId=wrss01&id=10000664",   "icon": "🌎"},
    {"name": "MarketWatch",     "url": "https://feeds.content.dowjones.io/public/rss/mw_topstories",                           "icon": "🌎"},
    {"name": "Reuters",         "url": "https://www.reutersagency.com/feed/?taxonomy=best-topics&post_type=best",              "icon": "🌎"},
]


def _parse_date(entry) -> str:
    """Extrai e formata a data de uma entrada RSS."""
    try:
        if hasattr(entry, "published_parsed") and entry.published_parsed:
            dt = datetime(*entry.published_parsed[:6], tzinfo=timezone.utc)
        elif hasattr(entry, "updated_parsed") and entry.updated_parsed:
            dt = datetime(*entry.updated_parsed[:6], tzinfo=timezone.utc)
        else:
            return ""

        now = datetime.now(timezone.utc)
        delta = now - dt
        hours = delta.total_seconds() / 3600

        if hours < 1:
            mins = int(delta.total_seconds() / 60)
            return f"há {max(1, mins)} min"
        elif hours < 24:
            return f"há {int(hours)}h"
        elif hours < 48:
            return "ontem"
        else:
            return dt.strftime("%d/%m")
    except Exception:
        return ""


def _clean_title(title: str) -> str:
    """Remove tags HTML residuais e trunca títulos longos."""
    import re
    title = re.sub(r"<[^>]+>", "", title)
    if len(title) > 130:
        title = title[:127] + "..."
    return title.strip()


@st.cache_data(ttl=600, show_spinner=False)
def get_news(region: str = "Brasil", max_items: int = 10) -> list:
    """
    Busca notícias via RSS.
    Args:
        region: 'Brasil' ou 'Mundo'
        max_items: Número máximo de notícias
    Returns:
        Lista de dicts: {title, link, source, time_ago, icon}
    """
    feeds = FEEDS_BR if region == "Brasil" else FEEDS_WORLD
    all_entries = []

    for feed_info in feeds:
        try:
            parsed = feedparser.parse(feed_info["url"])
            for entry in parsed.entries[:max_items]:
                title = _clean_title(entry.get("title", ""))
                link = entry.get("link", "#")
                time_ago = _parse_date(entry)

                if title:
                    all_entries.append({
                        "title": title,
                        "link": link,
                        "source": feed_info["name"],
                        "time_ago": time_ago,
                        "icon": feed_info["icon"],
                    })
        except Exception:
            continue

    # Remove duplicatas por título similar
    seen = set()
    unique = []
    for item in all_entries:
        key = item["title"][:50].lower()
        if key not in seen:
            seen.add(key)
            unique.append(item)

    return unique[:max_items]
