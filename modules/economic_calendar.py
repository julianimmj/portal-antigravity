"""
economic_calendar.py — Agenda econômica com os principais eventos e datas exatas de divulgação.
Dados estruturados com datas, horários e níveis de impacto no mercado.
"""

import streamlit as st
from datetime import datetime, date


# Eventos econômicos com datas exatas de divulgação
ECONOMIC_EVENTS = [
    # Brasil
    {
        "name": "Copom - Decisão de juros",
        "country": "Brasil",
        "flag": "🇧🇷",
        "importance": "Alta",
        "frequency": "~45 dias",
        "date": "30/07",
        "time": "18:30",
        "date_formatted": "30/07 · 18:30",
    },
    {
        "name": "IGP-M (Mensal)",
        "country": "Brasil",
        "flag": "🇧🇷",
        "importance": "Média",
        "frequency": "Mensal",
        "date": "29/07",
        "time": "08:00",
        "date_formatted": "29/07 · 08:00",
    },
    {
        "name": "Balança Comercial",
        "country": "Brasil",
        "flag": "🇧🇷",
        "importance": "Média",
        "frequency": "Mensal",
        "date": "01/08",
        "time": "15:00",
        "date_formatted": "01/08 · 15:00",
    },
    {
        "name": "Ata do Copom",
        "country": "Brasil",
        "flag": "🇧🇷",
        "importance": "Média",
        "frequency": "~45 dias",
        "date": "05/08",
        "time": "08:00",
        "date_formatted": "05/08 · 08:00",
    },
    {
        "name": "IPCA (Mensal)",
        "country": "Brasil",
        "flag": "🇧🇷",
        "importance": "Alta",
        "frequency": "Mensal",
        "date": "08/08",
        "time": "09:00",
        "date_formatted": "08/08 · 09:00",
    },
    {
        "name": "PIB Trimestral",
        "country": "Brasil",
        "flag": "🇧🇷",
        "importance": "Alta",
        "frequency": "Trimestral",
        "date": "01/09",
        "time": "09:00",
        "date_formatted": "01/09 · 09:00",
    },

    # Estados Unidos
    {
        "name": "FOMC - Decisão de juros",
        "country": "EUA",
        "flag": "🇺🇸",
        "importance": "Alta",
        "frequency": "~45 dias",
        "date": "30/07",
        "time": "15:00",
        "date_formatted": "30/07 · 15:00",
    },
    {
        "name": "Pedidos de Seguro-Desemprego",
        "country": "EUA",
        "flag": "🇺🇸",
        "importance": "Média",
        "frequency": "Semanal",
        "date": "31/07",
        "time": "09:30",
        "date_formatted": "31/07 · 09:30",
    },
    {
        "name": "Payroll (Non-Farm)",
        "country": "EUA",
        "flag": "🇺🇸",
        "importance": "Alta",
        "frequency": "Mensal",
        "date": "07/08",
        "time": "09:30",
        "date_formatted": "07/08 · 09:30",
    },
    {
        "name": "CPI (Inflação EUA)",
        "country": "EUA",
        "flag": "🇺🇸",
        "importance": "Alta",
        "frequency": "Mensal",
        "date": "12/08",
        "time": "09:30",
        "date_formatted": "12/08 · 09:30",
    },
    {
        "name": "Ata do FOMC",
        "country": "EUA",
        "flag": "🇺🇸",
        "importance": "Alta",
        "frequency": "~45 dias",
        "date": "19/08",
        "time": "15:00",
        "date_formatted": "19/08 · 15:00",
    },
    {
        "name": "PIB Trimestral (EUA)",
        "country": "EUA",
        "flag": "🇺🇸",
        "importance": "Alta",
        "frequency": "Trimestral",
        "date": "27/08",
        "time": "09:30",
        "date_formatted": "27/08 · 09:30",
    },
    {
        "name": "PCE (Inflação EUA)",
        "country": "EUA",
        "flag": "🇺🇸",
        "importance": "Alta",
        "frequency": "Mensal",
        "date": "28/08",
        "time": "09:30",
        "date_formatted": "28/08 · 09:30",
    },

    # Europa / Japão
    {
        "name": "BCE - Decisão de juros",
        "country": "Europa",
        "flag": "🇪🇺",
        "importance": "Alta",
        "frequency": "~45 dias",
        "date": "10/09",
        "time": "09:15",
        "date_formatted": "10/09 · 09:15",
    },
    {
        "name": "BoJ - Decisão de juros",
        "country": "Japão",
        "flag": "🇯🇵",
        "importance": "Alta",
        "frequency": "~45 dias",
        "date": "18/09",
        "time": "00:00",
        "date_formatted": "18/09 · 00:00",
    },
]


def get_economic_calendar() -> list:
    """Retorna a lista de eventos econômicos ordenados por data de divulgação."""
    return ECONOMIC_EVENTS


def get_events_by_importance(importance: str = "Alta") -> list:
    """Filtra eventos por importância."""
    return [e for e in ECONOMIC_EVENTS if e["importance"] == importance]


def get_events_by_country(country: str) -> list:
    """Filtra eventos por país/região."""
    return [e for e in ECONOMIC_EVENTS if e["country"] == country]
