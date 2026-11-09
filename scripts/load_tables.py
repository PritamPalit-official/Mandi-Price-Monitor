"""Fast step: flag suspects, build the model tables and load them. Run: python -m scripts.load_tables"""
import pandas as pd

from mandi import engine
from mandi.aggregate import (build_dim_commodity, build_dim_date, build_dim_market, build_dim_state,
                             build_dim_week, build_tables, flag_suspects)

md = flag_suspects(pd.read_parquet("data/interim/market_day.parquet"))
reject_counts = pd.read_csv("data/interim/reject_counts.csv")
suspects = md[md["suspect"]].groupby("commodity").size().rename("n").reset_index()
suspects["reason"] = "suspect_vs_same_day_median"
reject_counts = pd.concat([reject_counts, suspects[["reason", "commodity", "n"]]], ignore_index=True)
reject_counts["commodity"] = reject_counts["commodity"].str.title()

tables = build_tables(md)
tables["dim_date"] = build_dim_date(md["date"].min(), md["date"].max())
tables["dim_week"] = build_dim_week(tables["dim_date"])
tables["dim_state"] = build_dim_state(md)
tables["dim_commodity"] = build_dim_commodity(md)
tables["dim_market"] = build_dim_market(md)
tables["reject_counts"] = reject_counts
for name, df in tables.items():
    engine.load(df, name)
    print(f"loaded {name}: {len(df):,} rows")
