# Technical & Analytical Decisions Log (DECISIONS.md)

### Decision 1: Aggregation of Varieties to One Market-Day Price
- **Problem:** A single APMC mandi frequently reports multiple varieties for the same staple commodity on the same date (e.g., "Red", "Local", "Hybrid").
- **Evidence:** Naively treating varieties as separate observations skews market-level pricing or overweights mandis with finer variety breakdowns.
- **Options:** (1) Take a simple unweighted arithmetic mean across varieties; (2) Filter for only the primary variety; (3) Compute an arrivals-weighted mean across varieties.
- **Choice:** **Option 3 (Arrivals-weighted mean).** When daily arrival tonnage is reported per variety, modal prices are weighted by volume ($P_{market} = \frac{\sum P_{modal} \times A}{\sum A}$). If arrival quantities are missing/zero, it falls back cleanly to the arithmetic mean across varieties for that market-day.

---

### Decision 2: Daily National Benchmark Metric (Median vs. Mean)
- **Problem:** How to summarize daily market prices across diverse mandis into a robust national benchmark price.
- **Evidence:** Wholesale prices exhibit heavy-tailed distributions and recording fat-finger errors (e.g., miskeyed decimal places, single distress sales). Arithmetic averages are sensitive to extreme values.
- **Options:** (1) Arithmetic Mean; (2) Volume-weighted average price across all markets; (3) Median of market-day prices.
- **Choice:** **Option 3 (Median).** The median represents the price paid by the typical mandi while providing mathematical immunity against extreme single-market outliers or data entry typos.

---

### Decision 3: Suspect Outlier Rule (Relative to Same-Day Cross-Market Median)
- **Problem:** Data entry errors exist in mandi reports (e.g., Rs 150/quintal entered as Rs 15,000/quintal or Rs 15/quintal), but agricultural commodities genuinely experience massive national price spikes during crunches.
- **Evidence:** Fixed global thresholds fail because Rs 6,000/quintal is absurd for potatoes during harvest season, but completely normal during severe off-season shortages.
- **Options:** (1) Static min/max filters; (2) Time-series deviation (z-score against rolling history); (3) Cross-sectional ratio against the same day's cross-market median.
- **Choice:** **Option 3.** A market-day price is flagged as suspect only if its ratio to the *same day's median across reporting markets* is $< 0.25$ or $> 4.0$, provided at least `MIN_MARKETS` (5) reported that day. Genuine macro price surges lift all markets simultaneously and remain unflagged; localized fat-finger errors stick out sharply and are filtered out.

---

### Decision 4: Exclusion of Low-Coverage Days (`MIN_MARKETS < 5`)
- **Problem:** On regional holidays, weekends, or system outages, only 1 or 2 isolated mandis may submit reports, producing spurious swings in trend analysis.
- **Evidence:** Days with 1 or 2 reporting mandis show erratic day-to-day volatility unrepresentative of the broader wholesale market.
- **Options:** (1) Interpolate or forward-fill missing days; (2) Include all days regardless of market count; (3) Flag low-coverage days (`low_coverage = n_markets < 5`) and exclude them from benchmark trends.
- **Choice:** **Option 3.** Benchmark trends and rolling windows filter `WHERE NOT low_coverage`, preventing thin reporting days from distorting weekly moving averages and year-over-year figures.
