# PR2PO — Procurement Lifecycle & CPBG Compliance Analytics

**End-to-end analytics on real PSU procurement data** — from raw Excel exports to a
policy-audited, brand-designed Power BI dashboard. Built on 459 actual purchase orders
and 71 bank guarantee records from GAIL (India) Ltd., anonymized for public release.

> Most portfolio projects analyze Airbnb listings or Titanic survival. This one analyzes
> real government-sector procurement data against the company's own 250-page policy
> manual — and finds a genuine compliance gap most dashboards would never surface.

---

## Key Findings

| Finding | Number |
|---|---|
| CPBG intimation compliance (30-day rule, Clause 3.2.1 Note iii) | **14.5%** — vs 73-86% on value/duration compliance |
| PR-to-PO cycle time trend | Worsened from **~94 days → ~115 days** post-2023-24 |
| Foreign/import order cycle time vs domestic | **377 days vs 95-150 days** |
| Vendor concentration (HHI) volatility across 3 years | **1243 → 235 → 1114** |
| MSME combined spend share | **42-66%**, above typical policy mandates |
| Data quality issues caught & flagged (not hidden) | 6 impossible negative cycle-times, 100%-null columns, identical approval-stage dates |

---

## What Makes This Different

- **Real, not synthetic, data** — actual anonymized PO and CPBG records, not a Kaggle dataset.
- **Policy-grounded, not assumption-based** — 3 of the 11 KPIs are measured directly against
  cited clauses from GAIL's official C&P Procedure Manual, not invented benchmarks.
- **Data quality treated as a finding, not a footnote** — every anomaly (duplicate columns,
  sparse fields, impossible values) is documented and resolved with a stated rationale,
  not silently dropped.
- **Full stack, independently built** — Python cleaning → SQL modeling → DAX measures →
  branded Power BI design, end to end.

---

## Tech Stack

`Python` (pandas, numpy) · `SQL` (SQLite) · `Power BI` (DAX) · `Jupyter` · `Matplotlib / Seaborn`

---

## Repository Structure

```
├── data/
│   ├── anonymize_gail_data.py       # Vendor/employee/document masking script
│   ├── clean_and_derive.py          # Cleaning + feature engineering (standalone script)
│   ├── anonymized/                  # Post-anonymization, pre-cleaning CSVs
│   └── cleaned/                     # Analysis-ready CSVs with derived KPIs
├── notebooks/
│   ├── 01_data_cleaning_feature_engineering.ipynb
│   └── 02_eda_visualizations.ipynb  # 10 sections of plots, one per KPI group
├── sql/
│   ├── schema.sql                   # Table/index reference
│   ├── load_to_sqlite.py            # CSV -> SQLite loader with type cleaning
│   ├── analysis_queries.sql         # Every KPI query, organized by dashboard page
│   └── gail_procurement.db          # Pre-built, ready-to-query SQLite database
├── dashboard/
│   ├── gail_dashboard_branded.html  # Interactive 3-page dashboard prototype
│   └── POWER_BI_BUILD_GUIDE.md      # Full build guide: 21 DAX measures, theme, visuals
└── docs/
    ├── DATA_DICTIONARY.md           # Every column, every derived field, explained
    └── PROJECT_PLAN.md              # KPI definitions, SQL-vs-DAX rationale, workflow
```

---

## The 3-Page Dashboard

**Page 1 — PO Lifecycle & Bottlenecks:** cycle-time trend, 3-stage lifecycle funnel,
bottleneck breakdown by order type.

**Page 2 — Vendor Concentration & Risk:** top vendors by spend, HHI concentration index,
custom composite vendor risk score, MSME category spend split.

**Page 3 — CPBG Compliance & Exposure:** value/duration/intimation compliance rates
(cited against actual policy clauses), live bank guarantee exposure, 90-day expiry radar.

Open `dashboard/gail_dashboard_branded.html` directly in a browser for the interactive
prototype, or follow `dashboard/POWER_BI_BUILD_GUIDE.md` to build the full Power BI version.

---

## How to Run

```bash
# 1. Clone and install dependencies
git clone <this-repo>
cd pr2po-procurement-analytics
pip install pandas numpy matplotlib seaborn

# 2. Run the notebooks in order
jupyter notebook notebooks/01_data_cleaning_feature_engineering.ipynb
jupyter notebook notebooks/02_eda_visualizations.ipynb

# 3. Or query the pre-built database directly
sqlite3 sql/gail_procurement.db < sql/analysis_queries.sql

# 4. Or just open the dashboard prototype
open dashboard/gail_dashboard_branded.html
```

---

## Data & Privacy

All vendor names, employee names, bank names, and document numbers have been
**anonymized with consistent aliasing** (see `data/anonymize_gail_data.py`) — the same
real entity maps to the same alias across all 3 fiscal years, so trend analysis remains
valid. Monetary values are scaled by a randomized factor to obscure absolute figures
while preserving relative comparisons. This is an independent analytics project and is
not an official publication of GAIL (India) Ltd.

---

## Author

Built independently as a portfolio project demonstrating end-to-end analytics capability:
data engineering, domain research, statistical/business logic, and dashboard design.
