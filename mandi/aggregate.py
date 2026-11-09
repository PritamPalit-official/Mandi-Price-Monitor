import numpy as np
import pandas as pd

from mandi import config

KEYS = ["date", "market_code", "commodity"]
EPOCH = pd.Timestamp("2000-01-03")          # a Monday, so week_num buckets are Monday-start


def partial_market_day(clean):
    """Chunk-safe partial sums per (date, market, commodity). Combine many with combine_partials."""
    d = clean.copy()
    arrivals = d["arrivals_t"].fillna(0.0).clip(lower=0.0)
    d["arr"] = arrivals
    d["pxa"] = d["modal_price"] * arrivals
    out = d.groupby(KEYS, as_index=False).agg(
        sum_pxa=("pxa", "sum"),
        sum_arr=("arr", "sum"),
        sum_modal=("modal_price", "sum"),
        n_rows=("modal_price", "size"),
        min_price=("min_price", "min"),
        max_price=("max_price", "max"),
        state=("state", "first"), district=("district", "first"), market=("market", "first"),
        latitude=("latitude", "first"), longitude=("longitude", "first"),
        commodity_type=("commodity_type", "first"))
    return out


def combine_partials(parts):
    p = pd.concat(parts, ignore_index=True)
    return p.groupby(KEYS, as_index=False).agg(
        sum_pxa=("sum_pxa", "sum"), sum_arr=("sum_arr", "sum"), sum_modal=("sum_modal", "sum"),
        n_rows=("n_rows", "sum"), min_price=("min_price", "min"), max_price=("max_price", "max"),
        state=("state", "first"), district=("district", "first"), market=("market", "first"),
        latitude=("latitude", "first"), longitude=("longitude", "first"),
        commodity_type=("commodity_type", "first"))


def finalize_market_day(p):
    """One row per market per day. Price is arrivals-weighted when arrivals are known, else a plain mean."""
    md = p.copy()
    weighted = md["sum_arr"] > 0
    weighted_price = md["sum_pxa"] / md["sum_arr"].where(weighted, 1)
    md["price"] = np.where(weighted, weighted_price, md["sum_modal"] / md["n_rows"])
    md["arrivals_known"] = weighted
    md["arrivals_t"] = md["sum_arr"]
    return md.drop(columns=["sum_pxa", "sum_arr", "sum_modal"])


def flag_suspects(md):
    """Mark market-days far from the same day's median across markets (needs MIN_MARKETS that day)."""
    g = md.groupby(["date", "commodity"])["price"]
    day_median = g.transform("median")
    n_day = g.transform("size")
    ratio = md["price"] / day_median
    md = md.copy()
    far = (ratio < config.OUTLIER_LOW) | (ratio > config.OUTLIER_HIGH)
    md["suspect"] = (n_day >= config.MIN_MARKETS) & far
    return md


def add_calendar(df, col="date"):
    df = df.copy()
    d = pd.to_datetime(df[col])
    df["day_num"] = (d - EPOCH).dt.days
    df["week_num"] = df["day_num"] // 7
    df["week_start"] = EPOCH + pd.to_timedelta(df["week_num"] * 7, unit="D")
    iso = d.dt.isocalendar()
    df["iso_year"] = iso["year"].astype("int64")
    df["iso_week"] = iso["week"].astype("int64")
    df["year"] = d.dt.year
    df["month_num"] = d.dt.month
    return df


def build_tables(md):
    """From finalized, flagged market-days to the model tables."""
    good = md[~md["suspect"]]
    daily = good.groupby(["date", "commodity"]).agg(
        benchmark_price=("price", "median"),
        price_p25=("price", lambda s: s.quantile(0.25)),
        price_p75=("price", lambda s: s.quantile(0.75)),
        n_markets=("market_code", "nunique"),
        arrivals_t=("arrivals_t", "sum")).reset_index()
    daily["low_coverage"] = daily["n_markets"] < config.MIN_MARKETS
    benchmark_day = add_calendar(daily)

    g = add_calendar(good)
    state_week = g.groupby(["week_num", "week_start", "state", "commodity"]).agg(
        price=("price", "median"), arrivals_t=("arrivals_t", "sum"),
        n_markets=("market_code", "nunique")).reset_index()
    market_week = g.groupby(["week_num", "week_start", "state", "market_code", "market", "commodity"]).agg(
        price=("price", "mean"), arrivals_t=("arrivals_t", "sum"),
        days_reported=("date", "nunique")).reset_index()
    return {"benchmark_day": benchmark_day, "state_week": state_week, "market_week": market_week}


def build_dim_date(start, end):
    dates = pd.date_range(start, end, freq="D")
    df = pd.DataFrame({"date": dates})
    df = add_calendar(df)
    df["month_name"] = df["date"].dt.strftime("%b")
    df["month_start"] = df["date"].dt.to_period("M").dt.to_timestamp()
    fy_start = np.where(df["month_num"] >= 4, df["year"], df["year"] - 1)
    df["fiscal_year"] = ["FY%d-%02d" % (y, (y + 1) % 100) for y in fy_start]
    return df


def build_dim_commodity(md):
    return (md.groupby("commodity", as_index=False)["commodity_type"].first())


def build_dim_market(md):
    return (md.groupby("market_code", as_index=False)
            .agg(market=("market", "first"), district=("district", "first"), state=("state", "first"),
                 latitude=("latitude", "first"), longitude=("longitude", "first")))


def build_dim_week(dim_date):
    return dim_date.groupby("week_num", as_index=False).agg(
        week_start=("week_start", "first"), iso_year=("iso_year", "first"), iso_week=("iso_week", "first"))


def build_dim_state(md):
    return pd.DataFrame({"state": sorted(md["state"].dropna().unique())})
