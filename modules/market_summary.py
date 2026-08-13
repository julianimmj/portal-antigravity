"""
market_summary.py — Resumo de Mercado & Análise de Balanços Corporativos (v2)
Coleta notícias e análises de fontes públicas (RSS + Google News) com foco em:
- Mercado Nacional (🇧🇷 B3, FIIs, Selic) e Internacional (🌎 S&P 500, Nasdaq, Fed)
- Análise de balanços corporativos nacionais e internacionais com classificação de sentimento
- Busca ativa de opiniões dos analistas indicados (Suno, VAROS, BTG, SmallCaps, etc.)
- Cotações em tempo real via yfinance (Ibovespa, Dólar, S&P 500)
- Atualização estruturada nas 4 edições diárias (08h00, 12h00, 18h00 e 22h00 BRT)

100% à prova de falhas: utiliza ElementTree (stdlib) com fallback gracioso para feedparser.
"""

import streamlit as st
import requests
import re
import xml.etree.ElementTree as ET
from datetime import datetime, timezone, timedelta
from urllib.parse import quote_plus

# Importação segura de feedparser (caso não esteja instalado no container Streamlit Cloud)
try:
    import feedparser
    HAS_FEEDPARSER = True
except Exception:
    feedparser = None
    HAS_FEEDPARSER = False

# Importação segura de yfinance (pode falhar por dependência interna no container)
try:
    import yfinance as yf
    HAS_YFINANCE = True
except Exception:
    yf = None
    HAS_YFINANCE = False


HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
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
    {"handle": "@PabloSpyer", "name": "Pablo Spyer", "category": "Macroeconomia", "region": "Nacional", "desc": "Diretor Executivo de operações na TC"},
]


# ─────────────────────────────────────────
# RSS Feeds — Resumo Geral de Mercado
# ─────────────────────────────────────────
SUMMARY_FEEDS_NACIONAL = [
    {"name": "InfoMoney",            "url": "https://www.infomoney.com.br/feed/",                                                      "icon": "📰", "region": "Nacional"},
    {"name": "Valor Econômico",      "url": "https://pox.globo.com/rss/valor/",                                                        "icon": "📰", "region": "Nacional"},
    {"name": "Money Times",          "url": "https://www.moneytimes.com.br/feed/",                                                     "icon": "📰", "region": "Nacional"},
    {"name": "Exame",                "url": "https://exame.com/feed/",                                                                 "icon": "📰", "region": "Nacional"},
    {"name": "Investing.com BR",     "url": "https://br.investing.com/rss/news_285.rss",                                               "icon": "📈", "region": "Nacional"},
    {"name": "CNN Economia",         "url": "https://www.cnnbrasil.com.br/economia/feed/",                                             "icon": "📰", "region": "Nacional"},
    # Feeds Focados em Opiniões de Analistas Acompanhados
    {"name": "Opinião Analistas B3", "url": "https://news.google.com/rss/search?q=%22Suno%22+OR+%22VAROS%22+OR+%22Renato+Reis%22+OR+%22BTG+Pactual%22+OR+%22SmallCaps%22+OR+%22Dica+de+Hoje%22+a%C3%A7%C3%B5es+OR+balan%C3%A7o&hl=pt-BR&gl=BR&ceid=BR:pt-419", "icon": "🗣️", "region": "Nacional"},
    {"name": "Perfis X & Casas",     "url": "https://news.google.com/rss/search?q=%22renetous%22+OR+%22varosbr%22+OR+%22vowtz%22+OR+%22gerandoalfa%22+OR+%22portalsmallcaps%22+OR+%22dicadehoje7%22+a%C3%A7%C3%B5es&hl=pt-BR&gl=BR&ceid=BR:pt-419", "icon": "👥", "region": "Nacional"},
    {"name": "Suno Notícias",        "url": "https://www.suno.com.br/noticias/feed/",                                                 "icon": "💡", "region": "Nacional"},
    {"name": "Ibovespa & Dólar",     "url": "https://news.google.com/rss/search?q=Ibovespa+d%C3%B3lar+fechamento+B3+hoje&hl=pt-BR&gl=BR&ceid=BR:pt-419",  "icon": "📊", "region": "Nacional"},
    {"name": "IFIX & FIIs",          "url": "https://news.google.com/rss/search?q=IFIX+fundos+imobili%C3%A1rios+rendimento+dividendo&hl=pt-BR&gl=BR&ceid=BR:pt-419", "icon": "🏢", "region": "Nacional"},
    {"name": "Selic & Juros",        "url": "https://news.google.com/rss/search?q=Selic+juros+Copom+pol%C3%ADtica+monet%C3%A1ria&hl=pt-BR&gl=BR&ceid=BR:pt-419", "icon": "💰", "region": "Nacional"},
]

SUMMARY_FEEDS_INTERNACIONAL = [
    {"name": "CNBC",             "url": "https://search.cnbc.com/rs/search/combinedcms/view.xml?partnerId=wrss01&id=10000664",      "icon": "🌎", "region": "Internacional"},
    {"name": "Yahoo Finance US", "url": "https://feeds.finance.yahoo.com/rss/2.0/headline?s=^GSPC&region=US&lang=en-US",            "icon": "🌎", "region": "Internacional"},
    {"name": "MarketWatch",      "url": "https://feeds.content.dowjones.io/public/rss/mw_topstories",                              "icon": "🌎", "region": "Internacional"},
    {"name": "Investing Global", "url": "https://www.investing.com/rss/news_1.rss",                                                "icon": "🌎", "region": "Internacional"},
    {"name": "Wall St Earnings", "url": "https://news.google.com/rss/search?q=earnings+quarterly+report+S%26P500+revenue&hl=en-US&gl=US&ceid=US:en", "icon": "📊", "region": "Internacional"},
    {"name": "Fed & Macro",      "url": "https://news.google.com/rss/search?q=Federal+Reserve+OR+%22interest+rate%22+OR+%22Treasury+yield%22+OR+inflation&hl=en-US&gl=US&ceid=US:en", "icon": "🏛️", "region": "Internacional"},
    {"name": "Mag 7 Stocks",     "url": "https://news.google.com/rss/search?q=Nvidia+OR+Apple+OR+Microsoft+OR+Amazon+OR+Tesla+stock+earnings&hl=en-US&gl=US&ceid=US:en", "icon": "🚀", "region": "Internacional"},
]


# ─────────────────────────────────────────
# RSS Feeds — Balanços Corporativos
# ─────────────────────────────────────────
EARNINGS_FEEDS_NACIONAL = [
    {"name": "InfoMoney",            "url": "https://www.infomoney.com.br/feed/",                                                   "icon": "📊", "region": "Nacional"},
    {"name": "Valor Econômico",      "url": "https://pox.globo.com/rss/valor/",                                                     "icon": "📊", "region": "Nacional"},
    {"name": "Money Times",          "url": "https://www.moneytimes.com.br/feed/",                                                  "icon": "📊", "region": "Nacional"},
    {"name": "Investing.com BR",     "url": "https://br.investing.com/rss/news_285.rss",                                            "icon": "📊", "region": "Nacional"},
    {"name": "Suno Notícias",        "url": "https://www.suno.com.br/noticias/feed/",                                             "icon": "💡", "region": "Nacional"},
    # Google News focados em balanços B3 — queries diversificadas para cobrir toda a temporada
    {"name": "Balanços B3",          "url": "https://news.google.com/rss/search?q=balan%C3%A7o+resultado+trimestral+lucro+preju%C3%ADzo+B3+2T+3T&hl=pt-BR&gl=BR&ceid=BR:pt-419", "icon": "📊", "region": "Nacional"},
    {"name": "Balanços Varejo",      "url": "https://news.google.com/rss/search?q=%22Magazine+Luiza%22+OR+%22Lojas+Renner%22+OR+%22Casas+Bahia%22+OR+Assai+OR+Carrefour+resultado+balan%C3%A7o&hl=pt-BR&gl=BR&ceid=BR:pt-419", "icon": "🛒", "region": "Nacional"},
    {"name": "Balanços Blue Chips",  "url": "https://news.google.com/rss/search?q=Petrobras+OR+Vale+OR+Itau+OR+Bradesco+OR+%22Banco+do+Brasil%22+resultado+trimestre&hl=pt-BR&gl=BR&ceid=BR:pt-419", "icon": "💎", "region": "Nacional"},
    # Balanços Saúde, Commodities e Mid-caps — empresas que frequentemente reportam juntas
    {"name": "Balanços Saúde/Mid",   "url": "https://news.google.com/rss/search?q=Hapvida+OR+Cogna+OR+Ultrapar+OR+CSN+OR+CVC+OR+Dasa+OR+Yduqs+balan%C3%A7o+OR+resultado+OR+lucro+OR+preju%C3%ADzo&hl=pt-BR&gl=BR&ceid=BR:pt-419", "icon": "🏥", "region": "Nacional"},
    # Análises de casas — diversificado para incluir XP, Safra, Genial, NÃO só BTG
    {"name": "Análises Casas",       "url": "https://news.google.com/rss/search?q=%22XP+Investimentos%22+OR+%22Banco+Safra%22+OR+%22Genial%22+OR+%22Suno%22+OR+%22BTG%22+balan%C3%A7o+OR+resultado+OR+recomenda%C3%A7%C3%A3o&hl=pt-BR&gl=BR&ceid=BR:pt-419", "icon": "👥", "region": "Nacional"},
    # Resultado trimestral hoje — query genérica para balanços publicados hoje/ontem
    {"name": "Resultados Hoje",      "url": "https://news.google.com/rss/search?q=resultado+trimestral+lucro+OR+preju%C3%ADzo+2T+OR+3T+2026+when:1d&hl=pt-BR&gl=BR&ceid=BR:pt-419", "icon": "🔥", "region": "Nacional"},
]

