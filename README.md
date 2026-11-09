# Fresh-Produce Price-Risk Monitor

> An enterprise wholesale market price-risk monitor and procurement decision engine built on multi-year Indian APMC mandi records.

---

## Scenario (Fictional Procurement Persona)
You are a senior procurement analyst for a mid-sized Indian grocery retail chain buying volume staples (onion, tomato, potato). This dashboard and decision pipeline turns years of volatile daily APMC mandi data into actionable procurement intelligence: identifying spatial price arbitrage, assessing seasonality trends, evaluating margin risk under wastage/logistics assumptions, and early-warning alerts for upcoming price spikes.

*Note: The procurement persona and company scenario are fictional. All numbers, SQL views, and models trace directly to open-data AGMARKNET measurements.*

---

## Data Pipeline Architecture

```text
Raw AGMARKNET CSV (~3.9 GB)
       │
       ▼ (mandi/clean.py: chunk-safe cleaning, unit normalization, error rejection)
data/interim/market_day.parquet + reject_counts.csv
       │
       ▼ (mandi/engine.py: DuckDB local OLAP engine)
DuckDB Star Schema (mandi schema: benchmark_day, dimensions)
       │
       ▼ (sql/views.sql: 8 analytical window-function views)
data/export/*.csv
       │
       ▼ (Power BI Desktop: Star Schema & DAX measures)
5-Page Interactive Executive Dashboard + 1-Page Procurement Insight Memo
```

---

## Key Features & Analytics
1. **Chunk-Safe Data Pipeline:** Streams multi-gigabyte CSVs in 500,000-row chunks with zero memory exhaustion, converting mixed units to metric tonnes and logging reject reasons into an audit table.
2. **Robust SQL Window Analysis:** Built on DuckDB using calendar-aligned `RANGE BETWEEN ... PRECEDING` windows over ISO weeks, eliminating missing-data distortions.
3. **Early-Warning Spike Radar:** Algorithmic detection of supply-side market shocks (combines $+20\%$ price deviation with $-20\%$ arrival drop relative to 52-week moving baselines).
4. **What-If Margin Sensitivity:** Interactive Power BI scenario modeling allowing procurement managers to adjust selling price, transit logistics, and wastage percentage.
5. **Backtested Buy-Timing Rule:** Compares a disciplined trailing-median procurement strategy against naive month-start purchasing.

---

## Repository Structure
```
mandi-price-monitor/
├── data/
│   ├── raw/             # Raw AGMARKNET CSV (git-ignored)
│   ├── interim/         # Cleaned parquet & reject logs (git-ignored)
│   └── export/          # Exported CSVs feeding Power BI
├── docs/
│   ├── domain_notes.md  # APMC mandi mechanics, perishability & supply cycles
│   ├── DECISIONS.md     # Architectural & statistical decision log
│   └── kpi_dictionary.md# Definitions, formulas, and analytical caveats
├── mandi/
│   ├── config.py        # Pipeline parameters, thresholds, and engine selection
│   ├── clean.py         # Chunk-level validator and unit normalizer
│   ├── aggregate.py     # Partial-sum aggregator and star schema builder
│   ├── engine.py        # Unified DuckDB & Google BigQuery execution layer
│   └── backtest.py      # Trailing-median buy-timing backtesting engine
├── scripts/
│   ├── profile_csv.py   # Streams and profiles raw AGMARKNET records
│   ├── build_market_day.py # Executes full chunked cleaning & parquet export
│   ├── load_tables.py   # Populates DuckDB model tables and dimensions
│   ├── run_sql.py       # Executes sql/views.sql analytical views
│   ├── export_for_powerbi.py # Generates CSV datasets for Power BI import
│   └── run_backtest.py  # Runs historical backtest and prints savings summary
├── sql/
│   └── views.sql        # 8 production SQL views with window functions
├── tests/
│   ├── synth.py         # Realistic synthetic data generator with planted spikes
│   ├── test_clean.py    # Unit tests for data validation rules
│   ├── test_aggregate.py# Tests chunking equivalence and date math
│   ├── test_sql.py      # Verification of all SQL window functions
│   └── test_backtest.py # Unit tests ensuring zero lookahead bias
├── requirements.txt
├── pytest.ini
└── .env.example
```

---

## How to Run

1. **Activate virtual environment:**
   ```powershell
   .venv\Scripts\Activate.ps1
   ```
2. **Run test suite (21 synthetic tests):**
   ```powershell
   python -m pytest -q
   ```
3. **Execute pipeline end-to-end (when raw data is in `data/raw/`):**
   ```powershell
   python -m scripts.profile_csv
   python -m scripts.build_market_day
   python -m scripts.load_tables
   python -m scripts.run_sql
   python -m scripts.export_for_powerbi
   python -m scripts.run_backtest
   ```

---

## Transparency & Data Integrity
- **Scaffolding:** Code scaffolding was AI-assisted; analytical scope, business hypotheses, data quality decisions, verification hand-checks, and procurement conclusions are mine.
- **Honesty about Impact:** This is an analytical portfolio project. No claims of actual corporate savings are made; claims reflect measured historical figures.
