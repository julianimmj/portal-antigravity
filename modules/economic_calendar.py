"""
economic_calendar.py — Agenda econômica com dados ao vivo e cache de fim de semana.

Estratégia:
  - Dias úteis (seg-sex): busca dados frescos da API a cada 30 minutos
  - Fim de semana (sáb-dom): mantém os dados obtidos na sexta-feira,
    sem tentar atualizar (a API não publica dados novos no fim de semana)
  - Após reboot no fim de semana: tenta API; se vazia, usa fallback estimado
    marcado com badge "Estimado" para transparência
  - Eventos brasileiros: sempre complementados via template (API não cobre BRL)
"""

import streamlit as st
import requests
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

# ─── URLs da API pública ───
API_URLS = [
    "https://nfs.faireconomy.media/ff_calendar_thisweek.json",
    "https://nfs.faireconomy.media/ff_calendar_nextweek.json",
]

# ─── Eventos brasileiros recorrentes (API não cobre BRL) ───
BRAZILIAN_EVENTS_TEMPLATE = [
    {"name": "IPCA (Inflação Oficial IBGE)", "importance": "Alta",
     "frequency": "Mensal", "day_of_month": 10, "time_str": "09:00"},
    {"name": "Ata do Copom (BCB)", "importance": "Alta",
     "frequency": "~45 dias", "day_of_month": 5, "time_str": "08:00"},
    {"name": "IBC-Br (Prévia do PIB BCB)", "importance": "Alta",
     "frequency": "Mensal", "day_of_month": 14, "time_str": "09:00"},
    {"name": "Novo CAGED (Emprego)", "importance": "Média",
     "frequency": "Mensal", "day_of_month": 27, "time_str": "14:30"},
    {"name": "Balança Comercial (Mensal)", "importance": "Média",
     "frequency": "Mensal", "day_of_month": 3, "time_str": "15:00"},
    {"name": "Copom - Decisão de Juros", "importance": "Alta",
     "frequency": "~45 dias", "day_of_month": 16, "time_str": "18:30"},
    {"name": "PIB Trimestral Brasil", "importance": "Alta",
     "frequency": "Trimestral", "day_of_month": 1, "time_str": "09:00"},
]

# ─── Fallback internacional (última instância, após reboot no fim de semana) ───
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


# ─────────────────────────────────────────
# Store persistente (sobrevive entre page refreshes, perde no reboot)
# ─────────────────────────────────────────
@st.cache_resource
def _get_event_store():
    """
    Singleton que armazena os dados da API entre refreshes da página.
    Funciona como a "memória" do módulo entre sessões do usuário.
    Só é limpo quando o app é reiniciado (reboot).
    """
    return {"parsed_events": [], "fetched_at": None}


def _is_weekend(now: datetime) -> bool:
    """Retorna True se for sábado (5) ou domingo (6)."""
    return now.weekday() >= 5


def _should_fetch_from_api(now: datetime) -> bool:
    """
    Decide se deve buscar dados frescos da API.

    Regras:
      - Store vazio → sempre busca (primeiro acesso ou pós-reboot)
      - Fim de semana → NÃO busca (mantém dados de sexta)
      - Dia útil + dados com mais de 30min → busca
      - Dia útil + dados frescos → não busca
    """
    store = _get_event_store()

    # Store vazio: sempre tenta buscar
    if not store["parsed_events"] or store["fetched_at"] is None:
        return True

    # Fim de semana: mantém dados da sexta
    if _is_weekend(now):
        return False

    # Dia útil: refresh a cada 30 minutos
    elapsed = (now - store["fetched_at"]).total_seconds()
    return elapsed > 1800


# ─────────────────────────────────────────
# Fetch e parse da API
# ─────────────────────────────────────────
def _fetch_raw_api() -> list:
    """Busca eventos crus de ambos endpoints da API."""
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
    """
    Obtém eventos internacionais da API com lógica de cache inteligente.

    Durante a semana: atualiza a cada 30min e armazena no store.
    No fim de semana: retorna os dados armazenados de sexta-feira.
    Após reboot: tenta API; se vazia, store está vazio → retorna [].
    """
    store = _get_event_store()

    if _should_fetch_from_api(now):
        raw = _fetch_raw_api()
        parsed = _parse_api_events(raw)

        # Só atualiza o store se a API retornou dados
        if parsed:
            store["parsed_events"] = parsed
            store["fetched_at"] = now

    return list(store["parsed_events"])  # cópia para evitar mutação


# ─────────────────────────────────────────
# Geração de eventos estáticos
# ─────────────────────────────────────────
def _generate_static_events(templates: list, country: str = None,
                            flag: str = None, now: datetime = None,
                            source: str = "estimated") -> list:
    """Gera eventos a partir de templates para mês atual e próximo."""
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

                # Prefixo "~" apenas para eventos estimados
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
    Retorna eventos econômicos ordenados cronologicamente.

    Fluxo:
      Seg-Sex: API fresca (30min cache) → dados reais da semana
      Sáb-Dom: Dados replicados de sexta (sem nova consulta à API)
      Reboot no fim de semana: tenta API → se vazia, usa fallback estimado
      Brasil: sempre via template (API não cobre BRL)
    """
    now = datetime.now(BRT)
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)

    # ── Eventos internacionais (API + cache de fim de semana) ──
    intl_events = _get_api_events(now)

    # Se após tudo não há eventos internacionais futuros,
    # usa fallback estimado (marcado com badge "Estimado")
    intl_future = [e for e in intl_events if e["dt"] >= today_start]
    if not intl_future:
        intl_events = _generate_static_events(
            INTERNATIONAL_FALLBACK_TEMPLATE, now=now, source="estimated"
        )

    # ── Eventos brasileiros (sempre complementares) ──
    br_events = _generate_static_events(
        BRAZILIAN_EVENTS_TEMPLATE,
        country="Brasil", flag="🇧🇷", now=now, source="estimated"
    )

    # ── Combina e remove duplicatas ──
    all_events = intl_events + br_events
    source_priority = {"api": 0, "estimated": 1}
    seen_keys = set()
    unique_events = []
    for ev in sorted(all_events,
                     key=lambda x: (source_priority.get(x.get("source", ""), 9), x["dt"])):
        key = (ev["country"], ev["date"].lstrip("~"), ev["name"][:15].lower())
        if key not in seen_keys:
            seen_keys.add(key)
            unique_events.append(ev)

    # ── Filtra passados ──
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
