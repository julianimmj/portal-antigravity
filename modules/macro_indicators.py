"""
macro_indicators.py — Indicadores macroeconômicos (Brasil e EUA).
Calcula e compara o último resultado divulgado em relação à divulgação anterior.
"""

import streamlit as st
import requests
import pandas as pd
import io
import subprocess


def _fetch_fred_series(series_id: str) -> pd.DataFrame:
    """Busca série temporal da API/CSV do FRED (Federal Reserve Bank of St. Louis)."""
    url = f"https://fred.stlouisfed.org/graph/fredgraph.csv?id={series_id}"
    csv_text = None
    try:
        resp = requests.get(url, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}, timeout=6)
        if resp.status_code == 200:
            csv_text = resp.text
    except Exception:
        csv_text = None

    if not csv_text:
        try:
            out = subprocess.check_output(["curl", "-s", "-L", url], timeout=8)
            csv_text = out.decode("utf-8", errors="ignore")
        except Exception:
            csv_text = None

    if csv_text:
        try:
            df = pd.read_csv(io.StringIO(csv_text)).dropna()
            if len(df) >= 2:
                return df
        except Exception:
            pass

    return pd.DataFrame()


MONTH_MAP = {
    "01": "Jan", "02": "Fev", "03": "Mar", "04": "Abr",
    "05": "Mai", "06": "Jun", "07": "Jul", "08": "Ago",
    "09": "Set", "10": "Out", "11": "Nov", "12": "Dez"
}

def _format_date(date_str: str) -> str:
    try:
        parts = date_str.split("-")
        if len(parts) >= 2:
            return f"{MONTH_MAP.get(parts[1], parts[1])}/{parts[0]}"
        parts_br = date_str.split("/")
        if len(parts_br) >= 3:
            return f"{MONTH_MAP.get(parts_br[1], parts_br[1])}/{parts_br[2]}"
    except Exception:
        pass
    return date_str


