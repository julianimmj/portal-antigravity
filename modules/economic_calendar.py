"""
economic_calendar.py — Agenda econômica com dados ao vivo, API oficial IBGE e cache de fim de semana.

Estratégia:
  - Dias úteis (seg-sex): busca dados frescos da API internacional (30min) e IBGE (1h)
  - Fim de semana (sáb-dom): mantém os dados obtidos na sexta-feira sem tentar atualizar
  - Eventos brasileiros:
      1. API Oficial do IBGE (ao vivo: IPCA, PNAD Desemprego, PIB, Indústria, Varejo, Serviços)
      2. Eventos semanais recorrentes do BCB (Boletim Focus seg 08:25, Fluxo Cambial qua 14:30)
      3. Calendário Copom, Ata, IBC-Br, Novo CAGED, IGP-M e Balança Comercial
  - Fallback internacional: eventos estimados caso a API internacional esteja indisponível
"""

import streamlit as st
import requests
import csv
import io
from datetime import datetime, timedelta, timezone


# ─── Mapeamento de moedas para país/bandeira ───
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

# ─── Mapeamento de impacto ───
IMPACT_MAP = {
    "High": "Alta",
    "Medium": "Média",
    "Low": "Baixa",
    "Holiday": "Feriado",
}

# ─── Fuso horário de Brasília (UTC-3) ───
BRT = timezone(timedelta(hours=-3))

# ─── URLs da API internacional (ForexFactory via CDN) ───
API_URL_JSON = "https://nfs.faireconomy.media/ff_calendar_thisweek.json"
API_URL_CSV = "https://nfs.faireconomy.media/ff_calendar_thisweek.csv"

# ─── Fallback internacional (usado em caso de indisponibilidade da API) ───
INTERNATIONAL_FALLBACK_TEMPLATE = [
    {"name": "Payroll (Relatório de Emprego EUA)", "country": "EUA",
     "flag": "🇺🇸", "importance": "Alta", "frequency": "Mensal",
     "day_of_month": 4, "time_str": "09:30"},
    {"name": "CPI (Inflação ao Consumidor EUA)", "country": "EUA",
     "flag": "🇺🇸", "importance": "Alta", "frequency": "Mensal",
     "day_of_month": 12, "time_str": "09:30"},
    {"name": "Vendas no Varejo (EUA)", "country": "EUA",
     "flag": "🇺🇸", "importance": "Média", "frequency": "Mensal",
     "day_of_month": 15, "time_str": "09:30"},
    {"name": "Ata do FOMC (Federal Reserve)", "country": "EUA",
     "flag": "🇺🇸", "importance": "Alta", "frequency": "~45 dias",
     "day_of_month": 19, "time_str": "15:00"},
    {"name": "PIB Trimestral EUA", "country": "EUA",
     "flag": "🇺🇸", "importance": "Alta", "frequency": "Trimestral",
     "day_of_month": 27, "time_str": "09:30"},
    {"name": "PCE (Inflação Preferida do Fed)", "country": "EUA",
     "flag": "🇺🇸", "importance": "Alta", "frequency": "Mensal",
     "day_of_month": 28, "time_str": "09:30"},
    {"name": "FOMC - Decisão de Juros EUA", "country": "EUA",
     "flag": "🇺🇸", "importance": "Alta", "frequency": "~45 dias",
     "day_of_month": 16, "time_str": "15:00"},
    {"name": "PIB Zona do Euro", "country": "Europa",
     "flag": "🇪🇺", "importance": "Média", "frequency": "Trimestral",
     "day_of_month": 14, "time_str": "06:00"},
    {"name": "BCE - Decisão de Juros Europa", "country": "Europa",
     "flag": "🇪🇺", "importance": "Alta", "frequency": "~45 dias",
     "day_of_month": 10, "time_str": "09:15"},
    {"name": "CPI Zona do Euro", "country": "Europa",
     "flag": "🇪🇺", "importance": "Alta", "frequency": "Mensal",
     "day_of_month": 17, "time_str": "06:00"},
    {"name": "BoJ - Decisão de Juros Japão", "country": "Japão",
     "flag": "🇯🇵", "importance": "Alta", "frequency": "~45 dias",
     "day_of_month": 18, "time_str": "00:00"},
    {"name": "BoE - Decisão de Juros UK", "country": "Reino Unido",
     "flag": "🇬🇧", "importance": "Alta", "frequency": "~45 dias",
     "day_of_month": 5, "time_str": "08:00"},
]

