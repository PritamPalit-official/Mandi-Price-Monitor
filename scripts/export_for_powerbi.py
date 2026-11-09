"""Write CSVs for Power BI. Run: python -m scripts.export_for_powerbi"""
from mandi import engine

EXPORTS = ["benchmark_day", "v_weekly_trend", "v_spike_flags", "v_state_spread", "market_week",
           "v_seasonality", "v_seasonal_index", "v_data_quality", "reject_counts",
           "dim_date", "dim_week", "dim_state", "dim_commodity", "dim_market"]
for name in EXPORTS:
    df = engine.query(f"SELECT * FROM mandi.{name}")
    df.to_csv(f"data/export/{name}.csv", index=False)
    print(f"exported {name}: {len(df):,} rows")
