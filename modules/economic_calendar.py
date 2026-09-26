"""
economic_calendar.py — Agenda econômica com dados ao vivo via API pública (ForexFactory/FairEconomy).
Busca eventos atualizados automaticamente, sem necessidade de atualização manual.
Mantém fallback com eventos estáticos do Brasil caso a API esteja indisponível.
"""

import streamlit as st
import requests
from datetime import datetime, timedelta, timezone


# ─── Mapeamento de moedas para país/bandeira (formato usado pelo app) ───
CURRENCY_MAP = {
    "USD": {"country": "EUA", "flag": "🇺🇸"},
    "EUR": {"country": "Europa", "flag": "🇪🇺"},
    "GBP": {"country": "Reino Unido", "flag": "🇬🇧"},
    "JPY": {"country": "Japão", "flag": "🇯🇵"},
    "CAD": {"country": "Canadá", "flag": "🇨🇦"},
    "AUD": {"country": "Austrália", "flag": "🇦🇺"},
    "NZD": {"country": "Nova Zelândia", "flag": "🇳🇿"},
    "CHF": {"country": "Suíça", "flag": "🇨🇭"},
    "CNY": {"country": "China", "flag": "🇨🇳"},
    "BRL": {"country": "Brasil", "flag": "🇧🇷"},
}

# ─── Mapeamento de impacto (ForexFactory → formato do app) ───
IMPACT_MAP = {
    "High": "Alta",
    "Medium": "Média",
    "Low": "Baixa",
    "Holiday": "Feriado",
}

# ─── Fuso horário de Brasília (UTC-3) ───
BRT = timezone(timedelta(hours=-3))

# ─── URLs da API pública (ForexFactory via FairEconomy CDN) ───
API_URLS = [
    "https://nfs.faireconomy.media/ff_calendar_thisweek.json",
    "https://nfs.faireconomy.media/ff_calendar_nextweek.json",
]


# ─── Eventos complementares brasileiros (não cobertos pela API) ───
# Esses são adicionados para garantir cobertura de indicadores BR relevantes.
# As datas são genéricas (dia/mês) e são resolvidas para o mês/ano corrente.
BRAZILIAN_EVENTS_TEMPLATE = [
    {
        "name": "IPCA (Inflação Oficial IBGE)",
        "importance": "Alta",
        "frequency": "Mensal",
        "day_of_month": 10,
        "time_str": "09:00",
    },
    {
        "name": "Ata do Copom (BCB)",
        "importance": "Alta",
        "frequency": "~45 dias",
        "day_of_month": 5,
        "time_str": "08:00",
    },
    {
        "name": "IBC-Br (Prévia do PIB BCB)",
        "importance": "Alta",
        "frequency": "Mensal",
        "day_of_month": 14,
        "time_str": "09:00",
    },
    {
        "name": "Novo CAGED (Emprego)",
        "importance": "Média",
        "frequency": "Mensal",
        "day_of_month": 27,
        "time_str": "14:30",
    },
    {
        "name": "Balança Comercial (Mensal)",
        "importance": "Média",
        "frequency": "Mensal",
        "day_of_month": 3,
        "time_str": "15:00",
    },
    {
        "name": "Copom - Decisão de Juros",
        "importance": "Alta",
        "frequency": "~45 dias",
        "day_of_month": 16,
        "time_str": "18:30",
    },
    {
        "name": "PIB Trimestral Brasil",
        "importance": "Alta",
        "frequency": "Trimestral",
        "day_of_month": 1,
        "time_str": "09:00",
    },
]


def _generate_brazilian_events(now: datetime) -> list:
    """
    Gera eventos brasileiros aproximados para o mês corrente e o próximo.
    Retorna lista de eventos no formato padrão do app.
    """
    events = []
    for month_offset in range(2):  # mês atual e próximo
        target_month = now.month + month_offset
        target_year = now.year
        if target_month > 12:
            target_month -= 12
            target_year += 1

        for tmpl in BRAZILIAN_EVENTS_TEMPLATE:
            try:
                day = tmpl["day_of_month"]
                h, m = [int(x) for x in tmpl["time_str"].split(":")]
                dt_obj = datetime(target_year, target_month, day, h, m, tzinfo=BRT)

                # Formata data para exibição (DD/MM · HH:MM)
                date_str = dt_obj.strftime("%d/%m")
                date_formatted = f"{date_str} · {tmpl['time_str']}"

                events.append({
                    "name": tmpl["name"],
                    "country": "Brasil",
                    "flag": "🇧🇷",
                    "importance": tmpl["importance"],
                    "frequency": tmpl["frequency"],
                    "date": date_str,
                    "time": tmpl["time_str"],
                    "date_formatted": date_formatted,
                    "dt": dt_obj,
                    "source": "static",
                })
            except ValueError:
                # dia inválido para o mês (ex: 31 em fevereiro)
                continue

    return events