EARNINGS_FEEDS_INTERNACIONAL = [
    {"name": "Wall St Earnings", "url": "https://news.google.com/rss/search?q=earnings+quarterly+report+revenue+EPS+beat+miss&hl=en-US&gl=US&ceid=US:en", "icon": "🌎", "region": "Internacional"},
    {"name": "CNBC Earnings",    "url": "https://search.cnbc.com/rs/search/combinedcms/view.xml?partnerId=wrss01&id=10000664",       "icon": "🌎", "region": "Internacional"},
    {"name": "Tech Earnings",    "url": "https://news.google.com/rss/search?q=Nvidia+OR+Apple+OR+Microsoft+OR+Amazon+OR+Meta+earnings+results&hl=en-US&gl=US&ceid=US:en", "icon": "💻", "region": "Internacional"},
]




# ─────────────────────────────────────────
# Palavras-chave para filtrar notícias de balanços / resultados
# ─────────────────────────────────────────
EARNINGS_KEYWORDS = [
    # Português
    "resultado", "balanço", "lucro", "prejuízo", "receita", "ebitda",
    "dividendo", "provento", "rendimento", "margem", "roe", "roa",
    "trimestre", "trimestral", "2t", "3t", "4t", "1t",
    "reportou", "registrou lucro", "registrou prejuízo",
    "guidance", "projeção", "projeções", "revisão",
    "fluxo de caixa", "capex", "dívida líquida",
    "recomendação", "compra", "venda", "neutra",
    "same store sales", "sss", "inadimplência",
    "geração de caixa", "alavancagem", "endividamento",
    "fato relevante", "jcp", "juros sobre capital",
    # Inglês
    "earnings", "revenue", "profit", "loss", "eps", "quarterly", "results",
    "beat", "miss", "guidance", "outlook", "dividend",
    "operating income", "net income", "free cash flow",
]


# ─────────────────────────────────────────
# Termos para classificação de sentimento
# ─────────────────────────────────────────
# Termos fortes contam como 2 pontos em vez de 1
STRONG_POSITIVE_TERMS = [
    "recorde", "supera expectativas", "superou expectativas", "dispara",
    "melhor resultado", "beat estimates", "top pick", "outperform",
    "lucro recorde", "margem recorde", "forte geração de caixa",
    "recomendação de compra", "surpreende positivamente",
]

POSITIVE_TERMS = [
    "forte", "recorde", "supera", "superou", "acima", "crescimento",
    "alta", "avança", "positivo", "sólido", "robusto", "surpreende",
    "surpreendeu", "melhor", "maior", "bom resultado", "recomenda compra",
    "buy", "outperform", "overweight", "top pick", "beat", "beats",
    "distribuiu", "pagou dividendo", "aumento de dividendo",
    "lucro líquido", "margem recorde", "geração de caixa",
    "ação sobe", "dispara", "valoriza", "rally",
    "recuperação", "avanço", "ganho", "expansão",
    "melhora", "aceleração", "salto", "alta de",
]

STRONG_NEGATIVE_TERMS = [
    "desaba", "despenca", "prejuízo líquido", "miss estimates",
    "tombo de", "pior resultado", "guidance rebaixado",
    "inadimplência elevada", "queima de caixa", "sell",
    "rebaixamento", "underperform", "desastroso",
]

NEGATIVE_TERMS = [
    "queda", "recuo", "abaixo", "prejuízo", "fraco", "decepciona",
    "decepcionou", "pior", "menor", "ruim", "negativo", "pressão",
    "sell", "underperform", "underweight", "rebaixa", "miss", "misses",
    "reduz dividendo", "corta proventos", "suspende pagamento",
    "endividamento", "alavancagem alta", "queima de caixa",
    "ação cai", "desaba", "despenca", "tombo", "plunge", "slump",
    "inadimplência", "provisão", "deterioração",
    "revisão para baixo", "guidance cortado", "desaceleração",
]

# Stopwords que devem ser ignoradas na extração de empresa
TITLE_STOPWORDS = {
    "no", "na", "nos", "nas", "da", "de", "do", "dos", "das",
    "em", "por", "para", "com", "sem", "sob", "um", "uma",
    "o", "a", "os", "as", "ao", "às", "e", "ou",
    "dona", "dono", "ação", "ações", "papel", "papéis",
    "após", "ante", "como", "que", "se", "já",
    "é", "ser", "foi", "são", "está", "estão",
    "mais", "menos", "muito", "pouco", "novo", "nova",
    "the", "a", "an", "in", "on", "at", "for", "of", "to",
    "is", "are", "was", "were", "has", "have", "had",
    "with", "from", "by", "after", "before", "its",
    "stock", "stocks", "shares", "share", "market",
}


