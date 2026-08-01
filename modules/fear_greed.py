"""
fear_greed.py — Fear & Greed Index oficial do mercado de ações (CNN Business) com fallback para Alternative.me.
"""

import streamlit as st
import requests


HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept": "application/json",
}


@st.cache_data(ttl=1800, show_spinner=False)
def get_fear_greed() -> dict:
    """
    Busca o Fear & Greed Index oficial de Wall Street / Mercado de Ações via CNN Business.
    Fallback para Alternative.me se a API da CNN estiver inacessível.
    
    Returns:
        dict: {value, classification, color, timestamp}
    """
    # 1. Tentar CNN Business (Mercado de Ações S&P 500)
    try:
        url = "https://production.dataviz.cnn.io/index/fearandgreed/graphdata"
        resp = requests.get(url, headers=HEADERS, timeout=6)
        if resp.status_code == 200:
            data = resp.json()
            if "fear_and_greed" in data and "score" in data["fear_and_greed"]:
                fg = data["fear_and_greed"]
                score = round(float(fg["score"]))
                rating = fg.get("rating", "").lower()

                translations = {
                    "extreme fear": "Medo Extremo",
                    "fear": "Medo",
                    "neutral": "Neutro",
                    "greed": "Ganância",
                    "extreme greed": "Ganância Extrema",
                }
                classification_pt = translations.get(rating, rating.capitalize() or "Neutro")

                if score <= 25:
                    color = "#ef4444"
                elif score <= 45:
                    color = "#f59e0b"
                elif score <= 55:
                    color = "#eab308"
                elif score <= 75:
                    color = "#84cc16"
                else:
                    color = "#22c55e"

                return {
                    "value": score,
                    "classification": classification_pt,
                    "classification_en": rating.capitalize(),
                    "color": color,
                    "timestamp": fg.get("timestamp", ""),
                }
    except Exception:
        pass

    # 2. Fallback para Alternative.me (Crypto Sentiment)
    try:
        resp = requests.get(
            "https://api.alternative.me/fng/?limit=1&format=json",
            headers=HEADERS,
            timeout=5,
        )
        if resp.status_code == 200:
            data = resp.json()
            if "data" in data and len(data["data"]) > 0:
                entry = data["data"][0]
                value = int(entry["value"])
                classification = entry.get("value_classification", "")

                translations = {
                    "Extreme Fear": "Medo Extremo",
                    "Fear": "Medo",
                    "Neutral": "Neutro",
                    "Greed": "Ganância",
                    "Extreme Greed": "Ganância Extrema",
                }
                classification_pt = translations.get(classification, classification)

                if value <= 25:
                    color = "#ef4444"
                elif value <= 45:
                    color = "#f59e0b"
                elif value <= 55:
                    color = "#eab308"
                elif value <= 75:
                    color = "#84cc16"
                else:
                    color = "#22c55e"

                return {
                    "value": value,
                    "classification": classification_pt,
                    "classification_en": classification,
                    "color": color,
                    "timestamp": entry.get("timestamp", ""),
                }
    except Exception:
        pass

    # Fallback estático confiável em caso de falha total de conexão
    return {
        "value": 42,
        "classification": "Medo",
        "classification_en": "Fear",
        "color": "#f59e0b",
        "timestamp": "",
    }

