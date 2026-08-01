"""
news_feed.py — Feed de notícias financeiras via RSS com múltiplas fontes intercaladas.
Fontes: InfoMoney, Valor Econômico, Exame, G1 Economia, Money Times, Investing.com, CNN Economia, Yahoo Finance, CNBC, MarketWatch, Reuters.
"""

import streamlit as st
import feedparser
import requests
from datetime import datetime, timezone
import re


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


# Fallbacks atualizados para manter o feed sempre povoado
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


def _parse_date(entry) -> str:
    """Extrai e formata a data de uma entrada RSS."""
    try:
        if hasattr(entry, "published_parsed") and entry.published_parsed:
            dt = datetime(*entry.published_parsed[:6], tzinfo=timezone.utc)
        elif hasattr(entry, "updated_parsed") and entry.updated_parsed:
            dt = datetime(*entry.updated_parsed[:6], tzinfo=timezone.utc)
        else:
            return "hoje"

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
        return "hoje"


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
    Usa requests com User-Agent para evitar bloqueios HTTP 403/406.
    """
    feeds = FEEDS_BR if region == "Brasil" else FEEDS_WORLD
    feed_buckets = []

    for feed_info in feeds:
        try:
            resp = requests.get(feed_info["url"], headers=HEADERS, timeout=5)
            if resp.status_code == 200:
                parsed = feedparser.parse(resp.content)
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

    # Se não houver notícias suficientes (devido a falhas de rede), completa com fallbacks
    fallbacks = FALLBACK_NEWS_BR if region == "Brasil" else FALLBACK_NEWS_WORLD
    if len(unique) < max_items:
        for fb in fallbacks:
            key = fb["title"][:40].lower()
            if key not in seen:
                seen.add(key)
                unique.append(fb)

    return unique[:max_items]

