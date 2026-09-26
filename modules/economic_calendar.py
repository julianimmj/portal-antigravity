"""
economic_calendar.py — Agenda econômica com dados ao vivo e fallback inteligente.

Estratégia de dados em 3 camadas:
  1. API ao vivo (ForexFactory/FairEconomy) — dados precisos e atualizados
  2. Cache persistente (st.cache_resource) — última resposta válida da API,
     sobrevive ao refresh da página (só perde no reboot do app)
  3. Eventos recorrentes estimados — gerados dinamicamente para mês atual/próximo
     com indicação visual "(Estimado)" para transparência

Os eventos brasileiros SEMPRE são complementados (a API não cobre BRL).
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


# ─── Eventos estáticos recorrentes (fallback de última instância) ───
# Datas são APROXIMADAS (dia genérico do mês). Quando exibidos, são marcados
# como "(Estimado)" para que o usuário saiba que a data pode variar.
# Cobrem apenas eventos brasileiros (a API internacional não cobre BRL).
BRAZILIAN_EVENTS_TEMPLATE = [
    {
        "name": "IPCA (Inflação Oficial IBGE)",
        "importance": "Alta", "frequency": "Mensal",
        "day_of_month": 10, "time_str": "09:00",
    },
    {
        "name": "Ata do Copom (BCB)",
        "importance": "Alta", "frequency": "~45 dias",
        "day_of_month": 5, "time_str": "08:00",
    },
    {
        "name": "IBC-Br (Prévia do PIB BCB)",
        "importance": "Alta", "frequency": "Mensal",
        "day_of_month": 14, "time_str": "09:00",
    },
    {
        "name": "Novo CAGED (Emprego)",
        "importance": "Média", "frequency": "Mensal",
        "day_of_month": 27, "time_str": "14:30",
    },
    {
        "name": "Balança Comercial (Mensal)",
        "importance": "Média", "frequency": "Mensal",
        "day_of_month": 3, "time_str": "15:00",
    },
    {
        "name": "Copom - Decisão de Juros",
        "importance": "Alta", "frequency": "~45 dias",
        "day_of_month": 16, "time_str": "18:30",
    },
    {
        "name": "PIB Trimestral Brasil",
        "importance": "Alta", "frequency": "Trimestral",
        "day_of_month": 1, "time_str": "09:00",
    },
]

# ─── Eventos internacionais de fallback (última instância) ───
# Usados SOMENTE se: API não retorna dados futuros E cache persistente está vazio.
# Marcados com "(Estimado)" para transparência.
INTERNATIONAL_FALLBACK_TEMPLATE = [
    # EUA
    {
        "name": "Payroll (Relatório de Emprego EUA)",
        "country": "EUA", "flag": "🇺🇸",
        "importance": "Alta", "frequency": "Mensal",
        "day_of_month": 4, "time_str": "09:30",
    },
    {
        "name": "CPI (Inflação ao Consumidor EUA)",
        "country": "EUA", "flag": "🇺🇸",
        "importance": "Alta", "frequency": "Mensal",
        "day_of_month": 12, "time_str": "09:30",
    },
    {
        "name": "Vendas no Varejo (EUA)",
        "country": "EUA", "flag": "🇺🇸",
        "importance": "Média", "frequency": "Mensal",
        "day_of_month": 15, "time_str": "09:30",
    },
    {
        "name": "Ata do FOMC (Federal Reserve)",
        "country": "EUA", "flag": "🇺🇸",
        "importance": "Alta", "frequency": "~45 dias",
        "day_of_month": 19, "time_str": "15:00",
    },
    {
        "name": "PIB Trimestral EUA",
        "country": "EUA", "flag": "🇺🇸",
        "importance": "Alta", "frequency": "Trimestral",
        "day_of_month": 27, "time_str": "09:30",
    },
    {
        "name": "PCE (Inflação Preferida do Fed)",
        "country": "EUA", "flag": "🇺🇸",
        "importance": "Alta", "frequency": "Mensal",
        "day_of_month": 28, "time_str": "09:30",
    },
    {
        "name": "FOMC - Decisão de Juros EUA",
        "country": "EUA", "flag": "🇺🇸",
        "importance": "Alta", "frequency": "~45 dias",
        "day_of_month": 16, "time_str": "15:00",
    },
    # Europa
    {
        "name": "PIB Zona do Euro",
        "country": "Europa", "flag": "🇪🇺",
        "importance": "Média", "frequency": "Trimestral",
        "day_of_month": 14, "time_str": "06:00",
    },
    {
        "name": "BCE - Decisão de Juros Europa",
        "country": "Europa", "flag": "🇪🇺",
        "importance": "Alta", "frequency": "~45 dias",
        "day_of_month": 10, "time_str": "09:15",
    },
    {
        "name": "CPI Zona do Euro",
        "country": "Europa", "flag": "🇪🇺",
        "importance": "Alta", "frequency": "Mensal",
        "day_of_month": 17, "time_str": "06:00",
    },
    # Japão
    {
        "name": "BoJ - Decisão de Juros Japão",
        "country": "Japão", "flag": "🇯🇵",
        "importance": "Alta", "frequency": "~45 dias",
        "day_of_month": 18, "time_str": "00:00",
    },
    # Reino Unido
    {
        "name": "BoE - Decisão de Juros UK",
        "country": "Reino Unido", "flag": "🇬🇧",
        "importance": "Alta", "frequency": "~45 dias",
        "day_of_month": 5, "time_str": "08:00",
    },
]


# ─────────────────────────────────────────
# Cache persistente (sobrevive entre page refreshes)
# ─────────────────────────────────────────
@st.cache_resource
def _get_persistent_cache():
    """
    Armazena a última resposta válida da API com eventos futuros.
    Usa cache_resource para persistir entre refreshes (só perde no reboot).
    Retorna um dict mutável que funciona como storage singleton.
    """
    return {"events": [], "fetched_at": None}


def _save_to_persistent_cache(events: list, fetched_at: datetime):
    """Salva eventos no cache persistente."""
    cache = _get_persistent_cache()
    cache["events"] = events
    cache["fetched_at"] = fetched_at


def _load_from_persistent_cache() -> tuple:
    """Carrega eventos do cache persistente. Retorna (events, fetched_at)."""
    cache = _get_persistent_cache()
    return cache.get("events", []), cache.get("fetched_at")


# ─────────────────────────────────────────
# Geração de eventos estáticos (fallback)
# ─────────────────────────────────────────
def _generate_static_events(templates: list, country: str = None,
                            flag: str = None, now: datetime = None) -> list:
    """
    Gera eventos a partir de templates para o mês corrente e o próximo.
    Eventos gerados são marcados com source='estimated'.
    """
    if now is None:
        now = datetime.now(BRT)

    events = []
    for month_offset in range(2):  # mês atual e próximo
        target_month = now.month + month_offset
        target_year = now.year
        if target_month > 12:
            target_month -= 12
            target_year += 1

        for tmpl in templates:
            try:
                day = tmpl["day_of_month"]
                h, m = [int(x) for x in tmpl["time_str"].split(":")]
                dt_obj = datetime(target_year, target_month, day, h, m, tzinfo=BRT)

                date_str = dt_obj.strftime("%d/%m")
                date_formatted = f"{date_str} · {tmpl['time_str']}"

                ev_country = tmpl.get("country", country)
                ev_flag = tmpl.get("flag", flag)

                events.append({
                    "name": tmpl["name"],
                    "country": ev_country,
                    "flag": ev_flag,
                    "importance": tmpl["importance"],
                    "frequency": tmpl.get("frequency", ""),
                    "date": date_str,
                    "time": tmpl["time_str"],
                    "date_formatted": f"~{date_formatted}",  # ~ indica estimativa
                    "dt": dt_obj,
                    "source": "estimated",
                })
            except ValueError:
                continue

    return events


# ─────────────────────────────────────────
# Fetch da API (com cache de 30 min)
# ─────────────────────────────────────────
@st.cache_data(ttl=1800, show_spinner=False)
def _fetch_api_events() -> list:
    """
    Busca eventos de ambos os endpoints da API (semana atual e próxima).
    Cache de 30 minutos para não sobrecarregar a API.
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
    """Converte eventos crus da API para o formato padrão do app."""
    parsed = []
    for ev in raw_events:
        try:
            if ev.get("impact") == "Holiday":
                continue

            currency = ev.get("country", "")
            mapping = CURRENCY_MAP.get(currency)
            if not mapping:
                continue

            date_str_raw = ev.get("date", "")
            if not date_str_raw:
                continue

            dt_obj = datetime.fromisoformat(date_str_raw).astimezone(BRT)

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