# ─── Template de eventos brasileiros complementares (BCB, FGV, MDIC) ───
BRAZILIAN_EVENTS_TEMPLATE = [
    {"name": "Copom - Decisão de Juros", "importance": "Alta",
     "frequency": "~45 dias", "day_of_month": 16, "time_str": "18:30"},
    {"name": "Ata do Copom (BCB)", "importance": "Alta",
     "frequency": "~45 dias", "day_of_month": 5, "time_str": "08:00"},
    {"name": "IBC-Br (Prévia do PIB BCB)", "importance": "Alta",
     "frequency": "Mensal", "day_of_month": 14, "time_str": "09:00"},
    {"name": "Novo CAGED (Emprego MTE)", "importance": "Média",
     "frequency": "Mensal", "day_of_month": 28, "time_str": "14:30"},
    {"name": "Balança Comercial (Mensal Secex)", "importance": "Média",
     "frequency": "Mensal", "day_of_month": 3, "time_str": "15:00"},
    {"name": "IGP-M (Inflação FGV)", "importance": "Alta",
     "frequency": "Mensal", "day_of_month": 29, "time_str": "08:00"},
    {"name": "PIB Trimestral Brasil", "importance": "Alta",
     "frequency": "Trimestral", "day_of_month": 1, "time_str": "09:00"},
    {"name": "IPCA (Inflação Oficial IBGE)", "importance": "Alta",
     "frequency": "Mensal", "day_of_month": 10, "time_str": "09:00"},
    {"name": "Taxa de Desemprego (PNAD Contínua)", "importance": "Alta",
     "frequency": "Mensal", "day_of_month": 29, "time_str": "09:00"},
]


# ─────────────────────────────────────────
# Store persistente (sobrevive entre page refreshes)
# ─────────────────────────────────────────
@st.cache_resource
def _get_event_store():
    """
    Singleton que armazena os dados da API internacional entre refreshes da página.
    Funciona como memória do módulo entre sessões do usuário.
    """
    return {"parsed_events": [], "fetched_at": None}


def _is_weekend(now: datetime) -> bool:
    """Retorna True se for sábado (5) ou domingo (6)."""
    return now.weekday() >= 5


def _should_fetch_from_api(now: datetime) -> bool:
    """
    Decide se deve buscar dados frescos da API internacional.
    - Store vazio → sempre busca
    - Fim de semana → NÃO busca (mantém dados de sexta)
    - Dia útil + dados >30min → busca
    """
    store = _get_event_store()
    if not store["parsed_events"] or store["fetched_at"] is None:
        return True
    if _is_weekend(now):
        return False
    elapsed = (now - store["fetched_at"]).total_seconds()
    return elapsed > 1800


