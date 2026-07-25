"""
economic_calendar.py — Agenda econômica com os principais eventos.
Dados curados manualmente com datas dos eventos mais relevantes.
"""

import streamlit as st
from datetime import datetime, date, timedelta


# Eventos econômicos recorrentes e importantes
# Cada evento tem: nome, país, bandeira, importância (Alta/Média/Baixa)
RECURRING_EVENTS = [
    # Brasil
    {"name": "Copom - Decisão de juros",    "country": "Brasil",  "flag": "🇧🇷", "importance": "Alta",  "frequency": "~45 dias"},
    {"name": "IPCA (Mensal)",               "country": "Brasil",  "flag": "🇧🇷", "importance": "Alta",  "frequency": "Mensal"},
    {"name": "PIB Trimestral",              "country": "Brasil",  "flag": "🇧🇷", "importance": "Alta",  "frequency": "Trimestral"},
    {"name": "Ata do Copom",                "country": "Brasil",  "flag": "🇧🇷", "importance": "Média", "frequency": "~45 dias"},
    {"name": "Balança Comercial",           "country": "Brasil",  "flag": "🇧🇷", "importance": "Média", "frequency": "Mensal"},
    {"name": "IGP-M (Mensal)",              "country": "Brasil",  "flag": "🇧🇷", "importance": "Média", "frequency": "Mensal"},

    # Estados Unidos
    {"name": "FOMC - Decisão de juros",     "country": "EUA",     "flag": "🇺🇸", "importance": "Alta",  "frequency": "~45 dias"},
    {"name": "Payroll (Non-Farm)",          "country": "EUA",     "flag": "🇺🇸", "importance": "Alta",  "frequency": "Mensal"},
    {"name": "CPI (Inflação)",              "country": "EUA",     "flag": "🇺🇸", "importance": "Alta",  "frequency": "Mensal"},
    {"name": "Ata do FOMC",                 "country": "EUA",     "flag": "🇺🇸", "importance": "Alta",  "frequency": "~45 dias"},
    {"name": "PIB Trimestral (EUA)",        "country": "EUA",     "flag": "🇺🇸", "importance": "Alta",  "frequency": "Trimestral"},
    {"name": "PCE (Inflação)",              "country": "EUA",     "flag": "🇺🇸", "importance": "Alta",  "frequency": "Mensal"},
    {"name": "Pedidos de Seguro-Desemprego","country": "EUA",     "flag": "🇺🇸", "importance": "Média", "frequency": "Semanal"},

    # Europa / Outros
    {"name": "BCE - Decisão de juros",      "country": "Europa",  "flag": "🇪🇺", "importance": "Alta",  "frequency": "~45 dias"},
    {"name": "BoJ - Decisão de juros",      "country": "Japão",   "flag": "🇯🇵", "importance": "Alta",  "frequency": "~45 dias"},
]


def get_economic_calendar() -> list:
    """
    Retorna a lista de eventos econômicos recorrentes.
    Como não temos uma API gratuita confiável para datas exatas,
    retornamos a lista curada dos eventos mais relevantes.
    """
    return RECURRING_EVENTS


def get_events_by_importance(importance: str = "Alta") -> list:
    """Filtra eventos por importância."""
    return [e for e in RECURRING_EVENTS if e["importance"] == importance]


def get_events_by_country(country: str) -> list:
    """Filtra eventos por país/região."""
    return [e for e in RECURRING_EVENTS if e["country"] == country]
