"""
market_data.py — Dados de mercado em tempo (quase) real via yfinance.
Cache de 5 minutos para evitar excesso de requisições.
"""

import streamlit as st
import yfinance as yf


TICKERS_CONFIG = {
    "IBOV":    {"symbol": "^BVSP",    "prefix": "",     "suffix": "",  "decimals": 0},
    "S&P 500": {"symbol": "^GSPC",    "prefix": "",     "suffix": "",  "decimals": 2},
    "NASDAQ":  {"symbol": "^IXIC",    "prefix": "",     "suffix": "",  "decimals": 2},
    "DÓLAR":   {"symbol": "BRL=X",    "prefix": "R$ ",  "suffix": "",  "decimals": 2},
    "SELIC":   {"symbol": None,       "prefix": "",     "suffix": "%", "decimals": 2},
    "VIX":     {"symbol": "^VIX",     "prefix": "",     "suffix": "",  "decimals": 2},
    "BTC":     {"symbol": "BTC-USD",  "prefix": "US$ ", "suffix": "",  "decimals": 0},
    "PETR4":   {"symbol": "PETR4.SA", "prefix": "R$ ",  "suffix": "",  "decimals": 2},
    "VALE3":   {"symbol": "VALE3.SA", "prefix": "R$ ",  "suffix": "",  "decimals": 2},
}


@st.cache_data(ttl=300, show_spinner=False)
def get_market_overview() -> dict:
    """
    Retorna um dict com os principais indicadores de mercado.
    Cada entrada: {name: {price, change_pct, color, formatted_price, formatted_change}}
    """
    symbols = [v["symbol"] for v in TICKERS_CONFIG.values() if v["symbol"]]

    try:
        data = yf.download(
            tickers=symbols,
            period="2d",
            interval="1d",
            group_by="ticker",
            progress=False,
            threads=True,
        )
    except Exception:
        return {}

    result = {}
    for name, cfg in TICKERS_CONFIG.items():
        sym = cfg["symbol"]
        if sym is None:
            continue
        try:
            if len(symbols) == 1:
                ticker_data = data
            else:
                ticker_data = data[sym]

            closes = ticker_data["Close"].dropna()
            if len(closes) < 2:
                continue

            price = float(closes.iloc[-1])
            prev = float(closes.iloc[-2])
            change_pct = ((price - prev) / prev) * 100

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
        except Exception:
            continue

    return result


@st.cache_data(ttl=300, show_spinner=False)
def get_top_movers(n: int = 6) -> dict:
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
            period="2d",
            interval="1d",
            group_by="ticker",
            progress=False,
            threads=True,
        )
    except Exception:
        return {"altas": [], "baixas": []}

    changes = []
    for sym in ibov_tickers:
        try:
            closes = data[sym]["Close"].dropna()
            if len(closes) < 2:
                continue
            price = float(closes.iloc[-1])
            prev = float(closes.iloc[-2])
            pct = ((price - prev) / prev) * 100
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

    return {
        "altas": changes[:n],
        "baixas": changes[-n:][::-1] if len(changes) >= n else [],
    }
