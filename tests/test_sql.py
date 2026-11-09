"""Runs sql/views.sql on DuckDB and checks the numbers against plain pandas."""
import numpy as np
import pandas as pd
import pytest

from mandi import config, engine
from mandi.aggregate import (build_dim_date, build_tables, combine_partials, finalize_market_day,
                             flag_suspects, partial_market_day)
from mandi.clean import clean_chunk
from tests.synth import make_raw


@pytest.fixture(scope="module")
def db(tmp_path_factory):
    mp = pytest.MonkeyPatch()
    mp.setattr(config, "ENGINE", "duckdb")
    mp.setattr(config, "DUCKDB_PATH", str(tmp_path_factory.mktemp("d") / "t.duckdb"))
    mp.setattr(config, "COMMODITIES", ["onion", "tomato"])
    mp.setattr(config, "STATES", [])
    mp.setattr(config, "MIN_MARKETS", 3)
    clean, _ = clean_chunk(make_raw())
    md = flag_suspects(finalize_market_day(combine_partials([partial_market_day(clean)])))
    tables = build_tables(md)
    tables["dim_date"] = build_dim_date(md["date"].min(), md["date"].max())
    for name, df in tables.items():
        engine.load(df, name)
    engine.run_sql_file("sql/views.sql")
    yield tables
    mp.undo()


def weekly(commodity):
    return engine.query(f"SELECT * FROM mandi.v_benchmark_weekly WHERE commodity = '{commodity}' ORDER BY week_num")


def trend(view, commodity):
    return engine.query(f"SELECT * FROM mandi.{view} WHERE commodity = '{commodity}' ORDER BY week_num")


def test_weekly_benchmark_skips_low_coverage_days(db):
    w = weekly("Onion")
    assert (w["days_reported"] <= 7).all() and w["price"].notna().all()


def test_ma4_prior52w_and_yoy_match_pandas(db):
    w, t = weekly("Onion"), trend("v_weekly_trend", "Onion")
    price = w.set_index("week_num")["price"]
    for _, r in t.iterrows():
        wn = r["week_num"]
        assert abs(r["price_ma4"] - price[(price.index >= wn - 3) & (price.index <= wn)].mean()) < 1e-6
        prior = price[(price.index >= wn - 52) & (price.index <= wn - 1)]
        if len(prior):
            assert abs(r["price_avg_prior52w"] - prior.mean()) < 1e-6 and r["weeks_prior52w"] == len(prior)
        else:
            assert pd.isna(r["price_avg_prior52w"])
        if wn - 52 in price.index:
            assert abs(r["yoy_pct"] - (price[wn] - price[wn - 52]) / price[wn - 52] * 100) < 1e-6
        else:
            assert pd.isna(r["yoy_pct"])


def test_cv_matches_pandas(db):
    w, t = weekly("Tomato"), trend("v_weekly_trend", "Tomato")
    price = w.set_index("week_num")["price"]
    r = t.iloc[-1]
    win = price[(price.index >= r["week_num"] - 25) & (price.index <= r["week_num"])]
    assert abs(r["cv_26w"] - win.std(ddof=0) / win.mean()) < 1e-9


def test_spike_flag_fires_only_in_the_planted_spike(db):
    onion = trend("v_spike_flags", "Onion")
    spike_weeks = onion[(onion["week_start"] >= pd.Timestamp("2025-02-10")) &
                        (onion["week_start"] <= pd.Timestamp("2025-03-10"))]
    assert len(spike_weeks) >= 4 and (spike_weeks["is_spike"] == 1).all()
    assert onion[~onion["week_num"].isin(spike_weeks["week_num"])]["is_spike"].sum() <= 1   # edge weeks
    assert trend("v_spike_flags", "Tomato")["is_spike"].sum() == 0


def test_seasonality_uses_only_full_years_and_averages_100(db):
    s = engine.query("SELECT * FROM mandi.v_seasonality")
    assert set(s["year"]) == {2023, 2024}                      # 2025 has 3 months only
    assert np.allclose(s.groupby(["commodity", "year"])["price_index"].mean(), 100.0)
    idx = engine.query("SELECT * FROM mandi.v_seasonal_index")
    assert (idx["n_years"] == 2).all() and idx["month_num"].nunique() == 12


def test_state_spread_formula(db):
    s = engine.query("SELECT * FROM mandi.v_state_spread WHERE commodity = 'Onion' LIMIT 50")
    expected = (s["state_price"] - s["national_price"]) / s["national_price"] * 100
    assert np.allclose(s["spread_pct"], expected)


def test_data_quality_counts_days(db):
    q = engine.query("SELECT SUM(days_with_data) AS d FROM mandi.v_data_quality")["d"].iloc[0]
    assert q == len(db["benchmark_day"])
