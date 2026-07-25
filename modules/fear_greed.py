"""
fear_greed.py — Fear & Greed Index via Alternative.me API (gratuita, sem auth).
"""

import streamlit as st
import requests


@st.cache_data(ttl=3600, show_spinner=False)
def get_fear_greed() -> dict:
    """
    Busca o Fear & Greed Index de criptomoedas via Alternative.me.
    Apesar de ser focado em crypto, é um bom indicador de sentimento geral.
    
    Returns:
        dict: {value, classification, color, timestamp}
    """
    try:
        resp = requests.get(
            "https://api.alternative.me/fng/?limit=1&format=json",
            timeout=10,
        )
        resp.raise_for_status()
        data = resp.json()

        if "data" in data and len(data["data"]) > 0:
            entry = data["data"][0]
            value = int(entry["value"])
            classification = entry["value_classification"]

            # Traduzir para português
            translations = {
                "Extreme Fear": "Medo Extremo",
                "Fear": "Medo",
                "Neutral": "Neutro",
                "Greed": "Ganância",
                "Extreme Greed": "Ganância Extrema",
            }
            classification_pt = translations.get(classification, classification)

            # Cor baseada no valor
            if value <= 25:
                color = "#ef4444"    # Vermelho — medo extremo
            elif value <= 45:
                color = "#f59e0b"    # Laranja — medo
            elif value <= 55:
                color = "#eab308"    # Amarelo — neutro
            elif value <= 75:
                color = "#84cc16"    # Verde claro — ganância
            else:
                color = "#22c55e"    # Verde — ganância extrema

            return {
                "value": value,
                "classification": classification_pt,
                "classification_en": classification,
                "color": color,
                "timestamp": entry.get("timestamp", ""),
            }

    except Exception:
        pass

    return {
        "value": None,
        "classification": "Indisponível",
        "classification_en": "Unavailable",
        "color": "#666",
        "timestamp": "",
    }
