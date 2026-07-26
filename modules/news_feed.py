"""
news_feed.py — Feed de notícias financeiras via RSS com múltiplas fontes intercaladas.
Fontes: InfoMoney, Valor Econômico, Exame, G1 Economia, Money Times, Investing.com, CNN Economia, Yahoo Finance, CNBC, MarketWatch, Reuters.
"""

import streamlit as st
import feedparser
from datetime import datetime, timezone
import re


FEEDS_BR = [
    {"name": "InfoMoney",       "url": "https://www.infomoney.com.br/feed/",           "icon": "📰"},
    {"name": "Valor Econômico", "url": "https://pox.globo.com/rss/valor/",             "icon": "📰"},
    {"name": "Exame",           "url": "https://exame.com/feed/",                      "icon": "📰"},
    {"name": "G1 Economia",     "url": "https://g1.globo.com/rss/g1/economia/",        "icon": "📰"},
    {"name": "Money Times",     "url": "https://www.moneytimes.com.br/feed/",          "icon": "📰"},
    {"name": "Investing.com BR","url": "https://br.investing.com/rss/news_285.rss",    "icon": "📰"},
    {"name": "CNN Economia",    "url": "https://www.cnnbrasil.com.br/economia/feed/",  "icon": "📰"},
]

FEEDS_WORLD = [
    {"name": "Yahoo Finance",   "url": "https://feeds.finance.yahoo.com/rss/2.0/headline?s=^GSPC&region=US&lang=en-US", "icon": "🌎"},
    {"name": "CNBC",            "url": "https://search.cnbc.com/rs/search/combinedcms/view.xml?partnerId=wrss01&id=10000664",   "icon": "🌎"},
    {"name": "MarketWatch",     "url": "https://feeds.content.dowjones.io/public/rss/mw_topstories",                           "icon": "🌎"},
    {"name": "Reuters",         "url": "https://www.reutersagency.com/feed/?taxonomy=best-topics&post_type=best",              "icon": "🌎"},
    {"name": "Investing.com",   "url": "https://www.investing.com/rss/news_1.rss",                                            "icon": "🌎"},
    {"name": "WSJ Markets",     "url": "https://feeds.a.dj.com/rss/RSSMarketsMain.xml",                                        "icon": "🌎"},
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
    title = re.sub(r"<[^>]+>", "", title)
    if len(title) > 120:
        title = title[:117] + "..."
    return title.strip()


@st.cache_data(ttl=600, show_spinner=False)
def get_news(region: str = "Brasil", max_items: int = 10) -> list:
    """
    Busca notícias via RSS intercalando múltiplas fontes para máxima diversidade.
    Args:
        region: 'Brasil' ou 'Mundo'
        max_items: Número máximo de notícias
    Returns:
        Lista de dicts: {title, link, source, time_ago, icon}
    """
    feeds = FEEDS_BR if region == "Brasil" else FEEDS_WORLD
    feed_buckets = []

    for feed_info in feeds:
        try:
            parsed = feedparser.parse(feed_info["url"])
            bucket = []
            for entry in parsed.entries[:5]:
                title = _clean_title(entry.get("title", ""))
                link = entry.get("link", "#")
                time_ago = _parse_date(entry)

                if title:
                    bucket.append({
                        "title": title,
                        "link": link,
                        "source": feed_info["name"],
                        "time_ago": time_ago,
                        "icon": feed_info["icon"],
                    })
            if bucket:
                feed_buckets.append(bucket)
        except Exception:
            continue

    # Intercalar notícias de diferentes fontes (Round-Robin)
    all_entries = []
    max_len = max((len(b) for b in feed_buckets), default=0)
    for i in range(max_len):
        for bucket in feed_buckets:
            if i < len(bucket):
                all_entries.append(bucket[i])

    # Remove duplicatas por título similar
    seen = set()
    unique = []
    for item in all_entries:
        key = item["title"][:40].lower()
        if key not in seen:
            seen.add(key)
            unique.append(item)

    return unique[:max_items]
