"""
app.py — Trader Support
Portal profissional de análise financeira com dashboard de mercado,
notícias, taxas de juros e acesso organizado a todas as aplicações.
Hospedado no Streamlit Cloud.
"""

import streamlit as st
from datetime import datetime
import base64 as _b64
import math
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


def st_html(content: str):
    """
    Renderiza HTML limpando qualquer espaçamento no início das linhas.
    Isso impede que o Markdown do Streamlit confunda HTML com blocos de código (<pre><code>).
    """
    clean_lines = [line.strip() for line in content.split("\n") if line.strip()]
    st.markdown("".join(clean_lines), unsafe_allow_html=True)


def render_fear_greed_gauge_svg(value: int, classification: str, color: str) -> str:
    """
    Renderiza um velocímetro (Gauge) SVG em formato semicircular
    com faixas em Vermelho, Laranja, Amarelo, Verde Claro e Verde Brilhante,
    ponteiro direcionado e valor numérico do índice em destaque.
    """
    val = max(0, min(100, int(value)))
    angle_deg = -180.0 + (val / 100.0) * 180.0
    rad = math.radians(angle_deg)
    nx = 100.0 + 52.0 * math.cos(rad)
    ny = 90.0 + 52.0 * math.sin(rad)

    return f"""
    <div style="text-align: center; padding: 0.1rem 0;">
        <svg viewBox="0 0 200 110" width="100%" height="135" style="max-width: 220px; margin: 0 auto; display: block;">
            <defs>
                <filter id="needleGlow" x="-20%" y="-20%" width="140%" height="140%">
                    <feGaussianBlur stdDeviation="1.5" result="blur" />
                    <feComposite in="SourceGraphic" in2="blur" operator="over" />
                </filter>
            </defs>

            <!-- Arcos Coloridos do Velocímetro (Vermelho -> Laranja -> Amarelo -> Verde Claro -> Verde) -->
            <path d="M 30,90 A 70,70 0 0,1 50.5,40.5" fill="none" stroke="#ef4444" stroke-width="11" stroke-linecap="round" />
            <path d="M 50.5,40.5 A 70,70 0 0,1 89,21" fill="none" stroke="#f97316" stroke-width="11" />
            <path d="M 89,21 A 70,70 0 0,1 111,21" fill="none" stroke="#eab308" stroke-width="11" />
            <path d="M 111,21 A 70,70 0 0,1 149.5,40.5" fill="none" stroke="#84cc16" stroke-width="11" />
            <path d="M 149.5,40.5 A 70,70 0 0,1 170,90" fill="none" stroke="#00e676" stroke-width="11" stroke-linecap="round" />

            <!-- Marcas de escala -->
            <text x="20" y="104" font-size="7.5" font-weight="700" fill="rgba(255,255,255,0.4)" font-family="sans-serif">0</text>
            <text x="96" y="12" font-size="7.5" font-weight="700" fill="rgba(255,255,255,0.4)" font-family="sans-serif">50</text>
            <text x="171" y="104" font-size="7.5" font-weight="700" fill="rgba(255,255,255,0.4)" font-family="sans-serif">100</text>

            <!-- Ponteiro / Agulha -->
            <line x1="100" y1="90" x2="{nx:.1f}" y2="{ny:.1f}" stroke="#ffffff" stroke-width="3" stroke-linecap="round" filter="url(#needleGlow)" />
            <circle cx="100" cy="90" r="6" fill="#7c4dff" />
            <circle cx="100" cy="90" r="3" fill="#ffffff" />
        </svg>

        <div style="font-size: 2.2rem; font-weight: 900; color: #ffffff; font-family: 'JetBrains Mono', monospace; line-height: 1; margin-top: -10px;">
            {val}
        </div>
        <div style="font-size: 0.82rem; font-weight: 700; color: {color}; text-transform: uppercase; letter-spacing: 1px; margin-top: 4px;">
            {classification}
        </div>
        <div style="font-size: 0.65rem; color: rgba(255,255,255,0.35); margin-top: 2px;">
            Fear & Greed Index
        </div>
    </div>
    """


