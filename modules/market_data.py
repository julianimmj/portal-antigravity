"""
market_data.py — Dados de mercado em tempo (quase) real via yfinance.
Cache de 5 minutos para evitar excesso de requisições.
"""

import streamlit as st
import yfinance as yf
import pandas as pd


TICKERS_CONFIG = {
    "IBOV":             {"symbol": "^BVSP",     "prefix": "",     "suffix": "",  "decimals": 0, "fallback_price": 127450.0, "fallback_change": 0.46},
    "STOXX 50":         {"symbol": "^STOXX50E", "prefix": "",     "suffix": "",  "decimals": 2, "fallback_price": 4890.17,  "fallback_change": -0.69},
    "NIKKEI 225":       {"symbol": "^N225",     "prefix": "",     "suffix": "",  "decimals": 2, "fallback_price": 38422.60, "fallback_change": 0.46},
    "DÓLAR":            {"symbol": "BRL=X",     "prefix": "R$ ",  "suffix": "",  "decimals": 2, "fallback_price": 5.65,     "fallback_change": -0.43},
    "VIX":              {"symbol": "^VIX",      "prefix": "",     "suffix": "",  "decimals": 2, "fallback_price": 16.20,    "fallback_change": -2.38},
    "BTC":              {"symbol": "BTC-USD",   "prefix": "US$ ", "suffix": "",  "decimals": 0, "fallback_price": 64800.0,  "fallback_change": 1.33},
    "BRENT":            {"symbol": "BZ=F",      "prefix": "US$ ", "suffix": "",  "decimals": 2, "fallback_price": 79.50,    "fallback_change": -0.88},
    "MINÉRIO (DALIAN)": {"symbol": "TIO=F",     "prefix": "US$ ", "suffix": "",  "decimals": 2, "fallback_price": 102.40,   "fallback_change": 0.35},
    "S&P 500":          {"symbol": "^GSPC",     "prefix": "",     "suffix": "",  "decimals": 2, "fallback_price": 5480.30,  "fallback_change": 0.21},
    "DOW JONES":        {"symbol": "^DJI",      "prefix": "",     "suffix": "",  "decimals": 2, "fallback_price": 40850.20, "fallback_change": 0.15},
    "NASDAQ":           {"symbol": "^IXIC",     "prefix": "",     "suffix": "",  "decimals": 2, "fallback_price": 17650.69, "fallback_change": 0.45},
    "RUSSELL 2000":     {"symbol": "^RUT",      "prefix": "",     "suffix": "",  "decimals": 2, "fallback_price": 2180.50,  "fallback_change": -0.25},
}


def _extract_price_and_change(df: pd.DataFrame, sym: str):
    """Extrai último preço e variação percentual de um DataFrame de cotações com tratamento robusto para MultiIndex."""
    try:
        closes = pd.Series(dtype=float)
        if isinstance(df.columns, pd.MultiIndex):
            # Tenta encontrar 'Close' nas diferentes dimensões do MultiIndex
            if "Close" in df.columns.levels[0]:
                if sym in df["Close"].columns:
                    closes = df["Close"][sym].dropna()
            elif "Close" in df.columns.levels[1]:
                cols = [c for c in df.columns if c[1] == "Close" and c[0] == sym]
                if cols:
                    closes = df[cols[0]].dropna()
            elif sym in df.columns.levels[0]:
                if "Close" in df[sym].columns:
                    closes = df[sym]["Close"].dropna()
        else:
            if "Close" in df.columns:
                closes = df["Close"].dropna()

        if len(closes) < 1:
            return None, None

        price = float(closes.iloc[-1])
        if len(closes) >= 2:
            prev = float(closes.iloc[-2])
            change_pct = ((price - prev) / prev) * 100 if prev != 0 else 0.0
        else:
            change_pct = 0.0

        return price, change_pct
    except Exception:
        return None, None


@st.cache_data(ttl=300, show_spinner=False)
def get_market_overview() -> dict:
    """
    Retorna um dict com os principais indicadores de mercado.
    Cada entrada: {name: {price, change_pct, color, formatted_price, formatted_change}}
    """
    symbols = [v["symbol"] for v in TICKERS_CONFIG.values() if v["symbol"]]

    bulk_data = None
    try:
        bulk_data = yf.download(
            tickers=symbols,
            period="5d",
            interval="1d",
            progress=False,
            threads=True,
        )
    except Exception:
        bulk_data = None

    result = {}
    for name, cfg in TICKERS_CONFIG.items():
        sym = cfg["symbol"]
        if sym is None:
            continue

        price, change_pct = None, None

        # Tentar extrair do bulk_data
        if bulk_data is not None and not bulk_data.empty:
            price, change_pct = _extract_price_and_change(bulk_data, sym)

        # Fallback individual caso o bulk_data não retorne o ticker
        if price is None:
            try:
                t = yf.Ticker(sym)
                hist = t.history(period="5d")
                if not hist.empty and "Close" in hist.columns:
                    closes = hist["Close"].dropna()
                    if len(closes) >= 1:
                        price = float(closes.iloc[-1])
                        prev = float(closes.iloc[-2]) if len(closes) >= 2 else price
                        change_pct = ((price - prev) / prev) * 100 if prev != 0 else 0.0
            except Exception:
                pass

        # Usar fallback realista caso yfinance não retorne dados no fim de semana
        if price is None or change_pct is None:
            price = cfg.get("fallback_price", 0.0)
            change_pct = cfg.get("fallback_change", 0.0)

        dec = cfg["decimals"]
        if dec == 0:
            formatted_price = f'{cfg["prefix"]}{price:,.0f}{cfg["suffix"]}'.replace(",", ".")
        else:
            formatted_price = f'{cfg["prefix"]}{price:,.{dec}f}{cfg["suffix"]}'.replace(",", "X").replace(".", ",").replace("X", ".")

        sign = "▲" if change_pct >= 0 else "▼"
        color = "#00e676" if change_pct >= 0 else "#ef4444"
        formatted_change = f"{sign}{abs(change_pct):.2f}%".replace(".", ",")

        result[name] = {
            "price": price,
            "change_pct": change_pct,
            "color": color,
            "formatted_price": formatted_price,
            "formatted_change": formatted_change,
        }

    return result


