"""Generate realistic multi-year AGMARKNET mandi data for Onion, Tomato, and Potato (2020 - 2025)."""
import os
import numpy as np
import pandas as pd

np.random.seed(42)

MANDIS = {
    "MAHARASHTRA": [
        ("M1", "Lasalgaon Mandi", "Nashik", 20.14, 74.22),
        ("M2", "Pimpalgaon Mandi", "Nashik", 20.17, 73.98),
        ("M3", "Pune Mandi", "Pune", 18.52, 73.85),
        ("M4", "Nashik Mandi", "Nashik", 19.99, 73.78),
        ("M5", "Ahmednagar Mandi", "Ahmednagar", 19.09, 74.74),
    ],
    "KARNATAKA": [
        ("K1", "Bangalore Mandi", "Bangalore", 12.97, 77.59),
        ("K2", "Kolar Mandi", "Kolar", 13.13, 78.13),
        ("K3", "Hubli Mandi", "Dharwad", 15.36, 75.12),
        ("K4", "Belgaum Mandi", "Belgaum", 15.84, 74.49),
    ],
    "GUJARAT": [
        ("G1", "Mahuva Mandi", "Bhavnagar", 21.09, 71.76),
        ("G2", "Gondal Mandi", "Rajkot", 21.96, 70.79),
        ("G3", "Ahmedabad Mandi", "Ahmedabad", 23.02, 72.57),
    ],
    "UTTAR PRADESH": [
        ("U1", "Agra Mandi", "Agra", 27.17, 78.00),
        ("U2", "Farrukhabad Mandi", "Farrukhabad", 27.38, 79.58),
        ("U3", "Kanpur Mandi", "Kanpur", 26.44, 80.33),
    ],
    "MADHYA PRADESH": [
        ("P1", "Indore Mandi", "Indore", 22.71, 75.85),
        ("P2", "Neemuch Mandi", "Neemuch", 24.47, 74.87),
        ("P3", "Ujjain Mandi", "Ujjain", 23.17, 75.78),
    ],
}

COMMODITY_CONFIG = {
    "Onion": {
        "base_price": 1600.0,
        "base_arrivals": 120.0,
        "varieties": ["Red", "Local", "Nasik"],
        "season_phase": 0.4,
    },
    "Tomato": {
        "base_price": 2200.0,
        "base_arrivals": 90.0,
        "varieties": ["Hybrid", "Local", "Deshi"],
        "season_phase": 1.2,
    },
    "Potato": {
        "base_price": 1200.0,
        "base_arrivals": 160.0,
        "varieties": ["Jyoti", "Chandramukhi", "Local"],
        "season_phase": 2.0,
    },
}

# Historical spikes
# 1. Tomato surge in July - August 2023
TOMATO_SPIKE = (pd.Timestamp("2023-06-25"), pd.Timestamp("2023-08-20"))
# 2. Onion spike in late 2023 (Oct - Dec 2023)
ONION_SPIKE_1 = (pd.Timestamp("2023-10-15"), pd.Timestamp("2023-12-10"))
# 3. Onion spike in early 2025 (Feb - Mar 2025)
ONION_SPIKE_2 = (pd.Timestamp("2025-02-01"), pd.Timestamp("2025-03-25"))

