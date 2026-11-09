"""Synthetic raw data shaped like the AGMARKNET CSV, with known quirks and a planted spike."""
import numpy as np
import pandas as pd

STATES = {"Maharashtra": ["M1", "M2", "M3"], "Karnataka": ["K1", "K2", "K3"], "Gujarat": ["G1", "G2", "G3"]}
SPIKE = (pd.Timestamp("2025-02-03"), pd.Timestamp("2025-03-16"))    # onion: price up, arrivals down


def make_raw(start="2023-01-01", end="2025-03-31", seed=0, dirty=True):
    rng = np.random.default_rng(seed)
    rows = []
    for date in pd.date_range(start, end, freq="D"):
        season = 1 + 0.3 * np.sin(2 * np.pi * date.dayofyear / 365)
        for state, markets in STATES.items():
            for mi, market in enumerate(markets):
                for commodity, base in [("Onion", 1500.0), ("Tomato", 2000.0)]:
                    if rng.random() < 0.10:
                        continue                                    # market did not report
                    price = base * season * (1 + 0.04 * (mi - 1)) * (1 + rng.normal(0, 0.01))
                    arrivals = float(rng.uniform(50, 200))
                    if commodity == "Onion" and SPIKE[0] <= date <= SPIKE[1]:
                        price, arrivals = price * 1.6, arrivals * 0.4
                    varieties = ["Red", "Local"] if commodity == "Onion" else ["Hybrid"]
                    for v in varieties:
                        rows.append({
                            "report_date": date.strftime("%Y-%m-%d"), "state_name": state.upper(),
                            "district_name": "D1", "market_code": market, "market_center": market + " Mandi",
                            "latitude": 18.5, "longitude": 73.8, "commodity_type": "Vegetables",
                            "commodity": commodity, "variety": v, "arrivals_tonnes": arrivals / len(varieties),
                            "arrivals_unit": "Tonnes", "min_price": price * 0.9, "max_price": price * 1.1,
                            "modal_price": price, "price_unit": "Rs/Quintal"})
    df = pd.DataFrame(rows)
    if dirty:
        df.loc[df.sample(30, random_state=1).index, "price_unit"] = "Rs/Piece"
        df.loc[df.sample(20, random_state=2).index, "modal_price"] = 0
        df.loc[df.sample(20, random_state=3).index, "report_date"] = "not a date"
    return df