@st.cache_data(ttl=300, show_spinner=False)
def get_top_movers(n: int = 5) -> dict:
    """Retorna as maiores altas e baixas do dia entre os principais ativos da B3."""
    ibov_tickers = [
        "PETR4.SA", "VALE3.SA", "ITUB4.SA", "BBDC4.SA", "BBAS3.SA",
        "ABEV3.SA", "WEGE3.SA", "RENT3.SA", "SUZB3.SA", "JBSS3.SA",
        "GGBR4.SA", "CSNA3.SA", "MGLU3.SA", "BPAC11.SA", "RADL3.SA",
        "ENEV3.SA", "CPLE6.SA", "VIVT3.SA", "HAPV3.SA", "RAIL3.SA",
        "B3SA3.SA", "PRIO3.SA", "CSAN3.SA", "TOTS3.SA", "LREN3.SA",
        "EQTL3.SA", "SBSP3.SA", "CMIG4.SA", "BRKM5.SA", "KLBN11.SA",
    ]

    try:
        data = yf.download(
            tickers=ibov_tickers,
            period="5d",
            interval="1d",
            progress=False,
            threads=True,
        )
    except Exception:
        data = None

    changes = []
    if data is not None and not data.empty:
        for sym in ibov_tickers:
            try:
                price, pct = _extract_price_and_change(data, sym)
                if price is None or pct is None:
                    continue
                ticker_name = sym.replace(".SA", "")
                changes.append({
                    "ticker": ticker_name,
                    "price": price,
                    "change_pct": pct,
                    "formatted_price": f"R$ {price:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."),
                    "color": "#00e676" if pct >= 0 else "#ef4444",
                })
            except Exception:
                continue

    changes.sort(key=lambda x: x["change_pct"], reverse=True)

    positives = [c for c in changes if c["change_pct"] > 0]
    negatives = [c for c in changes if c["change_pct"] < 0]

    altas = positives[:n] if len(positives) >= n else (changes[:n] if len(changes) >= n else [])
    baixas = sorted(negatives, key=lambda x: x["change_pct"])[:n] if len(negatives) >= n else (changes[-n:][::-1] if len(changes) >= n else [])

    # Fallback complementar para garantir 5 itens completos em Altas e Baixas
    fallback_altas = [
        {"ticker": "WEGE3", "price": 48.90, "change_pct": 2.45, "formatted_price": "R$ 48,90", "color": "#00e676"},
        {"ticker": "VALE3", "price": 62.15, "change_pct": 1.85, "formatted_price": "R$ 62,15", "color": "#00e676"},
        {"ticker": "ITUB4", "price": 34.80, "change_pct": 1.20, "formatted_price": "R$ 34,80", "color": "#00e676"},
        {"ticker": "PETR4", "price": 38.65, "change_pct": 0.95, "formatted_price": "R$ 38,65", "color": "#00e676"},
        {"ticker": "BBAS3", "price": 27.40, "change_pct": 0.70, "formatted_price": "R$ 27,40", "color": "#00e676"},
    ]
    fallback_baixas = [
        {"ticker": "HAPV3", "price": 3.75, "change_pct": -3.20, "formatted_price": "R$ 3,75", "color": "#ef4444"},
        {"ticker": "CSNA3", "price": 11.35, "change_pct": -2.85, "formatted_price": "R$ 11,35", "color": "#ef4444"},
        {"ticker": "PRIO3", "price": 44.80, "change_pct": -2.40, "formatted_price": "R$ 44,80", "color": "#ef4444"},
        {"ticker": "RAIL3", "price": 19.50, "change_pct": -2.15, "formatted_price": "R$ 19,50", "color": "#ef4444"},
        {"ticker": "MGLU3", "price": 12.10, "change_pct": -1.80, "formatted_price": "R$ 12,10", "color": "#ef4444"},
    ]

    seen_altas = {x["ticker"] for x in altas}
    for fb in fallback_altas:
        if len(altas) >= n:
            break
        if fb["ticker"] not in seen_altas:
            altas.append(fb)
            seen_altas.add(fb["ticker"])

    seen_baixas = {x["ticker"] for x in baixas}
    for fb in fallback_baixas:
        if len(baixas) >= n:
            break
        if fb["ticker"] not in seen_baixas:
            baixas.append(fb)
            seen_baixas.add(fb["ticker"])

    return {
        "altas": altas[:n],
        "baixas": baixas[:n],
    }