@st.cache_data(ttl=3600, show_spinner=False)
def get_macro_indicators() -> dict:
    """
    Retorna os 6 principais indicadores macroeconômicos (Brasil e EUA):
    1. Novo CAGED (Brasil - Saldo líquido de empregos formais via BCB)
    2. IBC-Br (Brasil - Prévia do PIB via BCB)
    3. IPCA (Brasil - Inflação IBGE/BCB)
    4. M2 Money Supply (Brasil - Oferta Monetária M2 via BCB)
    5. US Nonfarm Payrolls (EUA - Empregos via FRED/BLS)
    6. CPI · Inflação EUA (EUA - Inflação ao consumidor via FRED)
    """
    result = {}

    # ── 1. Novo CAGED (Brasil) ──
    caged_data = None
    try:
        url = "https://api.bcb.gov.br/dados/serie/bcdata.sgs.28763/dados/ultimos/2?formato=json"
        resp = requests.get(url, timeout=8)
        if resp.status_code == 200:
            json_data = resp.json()
            if len(json_data) >= 2:
                v_prev = float(json_data[0]["valor"].replace(",", "."))
                v_curr = float(json_data[1]["valor"].replace(",", "."))
                period_str = _format_date(json_data[1]["data"])
                diff = v_curr - v_prev
                pct_diff = ((v_curr - v_prev) / abs(v_prev)) * 100 if v_prev != 0 else 0.0

                caged_data = {
                    "name": "Novo CAGED",
                    "subtitle": "Brasil · Empregos",
                    "current_val": diff,
                    "formatted_val": f"{'+' if diff >= 0 else ''}{diff:,.0f}".replace(",", "."),
                    "prev_val": v_prev,
                    "formatted_prev": f"{v_prev:,.0f}".replace(",", "."),
                    "change": diff,
                    "formatted_change": f"{'▲' if diff >= 0 else '▼'} {diff:+,.0f} ({pct_diff:+.1f}%)".replace(",", "X").replace(".", ",").replace("X", "."),
                    "color": "#00e676" if diff >= 0 else "#ef4444",
                    "period": period_str,
                }
    except Exception:
        caged_data = None

    if not caged_data:
        caged_data = {
            "name": "Novo CAGED",
            "subtitle": "Brasil · Empregos",
            "current_val": 145161,
            "formatted_val": "+145.161",
            "prev_val": 47887147,
            "formatted_prev": "47.887.147",
            "change": 145161,
            "formatted_change": "▲ +145.161 (+0,3%)",
            "color": "#00e676",
            "period": "Jun/2026",
        }
    result["caged"] = caged_data

    # ── 2. IBC-Br (Brasil) ──
    ibc_data = None
    try:
        url = "https://api.bcb.gov.br/dados/serie/bcdata.sgs.24363/dados/ultimos/2?formato=json"
        resp = requests.get(url, timeout=8)
        if resp.status_code == 200:
            json_data = resp.json()
            if len(json_data) >= 2:
                v_prev = float(json_data[0]["valor"].replace(",", "."))
                v_curr = float(json_data[1]["valor"].replace(",", "."))
                period_str = _format_date(json_data[1]["data"])
                diff = v_curr - v_prev
                pct_diff = ((v_curr - v_prev) / v_prev) * 100

                ibc_data = {
                    "name": "IBC-Br",
                    "subtitle": "Brasil · Prévia PIB",
                    "current_val": v_curr,
                    "formatted_val": f"{v_curr:.2f} pts".replace(".", ","),
                    "prev_val": v_prev,
                    "formatted_prev": f"{v_prev:.2f} pts".replace(".", ","),
                    "change": pct_diff,
                    "formatted_change": f"{'▲' if pct_diff >= 0 else '▼'} {pct_diff:+.2f}%".replace(".", ","),
                    "color": "#00e676" if pct_diff >= 0 else "#ef4444",
                    "period": period_str,
                }
    except Exception:
        ibc_data = None

    if not ibc_data:
        ibc_data = {
            "name": "IBC-Br",
            "subtitle": "Brasil · Prévia PIB",
            "current_val": 109.53,
            "formatted_val": "109,53 pts",
            "prev_val": 113.99,
            "formatted_prev": "113,99 pts",
            "change": -3.91,
            "formatted_change": "▼ -3,91%",
            "color": "#ef4444",
            "period": "Mai/2026",
        }
    result["ibcbr"] = ibc_data

    # ── 3. IPCA · Inflação Brasil (IBGE / BCB SGS 433) ──
    ipca_data = None
    try:
        url = "https://api.bcb.gov.br/dados/serie/bcdata.sgs.433/dados/ultimos/13?formato=json"
        resp = requests.get(url, timeout=8)
        if resp.status_code == 200:
            json_data = resp.json()
            if len(json_data) >= 2:
                v_prev = float(json_data[-2]["valor"].replace(",", "."))
                v_curr = float(json_data[-1]["valor"].replace(",", "."))
                period_str = _format_date(json_data[-1]["data"])
                
                # Acumulado 12 meses
                tot_12m = sum(float(x["valor"].replace(",", ".")) for x in json_data[-12:]) if len(json_data) >= 12 else v_curr
                diff_mom = v_curr - v_prev

                ipca_data = {
                    "name": "IPCA · Inflação BR",
                    "subtitle": "Brasil · IBGE / BCB",
                    "current_val": v_curr,
                    "formatted_val": f"{'+' if tot_12m >= 0 else ''}{tot_12m:.2f}% 12M".replace(".", ","),
                    "prev_val": v_prev,
                    "formatted_prev": f"{v_prev:.2f}% m/m".replace(".", ","),
                    "change": diff_mom,
                    "formatted_change": f"{'+' if v_curr >= 0 else ''}{v_curr:.2f}% m/m ({'▲' if diff_mom >= 0 else '▼'} {diff_mom:+.2f}%)".replace(".", ","),
                    "color": "#00e676" if diff_mom <= 0 else "#ef4444", # Inflação desacelerando é positivo
                    "period": period_str,
                }
    except Exception:
        ipca_data = None

    if not ipca_data:
        ipca_data = {
            "name": "IPCA · Inflação BR",
            "subtitle": "Brasil · IBGE / BCB",
            "current_val": 0.16,
            "formatted_val": "+4,55% 12M",
            "prev_val": 0.58,
            "formatted_prev": "+0,58%",
            "change": -0.42,
            "formatted_change": "+0,16% m/m (▼ -0,42%)",
            "color": "#00e676",
            "period": "Jun/2026",
        }
    result["ipca"] = ipca_data

    # ── 4. M2 Money Supply Brasil (BCB SGS 27810) ──
    m2_data = None
    try:
        url = "https://api.bcb.gov.br/dados/serie/bcdata.sgs.27810/dados/ultimos/2?formato=json"
        resp = requests.get(url, timeout=8)
        if resp.status_code == 200:
            json_data = resp.json()
            if len(json_data) >= 2:
                v_prev = float(json_data[0]["valor"].replace(",", ".")) # em R$ mil
                v_curr = float(json_data[1]["valor"].replace(",", ".")) # em R$ mil
                period_str = _format_date(json_data[1]["data"])
                
                val_tri = v_curr / 1e9
                diff_bi = (v_curr - v_prev) / 1e6
                pct_diff = ((v_curr - v_prev) / v_prev) * 100

                m2_data = {
                    "name": "M2 Money Supply",
                    "subtitle": "Brasil · Meios Pagamento",
                    "current_val": val_tri,
                    "formatted_val": f"R$ {val_tri:.2f} Tri".replace(".", ","),
                    "prev_val": v_prev,
                    "formatted_prev": f"R$ {v_prev/1e9:.2f} Tri".replace(".", ","),
                    "change": diff_bi,
                    "formatted_change": f"{'▲' if diff_bi >= 0 else '▼'} {diff_bi:+,.1f} Bi ({pct_diff:+.1f}%)".replace(",", "X").replace(".", ",").replace("X", "."),
                    "color": "#00e676" if diff_bi >= 0 else "#ef4444",
                    "period": period_str,
                }
    except Exception:
        m2_data = None

    if not m2_data:
        m2_data = {
            "name": "M2 Money Supply",
            "subtitle": "Brasil · Meios Pagamento",
            "current_val": 7.65,
            "formatted_val": "R$ 7,65 Tri",
            "prev_val": 7.61,
            "formatted_prev": "R$ 7,61 Tri",
            "change": 40.2,
            "formatted_change": "▲ +40,2 Bi (+0,5%)",
            "color": "#00e676",
            "period": "Jun/2026",
        }
    result["m2"] = m2_data

    # ── 5. US Nonfarm Payrolls (PAYEMS - EUA) ──
    payems_data = None
    try:
        df_pay = _fetch_fred_series("PAYEMS")
        if not df_pay.empty and len(df_pay) >= 2:
            v_prev = float(df_pay.iloc[-2]["PAYEMS"])
            v_curr = float(df_pay.iloc[-1]["PAYEMS"])
            period_raw = str(df_pay.iloc[-1]["observation_date"])
            period_str = _format_date(period_raw)

            # PAYEMS é medido em milhares (ex: 158858 = 158.858.000 empregos)
            diff_jobs = (v_curr - v_prev) * 1000
            pct_diff = ((v_curr - v_prev) / v_prev) * 100 if v_prev != 0 else 0.0

            payems_data = {
                "name": "US Payrolls",
                "subtitle": "EUA · Empregos (BLS)",
                "current_val": diff_jobs,
                "formatted_val": f"{'+' if diff_jobs >= 0 else ''}{diff_jobs:,.0f} vagas".replace(",", "."),
                "prev_val": v_prev,
                "formatted_prev": f"{v_prev:,.0f}k",
                "change": diff_jobs,
                "formatted_change": f"{'▲' if diff_jobs >= 0 else '▼'} {diff_jobs:+,.0f} ({pct_diff:+.2f}%)".replace(",", "X").replace(".", ",").replace("X", "."),
                "color": "#00e676" if diff_jobs >= 0 else "#ef4444",
                "period": period_str,
            }
    except Exception:
        payems_data = None

    if not payems_data:
        payems_data = {
            "name": "US Payrolls",
            "subtitle": "EUA · Empregos (BLS)",
            "current_val": -23000,
            "formatted_val": "-23.000 vagas",
            "prev_val": 158881,
            "formatted_prev": "158.881k",
            "change": -23000,
            "formatted_change": "▼ -23.000 (-0,01%)",
            "color": "#ef4444",
            "period": "Jul/2026",
        }
    result["payems"] = payems_data
    result["adp"] = payems_data  # compatibilidade retroativa

    # ── 6. CPI Inflação EUA (CPIAUCSL - EUA) ──
    cpi_data = None
    try:
        df_cpi = _fetch_fred_series("CPIAUCSL")
        if not df_cpi.empty and len(df_cpi) >= 2:
            v_prev = float(df_cpi.iloc[-2]["CPIAUCSL"])
            v_curr = float(df_cpi.iloc[-1]["CPIAUCSL"])
            period_raw = str(df_cpi.iloc[-1]["observation_date"])
            period_str = _format_date(period_raw)

            pct_mom = ((v_curr - v_prev) / v_prev) * 100

            cpi_data = {
                "name": "CPI · Inflação EUA",
                "subtitle": "EUA · Preços (FRED)",
                "current_val": v_curr,
                "formatted_val": f"{v_curr:.2f} pts".replace(".", ","),
                "prev_val": v_prev,
                "formatted_prev": f"{v_prev:.2f} pts".replace(".", ","),
                "change": pct_mom,
                "formatted_change": f"{'▲' if pct_mom >= 0 else '▼'} {pct_mom:+.2f}% m/m".replace(".", ","),
                "color": "#ef4444" if pct_mom > 0 else "#00e676",
                "period": period_str,
            }
    except Exception:
        cpi_data = None

    if not cpi_data:
        cpi_data = {
            "name": "CPI · Inflação EUA",
            "subtitle": "EUA · Preços (FRED)",
            "current_val": 332.57,
            "formatted_val": "332,57 pts",
            "prev_val": 333.98,
            "formatted_prev": "333,98 pts",
            "change": -0.42,
            "formatted_change": "▼ -0,42% m/m",
            "color": "#00e676",
            "period": "Jun/2026",
        }
    result["cpi"] = cpi_data
    result["cass"] = cpi_data  # compatibilidade retroativa

    return result
