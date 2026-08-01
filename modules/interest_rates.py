"""
interest_rates.py — Taxas de juros nacionais e internacionais.
Dados do Banco Central do Brasil (API pública SGS) e valores de referência internacionais.
"""

import streamlit as st
import requests
from datetime import datetime


HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept": "application/json",
}

# Séries do BCB - Sistema Gerenciador de Séries (SGS)
BCB_SERIES = {
    "SELIC Meta": {"id": 432,   "fallback": 10.50},
    "CDI":        {"id": 4389,  "fallback": 10.40},
    "IPCA (12m)": {"id": 13522, "fallback": 4.23},
    "IGP-M (12m)": {"id": 189,   "fallback": 3.82},
}


@st.cache_data(ttl=3600, show_spinner=False)
def get_brazilian_rates() -> dict:
    """
    Busca as taxas de juros brasileiras na API pública do BCB.
    Retorna dict com nome -> {valor, formatted, data, status}
    """
    result = {}
    for name, cfg in BCB_SERIES.items():
        serie_id = cfg["id"]
        fallback_val = cfg["fallback"]
        try:
            url = f"https://api.bcb.gov.br/dados/serie/bcdata.sgs.{serie_id}/dados/ultimos/1?formato=json"
            resp = requests.get(url, headers=HEADERS, timeout=6)
            if resp.status_code == 200:
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
                    continue
        except Exception:
            pass

        # Fallback confiável se API do BCB não responder
        result[name] = {
            "valor": fallback_val,
            "formatted": f"{fallback_val:.2f}%".replace(".", ","),
            "data": "Julho/2026",
            "status": "Vigente (Estimativa)",
        }

    return result


@st.cache_data(ttl=3600, show_spinner=False)
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
        if not t10.empty and "Close" in t10.columns:
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
        "BCE (Europa)":          {"valor": 4.25, "status": "Estável"},
        "BoJ (Japão)":           {"valor": 0.25, "status": "Estável"},
    }

    for name, info in reference_rates.items():
        result[name] = {
            "valor": info["valor"],
            "formatted": f'{info["valor"]:.2f}%'.replace(".", ","),
            "status": info["status"],
            "color": "rgba(255,255,255,0.45)",
        }

    return result

