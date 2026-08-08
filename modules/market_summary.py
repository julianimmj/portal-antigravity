"""
market_summary.py — Resumo de Mercado & Análise de Balanços Corporativos
Coleta notícias e análises de fontes públicas (RSS + Google News) com foco em:
- Mercado Nacional (🇧🇷 B3, FIIs, Selic) e Internacional (🌎 S&P 500, Nasdaq, Fed)
- Análise de balanços corporativos nacionais e internacionais com classificação de sentimento
- Busca ativa de opiniões e relatórios das casas/analistas indicados (Suno, VAROS, BTG, SmallCaps, etc.)
- Atualização estruturada nas 4 edições diárias (08h00, 12h00, 18h00 e 22h00 BRT)

100% à prova de falhas: utiliza ElementTree (stdlib) com fallback gracioso para feedparser.
"""

import streamlit as st
import requests
import re
import xml.etree.ElementTree as ET
from datetime import datetime, timezone, timedelta

# Importação segura de feedparser (caso não esteja instalado no container Streamlit Cloud)
try:
    import feedparser
    HAS_FEEDPARSER = True
except ImportError:
    feedparser = None
    HAS_FEEDPARSER = False


HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept": "application/rss+xml, application/xml, application/atom+xml, text/xml;q=0.9, */*;q=0.8",
}

# ─────────────────────────────────────────
# Perfis e Casas de Análise Acompanhados (X / Twitter)
# ─────────────────────────────────────────
FOLLOWED_PROFILES = [
    # Ações, Valuation e Small Caps
    {"handle": "@varosbr", "name": "VAROS", "category": "Ações & Valuation", "region": "Nacional", "desc": "Investir e multiplicar seu dinheiro com segurança"},
    {"handle": "@vowtz", "name": "Leandro Siqueira", "category": "Ações & Valuation", "region": "Nacional", "desc": "Co-founder @varosbr · Valuations"},
    {"handle": "@gerandoalfa", "name": "Lucas Schneider, CNPI", "category": "Ações & Valuation", "region": "Nacional", "desc": "Investidor Profissional"},
    {"handle": "@Kaio_GAInvest", "name": "Kaio Silva | CNPI", "category": "Ações & Valuation", "region": "Nacional", "desc": "Especialista em Análise de Ações - #GAInvest"},
    {"handle": "@renetous", "name": "Renato A. F. Reis | CNPI-P", "category": "Ações & Valuation", "region": "Nacional", "desc": "Investidor e Analista Fundamentalista na Blue3 Research"},
    {"handle": "@MalekZein7", "name": "Malek Zein, CNPI", "category": "Ações & Valuation", "region": "Nacional", "desc": "Suno Research - Equity Research Analyst"},
    {"handle": "@portalsmallcaps", "name": "SmallCaps", "category": "Ações & Valuation", "region": "Nacional", "desc": "Portal colaborativo focado nas Small Caps brasileiras"},
    {"handle": "@valor_adicionad", "name": "Valor Adicionado", "category": "Ações & Valuation", "region": "Nacional", "desc": "Estrutura produtiva, comercial e tecnológica"},
    {"handle": "@analisedeacoes", "name": "Análise de Ações", "category": "Ações & Valuation", "region": "Nacional", "desc": "Faça seu dinheiro trabalhar para você"},
    {"handle": "@CalixtoCapital", "name": "Calixto Capital", "category": "Ações & Valuation", "region": "Nacional", "desc": "TOP 4 dentre mais de 2.200 fundos de ações ativos"},
    {"handle": "@MZInvestimentos", "name": "MZ Investimentos", "category": "Ações & Valuation", "region": "Nacional", "desc": "Investidor Profissional, Empreendedor e Ciclista"},
    {"handle": "@leiatheinvestor", "name": "The Investor", "category": "Ações & Valuation", "region": "Internacional", "desc": "Truth is like poetry."},
    {"handle": "@marcelohars", "name": "marcelohars", "category": "Ações & Valuation", "region": "Nacional", "desc": "CEO da CGR - Concordia Gestão de Recursos"},

    # Macroeconomia e Notícias
    {"handle": "@MercadosBrasil", "name": "Mercados Brasil", "category": "Macroeconomia", "region": "Nacional", "desc": "Resultados e fatos relevantes das empresas listadas na bolsa"},
    {"handle": "@NotDaBolsa", "name": "Notícias da Bolsa", "category": "Macroeconomia", "region": "Nacional", "desc": "Notícias e fatos relevantes do mercado"},
    {"handle": "@fatosdabolsa", "name": "Fatos da Bolsa", "category": "Macroeconomia", "region": "Nacional", "desc": "Conteúdo educativo somente"},
    {"handle": "@robin_j_brooks", "name": "Robin Brooks", "category": "Macroeconomia", "region": "Internacional", "desc": "Senior Fellow @BrookingsInst, previously Chief Economist @IIF"},
    {"handle": "@insiderreportbr", "name": "Insider Report Brazil", "category": "Macroeconomia", "region": "Nacional", "desc": "Divulgação de movimentações de tesouraria, controlador, conselho e diretoria"},
    {"handle": "@mcmanocall", "name": "Mano Call", "category": "Macroeconomia", "region": "Nacional", "desc": "Davidson @formadores_edu"},
    {"handle": "@BurryArchive", "name": "Michael Burry Archive", "category": "Macroeconomia", "region": "Internacional", "desc": "Archive of @michaeljburry tweets"},
    {"handle": "@odanielscott", "name": "Daniel Scott", "category": "Macroeconomia", "region": "Nacional", "desc": "Negócios e Gestão"},
    {"handle": "@EconomaticaBR", "name": "Economatica", "category": "Macroeconomia", "region": "Nacional", "desc": "Plataforma de dados do mercado financeiro"},
    {"handle": "@Carlos_Parente2", "name": "Carlos Parente", "category": "Macroeconomia", "region": "Nacional", "desc": "Investimentos"},
    {"handle": "@ManfroiRenato", "name": "cansera ok", "category": "Macroeconomia", "region": "Nacional", "desc": "YouTube e conteúdo"},

    # FIIs / Fundos Imobiliários
    {"handle": "@Fiis_FI", "name": "Fundos Imobiliários", "category": "FIIs", "region": "Nacional", "desc": "Promovendo conhecimento em FII's · Renda passiva"},
    {"handle": "@dicadehoje7", "name": "Dica de Hoje", "category": "FIIs", "region": "Nacional", "desc": "Casa de Análise Top 1 pela Anbima e + de 25 anos no mercado financeiro"},

    # Análise Técnica e Cripto
    {"handle": "@LucasCostaAT", "name": "Lucas Costa, CMT", "category": "Análise Técnica", "region": "Nacional", "desc": "Head of Technical Analysis Research – BTG Pactual Investment Bank"},
    {"handle": "@ografista", "name": "O Grafista | Investidor", "category": "Análise Técnica", "region": "Nacional", "desc": "Toda Semana 1 Gráfico Para Seus Investimentos"},
    {"handle": "@TopGrafx", "name": "Nilson Marcelo | @TopGrafx", "category": "Análise Técnica", "region": "Nacional", "desc": "Analista CNPI | Mercado financeiro"},
    {"handle": "@Fernandomarxk", "name": "Fernando Marx Katz", "category": "Análise Técnica", "region": "Nacional", "desc": "Trader @ TC Cosmos FIM | Former Financial Advisor"},
    {"handle": "@CesarFrade1", "name": "CesarFrade", "category": "Análise Técnica", "region": "Nacional", "desc": "Analista e educador"},
    {"handle": "@BHM_Options", "name": "BHM Options", "category": "Opções", "region": "Nacional", "desc": "Algum conhecimento e zero didática"},
    {"handle": "@castacrypto", "name": "Castaneda", "category": "Cripto", "region": "Internacional", "desc": "Co-Founder & COO da @OxusFinance | Pagamentos globais"},
    {"handle": "@CryptoInsightsX", "name": "Crypto Insights", "category": "Cripto", "region": "Internacional", "desc": "Daily Crypto News"},
]


# ─────────────────────────────────────────
# RSS Feeds de Notícias e Análises (Nacionais & Internacionais)
# ─────────────────────────────────────────
SUMMARY_FEEDS_NACIONAL = [
    {"name": "InfoMoney",        "url": "https://www.infomoney.com.br/feed/",                                                      "icon": "📰", "region": "Nacional"},
    {"name": "Valor Econômico",  "url": "https://pox.globo.com/rss/valor/",                                                        "icon": "📰", "region": "Nacional"},
    {"name": "Money Times",      "url": "https://www.moneytimes.com.br/feed/",                                                     "icon": "📰", "region": "Nacional"},
    {"name": "Exame",            "url": "https://exame.com/feed/",                                                                 "icon": "📰", "region": "Nacional"},
    {"name": "Investing.com BR", "url": "https://br.investing.com/rss/news_285.rss",                                               "icon": "📈", "region": "Nacional"},
    {"name": "CNN Economia",     "url": "https://www.cnnbrasil.com.br/economia/feed/",                                             "icon": "📰", "region": "Nacional"},
    {"name": "Analistas & Casas", "url": "https://news.google.com/rss/search?q=VAROS+OR+Suno+Research+OR+Renato+Reis+OR+SmallCaps&hl=pt-BR&gl=BR&ceid=BR:pt-419", "icon": "👥", "region": "Nacional"},
]

SUMMARY_FEEDS_INTERNACIONAL = [
    {"name": "CNBC",             "url": "https://search.cnbc.com/rs/search/combinedcms/view.xml?partnerId=wrss01&id=10000664",    "icon": "🌎", "region": "Internacional"},
    {"name": "Yahoo Finance US", "url": "https://feeds.finance.yahoo.com/rss/2.0/headline?s=^GSPC&region=US&lang=en-US",            "icon": "🌎", "region": "Internacional"},
    {"name": "MarketWatch",      "url": "https://feeds.content.dowjones.io/public/rss/mw_topstories",                              "icon": "🌎", "region": "Internacional"},
    {"name": "Investing Global", "url": "https://www.investing.com/rss/news_1.rss",                                                "icon": "🌎", "region": "Internacional"},
    {"name": "Wall St Earnings", "url": "https://news.google.com/rss/search?q=US+earnings+quarterly+report+S%26P500&hl=en-US&gl=US&ceid=US:en", "icon": "📊", "region": "Internacional"},
    {"name": "Global Macro",     "url": "https://news.google.com/rss/search?q=Robin+Brooks+OR+Michael+Burry+OR+Federal+Reserve&hl=en-US&gl=US&ceid=US:en", "icon": "👥", "region": "Internacional"},
]

# Palavras-chave para filtrar notícias de balanços / resultados
EARNINGS_KEYWORDS = [
    "resultado", "balanço", "lucro", "prejuízo", "receita", "ebitda",
    "dividendo", "provento", "rendimento", "margem", "roe", "roa",
    "trimestre", "trimestral", "2t", "3t", "4t", "1t",
    "reportou", "registrou lucro", "registrou prejuízo",
    "guidance", "projeção", "projeções", "revisão",
    "fluxo de caixa", "capex", "dívida líquida",
    "earnings", "revenue", "profit", "loss", "eps", "quarterly", "results",
]

# Termos para classificação de sentimento
POSITIVE_TERMS = [
    "forte", "recorde", "supera", "superou", "acima", "crescimento",
    "alta", "avança", "positivo", "sólido", "robusto", "surpreende",
    "surpreendeu", "melhor", "maior", "bom resultado", "recomenda compra",
    "buy", "outperform", "overweight", "top pick", "beat", "beats",
    "distribuiu", "pagou dividendo", "aumento de dividendo",
    "lucro líquido", "margem recorde", "geração de caixa",
    "ação sobe", "dispara", "valoriza", "rally",
]

NEGATIVE_TERMS = [
    "queda", "recuo", "abaixo", "prejuízo", "fraco", "decepciona",
    "decepcionou", "pior", "menor", "ruim", "negativo", "pressão",
    "sell", "underperform", "underweight", "rebaixa", "miss", "misses",
    "reduz dividendo", "corta proventos", "suspende pagamento",
    "endividamento", "alavancagem alta", "queima de caixa",
    "ação cai", "desaba", "despenca", "tombo", "plunge", "slump",
]


def get_update_time_slot() -> dict:
    """
    Retorna a edição atual com base no horário BRT (UTC-3):
    - 08:00h (Matinal / Abertura)
    - 12:00h (Meio-Dia / Almoço)
    - 18:00h (Fechamento B3)
    - 22:00h (Noturna / Wall St & Ásia)
    """
    now_brt = datetime.now(timezone.utc) - timedelta(hours=3)
    hour = now_brt.hour

    if 5 <= hour < 11:
        slot = "08:00"
        title = "Edição Matinal (08h00)"
        icon = "🌅"
        desc = "Abertura dos mercados, prévia do dia e radar de análises"
    elif 11 <= hour < 16:
        slot = "12:00"
        title = "Edição do Meio-Dia (12h00)"
        icon = "☀️"
        desc = "Giro de mercado, parcial de ações, FIIs e câmbio"
    elif 16 <= hour < 21:
        slot = "18:00"
        title = "Edição de Fechamento (18h00)"
        icon = "🌆"
        desc = "Fechamento B3, proventos, fatos relevantes e análises do dia"
    else:
        slot = "22:00"
        title = "Edição Noturna (22h00)"
        icon = "🌙"
        desc = "Fechamento de Wall Street, balanços noturnos e perspectiva global"

    time_str = now_brt.strftime("%H:%M") + " BRT"
    date_str = now_brt.strftime("%d/%m/%Y")

    return {
        "slot": slot,
        "title": title,
        "icon": icon,
        "desc": desc,
        "time_str": time_str,
        "date_str": date_str,
    }


def _clean_title(title: str) -> str:
    """Remove tags HTML residuais e trunca títulos longos."""
    if not title:
        return ""
    title = re.sub(r"<[^>]+>", "", title)
    if len(title) > 150:
        title = title[:147] + "..."
    return title.strip()


def _clean_summary(summary: str) -> str:
    """Limpa a descrição / resumo."""
    if not summary:
        return ""
    summary = re.sub(r"<[^>]+>", "", summary)
    summary = re.sub(r"\s+", " ", summary).strip()
    if len(summary) > 300:
        summary = summary[:297] + "..."
    return summary


def _parse_feed_items(xml_content: bytes) -> list:
    """
    Parser híbrido de RSS/Atom: usa feedparser se disponível,
    ou xml.etree.ElementTree como fallback de zero dependências.
    """
    items = []

    if HAS_FEEDPARSER:
        try:
            parsed = feedparser.parse(xml_content)
            for entry in parsed.entries[:15]:
                title = _clean_title(entry.get("title", ""))
                link = entry.get("link", "#")
                summary = _clean_summary(entry.get("summary", "") or entry.get("description", ""))

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
                    items.append({
                        "title": title,
                        "link": link,
                        "summary": summary,
                        "time_ago": time_ago,
                    })
            if items:
                return items
        except Exception:
            pass

    # Fallback ElementTree (stdlib Python)
    try:
        root = ET.fromstring(xml_content)
        channel = root.find("channel")
        xml_items = channel.findall("item") if channel is not None else root.findall("item") or root.findall("{http://www.w3.org/2005/Atom}entry")

        for item in xml_items[:15]:
            title = _clean_title(item.findtext("title") or item.findtext("{http://www.w3.org/2005/Atom}title") or "")
            link = item.findtext("link") or item.findtext("{http://www.w3.org/2005/Atom}link") or "#"
            summary = _clean_summary(item.findtext("description") or item.findtext("summary") or item.findtext("{http://www.w3.org/2005/Atom}summary") or "")
            pub_date = item.findtext("pubDate") or item.findtext("published") or ""

            time_ago = "hoje"
            if pub_date:
                time_ago = pub_date[:16]

            if title:
                items.append({
                    "title": title,
                    "link": link,
                    "summary": summary,
                    "time_ago": time_ago,
                })
    except Exception:
        pass

    return items


def _classify_sentiment(title: str, summary: str) -> dict:
    """Classifica o sentimento de uma notícia de balanço como positivo, negativo ou misto."""
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
    """Tenta extrair o ticker (ex: PETR4, AAPL) ou nome da empresa do título."""
    b3_match = re.search(r'\b([A-Z]{4}\d{1,2})\b', title.upper())
    if b3_match:
        return b3_match.group(1)

    us_match = re.search(r'\(([A-Z]{2,5})\)', title)
    if us_match:
        return us_match.group(1)

    company_match = re.search(r'^([A-ZÀ-ÚÇ][a-zà-úç&\s\.]+?)(?:\s+(?:registr|report|anunci|divulg|luc|prej|tem|apresent|beats|misses))', title)
    if company_match:
        return company_match.group(1).strip()

    words = title.split()
    if words and len(words[0]) >= 3 and words[0][0].isupper():
        return words[0].rstrip(",.:;")

    return ""


def _fetch_feed_group(feed_list: list) -> list:
    """Busca e intercala notícias de um grupo de feeds."""
    feed_buckets = []
    for feed_info in feed_list:
        try:
            resp = requests.get(feed_info["url"], headers=HEADERS, timeout=6)
            if resp.status_code == 200:
                entries = _parse_feed_items(resp.content)
                bucket = []
                for entry in entries:
                    bucket.append({
                        "title": entry["title"],
                        "summary": entry["summary"],
                        "link": entry["link"],
                        "source": feed_info["name"],
                        "time_ago": entry["time_ago"],
                        "icon": feed_info["icon"],
                        "region": feed_info["region"],
                    })
                if bucket:
                    feed_buckets.append(bucket)
        except Exception:
            continue

    all_entries = []
    max_len = max((len(b) for b in feed_buckets), default=0)
    for i in range(max_len):
        for bucket in feed_buckets:
            if i < len(bucket):
                all_entries.append(bucket[i])

    seen = set()
    unique = []
    for item in all_entries:
        key = item["title"][:45].lower()
        if key not in seen:
            seen.add(key)
            unique.append(item)

    return unique


@st.cache_data(ttl=1800, show_spinner=False)
def get_market_summary(region: str = "Todos", max_items: int = 15) -> list:
    """
    Coleta resumo geral do mercado via RSS.
    Se region == "Todos", intercala estritamente 1 item Nacional (🇧🇷) e 1 item Internacional (🌎)
    para garantir que ambas as esferas estejam sempre presentes de forma equilibrada.
    """
    if region == "Nacional":
        return _fetch_feed_group(SUMMARY_FEEDS_NACIONAL)[:max_items]
    elif region == "Internacional":
        return _fetch_feed_group(SUMMARY_FEEDS_INTERNACIONAL)[:max_items]

    # region == "Todos": Intercalar 1-a-1 Nacional e Internacional
    nac_items = _fetch_feed_group(SUMMARY_FEEDS_NACIONAL)
    int_items = _fetch_feed_group(SUMMARY_FEEDS_INTERNACIONAL)

    combined = []
    max_idx = max(len(nac_items), len(int_items))
    seen = set()

    for i in range(max_idx):
        if i < len(nac_items):
            key = nac_items[i]["title"][:45].lower()
            if key not in seen:
                seen.add(key)
                combined.append(nac_items[i])
        if i < len(int_items):
            key = int_items[i]["title"][:45].lower()
            if key not in seen:
                seen.add(key)
                combined.append(int_items[i])

    return combined[:max_items]


@st.cache_data(ttl=1800, show_spinner=False)
def get_earnings_analysis(region: str = "Todos", max_items: int = 12) -> list:
    """
    Coleta análises de balanços corporativos (nacionais e internacionais) com classificação de sentimento.
    Suporta filtro por região: 'Todos', 'Nacional', 'Internacional'.
    """
    earnings_feeds = [
        {"name": "InfoMoney",        "url": "https://www.infomoney.com.br/feed/",                                                                "icon": "📊", "region": "Nacional"},
        {"name": "Valor Econômico",  "url": "https://pox.globo.com/rss/valor/",                                                                  "icon": "📊", "region": "Nacional"},
        {"name": "Money Times",      "url": "https://www.moneytimes.com.br/feed/",                                                               "icon": "📊", "region": "Nacional"},
        {"name": "Investing.com BR", "url": "https://br.investing.com/rss/news_285.rss",                                                         "icon": "📊", "region": "Nacional"},
        {"name": "Analistas B3",     "url": "https://news.google.com/rss/search?q=balan%C3%A7o+resultado+lucro+preju%C3%ADzo+B3&hl=pt-BR&gl=BR&ceid=BR:pt-419", "icon": "📊", "region": "Nacional"},
        {"name": "Wall St Earnings", "url": "https://news.google.com/rss/search?q=US+earnings+quarterly+report+revenue+S%26P500&hl=en-US&gl=US&ceid=US:en", "icon": "🌎", "region": "Internacional"},
        {"name": "CNBC Earnings",    "url": "https://search.cnbc.com/rs/search/combinedcms/view.xml?partnerId=wrss01&id=10000664",            "icon": "🌎", "region": "Internacional"},
    ]

    if region != "Todos":
        earnings_feeds = [f for f in earnings_feeds if f["region"] == region]

    all_earnings = []

    for feed_info in earnings_feeds:
        try:
            resp = requests.get(feed_info["url"], headers=HEADERS, timeout=6)
            if resp.status_code == 200:
                entries = _parse_feed_items(resp.content)
                for entry in entries:
                    title = entry["title"]
                    summary = entry["summary"]
                    link = entry["link"]
                    time_ago = entry["time_ago"]

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
                            "region": feed_info["region"],
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

    # Ordenar: negativos primeiro, depois mistos, depois positivos
    sentiment_order = {"Negativo": 0, "Misto": 1, "Positivo": 2, "Neutro": 3}
    unique.sort(key=lambda x: sentiment_order.get(x["sentiment"]["label"], 4))

    return unique[:max_items]


def get_followed_profiles(region: str = "Todos") -> dict:
    """Retorna os perfis acompanhados organizados por categoria e região."""
    categories = {}
    for p in FOLLOWED_PROFILES:
        if region != "Todos" and p["region"] != region:
            continue
        cat = p["category"]
        if cat not in categories:
            categories[cat] = []
        categories[cat].append(p)
    return categories