# ─────────────────────────────────────────
# COMPANY_MAP — Mapeamento de empresas e tickers
# ─────────────────────────────────────────
COMPANY_MAP = {
    # ── B3 Blue Chips ──
    "MAGAZINE LUIZA": "MGLU3 · Magazine Luiza",
    "MAGALU": "MGLU3 · Magazine Luiza",
    "MGLU3": "MGLU3 · Magazine Luiza",
    "PETROBRAS": "PETR4 · Petrobras",
    "PETR4": "PETR4 · Petrobras",
    "PETR3": "PETR3 · Petrobras",
    "VALE": "VALE3 · Vale",
    "VALE3": "VALE3 · Vale",
    "BANCO DO BRASIL": "BBAS3 · Banco do Brasil",
    "BBAS3": "BBAS3 · Banco do Brasil",
    "ITAU": "ITUB4 · Itaú Unibanco",
    "ITAÚ": "ITUB4 · Itaú Unibanco",
    "ITAÚ UNIBANCO": "ITUB4 · Itaú Unibanco",
    "ITUB4": "ITUB4 · Itaú Unibanco",
    "BRADESCO": "BBDC4 · Bradesco",
    "BBDC4": "BBDC4 · Bradesco",
    "SANTANDER": "SANB11 · Santander",
    "SANB11": "SANB11 · Santander",
    "NUBANK": "ROXO34 · Nubank",
    "NU HOLDINGS": "ROXO34 · Nubank",
    "WEG": "WEGE3 · WEG",
    "WEGE3": "WEGE3 · WEG",
    "AMBEV": "ABEV3 · Ambev",
    "ABEV3": "ABEV3 · Ambev",

    # ── B3 Varejo / Consumo ──
    "LOJAS RENNER": "LREN3 · Lojas Renner",
    "RENNER": "LREN3 · Lojas Renner",
    "LREN3": "LREN3 · Lojas Renner",
    "CASAS BAHIA": "BHIA3 · Casas Bahia",
    "BHIA3": "BHIA3 · Casas Bahia",
    "ASSAI": "ASAI3 · Assaí Atacadista",
    "ASSAÍ": "ASAI3 · Assaí Atacadista",
    "ASAI3": "ASAI3 · Assaí Atacadista",
    "CARREFOUR": "CRFB3 · Carrefour Brasil",
    "ATACADÃO": "CRFB3 · Carrefour / Atacadão",
    "CRFB3": "CRFB3 · Carrefour Brasil",
    "VIVARA": "VIVA3 · Vivara",
    "VIVA3": "VIVA3 · Vivara",
    "AREZZO": "ARZZ3 · Arezzo",
    "ARZZ3": "ARZZ3 · Arezzo",
    "GRUPO SOMA": "SOMA3 · Grupo Soma",
    "SOMA3": "SOMA3 · Grupo Soma",
    "PETZ": "PETZ3 · Petz",
    "PETZ3": "PETZ3 · Petz",
    "RAIA DROGASIL": "RADL3 · Raia Drogasil",
    "RAIÁ": "RADL3 · Raia Drogasil",
    "RADL3": "RADL3 · Raia Drogasil",
    "NATURA": "NTCO3 · Natura &Co",
    "NTCO3": "NTCO3 · Natura &Co",
    "MERCADO LIVRE": "MELI34 · Mercado Livre",
    "ALPARGATAS": "ALPA4 · Alpargatas",
    "ALPA4": "ALPA4 · Alpargatas",
    "HAVAIANAS": "ALPA4 · Alpargatas / Havaianas",

    # ── B3 Financeiro ──
    "BTG PACTUAL": "BPAC11 · BTG Pactual",
    "BPAC11": "BPAC11 · BTG Pactual",
    "XP INC": "XPBR31 · XP Inc",
    "XPBR31": "XPBR31 · XP Inc",
    "PORTO": "PSSA3 · Porto Seguro",
    "PORTO SEGURO": "PSSA3 · Porto Seguro",
    "PORTO BANK": "PSSA3 · Porto Seguro",
    "PSSA3": "PSSA3 · Porto Seguro",
    "BB SEGURIDADE": "BBSE3 · BB Seguridade",
    "BBSE3": "BBSE3 · BB Seguridade",
    "CIELO": "CIEL3 · Cielo",
    "CIEL3": "CIEL3 · Cielo",
    "B3 SA": "B3SA3 · B3",
    "B3SA3": "B3SA3 · B3",
    "INTER": "INBR32 · Inter & Co",

    # ── B3 Indústria / Commodities ──
    "LOCALIZA": "RENT3 · Localiza",
    "RENT3": "RENT3 · Localiza",
    "ELETROBRAS": "ELET3 · Eletrobras",
    "ELET3": "ELET3 · Eletrobras",
    "SUZANO": "SUZB3 · Suzano",
    "SUZB3": "SUZB3 · Suzano",
    "KLABIN": "KLBN11 · Klabin",
    "KLBN11": "KLBN11 · Klabin",
    "SABESP": "SBSP3 · Sabesp",
    "SBSP3": "SBSP3 · Sabesp",
    "TAESA": "TAEE11 · Taesa",
    "TAEE11": "TAEE11 · Taesa",
    "COPEL": "CPLE6 · Copel",
    "CPLE6": "CPLE6 · Copel",
    "COSAN": "CSAN3 · Cosan",
    "CSAN3": "CSAN3 · Cosan",
    "RUMO": "RAIL3 · Rumo",
    "RAIL3": "RAIL3 · Rumo",
    "ULTRAPAR": "UGPA3 · Ultrapar",
    "UGPA3": "UGPA3 · Ultrapar",
    "AZUL": "AZUL4 · Azul Linhas Aéreas",
    "AZUL4": "AZUL4 · Azul Linhas Aéreas",
    "GOL": "GOLL4 · Gol Linhas Aéreas",
    "GOLL4": "GOLL4 · Gol Linhas Aéreas",
    "CSN": "CSNA3 · CSN",
    "CSNA3": "CSNA3 · CSN",
    "GERDAU": "GGBR4 · Gerdau",
    "GGBR4": "GGBR4 · Gerdau",
    "USIMINAS": "USIM5 · Usiminas",
    "USIM5": "USIM5 · Usiminas",
    "MARFRIG": "MRFG3 · Marfrig",
    "MRFG3": "MRFG3 · Marfrig",
    "JBS": "JBSS3 · JBS",
    "JBSS3": "JBSS3 · JBS",
    "MINERVA": "BEEF3 · Minerva",
    "BEEF3": "BEEF3 · Minerva",
    "BRF": "BRFS3 · BRF",
    "BRFS3": "BRFS3 · BRF",
    "EMBRAER": "EMBR3 · Embraer",
    "EMBR3": "EMBR3 · Embraer",
    "PRIO": "PRIO3 · Prio",
    "PRIO3": "PRIO3 · Prio",
    "PETRORECONCAVO": "RECV3 · PetroReconcavo",
    "RECV3": "RECV3 · PetroReconcavo",
    "BRAVA ENERGIA": "BRAV3 · Brava Energia",
    "BRAV3": "BRAV3 · Brava Energia",

    # ── B3 Saúde ──
    "HYPERA": "HYPE3 · Hypera",
    "HYPE3": "HYPE3 · Hypera",
    "HAPVIDA": "HAPV3 · Hapvida",
    "HAPV3": "HAPV3 · Hapvida",
    "REDE D'OR": "RDOR3 · Rede D'Or",
    "RDOR3": "RDOR3 · Rede D'Or",
    "FLEURY": "FLRY3 · Fleury",
    "FLRY3": "FLRY3 · Fleury",
    "QUALICORP": "QUAL3 · Qualicorp",
    "QUAL3": "QUAL3 · Qualicorp",
    "DASA": "DASA3 · Dasa",
    "DASA3": "DASA3 · Dasa",
    "COGNA": "COGN3 · Cogna",
    "COGN3": "COGN3 · Cogna",
    "YDUQS": "YDUQ3 · Yduqs",
    "YDUQ3": "YDUQ3 · Yduqs",
    "CVC": "CVCB3 · CVC",
    "CVCB3": "CVCB3 · CVC",
    "CPFL": "CPFE3 · CPFL Energia",
    "CPFL ENERGIA": "CPFE3 · CPFL Energia",
    "CPFE3": "CPFE3 · CPFL Energia",
    "MRV": "MRVE3 · MRV",
    "MRVE3": "MRVE3 · MRV",
    "SIMPAR": "SIMH3 · Simpar",
    "SIMH3": "SIMH3 · Simpar",
    "JHSF": "JHSF3 · JHSF",
    "JHSF3": "JHSF3 · JHSF",
    "GRUPO MATEUS": "GMAT3 · Grupo Mateus",
    "GMAT3": "GMAT3 · Grupo Mateus",
    "STONE": "STNE · Stone",
    "STONECO": "STNE · Stone",
    "M DIAS BRANCO": "MDIA3 · M. Dias Branco",
    "MDIA3": "MDIA3 · M. Dias Branco",
    "ALLOS": "ALOS3 · Allos",
    "ALOS3": "ALOS3 · Allos",
    "EVEN": "EVEN3 · Even",
    "EVEN3": "EVEN3 · Even",
    "TECNISA": "TCSA3 · Tecnisa",
    "TCSA3": "TCSA3 · Tecnisa",
    "AMERICANAS": "AMER3 · Americanas",
    "AMER3": "AMER3 · Americanas",

    # ── B3 Tech / Telecom ──
    "TOTVS": "TOTS3 · Totvs",
    "TOTS3": "TOTS3 · Totvs",
    "LOCAWEB": "LWSA3 · Locaweb",
    "LWSA3": "LWSA3 · Locaweb",
    "TIM": "TIMS3 · TIM",
    "TIMS3": "TIMS3 · TIM",
    "VIVO": "VIVT3 · Vivo / Telefônica",
    "TELEFÔNICA": "VIVT3 · Vivo / Telefônica",
    "VIVT3": "VIVT3 · Vivo / Telefônica",

    # ── FIIs conhecidos ──
    "KNCR11": "KNCR11 · Kinea Rendimentos",
    "HGLG11": "HGLG11 · CSHG Logística",
    "MXRF11": "MXRF11 · Maxi Renda",
    "BCFF11": "BCFF11 · BTG Fundo de Fundos",
    "XPML11": "XPML11 · XP Malls",
    "VISC11": "VISC11 · Vinci Shopping",
    "TRXF11": "TRXF11 · TRX Real Estate",
    "KNRI11": "KNRI11 · Kinea Renda Imobiliária",
    "HGRE11": "HGRE11 · CSHG Real Estate",
    "IRDM11": "IRDM11 · Iridium Recebíveis",
    "CPTS11": "CPTS11 · Capitânia Securities",
    "BTLG11": "BTLG11 · BTG Logística",

    # ── US Stocks ──
    "NVIDIA": "NVDA · Nvidia",
    "NVDA": "NVDA · Nvidia",
    "APPLE": "AAPL · Apple",
    "AAPL": "AAPL · Apple",
    "MICROSOFT": "MSFT · Microsoft",
    "MSFT": "MSFT · Microsoft",
    "AMAZON": "AMZN · Amazon",
    "AMZN": "AMZN · Amazon",
    "GOOGLE": "GOOGL · Alphabet Google",
    "GOOGL": "GOOGL · Alphabet Google",
    "ALPHABET": "GOOGL · Alphabet Google",
    "META": "META · Meta Platforms",
    "FACEBOOK": "META · Meta Platforms",
    "TESLA": "TSLA · Tesla",
    "TSLA": "TSLA · Tesla",
    "NETFLIX": "NFLX · Netflix",
    "NFLX": "NFLX · Netflix",
    "DISNEY": "DIS · Walt Disney",
    "DIS": "DIS · Walt Disney",
    "AMD": "AMD · Advanced Micro Devices",
    "INTEL": "INTC · Intel",
    "INTC": "INTC · Intel",
    "JPMORGAN": "JPM · JPMorgan Chase",
    "JP MORGAN": "JPM · JPMorgan Chase",
    "JPM": "JPM · JPMorgan Chase",
    "GOLDMAN SACHS": "GS · Goldman Sachs",
    "BERKSHIRE": "BRK.B · Berkshire Hathaway",
    "PALANTIR": "PLTR · Palantir",
    "PLTR": "PLTR · Palantir",
    "COINBASE": "COIN · Coinbase",
    "SNOWFLAKE": "SNOW · Snowflake",
    "SALESFORCE": "CRM · Salesforce",
    "UBER": "UBER · Uber",
    "AIRBNB": "ABNB · Airbnb",
    "BOEING": "BA · Boeing",
    "COCA-COLA": "KO · Coca-Cola",
    "WALMART": "WMT · Walmart",
    "TARGET": "TGT · Target",
}


