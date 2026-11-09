-- Weekly national benchmark: the average of the daily benchmarks, skipping low-coverage days.
CREATE OR REPLACE VIEW mandi.v_benchmark_weekly AS
SELECT
  commodity, week_num, week_start, iso_year, iso_week,
  AVG(benchmark_price) AS price,
  SUM(arrivals_t) AS arrivals_t,
  AVG(n_markets) AS avg_markets,
  COUNT(*) AS days_reported
FROM mandi.benchmark_day
WHERE NOT low_coverage
GROUP BY commodity, week_num, week_start, iso_year, iso_week;

-- Trend measures. RANGE over week_num counts calendar weeks, so gaps do not shift the windows.
CREATE OR REPLACE VIEW mandi.v_weekly_trend AS
SELECT
  w.commodity, w.week_num, w.week_start, w.iso_year, w.iso_week,
  w.price, w.arrivals_t, w.avg_markets, w.days_reported,
  AVG(w.price) OVER (PARTITION BY w.commodity ORDER BY w.week_num
       RANGE BETWEEN 3 PRECEDING AND CURRENT ROW) AS price_ma4,
  AVG(w.price) OVER (PARTITION BY w.commodity ORDER BY w.week_num
       RANGE BETWEEN 52 PRECEDING AND 1 PRECEDING) AS price_avg_prior52w,
  AVG(w.arrivals_t) OVER (PARTITION BY w.commodity ORDER BY w.week_num
       RANGE BETWEEN 52 PRECEDING AND 1 PRECEDING) AS arrivals_avg_prior52w,
  COUNT(w.price) OVER (PARTITION BY w.commodity ORDER BY w.week_num
       RANGE BETWEEN 52 PRECEDING AND 1 PRECEDING) AS weeks_prior52w,
  STDDEV_POP(w.price) OVER (PARTITION BY w.commodity ORDER BY w.week_num
       RANGE BETWEEN 25 PRECEDING AND CURRENT ROW)
    / NULLIF(AVG(w.price) OVER (PARTITION BY w.commodity ORDER BY w.week_num
       RANGE BETWEEN 25 PRECEDING AND CURRENT ROW), 0) AS cv_26w,
  ly.price AS price_last_year,
  (w.price - ly.price) / NULLIF(ly.price, 0) * 100 AS yoy_pct
FROM mandi.v_benchmark_weekly w
LEFT JOIN mandi.v_benchmark_weekly ly
  ON ly.commodity = w.commodity AND ly.week_num = w.week_num - 52;

-- Early-warning flag: price well above its 52-week norm while arrivals are well below theirs.
CREATE OR REPLACE VIEW mandi.v_spike_flags AS
SELECT
  t.*,
  (t.price / NULLIF(t.price_avg_prior52w, 0) - 1) * 100 AS price_vs_52w_pct,
  (t.arrivals_t / NULLIF(t.arrivals_avg_prior52w, 0) - 1) * 100 AS arrivals_vs_52w_pct,
  CASE WHEN t.weeks_prior52w >= 26
        AND t.days_reported >= 3
        AND t.price > 1.2 * t.price_avg_prior52w
        AND t.arrivals_t < 0.8 * t.arrivals_avg_prior52w
       THEN 1 ELSE 0 END AS is_spike
FROM mandi.v_weekly_trend t;

-- Where to buy: each state against the national benchmark for the same week.
CREATE OR REPLACE VIEW mandi.v_state_spread AS
SELECT
  s.commodity, s.state, s.week_num, s.week_start,
  s.price AS state_price, s.arrivals_t, s.n_markets,
  w.price AS national_price,
  (s.price - w.price) / NULLIF(w.price, 0) * 100 AS spread_pct
FROM mandi.state_week s
JOIN mandi.v_benchmark_weekly w
  ON w.commodity = s.commodity AND w.week_num = s.week_num;

-- When to buy: month price as a percentage of that year's average (years with 10+ good months only).
CREATE OR REPLACE VIEW mandi.v_seasonality AS
WITH monthly AS (
  SELECT commodity, year, month_num, AVG(benchmark_price) AS month_price, COUNT(*) AS days
  FROM mandi.benchmark_day
  WHERE NOT low_coverage
  GROUP BY commodity, year, month_num
  HAVING COUNT(*) >= 10
), yearly AS (
  SELECT m.*,
         AVG(m.month_price) OVER (PARTITION BY m.commodity, m.year) AS year_avg_price,
         COUNT(*) OVER (PARTITION BY m.commodity, m.year) AS months_in_year
  FROM monthly m
)
SELECT commodity, year, month_num, month_price, days,
       month_price / NULLIF(year_avg_price, 0) * 100 AS price_index
FROM yearly
WHERE months_in_year >= 10;

CREATE OR REPLACE VIEW mandi.v_seasonal_index AS
SELECT commodity, month_num, AVG(price_index) AS seasonal_index, COUNT(*) AS n_years
FROM mandi.v_seasonality
GROUP BY commodity, month_num;

-- Data quality: how many markets actually reported.
CREATE OR REPLACE VIEW mandi.v_data_quality AS
SELECT
  commodity, year, month_num,
  COUNT(*) AS days_with_data,
  AVG(n_markets) AS avg_markets_per_day,
  MIN(n_markets) AS min_markets_per_day,
  SUM(CASE WHEN low_coverage THEN 1 ELSE 0 END) AS low_coverage_days
FROM mandi.benchmark_day
GROUP BY commodity, year, month_num;
