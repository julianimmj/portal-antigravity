"""
interest_rates.py — Taxas de juros nacionais e internacionais.
Dados do Banco Central do Brasil (API pública SGS) e valores de referência internacionais.
"""

import streamlit as st
import requests
from datetime import datetime


# Séries do BCB - Sistema Gerenciador de Séries (SGS)
BCB_SERIES = {
    "SELIC Meta": 432,
    "CDI":        4389,
    "IPCA (12m)": 13522,
    "IGP-M (12m)": 189,
}


@st.cache_data(ttl=3600, show_spinner=False)
def get_brazilian_rates() -> dict:
    """
    Busca as taxas de juros brasileiras na API pública do BCB.
    Retorna dict com nome -> {valor, data}
    """
    result = {}
    for name, serie_id in BCB_SERIES.items():
        try:
            url = f"https://api.bcb.gov.br/dados/serie/bcdata.sgs.{serie_id}/dados/ultimos/1?formato=json"
            resp = requests.get(url, timeout=10)
            resp.raise_for_status()
            data = resp.json()
            if data:
                entry = data[0]
                valor = float(entry["valor"].replace(",", "."))
                date_str = entry["data"]
                result[name] = {
                    "valor": valor,
                    "formatted": f"{valor:.2f}%".replace(".", ","),
                    "data": date_str,
                }
        except Exception:
            result[name] = {
                "valor": None,
                "formatted": "—",
                "data": "—",
            }

    return result


@st.cache_data(ttl=86400, show_spinner=False)
def get_international_rates() -> dict:
    """
    Retorna taxas de juros internacionais de referência.
    Usa yfinance para Treasury 10Y e valores de referência para Fed Funds, BCE e BoJ.
    """
    result = {}

    # Treasury 10Y via yfinance
    try:
        import yfinance as yf
        t10 = yf.download("^TNX", period="2d", interval="1d", progress=False)
        closes = t10["Close"].dropna()
        if len(closes) >= 1:
            val = float(closes.iloc[-1])
            prev = float(closes.iloc[-2]) if len(closes) >= 2 else val
            change = val - prev
            result["Treasury 10Y"] = {
                "valor": val,
                "formatted": f"{val:.2f}%".replace(".", ","),
                "change": change,
                "change_formatted": f"{change:+.2f}%".replace(".", ",") if abs(change) > 0.001 else "(estável)",
                "color": "#ef4444" if change > 0.01 else ("#00e676" if change < -0.01 else "#888"),
            }
    except Exception:
        pass

    # Valores de referência (atualizados periodicamente)
    reference_rates = {
        "Fed Funds Rate": {"valor": 5.50, "note": "estável"},
        "BCE (Europa)":   {"valor": 4.50, "note": "estável"},
        "BoJ (Japão)":    {"valor": 0.10, "note": "estável"},
    }

    for name, info in reference_rates.items():
        result[name] = {
            "valor": info["valor"],
            "formatted": f'{info["valor"]:.2f}%'.replace(".", ","),
            "change": 0,
            "change_formatted": f'({info["note"]})',
            "color": "#888",
        }

    return result
