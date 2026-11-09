import numpy as np
import pandas as pd

from mandi import config
from mandi.aggregate import (add_calendar, build_dim_date, build_dim_state, build_dim_week,
                             build_tables, combine_partials,
                             finalize_market_day, flag_suspects, partial_market_day)
from mandi.clean import clean_chunk
from tests.synth import make_raw


def prep(monkeypatch, start="2024-01-01", end="2024-02-15"):
    monkeypatch.setattr(config, "COMMODITIES", ["onion", "tomato"])
    monkeypatch.setattr(config, "STATES", [])
    monkeypatch.setattr(config, "MIN_MARKETS", 3)
    clean, _ = clean_chunk(make_raw(start, end, dirty=False))
    return clean


def test_weighted_price_and_unweighted_fallback():
    base = {"date": pd.Timestamp("2024-01-01"), "market_code": "M1", "commodity": "Onion", "state": "S",
            "district": "D", "market": "M", "latitude": 1, "longitude": 2, "commodity_type": "V",
            "min_price": 1, "max_price": 2}
    clean = pd.DataFrame([dict(base, arrivals_t=10.0, modal_price=1000.0),
                          dict(base, arrivals_t=30.0, modal_price=2000.0)])
    md = finalize_market_day(partial_market_day(clean))
    assert md["price"].iloc[0] == (10 * 1000 + 30 * 2000) / 40 and md["arrivals_known"].iloc[0]
    clean["arrivals_t"] = np.nan
    md = finalize_market_day(partial_market_day(clean))
    assert md["price"].iloc[0] == 1500.0 and not md["arrivals_known"].iloc[0]


def test_chunked_equals_one_shot(monkeypatch):
    clean = prep(monkeypatch)
    one = finalize_market_day(partial_market_day(clean)).sort_values(["date", "market_code", "commodity"])
    parts = [partial_market_day(clean.iloc[idx]) for idx in np.array_split(np.arange(len(clean)), 7)]
    many = finalize_market_day(combine_partials(parts)).sort_values(["date", "market_code", "commodity"])
    pd.testing.assert_frame_equal(one.reset_index(drop=True), many.reset_index(drop=True), check_dtype=False)


def test_suspect_flag_catches_lone_outlier_but_not_a_market_wide_spike(monkeypatch):
    base = finalize_market_day(partial_market_day(prep(monkeypatch)))
    md = base.copy()
    day = md[(md["commodity"] == "Tomato") & (md["date"] == md["date"].iloc[0])].index
    md.loc[day[0], "price"] = md.loc[day[0], "price"] * 6
    flagged = flag_suspects(md)
    assert flagged.loc[day[0], "suspect"]
    wide = base.copy()
    wide["price"] = wide["price"] * 2.5                    # every market doubles: a real spike
    assert not flag_suspects(wide)["suspect"].any()


def test_calendar_weeks_start_on_monday():
    df = add_calendar(pd.DataFrame({"date": pd.to_datetime(["2024-01-01", "2024-01-07", "2024-01-08"])}))
    assert list(df["week_start"].dt.dayofweek) == [0, 0, 0]
    assert df["week_num"].iloc[1] == df["week_num"].iloc[0] and df["week_num"].iloc[2] == df["week_num"].iloc[0] + 1


def test_fiscal_year_labels():
    dd = build_dim_date("2024-03-30", "2024-04-02").set_index("date")["fiscal_year"]
    assert dd[pd.Timestamp("2024-03-31")] == "FY2023-24" and dd[pd.Timestamp("2024-04-01")] == "FY2024-25"


def test_benchmark_is_median_and_flags_low_coverage(monkeypatch):
    md = flag_suspects(finalize_market_day(partial_market_day(prep(monkeypatch))))
    t = build_tables(md)["benchmark_day"]
    d, c = t.iloc[0]["date"], t.iloc[0]["commodity"]
    expected = md[(md["date"] == d) & (md["commodity"] == c) & ~md["suspect"]]["price"].median()
    assert abs(t.iloc[0]["benchmark_price"] - expected) < 1e-9
    monkeypatch.setattr(config, "MIN_MARKETS", 99)
    assert build_tables(md)["benchmark_day"]["low_coverage"].all()


def test_dim_week_is_one_row_per_week_and_dim_state_is_unique(monkeypatch):
    dd = build_dim_date("2024-01-01", "2024-03-31")
    wk = build_dim_week(dd)
    assert wk["week_num"].is_unique and (wk["week_start"].dt.dayofweek == 0).all()
    md = finalize_market_day(partial_market_day(prep(monkeypatch)))
    assert build_dim_state(md)["state"].tolist() == ["Gujarat", "Karnataka", "Maharashtra"]
