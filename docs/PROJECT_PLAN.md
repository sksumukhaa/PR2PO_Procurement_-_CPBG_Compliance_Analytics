# GAIL Procurement & CPBG Analytics — Project Plan

Source data: PO details + CPBG details, FY 2023-24 to 2025-26 (anonymized).
Reference: GAIL C&P Procedural Manual, 3rd Edition (Issue Date 31.10.2022).

---

## 1. Policy Guidelines Extracted from the C&P Procedure

| Rule | Detail | Clause |
|---|---|---|
| CPBG submission deadline | 30 days from FOA; extendable to 60 days with ED/CGM approval; beyond 60 only if vendor is mobilized at site | 3.2.1(iii), p.85 |
| CPBG value — current | 3% of order/contract value (orders concluded after 31.03.2023 amendment) | 3.2.1A |
| CPBG value — legacy | 10% of order/contract value (orders before the amendment) | 3.2.1(iii)/(iv) |
| CPBG validity duration | 90 days beyond contract period, plus any warranty/DLP | 3.2.1 Note (ii) |
| BG detail intimation to C&P | Within 30 days (this is the exact rule our `cpbg_intimation_diff` compliance flag measures) | 3.2.1 Note (iii), referenced circular 04.07.2022 |
| PR-to-PO cycle time | **No fixed numeric SLA exists** — Section 6.1 provides only blank tracking templates (Tables 6.1-1 to 6.1-4); the manual just says "endeavor to achieve targets" | 6.1.1-6.1.2, p.169-172 |
| Single-bid tender finalization | Should complete within 30 days of bid opening (partial benchmark) | 2.19 |

**Implication for the project:** frame the PR-to-PO cycle time analysis as *establishing an empirical baseline* (since GAIL's own procedure doesn't fix one), while framing the CPBG analysis as *compliance measurement against an explicit, cited policy* — these are two different (and both legitimate) analytical postures, and saying so explicitly is a strong, honest thing to point out in an interview.

---

## 2. KPIs (11 total)

