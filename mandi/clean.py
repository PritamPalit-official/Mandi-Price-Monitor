import pandas as pd

from mandi import config

COLS = ["report_date", "state_name", "district_name", "market_code", "market_center",
        "latitude", "longitude", "commodity_type", "commodity", "variety",
        "arrivals_tonnes", "arrivals_unit", "min_price", "max_price", "modal_price", "price_unit"]


def _key(series):
    return series.astype("string").str.strip().str.lower()


def clean_chunk(raw):
    """Scope, validate and convert one chunk of the raw CSV.

    Returns (clean, counts). `counts` has one row per (reason, commodity) for in-scope rows,
    with reason 'ok' for the rows that were kept. That table feeds the data-quality page.
    """
    df = raw.reindex(columns=COLS).copy()
    df["commodity_key"] = _key(df["commodity"])
    if config.COMMODITIES:
        df = df[df["commodity_key"].isin([c.lower() for c in config.COMMODITIES])]
    if config.STATES:
        df = df[_key(df["state_name"]).isin([s.lower() for s in config.STATES])]
    if df.empty:
        return df.iloc[0:0], pd.DataFrame(columns=["reason", "commodity", "n"])

    df["date"] = pd.to_datetime(df["report_date"], errors="coerce")
    for col in ["arrivals_tonnes", "min_price", "max_price", "modal_price"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    factor = _key(df["arrivals_unit"]).map(config.ARRIVALS_TO_TONNES).astype("float64")
    has_arrivals = df["arrivals_tonnes"].notna()

    tol = 0.01
    bad_range = (df["min_price"].notna() & df["max_price"].notna() &
                 ((df["min_price"] > df["max_price"] * (1 + tol)) |
                  (df["modal_price"] < df["min_price"] * (1 - tol)) |
                  (df["modal_price"] > df["max_price"] * (1 + tol))))
    checks = [                                    # first failing rule wins
        ("bad_date", df["date"].isna()),
        ("missing_key", df["market_code"].isna() | df["commodity_key"].isna()),
        ("bad_price_unit", ~_key(df["price_unit"]).isin(config.PRICE_UNITS_OK).fillna(False)),
        ("bad_price", df["modal_price"].isna() | (df["modal_price"] <= 0) |
         (df["modal_price"] > config.MAX_PRICE)),
        ("bad_range", bad_range),
        ("bad_arrival_unit", has_arrivals & factor.isna()),
    ]
    reason = pd.Series("ok", index=df.index)
    for name, mask in checks:
        reason = reason.mask((reason == "ok") & mask.fillna(True), name)

    counts = (pd.DataFrame({"reason": reason, "commodity": df["commodity_key"]})
              .groupby(["reason", "commodity"], as_index=False).size().rename(columns={"size": "n"}))

    ok = df[reason == "ok"].copy()
    ok["arrivals_t"] = ok["arrivals_tonnes"] * factor[ok.index]
    ok["market_code"] = ok["market_code"].astype("string").str.strip()
    ok["state"] = ok["state_name"].astype("string").str.strip().str.title()
    ok["district"] = ok["district_name"].astype("string").str.strip().str.title()
    ok["market"] = ok["market_center"].astype("string").str.strip().str.title()
    ok["commodity"] = ok["commodity_key"].astype("string").str.title()
    keep = ["date", "state", "district", "market_code", "market", "latitude", "longitude",
            "commodity_type", "commodity", "variety", "arrivals_t", "min_price", "max_price",
            "modal_price"]
    return ok[keep], counts
