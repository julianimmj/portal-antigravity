"""
market_summary.py — Resumo de Mercado & Análise de Balanços Corporativos
Coleta notícias e análises de fontes públicas (RSS) com foco em:
- Resumo geral do mercado (macro, ações, FIIs, cripto)
- Análise de balanços corporativos com classificação de sentimento
Fontes: InfoMoney, Valor Econômico, Money Times, Suno, SmallCaps, Investing.com BR
"""

import streamlit as st
import feedparser
import requests
import re
from datetime import datetime, timezone


HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept": "application/rss+xml, application/xml, application/atom+xml, text/xml;q=0.9, */*;q=0.8",
}

# ─────────────────────────────────────────
# Perfis acompanhados (X / Twitter)
# ─────────────────────────────────────────
FOLLOWED_PROFILES = [
    # Ações, Valuation e Small Caps
    {"handle": "@varosbr", "name": "VAROS", "category": "Ações & Valuation", "desc": "Investir e multiplicar seu dinheiro com segurança"},
    {"handle": "@vowtz", "name": "Leandro Siqueira", "category": "Ações & Valuation", "desc": "Co-founder @varosbr · Valuations"},
    {"handle": "@gerandoalfa", "name": "Lucas Schneider, CNPI", "category": "Ações & Valuation", "desc": "Investidor Profissional"},
    {"handle": "@Kaio_GAInvest", "name": "Kaio Silva | CNPI", "category": "Ações & Valuation", "desc": "Especialista em Análise de Ações - #GAInvest"},
    {"handle": "@renetous", "name": "Renato A. F. Reis | CNPI-P", "category": "Ações & Valuation", "desc": "Investidor e Analista Fundamentalista na Blue3 Research"},
    {"handle": "@MalekZein7", "name": "Malek Zein, CNPI", "category": "Ações & Valuation", "desc": "Suno Research - Equity Research Analyst"},
    {"handle": "@portalsmallcaps", "name": "SmallCaps", "category": "Ações & Valuation", "desc": "Portal colaborativo focado nas Small Caps brasileiras"},
    {"handle": "@valor_adicionad", "name": "Valor Adicionado", "category": "Ações & Valuation", "desc": "Estrutura produtiva, comercial e tecnológica"},
    {"handle": "@analisedeacoes", "name": "Análise de Ações", "category": "Ações & Valuation", "desc": "Faça seu dinheiro trabalhar para você"},
    {"handle": "@CalixtoCapital", "name": "Calixto Capital", "category": "Ações & Valuation", "desc": "TOP 4 dentre mais de 2.200 fundos de ações ativos"},
    {"handle": "@MZInvestimentos", "name": "MZ Investimentos", "category": "Ações & Valuation", "desc": "Investidor Profissional, Empreendedor e Ciclista"},
    {"handle": "@leiatheinvestor", "name": "The Investor", "category": "Ações & Valuation", "desc": "Truth is like poetry."},
    {"handle": "@marcelohars", "name": "marcelohars", "category": "Ações & Valuation", "desc": "CEO da CGR - Concordia Gestão de Recursos"},
    # Macroeconomia e Notícias
    {"handle": "@MercadosBrasil", "name": "Mercados Brasil", "category": "Macroeconomia", "desc": "Resultados e fatos relevantes das empresas listadas na bolsa"},
    {"handle": "@NotDaBolsa", "name": "Notícias da Bolsa", "category": "Macroeconomia", "desc": "Notícias e fatos relevantes do mercado"},
    {"handle": "@fatosdabolsa", "name": "Fatos da Bolsa", "category": "Macroeconomia", "desc": "Conteúdo educativo somente"},
    {"handle": "@robin_j_brooks", "name": "Robin Brooks", "category": "Macroeconomia", "desc": "Senior Fellow @BrookingsInst, previously Chief Economist @IIF"},
    {"handle": "@insiderreportbr", "name": "Insider Report Brazil", "category": "Macroeconomia", "desc": "Divulgação de movimentações de tesouraria, controlador, conselho e diretoria"},
    {"handle": "@mcmanocall", "name": "Mano Call", "category": "Macroeconomia", "desc": "Davidson @formadores_edu"},
    {"handle": "@BurryArchive", "name": "Michael Burry Archive", "category": "Macroeconomia", "desc": "Archive of @michaeljburry tweets"},
    {"handle": "@odanielscott", "name": "Daniel Scott", "category": "Macroeconomia", "desc": "Negócios e Gestão"},
    {"handle": "@EconomaticaBR", "name": "Economatica", "category": "Macroeconomia", "desc": "Plataforma de dados do mercado financeiro"},
    {"handle": "@Carlos_Parente2", "name": "Carlos Parente", "category": "Macroeconomia", "desc": "Investimentos"},
    {"handle": "@ManfroiRenato", "name": "cansera ok", "category": "Macroeconomia", "desc": "YouTube e conteúdo"},
    # FIIs / Fundos Imobiliários
    {"handle": "@Fiis_FI", "name": "Fundos Imobiliários", "category": "FIIs", "desc": "Promovendo conhecimento em FII's · Renda passiva"},
    {"handle": "@dicadehoje7", "name": "Dica de Hoje", "category": "FIIs", "desc": "Casa de Análise Top 1 pela Anbima e + de 25 anos no mercado financeiro"},
    # Análise Técnica e Cripto
    {"handle": "@LucasCostaAT", "name": "Lucas Costa, CMT", "category": "Análise Técnica", "desc": "Head of Technical Analysis Research – BTG Pactual Investment Bank"},
    {"handle": "@ografista", "name": "O Grafista | Investidor", "category": "Análise Técnica", "desc": "Toda Semana 1 Gráfico Para Seus Investimentos"},
    {"handle": "@TopGrafx", "name": "Nilson Marcelo | @TopGrafx", "category": "Análise Técnica", "desc": "Analista CNPI | Mercado financeiro"},
    {"handle": "@Fernandomarxk", "name": "Fernando Marx Katz", "category": "Análise Técnica", "desc": "Trader @ TC Cosmos FIM | Former Financial Advisor"},
    {"handle": "@CesarFrade1", "name": "CesarFrade", "category": "Análise Técnica", "desc": "Analista e educador"},
    {"handle": "@BHM_Options", "name": "BHM Options", "category": "Opções", "desc": "Algum conhecimento e zero didática"},
    {"handle": "@castacrypto", "name": "Castaneda", "category": "Cripto", "desc": "Co-Founder & COO da @OxusFinance | Pagamentos globais"},
    {"handle": "@CryptoInsightsX", "name": "Crypto Insights", "category": "Cripto", "desc": "Daily Crypto News"},
]


# ─────────────────────────────────────────
# RSS Feeds para Resumo de Mercado
# ─────────────────────────────────────────
SUMMARY_FEEDS = [
    {"name": "InfoMoney",        "url": "https://www.infomoney.com.br/feed/",                 "icon": "📰", "focus": "geral"},
    {"name": "Valor Econômico",  "url": "https://pox.globo.com/rss/valor/",                   "icon": "📰", "focus": "geral"},
    {"name": "Money Times",      "url": "https://www.moneytimes.com.br/feed/",                "icon": "📰", "focus": "geral"},
    {"name": "Exame",            "url": "https://exame.com/feed/",                             "icon": "📰", "focus": "geral"},
    {"name": "Investing.com BR", "url": "https://br.investing.com/rss/news_285.rss",           "icon": "📈", "focus": "geral"},
    {"name": "CNN Economia",     "url": "https://www.cnnbrasil.com.br/economia/feed/",         "icon": "📰", "focus": "geral"},
    {"name": "G1 Economia",      "url": "https://g1.globo.com/rss/g1/economia/",               "icon": "📰", "focus": "geral"},
    {"name": "CNBC",             "url": "https://search.cnbc.com/rs/search/combinedcms/view.xml?partnerId=wrss01&id=10000664", "icon": "🌎", "focus": "global"},
    {"name": "Yahoo Finance",    "url": "https://feeds.finance.yahoo.com/rss/2.0/headline?s=^GSPC&region=US&lang=en-US",       "icon": "🌎", "focus": "global"},
]

# Palavras-chave para filtrar notícias de balanços / resultados
EARNINGS_KEYWORDS = [
    "resultado", "balanço", "lucro", "prejuízo", "receita", "ebitda",
    "dividendo", "provento", "rendimento", "margem", "roe", "roa",
    "trimestre", "trimestral", "2t", "3t", "4t", "1t",
    "reportou", "registrou lucro", "registrou prejuízo",
    "guidance", "projeção", "projeções", "revisão",
    "fluxo de caixa", "capex", "dívida líquida",
    "resultado operacional", "resultado financeiro",
    "earnings", "revenue", "profit", "loss", "eps",
    "fii", "cota", "cotista", "distribuição",
]

# Termos para classificação de sentimento
POSITIVE_TERMS = [
    "forte", "recorde", "supera", "superou", "acima", "crescimento",
    "alta", "avança", "positivo", "sólido", "robusto", "surpreende",
    "surpreendeu", "melhor", "maior", "bom resultado", "recomenda compra",
    "buy", "outperform", "overweight", "top pick",
    "distribuiu", "pagou dividendo", "aumento de dividendo",
    "lucro líquido", "margem recorde", "geração de caixa",
    "ação sobe", "dispara", "valoriza",
]

NEGATIVE_TERMS = [
    "queda", "recuo", "abaixo", "prejuízo", "fraco", "decepciona",
    "decepcionou", "pior", "menor", "ruim", "negativo", "pressão",
    "sell", "underperform", "underweight", "rebaixa",
    "reduz dividendo", "corta proventos", "suspende pagamento",
    "endividamento", "alavancagem alta", "queima de caixa",
    "ação cai", "desaba", "despenca", "tombo",
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
    if len(title) > 150:
        title = title[:147] + "..."
    return title.strip()


def _get_summary_text(entry) -> str:
    """Extrai o resumo/descrição de uma entrada RSS."""
    summary = entry.get("summary", "") or entry.get("description", "")
    summary = re.sub(r"<[^>]+>", "", summary)
    summary = re.sub(r"\s+", " ", summary).strip()
    if len(summary) > 300:
        summary = summary[:297] + "..."
    return summary


def _classify_sentiment(title: str, summary: str) -> dict:
    """
    Classifica o sentimento de uma notícia de balanço como positivo, negativo ou misto.
    Retorna dict com 'label', 'emoji' e 'color'.
    """
    text = (title + " " + summary).lower()

    pos_count = sum(1 for term in POSITIVE_TERMS if term in text)
    neg_count = sum(1 for term in NEGATIVE_TERMS if term in text)

    if pos_count > neg_count and pos_count >= 2:
        return {"label": "Positivo", "emoji": "🟢", "color": "#00e676"}
    elif neg_count > pos_count and neg_count >= 2:
        return {"label": "Negativo", "emoji": "🔴", "color": "#ef4444"}
    elif pos_count > 0 or neg_count > 0:
        return {"label": "Misto", "emoji": "🟡", "color": "#f59e0b"}
    else:
        return {"label": "Neutro", "emoji": "⚪", "color": "rgba(255,255,255,0.5)"}


def _is_earnings_related(title: str, summary: str) -> bool:
    """Verifica se uma notícia é sobre balanço/resultado corporativo."""
    text = (title + " " + summary).lower()
    matches = sum(1 for kw in EARNINGS_KEYWORDS if kw in text)
    return matches >= 2


def _extract_ticker_or_company(title: str) -> str:
    """Tenta extrair o ticker (ex: PETR4) ou nome da empresa do título."""
    # Buscar padrão de ticker B3 (4 letras + 1-2 dígitos)
    ticker_match = re.search(r'\b([A-Z]{4}\d{1,2})\b', title.upper())
    if ticker_match:
        return ticker_match.group(1)

    # Buscar nome de empresa entre parênteses ou antes de "registra/reporta/anuncia"
    company_match = re.search(r'^([A-ZÀ-ÚÇ][a-zà-úç&\s\.]+?)(?:\s+(?:registr|report|anunci|divulg|luc|prej|tem|apresent))', title)
    if company_match:
        return company_match.group(1).strip()

    # Primeiras palavras como fallback (para nomes curtos como "Vale", "Petrobras")
    words = title.split()
    if words and len(words[0]) >= 3 and words[0][0].isupper():
        return words[0].rstrip(",.:;")

    return ""


@st.cache_data(ttl=1800, show_spinner=False)
def get_market_summary(max_items: int = 15) -> list:
    """
    Coleta resumo geral do mercado via RSS, intercalando fontes.
    Retorna lista de dicts com: title, summary, source, time_ago, link, icon.
    """
    feed_buckets = []

    for feed_info in SUMMARY_FEEDS:
        try:
            resp = requests.get(feed_info["url"], headers=HEADERS, timeout=6)
            if resp.status_code == 200:
                parsed = feedparser.parse(resp.content)
                bucket = []
                for entry in parsed.entries[:8]:
                    title = _clean_title(entry.get("title", ""))
                    link = entry.get("link", "#")
                    time_ago = _parse_date(entry)
                    summary = _get_summary_text(entry)

                    if title:
                        bucket.append({
                            "title": title,
                            "summary": summary,
                            "link": link,
                            "source": feed_info["name"],
                            "time_ago": time_ago,
                            "icon": feed_info["icon"],
                            "focus": feed_info["focus"],
                        })
                if bucket:
                    feed_buckets.append(bucket)
        except Exception:
            continue

    # Intercalar (Round-Robin) para diversidade de fontes
    all_entries = []
    max_len = max((len(b) for b in feed_buckets), default=0)
    for i in range(max_len):
        for bucket in feed_buckets:
            if i < len(bucket):
                all_entries.append(bucket[i])

    # Deduplicar
    seen = set()
    unique = []
    for item in all_entries:
        key = item["title"][:45].lower()
        if key not in seen:
            seen.add(key)
            unique.append(item)

    return unique[:max_items]


@st.cache_data(ttl=1800, show_spinner=False)
def get_earnings_analysis(max_items: int = 12) -> list:
    """
    Coleta análises de balanços corporativos com classificação de sentimento.
    Filtra notícias que contêm pelo menos 2 palavras-chave de balanço.
    Retorna lista de dicts com: title, summary, source, time_ago, link,
                                 sentiment, company.
    """
    earnings_feeds = [
        {"name": "InfoMoney",       "url": "https://www.infomoney.com.br/feed/",          "icon": "📊"},
        {"name": "Valor Econômico", "url": "https://pox.globo.com/rss/valor/",            "icon": "📊"},
        {"name": "Money Times",     "url": "https://www.moneytimes.com.br/feed/",         "icon": "📊"},
        {"name": "Exame",           "url": "https://exame.com/feed/",                      "icon": "📊"},
        {"name": "Investing.com BR","url": "https://br.investing.com/rss/news_285.rss",   "icon": "📊"},
        {"name": "CNN Economia",    "url": "https://www.cnnbrasil.com.br/economia/feed/", "icon": "📊"},
    ]

    all_earnings = []

    for feed_info in earnings_feeds:
        try:
            resp = requests.get(feed_info["url"], headers=HEADERS, timeout=6)
            if resp.status_code == 200:
                parsed = feedparser.parse(resp.content)
                for entry in parsed.entries[:15]:
                    title = _clean_title(entry.get("title", ""))
                    summary = _get_summary_text(entry)
                    link = entry.get("link", "#")
                    time_ago = _parse_date(entry)

                    if title and _is_earnings_related(title, summary):
                        sentiment = _classify_sentiment(title, summary)
                        company = _extract_ticker_or_company(title)

                        all_earnings.append({
                            "title": title,
                            "summary": summary,
                            "link": link,
                            "source": feed_info["name"],
                            "time_ago": time_ago,
                            "icon": feed_info["icon"],
                            "sentiment": sentiment,
                            "company": company,
                        })
        except Exception:
            continue

    # Deduplicar por título
    seen = set()
    unique = []
    for item in all_earnings:
        key = item["title"][:45].lower()
        if key not in seen:
            seen.add(key)
            unique.append(item)

    # Ordenar: negativos primeiro (mais impactantes), depois mistos, depois positivos
    sentiment_order = {"Negativo": 0, "Misto": 1, "Positivo": 2, "Neutro": 3}
    unique.sort(key=lambda x: sentiment_order.get(x["sentiment"]["label"], 4))

    return unique[:max_items]


def get_followed_profiles() -> dict:
    """Retorna os perfis acompanhados organizados por categoria."""
    categories = {}
    for p in FOLLOWED_PROFILES:
        cat = p["category"]
        if cat not in categories:
            categories[cat] = []
        categories[cat].append(p)
    return categories
