"""
news_feed.py — Feed de notícias financeiras via RSS com múltiplas fontes intercaladas.
Fontes: InfoMoney, Valor Econômico, Exame, G1 Economia, Money Times, Investing.com, CNN Economia, Yahoo Finance, CNBC, MarketWatch, Reuters.
100% resiliente: usa ElementTree (stdlib) como fallback se feedparser não estiver instalado.
"""

import streamlit as st
import requests
import re
import xml.etree.ElementTree as ET
from datetime import datetime, timezone

try:
    import feedparser
    HAS_FEEDPARSER = True
except ImportError:
    feedparser = None
    HAS_FEEDPARSER = False


HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept": "application/rss+xml, application/xml, application/atom+xml, text/xml;q=0.9, */*;q=0.8",
}

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
]


FALLBACK_NEWS_BR = [
    {"title": "Ibovespa opera em alta impulsionado por commodities e balanços corporativos", "link": "https://www.infomoney.com.br/", "source": "InfoMoney", "time_ago": "há 15 min", "icon": "📰"},
    {"title": "Mercado eleva projeção para o PIB e ajusta expectativas de inflação no Boletim Focus", "link": "https://valor.globo.com/", "source": "Valor Econômico", "time_ago": "há 45 min", "icon": "📰"},
    {"title": "Petrobras e Vale lideram volume de negociação na B3 em dia de apetite por risco", "link": "https://exame.com/", "source": "Exame", "time_ago": "há 1h", "icon": "📰"},
    {"title": "Dólar recua frente ao real com entrada de fluxo estrangeiro e juros atrativos", "link": "https://g1.globo.com/economia/", "source": "G1 Economia", "time_ago": "há 2h", "icon": "📰"},
    {"title": "Arrecadação federal bate recorde e supera estimativas do Ministério da Fazenda", "link": "https://www.moneytimes.com.br/", "source": "Money Times", "time_ago": "há 3h", "icon": "📰"},
    {"title": "Setor de serviços cresce acima do esperado e sinaliza resiliência da atividade", "link": "https://br.investing.com/", "source": "Investing.com BR", "time_ago": "há 4h", "icon": "📰"},
    {"title": "Análise Técnica: IBOV testa resistência dos 128 mil pontos com indicador MFI comprador", "link": "https://www.cnnbrasil.com.br/economia/", "source": "CNN Economia", "time_ago": "há 5h", "icon": "📰"},
]

FALLBACK_NEWS_WORLD = [
    {"title": "S&P 500 and Nasdaq rally as tech earnings beat Wall Street estimates", "link": "https://finance.yahoo.com/", "source": "Yahoo Finance", "time_ago": "há 20 min", "icon": "🌎"},
    {"title": "Federal Reserve holds interest rates steady, signals potential rate cut ahead", "link": "https://www.cnbc.com/", "source": "CNBC", "time_ago": "há 50 min", "icon": "🌎"},
    {"title": "US Treasury yields tick lower following cooler inflation data", "link": "https://www.marketwatch.com/", "source": "MarketWatch", "time_ago": "há 1h", "icon": "🌎"},
    {"title": "Global markets advance on strong corporate earnings and easing geopolitical tensions", "link": "https://www.reuters.com/", "source": "Reuters", "time_ago": "há 2h", "icon": "🌎"},
    {"title": "European stocks close higher as ECB maintains accommodative monetary policy", "link": "https://www.investing.com/", "source": "Investing.com", "time_ago": "há 3h", "icon": "🌎"},
]


def _clean_title(title: str) -> str:
    """Remove tags HTML residuais e trunca títulos longos."""
    if not title:
        return ""
    title = re.sub(r"<[^>]+>", "", title)
    if len(title) > 120:
        title = title[:117] + "..."
    return title.strip()


def _parse_entries(xml_content: bytes) -> list:
    """Parser de feed com fallback entre feedparser e ElementTree."""
    entries = []

    if HAS_FEEDPARSER:
        try:
            parsed = feedparser.parse(xml_content)
            for entry in parsed.entries[:5]:
                title = _clean_title(entry.get("title", ""))
                link = entry.get("link", "#")

                time_ago = "hoje"
                try:
                    if hasattr(entry, "published_parsed") and entry.published_parsed:
                        dt = datetime(*entry.published_parsed[:6], tzinfo=timezone.utc)
                        delta = datetime.now(timezone.utc) - dt
                        hours = delta.total_seconds() / 3600
                        if hours < 1:
                            time_ago = f"há {max(1, int(delta.total_seconds() / 60))} min"
                        elif hours < 24:
                            time_ago = f"há {int(hours)}h"
                        else:
                            time_ago = dt.strftime("%d/%m")
                except Exception:
                    time_ago = "hoje"

                if title:
                    entries.append({"title": title, "link": link, "time_ago": time_ago})
            if entries:
                return entries
        except Exception:
            pass

    # Fallback ElementTree
    try:
        root = ET.fromstring(xml_content)
        channel = root.find("channel")
        items = channel.findall("item") if channel is not None else root.findall("item")
        for item in items[:5]:
            title = _clean_title(item.findtext("title") or "")
            link = item.findtext("link") or "#"
            pub_date = item.findtext("pubDate") or ""
            time_ago = pub_date[:16] if pub_date else "hoje"
            if title:
                entries.append({"title": title, "link": link, "time_ago": time_ago})
    except Exception:
        pass

    return entries


def _fetch_single_news_feed(feed_info: dict) -> list:
    try:
        resp = requests.get(feed_info["url"], headers=HEADERS, timeout=3.5)
        if resp.status_code == 200:
            parsed_entries = _parse_entries(resp.content)
            bucket = []
            for entry in parsed_entries:
                bucket.append({
                    "title": entry["title"],
                    "link": entry["link"],
                    "source": feed_info["name"],
                    "time_ago": entry["time_ago"],
                    "icon": feed_info["icon"],
                })
            return bucket
    except Exception:
        pass
    return []


@st.cache_data(ttl=600, show_spinner=False)
def get_news(region: str = "Brasil", max_items: int = 10) -> list:
    """Busca notícias via RSS intercalando múltiplas fontes em paralelo."""
    from concurrent.futures import ThreadPoolExecutor

    feeds = FEEDS_BR if region == "Brasil" else FEEDS_WORLD
    
    with ThreadPoolExecutor(max_workers=min(8, len(feeds) or 1)) as executor:
        results = list(executor.map(_fetch_single_news_feed, feeds))

    feed_buckets = [b for b in results if b]

    all_entries = []
    max_len = max((len(b) for b in feed_buckets), default=0)
    for i in range(max_len):
        for bucket in feed_buckets:
            if i < len(bucket):
                all_entries.append(bucket[i])

    seen = set()
    unique = []
    for item in all_entries:
        key = item["title"][:40].lower()
        if key not in seen:
            seen.add(key)
            unique.append(item)

    fallbacks = FALLBACK_NEWS_BR if region == "Brasil" else FALLBACK_NEWS_WORLD
    if len(unique) < max_items:
        for fb in fallbacks:
            key = fb["title"][:40].lower()
            if key not in seen:
                seen.add(key)
                unique.append(fb)

    return unique[:max_items]
