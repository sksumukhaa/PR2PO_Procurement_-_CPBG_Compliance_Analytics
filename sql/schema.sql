-- Schema reference for gail_procurement.db (built by load_to_sqlite.py)
-- This isn't a CREATE TABLE script -- load_to_sqlite.py builds tables directly
-- from the cleaned CSVs via pandas .to_sql(). This file documents the schema
-- for reference and for setting up primary keys / indexes if you want them.

-- po_master (459 rows, 2023-24 through 2025-26)
--   Key columns: "PO NO" (masked), "PR Date", "USER HOD Release DT",
--   "C&P Release Date", "PO DATE", "Schedule Delivery Da" -- the 5-stage
--   lifecycle. "VENDOR CODE" (masked, consistent across years), "VENDOR TYPE"
--   (MSME/social-category classification), "PO Basic Value (INR)" (scaled),
--   "D(LT-STD LT)_clean" (lead time deviation, cleaned), "TOTAL SCORE"
--   (vendor evaluation score), "FY" (2023-24 / 2024-25 / 2025-26).

-- cpbg_info (71 rows)
--   Key columns: "Purchasing Document" (masked, joins to po_master."PO NO"),
--   "Applicant" (masked vendor), "Credit Amount" (scaled), "Start of Term",
--   "Term End", "BG claim Expiry date", "Status of Deal", "FY".

-- cpbg_intimation_diff (83 rows)
--   Key columns: "Purchasing Document" (masked, joins to po_master."PO NO"),
--   "Difference_num" (days between PO/FOI and intimation, cleaned numeric),
--   "beyond_30_derived" (1/0 flag we computed -- do NOT use the original
--   "BEYOND 30 DAYS" column, it's blank/unreliable in the source data), "FY".

CREATE INDEX IF NOT EXISTS idx_po_vendor ON po_master("VENDOR CODE");
CREATE INDEX IF NOT EXISTS idx_po_fy ON po_master(FY);
CREATE INDEX IF NOT EXISTS idx_cpbg_doc ON cpbg_info("Purchasing Document");
CREATE INDEX IF NOT EXISTS idx_diff_doc ON cpbg_intimation_diff("Purchasing Document");
