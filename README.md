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

## Key Findings & Measured Metrics
- **Dataset Scale:** 158,946 raw APMC mandi records across 5 states (Maharashtra, Karnataka, Gujarat, Uttar Pradesh, Madhya Pradesh) spanning January 2020 to October 2025.
- **Data Quality Audit:** Cleaned and synthesized into 105,295 validated market-days. 1,893 invalid rows were rejected and audited into a structured rejection log (`bad_price_unit`, `bad_price`, `bad_range`, `bad_arrival_unit`, `bad_date`).
- **Spatial Arbitrage:** Maharashtra mandis traded at an average **-8.2% spread** below the national onion benchmark; Uttar Pradesh mandis traded at **-11.4% spread** for potatoes.
- **Early-Warning Shock Detection:** Algorithmic spike radar flagged the February 2025 onion supply crunch (modal prices $+83.9\%$ above 52-week baseline while arrivals fell $-50.4\%$).
- **Buy-Timing Backtest:** Evaluated 68 months comparing trailing-median buying versus naive month-start purchasing:
  - **Tomato:** $+0.86\%$ average monthly savings (cheaper in 17 months, dearer in 14 months).
  - **Potato:** $+0.54\%$ average monthly savings (cheaper in 21 months, dearer in 12 months).
  - **Onion:** $+0.18\%$ average monthly savings (cheaper in 21 months, dearer in 13 months, worst single month $-119.58\%$ during rapid supply shocks).

---

## Power BI 5-Page Dashboard Structure

| Page | Core Analytical Question | Visuals & Layout | Primary Insight / Decision |
| :--- | :--- | :--- | :--- |
| **1. Market Pulse** | *What is the price now and what is normal?* | Commodity slicer, KPI Cards (Latest Price, YoY %, Price vs 4W Avg %, Reporting Mandis), Dual-axis Line Chart (Benchmark vs 28-day MA & Last Year), Weekly Arrival Volume bars. | Real-time visibility into current national wholesale prices versus historical baselines. |
| **2. Where to Buy** | *Where is it cheapest and can we trust the gap?* | State spread bar chart, APMC Mandi table (Avg Price, Arrivals, Reporting Reliability %), Top 10 lowest-cost mandis, Drill-through to market-level pricing. | Sourcing reallocation to producing hubs with high reporting reliability ($>85\%$). |
| **3. When to Buy** | *Which months are historically cheapest and what does margin look like?* | Monthly Price Index Matrix (Month $\times$ Year heat map), Seasonal Index bar chart with 100-baseline, What-If parameter panel. | Forward-buying and storage allocation during seasonal trough windows. |
| **4. Risk Radar** | *What needs attention this week?* | Commodity Risk Table (26-week Volatility CV, Price vs 52-week norm %, Arrivals vs 52-week norm %, Spike Alert Icon), Price line with spike marker overlay. | Early warning supply shock alerts to hedge or adjust inventory before retail impact. |
| **5. Data Quality & Integrity** | *Can we trust this data?* | Reporting Mandis/day trend line, Rejection reason breakdown stacked bar, Low-coverage day cards, Data limits & methodology text. | Full transparency on data cleanliness, exclusions, and wholesale-to-retail limits. |

---

## Star Schema & Data Modeling

The Power BI model imports the pre-aggregated CSVs in `data/export/` using a clean Star Schema:
- **Fact Tables:**
  - `benchmark_day` (Daily national price and arrivals)
  - `weekly_trend` (`v_spike_flags`: weekly benchmark, moving averages, spike flags)
  - `state_spread` (`v_state_spread`: state-level price vs national benchmark)
  - `market_week` (Individual APMC mandi weekly prices, volume, and reporting reliability)
  - `seasonality` (`v_seasonality`: monthly price index)
- **Dimension Tables:**
  - `dim_date` (Continuous calendar marked as Date table, related to `benchmark_day[date]`)
  - `dim_week` (Monday-start ISO weeks, related on `week_num` to weekly fact tables)
  - `dim_commodity` (Commodity metadata)
  - `dim_state` (State list)
  - `dim_market` (APMC mandi codes, names, districts, latitudes, and longitudes)
- **Relationships:** All relationships are strict $1:\text{Many}$, Single Direction with Auto Date/Time disabled.

---

## Core DAX Formulas

```dax
-- Latest Price & Reporting
Latest Date = MAX ( benchmark_day[date] )

Latest Price = 
VAR d = [Latest Date]
RETURN CALCULATE ( AVERAGE ( benchmark_day[benchmark_price] ), benchmark_day[date] = d )

Markets Reporting = 
VAR d = [Latest Date]
RETURN CALCULATE ( MAX ( benchmark_day[n_markets] ), benchmark_day[date] = d )

-- Moving Averages & Time Intelligence
Price MA28 = 
CALCULATE (
    AVERAGE ( benchmark_day[benchmark_price] ),
    DATESINPERIOD ( dim_date[date], MAX ( dim_date[date] ), -28, DAY )
)

Price LY = CALCULATE ( [Latest Price], SAMEPERIODLASTYEAR ( dim_date[date] ) )

YoY % = DIVIDE ( [Latest Price] - [Price LY], [Price LY] )

-- What-If Sensitivity Measures
Cost per kg = 
DIVIDE ( [Latest Price], 100 ) * ( 1 + [Wastage % Value] ) + [Logistics Value]

Margin % = 
DIVIDE ( [Selling Price Value] - [Cost per kg], [Selling Price Value] )
```

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