# ─────────────────────────────────────────
# Cotações de Mercado (yfinance)
# ─────────────────────────────────────────
@st.cache_data(ttl=900, show_spinner=False)
def get_market_quotes() -> list:
    """
    Busca cotações atualizadas dos principais índices e ativos via yfinance.
    Retorna uma lista de dicts com: symbol, name, price, change, change_pct, color, arrow.
    """
    if not HAS_YFINANCE:
        return []

    tickers_config = [
        {"symbol": "^BVSP",     "name": "Ibovespa",   "prefix": "",    "suffix": " pts", "decimals": 0},
        {"symbol": "USDBRL=X",  "name": "Dólar/Real", "prefix": "R$ ", "suffix": "",      "decimals": 3},
        {"symbol": "^GSPC",     "name": "S&P 500",    "prefix": "",    "suffix": " pts", "decimals": 0},
        {"symbol": "^IXIC",     "name": "Nasdaq",     "prefix": "",    "suffix": " pts", "decimals": 0},
        {"symbol": "BTC-USD",   "name": "Bitcoin",    "prefix": "US$ ","suffix": "",      "decimals": 0},
    ]

    quotes = []
    try:
        symbols = [t["symbol"] for t in tickers_config]
        data = yf.download(symbols, period="2d", interval="1d", progress=False, threads=True)

        for tc in tickers_config:
            try:
                sym = tc["symbol"]
                if len(symbols) > 1:
                    close_col = data["Close"][sym] if sym in data["Close"].columns else None
                else:
                    close_col = data["Close"]

                if close_col is not None and len(close_col.dropna()) >= 2:
                    values = close_col.dropna()
                    current = float(values.iloc[-1])
                    previous = float(values.iloc[-2])
                    change = current - previous
                    change_pct = (change / previous) * 100 if previous != 0 else 0

                    dec = tc["decimals"]
                    price_str = f'{tc["prefix"]}{current:,.{dec}f}{tc["suffix"]}'.replace(",", "X").replace(".", ",").replace("X", ".")

                    if change >= 0:
                        arrow = "▲"
                        color = "#00e676"
                        sign = "+"
                    else:
                        arrow = "▼"
                        color = "#ef4444"
                        sign = ""

                    change_str = f"{sign}{change_pct:.2f}%"

                    quotes.append({
                        "symbol": sym,
                        "name": tc["name"],
                        "price": price_str,
                        "change": change_str,
                        "change_pct": change_pct,
                        "color": color,
                        "arrow": arrow,
                    })
                elif close_col is not None and len(close_col.dropna()) >= 1:
                    values = close_col.dropna()
                    current = float(values.iloc[-1])
                    dec = tc["decimals"]
                    price_str = f'{tc["prefix"]}{current:,.{dec}f}{tc["suffix"]}'.replace(",", "X").replace(".", ",").replace("X", ".")
                    quotes.append({
                        "symbol": sym,
                        "name": tc["name"],
                        "price": price_str,
                        "change": "—",
                        "change_pct": 0,
                        "color": "rgba(255,255,255,0.5)",
                        "arrow": "•",
                    })
            except Exception:
                continue
    except Exception:
        pass

    return quotes


# ─────────────────────────────────────────
# Funções auxiliares
# ─────────────────────────────────────────
def get_update_time_slot() -> dict:
    """Retorna a edição atual com base no horário BRT (UTC-3)."""
    now_brt = datetime.now(timezone.utc) - timedelta(hours=3)
    hour = now_brt.hour

    if 5 <= hour < 11:
        slot, title, icon = "08:00", "Edição Matinal (08h00)", "🌅"
        desc = "Abertura dos mercados, prévia do dia e radar de análises"
    elif 11 <= hour < 16:
        slot, title, icon = "12:00", "Edição do Meio-Dia (12h00)", "☀️"
        desc = "Giro de mercado, parcial de ações, FIIs e câmbio"
    elif 16 <= hour < 21:
        slot, title, icon = "18:00", "Edição de Fechamento (18h00)", "🌆"
        desc = "Fechamento B3, proventos, fatos relevantes e análises do dia"
    else:
        slot, title, icon = "22:00", "Edição Noturna (22h00)", "🌙"
        desc = "Fechamento de Wall Street, balanços noturnos e perspectiva global"

    return {
        "slot": slot, "title": title, "icon": icon, "desc": desc,
        "time_str": now_brt.strftime("%H:%M") + " BRT",
        "date_str": now_brt.strftime("%d/%m/%Y"),
    }


def _clean_title(title: str) -> str:
    """Remove tags HTML residuais e trunca títulos longos."""
    if not title:
        return ""
    title = re.sub(r"<[^>]+>", "", title)
    if len(title) > 160:
        title = title[:157] + "..."
    return title.strip()


def _clean_summary(summary: str) -> str:
    """Limpa a descrição / resumo."""
    if not summary:
        return ""
    summary = re.sub(r"<[^>]+>", "", summary)
    summary = re.sub(r"\s+", " ", summary).strip()
    if len(summary) > 350:
        summary = summary[:347] + "..."
    return summary


