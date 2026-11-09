"""Slow step, run once: stream the raw CSV, clean and aggregate to one row per market per day.
Run: python -m scripts.build_market_day"""
import pandas as pd

from mandi import config
from mandi.aggregate import combine_partials, finalize_market_day, partial_market_day
from mandi.clean import clean_chunk

parts, counts, seen = [], [], 0
for chunk in pd.read_csv(config.RAW_CSV, chunksize=config.CHUNK_ROWS, low_memory=False):
    seen += len(chunk)
    clean, c = clean_chunk(chunk)
    counts.append(c)
    if len(clean):
        parts.append(partial_market_day(clean))
    print(f"rows read: {seen:,}", end="\r")

market_day = finalize_market_day(combine_partials(parts))
reject_counts = pd.concat(counts).groupby(["reason", "commodity"], as_index=False)["n"].sum()
market_day.to_parquet("data/interim/market_day.parquet", index=False)
reject_counts.to_csv("data/interim/reject_counts.csv", index=False)
print(f"\nmarket-days: {len(market_day):,}")
print(reject_counts.pivot_table(index="commodity", columns="reason", values="n", fill_value=0))
