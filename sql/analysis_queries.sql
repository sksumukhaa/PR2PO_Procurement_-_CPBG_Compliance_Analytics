-- Analysis queries for gail_procurement.db
-- Each block maps to a KPI and a dashboard page from the project plan.
-- Run these directly in SQLite, or connect Power BI to the .db file and use
-- these as the logic reference for your DAX measures / Power Query steps.
-- All tested against the real (anonymized) data.

-- ============================================================
-- PAGE 1: PO Lifecycle & Bottlenecks (KPIs 1, 2, 3)
-- ============================================================

-- KPI 1: PR-to-PO cycle time, trended by FY
SELECT
    FY,
    ROUND(AVG(julianday("PO DATE") - julianday("PR Date")), 1) AS avg_cycle_days,
    COUNT(*) AS po_count
FROM po_master
WHERE "PR Date" IS NOT NULL AND "PO DATE" IS NOT NULL
GROUP BY FY
ORDER BY FY;

-- KPI 1b: full lifecycle funnel -- avg days at each stage
SELECT
    FY,
    ROUND(AVG(julianday("USER HOD Release DT") - julianday("PR Date")), 1) AS pr_to_hod_days,
    ROUND(AVG(julianday("C&P Release Date") - julianday("USER HOD Release DT")), 1) AS hod_to_cp_days,
    ROUND(AVG(julianday("PO DATE") - julianday("C&P Release Date")), 1) AS cp_to_po_days,
    ROUND(AVG(julianday("Schedule Delivery Da") - julianday("PO DATE")), 1) AS po_to_delivery_days
FROM po_master
GROUP BY FY
ORDER BY FY;

-- KPI 2: Internal approval lag (PO Date - C&P Release Date)
SELECT
    FY,
    ROUND(AVG(julianday("PO DATE") - julianday("C&P Release Date")), 1) AS avg_approval_lag_days
FROM po_master
WHERE "C&P Release Date" IS NOT NULL
GROUP BY FY
ORDER BY FY;

-- KPI 3: Lead time deviation rate -- % of POs exceeding standard lead time
SELECT
    FY,
    ROUND(100.0 * SUM(CASE WHEN "D(LT-STD LT)_clean" > 0 THEN 1 ELSE 0 END)
        / SUM(CASE WHEN "D(LT-STD LT)_clean" IS NOT NULL THEN 1 ELSE 0 END), 1) AS pct_exceeding_std,
    ROUND(AVG("D(LT-STD LT)_clean"), 1) AS avg_deviation_days
FROM po_master
GROUP BY FY
ORDER BY FY;

-- Cycle time by Purchasing Group -- spot bottleneck departments
SELECT
    "Purchasing Group",
    COUNT(*) AS po_count,
    ROUND(AVG(julianday("PO DATE") - julianday("PR Date")), 1) AS avg_cycle_days
FROM po_master
WHERE "PR Date" IS NOT NULL
GROUP BY "Purchasing Group"
ORDER BY avg_cycle_days DESC;

-- ============================================================
-- PAGE 2: Vendor Concentration & Risk (KPIs 5, 7, 8, bonus 9)
-- ============================================================

-- KPI 5: Vendor concentration -- top-5 vendor share of spend, by FY
WITH vendor_totals AS (
    SELECT FY, "VENDOR CODE" AS vendor, SUM("PO Basic Value (INR)") AS spend
    FROM po_master
    GROUP BY FY, "VENDOR CODE"
),
ranked AS (
    SELECT FY, vendor, spend,
        RANK() OVER (PARTITION BY FY ORDER BY spend DESC) AS rnk,
        SUM(spend) OVER (PARTITION BY FY) AS total_spend
    FROM vendor_totals
)
SELECT FY,
    ROUND(100.0 * SUM(CASE WHEN rnk <= 5 THEN spend ELSE 0 END) / MAX(total_spend), 1) AS top5_share_pct
FROM ranked
GROUP BY FY
ORDER BY FY;

-- KPI 5b (proper HHI): sum of squared market shares per vendor, by FY
WITH vendor_totals AS (
    SELECT FY, "VENDOR CODE" AS vendor, SUM("PO Basic Value (INR)") AS spend
    FROM po_master
    GROUP BY FY, "VENDOR CODE"
),
shares AS (
    SELECT FY, vendor, spend,
        1.0 * spend / SUM(spend) OVER (PARTITION BY FY) AS share
    FROM vendor_totals
)
SELECT FY, ROUND(SUM(share * share) * 10000, 0) AS hhi_index  -- >2500 = highly concentrated
FROM shares
GROUP BY FY
ORDER BY FY;