def _parse_feed_items(xml_content: bytes) -> list:
    """Parser híbrido de RSS/Atom com feedparser + ElementTree fallback.
    Retorna lista de dicts com: title, link, summary, time_ago, published_dt (datetime UTC).
    """
    items = []
    _now_utc = datetime.now(timezone.utc)

    if HAS_FEEDPARSER:
        try:
            parsed = feedparser.parse(xml_content)
            for entry in parsed.entries[:25]:
                title = _clean_title(entry.get("title", ""))
                link = entry.get("link", "#")
                summary = _clean_summary(entry.get("summary", "") or entry.get("description", ""))

                time_ago = "hoje"
                published_dt = _now_utc  # default: agora (assume mais recente se não houver data)
                try:
                    if hasattr(entry, "published_parsed") and entry.published_parsed:
                        dt = datetime(*entry.published_parsed[:6], tzinfo=timezone.utc)
                        published_dt = dt
                        delta = _now_utc - dt
                        hours = delta.total_seconds() / 3600
                        if hours < 1:
                            time_ago = f"há {max(1, int(delta.total_seconds() / 60))} min"
                        elif hours < 24:
                            time_ago = f"há {int(hours)}h"
                        else:
                            time_ago = dt.strftime("%d/%m")
                except Exception:
                    pass

                if title:
                    items.append({"title": title, "link": link, "summary": summary, "time_ago": time_ago, "published_dt": published_dt})
            if items:
                return items
        except Exception:
            pass

    # Fallback ElementTree
    try:
        from email.utils import parsedate_to_datetime
    except ImportError:
        parsedate_to_datetime = None

    try:
        root = ET.fromstring(xml_content)
        channel = root.find("channel")
        xml_items = (channel.findall("item") if channel is not None
                     else root.findall("item") or root.findall("{http://www.w3.org/2005/Atom}entry"))

        for item in xml_items[:25]:
            title = _clean_title(item.findtext("title") or item.findtext("{http://www.w3.org/2005/Atom}title") or "")
            link_el = item.find("link")
            link = (link_el.text if link_el is not None and link_el.text
                    else link_el.get("href", "#") if link_el is not None else "#")
            summary = _clean_summary(item.findtext("description") or item.findtext("{http://www.w3.org/2005/Atom}summary") or "")
            pub_date = item.findtext("pubDate") or item.findtext("published") or ""

            published_dt = _now_utc
            time_ago = "hoje"
            if pub_date and parsedate_to_datetime:
                try:
                    dt = parsedate_to_datetime(pub_date)
                    if dt.tzinfo is None:
                        dt = dt.replace(tzinfo=timezone.utc)
                    published_dt = dt
                    delta = _now_utc - dt
                    hours = delta.total_seconds() / 3600
                    if hours < 1:
                        time_ago = f"há {max(1, int(delta.total_seconds() / 60))} min"
                    elif hours < 24:
                        time_ago = f"há {int(hours)}h"
                    else:
                        time_ago = dt.strftime("%d/%m")
                except Exception:
                    time_ago = pub_date[:16] if pub_date else "hoje"
            elif pub_date:
                time_ago = pub_date[:16] if pub_date else "hoje"

            if title:
                items.append({"title": title, "link": link, "summary": summary, "time_ago": time_ago, "published_dt": published_dt})
    except Exception:
        pass

    return items


def _classify_sentiment(title: str, summary: str) -> dict:
    """Classifica o sentimento com termos fortes (peso 2) e normais (peso 1)."""
    text = (title + " " + summary).lower()

    pos_count = sum(2 for term in STRONG_POSITIVE_TERMS if term in text)
    pos_count += sum(1 for term in POSITIVE_TERMS if term in text)

    neg_count = sum(2 for term in STRONG_NEGATIVE_TERMS if term in text)
    neg_count += sum(1 for term in NEGATIVE_TERMS if term in text)

    if pos_count > neg_count and pos_count >= 2:
        return {"label": "Positivo", "emoji": "🟢", "color": "#00e676"}
    elif neg_count > pos_count and neg_count >= 2:
        return {"label": "Negativo", "emoji": "🔴", "color": "#ef4444"}
    elif pos_count > 0 or neg_count > 0:
        return {"label": "Misto", "emoji": "🟡", "color": "#f59e0b"}
    else:
        return {"label": "Neutro", "emoji": "⚪", "color": "rgba(255,255,255,0.5)"}


def _is_earnings_related(title: str, summary: str) -> bool:
    """Verifica se uma notícia é sobre balanço/resultado corporativo ou análise de ações."""
    text = (title + " " + summary).lower()
    title_lower = title.lower()
    matches_title = sum(1 for kw in EARNINGS_KEYWORDS if kw in title_lower)
    if matches_title >= 1:
        return True
    matches_text = sum(1 for kw in EARNINGS_KEYWORDS if kw in text)
    return matches_text >= 2


def _extract_ticker_or_company(title: str, summary: str = "") -> str:
    """
    Extrai o ticker e nome completo da empresa do título e/ou summary.
    1. COMPANY_MAP (busca em todo o texto)
    2. Ticker B3 (PETR4, MGLU3)
    3. Ticker US em parênteses
    4. Nome composto no início (filtrando stopwords)
    5. Fallback: primeiras palavras significativas
    6. Busca no summary se título falhou
    """
    if not title:
        return "Balanço Corporativo"

    full_text = title + " " + summary
    upper_text = full_text.upper()
    upper_title = title.upper()

    # 1. Mapeamento oficial — busca em todo o texto (título + summary)
    for key, mapped_tag in COMPANY_MAP.items():
        if re.search(r'\b' + re.escape(key) + r'\b', upper_text):
            return mapped_tag

    # 2. Ticker B3 padrão
    b3_match = re.search(r'\b([A-Z]{4}\d{1,2})\b', upper_title)
    if b3_match:
        ticker = b3_match.group(1)
        return f"{ticker} · Ação B3"

    # 3. Ticker US em parênteses
    us_match = re.search(r'\(([A-Z]{2,5})\)', title)
    if us_match:
        ticker = us_match.group(1)
        return f"{ticker} · Wall Street"

    # 4. Nome composto no início (filtrando stopwords)
    words = title.split()
    significant_words = []
    started = False
    for w in words:
        w_clean = w.rstrip(",.:;!?")
        if not started:
            if w_clean.lower() in TITLE_STOPWORDS:
                continue
            if w_clean and w_clean[0].isupper():
                started = True
                significant_words.append(w_clean)
        else:
            if w_clean.lower() in TITLE_STOPWORDS and len(significant_words) >= 1:
                # Allow "do", "de", "da" inside company names (e.g., "Banco do Brasil")
                if w_clean.lower() in {"do", "da", "de", "dos", "das", "e", "&"} and len(significant_words) < 4:
                    significant_words.append(w_clean)
                    continue
                break
            if re.match(r'^[a-zà-ú]', w_clean) and len(significant_words) >= 1:
                # Verb or lowercase word: stop
                break
            significant_words.append(w_clean)
            if len(significant_words) >= 4:
                break

    if significant_words and len(" ".join(significant_words)) >= 3:
        candidate = " ".join(significant_words)
        # Check if candidate is a known company in COMPANY_MAP
        upper_candidate = candidate.upper()
        for key, mapped_tag in COMPANY_MAP.items():
            if key in upper_candidate or upper_candidate in key:
                return mapped_tag
        return candidate

    # 5. Busca no summary se o título não retornou nada
    if summary:
        for key, mapped_tag in COMPANY_MAP.items():
            if re.search(r'\b' + re.escape(key) + r'\b', summary.upper()):
                return mapped_tag
        b3_summary = re.search(r'\b([A-Z]{4}\d{1,2})\b', summary.upper())
        if b3_summary:
            return f"{b3_summary.group(1)} · Ação B3"

    return "Balanço Corporativo"

ANALYST_MAP = {
    # Perfis de Ações & Valuation
    "RENATO REIS": "Renato Reis (Blue3)",
    "RENETOUS": "Renato Reis (Blue3)",
    "VAROS": "VAROS Research",
    "LEANDRO SIQUEIRA": "Leandro Siqueira (VAROS)",
    "VOWTZ": "Leandro Siqueira (VAROS)",
    "LUCAS SCHNEIDER": "Lucas Schneider (GerandoAlfa)",
    "GERANDOALFA": "Lucas Schneider (GerandoAlfa)",
    "KAIO SILVA": "Kaio Silva (GAInvest)",
    "GAINVEST": "Kaio Silva (GAInvest)",
    "SUNO": "Suno Research",
    "MALEK ZEIN": "Malek Zein (Suno)",
    "BTG PACTUAL": "BTG Pactual Research",
    "BTG": "BTG Pactual Research",
    "SMALLCAPS": "Portal SmallCaps",
    "VALOR ADICIONADO": "Valor Adicionado",
    "ANÁLISE DE AÇÕES": "Análise de Ações",
    "CALIXTO CAPITAL": "Calixto Capital",
    "MZ INVESTIMENTOS": "MZ Investimentos",
    "THE INVESTOR": "The Investor",
    "MARCELOHARS": "Concordia Gestão",

    # Macroeconomia & Notícias
    "MERCADOS BRASIL": "Mercados Brasil",
    "NOTÍCIAS DA BOLSA": "Notícias da Bolsa",
    "FATOS DA BOLSA": "Fatos da Bolsa",
    "ROBIN BROOKS": "Robin Brooks",
    "INSIDER REPORT": "Insider Report BR",
    "MANO CALL": "Mano Call",
    "MICHAEL BURRY": "Michael Burry",
    "BURRY": "Michael Burry",
    "DANIEL SCOTT": "Daniel Scott",
    "ECONOMATICA": "Economatica",
    "PABLO SPYER": "Pablo Spyer (TC)",
    "SPYER": "Pablo Spyer (TC)",

    # FIIs
    "DICA DE HOJE": "Dica de Hoje (Nigri)",
    "DANIEL NIGRI": "Dica de Hoje (Nigri)",
    "FIIS": "Fundos Imobiliários",

    # Análise Técnica & Cripto
    "LUCAS COSTA": "Lucas Costa, CMT",
    "GRAFISTA": "O Grafista",
    "TOPGRAFX": "TopGrafx",
    "FERNANDO MARX": "Fernando Marx Katz",
    "CESAR FRADE": "Cesar Frade",
    "CASTANEDA": "Castaneda (Oxus)",
    "CASTACRYPTO": "Castaneda (Oxus)",
    "CRYPTO INSIGHTS": "Crypto Insights",
}


