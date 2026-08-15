"""
Clean and derive analysis-ready fields from the anonymized GAIL data, based on
EDA findings (null audit, duplicate-column check, outlier scan) and the CPBG
policy rules from the C&P Procedure Manual.

Run locally: pip install pandas
"""
import pandas as pd
import numpy as np

po = pd.read_csv("po_master_anonymized.csv")
cpbg = pd.read_csv("cpbg_info_anonymized.csv")
diff = pd.read_csv("cpbg_intimation_diff_anonymized.csv")

# ---------------------------------------------------------------------------
# 1) Drop confirmed-redundant columns (per EDA: 100% null, or 100% 1:1
#    duplicate of another column -- keeping the more reliable/granular one)
# ---------------------------------------------------------------------------
po_drop_cols = [
    "SNO",                    # row index, not analytical
    "EIC Name",               # EIC (code) is more reliable: 100% code->name
                               # consistency vs only 37% name->code
    "IND. DEPT.",             # 100% duplicate of INDENTING DEPT.
    "Conutry",                # 100% duplicate of Country Code (also a typo'd name)
    "PR created by Name.",    # 100%/98.2% duplicate of PR Created by.
    "Created by",             # 100% duplicate of Created by(CPF)
    "PLANT NAME",             # duplicate of PLANT
    "PO Ex Rate",             # Exchange Value(INR) already reflects conversion;
                               # only 9/459 rows are non-INR anyway
]
po_clean = po.drop(columns=[c for c in po_drop_cols if c in po.columns])

# TOTAL SCORE is 98.5% null -- keep the column but flag it as unusable for
# any KPI requiring reasonable sample size (Page 4's original "score vs delay"
# idea should be dropped or clearly caveated as n=7)
print(f"NOTE: TOTAL SCORE has only {po['TOTAL SCORE'].notna().sum()} non-null "
      f"values out of {len(po)} -- too sparse for the score-vs-delay KPI as planned.")

cpbg_drop_cols = ["Assignment", "Transaction", "Entered On.1", "Dealing Officer"]
cpbg_clean = cpbg.drop(columns=[c for c in cpbg_drop_cols if c in cpbg.columns])

diff_drop_cols = ["BEYOND 30 DAYS"]  # 100% null, unreliable -- we derive our own
diff_clean = diff.drop(columns=[c for c in diff_drop_cols if c in diff.columns])

# ---------------------------------------------------------------------------
# 2) Derived fields on po_clean
# ---------------------------------------------------------------------------
po_clean["PR Date"] = pd.to_datetime(po_clean["PR Date"], errors="coerce")
po_clean["PO DATE"] = pd.to_datetime(po_clean["PO DATE"], errors="coerce")
po_clean["Schedule Delivery Da"] = pd.to_datetime(po_clean["Schedule Delivery Da"], errors="coerce")
po_clean["USER HOD Release DT"] = pd.to_datetime(po_clean["USER HOD Release DT"], errors="coerce")
po_clean["C&P Release Date"] = pd.to_datetime(po_clean["C&P Release Date"], errors="coerce")

po_clean["cycle_days_pr_to_po"] = (po_clean["PO DATE"] - po_clean["PR Date"]).dt.days
po_clean["approval_lag_days"] = (po_clean["PO DATE"] - po_clean["C&P Release Date"]).dt.days

# Flag logically-impossible negative cycle times rather than silently
# including them in averages (6 rows found in EDA)
po_clean["cycle_time_data_flag"] = np.where(
    po_clean["cycle_days_pr_to_po"] < 0, "NEGATIVE_CYCLE_CHECK_DATA", "OK"
)

# Clean D(LT-STD LT) -- SAP trailing-minus format, already handled in the SQL
# loader, replicated here for a fully self-contained cleaned CSV
def clean_trailing_minus(val):
    if pd.isna(val):
        return None
    s = str(val).strip()
    if s == "" or s.upper() in ("NIL", "NA", "N/A", "-"):
        return None
    if s.endswith("-"):
        s = "-" + s[:-1].strip()
    try:
        return float(s)
    except ValueError:
        return None

