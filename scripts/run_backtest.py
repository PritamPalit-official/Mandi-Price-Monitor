"""Run the buy-timing backtest. Run: python -m scripts.run_backtest"""
import pandas as pd

from mandi import engine
from mandi.backtest import run_backtest, summarise

bench = engine.query("SELECT date, commodity, benchmark_price, low_coverage FROM mandi.benchmark_day")
monthly = pd.concat([run_backtest(bench, c) for c in sorted(bench["commodity"].unique())])
monthly.to_csv("data/export/backtest_monthly.csv", index=False)
for c, part in monthly.groupby("commodity"):
    print(c, summarise(part))