# ─────────────────────────────────────────
# Custom CSS
# ─────────────────────────────────────────
def inject_css():
    st_html("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap');
        @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500;600&display=swap');

        html, body, [class*="css"] {
            font-family: 'Inter', sans-serif;
        }

        /* ── Main Container Top Padding (Prevents Top Clipping) ─── */
        .block-container {
            padding-top: 3.2rem !important;
            padding-bottom: 1.2rem !important;
            padding-left: 1.8rem !important;
            padding-right: 1.8rem !important;
            max-width: 98% !important;
        }

        /* ── Global Background ─── */
        .stApp {
            background: #060613;
            background-image:
                radial-gradient(circle at 15% 50%, rgba(124, 77, 255, 0.03) 0%, transparent 50%),
                radial-gradient(circle at 85% 30%, rgba(0, 200, 255, 0.02) 0%, transparent 50%);
        }

        /* ── Streamlit Header Transparent ─── */
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        header[data-testid="stHeader"] {
            background: transparent !important;
            height: 2.2rem !important;
        }

        /* ── Sidebar Container & Background ─── */
        section[data-testid="stSidebar"] {
            background: linear-gradient(180deg, #090919 0%, #0d0d26 100%) !important;
            border-right: 1px solid rgba(124, 77, 255, 0.15) !important;
        }

        /* ── Premium Sidebar Radio Menu Items ─── */
        section[data-testid="stSidebar"] div[data-testid="stRadio"] > div {
            gap: 0.4rem !important;
        }
        section[data-testid="stSidebar"] div[data-testid="stRadio"] label {
            background: rgba(255, 255, 255, 0.02) !important;
            border: 1px solid rgba(255, 255, 255, 0.06) !important;
            border-radius: 12px !important;
            padding: 0.65rem 1rem !important;
            margin-bottom: 0.1rem !important;
            cursor: pointer !important;
            transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1) !important;
            width: 100% !important;
            display: flex !important;
            align-items: center !important;
        }
        /* Hide standard radio circle */
        section[data-testid="stSidebar"] div[data-testid="stRadio"] label > div:first-child {
            display: none !important;
        }
        section[data-testid="stSidebar"] div[data-testid="stRadio"] label div[data-testid="stMarkdownContainer"] p {
            font-size: 0.9rem !important;
            font-weight: 500 !important;
            color: rgba(255, 255, 255, 0.65) !important;
            margin: 0 !important;
            letter-spacing: 0.2px !important;
        }

        /* Hover State */
        section[data-testid="stSidebar"] div[data-testid="stRadio"] label:hover {
            background: rgba(124, 77, 255, 0.12) !important;
            border-color: rgba(124, 77, 255, 0.35) !important;
            transform: translateX(4px) !important;
        }
        section[data-testid="stSidebar"] div[data-testid="stRadio"] label:hover p {
            color: #ffffff !important;
        }

        /* Checked / Active Menu State */
        section[data-testid="stSidebar"] div[data-testid="stRadio"] label:has(input:checked),
        section[data-testid="stSidebar"] div[data-testid="stRadio"] label[aria-checked="true"] {
            background: linear-gradient(135deg, rgba(124, 77, 255, 0.28) 0%, rgba(0, 200, 255, 0.18) 100%) !important;
            border: 1px solid rgba(124, 77, 255, 0.6) !important;
            box-shadow: 0 4px 20px rgba(124, 77, 255, 0.25) !important;
            position: relative !important;
        }
        section[data-testid="stSidebar"] div[data-testid="stRadio"] label:has(input:checked)::before,
        section[data-testid="stSidebar"] div[data-testid="stRadio"] label[aria-checked="true"]::before {
            content: '' !important;
            position: absolute !important;
            left: 0 !important;
            top: 15% !important;
            bottom: 15% !important;
            width: 4px !important;
            background: #7c4dff !important;
            border-radius: 0 4px 4px 0 !important;
            box-shadow: 0 0 10px #7c4dff !important;
        }
        section[data-testid="stSidebar"] div[data-testid="stRadio"] label:has(input:checked) p,
        section[data-testid="stSidebar"] div[data-testid="stRadio"] label[aria-checked="true"] p {
            color: #ffffff !important;
            font-weight: 700 !important;
        }

        /* ── Ticker Bar ─── */
        .ticker-bar {
            display: flex;
            justify-content: space-between;
            align-items: center;
            gap: 0.5rem;
            padding: 0.6rem 1rem;
            background: linear-gradient(135deg, rgba(10, 10, 30, 0.95) 0%, rgba(15, 15, 45, 0.95) 100%);
            border: 1px solid rgba(124, 77, 255, 0.2);
            border-radius: 12px;
            margin-bottom: 1rem;
            overflow-x: auto;
            flex-wrap: nowrap;
        }
        .ticker-item {
            text-align: center;
            min-width: 90px;
            flex-shrink: 0;
        }
        .ticker-name {
            font-size: 0.72rem;
            font-weight: 800;
            color: #00c8ff;
            text-transform: uppercase;
            letter-spacing: 1px;
            margin-bottom: 2px;
        }
        .ticker-price {
            font-size: 0.92rem;
            font-weight: 700;
            color: #ffffff;
            font-family: 'JetBrains Mono', monospace;
        }
        .ticker-change {
            font-size: 0.72rem;
            font-weight: 600;
            font-family: 'JetBrains Mono', monospace;
        }

        /* ── Metric Cards ─── */
        .metric-card {
            background: linear-gradient(135deg, rgba(15, 15, 35, 0.85) 0%, rgba(20, 20, 50, 0.65) 100%);
            border: 1px solid rgba(124, 77, 255, 0.18);
            border-radius: 14px;
            padding: 0.85rem 0.8rem;
            text-align: center;
            transition: all 0.3s ease;
        }
        .metric-card:hover {
            border-color: rgba(124, 77, 255, 0.4);
            transform: translateY(-2px);
        }
        .metric-label {
            font-size: 0.85rem;
            font-weight: 800;
            color: #7c4dff;
            text-transform: uppercase;
            letter-spacing: 1px;
            margin-bottom: 0.25rem;
        }
        .metric-value {
            font-size: 1.45rem;
            font-weight: 800;
            color: #ffffff;
            font-family: 'JetBrains Mono', monospace;
        }
        .metric-change {
            font-size: 0.78rem;
            font-weight: 600;
            font-family: 'JetBrains Mono', monospace;
            margin-top: 0.1rem;
        }

        /* ── Section Panel ─── */
        .section-panel {
            background: linear-gradient(135deg, rgba(12, 12, 30, 0.8) 0%, rgba(18, 18, 45, 0.6) 100%);
            border: 1px solid rgba(124, 77, 255, 0.1);
            border-radius: 14px;
            padding: 0.95rem 1.1rem;
            margin-bottom: 0.8rem;
            box-sizing: border-box;
            height: 100%;
        }
        .section-title {
            font-size: 0.92rem;
            font-weight: 700;
            color: rgba(255,255,255,0.9);
            margin-bottom: 0.6rem;
            display: flex;
            align-items: center;
            gap: 0.4rem;
        }

        /* ── News Items ─── */
        .news-item {
            padding: 0.45rem 0;
            border-bottom: 1px solid rgba(255,255,255,0.05);
            transition: background 0.2s ease;
        }
        .news-item:hover {
            background: rgba(124, 77, 255, 0.05);
            border-radius: 6px;
            padding-left: 0.3rem;
        }
        .news-item:last-child {
            border-bottom: none;
        }
        .news-title {
            font-size: 0.82rem;
            font-weight: 500;
            color: rgba(255,255,255,0.85);
            line-height: 1.3;
            margin-bottom: 0.15rem;
        }
        .news-title a {
            color: rgba(255,255,255,0.85) !important;
            text-decoration: none !important;
        }
        .news-title a:hover {
            color: #7c4dff !important;
        }
        .news-meta {
            font-size: 0.7rem;
            color: rgba(255,255,255,0.4);
        }
        .news-source {
            color: #7c4dff;
            font-weight: 600;
        }

        /* ── Rates Table ─── */
        .rates-section {
            margin-bottom: 0.6rem;
        }
        .rates-country {
            font-size: 0.78rem;
            font-weight: 700;
            color: rgba(255,255,255,0.65);
            margin-bottom: 0.3rem;
            display: flex;
            align-items: center;
            gap: 0.3rem;
        }
        .rate-row {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 0.28rem 0;
            border-bottom: 1px solid rgba(255,255,255,0.04);
        }
        .rate-name {
            font-size: 0.8rem;
            color: rgba(255,255,255,0.7);
        }
        .rate-value {
            font-size: 0.82rem;
            font-weight: 700;
            color: #fff;
            font-family: 'JetBrains Mono', monospace;
        }
        .rate-note {
            font-size: 0.68rem;
            font-weight: 500;
            margin-left: 0.2rem;
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
            gap: 0.5rem;
            padding: 0.38rem 0;
            border-bottom: 1px solid rgba(255,255,255,0.04);
        }
        .cal-event:last-child { border-bottom: none; }
        .cal-flag { font-size: 0.95rem; }
        .cal-name {
            font-size: 0.8rem;
            color: rgba(255,255,255,0.75);
            flex: 1;
        }
        .cal-importance {
            font-size: 0.6rem;
            font-weight: 700;
            padding: 1px 5px;
            border-radius: 4px;
            text-transform: uppercase;
            letter-spacing: 0.3px;
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

        /* ── Movers Table ─── */
        .mover-row {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 0.28rem 0;
            border-bottom: 1px solid rgba(255,255,255,0.04);
        }
        .mover-ticker {
            font-size: 0.78rem;
            font-weight: 700;
            color: rgba(255,255,255,0.85);
            font-family: 'JetBrains Mono', monospace;
        }
        .mover-price {
            font-size: 0.74rem;
            color: rgba(255,255,255,0.5);
            font-family: 'JetBrains Mono', monospace;
        }
        .mover-change {
            font-size: 0.74rem;
            font-weight: 700;
            font-family: 'JetBrains Mono', monospace;
        }

        /* ── Footer ─── */
        .portal-footer {
            text-align: center;
            padding: 1.5rem 0 1rem;
            border-top: 1px solid rgba(124, 77, 255, 0.08);
            margin-top: 1.5rem;
        }
        .portal-footer .brand {
            font-size: 0.85rem;
            font-weight: 700;
            color: rgba(255,255,255,0.2);
            letter-spacing: 2px;
            text-transform: uppercase;
        }
        .portal-footer .copy {
            font-size: 0.68rem;
            color: rgba(255,255,255,0.12);
            margin-top: 0.2rem;
        }

        /* ── Responsive ─── */
        @media (max-width: 768px) {
            .block-container {
                padding-top: 2rem !important;
                padding-left: 0.8rem !important;
                padding-right: 0.8rem !important;
            }
            .ticker-bar {
                gap: 0.3rem;
                padding: 0.4rem 0.5rem;
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
    """)


# ─────────────────────────────────────────
# Ticker Bar Component (Barra Superior Completa)
# ─────────────────────────────────────────
def render_ticker_bar():
    """Renderiza a barra de cotações no topo com nomes destacados."""
    from modules.market_data import get_market_overview

    market = get_market_overview()
    if not market:
        return

    items_html = ""
    for name, data in market.items():
        items_html += f'<div class="ticker-item"><div class="ticker-name">{name}</div><div class="ticker-price">{data["formatted_price"]}</div><div class="ticker-change" style="color:{data["color"]}">{data["formatted_change"]}</div></div>'

    st_html(f'<div class="ticker-bar">{items_html}</div>')


# ─────────────────────────────────────────
# Page: Dashboard
# ─────────────────────────────────────────
def page_dashboard():
    """Visão geral do portal com 5 Destaques, Notícias expandidas e novos índices globais."""
    from modules.market_data import get_market_overview, get_top_movers
    from modules.interest_rates import get_brazilian_rates, get_international_rates
    from modules.news_feed import get_news
    from modules.economic_calendar import get_economic_calendar
    from modules.fear_greed import get_fear_greed

    # ── Metric Cards (4 Indicadores Globais Principais) ──
    market = get_market_overview()
    main_metrics = ["IBOV", "STOXX 50", "NIKKEI 225", "DÓLAR"]
    cols = st.columns(len(main_metrics))
    for i, name in enumerate(main_metrics):
        with cols[i]:
            if name in market:
                d = market[name]
                st_html(f'<div class="metric-card"><div class="metric-label">{name}</div><div class="metric-value">{d["formatted_price"]}</div><div class="metric-change" style="color:{d["color"]}">{d["formatted_change"]}</div></div>')
            else:
                st_html(f'<div class="metric-card"><div class="metric-label">{name}</div><div class="metric-value">—</div><div class="metric-change" style="color:#666">carregando...</div></div>')

    st_html('<div style="margin-bottom: 0.8rem;"></div>')

    # ── Main Layout (4 Colunas): Destaques (5 Altas/Baixas) | Notícias (10 itens) | Agenda | Juros + Sentimento (Velocímetro) ──
    col_mov, col_news, col_agenda, col_right = st.columns([1.4, 2.2, 2.0, 1.8])

    # ── Col 1: 🔥 Destaques do Dia (5 Altas e 5 Baixas mais relevantes) ──
    with col_mov:
        movers = get_top_movers(n=5)
        st_html('<div class="section-panel"><div class="section-title">🔥 Destaques</div>')
        if movers.get("altas"):
            movers_html = '<div style="margin-bottom:0.2rem"><span style="font-size:0.72rem;font-weight:700;color:#00e676">▲ Altas (Top 5)</span></div>'
            for m in movers["altas"]:
                pct = f"+{m['change_pct']:.1f}%".replace(".", ",")
                movers_html += f'<div class="mover-row"><span class="mover-ticker">{m["ticker"]}</span><span class="mover-price">{m["formatted_price"]}</span><span class="mover-change" style="color:#00e676">{pct}</span></div>'

            if movers.get("baixas"):
                movers_html += '<div style="margin: 0.5rem 0 0.2rem"><span style="font-size:0.72rem;font-weight:700;color:#ef4444">▼ Baixas (Top 5)</span></div>'
                for m in movers["baixas"]:
                    pct = f"{m['change_pct']:.1f}%".replace(".", ",")
                    movers_html += f'<div class="mover-row"><span class="mover-ticker">{m["ticker"]}</span><span class="mover-price">{m["formatted_price"]}</span><span class="mover-change" style="color:#ef4444">{pct}</span></div>'

            st_html(movers_html)
        else:
            st.caption("Carregando...")
        st_html('</div>')

    # ── Col 2: 📰 Principais Notícias (Feed Expandido com 10 notícias intercaladas) ──
    with col_news:
        st_html('<div class="section-panel"><div class="section-title">📰 Principais Notícias</div>')

        tab_br, tab_world = st.tabs(["Brasil", "Mundo"])

        with tab_br:
            news_br = get_news("Brasil", max_items=10)
            if news_br:
                news_html = ""
                for item in news_br:
                    news_html += f'<div class="news-item"><div class="news-title"><a href="{item["link"]}" target="_blank">{item["title"]}</a></div><div class="news-meta"><span class="news-source">{item["source"]}</span> · {item["time_ago"]}</div></div>'
                st_html(news_html)
            else:
                st.caption("Nenhuma notícia disponível no momento.")

        with tab_world:
            news_world = get_news("Mundo", max_items=10)
            if news_world:
                news_html = ""
                for item in news_world:
                    news_html += f'<div class="news-item"><div class="news-title"><a href="{item["link"]}" target="_blank">{item["title"]}</a></div><div class="news-meta"><span class="news-source">{item["source"]}</span> · {item["time_ago"]}</div></div>'
                st_html(news_html)
            else:
                st.caption("Nenhuma notícia disponível no momento.")

        st_html('</div>')

    # ── Col 3: 📅 Agenda Econômica ──
    with col_agenda:
        st_html('<div class="section-panel"><div class="section-title">📅 Agenda Econômica</div>')

        tab_all, tab_br2, tab_eua = st.tabs(["Todos", "Brasil", "EUA"])

        with tab_all:
            events = get_economic_calendar()
            events_html = ""
            for ev in events[:8]:
                imp_class = "alta" if ev["importance"] == "Alta" else "media"
                events_html += f'<div class="cal-event"><span class="cal-flag">{ev["flag"]}</span><span class="cal-name">{ev["name"]}</span><span class="cal-importance {imp_class}">{ev["importance"]}</span></div>'
            st_html(events_html)

        with tab_br2:
            from modules.economic_calendar import get_events_by_country
            events_br = get_events_by_country("Brasil")
            events_html = ""
            for ev in events_br[:8]:
                imp_class = "alta" if ev["importance"] == "Alta" else "media"
                events_html += f'<div class="cal-event"><span class="cal-flag">{ev["flag"]}</span><span class="cal-name">{ev["name"]}</span><span class="cal-importance {imp_class}">{ev["importance"]}</span></div>'
            st_html(events_html)

        with tab_eua:
            events_eua = get_events_by_country("EUA")
            events_html = ""
            for ev in events_eua[:8]:
                imp_class = "alta" if ev["importance"] == "Alta" else "media"
                events_html += f'<div class="cal-event"><span class="cal-flag">{ev["flag"]}</span><span class="cal-name">{ev["name"]}</span><span class="cal-importance {imp_class}">{ev["importance"]}</span></div>'
            st_html(events_html)

        st_html('</div>')

    # ── Col 4: 💰 Taxas de Juros & 🎯 Sentimento (Velocímetro em SVG) ──
    with col_right:
        # Box Taxas de Juros
        st_html('<div class="section-panel"><div class="section-title">💰 Taxas de Juros</div>')

        br_rates = get_brazilian_rates()
        intl_rates = get_international_rates()

        rates_html = '<div class="rates-section"><div class="rates-country">Brasil</div>'
        for name, data in br_rates.items():
            rates_html += f'<div class="rate-row"><span class="rate-name">{name}</span><span class="rate-value">{data["formatted"]}</span></div>'
        rates_html += '</div>'

        rates_html += '<div class="rates-section" style="margin-top:0.4rem"><div class="rates-country">EUA / Internacional</div>'
        for name in ["Fed Funds Rate", "Treasury 10Y", "BCE (Europa)", "BoJ (Japão)"]:
            if name in intl_rates:
                d = intl_rates[name]
                note = f' <span class="rate-note" style="color:{d["color"]}">{d["change_formatted"]}</span>' if d.get("change_formatted") else ''
                rates_html += f'<div class="rate-row"><span class="rate-name">{name}</span><span class="rate-value">{d["formatted"]}{note}</span></div>'
        rates_html += '</div>'

        st_html(rates_html)
        st_html('</div>')

        # Box Sentimento do Mercado (Velocímetro SVG)
        fg = get_fear_greed()
        st_html('<div class="section-panel"><div class="section-title">🎯 Sentimento do Mercado</div>')
        if fg["value"] is not None:
            svg_gauge = render_fear_greed_gauge_svg(fg["value"], fg["classification"], fg["color"])
            st_html(svg_gauge)
        else:
            st.caption("Indisponível no momento")
        st_html('</div>')


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
        st_html(f'<div class="category-header">{icon} {cat}</div>')

        apps_in_cat = grouped[cat]
        cols = st.columns(3)
        for i, app in enumerate(apps_in_cat):
            with cols[i % 3]:
                render_app_card(app)


def render_app_card(app: dict):
    """Renderiza um card de aplicação compacto."""
    tags_html = "".join(f'<span class="tag">{t}</span>' for t in app["tags"])

    st_html(f'<div class="app-card-compact" style="border-top: 2px solid {app["accent"]};"><div class="card-header"><span class="card-icon">{app["icon"]}</span><div><div class="card-title">{app["title"]}</div><div class="card-subtitle" style="color:{app["accent"]}">{app["subtitle"]}</div></div></div><div class="card-desc">{app["description"]}</div><div class="card-tags">{tags_html}</div><a href="{app["url"]}" target="_blank" class="launch-btn" style="background:{app["accent"]}">Acessar →</a></div>')


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
        st_html('<div class="section-panel"><div class="section-title">Brasil</div>')

        br_rates = get_brazilian_rates()
        for name, data in br_rates.items():
            st_html(f'<div class="rate-row"><span class="rate-name" style="font-size:1rem">{name}</span><span class="rate-value" style="font-size:1.1rem">{data["formatted"]}</span></div>')
            if data["data"] != "—":
                st.caption(f"  Última atualização: {data['data']}")

        st_html('</div>')

    with col2:
        st_html('<div class="section-panel"><div class="section-title">EUA / Internacional</div>')

        intl_rates = get_international_rates()
        for name, data in intl_rates.items():
            note_html = f'<span class="rate-note" style="color:{data["color"]}">{data["change_formatted"]}</span>'
            st_html(f'<div class="rate-row"><span class="rate-name" style="font-size:1rem">{name}</span><span class="rate-value" style="font-size:1.1rem">{data["formatted"]} {note_html}</span></div>')

        st_html('</div>')


# ─────────────────────────────────────────
# Page: Notícias (Expandida)
# ─────────────────────────────────────────
def page_news():
    """Feed de notícias expandido com mais itens."""
    from modules.news_feed import get_news

    st.markdown("### 📰 Notícias Financeiras")
    st.caption("Fontes: InfoMoney, Valor Econômico, Exame, G1 Economia, Money Times, Investing.com, CNN Economia, Yahoo Finance, CNBC, MarketWatch, Reuters, WSJ")

    tab_br, tab_world = st.tabs(["Brasil", "Mundo"])

    with tab_br:
        news = get_news("Brasil", max_items=15)
        if news:
            for item in news:
                st_html(f'<div class="news-item"><div class="news-title"><a href="{item["link"]}" target="_blank">{item["title"]}</a></div><div class="news-meta"><span class="news-source">{item["source"]}</span> · {item["time_ago"]}</div></div>')
        else:
            st.info("Nenhuma notícia disponível no momento.")

    with tab_world:
        news = get_news("Mundo", max_items=15)
        if news:
            for item in news:
                st_html(f'<div class="news-item"><div class="news-title"><a href="{item["link"]}" target="_blank">{item["title"]}</a></div><div class="news-meta"><span class="news-source">{item["source"]}</span> · {item["time_ago"]}</div></div>')
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

    tab_all, tab_br, tab_eua, tab_global = st.tabs(["📋 Todos", "Brasil", "EUA", "🌎 Global"])

    def render_events(events):
        for ev in events:
            imp_class = "alta" if ev["importance"] == "Alta" else "media"
            st_html(f'<div class="cal-event"><span class="cal-flag">{ev["flag"]}</span><span class="cal-name">{ev["name"]}</span><span style="font-size:0.7rem;color:rgba(255,255,255,0.35);margin-right:0.5rem">{ev["frequency"]}</span><span class="cal-importance {imp_class}">{ev["importance"]}</span></div>')

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
        - RSS Feeds (InfoMoney, Valor, Exame, G1, Money Times, Investing, CNBC, Reuters)
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
    st_html(f'<div style="text-align:center; color: rgba(255,255,255,0.3); font-size: 0.8rem;">Versão 2.0 · Atualizado em {datetime.now().strftime("%d/%m/%Y")}</div>')


# ─────────────────────────────────────────
# Sidebar Navigation
# ─────────────────────────────────────────
def render_sidebar():
    """Renderiza a sidebar de navegação estilo plataforma profissional."""
    with st.sidebar:
        st_html("""
        <div style="padding: 0.8rem 0 1.2rem; border-bottom: 1px solid rgba(124, 77, 255, 0.12); margin-bottom: 1rem;">
            <div style="display: flex; align-items: center; gap: 0.6rem;">
                <div style="background: linear-gradient(135deg, #7c4dff 0%, #00c8ff 100%); 
                            width: 36px; height: 36px; border-radius: 10px; 
                            display: flex; align-items: center; justify-content: center; 
                            font-size: 1.2rem; box-shadow: 0 4px 15px rgba(124, 77, 255, 0.4);">
                    📈
                </div>
                <div>
                    <div style="font-size: 1.15rem; font-weight: 900; color: #ffffff; 
                                letter-spacing: -0.5px; line-height: 1.1;">
                        Trader Support
                    </div>
                    <div style="font-size: 0.65rem; color: #00c8ff; font-weight: 700; 
                                letter-spacing: 1px; text-transform: uppercase; margin-top: 2px;">
                        PRO PORTAL
                    </div>
                </div>
            </div>
        </div>
        """)

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

        # Status do Sistema
        online_count = len([a for a in APPS if a["status"] == "online"])
        st_html(f"""
        <div style="background: rgba(255,255,255,0.02); border: 1px solid rgba(255,255,255,0.05); 
                    border-radius: 12px; padding: 0.8rem; text-align: center;">
            <div style="display: flex; align-items: center; justify-content: center; gap: 6px; 
                        font-size: 0.72rem; color: #00e676; font-weight: 600; margin-bottom: 4px;">
                <span style="width: 7px; height: 7px; border-radius: 50%; background: #00e676; 
                             box-shadow: 0 0 8px #00e676;"></span>
                SISTEMA OPERACIONAL
            </div>
            <div style="font-size: 1.4rem; font-weight: 800; color: #ffffff; 
                        font-family: 'JetBrains Mono', monospace;">{online_count} <span style="font-size: 0.75rem; font-weight: 400; color: rgba(255,255,255,0.4);">/ 12 APPS</span></div>
        </div>
        """)

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
    st_html(f'<div class="portal-footer"><div class="brand">Trader Support</div><div class="copy">© {year} · Dados via Yahoo Finance, Banco Central do Brasil, RSS Feeds</div></div>')


if __name__ == "__main__":
    main()
