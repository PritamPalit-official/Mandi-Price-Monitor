from mandi import engine

df = engine.query("""
    SELECT commodity, week_num, week_start, price, price_ma4, price_last_year, yoy_pct 
    FROM mandi.v_weekly_trend 
    WHERE commodity = 'Onion' 
    ORDER BY week_num DESC 
    LIMIT 5
""")
print("--- Weekly Trend (Onion) ---")
print(df.to_string())

spikes = engine.query("""
    SELECT commodity, week_start, round(price, 1) as price, 
           round(price_avg_prior52w, 1) as prior52w_price, 
           round(price_vs_52w_pct, 1) as price_vs_52w_pct, 
           round(arrivals_vs_52w_pct, 1) as arrivals_vs_52w_pct, is_spike 
    FROM mandi.v_spike_flags 
    WHERE is_spike = 1 
    ORDER BY week_start
""")
print("\n--- Detected Price Spikes ---")
print(spikes.to_string())
