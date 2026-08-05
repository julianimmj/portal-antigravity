"""
economic_calendar.py — Agenda econômica com os principais eventos e datas exatas de divulgação.
Dados estruturados com datas, horários e níveis de impacto no mercado.
"""

import streamlit as st
from datetime import datetime, date


ECONOMIC_EVENTS = [
    # Brasil
    {
        "name": "Balança Comercial (Mensal)",
        "country": "Brasil",
        "flag": "🇧🇷",
        "importance": "Média",
        "frequency": "Mensal",
        "date": "03/08",
        "time": "15:00",
        "date_formatted": "03/08 · 15:00",
    },
    {
        "name": "Ata do Copom (BCB)",
        "country": "Brasil",
        "flag": "🇧🇷",
        "importance": "Alta",
        "frequency": "~45 dias",
        "date": "05/08",
        "time": "08:00",
        "date_formatted": "05/08 · 08:00",
    },
    {
        "name": "IPCA (Inflação Oficial IBGE)",
        "country": "Brasil",
        "flag": "🇧🇷",
        "importance": "Alta",
        "frequency": "Mensal",
        "date": "11/08",
        "time": "09:00",
        "date_formatted": "11/08 · 09:00",
    },
    {
        "name": "IBC-Br (Prévia do PIB BCB)",
        "country": "Brasil",
        "flag": "🇧🇷",
        "importance": "Alta",
        "frequency": "Mensal",
        "date": "14/08",
        "time": "09:00",
        "date_formatted": "14/08 · 09:00",
    },
    {
        "name": "Novo CAGED (Emprego)",
        "country": "Brasil",
        "flag": "🇧🇷",
        "importance": "Média",
        "frequency": "Mensal",
        "date": "27/08",
        "time": "14:30",
        "date_formatted": "27/08 · 14:30",
    },
    {
        "name": "PIB Trimestral Brasil",
        "country": "Brasil",
        "flag": "🇧🇷",
        "importance": "Alta",
        "frequency": "Trimestral",
        "date": "01/09",
        "time": "09:00",
        "date_formatted": "01/09 · 09:00",
    },
    {
        "name": "Copom - Decisão de Juros",
        "country": "Brasil",
        "flag": "🇧🇷",
        "importance": "Alta",
        "frequency": "~45 dias",
        "date": "16/09",
        "time": "18:30",
        "date_formatted": "16/09 · 18:30",
    },

    # Estados Unidos
    {
        "name": "Payroll (Relatório de Emprego EUA)",
        "country": "EUA",
        "flag": "🇺🇸",
        "importance": "Alta",
        "frequency": "Mensal",
        "date": "07/08",
        "time": "09:30",
        "date_formatted": "07/08 · 09:30",
    },
    {
        "name": "CPI (Inflação ao Consumidor EUA)",
        "country": "EUA",
        "flag": "🇺🇸",
        "importance": "Alta",
        "frequency": "Mensal",
        "date": "12/08",
        "time": "09:30",
        "date_formatted": "12/08 · 09:30",
    },
    {
        "name": "Vendas no Varejo (EUA)",
        "country": "EUA",
        "flag": "🇺🇸",
        "importance": "Média",
        "frequency": "Mensal",
        "date": "15/08",
        "time": "09:30",
        "date_formatted": "15/08 · 09:30",
    },
    {
        "name": "Ata do FOMC (Federal Reserve)",
        "country": "EUA",
        "flag": "🇺🇸",
        "importance": "Alta",
        "frequency": "~45 dias",
        "date": "19/08",
        "time": "15:00",
        "date_formatted": "19/08 · 15:00",
    },
    {
        "name": "PIB Trimestral EUA (2ª Leitura)",
        "country": "EUA",
        "flag": "🇺🇸",
        "importance": "Alta",
        "frequency": "Trimestral",
        "date": "27/08",
        "time": "09:30",
        "date_formatted": "27/08 · 09:30",
    },
    {
        "name": "PCE (Inflação Preferida do Fed)",
        "country": "EUA",
        "flag": "🇺🇸",
        "importance": "Alta",
        "frequency": "Mensal",
        "date": "28/08",
        "time": "09:30",
        "date_formatted": "28/08 · 09:30",
    },
    {
        "name": "FOMC - Decisão de Juros EUA",
        "country": "EUA",
        "flag": "🇺🇸",
        "importance": "Alta",
        "frequency": "~45 dias",
        "date": "16/09",
        "time": "15:00",
        "date_formatted": "16/09 · 15:00",
    },

    # Europa / Japão
    {
        "name": "PIB Zona do Euro",
        "country": "Europa",
        "flag": "🇪🇺",
        "importance": "Média",
        "frequency": "Trimestral",
        "date": "14/08",
        "time": "06:00",
        "date_formatted": "14/08 · 06:00",
    },
    {
        "name": "BCE - Decisão de Juros Europa",
        "country": "Europa",
        "flag": "🇪🇺",
        "importance": "Alta",
        "frequency": "~45 dias",
        "date": "10/09",
        "time": "09:15",
        "date_formatted": "10/09 · 09:15",
    },
    {
        "name": "BoJ - Decisão de Juros Japão",
        "country": "Japão",
        "flag": "🇯🇵",
        "importance": "Alta",
        "frequency": "~45 dias",
        "date": "18/09",
        "time": "00:00",
        "date_formatted": "18/09 · 00:00",
    },
]


def _parse_event_datetime(ev: dict, ref_dt: datetime = None) -> datetime:
    """Converte 'date' (DD/MM) e 'time' (HH:MM) para objeto datetime."""
    if ref_dt is None:
        ref_dt = datetime.now()

    parts = ev["date"].split("/")
    day, month = int(parts[0]), int(parts[1])
    year = ref_dt.year

    # Se o mês do evento for menor que o mês atual - 2 (ex: Jan em Dez), é para o ano seguinte
    if month < ref_dt.month - 2:
        year += 1

    hour, minute = 0, 0
    if "time" in ev and ":" in ev["time"]:
        t_parts = ev["time"].split(":")
        hour, minute = int(t_parts[0]), int(t_parts[1])

    return datetime(year, month, day, hour, minute)


def get_economic_calendar(include_past: bool = False) -> list:
    """
    Retorna a lista de eventos econômicos ordenados cronologicamente
    (da data/hora mais próxima à mais distante).
    Por padrão, oculta eventos cujas datas já ultrapassaram o dia atual.
    """
    now = datetime.now()
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)

    processed_events = []
    for ev in ECONOMIC_EVENTS:
        try:
            dt_obj = _parse_event_datetime(ev, now)
            ev_copy = dict(ev)
            ev_copy["dt"] = dt_obj
            processed_events.append(ev_copy)
        except Exception:
            continue

    if not include_past:
        processed_events = [e for e in processed_events if e["dt"] >= today_start]

    processed_events.sort(key=lambda x: x["dt"])
    return processed_events


def get_events_by_importance(importance: str = "Alta", include_past: bool = False) -> list:
    """Filtra eventos por importância, ordenados por data."""
    events = get_economic_calendar(include_past=include_past)
    return [e for e in events if e.get("importance") == importance]


def get_events_by_country(country: str, include_past: bool = False) -> list:
    """Filtra eventos por país/região, ordenados por data."""
    events = get_economic_calendar(include_past=include_past)
    return [e for e in events if e.get("country") == country]


