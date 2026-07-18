"""
app.py — Trader Support
Hub profissional para acesso a todas as aplicações de análise financeira.
Hospedado no Streamlit Cloud — apenas links, sem alterar nenhuma aplicação.
"""

import streamlit as st
from datetime import datetime

# ─────────────────────────────────────────
# Page Config
# ─────────────────────────────────────────
st.set_page_config(
    page_title="Trader Support · Portal de Análise Financeira",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ─────────────────────────────────────────
# App Registry
# ─────────────────────────────────────────
APPS = [
    {
        "id": "opcoes",
        "title": "Opções Screener",
        "subtitle": "Análise de Opções B3",
        "description": "Screener de opções com precificação Black-Scholes, identificação de opções subavaliadas e análise de volatilidade implícita para o mercado brasileiro.",
        "url": "https://opcoes-screener.streamlit.app/",
        "icon": "📊",
        "accent": "#ff6b6b",
        "gradient": "linear-gradient(135deg, #1a1a2e 0%, #2d1b3d 100%)",
        "tags": ["Opções", "Black-Scholes", "B3"],
        "status": "online",
    },
    {
        "id": "smc",
        "title": "SMC Screener v3.0",
        "subtitle": "Smart Money Concepts",
        "description": "Detecção automatizada de estruturas institucionais: Order Blocks, Fair Value Gaps, pontos de entrada e saída com Risk/Reward calculado.",
        "url": "https://smc-v30.streamlit.app/",
        "icon": "🏦",
        "accent": "#4ecdc4",
        "gradient": "linear-gradient(135deg, #0f2027 0%, #203a43 50%, #2c5364 100%)",
        "tags": ["SMC", "Order Blocks", "Institucional"],
        "status": "online",
    },
    {
        "id": "screener-mobile",
        "title": "Screener Pro",
        "subtitle": "Screener de Ações Mobile",
        "description": "Screener de ações otimizado para dispositivos móveis com algoritmos de seleção baseados em análise técnica e fundamentalista.",
        "url": "https://screenermobile.streamlit.app/",
        "icon": "📱",
        "accent": "#45b7d1",
        "gradient": "linear-gradient(135deg, #0c0c1d 0%, #1a1a3e 100%)",
        "tags": ["Ações", "Mobile", "Técnica"],
        "status": "online",
    },
    {
        "id": "mfi",
        "title": "Screener MFI",
        "subtitle": "Money Flow Index · Fluxo Financeiro",
        "description": "Screener baseado no indicador MFI duplo com filtros cruzados (MFI1 7D e MFI2 5D). Elimina falsos positivos exigindo confluência de sobrecompra e sobrevenda em ambos os timeframes.",
        "url": "https://screener-mfi.streamlit.app/",
        "icon": "💹",
        "accent": "#00c8ff",
        "gradient": "linear-gradient(135deg, #0a0a2e 0%, #1a0a3e 100%)",
        "tags": ["MFI Duplo", "Fluxo Cruzado", "Confirmação"],
        "status": "online",
    },
    {
        "id": "fcf",
        "title": "Screener FCF Yield",
        "subtitle": "Free Cash Flow · Fluxo de Caixa Livre",
        "description": "Análise fundamentalista profunda baseada em caixa real: FCO − Capex − Juros − Impostos. Classifica ativos como Barato, Justo ou Caro com modos Normal e Conservador.",
        "url": "https://screener-fluxo-de-caixa.streamlit.app/",
        "icon": "🚀",
        "accent": "#7c4dff",
        "gradient": "linear-gradient(135deg, #0f0c29 0%, #302b63 50%, #24243e 100%)",
        "tags": ["FCF Yield", "Fundamentalista", "Value"],
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
        "gradient": "linear-gradient(135deg, #1a0f00 0%, #2d1f0a 100%)",
        "tags": ["Crypto", "Bitcoin", "DeFi"],
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
        "gradient": "linear-gradient(135deg, #1e1b4b 0%, #312e81 100%)",
        "tags": ["Stoch 80", "FMFI", "Quant"],
        "status": "online",
    },
    {
        "id": "week-smc",
        "title": "Week Screener SMC",
        "subtitle": "Smart Money Concepts · Semanal",
        "description": "Screener SMC no timeframe semanal (W1). Mesma lógica institucional do SMC v3.0 — Liquidity Sweeps, BOS/CHOCH, Order Blocks e Fibonacci — aplicada a candles semanais para swing trades de médio prazo.",
        "url": "https://week-smc.streamlit.app/",
        "icon": "📅",
        "accent": "#0ea5e9",
        "gradient": "linear-gradient(135deg, #0c1929 0%, #1a3a5c 50%, #0d2137 100%)",
        "tags": ["SMC", "Semanal", "Swing"],
        "status": "online",
    },
    {
        "id": "fundamentus",
        "title": "Fundamentus Engine",
        "subtitle": "Análise Top-Down B3",
        "description": "Motor quantitativo de análise fundamentalista completo. Inclui painel macroeconômico, mapa setorial, e screener com modelos de valuation e pontuação customizada (ações, BDRs, FIIs e bancos).",
        "url": "https://fundamentus-engine.streamlit.app/",
        "icon": "🏦",
        "accent": "#00ff88",
        "gradient": "linear-gradient(135deg, #0a1628 0%, #111b2e 100%)",
        "tags": ["Top-Down", "Macro", "Valuation"],
        "status": "online",
    },
    {
        "id": "assimetricas",
        "title": "Opções Assimétricas",
        "subtitle": "Screener de Proteção Assimétrica · B3",
        "description": "Screener inteligente que identifica opções com IV historicamente barato (Percentile ≤35%) e monta estruturas Strap/Strip assimétricas com proteção clássica (2:1) ou total (cobertura dinâmica) para o mercado B3.",
        "url": "https://opassimetricas.streamlit.app/",
        "icon": "🛡️",
        "accent": "#00d2ff",
        "gradient": "linear-gradient(135deg, #0a192f 0%, #172a45 50%, #1a1a3e 100%)",
        "tags": ["Opções", "Strap/Strip", "Proteção"],
        "status": "online",
    },
    {
        "id": "fairprice",
        "title": "Fair Price",
        "subtitle": "Valuation Algorítmico · B3",
        "description": "Motor completo de valuation de ações brasileiras selecionando dinamicamente entre o Gordon Growth Model (DDM), FCD 2 Estágios (DCF) ou Múltiplos Relativos, com filtros de segurança contra endividamento e insolvência.",
        "url": "https://fair-price.streamlit.app/",
        "icon": "🎯",
        "accent": "#00e676",
        "gradient": "linear-gradient(135deg, #0a1f16 0%, #112d20 50%, #173b2a 100%)",
        "tags": ["Valuation", "Gordon DDM", "FCD/DCF"],
        "status": "online",
    },
    {
        "id": "future-2",
        "title": "Espaço Reservado",
        "subtitle": "Em Desenvolvimento · 🏗️",
        "description": "Ambiente preparado para futuras ferramentas de rastreamento de fluxo institucional e algoritmos proprietários de alta performance.",
        "url": "#",
        "icon": "🏗️",
        "accent": "#ef4444",
        "gradient": "linear-gradient(135deg, #121214 0%, #1e1e24 100%)",
        "tags": ["Fluxo", "Futuro", "Algoritmos"],
        "status": "offline",
    },
]


# ─────────────────────────────────────────
# Custom CSS
# ─────────────────────────────────────────
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap');
    @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500&display=swap');

    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }

    /* Streamlit branding — gerenciado pelo bloco hide_streamlit_style */

    /* ── Animated background ──────────── */
    .stApp {
        background: #060613;
        background-image:
            radial-gradient(circle at 15% 50%, rgba(124, 77, 255, 0.04) 0%, transparent 50%),
            radial-gradient(circle at 85% 30%, rgba(0, 200, 255, 0.03) 0%, transparent 50%),
            radial-gradient(circle at 50% 80%, rgba(255, 107, 107, 0.02) 0%, transparent 50%);
    }

    /* ── Hero Section ─────────────────── */
    .hero-portal {
        text-align: center;
        padding: 0;
        position: relative;
        margin-bottom: 0.5rem;
    }
    .hero-portal .logo {
        margin: 0;
        padding: 0;
        width: 100%;
        max-height: 250px;
        overflow: hidden;
        display: flex;
        justify-content: center;
        align-items: center;
        line-height: 0;
        position: relative;
    }
    .hero-portal .logo img {
        width: 100%;
        max-width: 100%;
        height: auto;
        object-fit: cover;
        object-position: center 40%;
        display: block;
        margin: 0;
    }
    .hero-portal .hero-text {
        position: absolute;
        bottom: 0;
        left: 0;
        right: 0;
        padding: 2rem 1rem 1rem;
        background: linear-gradient(to top, rgba(6,6,19,0.95) 0%, rgba(6,6,19,0.6) 50%, transparent 100%);
        z-index: 2;
    }
    .hero-portal h1 {
        font-size: 3.2rem;
        font-weight: 900;
        letter-spacing: -2px;
        margin: 0;
        padding: 0;
        background: linear-gradient(135deg, #ffffff 0%, #7c4dff 40%, #00c8ff 70%, #ffffff 100%);
        background-size: 300% 300%;
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        animation: gradient-shift 6s ease infinite;
    }
    @keyframes gradient-shift {
        0% { background-position: 0% 50%; }
        50% { background-position: 100% 50%; }
        100% { background-position: 0% 50%; }
    }
    .hero-portal .tagline {
        font-size: 1.05rem;
        color: rgba(255, 255, 255, 0.6);
        margin-top: 0.4rem;
        font-weight: 300;
        letter-spacing: 0.5px;
    }
    .hero-portal .tagline b {
        color: rgba(255, 255, 255, 0.8);
    }

    /* ── Stats Bar ────────────────────── */
    .stats-bar {
        display: flex;
        justify-content: center;
        gap: 2.5rem;
        margin: 1.5rem 0 2.5rem;
        padding: 1rem 0;
        border-top: 1px solid rgba(124, 77, 255, 0.15);
        border-bottom: 1px solid rgba(124, 77, 255, 0.15);
    }
    .stats-bar .stat {
        text-align: center;
    }
    .stats-bar .stat .num {
        font-size: 1.8rem;
        font-weight: 800;
        color: #7c4dff;
        font-family: 'JetBrains Mono', monospace;
    }
    .stats-bar .stat .lbl {
        font-size: 0.7rem;
        text-transform: uppercase;
        letter-spacing: 1.5px;
        color: rgba(255,255,255,0.4);
        margin-top: 2px;
    }

    /* ── Card Grid — uniform sizing ────── */
    div[data-testid="stHorizontalBlock"] {
        display: grid !important;
        grid-template-columns: repeat(3, 1fr) !important;
        gap: 1.5rem !important;
        align-items: stretch !important;
    }
    div[data-testid="stHorizontalBlock"] > div[data-testid="stColumn"] {
        width: 100% !important;
        flex: none !important;
    }

    /* Tablet and Portrait/Vertical Desktop Screens (widths between 769px and 1200px) */
    @media (min-width: 769px) and (max-width: 1200px) {
        div[data-testid="stHorizontalBlock"] {
            grid-template-columns: repeat(2, 1fr) !important;
        }
    }

    /* ── App Card ──────────────────────── */
    .app-card {
        border-radius: 20px;
        padding: 2rem;
        position: relative;
        overflow: hidden;
        border: 1px solid rgba(255,255,255,0.06);
        transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
        height: 100%;
        min-height: 360px;
        display: flex;
        flex-direction: column;
        box-sizing: border-box;
    }
    .app-card:hover {
        transform: translateY(-6px);
        border-color: rgba(255,255,255,0.12);
        box-shadow: 0 20px 60px rgba(0,0,0,0.5);
    }
    .app-card::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        height: 3px;
        border-radius: 20px 20px 0 0;
    }
    .app-card .card-icon {
        font-size: 2.8rem;
        margin-bottom: 1rem;
        display: block;
    }
    .app-card .card-title {
        font-size: 1.4rem;
        font-weight: 800;
        color: #fff;
        margin: 0 0 0.3rem 0;
        letter-spacing: -0.5px;
    }
    .app-card .card-subtitle {
        font-size: 0.8rem;
        font-weight: 500;
        margin-bottom: 1rem;
        opacity: 0.6;
    }
    .app-card .card-desc {
        font-size: 0.88rem;
        line-height: 1.6;
        color: rgba(255,255,255,0.6);
        flex: 1 1 auto;
        margin-bottom: 1.2rem;
        min-height: 80px;
    }
    .app-card .card-tags {
        display: flex;
        gap: 0.5rem;
        flex-wrap: wrap;
        margin-bottom: 1.2rem;
    }
    .app-card .tag {
        font-size: 0.65rem;
        padding: 3px 10px;
        border-radius: 20px;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        border: 1px solid rgba(255,255,255,0.1);
        background: rgba(255,255,255,0.04);
        color: rgba(255,255,255,0.6);
    }
    .app-card .card-status {
        display: flex;
        align-items: center;
        gap: 6px;
        font-size: 0.72rem;
        color: rgba(255,255,255,0.35);
        margin-bottom: 1rem;
    }
    .app-card .status-dot {
        width: 7px;
        height: 7px;
        border-radius: 50%;
        background: #00e676;
        box-shadow: 0 0 6px rgba(0,230,118,0.5);
        animation: pulse-dot 2s infinite;
    }
    @keyframes pulse-dot {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.4; }
    }

    /* ── Launch Button ────────────────── */
    .launch-btn {
        display: inline-flex;
        align-items: center;
        justify-content: center;
        gap: 8px;
        padding: 14px 28px;
        border-radius: 12px;
        font-weight: 800;
        font-size: 0.95rem;
        text-decoration: none !important;
        color: #ffffff !important;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        border: 1px solid rgba(255,255,255,0.2);
        cursor: pointer;
        width: 100%;
        text-align: center;
        letter-spacing: 0.5px;
        text-shadow: 0 1px 4px rgba(0,0,0,0.6);
    }
    .launch-btn:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 25px rgba(0,0,0,0.4);
        color: #ffffff !important;
        text-decoration: none !important;
        filter: brightness(1.15);
    }
    .launch-btn:visited,
    .launch-btn:focus,
    .launch-btn:active {
        color: #ffffff !important;
        text-decoration: none !important;
    }

    /* ── Footer ───────────────────────── */
    .portal-footer {
        text-align: center;
        padding: 3rem 0 2rem;
        border-top: 1px solid rgba(124, 77, 255, 0.1);
        margin-top: 3rem;
    }
    .portal-footer .brand {
        font-size: 1.1rem;
        font-weight: 700;
        color: rgba(255,255,255,0.3);
        letter-spacing: 2px;
        text-transform: uppercase;
    }
    .portal-footer .copy {
        font-size: 0.75rem;
        color: rgba(255,255,255,0.15);
        margin-top: 0.5rem;
    }
    .portal-footer a {
        color: #7c4dff;
        text-decoration: none;
    }
    .portal-footer a:hover {
        color: #b388ff;
    }

    /* ── Responsive ───────────────────── */
    @media (max-width: 768px) {
        .hero-portal .logo {
            max-height: 200px !important;
        }
        .hero-portal .hero-text {
            padding: 1.5rem 0.8rem 0.8rem !important;
        }
        .hero-portal h1 {
            font-size: 1.8rem !important;
            letter-spacing: -1px !important;
            white-space: nowrap !important;
        }
        .hero-portal .tagline {
            font-size: 0.78rem !important;
            line-height: 1.4 !important;
        }
        .stats-bar {
            gap: 1rem !important;
            flex-wrap: wrap;
        }
        .stats-bar .stat .num {
            font-size: 1.3rem !important;
        }
        div[data-testid="stHorizontalBlock"] {
            grid-template-columns: 1fr !important;
        }
        .app-card {
            min-height: auto !important;
            padding: 1.5rem !important;
        }
        .app-card .card-title {
            font-size: 1.2rem !important;
        }
        .app-card .card-desc {
            min-height: auto !important;
        }
    }