@st.cache_data(ttl=1800, show_spinner=False)
def _fetch_api_events() -> list:
    """
    Busca eventos de ambos os endpoints da API (semana atual e próxima).
    Cache de 30 minutos para não sobrecarregar a API.
    Retorna lista combinada de eventos ou lista vazia em caso de erro.
    """
    all_events = []
    headers = {
        "User-Agent": "TraderSupport/1.0 (Economic Calendar Widget)",
        "Accept": "application/json",
    }

    for url in API_URLS:
        try:
            resp = requests.get(url, timeout=15, headers=headers)
            if resp.status_code == 200:
                text = resp.text.strip()
                if text and text.startswith("["):
                    data = resp.json()
                    if isinstance(data, list):
                        all_events.extend(data)
        except Exception:
            continue

    return all_events


def _parse_api_events(raw_events: list, now: datetime) -> list:
    """
    Converte eventos crus da API para o formato padrão do app.
    """
    parsed = []
    for ev in raw_events:
        try:
            # Ignora feriados
            if ev.get("impact") == "Holiday":
                continue

            currency = ev.get("country", "")
            mapping = CURRENCY_MAP.get(currency)
            if not mapping:
                continue

            # Parse da data ISO 8601
            date_str_raw = ev.get("date", "")
            if not date_str_raw:
                continue

            # A API retorna datas como "2026-09-23T21:30:00-04:00" (ET)
            # Converte para horário de Brasília
            dt_obj = datetime.fromisoformat(date_str_raw).astimezone(BRT)

            # Formata para exibição
            date_display = dt_obj.strftime("%d/%m")
            time_display = dt_obj.strftime("%H:%M")
            date_formatted = f"{date_display} · {time_display}"

            importance = IMPACT_MAP.get(ev.get("impact", ""), "Média")

            parsed.append({
                "name": ev.get("title", "Evento"),
                "country": mapping["country"],
                "flag": mapping["flag"],
                "importance": importance,
                "frequency": "",
                "date": date_display,
                "time": time_display,
                "date_formatted": date_formatted,
                "dt": dt_obj,
                "source": "api",
            })
        except Exception:
            continue

    return parsed


def get_economic_calendar(include_past: bool = False) -> list:
    """
    Retorna a lista de eventos econômicos ordenados cronologicamente
    (da data/hora mais próxima à mais distante).
    Por padrão, oculta eventos cujas datas já ultrapassaram o dia atual.

    Combina dados da API ao vivo com eventos brasileiros complementares.
    """
    now = datetime.now(BRT)
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)

    # 1. Busca eventos da API
    raw_api = _fetch_api_events()
    api_events = _parse_api_events(raw_api, now)

    # 2. Gera eventos brasileiros como complemento
    br_events = _generate_brazilian_events(now)

    # Combina todos os eventos
    all_events = api_events + br_events

    # Remove duplicatas (BR estáticos vs possíveis BRL da API)
    # Prioriza eventos da API quando existirem
    seen_keys = set()
    unique_events = []
    for ev in sorted(all_events, key=lambda x: (x.get("source", "") != "api", x["dt"])):
        # Chave: país + data (dia/mês) — evita duplicatas do mesmo evento
        key = (ev["country"], ev["date"], ev["name"][:15].lower())
        if key not in seen_keys:
            seen_keys.add(key)
            unique_events.append(ev)

    # Filtra eventos passados (se solicitado)
    if not include_past:
        unique_events = [e for e in unique_events if e["dt"] >= today_start]

    # Ordena cronologicamente
    unique_events.sort(key=lambda x: x["dt"])

    return unique_events


def get_events_by_importance(importance: str = "Alta", include_past: bool = False) -> list:
    """Filtra eventos por importância, ordenados por data."""
    events = get_economic_calendar(include_past=include_past)
    return [e for e in events if e.get("importance") == importance]


def get_events_by_country(country: str, include_past: bool = False) -> list:
    """Filtra eventos por país/região, ordenados por data."""
    events = get_economic_calendar(include_past=include_past)
    return [e for e in events if e.get("country") == country]
