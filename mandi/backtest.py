import pandas as pd


def trailing_median(prices, window="364D", min_obs=60):
    """Median of the previous `window` of days, NOT including the current day (no look-ahead)."""
    return prices.rolling(window, closed="left", min_periods=min_obs).median()


def run_backtest(benchmark_day, commodity, window="364D", min_obs=60):
    """Compare two ways to buy ONE unit per month at the national benchmark price.

    baseline: buy on the first reported day of the month.
    rule:     buy on the first day the price is at or below its trailing median; if that never
              happens in the month, buy on the last reported day.
    Returns one row per month. Positive saving_pct means the rule was cheaper.
    """
    d = benchmark_day[(benchmark_day["commodity"] == commodity) & (~benchmark_day["low_coverage"])]
    s = d.set_index(pd.to_datetime(d["date"]))["benchmark_price"].sort_index()
    trail = trailing_median(s, window, min_obs)
    rows = []
    for period, prices in s.groupby(s.index.to_period("M")):
        t = trail.loc[prices.index]
        if t.isna().all():
            continue                                     # not enough history yet
        baseline_price = prices.iloc[0]
        cheap = prices[prices <= t]
        pick = cheap if len(cheap) else prices.iloc[[-1]]       # first cheap day, else the last day
        rule_day, rule_price = pick.index[0], pick.iloc[0]
        rows.append({"commodity": commodity, "month": str(period), "baseline_price": baseline_price,
                     "rule_price": rule_price, "rule_day": rule_day.date(),
                     "saving_pct": (baseline_price - rule_price) / baseline_price * 100})
    return pd.DataFrame(rows)


def summarise(monthly):
    if monthly.empty:
        return {}
    return {"months": len(monthly),
            "avg_baseline": round(float(monthly["baseline_price"].mean()), 1),
            "avg_rule": round(float(monthly["rule_price"].mean()), 1),
            "avg_saving_pct": round(float(monthly["saving_pct"].mean()), 2),
            "months_rule_cheaper": int((monthly["saving_pct"] > 0).sum()),
            "months_rule_dearer": int((monthly["saving_pct"] < 0).sum()),
            "worst_month_pct": round(float(monthly["saving_pct"].min()), 2)}
