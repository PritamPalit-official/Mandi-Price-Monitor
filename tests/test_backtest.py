import pandas as pd

from mandi.backtest import run_backtest, summarise, trailing_median


def series(values_by_month):
    """400 days of price 100 from 2023-01-01, then the given days overwritten."""
    dates = pd.date_range("2023-01-01", "2024-03-31", freq="D")
    price = pd.Series(100.0, index=dates)
    for start, vals in values_by_month.items():
        for i, v in enumerate(vals):
            price[pd.Timestamp(start) + pd.Timedelta(days=i)] = v
    return pd.DataFrame({"date": dates, "commodity": "Onion", "benchmark_price": price.values,
                         "low_coverage": False})


def test_trailing_median_excludes_today():
    s = pd.Series([1.0] * 100 + [50.0], index=pd.date_range("2023-01-01", periods=101))
    assert trailing_median(s).iloc[-1] == 1.0              # the 50 is not in its own window


def test_rule_picks_first_cheap_day_and_falls_back_to_last_day():
    bench = series({"2024-01-01": [120, 110, 90, 95], "2024-02-01": [130] * 29})
    m = run_backtest(bench, "Onion").set_index("month")
    jan, feb = m.loc["2024-01"], m.loc["2024-02"]
    assert jan["baseline_price"] == 120 and jan["rule_price"] == 90 and jan["saving_pct"] == 25.0
    assert feb["baseline_price"] == 130 and feb["rule_price"] == 130      # never cheap: last day, same price here


def test_months_without_history_are_skipped_and_summary_counts():
    m = run_backtest(series({}), "Onion")
    assert m["month"].min() >= "2023-03"                   # first ~60 days have no trailing median
    s = summarise(m)
    assert s["months"] == len(m) and s["months_rule_cheaper"] + s["months_rule_dearer"] <= s["months"]
