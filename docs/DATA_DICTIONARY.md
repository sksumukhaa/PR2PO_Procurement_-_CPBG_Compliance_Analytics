# Data Dictionary — Cleaned GAIL Procurement Dataset

## EDA Summary

**Null audit highlights:**
- `TOTAL SCORE` — 98.5% null (7/459 rows). Too sparse to support the original
  "vendor score vs delay" correlation KPI — dropped from the KPI list, kept in
  the raw column set for reference only.
- `BANK NAME.` / `BG NUMBER` / `BG EXP.` — 83% null in `po_master`, but this is
  **expected sparsity, not bad data**: per Clause 3.2.1(i)-(ii), orders under
  ₹5 lakhs and proprietary-item purchases are exempt from CPBG entirely, so
  most POs legitimately have no guarantee attached.
- `PR Date` / `USER HOD Release DT` / `C&P Release Date` — 25.1% null,
  consistent with certain PO types (e.g. repeat orders, rate contracts) that
  don't go through the full PR→tender cycle.
- `Assignment` (CPBG_INFO) and `BEYOND 30 DAYS` (CPBG_DIFF) — 100% null,
  dropped.

**Duplicate-column resolution (all confirmed via 1:1 mapping check, not just
column-name similarity):**
| Kept | Dropped | Reason |
|---|---|---|
| `EIC` | `EIC Name` | Code→name is 100% consistent; name→code only 37% (same name maps to multiple codes — a real data quality issue in the name field) |
| `INDENTING DEPT.` | `IND. DEPT.` | 100% duplicate both directions |
| `Country Code` | `Conutry` | 100% duplicate both directions (also a typo'd column name) |
| `PR Created by.` | `PR created by Name.` | ~100%/98.2% duplicate |
| `Created by(CPF)` | `Created by` | 100% duplicate both directions |
| `PLANT` | `PLANT NAME` | 100% duplicate |
| `Exchange Value(INR)` | `PO Ex Rate` | Only 9/459 rows are non-INR; the converted value column is sufficient |
| — | `Assignment`, `Transaction`, `Entered On.1`, `Dealing Officer` (CPBG_INFO only) | 100% null or redundant row identifiers |

**Outlier scan (IQR method):**
- `PO Basic Value (INR)`: 11.1% outliers (up to ~₹25.6 crore) — real large
  contracts, not errors. Use median alongside mean; consider log scale for
  the value-distribution chart.
- `Credit Amount` (CPBG): 8.5% outliers.
- `cycle_days_pr_to_po`: **6 rows have negative values** (PO dated before PR)
  — logically impossible, flagged via `cycle_time_data_flag` rather than
  silently averaged in. Decide whether to exclude, investigate, or footnote
  these before finalizing Page 1's cycle-time KPIs.

---

## po_master_cleaned.csv (459 rows, 50 columns)

Key derived columns (all others are original, cleaned-dtype columns):

| Column | Type | Description |
|---|---|---|
| `cycle_days_pr_to_po` | int | `PO DATE − PR Date`, days |
| `approval_lag_days` | int | `PO DATE − C&P Release Date`, days |
| `cycle_time_data_flag` | text | `"OK"` or `"NEGATIVE_CYCLE_CHECK_DATA"` — flags the 6 impossible rows |
| `lead_time_deviation_days` | float | Cleaned version of `D(LT-STD LT)` (SAP trailing-minus format fixed) |

## cpbg_info_cleaned.csv (71 rows, 26 columns)

| Column | Type | Description |
|---|---|---|
| `PO Basic Value (INR)` | float | Joined from po_master via `Purchasing Document` = `PO NO` |
| `Schedule Delivery Da` | date | Joined from po_master |
| `expected_cpbg_pct` | float | 10.0 if PO Date < 2023-04-01, else 3.0 (Clause 3.2.1A) |
| `actual_cpbg_pct` | float | `Credit Amount / PO Basic Value (INR) * 100` |
| `cpbg_value_compliant` | bool | `actual_cpbg_pct >= expected_cpbg_pct − 0.5` (0.5pp rounding tolerance) |
| `required_term_end` | date | `Schedule Delivery Da + 90 days` (Clause 3.2.1 Note ii) |
| `cpbg_duration_compliant` | bool | `Term End >= required_term_end` |

**Result: 73.2% value-compliant, 85.9% duration-compliant.**

## cpbg_intimation_diff_cleaned.csv (83 rows, 9 columns)

| Column | Type | Description |
|---|---|---|
| `Difference_num` | float | Cleaned numeric version of `Difference` |
| `intimation_compliant` | bool | `Difference_num <= 30` (Clause 3.2.1 Note iii — replaces the unreliable, blank `BEYOND 30 DAYS` column) |

**Result: only 14.5% compliant.** This is your headline compliance finding.
