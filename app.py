"""
app.py — Trader Support
Portal profissional de análise financeira com dashboard de mercado,
notícias, taxas de juros e acesso organizado a todas as aplicações.
Hospedado no Streamlit Cloud.
"""

import streamlit as st
from datetime import datetime
import base64 as _b64
from pathlib import Path as _Path

# ─────────────────────────────────────────
# Page Config
# ─────────────────────────────────────────
st.set_page_config(
    page_title="Trader Support · Portal de Análise Financeira",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─────────────────────────────────────────
# App Registry — Organizado por Categorias
# ─────────────────────────────────────────
APPS = [
    {
        "id": "smc",
        "title": "SMC Screener v3.0",
        "subtitle": "Smart Money Concepts",
        "description": "Detecção automatizada de estruturas institucionais: Order Blocks, Fair Value Gaps, pontos de entrada e saída com Risk/Reward calculado.",
        "url": "https://smc-v30.streamlit.app/",
        "icon": "🏦",
        "accent": "#4ecdc4",
        "tags": ["SMC", "Order Blocks", "Institucional"],
        "category": "Screening & Análise Técnica",
        "status": "online",
    },
    {
        "id": "multistoch",
        "title": "Screener MultiStoch",
        "subtitle": "Confluência Multi-Timeframe",
        "description": "Algoritmo que monitora múltiplos tempos gráficos e analisa o fluxo financeiro através da Transformada Discreta de Fourier para encontrar reversões.",
        "url": "https://confluencescreener.streamlit.app/",
        "icon": "📈",
        "accent": "#6366f1",
        "tags": ["Stoch 80", "FMFI", "Quant"],
        "category": "Screening & Análise Técnica",
        "status": "online",
    },
    {
        "id": "mfi",
        "title": "Screener MFI",
        "subtitle": "Money Flow Index · Fluxo Financeiro",
        "description": "Screener baseado no indicador MFI duplo com filtros cruzados (MFI1 7D e MFI2 5D). Elimina falsos positivos exigindo confluência de sobrecompra e sobrevenda.",
        "url": "https://screener-mfi.streamlit.app/",
        "icon": "💹",
        "accent": "#00c8ff",
        "tags": ["MFI Duplo", "Fluxo Cruzado", "Confirmação"],
        "category": "Screening & Análise Técnica",
        "status": "online",
    },
    {
        "id": "week-smc",
        "title": "Week Screener SMC",
        "subtitle": "Smart Money Concepts · Semanal",
        "description": "Screener SMC no timeframe semanal (W1). Liquidity Sweeps, BOS/CHOCH, Order Blocks e Fibonacci aplicados a candles semanais para swing trades.",
        "url": "https://week-smc.streamlit.app/",
        "icon": "📅",
        "accent": "#0ea5e9",
        "tags": ["SMC", "Semanal", "Swing"],
        "category": "Screening & Análise Técnica",
        "status": "online",
    },
    {
        "id": "screener-mobile",
        "title": "Screener Pro Mobile",
        "subtitle": "Screener de Ações Otimizado",
        "description": "Screener de ações otimizado para dispositivos móveis com algoritmos de seleção baseados em análise técnica e fundamentalista.",
        "url": "https://screenermobile.streamlit.app/",
        "icon": "📱",
        "accent": "#45b7d1",
        "tags": ["Ações", "Mobile", "Técnica"],
        "category": "Screening & Análise Técnica",
        "status": "online",
    },
    {
        "id": "fundamentus",
        "title": "Fundamentus Engine",
        "subtitle": "Análise Top-Down B3",
        "description": "Motor quantitativo de análise fundamentalista completo. Inclui painel macroeconômico, mapa setorial, e screener com modelos de valuation e pontuação customizada.",
        "url": "https://fundamentus-engine.streamlit.app/",
        "icon": "🏛️",
        "accent": "#00ff88",
        "tags": ["Top-Down", "Macro", "Valuation"],
        "category": "Fundamentalista & Valuation",
        "status": "online",
    },
    {
        "id": "fairprice",
        "title": "Fair Price",
        "subtitle": "Valuation Algorítmico · B3",
        "description": "Motor completo de valuation selecionando entre Gordon Growth Model (DDM), FCD 2 Estágios (DCF) ou Múltiplos Relativos, com filtros de segurança.",
        "url": "https://fair-price.streamlit.app/",
        "icon": "🎯",
        "accent": "#00e676",
        "tags": ["Valuation", "Gordon DDM", "FCD/DCF"],
        "category": "Fundamentalista & Valuation",
        "status": "online",
    },
    {
        "id": "fcf",
        "title": "Screener FCF Yield",
        "subtitle": "Free Cash Flow · Fluxo de Caixa Livre",
        "description": "Análise fundamentalista profunda baseada em caixa real: FCO − Capex − Juros − Impostos. Classifica ativos como Barato, Justo ou Caro.",
        "url": "https://screener-fluxo-de-caixa.streamlit.app/",
        "icon": "🚀",
        "accent": "#7c4dff",
        "tags": ["FCF Yield", "Fundamentalista", "Value"],
        "category": "Fundamentalista & Valuation",
        "status": "online",
    },
    {
        "id": "opcoes",
        "title": "Opções Screener",
        "subtitle": "Análise de Opções B3",
        "description": "Screener de opções com precificação Black-Scholes, identificação de opções subavaliadas e análise de volatilidade implícita para o mercado brasileiro.",
        "url": "https://opcoes-screener.streamlit.app/",
        "icon": "📊",
        "accent": "#ff6b6b",
        "tags": ["Opções", "Black-Scholes", "B3"],
        "category": "Opções",
        "status": "online",
    },
    {
        "id": "assimetricas",
        "title": "Opções Assimétricas",
        "subtitle": "Screener de Proteção Assimétrica · B3",
        "description": "Screener que identifica opções com IV historicamente barato (Percentile ≤35%) e monta estruturas Strap/Strip assimétricas com proteção.",
        "url": "https://opassimetricas.streamlit.app/",
        "icon": "🛡️",
        "accent": "#00d2ff",
        "tags": ["Opções", "Strap/Strip", "Proteção"],
        "category": "Opções",
        "status": "online",
    },
    {
        "id": "positionandtax",
        "title": "Controle de IR & Carteira",
        "subtitle": "Apuração Tributária B3",
        "description": "Sistema completo para controle de carteira, custódia e apuração mensal de IR em Ações, BDRs, Opções e FIIs na B3. Gera DARF (6015).",
        "url": "https://positionandtax.streamlit.app/",
        "icon": "💼",
        "accent": "#7c4dff",
        "tags": ["Imposto de Renda", "Custódia", "DARF B3"],
        "category": "Ferramentas & Carteira",
        "status": "online",
    },
    {
        "id": "crypto",
        "title": "CryptoFilter Dashboard",
        "subtitle": "Análise de Criptoativos",
        "description": "Dashboard de filtragem e análise para o mercado de criptomoedas com indicadores técnicos, volume e tendências de mercado.",
        "url": "https://cryptofilter-dashboard.streamlit.app/",
        "icon": "₿",
        "accent": "#f7931a",
        "tags": ["Crypto", "Bitcoin", "DeFi"],
        "category": "Ferramentas & Carteira",
        "status": "online",
    },
]

# Categorias e seus ícones
CATEGORIES = {
    "Screening & Análise Técnica": "📈",
    "Fundamentalista & Valuation": "💰",
    "Opções": "📊",
    "Ferramentas & Carteira": "🔧",
}


# ─────────────────────────────────────────
# Custom CSS
# ─────────────────────────────────────────
def inject_css():
    st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap');
        @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500;600&display=swap');

        html, body, [class*="css"] {
            font-family: 'Inter', sans-serif;
        }

        /* ── Global Background ─── */
        .stApp {
            background: #060613;
            background-image:
                radial-gradient(circle at 15% 50%, rgba(124, 77, 255, 0.03) 0%, transparent 50%),
                radial-gradient(circle at 85% 30%, rgba(0, 200, 255, 0.02) 0%, transparent 50%);
        }

        /* ── Hide Streamlit branding ─── */
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        header[data-testid="stHeader"] {
            background: rgba(6, 6, 19, 0.95);
            backdrop-filter: blur(10px);
        }

        /* ── Sidebar Styling ─── */
        section[data-testid="stSidebar"] {
            background: linear-gradient(180deg, #0a0a1f 0%, #0d0d24 100%);
            border-right: 1px solid rgba(124, 77, 255, 0.1);
        }
        section[data-testid="stSidebar"] .stRadio label {
            font-size: 0.95rem !important;
            padding: 0.4rem 0 !important;
        }

        /* ── Ticker Bar ─── */
        .ticker-bar {
            display: flex;
            justify-content: space-between;
            align-items: center;
            gap: 0.5rem;
            padding: 0.7rem 1rem;
            background: linear-gradient(135deg, rgba(10, 10, 30, 0.9) 0%, rgba(15, 15, 40, 0.9) 100%);
            border: 1px solid rgba(124, 77, 255, 0.1);
            border-radius: 12px;
            margin-bottom: 1.2rem;
            overflow-x: auto;
            flex-wrap: nowrap;
        }
        .ticker-item {
            text-align: center;
            min-width: 90px;
            flex-shrink: 0;
        }
        .ticker-name {
            font-size: 0.65rem;
            font-weight: 600;
            color: rgba(255,255,255,0.45);
            text-transform: uppercase;
            letter-spacing: 1px;
            margin-bottom: 2px;
        }
        .ticker-price {
            font-size: 0.95rem;
            font-weight: 700;
            color: #fff;
            font-family: 'JetBrains Mono', monospace;
        }
        .ticker-change {
            font-size: 0.7rem;
            font-weight: 600;
            font-family: 'JetBrains Mono', monospace;
        }

        /* ── Metric Cards ─── */
        .metric-card {
            background: linear-gradient(135deg, rgba(15, 15, 35, 0.8) 0%, rgba(20, 20, 50, 0.6) 100%);
            border: 1px solid rgba(124, 77, 255, 0.12);
            border-radius: 16px;
            padding: 1.2rem;
            text-align: center;
            transition: all 0.3s ease;
        }
        .metric-card:hover {
            border-color: rgba(124, 77, 255, 0.3);
            transform: translateY(-2px);
        }
        .metric-label {
            font-size: 0.7rem;
            font-weight: 600;
            color: rgba(255,255,255,0.4);
            text-transform: uppercase;
            letter-spacing: 1.5px;
            margin-bottom: 0.4rem;
        }
        .metric-value {
            font-size: 1.6rem;
            font-weight: 800;
            color: #fff;
            font-family: 'JetBrains Mono', monospace;
        }
        .metric-change {
            font-size: 0.8rem;
            font-weight: 600;
            font-family: 'JetBrains Mono', monospace;
            margin-top: 0.2rem;
        }

        /* ── Section Panel ─── */
        .section-panel {
            background: linear-gradient(135deg, rgba(12, 12, 30, 0.8) 0%, rgba(18, 18, 45, 0.6) 100%);
            border: 1px solid rgba(124, 77, 255, 0.1);
            border-radius: 16px;
            padding: 1.5rem;
            margin-bottom: 1rem;
        }
        .section-title {
            font-size: 1rem;
            font-weight: 700;
            color: rgba(255,255,255,0.85);
            margin-bottom: 1rem;
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }

        /* ── News Items ─── */
        .news-item {
            padding: 0.8rem 0;
            border-bottom: 1px solid rgba(255,255,255,0.05);
            transition: background 0.2s ease;
        }
        .news-item:hover {
            background: rgba(124, 77, 255, 0.05);
            border-radius: 8px;
            padding-left: 0.5rem;
        }
        .news-item:last-child {
            border-bottom: none;
        }
        .news-title {
            font-size: 0.88rem;
            font-weight: 500;
            color: rgba(255,255,255,0.8);
            line-height: 1.4;
            margin-bottom: 0.3rem;
        }
        .news-title a {
            color: rgba(255,255,255,0.8) !important;
            text-decoration: none !important;
        }
        .news-title a:hover {
            color: #7c4dff !important;
        }
        .news-meta {
            font-size: 0.72rem;
            color: rgba(255,255,255,0.35);
        }
        .news-source {
            color: #7c4dff;
            font-weight: 600;
        }

        /* ── Rates Table ─── */
        .rates-section {
            margin-bottom: 1rem;
        }
        .rates-country {
            font-size: 0.8rem;
            font-weight: 700;
            color: rgba(255,255,255,0.6);
            margin-bottom: 0.5rem;
            display: flex;
            align-items: center;
            gap: 0.4rem;
        }
        .rate-row {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 0.45rem 0;
            border-bottom: 1px solid rgba(255,255,255,0.04);
        }
        .rate-name {
            font-size: 0.82rem;
            color: rgba(255,255,255,0.65);
        }
        .rate-value {
            font-size: 0.85rem;
            font-weight: 700;
            color: #fff;
            font-family: 'JetBrains Mono', monospace;
        }
        .rate-note {
            font-size: 0.7rem;
            font-weight: 500;
            margin-left: 0.4rem;
        }

        /* ── App Cards (Compact) ─── */
        .app-card-compact {
            background: linear-gradient(135deg, rgba(12, 12, 30, 0.9) 0%, rgba(20, 20, 50, 0.7) 100%);
            border: 1px solid rgba(255,255,255,0.06);
            border-radius: 14px;
            padding: 1.2rem 1.4rem;
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
            display: flex;
            flex-direction: column;
            height: 100%;
            min-height: 220px;
            position: relative;
            overflow: hidden;
        }
        .app-card-compact:hover {
            transform: translateY(-4px);
            border-color: rgba(255,255,255,0.15);
            box-shadow: 0 12px 40px rgba(0,0,0,0.4);
        }
        .app-card-compact .card-header {
            display: flex;
            align-items: center;
            gap: 0.7rem;
            margin-bottom: 0.6rem;
        }
        .app-card-compact .card-icon {
            font-size: 1.8rem;
        }
        .app-card-compact .card-title {
            font-size: 1.05rem;
            font-weight: 800;
            color: #fff;
            letter-spacing: -0.3px;
        }
        .app-card-compact .card-subtitle {
            font-size: 0.72rem;
            font-weight: 500;
            opacity: 0.5;
        }
        .app-card-compact .card-desc {
            font-size: 0.8rem;
            line-height: 1.5;
            color: rgba(255,255,255,0.5);
            flex: 1;
            margin-bottom: 0.8rem;
        }
        .app-card-compact .card-tags {
            display: flex;
            gap: 0.4rem;
            flex-wrap: wrap;
            margin-bottom: 0.8rem;
        }
        .app-card-compact .tag {
            font-size: 0.6rem;
            padding: 2px 8px;
            border-radius: 20px;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.3px;
            border: 1px solid rgba(255,255,255,0.08);
            background: rgba(255,255,255,0.03);
            color: rgba(255,255,255,0.5);
        }
        .app-card-compact .launch-btn {
            display: inline-flex;
            align-items: center;
            justify-content: center;
            gap: 6px;
            padding: 10px 20px;
            border-radius: 10px;
            font-weight: 700;
            font-size: 0.82rem;
            text-decoration: none !important;
            color: #ffffff !important;
            transition: all 0.3s ease;
            border: none;
            cursor: pointer;
            width: 100%;
            text-align: center;
            letter-spacing: 0.3px;
        }
        .app-card-compact .launch-btn:hover {
            filter: brightness(1.15);
            transform: translateY(-1px);
            box-shadow: 0 4px 15px rgba(0,0,0,0.3);
            color: #ffffff !important;
            text-decoration: none !important;
        }
        .app-card-compact .launch-btn:visited,
        .app-card-compact .launch-btn:focus,
        .app-card-compact .launch-btn:active {
            color: #ffffff !important;
            text-decoration: none !important;
        }

        /* ── Category Header ─── */
        .category-header {
            font-size: 1.15rem;
            font-weight: 800;
            color: rgba(255,255,255,0.85);
            margin: 1.8rem 0 1rem;
            padding-bottom: 0.6rem;
            border-bottom: 1px solid rgba(124, 77, 255, 0.15);
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }

        /* ── Calendar Event ─── */
        .cal-event {
            display: flex;
            align-items: center;
            gap: 0.7rem;
            padding: 0.6rem 0;
            border-bottom: 1px solid rgba(255,255,255,0.04);
        }
        .cal-event:last-child { border-bottom: none; }
        .cal-flag { font-size: 1.1rem; }
        .cal-name {
            font-size: 0.85rem;
            color: rgba(255,255,255,0.75);
            flex: 1;
        }
        .cal-importance {
            font-size: 0.65rem;
            font-weight: 700;
            padding: 2px 8px;
            border-radius: 4px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }
        .cal-importance.alta {
            background: rgba(239, 68, 68, 0.15);
            color: #ef4444;
            border: 1px solid rgba(239, 68, 68, 0.3);
        }
        .cal-importance.media {
            background: rgba(245, 158, 11, 0.15);
            color: #f59e0b;
            border: 1px solid rgba(245, 158, 11, 0.3);
        }

        /* ── Fear & Greed Gauge ─── */
        .fg-gauge {
            text-align: center;
            padding: 1rem 0;
        }
        .fg-value {
            font-size: 3rem;
            font-weight: 900;
            font-family: 'JetBrains Mono', monospace;
        }
        .fg-label {
            font-size: 0.9rem;
            font-weight: 600;
            margin-top: 0.3rem;
        }
        .fg-sublabel {
            font-size: 0.7rem;
            color: rgba(255,255,255,0.35);
            margin-top: 0.2rem;
        }

        /* ── Movers Table ─── */
        .mover-row {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 0.4rem 0;
            border-bottom: 1px solid rgba(255,255,255,0.04);
        }
        .mover-ticker {
            font-size: 0.82rem;
            font-weight: 700;
            color: rgba(255,255,255,0.8);
            font-family: 'JetBrains Mono', monospace;
        }
        .mover-price {
            font-size: 0.78rem;
            color: rgba(255,255,255,0.5);
            font-family: 'JetBrains Mono', monospace;
        }
        .mover-change {
            font-size: 0.78rem;
            font-weight: 700;
            font-family: 'JetBrains Mono', monospace;
        }

        /* ── Footer ─── */
        .portal-footer {
            text-align: center;
            padding: 2rem 0 1.5rem;
            border-top: 1px solid rgba(124, 77, 255, 0.08);
            margin-top: 2rem;
        }
        .portal-footer .brand {
            font-size: 0.9rem;
            font-weight: 700;
            color: rgba(255,255,255,0.2);
            letter-spacing: 2px;
            text-transform: uppercase;
        }
        .portal-footer .copy {
            font-size: 0.7rem;
            color: rgba(255,255,255,0.12);
            margin-top: 0.3rem;
        }

        /* ── Responsive ─── */
        @media (max-width: 768px) {
            .ticker-bar {
                gap: 0.3rem;
                padding: 0.5rem 0.6rem;
            }
            .ticker-item {
                min-width: 70px;
            }
            .ticker-price {
                font-size: 0.78rem;
            }
            .ticker-name {
                font-size: 0.55rem;
            }
            .metric-value {
                font-size: 1.2rem;
            }
            .app-card-compact {
                min-height: auto;
                padding: 1rem;
            }
            .category-header {
                font-size: 1rem;
            }
        }
    </style>
    """, unsafe_allow_html=True)


# ─────────────────────────────────────────
# Ticker Bar Component
# ─────────────────────────────────────────
def render_ticker_bar():
    """Renderiza a barra de cotações no topo."""
    from modules.market_data import get_market_overview

    market = get_market_overview()
    if not market:
        return

    items_html = ""
    for name, data in market.items():
        items_html += f"""
        <div class="ticker-item">
            <div class="ticker-name">{name}</div>
            <div class="ticker-price">{data['formatted_price']}</div>
            <div class="ticker-change" style="color:{data['color']}">{data['formatted_change']}</div>
        </div>
        """

    st.markdown(f'<div class="ticker-bar">{items_html}</div>', unsafe_allow_html=True)


# ─────────────────────────────────────────
# Page: Dashboard
# ─────────────────────────────────────────
def page_dashboard():
    """Visão geral do portal com métricas, notícias, agenda e juros."""
    from modules.market_data import get_market_overview, get_top_movers
    from modules.interest_rates import get_brazilian_rates, get_international_rates
    from modules.news_feed import get_news
    from modules.economic_calendar import get_economic_calendar
    from modules.fear_greed import get_fear_greed

    # ── Metric Cards ──
    market = get_market_overview()
    main_metrics = ["IBOV", "S&P 500", "NASDAQ", "DÓLAR", "BTC"]
    cols = st.columns(len(main_metrics))
    for i, name in enumerate(main_metrics):
        with cols[i]:
            if name in market:
                d = market[name]
                st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-label">{name}</div>
                    <div class="metric-value">{d['formatted_price']}</div>
                    <div class="metric-change" style="color:{d['color']}">{d['formatted_change']}</div>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-label">{name}</div>
                    <div class="metric-value">—</div>
                    <div class="metric-change" style="color:#666">carregando...</div>
                </div>
                """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Main Content: Notícias + Agenda | Juros + Sentimento ──
    col_main, col_side = st.columns([3, 1])

    with col_main:
        # Notícias e Agenda lado a lado
        col_news, col_agenda = st.columns(2)

        with col_news:
            st.markdown('<div class="section-panel">', unsafe_allow_html=True)
            st.markdown('<div class="section-title">📰 Principais Notícias</div>', unsafe_allow_html=True)

            tab_br, tab_world = st.tabs(["🇧🇷 Brasil", "🌎 Mundo"])

            with tab_br:
                news_br = get_news("Brasil", max_items=6)
                if news_br:
                    news_html = ""
                    for item in news_br:
                        news_html += f"""
                        <div class="news-item">
                            <div class="news-title"><a href="{item['link']}" target="_blank">{item['title']}</a></div>
                            <div class="news-meta"><span class="news-source">{item['source']}</span> · {item['time_ago']}</div>
                        </div>
                        """
                    st.markdown(news_html, unsafe_allow_html=True)
                else:
                    st.caption("Nenhuma notícia disponível no momento.")

            with tab_world:
                news_world = get_news("Mundo", max_items=6)
                if news_world:
                    news_html = ""
                    for item in news_world:
                        news_html += f"""
                        <div class="news-item">
                            <div class="news-title"><a href="{item['link']}" target="_blank">{item['title']}</a></div>
                            <div class="news-meta"><span class="news-source">{item['source']}</span> · {item['time_ago']}</div>
                        </div>
                        """
                    st.markdown(news_html, unsafe_allow_html=True)
                else:
                    st.caption("Nenhuma notícia disponível no momento.")

            st.markdown('</div>', unsafe_allow_html=True)

        with col_agenda:
            st.markdown('<div class="section-panel">', unsafe_allow_html=True)
            st.markdown('<div class="section-title">📅 Agenda Econômica</div>', unsafe_allow_html=True)

            tab_all, tab_br2, tab_eua = st.tabs(["Todos", "🇧🇷 Brasil", "🇺🇸 EUA"])

            with tab_all:
                events = get_economic_calendar()
                events_html = ""
                for ev in events[:8]:
                    imp_class = "alta" if ev["importance"] == "Alta" else "media"
                    events_html += f"""
                    <div class="cal-event">
                        <span class="cal-flag">{ev['flag']}</span>
                        <span class="cal-name">{ev['name']}</span>
                        <span class="cal-importance {imp_class}">{ev['importance']}</span>
                    </div>
                    """
                st.markdown(events_html, unsafe_allow_html=True)

            with tab_br2:
                from modules.economic_calendar import get_events_by_country
                events_br = get_events_by_country("Brasil")
                events_html = ""
                for ev in events_br:
                    imp_class = "alta" if ev["importance"] == "Alta" else "media"
                    events_html += f"""
                    <div class="cal-event">
                        <span class="cal-flag">{ev['flag']}</span>
                        <span class="cal-name">{ev['name']}</span>
                        <span class="cal-importance {imp_class}">{ev['importance']}</span>
                    </div>
                    """
                st.markdown(events_html, unsafe_allow_html=True)

            with tab_eua:
                events_eua = get_events_by_country("EUA")
                events_html = ""
                for ev in events_eua:
                    imp_class = "alta" if ev["importance"] == "Alta" else "media"
                    events_html += f"""
                    <div class="cal-event">
                        <span class="cal-flag">{ev['flag']}</span>
                        <span class="cal-name">{ev['name']}</span>
                        <span class="cal-importance {imp_class}">{ev['importance']}</span>
                    </div>
                    """
                st.markdown(events_html, unsafe_allow_html=True)

            st.markdown('</div>', unsafe_allow_html=True)

    with col_side:
        # Taxas de Juros
        st.markdown('<div class="section-panel">', unsafe_allow_html=True)
        st.markdown('<div class="section-title">💰 Taxas de Juros</div>', unsafe_allow_html=True)

        br_rates = get_brazilian_rates()
        intl_rates = get_international_rates()

        # Brasil
        rates_html = '<div class="rates-section"><div class="rates-country">🇧🇷 Brasil</div>'
        for name, data in br_rates.items():
            rates_html += f"""
            <div class="rate-row">
                <span class="rate-name">{name}</span>
                <span class="rate-value">{data['formatted']}</span>
            </div>
            """
        rates_html += '</div>'

        # Internacional
        rates_html += '<div class="rates-section" style="margin-top: 0.8rem;"><div class="rates-country">🇺🇸 Estados Unidos</div>'
        for name in ["Fed Funds Rate", "Treasury 10Y"]:
            if name in intl_rates:
                d = intl_rates[name]
                note_html = f'<span class="rate-note" style="color:{d["color"]}">{d["change_formatted"]}</span>'
                rates_html += f"""
                <div class="rate-row">
                    <span class="rate-name">{name}</span>
                    <span class="rate-value">{d['formatted']} {note_html}</span>
                </div>
                """
        rates_html += '</div>'

        rates_html += '<div class="rates-section" style="margin-top: 0.8rem;"><div class="rates-country">🇪🇺 Europa / 🇯🇵 Japão</div>'
        for name in ["BCE (Europa)", "BoJ (Japão)"]:
            if name in intl_rates:
                d = intl_rates[name]
                rates_html += f"""
                <div class="rate-row">
                    <span class="rate-name">{name}</span>
                    <span class="rate-value">{d['formatted']} <span class="rate-note" style="color:#888">{d['change_formatted']}</span></span>
                </div>
                """
        rates_html += '</div>'

        st.markdown(rates_html, unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

        # Fear & Greed
        fg = get_fear_greed()
        st.markdown('<div class="section-panel">', unsafe_allow_html=True)
        st.markdown('<div class="section-title">🎯 Sentimento do Mercado</div>', unsafe_allow_html=True)
        if fg["value"] is not None:
            st.markdown(f"""
            <div class="fg-gauge">
                <div class="fg-value" style="color:{fg['color']}">{fg['value']}</div>
                <div class="fg-label" style="color:{fg['color']}">{fg['classification']}</div>
                <div class="fg-sublabel">Fear & Greed Index (Crypto)</div>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.caption("Indisponível no momento")
        st.markdown('</div>', unsafe_allow_html=True)

        # Maiores Altas e Baixas
        movers = get_top_movers(n=4)
        if movers.get("altas"):
            st.markdown('<div class="section-panel">', unsafe_allow_html=True)
            st.markdown('<div class="section-title">🔥 Destaques do Dia</div>', unsafe_allow_html=True)

            movers_html = '<div style="margin-bottom:0.8rem"><span style="font-size:0.75rem;font-weight:700;color:#00e676">▲ Maiores Altas</span></div>'
            for m in movers["altas"]:
                pct = f"+{m['change_pct']:.2f}%".replace(".", ",")
                movers_html += f"""
                <div class="mover-row">
                    <span class="mover-ticker">{m['ticker']}</span>
                    <span class="mover-price">{m['formatted_price']}</span>
                    <span class="mover-change" style="color:#00e676">{pct}</span>
                </div>
                """

            if movers.get("baixas"):
                movers_html += '<div style="margin: 0.8rem 0 0.5rem"><span style="font-size:0.75rem;font-weight:700;color:#ef4444">▼ Maiores Baixas</span></div>'
                for m in movers["baixas"]:
                    pct = f"{m['change_pct']:.2f}%".replace(".", ",")
                    movers_html += f"""
                    <div class="mover-row">
                        <span class="mover-ticker">{m['ticker']}</span>
                        <span class="mover-price">{m['formatted_price']}</span>
                        <span class="mover-change" style="color:#ef4444">{pct}</span>
                    </div>
                    """

            st.markdown(movers_html, unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)


# ─────────────────────────────────────────
# Page: Aplicações
# ─────────────────────────────────────────
def page_apps():
    """Grid de aplicações organizado por categorias com busca."""

    # Busca
    search = st.text_input(
        "🔍 Buscar aplicação",
        placeholder="Ex: SMC, Opções, Fair Price, IR...",
        label_visibility="collapsed",
    )

    # Filtrar
    filtered = APPS
    if search:
        search_lower = search.lower()
        filtered = [
            a for a in APPS
            if search_lower in a["title"].lower()
            or search_lower in a["subtitle"].lower()
            or search_lower in a["description"].lower()
            or any(search_lower in t.lower() for t in a["tags"])
            or search_lower in a["category"].lower()
        ]

    if not filtered:
        st.info(f'Nenhuma aplicação encontrada para "{search}".')
        return

    # Agrupar por categoria
    categories_order = list(CATEGORIES.keys())
    grouped = {}
    for app in filtered:
        cat = app["category"]
        if cat not in grouped:
            grouped[cat] = []
        grouped[cat].append(app)

    # Renderizar por categoria
    for cat in categories_order:
        if cat not in grouped:
            continue

        icon = CATEGORIES.get(cat, "📌")
        st.markdown(f'<div class="category-header">{icon} {cat}</div>', unsafe_allow_html=True)

        apps_in_cat = grouped[cat]
        cols = st.columns(3)
        for i, app in enumerate(apps_in_cat):
            with cols[i % 3]:
                render_app_card(app)


def render_app_card(app: dict):
    """Renderiza um card de aplicação compacto."""
    tags_html = "".join(f'<span class="tag">{t}</span>' for t in app["tags"])

    st.markdown(f"""
    <div class="app-card-compact" style="border-top: 2px solid {app['accent']};">
        <div class="card-header">
            <span class="card-icon">{app['icon']}</span>
            <div>
                <div class="card-title">{app['title']}</div>
                <div class="card-subtitle" style="color:{app['accent']}">{app['subtitle']}</div>
            </div>
        </div>
        <div class="card-desc">{app['description']}</div>
        <div class="card-tags">{tags_html}</div>
        <a href="{app['url']}" target="_blank" class="launch-btn" style="background:{app['accent']}">Acessar →</a>
    </div>
    """, unsafe_allow_html=True)


# ─────────────────────────────────────────
# Page: Taxas de Juros (Detalhada)
# ─────────────────────────────────────────
def page_rates():
    """Página detalhada de taxas de juros nacionais e internacionais."""
    from modules.interest_rates import get_brazilian_rates, get_international_rates

    st.markdown("### 💰 Taxas de Juros — Panorama Global")
    st.caption("Dados atualizados via API do Banco Central do Brasil e referências internacionais.")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown('<div class="section-panel">', unsafe_allow_html=True)
        st.markdown('<div class="section-title">🇧🇷 Brasil</div>', unsafe_allow_html=True)

        br_rates = get_brazilian_rates()
        for name, data in br_rates.items():
            st.markdown(f"""
            <div class="rate-row">
                <span class="rate-name" style="font-size:1rem">{name}</span>
                <span class="rate-value" style="font-size:1.1rem">{data['formatted']}</span>
            </div>
            """, unsafe_allow_html=True)
            if data["data"] != "—":
                st.caption(f"  Última atualização: {data['data']}")

        st.markdown('</div>', unsafe_allow_html=True)

    with col2:
        st.markdown('<div class="section-panel">', unsafe_allow_html=True)
        st.markdown('<div class="section-title">🌎 Internacional</div>', unsafe_allow_html=True)

        intl_rates = get_international_rates()
        for name, data in intl_rates.items():
            note_html = f'<span class="rate-note" style="color:{data["color"]}">{data["change_formatted"]}</span>'
            st.markdown(f"""
            <div class="rate-row">
                <span class="rate-name" style="font-size:1rem">{name}</span>
                <span class="rate-value" style="font-size:1.1rem">{data['formatted']} {note_html}</span>
            </div>
            """, unsafe_allow_html=True)

        st.markdown('</div>', unsafe_allow_html=True)


# ─────────────────────────────────────────
# Page: Notícias (Expandida)
# ─────────────────────────────────────────
def page_news():
    """Feed de notícias expandido com mais itens."""
    from modules.news_feed import get_news

    st.markdown("### 📰 Notícias Financeiras")
    st.caption("Fontes: InfoMoney, Valor Econômico, Yahoo Finance, CNBC")

    tab_br, tab_world = st.tabs(["🇧🇷 Brasil", "🌎 Mundo"])

    with tab_br:
        news = get_news("Brasil", max_items=15)
        if news:
            for item in news:
                st.markdown(f"""
                <div class="news-item">
                    <div class="news-title"><a href="{item['link']}" target="_blank">{item['title']}</a></div>
                    <div class="news-meta"><span class="news-source">{item['source']}</span> · {item['time_ago']}</div>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.info("Nenhuma notícia disponível no momento.")

    with tab_world:
        news = get_news("Mundo", max_items=15)
        if news:
            for item in news:
                st.markdown(f"""
                <div class="news-item">
                    <div class="news-title"><a href="{item['link']}" target="_blank">{item['title']}</a></div>
                    <div class="news-meta"><span class="news-source">{item['source']}</span> · {item['time_ago']}</div>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.info("Nenhuma notícia disponível no momento.")


# ─────────────────────────────────────────
# Page: Agenda Econômica (Expandida)
# ─────────────────────────────────────────
def page_calendar():
    """Agenda econômica expandida com filtros."""
    from modules.economic_calendar import get_economic_calendar, get_events_by_country

    st.markdown("### 📅 Agenda Econômica")
    st.caption("Principais eventos econômicos recorrentes que impactam os mercados.")

    tab_all, tab_br, tab_eua, tab_global = st.tabs(["📋 Todos", "🇧🇷 Brasil", "🇺🇸 EUA", "🌎 Global"])

    def render_events(events):
        for ev in events:
            imp_class = "alta" if ev["importance"] == "Alta" else "media"
            st.markdown(f"""
            <div class="cal-event">
                <span class="cal-flag">{ev['flag']}</span>
                <span class="cal-name">{ev['name']}</span>
                <span style="font-size:0.7rem;color:rgba(255,255,255,0.35);margin-right:0.5rem">{ev['frequency']}</span>
                <span class="cal-importance {imp_class}">{ev['importance']}</span>
            </div>
            """, unsafe_allow_html=True)

    with tab_all:
        render_events(get_economic_calendar())
    with tab_br:
        render_events(get_events_by_country("Brasil"))
    with tab_eua:
        render_events(get_events_by_country("EUA"))
    with tab_global:
        global_events = [e for e in get_economic_calendar() if e["country"] in ("Europa", "Japão")]
        render_events(global_events)


# ─────────────────────────────────────────
# Page: Sobre
# ─────────────────────────────────────────
def page_about():
    """Informações sobre o portal e stack tecnológico."""
    st.markdown("### ⚡ Sobre o Trader Support")

    st.markdown("""
    **Trader Support** é uma plataforma centralizada de análise financeira que reúne
    screeners inteligentes, ferramentas de valuation, calculadoras e dashboards
    para o mercado brasileiro e internacional.
    """)

    st.markdown("---")

    t1, t2, t3 = st.columns(3)
    with t1:
        st.markdown("""
        **📡 Dados & Integrações**
        - Yahoo Finance API & Fundamentus
        - API do Banco Central do Brasil (SGS)
        - CoinGecko / Binance WebSockets
        - RSS Feeds (InfoMoney, Valor, CNBC)
        - Pipelines automatizados (GitHub Actions)
        """)
    with t2:
        st.markdown("""
        **🧠 Algoritmos & Modelos**
        - **Valuation**: Gordon (DDM), FCD/DCF 2 Estágios, Graham, FCF Yield, Bazin
        - **Institucional (SMC)**: Order Blocks, FVG, BOS/CHOCH, Liquidity Sweeps
        - **Opções**: Black-Scholes (IV/Gregas), Estruturas Assimétricas (Strap/Strip)
        - **MFI Duplo**: Filtro de confluência temporal cruzada (7D & 5D)
        - **Quant**: Transformada Discreta de Fourier (FMFI) & MultiStoch MTF
        """)
    with t3:
        st.markdown("""
        **🚀 Infraestrutura & Stack**
        - Streamlit Cloud (Hospedagem & Frontend)
        - GitHub Actions CI/CD (Agendamento & Deploy)
        - Python · Pandas · NumPy · SciPy
        - Visualizações com Plotly & HTML/CSS responsivo
        - Feed de notícias via RSS (feedparser)
        """)

    st.markdown("---")
    st.markdown(f"""
    <div style="text-align:center; color: rgba(255,255,255,0.3); font-size: 0.8rem;">
        Versão 2.0 · Atualizado em {datetime.now().strftime('%d/%m/%Y')}
    </div>
    """, unsafe_allow_html=True)


# ─────────────────────────────────────────
# Sidebar Navigation
# ─────────────────────────────────────────
def render_sidebar():
    """Renderiza a sidebar de navegação."""
    with st.sidebar:
        st.markdown("""
        <div style="text-align:center; padding: 1rem 0 1.5rem;">
            <div style="font-size: 1.5rem; font-weight: 900; 
                        background: linear-gradient(135deg, #fff 0%, #7c4dff 50%, #00c8ff 100%);
                        -webkit-background-clip: text; -webkit-text-fill-color: transparent;
                        letter-spacing: -1px;">
                📈 Trader Support
            </div>
            <div style="font-size: 0.7rem; color: rgba(255,255,255,0.35); 
                        letter-spacing: 1px; text-transform: uppercase; margin-top: 0.3rem;">
                Portal de Análise Financeira
            </div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("---")

        page = st.radio(
            "Navegação",
            options=[
                "📊 Dashboard",
                "🚀 Aplicações",
                "💰 Taxas de Juros",
                "📰 Notícias",
                "📅 Agenda Econômica",
                "⚙️ Sobre",
            ],
            label_visibility="collapsed",
        )

        st.markdown("---")

        # Stats rápidas
        online_count = len([a for a in APPS if a["status"] == "online"])
        st.markdown(f"""
        <div style="text-align:center; padding: 0.5rem 0;">
            <div style="font-size: 1.6rem; font-weight: 800; color: #7c4dff; 
                        font-family: 'JetBrains Mono', monospace;">{online_count}</div>
            <div style="font-size: 0.65rem; text-transform: uppercase; letter-spacing: 1.5px; 
                        color: rgba(255,255,255,0.35);">Aplicações Online</div>
        </div>
        """, unsafe_allow_html=True)

        return page


# ─────────────────────────────────────────
# Main
# ─────────────────────────────────────────
def main():
    inject_css()

    # Sidebar
    page = render_sidebar()

    # Ticker Bar (em todas as páginas)
    render_ticker_bar()

    # Roteamento
    if page == "📊 Dashboard":
        page_dashboard()
    elif page == "🚀 Aplicações":
        page_apps()
    elif page == "💰 Taxas de Juros":
        page_rates()
    elif page == "📰 Notícias":
        page_news()
    elif page == "📅 Agenda Econômica":
        page_calendar()
    elif page == "⚙️ Sobre":
        page_about()

    # Footer
    year = datetime.now().year
    st.markdown(f"""
    <div class="portal-footer">
        <div class="brand">Trader Support</div>
        <div class="copy">© {year} · Dados via Yahoo Finance, Banco Central do Brasil, RSS Feeds</div>
    </div>
    """, unsafe_allow_html=True)


if __name__ == "__main__":
    main()
