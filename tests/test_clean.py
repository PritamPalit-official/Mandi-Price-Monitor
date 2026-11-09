import pandas as pd

from mandi import config
from mandi.clean import clean_chunk


def row(**over):
    base = {"report_date": "2024-01-01", "state_name": "MAHARASHTRA", "district_name": "pune",
            "market_code": "M1", "market_center": "pune", "latitude": 1, "longitude": 2,
            "commodity_type": "Vegetables", "commodity": "Onion", "variety": "Red",
            "arrivals_tonnes": 10.0, "arrivals_unit": "Tonnes", "min_price": 900, "max_price": 1100,
            "modal_price": 1000, "price_unit": "Rs/Quintal"}
    base.update(over)
    return base


def run(rows, monkeypatch, commodities=("onion",)):
    monkeypatch.setattr(config, "COMMODITIES", list(commodities))
    monkeypatch.setattr(config, "STATES", [])
    return clean_chunk(pd.DataFrame(rows))


def reasons(counts):
    return dict(zip(counts["reason"], counts["n"]))


def test_scope_and_ok_rows(monkeypatch):
    clean, counts = run([row(), row(commodity="Tomato")], monkeypatch)
    assert len(clean) == 1 and reasons(counts) == {"ok": 1}      # tomato is out of scope, not a reject
    assert clean.iloc[0]["state"] == "Maharashtra" and clean.iloc[0]["commodity"] == "Onion"


def test_each_reject_reason(monkeypatch):
    rows = [row(price_unit="Rs/Piece"), row(modal_price=0), row(modal_price=1e7),
            row(min_price=1500, max_price=1100), row(report_date="garbage"), row(market_code=None),
            row(arrivals_unit="Bags")]
    clean, counts = run(rows, monkeypatch)
    assert clean.empty
    assert reasons(counts) == {"bad_price_unit": 1, "bad_price": 2, "bad_range": 1, "bad_date": 1,
                               "missing_key": 1, "bad_arrival_unit": 1}


def test_arrivals_converted_to_tonnes(monkeypatch):
    clean, _ = run([row(arrivals_tonnes=50.0, arrivals_unit="Quintal"), row(arrivals_tonnes=None)], monkeypatch)
    assert clean["arrivals_t"].iloc[0] == 5.0
    assert pd.isna(clean["arrivals_t"].iloc[1])


def test_case_insensitive_scope_and_states(monkeypatch):
    monkeypatch.setattr(config, "COMMODITIES", ["ONION"])
    monkeypatch.setattr(config, "STATES", ["maharashtra"])
    clean, _ = clean_chunk(pd.DataFrame([row(), row(state_name="Gujarat")]))
    assert len(clean) == 1