| # | KPI | Formula | Grounded in policy? |
|---|---|---|---|
| 1 | PR-to-PO Cycle Time | `PO Date − PR Date`, avg days, trended by FY/month | No fixed target — empirical baseline |
| 2 | Internal Approval Lag | `PO Date − C&P Release Date` | No fixed target |
| 3 | Lead Time Deviation Rate | % of POs where `D(LT-STD LT) > 0` | Uses GAIL's own internal "standard lead time" field |
| 4 | CPBG Submission Compliance | % of guarantees submitted within 30 days of FOA | **Yes — Clause 3.2.1(iii)** |
| 5 | CPBG Intimation Compliance | % of BG detail intimations to C&P within 30 days (derived from `Difference`, not the unreliable manual flag) | **Yes — Clause 3.2.1 Note (iii)** |
| 6 | CPBG Value Compliance | `BG VALUE / PO Basic Value` checked against 3% (post-Apr'23) or 10% (pre) benchmark | **Yes — Clause 3.2.1A** |
| 7 | CPBG Duration Compliance | Flag where `Term End < Schedule Delivery Date + 90 days` | **Yes — Clause 3.2.1 Note (ii)** |
| 8 | Live BG Exposure | Sum of `Credit Amount` where `Start of Term ≤ today ≤ Term End` | Operational metric |
| 9 | Vendor Concentration (HHI) | Herfindahl-Hirschman Index of PO value share by vendor, per FY | Standard risk metric |
| 10 | Vendor Risk Score (composite) | Weighted: delay rate (40%) + lead time deviation (30%) + CPBG compliance history (30%) | Custom-built metric |
| 11 | MSME/Domestic Spend Share | % of PO value by `VENDOR TYPE` (Micro/Small/Medium) and domestic vs foreign | Ties to GoI MSME procurement policy |

KPIs 6 and 7 are new — they only became possible after reading the actual manual, and they're the most distinctive ones in the whole project since almost no portfolio piece checks *compliance against a cited internal policy document*.

---

## 3. Calculation Approach: SQL vs DAX

**General principle:** clean and pre-aggregate in SQL (or Python) wherever a KPI doesn't need to respond to live slicer/filter interaction in the report. Use DAX only where a measure must recalculate dynamically as the user filters by plant, vendor, purchasing group, or date range — that's what DAX is actually for, and over-using it for static historical aggregates just makes the model slower and harder to debug.

| KPI | Where to calculate | Why |
|---|---|---|
| 1, 2 (Cycle time, Approval lag) | **SQL view**, then a thin DAX `AVERAGE` measure on top | Base calc is static (date arithmetic); DAX only needed so it responds to FY/Plant slicers |
| 3 (Lead time deviation) | **SQL** (cleaning of `D(LT-STD LT)` already done in `load_to_sqlite.py`) + DAX `DIVIDE`/`CALCULATE` for the % | Cleaning must happen once in SQL; the % should be filter-responsive |
| 4, 5 (CPBG compliance rates) | **SQL** for the derived flag (`beyond_30_derived`), **DAX** for the live % | Same pattern — clean once, aggregate dynamically |
| 6 (CPBG value compliance) | **SQL** — needs a `CASE WHEN PO Date < '2023-04-01' THEN 0.10 ELSE 0.03 END` lookup, cleanest as a computed column | One-time business-rule lookup, not filter-dependent |
| 7 (CPBG duration compliance) | **SQL** — simple date comparison flag | Same reasoning |
| 8 (Live BG exposure) | **DAX**, using `TODAY()` | Must always reflect the current date — SQL views won't auto-refresh unless rebuilt, DAX recalculates live |
| 9 (HHI) | **DAX**, using `SUMX` over vendor shares within `ALLSELECTED` | Needs to change as the user filters by FY/Plant — a true DAX use case, not just a static number |
| 10 (Vendor risk score) | **SQL** for the underlying delay/deviation aggregates, **DAX** for the final weighted composite | Lets you tweak weights live in the report without rebuilding SQL |
| 11 (MSME/domestic split) | **SQL** for categorization, **DAX** for the % of total (filter-responsive) | Standard pattern |

**Rule of thumb going forward:** if a number needs to change when someone clicks a slicer, it's DAX. If it's a one-time business rule or cleaning step, it's SQL/Python — don't rebuild that logic in DAX.

---

## 4. Columns to Review for Dropping

Proposed based on column names — **confirm with actual null%/duplication check in the Python EDA step (Section 5) before dropping anything**, since I haven't inspected all values yet.

**Likely redundant (duplicate ID/name pairs — keep one, drop the other):**
- `Created by(CPF)` vs `Created by`
- `EIC` vs `EIC Name`
- `PR Created by.` vs `PR created by Name.`
- `PLANT` vs `PLANT NAME`
- `IND. DEPT.` vs `INDENTING DEPT.`
- `Country Code` vs `Conutry` (note the typo in the source column name)

**Likely low-value / candidates to drop after null-check:**
- `SNO` — row index, not analytical
- `Doc. Type` — check if constant across all rows
- `Currency` / `PO Ex Rate` — check if always INR/1.0 (if so, `Exchange Value(INR)` alone is sufficient)
- `TYPE OF PROCUREMENT` — mostly null based on our earlier inspection (only 3 distinct non-null values seen)
- CPBG side: `Assignment`, `Transaction` — likely system-internal IDs, check if used anywhere downstream
- CPBG side: `Entered On` vs `Entered On.1` — duplicate pair

**Do not drop without checking:**
- `State` — has real nulls but useful for regional analysis if populated enough
- `PO SUBJECT.` / `REASON Desc` — free text, not for dropping but for the confidentiality scan you already need to do

---

## 5. Python EDA & Cleaning Plan (before dashboard building)

1. **Null audit** — % missing per column across all three tables; flag anything >80% null as a drop candidate.
2. **Duplicate-pair resolution** — confirm ID/Name column pairs actually map 1:1, keep the more analysis-friendly one.
3. **Dtype fixes** — dates parsed consistently (already handled for the known messy columns), numeric cleaning verified.
4. **Derive new fields** — `cpbg_value_pct` (BG VALUE / PO value), `cpbg_expected_pct` (3% or 10% by date rule), `cpbg_duration_ok` flag, FY-quarter columns.
5. **Outlier pass** — IQR-based flagging on `PO Basic Value (INR)` and `Credit Amount`, by category — informs whether extreme values are real or data-entry errors before they skew KPI averages.
6. **Univariate/bivariate exploration** — distribution plots of cycle time, boxplots by Purchasing Group, a correlation check between `TOTAL SCORE` and delay.
7. **Output** — a cleaned, analysis-ready dataset + a short data dictionary, before touching Power BI at all.

---

## 6. Three-Page Dashboard — Exact Plots

### Page 1: PO Lifecycle & Bottlenecks
- **Funnel/waterfall chart** — avg days at each of the 5 lifecycle stages (PR → HOD → C&P → PO → Delivery)
- **Line chart** — monthly PR-to-PO cycle time trend, one line per FY
- **KPI cards** — avg cycle time, avg approval lag, % lead time deviation
- **Clustered bar chart** — avg cycle time by Purchasing Group (or Plant) — surfaces bottleneck departments

### Page 2: Vendor Concentration & Risk
- **Treemap** — PO value by vendor (top 20), colored by delay severity
- **Line/bump chart** — HHI concentration index trend across the 3 years
- **Matrix table** — vendor risk scorecard: vendor alias, delay rate, avg deviation days, CPBG compliance history, composite risk score, conditional-formatted red/amber/green
- **100% stacked bar chart** — domestic vs foreign, and separately MSME category, spend split by FY

### Page 3: CPBG Compliance & Exposure
- **KPI cards** — CPBG submission compliance %, intimation compliance %, current live exposure value
- **Bar chart** — compliance rate (submission and intimation, two series) by FY
- **Gantt-style timeline or calendar heatmap** — BG term overlaps, showing exposure building/unwinding over time
- **Table with conditional formatting** — CPBG value compliance flags (actual % vs required 3%/10% benchmark) and duration compliance flags
- **Table** — "expiry radar": guarantees expiring in next 90 days, sorted by urgency

---

## 7. Workflow — Who Does What

**What I'll do (I already have your anonymized data in this session):**
1. Run the full Python EDA — null audit, duplicate-pair check, outlier scan — and report back the findings.
2. Build the cleaned/derived dataset (drop confirmed-redundant columns, add the new compliance-check fields from Section 2).
3. Write the finalized SQL views/queries for every KPI, and the exact DAX formulas for the ones that need to be filter-responsive.
4. Document everything in a data dictionary so you're not guessing what each field means when you're in Power BI.

**What you'll need to do:**
1. Review the EDA null/duplication report and confirm the column-drop list — you know GAIL's internal conventions better than I can infer from column names alone.
2. Install Power BI Desktop (if not already) and import the cleaned data/SQL views — I can't drive Power BI Desktop directly from here, so the actual report-building happens on your machine.
3. Build the visuals following the exact page-by-page plan in Section 6, pasting in the DAX formulas I provide.
4. Share screenshots as you go if you want feedback on layout/formatting choices, or hit a wall on a specific DAX measure.
5. Do the confidentiality scan on free-text columns (`PO SUBJECT.`, `REASON Desc`) before anything goes public, as flagged earlier.

Let's start with step 1 — want me to run the EDA now?