# ─────────────────────────────────────────
# Funções públicas (interface do módulo)
# ─────────────────────────────────────────
def get_economic_calendar(include_past: bool = False) -> list:
    """
    Retorna a lista de eventos econômicos ordenados cronologicamente.

    Estratégia de dados em 3 camadas:
      1. API ao vivo → dados precisos com datas reais
      2. Cache persistente → última resposta válida da API (sobrevive refreshes)
      3. Eventos estimados → datas aproximadas, marcados com "~" na data

    Eventos brasileiros são SEMPRE incluídos como complemento (API não cobre BRL).
    """
    now = datetime.now(BRT)
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)

    # ── Camada 1: API ao vivo ──
    raw_api = _fetch_api_events()
    api_events = _parse_api_events(raw_api, now)

    # Filtra apenas eventos futuros da API
    api_future = [e for e in api_events if e["dt"] >= today_start]

    # Se a API tem eventos internacionais futuros, salva no cache persistente
    api_intl_future = [e for e in api_future if e["country"] != "Brasil"]
    if api_intl_future:
        _save_to_persistent_cache(api_events, now)

    # ── Decidir fonte de dados internacionais ──
    intl_events = []

    if api_intl_future:
        # Camada 1: API tem dados futuros → usar API
        intl_events = api_events
    else:
        # Camada 2: Tentar cache persistente
        cached_events, cached_at = _load_from_persistent_cache()
        cached_future = [e for e in cached_events
                         if e["dt"] >= today_start and e["country"] != "Brasil"]
        if cached_future:
            intl_events = cached_events
        else:
            # Camada 3: Fallback com eventos estimados (marcados com ~)
            intl_events = _generate_static_events(
                INTERNATIONAL_FALLBACK_TEMPLATE, now=now
            )

    # ── Eventos brasileiros (sempre complementares) ──
    br_events = _generate_static_events(
        BRAZILIAN_EVENTS_TEMPLATE, country="Brasil", flag="🇧🇷", now=now
    )

    # ── Combina tudo ──
    all_events = intl_events + br_events

    # ── Remove duplicatas (prioriza API > cache > estimated) ──
    source_priority = {"api": 0, "cached": 1, "estimated": 2, "static": 2}
    seen_keys = set()
    unique_events = []
    for ev in sorted(all_events,
                     key=lambda x: (source_priority.get(x.get("source", ""), 9), x["dt"])):
        key = (ev["country"], ev["date"].lstrip("~"), ev["name"][:15].lower())
        if key not in seen_keys:
            seen_keys.add(key)
            unique_events.append(ev)

    # ── Filtra eventos passados ──
    if not include_past:
        unique_events = [e for e in unique_events if e["dt"] >= today_start]

    # ── Ordena cronologicamente ──
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