</style>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────
# Hero Section
# ─────────────────────────────────────────
import base64 as _b64
from pathlib import Path as _Path

_HERO_IMG = _Path(__file__).parent / "assets" / "hero_chart.png"
with open(_HERO_IMG, "rb") as _f:
    _img_b64 = _b64.b64encode(_f.read()).decode()

st.markdown(f"""
<div class="hero-portal">
    <span class="logo">
        <img src="data:image/png;base64,{_img_b64}" alt="Trading Chart" />
        <div class="hero-text">
            <h1>Trader Support</h1>
            <p class="tagline">
                Plataforma de <b>Análise Financeira</b> — Screeners inteligentes para
                <b>Ações</b>, <b>Opções</b>, <b>Crypto</b> e <b>Smart Money</b>
            </p>
        </div>
    </span>
</div>
""", unsafe_allow_html=True)

# Stats
st.markdown(f"""
<div class="stats-bar">
    <div class="stat">
        <div class="num">{len([a for a in APPS if a['status'] == "online"])}</div>
        <div class="lbl">Aplicações</div>
    </div>
    <div class="stat">
        <div class="num">500+</div>
        <div class="lbl">Ativos Monitorados</div>
    </div>
    <div class="stat">
        <div class="num">24h</div>
        <div class="lbl">Atualização</div>
    </div>
    <div class="stat">
        <div class="num">∞</div>
        <div class="lbl">Acesso Gratuito</div>
    </div>
</div>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────
# App Grid (3 columns × 2 rows)
# ─────────────────────────────────────────
def render_card(app: dict):
    """Render a single app card with HTML."""
    tags_html = "".join(
        f'<span class="tag">{t}</span>' for t in app["tags"]
    )

    status_html = ""
    if app['status'] == "online":
        status_html = f'<div class="card-status"><span class="status-dot"></span>Online</div>'
    else:
        status_html = f'<div class="card-status"><span class="status-dot" style="background: #ef4444; box-shadow: 0 0 6px rgba(239, 68, 68, 0.5); animation: none;"></span>Em Desenvolvimento</div>'

    btn_html = ""
    if app['status'] == "online":
        btn_html = f'<a href="{app["url"]}" target="_blank" class="launch-btn" style="background:{app["accent"]};">Acessar Aplicação →</a>'
    else:
        btn_html = f'<a href="{app["url"]}" class="launch-btn" style="background:transparent; color: rgba(255,255,255,0.4) !important; border: 1px solid rgba(255,255,255,0.1); cursor: not-allowed; text-shadow: none;">Em Construção</a>'

    st.markdown(f"""
    <div class="app-card" style="background: {app['gradient']};">
        <div style="position:absolute;top:0;left:0;right:0;height:3px;background:{app['accent']};border-radius:20px 20px 0 0;"></div>
        <span class="card-icon">{app['icon']}</span>
        <div class="card-title">{app['title']}</div>
        <div class="card-subtitle" style="color:{app['accent']};">{app['subtitle']}</div>
        {status_html}
        <div class="card-desc">{app['description']}</div>
        <div class="card-tags">{tags_html}</div>
        {btn_html}
    </div>
    """, unsafe_allow_html=True)


# Dynamic App Grid
cols = st.columns(len(APPS), gap="medium")
for i, app in enumerate(APPS):
    with cols[i]:
        render_card(app)


# ─────────────────────────────────────────
# Technology Section
# ─────────────────────────────────────────
st.markdown("<br>", unsafe_allow_html=True)

with st.expander("⚡ Stack Tecnológico", expanded=False):
    t1, t2, t3 = st.columns(3)
    with t1:
        st.markdown("""
        **📡 Dados & Integrações**
        - Yahoo Finance API & Fundamentus
        - CoinGecko / Binance WebSockets
        - Cotações em tempo real e dados fundamentalistas históricos
        - Pipelines automatizados (GitHub Actions Cron)
        """)
    with t2:
        st.markdown("""
        **🧠 Algoritmos & Modelos**
        - **Valuation**: Gordon (DDM), FCD/DCF de 2 Estágios, Graham, FCF Yield, Bazin
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
        """)


# ─────────────────────────────────────────
# Footer
# ─────────────────────────────────────────
year = datetime.now().year
st.markdown(f"""
<div class="portal-footer">
    <div class="brand">Trader Support</div>
    <div class="copy">
        © {year} · Dados via Yahoo Finance
    </div>
</div>
""", unsafe_allow_html=True)