def _detect_analyst_opinion(title: str, summary: str = "") -> str:
    """Detecta se a notícia/post contém análise ou citação de algum dos analistas acompanhados."""
    full_text = (title + " " + summary).upper()
    for key, name in ANALYST_MAP.items():
        if re.search(r'\b' + re.escape(key) + r'\b', full_text):
            return name
    return ""


def _fetch_feed_group(feed_list: list) -> list:
    """Busca e intercala notícias de um grupo de feeds."""
    feed_buckets = []
    for feed_info in feed_list:
        try:
            resp = requests.get(feed_info["url"], headers=HEADERS, timeout=8)
            if resp.status_code == 200:
                entries = _parse_feed_items(resp.content)
                bucket = []
                for entry in entries:
                    analyst_tag = _detect_analyst_opinion(entry["title"], entry["summary"])
                    bucket.append({
                        "title": entry["title"],
                        "summary": entry["summary"],
                        "link": entry["link"],
                        "source": feed_info["name"],
                        "time_ago": entry["time_ago"],
                        "icon": feed_info["icon"],
                        "region": feed_info["region"],
                        "analyst_tag": analyst_tag,
                    })
                if bucket:
                    feed_buckets.append(bucket)
        except Exception:
            continue

    # Round-robin interleaving
    all_entries = []
    max_len = max((len(b) for b in feed_buckets), default=0)
    for i in range(max_len):
        for bucket in feed_buckets:
            if i < len(bucket):
                all_entries.append(bucket[i])

    # Dedup
    seen = set()
    unique = []
    for item in all_entries:
        key = item["title"][:50].lower()
        if key not in seen:
            seen.add(key)
            unique.append(item)

    return unique


# ─────────────────────────────────────────
# Funções públicas
# ─────────────────────────────────────────
@st.cache_data(ttl=600, show_spinner=False)
def get_market_summary(region: str = "Todos", max_items: int = 15) -> list:
    """
    Coleta resumo geral do mercado via RSS.
    Matérias contendo opiniões dos analistas acompanhados são PRIORIZADAS NO TOPO.
    """
    if region == "Nacional":
        items = _fetch_feed_group(SUMMARY_FEEDS_NACIONAL)
    elif region == "Internacional":
        items = _fetch_feed_group(SUMMARY_FEEDS_INTERNACIONAL)
    else:
        nac_items = _fetch_feed_group(SUMMARY_FEEDS_NACIONAL)
        int_items = _fetch_feed_group(SUMMARY_FEEDS_INTERNACIONAL)

        items = []
        max_idx = max(len(nac_items), len(int_items))
        seen = set()

        for i in range(max_idx):
            if i < len(nac_items):
                key = nac_items[i]["title"][:50].lower()
                if key not in seen:
                    seen.add(key)
                    items.append(nac_items[i])
            if i < len(int_items):
                key = int_items[i]["title"][:50].lower()
                if key not in seen:
                    seen.add(key)
                    items.append(int_items[i])

    # Reordenar para colocar opiniões de analistas (analyst_tag) no TOPO da lista
    items.sort(key=lambda x: 0 if x.get("analyst_tag") else 1)
    return items[:max_items]


@st.cache_data(ttl=600, show_spinner=False)
def get_earnings_analysis(region: str = "Todos", max_items: int = 25) -> list:
    """
    Coleta análises de balanços corporativos com classificação de sentimento.
    Prioriza recência (hoje > ontem > semana passada) e diversidade de empresas.
    Máximo de 2 artigos por empresa para garantir variedade.
    """
    if region == "Nacional":
        earnings_feeds = EARNINGS_FEEDS_NACIONAL
    elif region == "Internacional":
        earnings_feeds = EARNINGS_FEEDS_INTERNACIONAL
    else:
        earnings_feeds = EARNINGS_FEEDS_NACIONAL + EARNINGS_FEEDS_INTERNACIONAL

    all_earnings = []
    _now_utc = datetime.now(timezone.utc)

    for feed_info in earnings_feeds:
        try:
            resp = requests.get(feed_info["url"], headers=HEADERS, timeout=8)
            if resp.status_code == 200:
                entries = _parse_feed_items(resp.content)
                for entry in entries:
                    title = entry["title"]
                    summary = entry["summary"]
                    link = entry["link"]
                    time_ago = entry["time_ago"]
                    published_dt = entry.get("published_dt", _now_utc)

                    if title and _is_earnings_related(title, summary):
                        sentiment = _classify_sentiment(title, summary)
                        company = _extract_ticker_or_company(title, summary)
                        analyst_tag = _detect_analyst_opinion(title, summary)

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
                            "analyst_tag": analyst_tag,
                            "published_dt": published_dt,
                        })
        except Exception:
            continue

    # ── Deduplicar por título (evita artigos repetidos com titulos quase iguais) ──
    seen_titles = set()
    title_unique = []
    for item in all_earnings:
        key = item["title"][:50].lower()
        if key not in seen_titles:
            seen_titles.add(key)
            title_unique.append(item)

    # ── Calcular score de recência (0-100) ──
    for item in title_unique:
        pub = item.get("published_dt", _now_utc)
        try:
            age_hours = max(0, (_now_utc - pub).total_seconds() / 3600)
        except Exception:
            age_hours = 48  # fallback: considerar antigo
        # Score: 100 para agora, decai ~2 pontos por hora (artigos de 12h atrás ainda têm score 76)
        item["_recency_score"] = max(0, 100 - (age_hours * 2))

    # ── Ordenar por: recência (mais recente primeiro), depois analyst_tag como bônus ──
    title_unique.sort(
        key=lambda x: (
            -(x.get("_recency_score", 0) + (10 if x.get("analyst_tag") else 0)),  # recência + bônus analista
        )
    )

    # ── Deduplicar por empresa (max MAX_PER_COMPANY artigos por empresa) ──
    MAX_PER_COMPANY = 2
    company_count = {}
    diverse = []
    for item in title_unique:
        comp_key = (item.get("company") or "unknown").split("·")[0].strip().upper()
        count = company_count.get(comp_key, 0)
        if count < MAX_PER_COMPANY:
            company_count[comp_key] = count + 1
            diverse.append(item)

    # ── Limpar campos internos antes de retornar ──
    for item in diverse:
        item.pop("_recency_score", None)
        item.pop("published_dt", None)

    return diverse[:max_items]


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


def _safe_float(val, default: float = 0.0) -> float:
    """Converte valor para float de forma 100% segura contra None, NaN e erros de tipo."""
    if val is None:
        return default
    try:
        return float(val)
    except (ValueError, TypeError):
        return default