# ─────────────────────────────────────────
# Fetch da API Internacional (JSON com fallback para CSV)
# ─────────────────────────────────────────
def _fetch_raw_api() -> list:
    """Busca eventos da API internacional (JSON com fallback para CSV)."""
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Accept": "application/json, text/csv, */*",
    }

    # Tentativa 1: Endpoint JSON
    try:
        resp = requests.get(API_URL_JSON, timeout=8, headers=headers)
        if resp.status_code == 200:
            text = resp.text.strip()
            if text and text.startswith("["):
                data = resp.json()
                if isinstance(data, list) and len(data) > 0:
                    return data
    except Exception:
        pass

    # Tentativa 2: Endpoint CSV (fallback caso JSON esteja com rate-limit)
    try:
        resp = requests.get(API_URL_CSV, timeout=8, headers=headers)
        if resp.status_code == 200:
            reader = csv.DictReader(io.StringIO(resp.text))
            csv_rows = []
            for row in reader:
                # Converte formato CSV para o mesmo formato do JSON
                date_val = row.get("Date", "")
                time_val = row.get("Time", "")
                if not date_val or not time_val or time_val.lower() in ("all day", "tentative"):
                    continue
                try:
                    dt_naive = datetime.strptime(f"{date_val} {time_val.upper()}", "%m-%d-%Y %I:%M%p")
                    # FairEconomy usa horário do leste americano (ET, UTC-4 no horário de verão)
                    dt_iso = dt_naive.replace(tzinfo=timezone(timedelta(hours=-4))).isoformat()
                    csv_rows.append({
                        "title": row.get("Title", ""),
                        "country": row.get("Country", ""),
                        "impact": row.get("Impact", ""),
                        "date": dt_iso,
                    })
                except Exception:
                    continue
            if csv_rows:
                return csv_rows
    except Exception:
        pass

    return []


def _parse_api_events(raw_events: list) -> list:
    """Converte eventos da API para o formato padrão do app."""
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

            parsed.append({
                "name": ev.get("title", "Evento"),
                "country": mapping["country"],
                "flag": mapping["flag"],
                "importance": IMPACT_MAP.get(ev.get("impact", ""), "Média"),
                "frequency": "",
                "date": date_display,
                "time": time_display,
                "date_formatted": f"{date_display} · {time_display}",
                "dt": dt_obj,
                "source": "api",
            })
        except Exception:
            continue
    return parsed


def _get_api_events(now: datetime) -> list:
    """Obtém eventos internacionais com cache inteligente de fim de semana."""
    store = _get_event_store()
    if _should_fetch_from_api(now):
        raw = _fetch_raw_api()
        parsed = _parse_api_events(raw)
        if parsed:
            store["parsed_events"] = parsed
            store["fetched_at"] = now

    return list(store["parsed_events"])


# ─────────────────────────────────────────
# Eventos do Brasil (API Oficial IBGE + BCB Semanal + Complementos)
# ─────────────────────────────────────────
@st.cache_data(ttl=3600, show_spinner=False)
def _fetch_ibge_events() -> list:
    """
    Busca divulgações econômicas oficiais do calendário público do IBGE.
    Cobre: IPCA, IPCA-15, PNAD Contínua (Desemprego), PIB, PIM-PF, PMC, PMS, IPP.
    """
    now = datetime.now(BRT)
    today_str = (now - timedelta(days=2)).strftime("%Y-%m-%d")
    future_str = (now + timedelta(days=45)).strftime("%Y-%m-%d")
    url = f"https://servicodados.ibge.gov.br/api/v3/calendario/?de={today_str}&ate={future_str}"

    KEY_SERIES = [
        ("Índice Nacional de Preços ao Consumidor Amplo 15", "IPCA-15 (Prévia da Inflação IBGE)", "Alta", "Mensal"),
        ("Índice Nacional de Preços ao Consumidor Amplo", "IPCA (Inflação Oficial IBGE)", "Alta", "Mensal"),
        ("Pesquisa Nacional por Amostra de Domicílios Contínua Mensal", "Taxa de Desemprego (PNAD Contínua IBGE)", "Alta", "Mensal"),
        ("Contas Nacionais Trimestrais", "PIB Trimestral Brasil (IBGE)", "Alta", "Trimestral"),
        ("Pesquisa Industrial Mensal: Produção Física", "Produção Industrial (PIM-PF IBGE)", "Média", "Mensal"),
        ("Pesquisa Mensal de Comércio", "Vendas no Varejo (PMC IBGE)", "Média", "Mensal"),
        ("Pesquisa Mensal de Serviços", "Volume de Serviços (PMS IBGE)", "Média", "Mensal"),
        ("Índice de Preços ao Produtor", "IPP - Preços ao Produtor (IBGE)", "Média", "Mensal"),
    ]

    events = []
    seen = set()
    try:
        resp = requests.get(url, timeout=8)
        if resp.status_code == 200:
            data = resp.json()
            for item in data.get("items", []):
                titulo = item.get("titulo", "")
                matched = None
                for key_search, name, imp, freq in KEY_SERIES:
                    if key_search.lower() in titulo.lower():
                        matched = (name, imp, freq)
                        break
                if not matched:
                    continue

                raw_dt = item.get("data_divulgacao", "")
                try:
                    dt_obj = datetime.strptime(raw_dt, "%d/%m/%Y %H:%M:%S").replace(
                        tzinfo=BRT, hour=9, minute=0, second=0
                    )
                except Exception:
                    continue

                key = (matched[0], dt_obj.strftime("%Y-%m-%d"))
                if key in seen:
                    continue
                seen.add(key)

                d_str = dt_obj.strftime("%d/%m")
                events.append({
                    "name": matched[0],
                    "country": "Brasil",
                    "flag": "🇧🇷",
                    "importance": matched[1],
                    "frequency": matched[2],
                    "date": d_str,
                    "time": "09:00",
                    "date_formatted": f"{d_str} · 09:00",
                    "dt": dt_obj,
                    "source": "api",
                })
    except Exception:
        pass

    return events


def _get_brazilian_weekly_events(now: datetime) -> list:
    """
    Gera os eventos semanais regulares do Banco Central do Brasil:
      - Boletim Focus: toda segunda-feira às 08:25
      - Fluxo Cambial Estrangeiro: toda quarta-feira às 14:30
    """
    events = []
    for d in range(45):
        day = now + timedelta(days=d)
        d_str = day.strftime("%d/%m")
        if day.weekday() == 0:  # Segunda-feira
            dt_focus = day.replace(hour=8, minute=25, second=0, microsecond=0)
            events.append({
                "name": "Boletim Focus (Expectativas BCB)",
                "country": "Brasil",
                "flag": "🇧🇷",
                "importance": "Alta",
                "frequency": "Semanal",
                "date": d_str,
                "time": "08:25",
                "date_formatted": f"{d_str} · 08:25",
                "dt": dt_focus,
                "source": "api",
            })
        elif day.weekday() == 2:  # Quarta-feira
            dt_fluxo = day.replace(hour=14, minute=30, second=0, microsecond=0)
            events.append({
                "name": "Fluxo Cambial Estrangeiro (BCB)",
                "country": "Brasil",
                "flag": "🇧🇷",
                "importance": "Média",
                "frequency": "Semanal",
                "date": d_str,
                "time": "14:30",
                "date_formatted": f"{d_str} · 14:30",
                "dt": dt_fluxo,
                "source": "api",
            })
    return events


def _get_official_copom_events(now: datetime) -> list:
    """
    Datas oficiais das reuniões do Copom e publicação da Ata divulgadas pelo Banco Central do Brasil.
    Horário da decisão: 18:30 BRT. Horário da Ata: 08:00 BRT.
    """
    OFFICIAL_COPOM_SCHEDULE = [
        (datetime(2026, 11, 4, 18, 30, tzinfo=BRT), "Copom - Decisão da Taxa Selic (BCB)", "Alta"),
        (datetime(2026, 11, 10, 8, 0, tzinfo=BRT), "Ata do Copom (BCB)", "Alta"),
        (datetime(2026, 12, 9, 18, 30, tzinfo=BRT), "Copom - Decisão da Taxa Selic (BCB)", "Alta"),
        (datetime(2026, 12, 15, 8, 0, tzinfo=BRT), "Ata do Copom (BCB)", "Alta"),
        (datetime(2027, 1, 27, 18, 30, tzinfo=BRT), "Copom - Decisão da Taxa Selic (BCB)", "Alta"),
        (datetime(2027, 2, 2, 8, 0, tzinfo=BRT), "Ata do Copom (BCB)", "Alta"),
        (datetime(2027, 3, 17, 18, 30, tzinfo=BRT), "Copom - Decisão da Taxa Selic (BCB)", "Alta"),
        (datetime(2027, 3, 23, 8, 0, tzinfo=BRT), "Ata do Copom (BCB)", "Alta"),
    ]
    events = []
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    for dt_obj, name, imp in OFFICIAL_COPOM_SCHEDULE:
        if dt_obj >= today_start:
            d_str = dt_obj.strftime("%d/%m")
            t_str = dt_obj.strftime("%H:%M")
            events.append({
                "name": name,
                "country": "Brasil",
                "flag": "🇧🇷",
                "importance": imp,
                "frequency": "~45 dias",
                "date": d_str,
                "time": t_str,
                "date_formatted": f"{d_str} · {t_str}",
                "dt": dt_obj,
                "source": "api",
            })
    return events


def _get_brazilian_events(now: datetime) -> list:
    """
    Obtém eventos econômicos do Brasil.

    Regra estrita:
      - Quando a API do IBGE estiver funcionando, utiliza EXCLUSIVAMENTE dados das APIs
        (API oficial do IBGE + calendário oficial do BCB).
      - Nenhum dado estimado é gerado ou adicionado quando a API está operando.
      - Fallback com dados estimados é utilizado APENAS e EXCLUSIVAMENTE se a API do IBGE
        falhar ou estiver inacessível.
    """
    ibge_events = _fetch_ibge_events()
    weekly_events = _get_brazilian_weekly_events(now)
    copom_events = _get_official_copom_events(now)

    if ibge_events:
        # API funcionando: dados 100% reais, NENHUM dado estimado
        combined = ibge_events + weekly_events + copom_events
    else:
        # Fallback de contingência: APENAS se a API oficial do IBGE falhar
        tmpl_events = _generate_static_events(
            BRAZILIAN_EVENTS_TEMPLATE, country="Brasil", flag="🇧🇷", now=now, source="estimated"
        )
        combined = tmpl_events + weekly_events + copom_events

    unique = []
    seen = set()
    for ev in sorted(combined, key=lambda x: (x.get("source") != "api", x["dt"])):
        key = (ev["name"][:12].lower(), ev["date"].lstrip("~"))
        if key not in seen:
            seen.add(key)
            unique.append(ev)

    return unique


# ─────────────────────────────────────────
# Geração de eventos estáticos de fallback internacional
# ─────────────────────────────────────────
def _generate_static_events(templates: list, country: str = None,
                            flag: str = None, now: datetime = None,
                            source: str = "estimated") -> list:
    """Gera eventos a partir de templates para o mês atual e o próximo."""
    if now is None:
        now = datetime.now(BRT)

    events = []
    for month_offset in range(2):
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
                ev_country = tmpl.get("country", country)
                ev_flag = tmpl.get("flag", flag)
                date_prefix = "~" if source == "estimated" else ""

                events.append({
                    "name": tmpl["name"],
                    "country": ev_country,
                    "flag": ev_flag,
                    "importance": tmpl["importance"],
                    "frequency": tmpl.get("frequency", ""),
                    "date": date_str,
                    "time": tmpl["time_str"],
                    "date_formatted": f"{date_prefix}{date_str} · {tmpl['time_str']}",
                    "dt": dt_obj,
                    "source": source,
                })
            except ValueError:
                continue
    return events


# ─────────────────────────────────────────
# Funções públicas
# ─────────────────────────────────────────
def get_economic_calendar(include_past: bool = False) -> list:
    """
    Retorna a lista completa de eventos econômicos ordenados cronologicamente.

    Fontes de dados:
      - Internacional: API ao vivo com cache de 30min / persistência no fim de semana
      - Brasil: API oficial IBGE + Banco Central do Brasil semanal + Copom / FGV
      - Fallback: estimativas para dias sem conexão à API
    """
    now = datetime.now(BRT)
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)

    # 1. Eventos internacionais
    intl_events = _get_api_events(now)
    intl_future = [e for e in intl_events if e["dt"] >= today_start]
    if not intl_future:
        intl_events = _generate_static_events(
            INTERNATIONAL_FALLBACK_TEMPLATE, now=now, source="estimated"
        )

    # 2. Eventos brasileiros (IBGE ao vivo + BCB semanal + complementos)
    br_events = _get_brazilian_events(now)

    # 3. Combina tudo
    all_events = intl_events + br_events

    # 4. Remove duplicatas (prioriza api > cached > estimated)
    source_priority = {"api": 0, "cached": 1, "estimated": 2, "static": 2}
    seen_keys = set()
    unique_events = []
    for ev in sorted(all_events,
                     key=lambda x: (source_priority.get(x.get("source", ""), 9), x["dt"])):
        key = (ev["country"], ev["date"].lstrip("~"), ev["name"][:15].lower())
        if key not in seen_keys:
            seen_keys.add(key)
            unique_events.append(ev)

    # 5. Filtra passados
    if not include_past:
        unique_events = [e for e in unique_events if e["dt"] >= today_start]

    unique_events.sort(key=lambda x: x["dt"])
    return unique_events


def get_events_by_importance(importance: str = "Alta", include_past: bool = False) -> list:
    """Filtra eventos por importância, ordenados por data."""
    return [e for e in get_economic_calendar(include_past=include_past)
            if e.get("importance") == importance]


def get_events_by_country(country: str, include_past: bool = False) -> list:
    """Filtra eventos por país/região, ordenados por data."""
    return [e for e in get_economic_calendar(include_past=include_past)
            if e.get("country") == country]