def generate():
    dates = pd.date_range("2020-01-01", "2025-10-31", freq="D")
    rows = []
    print(f"Generating realistic mandi dataset across {len(dates):,} days...")

    for d in dates:
        d_str = d.strftime("%Y-%m-%d")
        d_day_of_year = d.day_of_year

        for state, mandis in MANDIS.items():
            for m_code, m_center, dist, lat, lon in mandis:
                # 8% random non-reporting rate (APMC mandi closure/holiday)
                if np.random.rand() < 0.08:
                    continue

                for comm, cfg in COMMODITY_CONFIG.items():
                    # Seasonal oscillation
                    season = 1.0 + 0.35 * np.sin(2 * np.pi * (d_day_of_year / 365.25 + cfg["season_phase"]))
                    
                    price = cfg["base_price"] * season * (1.0 + np.random.normal(0, 0.05))
                    arrivals = cfg["base_arrivals"] * (1.0 / season) * (1.0 + np.random.normal(0, 0.08))
                    
                    # Inter-state spread variation
                    if state == "MAHARASHTRA" and comm == "Onion":
                        price *= 0.92  # Primary producing state cheaper
                    elif state == "UTTAR PRADESH" and comm == "Potato":
                        price *= 0.88  # Potato heartland cheaper
                    elif state == "KARNATAKA" and comm == "Tomato":
                        price *= 0.94  # Kolar tomato hub

                    # Apply planted realistic spikes
                    if comm == "Tomato" and (TOMATO_SPIKE[0] <= d <= TOMATO_SPIKE[1]):
                        price *= 2.8
                        arrivals *= 0.35
                    elif comm == "Onion" and (ONION_SPIKE_1[0] <= d <= ONION_SPIKE_1[1]):
                        price *= 2.1
                        arrivals *= 0.45
                    elif comm == "Onion" and (ONION_SPIKE_2[0] <= d <= ONION_SPIKE_2[1]):
                        price *= 1.85
                        arrivals *= 0.50

                    varieties = cfg["varieties"]
                    # 1 or 2 varieties reported per day
                    active_vars = np.random.choice(varieties, size=np.random.choice([1, 2]), replace=False)
                    
                    for v in active_vars:
                        var_arrivals = (arrivals / len(active_vars)) * np.random.uniform(0.8, 1.2)
                        var_price = price * (1.0 + np.random.normal(0, 0.02))
                        
                        min_p = round(var_price * np.random.uniform(0.88, 0.96), 2)
                        max_p = round(var_price * np.random.uniform(1.04, 1.14), 2)
                        modal_p = round(var_price, 2)
                        
                        rows.append({
                            "report_date": d_str,
                            "state_name": state,
                            "district_name": dist,
                            "market_code": m_code,
                            "market_center": m_center,
                            "latitude": lat,
                            "longitude": lon,
                            "commodity_type": "Vegetables",
                            "commodity": comm,
                            "variety": v,
                            "arrivals_tonnes": round(var_arrivals, 2),
                            "arrivals_unit": "Tonnes" if np.random.rand() > 0.15 else "Quintal",
                            "min_price": min_p,
                            "max_price": max_p,
                            "modal_price": modal_p,
                            "price_unit": "Rs/Quintal"
                        })

    df = pd.DataFrame(rows)
    print(f"Base records generated: {len(df):,}")

    # Introduce realistic dirty rows for data quality checks
    n = len(df)
    # 0.4% bad price units (e.g. Rs/Piece or Bags)
    idx_bad_unit = np.random.choice(n, size=int(n * 0.004), replace=False)
    df.loc[idx_bad_unit, "price_unit"] = "Rs/Piece"

    # 0.2% bad price (0 or null)
    idx_bad_p = np.random.choice(n, size=int(n * 0.002), replace=False)
    df.loc[idx_bad_p, "modal_price"] = 0

    # 0.2% inverted range (min > max)
    idx_bad_rng = np.random.choice(n, size=int(n * 0.002), replace=False)
    df.loc[idx_bad_rng, "min_price"] = df.loc[idx_bad_rng, "max_price"] * 1.5

    # 0.1% unparseable dates
    idx_bad_d = np.random.choice(n, size=int(n * 0.001), replace=False)
    df.loc[idx_bad_d, "report_date"] = "INVALID"

    # 0.3% unknown arrival units
    idx_bad_arr = np.random.choice(n, size=int(n * 0.003), replace=False)
    df.loc[idx_bad_arr, "arrivals_unit"] = "Baskets"

    os.makedirs("data/raw", exist_ok=True)
    out_path = "data/raw/agmarknet.csv"
    df.to_csv(out_path, index=False)
    print(f"Saved {len(df):,} records to {out_path} ({os.path.getsize(out_path) / (1024*1024):.1f} MB)")

if __name__ == "__main__":
    generate()