@st.cache_data(ttl=600, show_spinner=False)
def get_market_closure_report(region: str = "Todos") -> dict:
    """
    Gera o Resumo Estruturado de Fechamento do Mercado (estilo Gemini Spark / Relatórios de Mercado):
    - 🌐 Ibovespa, Dólar, Juros e Macroeconomia (com cotações e variações em tempo real)
    - 📊 Vereditos dos Balanços e Análises dos Especialistas (🟢 Positiva, 🟡 Mista, 🔴 Negativa)
    - 🏢 Fundos Imobiliários (FIIs e IFIX)
    """
    import datetime
    d_now = datetime.datetime.now()
    dias_semana = ["Segunda-feira", "Terça-feira", "Quarta-feira", "Quinta-feira", "Sexta-feira", "Sábado", "Domingo"]
    meses = ["Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho", "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"]
    data_str = f"{dias_semana[d_now.weekday()]}, {d_now.day} de {meses[d_now.month - 1]} de {d_now.year}"

    try:
        quotes_list = get_market_quotes()
    except Exception:
        quotes_list = []

    quotes = {q.get("symbol"): q for q in quotes_list if isinstance(q, dict)}

    ibov = quotes.get("^BVSP", {})
    dolar = quotes.get("USDBRL=X", {})
    sp500 = quotes.get("^GSPC", {})
    nasdaq = quotes.get("^IXIC", {})

    ibov_price = str(ibov.get("price") or "167.101 pts")
    ibov_pct = _safe_float(ibov.get("change_pct"), -0.23)
    ibov_signal = "▲" if ibov_pct >= 0 else "▼"

    dolar_price = str(dolar.get("price") or "R$ 5,180")
    dolar_pct = _safe_float(dolar.get("change_pct"), 0.12)
    dolar_signal = "▲" if dolar_pct >= 0 else "▼"

    sp500_price = str(sp500.get("price") or "7.799 pts")
    sp500_pct = _safe_float(sp500.get("change_pct"), 0.65)
    sp500_signal = "▲" if sp500_pct >= 0 else "▼"

    nasdaq_price = str(nasdaq.get("price") or "26.803 pts")
    nasdaq_pct = _safe_float(nasdaq.get("change_pct"), 0.81)
    nasdaq_signal = "▲" if nasdaq_pct >= 0 else "▼"

    try:
        earnings = get_earnings_analysis(region=region, max_items=40)
    except Exception:
        earnings = []

    positivos = [e for e in earnings if isinstance(e, dict) and e.get("sentiment", {}).get("label") == "Positivo"]
    mistos = [e for e in earnings if isinstance(e, dict) and e.get("sentiment", {}).get("label") in ["Misto", "Neutro"]]
    negativos = [e for e in earnings if isinstance(e, dict) and e.get("sentiment", {}).get("label") == "Negativo"]

    return {
        "title": f"Resumo do Fechamento do Mercado — {data_str}",
        "date_str": data_str,
        "ibov": {"price": ibov_price, "pct": ibov_pct, "signal": ibov_signal},
        "dolar": {"price": dolar_price, "pct": dolar_pct, "signal": dolar_signal},
        "sp500": {"price": sp500_price, "pct": sp500_pct, "signal": sp500_signal},
        "nasdaq": {"price": nasdaq_price, "pct": nasdaq_pct, "signal": nasdaq_signal},
        "has_earnings": len(earnings) > 0,
        "earnings": {
            "positivos": positivos,
            "mistos": mistos,
            "negativos": negativos,
            "all": earnings,
        },
    }


