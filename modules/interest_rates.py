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
    Retorna dict com nome -> {valor, formatted, data, status}
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
                    "status": "Vigente",
                }
        except Exception:
            result[name] = {
                "valor": None,
                "formatted": "—",
                "data": "—",
                "status": "Indisponível",
            }

    return result


@st.cache_data(ttl=86400, show_spinner=False)
def get_international_rates() -> dict:
    """
    Retorna taxas de juros internacionais de referência com formatação uniforme.
    """
    result = {}

    # Treasury 10Y via yfinance
    treasury_val = 4.25
    treasury_status = "Estável"
    try:
        import yfinance as yf
        t10 = yf.download("^TNX", period="2d", interval="1d", progress=False)
        closes = t10["Close"].dropna()
        if len(closes) >= 1:
            val = float(closes.iloc[-1])
            prev = float(closes.iloc[-2]) if len(closes) >= 2 else val
            change = val - prev
            treasury_val = val
            treasury_status = f"{change:+.2f}%".replace(".", ",") if abs(change) > 0.01 else "Estável"
    except Exception:
        pass

    result["Treasury 10Y (EUA)"] = {
        "valor": treasury_val,
        "formatted": f"{treasury_val:.2f}%".replace(".", ","),
        "status": treasury_status,
        "color": "#00c8ff",
    }

    # Taxas centrais globais padronizadas
    reference_rates = {
        "Fed Funds Rate (EUA)": {"valor": 5.50, "status": "Estável"},
        "BCE (Europa)":          {"valor": 4.50, "status": "Estável"},
        "BoJ (Japão)":           {"valor": 0.10, "status": "Estável"},
    }

    for name, info in reference_rates.items():
        result[name] = {
            "valor": info["valor"],
            "formatted": f'{info["valor"]:.2f}%'.replace(".", ","),
            "status": info["status"],
            "color": "rgba(255,255,255,0.45)",
        }

    return result
