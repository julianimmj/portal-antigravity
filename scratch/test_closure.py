import sys
sys.path.insert(0, '.')

from modules.market_summary import get_market_quotes, get_earnings_analysis, get_market_summary
from modules.market_data import get_top_movers
import datetime

d_now = datetime.datetime.now()
dias_semana = ["Segunda-feira", "Terça-feira", "Quarta-feira", "Quinta-feira", "Sexta-feira", "Sábado", "Domingo"]
meses = ["Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho", "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"]
data_formatada = f"{dias_semana[d_now.weekday()]}, {d_now.day} de {meses[d_now.month - 1]} de {d_now.year}"

print(f"=== {data_formatada} ===")

quotes = get_market_quotes()
print("Quotes:", [(q.get('symbol'), q.get('price'), q.get('change_pct')) for q in quotes if isinstance(q, dict)])

earnings = get_earnings_analysis(region="Todos", max_items=10)
print(f"Earnings count: {len(earnings)}")

pos = [e for e in earnings if e["sentiment"]["label"] == "Positivo"]
mis = [e for e in earnings if e["sentiment"]["label"] in ["Misto", "Neutro"]]
neg = [e for e in earnings if e["sentiment"]["label"] == "Negativo"]

print(f"Positivos: {len(pos)} | Mistos: {len(mis)} | Negativos: {len(neg)}")