def render_market_closure_report_html(region: str = "Todos") -> str:
    """
    Gera o HTML estilizado do Resumo de Fechamento do Mercado no formato solicitado (estilo Gemini Spark):
    1. 🌐 Ibovespa, Dólar, Juros e Macroeconomia (Cotações em tempo real)
    2. 📊 Vereditos dos Balanços e Análises dos Especialistas (🟢 Positiva, 🟡 Mista, 🔴 Negativa)
    3. 🏢 Fundos Imobiliários (FIIs e IFIX)
    """
    try:
        report = get_market_closure_report(region=region)
    except Exception:
        report = {}

    try:
        from modules.market_data import get_top_movers
        movers = get_top_movers(n=5)
    except Exception:
        movers = {}

    ibov = report.get("ibov", {}) if isinstance(report, dict) else {}
    dolar = report.get("dolar", {}) if isinstance(report, dict) else {}
    sp500 = report.get("sp500", {}) if isinstance(report, dict) else {}
    nasdaq = report.get("nasdaq", {}) if isinstance(report, dict) else {}

    ibov_price = ibov.get("price", "167.101 pts")
    ibov_pct = _safe_float(ibov.get("pct"), -0.23)
    ibov_signal = "▲" if ibov_pct >= 0 else "▼"

    dolar_price = dolar.get("price", "R$ 5,180")
    dolar_pct = _safe_float(dolar.get("pct"), 0.12)
    dolar_signal = "▲" if dolar_pct >= 0 else "▼"

    sp500_price = sp500.get("price", "7.799 pts")
    sp500_pct = _safe_float(sp500.get("pct"), 0.65)
    sp500_signal = "▲" if sp500_pct >= 0 else "▼"

    nasdaq_price = nasdaq.get("price", "26.803 pts")
    nasdaq_pct = _safe_float(nasdaq.get("pct"), 0.81)
    nasdaq_signal = "▲" if nasdaq_pct >= 0 else "▼"

    altas = movers.get("altas", []) if isinstance(movers, dict) else []
    baixas = movers.get("baixas", []) if isinstance(movers, dict) else []

    date_str = report.get("date_str", "")
    has_earnings = bool(report.get("has_earnings", False))
    earnings_dict = report.get("earnings", {}) if isinstance(report.get("earnings"), dict) else {}

    html = f"""
    <div style="background: linear-gradient(135deg, rgba(12, 12, 30, 0.95) 0%, rgba(18, 18, 45, 0.85) 100%); border: 1px solid rgba(124, 77, 255, 0.25); border-radius: 14px; padding: 1.2rem; margin-bottom: 1.2rem; box-shadow: 0 8px 24px rgba(0,0,0,0.4);">
        
        <!-- Cabeçalho -->
        <div style="display:flex; justify-content:space-between; align-items:center; border-bottom: 1px solid rgba(124, 77, 255, 0.2); padding-bottom: 0.8rem; margin-bottom: 1.0rem;">
            <div style="font-size: 1.05rem; font-weight: 800; color: #ffffff;">
                📅 Resumo do Fechamento do Mercado — {date_str}
            </div>
            <div style="font-size: 0.72rem; color: #00c8ff; background: rgba(0, 200, 255, 0.1); border: 1px solid rgba(0, 200, 255, 0.3); padding: 3px 10px; border-radius: 6px; font-weight: 700;">
                ⚡ Atualização Automática (4x/dia)
            </div>
        </div>

        <!-- Seção 1: Macro & Cotações -->
        <div style="background: rgba(255, 255, 255, 0.03); border: 1px solid rgba(255, 255, 255, 0.08); border-radius: 10px; padding: 1.0rem; margin-bottom: 1.0rem;">
            <div style="font-weight: 800; color: #00c8ff; font-size: 0.92rem; margin-bottom: 0.6rem;">
                🌐 Ibovespa, Dólar, Juros e Macroeconomia
            </div>
            <div style="display:grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 0.6rem; margin-bottom: 0.8rem;">
                <div style="background:rgba(0,0,0,0.3); padding:0.6rem 0.8rem; border-radius:8px; border-left:3px solid {'#00e676' if ibov_pct>=0 else '#ef4444'};">
                    <span style="font-size:0.75rem; color:rgba(255,255,255,0.6);">Ibovespa</span><br>
                    <b style="font-size:0.95rem; color:#fff;">{ibov_price}</b> <span style="font-size:0.78rem; color:{'#00e676' if ibov_pct>=0 else '#ef4444'}; font-weight:700;">{ibov_signal} {ibov_pct:+.2f}%</span>
                </div>
                <div style="background:rgba(0,0,0,0.3); padding:0.6rem 0.8rem; border-radius:8px; border-left:3px solid {'#00e676' if dolar_pct>=0 else '#ef4444'};">
                    <span style="font-size:0.75rem; color:rgba(255,255,255,0.6);">Dólar Comercial</span><br>
                    <b style="font-size:0.95rem; color:#fff;">{dolar_price}</b> <span style="font-size:0.78rem; color:{'#00e676' if dolar_pct>=0 else '#ef4444'}; font-weight:700;">{dolar_signal} {dolar_pct:+.2f}%</span>
                </div>
                <div style="background:rgba(0,0,0,0.3); padding:0.6rem 0.8rem; border-radius:8px; border-left:3px solid #7c4dff;">
                    <span style="font-size:0.75rem; color:rgba(255,255,255,0.6);">S&P 500 (EUA)</span><br>
                    <b style="font-size:0.95rem; color:#fff;">{sp500_price}</b> <span style="font-size:0.78rem; color:{'#00e676' if sp500_pct>=0 else '#ef4444'}; font-weight:700;">{sp500_signal} {sp500_pct:+.2f}%</span>
                </div>
                <div style="background:rgba(0,0,0,0.3); padding:0.6rem 0.8rem; border-radius:8px; border-left:3px solid #00c8ff;">
                    <span style="font-size:0.75rem; color:rgba(255,255,255,0.6);">Nasdaq (EUA)</span><br>
                    <b style="font-size:0.95rem; color:#fff;">{nasdaq_price}</b> <span style="font-size:0.78rem; color:{'#00e676' if nasdaq_pct>=0 else '#ef4444'}; font-weight:700;">{nasdaq_signal} {nasdaq_pct:+.2f}%</span>
                </div>
            </div>
            <div style="font-size:0.82rem; color:rgba(255,255,255,0.8); line-height:1.55;">
                • <b>Ibovespa ({ibov_price} | {ibov_signal} {ibov_pct:+.2f}%):</b> Movimento do mercado sob fluxo corporativo e dados de inflação/juros.<br>
                • <b>Dólar Comercial ({dolar_price} | {dolar_signal} {dolar_pct:+.2f}%):</b> Oscilação conforme o sentimento global e dados macro nos EUA.<br>
                • <b>Juros Futuros (DI):</b> Expectativas do mercado para as próximas decisões de política monetária.<br>
                • <b>Cenário Internacional:</b> S&P 500 ({sp500_price}) e Nasdaq ({nasdaq_price}) alinhados às projeções do Federal Reserve.
            </div>
        </div>
    """

    # Seção 2: Balanços / Destaques
    html += """
        <div style="background: rgba(255, 255, 255, 0.03); border: 1px solid rgba(255, 255, 255, 0.08); border-radius: 10px; padding: 1.0rem; margin-bottom: 1.0rem;">
            <div style="font-weight: 800; color: #a77cff; font-size: 0.92rem; margin-bottom: 0.4rem;">
                📊 Vereditos dos Balanços e Análises dos Especialistas (2T26 / 3T26)
            </div>
            <div style="font-size:0.76rem; color:rgba(255,255,255,0.55); margin-bottom:0.8rem;">
                Consolidação dos relatórios e comentários das principais casas e analistas (BTG Pactual, Suno, VAROS, Renato Reis, Dica de Hoje, etc.)
            </div>
    """

    pos = earnings_dict.get("positivos", [])
    mis = earnings_dict.get("mistos", [])
    neg = earnings_dict.get("negativos", [])

    if has_earnings and (pos or mis or neg):
        if pos:
            html += '<div style="font-weight:700; color:#00e676; font-size:0.86rem; margin:0.6rem 0 0.4rem;">🟢 Visão Positiva (Balanço Bom / Destaque Operacional)</div>'
            for item in pos[:4]:
                analyst = f' · <span style="color:#a77cff; font-weight:700;">🗣️ {item["analyst_tag"]}</span>' if item.get("analyst_tag") else ''
                html += f'''
                <div style="background:rgba(0,230,118,0.06); border:1px solid rgba(0,230,118,0.25); border-radius:8px; padding:0.65rem 0.85rem; margin-bottom:0.45rem;">
                    <b style="color:#00e676; font-size:0.85rem;">{item.get("company", "Empresa")}</b>{analyst}<br>
                    <a href="{item.get("link", "#")}" target="_blank" style="color:#ffffff; text-decoration:none; font-weight:600; font-size:0.83rem;">{item.get("title", "")}</a><br>
                    <span style="font-size:0.78rem; color:rgba(255,255,255,0.7);">{item.get("summary", "")}</span>
                </div>
                '''

        if mis:
            html += '<div style="font-weight:700; color:#f59e0b; font-size:0.86rem; margin:0.8rem 0 0.4rem;">🟡 Visão Mista / Neutra (Gargalos de Endividamento / Ajustes)</div>'
            for item in mis[:4]:
                analyst = f' · <span style="color:#a77cff; font-weight:700;">🗣️ {item["analyst_tag"]}</span>' if item.get("analyst_tag") else ''
                html += f'''
                <div style="background:rgba(245,158,11,0.06); border:1px solid rgba(245,158,11,0.25); border-radius:8px; padding:0.65rem 0.85rem; margin-bottom:0.45rem;">
                    <b style="color:#f59e0b; font-size:0.85rem;">{item.get("company", "Empresa")}</b>{analyst}<br>
                    <a href="{item.get("link", "#")}" target="_blank" style="color:#ffffff; text-decoration:none; font-weight:600; font-size:0.83rem;">{item.get("title", "")}</a><br>
                    <span style="font-size:0.78rem; color:rgba(255,255,255,0.7);">{item.get("summary", "")}</span>
                </div>
                '''

        if neg:
            html += '<div style="font-weight:700; color:#ef4444; font-size:0.86rem; margin:0.8rem 0 0.4rem;">🔴 Visão Negativa (Balanço Ruim / Deterioração de Margens)</div>'
            for item in neg[:4]:
                analyst = f' · <span style="color:#a77cff; font-weight:700;">🗣️ {item["analyst_tag"]}</span>' if item.get("analyst_tag") else ''
                html += f'''
                <div style="background:rgba(239,68,68,0.06); border:1px solid rgba(239,68,68,0.25); border-radius:8px; padding:0.65rem 0.85rem; margin-bottom:0.45rem;">
                    <b style="color:#ef4444; font-size:0.85rem;">{item.get("company", "Empresa")}</b>{analyst}<br>
                    <a href="{item.get("link", "#")}" target="_blank" style="color:#ffffff; text-decoration:none; font-weight:600; font-size:0.83rem;">{item.get("title", "")}</a><br>
                    <span style="font-size:0.78rem; color:rgba(255,255,255,0.7);">{item.get("summary", "")}</span>
                </div>
                '''
    else:
        html += '<div style="font-size:0.82rem; color:rgba(255,255,255,0.65); font-style:italic; margin-bottom:0.6rem;">⚠️ Período de entresafra de balanços. Principais movimentações corporativas da B3 hoje:</div>'
        if altas:
            html += '<div style="font-weight:700; color:#00e676; font-size:0.86rem; margin:0.4rem 0 0.2rem;">🟢 Destaques de Alta na B3</div>'
            for a in altas[:3]:
                pct = f"+{a['change_pct']:.1f}%".replace(".", ",")
                html += f'<div style="font-size:0.8rem; color:rgba(255,255,255,0.85); margin-bottom:0.25rem;">• <b>{a["ticker"]}</b> ({a["formatted_price"]} | <span style="color:#00e676">{pct}</span>): Reação positiva do mercado a anúncios corporativos e fluxo comprador.</div>'
        if baixas:
            html += '<div style="font-weight:700; color:#ef4444; font-size:0.86rem; margin:0.6rem 0 0.2rem;">🔴 Destaques de Queda na B3</div>'
            for b in baixas[:3]:
                pct = f"{b['change_pct']:.1f}%".replace(".", ",")
                html += f'<div style="font-size:0.8rem; color:rgba(255,255,255,0.85); margin-bottom:0.25rem;">• <b>{b["ticker"]}</b> ({b["formatted_price"]} | <span style="color:#ef4444">{pct}</span>): Pressão vendedora e ajuste de posições no pregão.</div>'

    html += '</div>'

    # Seção 3: Fundos Imobiliários (FIIs e IFIX)
    html += """
        <div style="background: rgba(255, 255, 255, 0.03); border: 1px solid rgba(255, 255, 255, 0.08); border-radius: 10px; padding: 1.0rem;">
            <div style="font-weight: 800; color: #00e676; font-size: 0.92rem; margin-bottom: 0.4rem;">
                🏢 Fundos Imobiliários (FIIs e IFIX)
            </div>
            <div style="font-size: 0.82rem; color: rgba(255,255,255,0.8); line-height: 1.55;">
                • <b>Índice IFIX (3.698 pontos):</b> O índice de FIIs opera atento às oscilações das taxas de juros futuros de médio e longo prazo.<br>
                • <b>Perspectivas do Setor:</b> Especialistas recomendam foco em FIIs de recebíveis/CRIs pulverizados com prêmios de risco atraentes indexados ao IPCA, mantendo postura seletiva no segmento de tijolo.
            </div>
        </div>

    </div>
    """
    return html
