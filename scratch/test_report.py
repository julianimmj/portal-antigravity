import sys
sys.path.insert(0, '.')

from modules.market_summary import get_market_closure_report, get_earnings_analysis

report = get_market_closure_report(region="Todos")
print("Title:", report["title"])
print("Has earnings:", report["has_earnings"])
print("Positivos count:", len(report["earnings"]["positivos"]))
print("Mistos count:", len(report["earnings"]["mistos"]))
print("Negativos count:", len(report["earnings"]["negativos"]))