-- KPI 7: Vendor risk score (delay rate + value volatility), top 15
SELECT
    "VENDOR CODE" AS vendor,
    COUNT(*) AS total_pos,
    ROUND(AVG(CASE WHEN "D(LT-STD LT)_clean" > 0 THEN "D(LT-STD LT)_clean" ELSE 0 END), 1) AS avg_delay_days,
    ROUND(100.0 * SUM(CASE WHEN "D(LT-STD LT)_clean" > 0 THEN 1 ELSE 0 END) / COUNT(*), 1) AS delay_rate_pct,
    ROUND(
        AVG(CASE WHEN "D(LT-STD LT)_clean" > 0 THEN "D(LT-STD LT)_clean" ELSE 0 END) * 0.6
        + (100.0 * SUM(CASE WHEN "D(LT-STD LT)_clean" > 0 THEN 1 ELSE 0 END) / COUNT(*)) * 0.4
    , 1) AS risk_score
FROM po_master
WHERE "D(LT-STD LT)_clean" IS NOT NULL
GROUP BY "VENDOR CODE"
HAVING COUNT(*) >= 2   -- exclude one-off vendors from ranking (too little data to trust)
ORDER BY risk_score DESC
LIMIT 15;

-- KPI 8: Domestic vs foreign vendor spend split, by FY
SELECT
    FY,
    CASE WHEN "Conutry" = 'IN' OR "Conutry" IS NULL THEN 'Domestic' ELSE 'Foreign' END AS vendor_origin,
    ROUND(SUM("PO Basic Value (INR)"), 0) AS total_spend,
    COUNT(*) AS po_count
FROM po_master
GROUP BY FY, vendor_origin
ORDER BY FY, vendor_origin;

-- Bonus KPI 9: MSME / social-category vendor spend share (ties to actual GoI
-- procurement policy -- govt PSUs have MSME purchase targets)
SELECT
    FY,
    CASE
        WHEN "VENDOR TYPE" LIKE 'MICRO%' THEN 'Micro'
        WHEN "VENDOR TYPE" LIKE 'SMALL%' THEN 'Small'
        WHEN "VENDOR TYPE" LIKE 'MED%' THEN 'Medium'
        ELSE 'Others'
    END AS msme_category,
    ROUND(SUM("PO Basic Value (INR)"), 0) AS spend,
    ROUND(100.0 * SUM("PO Basic Value (INR)") / SUM(SUM("PO Basic Value (INR)")) OVER (PARTITION BY FY), 1) AS pct_of_year_spend
FROM po_master
GROUP BY FY, msme_category
ORDER BY FY, msme_category;

-- ============================================================
-- PAGE 3: Bank Guarantee Exposure & Compliance (KPIs 4, 6)
-- ============================================================

-- KPI 4: BG intimation compliance rate (DERIVED from Difference, not the
-- unreliable BEYOND 30 DAYS column), by FY
SELECT
    FY,
    ROUND(100.0 * SUM(CASE WHEN beyond_30_derived = 0 THEN 1 ELSE 0 END) / COUNT(*), 1) AS on_time_pct,
    COUNT(*) AS n
FROM cpbg_intimation_diff
WHERE Difference_num IS NOT NULL
GROUP BY FY
ORDER BY FY;

-- KPI 6: Live BG exposure as of today
SELECT
    ROUND(SUM("Credit Amount"), 0) AS total_live_exposure,
    COUNT(*) AS live_guarantee_count
FROM cpbg_info
WHERE "Start of Term" <= date('now') AND "Term End" >= date('now');

-- BG exposure trend -- total value active at end of each quarter (requires a
-- calendar spine; simplified here as exposure by Term Start quarter)
SELECT
    FY,
    strftime('%Y-Q', "Start of Term") ||
        ((CAST(strftime('%m', "Start of Term") AS INTEGER) - 1) / 3 + 1) AS quarter,
    ROUND(SUM("Credit Amount"), 0) AS new_exposure_value,
    COUNT(*) AS new_guarantees
FROM cpbg_info
WHERE "Start of Term" IS NOT NULL
GROUP BY FY, quarter
ORDER BY quarter;

-- Expiry radar: guarantees expiring in next 90 days
SELECT
    "Applicant" AS vendor,
    "Purchasing Document" AS po_ref,
    "Term End",
    "Credit Amount",
    CAST(julianday("Term End") - julianday('now') AS INTEGER) AS days_to_expiry
FROM cpbg_info
WHERE "Term End" BETWEEN date('now') AND date('now', '+90 days')
ORDER BY "Term End";

-- ============================================================
-- PAGE 4 (stretch): Correlation & Anomaly Detection
-- ============================================================

-- Vendor score vs delay -- does a higher TOTAL SCORE actually predict on-time delivery?
SELECT
    "VENDOR CODE" AS vendor,
    "TOTAL SCORE",
    "D(LT-STD LT)_clean" AS lead_time_deviation
FROM po_master
WHERE "TOTAL SCORE" IS NOT NULL AND "D(LT-STD LT)_clean" IS NOT NULL;

-- PO value outliers by category (simple IQR-style flag -- compute bounds in
-- Python/pandas for the real IQR; this just surfaces the extremes for a first look)
SELECT
    "TYPE OF PROCUREMENT",
    "VENDOR CODE",
    "PO Basic Value (INR)",
    "PO NO"
FROM po_master
WHERE "PO Basic Value (INR)" IS NOT NULL
ORDER BY "PO Basic Value (INR)" DESC
LIMIT 20;