po_clean["lead_time_deviation_days"] = po_clean["D(LT-STD LT)"].apply(clean_trailing_minus)

# ---------------------------------------------------------------------------
# 3) CPBG compliance fields, grounded in C&P Procedure Clause 3.2.1 / 3.2.1A
# ---------------------------------------------------------------------------
cpbg_clean["PO Date"] = pd.to_datetime(cpbg_clean["PO Date"], errors="coerce")
cpbg_clean["Start of Term"] = pd.to_datetime(cpbg_clean["Start of Term"], errors="coerce")
cpbg_clean["Term End"] = pd.to_datetime(cpbg_clean["Term End"], errors="coerce")

# Join to po_clean to get PO value and schedule delivery date for the
# compliance checks (join key: Purchasing Document <-> PO NO, both anonymized
# consistently by the earlier anonymization script)
po_lookup = po_clean[["PO NO", "PO Basic Value (INR)", "Schedule Delivery Da", "BG VALUE"]].drop_duplicates("PO NO")
cpbg_clean = cpbg_clean.merge(
    po_lookup, left_on="Purchasing Document", right_on="PO NO", how="left"
)

# KPI 6: CPBG value compliance -- 3% for orders after the 31.03.2023
# amendment, 10% for orders before it (Clause 3.2.1A)
CUTOFF = pd.Timestamp("2023-04-01")
cpbg_clean["expected_cpbg_pct"] = np.where(cpbg_clean["PO Date"] < CUTOFF, 10.0, 3.0)
cpbg_clean["actual_cpbg_pct"] = (
    cpbg_clean["Credit Amount"] / cpbg_clean["PO Basic Value (INR)"] * 100
)
# Allow a small tolerance (0.5 pp) for rounding in the original data
cpbg_clean["cpbg_value_compliant"] = (
    (cpbg_clean["actual_cpbg_pct"] >= cpbg_clean["expected_cpbg_pct"] - 0.5)
)

# KPI 7: CPBG duration compliance -- Term End must be >= Schedule Delivery +
# 90 days (Clause 3.2.1 Note ii)
cpbg_clean["required_term_end"] = cpbg_clean["Schedule Delivery Da"] + pd.Timedelta(days=90)
cpbg_clean["cpbg_duration_compliant"] = cpbg_clean["Term End"] >= cpbg_clean["required_term_end"]

# ---------------------------------------------------------------------------
# 4) Intimation compliance (KPI 5), derived from Difference, not the blank
#    BEYOND 30 DAYS column (Clause 3.2.1 Note iii -- 30-day intimation rule)
# ---------------------------------------------------------------------------
diff_clean["Difference_num"] = pd.to_numeric(diff_clean["Difference"], errors="coerce")
diff_clean["intimation_compliant"] = diff_clean["Difference_num"] <= 30

# ---------------------------------------------------------------------------
# Save cleaned, analysis-ready outputs
# ---------------------------------------------------------------------------
po_clean.to_csv("po_master_cleaned.csv", index=False)
cpbg_clean.to_csv("cpbg_info_cleaned.csv", index=False)
diff_clean.to_csv("cpbg_intimation_diff_cleaned.csv", index=False)

print("\nCleaned files saved:")
print(f"  po_master_cleaned.csv:            {po_clean.shape}")
print(f"  cpbg_info_cleaned.csv:            {cpbg_clean.shape}")
print(f"  cpbg_intimation_diff_cleaned.csv: {diff_clean.shape}")
print(f"\nCPBG value compliance rate: {cpbg_clean['cpbg_value_compliant'].mean()*100:.1f}%")
print(f"CPBG duration compliance rate: {cpbg_clean['cpbg_duration_compliant'].mean()*100:.1f}%")
print(f"Intimation compliance rate (<=30 days): {diff_clean['intimation_compliant'].mean()*100:.1f}%")
print(f"Rows with negative cycle time (data quality flag): {(po_clean['cycle_time_data_flag']=='NEGATIVE_CYCLE_CHECK_DATA').sum()}")
