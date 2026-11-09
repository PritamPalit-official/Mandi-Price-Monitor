# Executive Procurement Decision Memo

**TO:** Head of Procurement (Fictional Grocery Retail Chain)  
**FROM:** Pritam Palit, Senior Procurement & BI Analyst  
**DATE:** November 10, 2026  
**DATA TIMEFRAME:** AGMARKNET Daily Mandi Wholesale Reports (January 2020 – October 2025)  
**DECISION NEEDED:** Forward-buying schedule, seasonal sourcing shifts, and price shock mitigation for Onion, Tomato, and Potato.

---

### Key Analytical Findings

1. **Spatial Arbitrage in Producing Belts (Page 2 - Where to Buy):**  
   - **Finding:** Maharashtra mandis (Lasalgaon, Pimpalgaon) consistently traded at an average **-8.2% spread** relative to the national weekly onion benchmark, while Uttar Pradesh mandis (Agra, Farrukhabad) traded at an average **-11.4% spread** for potatoes.  
   - **So What (Action):** Shift 40% of contracted northern volume directly to farmgate/mandi sourcing hubs in Nashik (Onion) and Agra (Potato), provided interstate logistics costs remain below ₹1.80/kg.

2. **Supply Shock Warning Precedes Peaks by 1–2 Weeks (Page 4 - Risk Radar):**  
   - **Finding:** In February 2025, onion modal prices surged **+83.9% above the 52-week trailing baseline** (₹2,898/qtl vs ₹1,576/qtl baseline) precisely as daily mandi arrival volumes collapsed by **-50.4%**.  
   - **So What (Action):** Establish an automated procurement trigger: whenever weekly prices cross $+20\%$ and arrivals fall below $-20\%$ of their 52-week trend for 2 consecutive weeks, immediately execute forward purchase orders before secondary wholesale spikes hit retail shelves.

3. **Seasonality Cycle & Margin Exposure (Page 3 - When to Buy & What-If):**  
   - **Finding:** Under baseline logistics (₹2.50/kg) and wastage assumptions (8%), retail margins turn negative ($<0\%$) during historical off-season peaks (July–August for Tomato, October–November for Onion) if retail shelf prices are held fixed at standard MRPs.  
   - **So What (Action):** Institute a dynamic retail markup window during Q3/Q4 peak months or contract ventilated cold-storage space in May–June when the seasonal index sits at historical lows (~82% of annual mean).

---

### Recommendation & Strategy Trade-Offs

**Recommendation:**  
Execute a hybrid procurement model:
- **Baseline Volume (70%):** Direct forward contracts with producing APMCs during low-season windows (April–May for Rabi Onion and Potato).
- **Spot Buffer (30%):** Flexible local mandi sourcing monitored daily via the Power BI Risk Radar.

**Trade-Offs & Primary Risk:**  
Forward contracting locks in favorable pricing but exposes the organization to storage weight loss, rotting (spoilage risk up to 12–15% without temperature-controlled cold chains), and sudden post-harvest policy shocks (such as government export bans or emergency buffer releases by NAFED).

---

### Buy-Timing Backtest Summary

- **Backtested Rule:** Buy 1 unit/month on the first day prices drop to or below the trailing 364-day median; if prices never drop below the median in that calendar month, buy on the last business day (compared to buying on Day 1).
- **Measured Result (68 Months Evaluated):**
  - **Onion:** Average monthly price reduction of **+0.18%** (cheaper in 21 months, dearer in 13 months, worst single month: **-119.58%** during an explosive supply shock where delayed buying hit peak prices).
  - **Potato:** Average monthly price reduction of **+0.54%** (cheaper in 21 months, dearer in 12 months, worst month: -16.8%).
  - **Tomato:** Average monthly price reduction of **+0.86%** (cheaper in 17 months, dearer in 14 months, worst month: -21.32%).
- **Key Takeaway:** A naive trailing-median rule performs modestly in stable markets (+0.5% to +0.9%) but incurs severe drawdown in panic-driven supply shocks. Procurement requires combining price rules with arrival volume flags (`is_spike`).

---

### Analytical Limitations & Integrity
- **Wholesale vs. Retail:** Mandi modal prices reflect primary agricultural transactions, not retail landing costs.
- **Modal Metric:** Modal price is the most frequently traded price tier, not an arithmetic average or volume-weighted average.
- **Reporting Completeness:** Mandi attendance and reporting compliance fluctuate across holidays and weekends; low-coverage days ($<5$ mandis) were systematically excluded.
- **Cost Exclusions:** Excludes transit transit spoilage, cold-storage demurrage, and inter-state toll overheads.
