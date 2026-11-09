"""Profile the big raw CSV in chunks. Run: python -m scripts.profile_csv  (takes several minutes)"""
import pandas as pd

from mandi import config

rows, dates = 0, []
commodity, state, price_unit, arrivals_unit = (pd.Series(dtype="int64") for _ in range(4))
nulls = pd.Series(dtype="int64")
for chunk in pd.read_csv(config.RAW_CSV, chunksize=config.CHUNK_ROWS, low_memory=False):
    rows += len(chunk)
    d = pd.to_datetime(chunk["report_date"], errors="coerce")
    dates += [d.min(), d.max()]
    commodity = commodity.add(chunk["commodity"].astype("string").str.strip().value_counts(), fill_value=0)
    state = state.add(chunk["state_name"].astype("string").str.strip().value_counts(), fill_value=0)
    price_unit = price_unit.add(chunk["price_unit"].astype("string").value_counts(dropna=False), fill_value=0)
    arrivals_unit = arrivals_unit.add(
        chunk["arrivals_unit"].astype("string").value_counts(dropna=False), fill_value=0)
    nulls = nulls.add(chunk.isna().sum(), fill_value=0)

print("rows:", rows)
valid = [x for x in dates if pd.notna(x)]
print("date range:", min(valid).date(), "to", max(valid).date())
print("\nTop 40 commodities by rows:\n", commodity.sort_values(ascending=False).head(40).astype(int))
print("\nTop 15 states by rows:\n", state.sort_values(ascending=False).head(15).astype(int))
print("\nprice_unit values:\n", price_unit.astype(int))
print("\narrivals_unit values:\n", arrivals_unit.astype(int))
print("\nnull counts:\n", nulls.astype(int))
