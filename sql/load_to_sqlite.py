"""
Load the 3 anonymized CSVs into a single SQLite database, with cleaning for
known data quirks (SAP-style trailing-minus numbers, whitespace padding).

Run locally: pip install pandas
Expects po_master_anonymized.csv, cpbg_info_anonymized.csv,
cpbg_intimation_diff_anonymized.csv in the same folder as this script.
"""
import sqlite3
import pandas as pd
import re

def clean_trailing_minus_number(val):
    """SAP exports sometimes write negative numbers as '29-' instead of '-29',
    plus stray whitespace. Converts to a proper float, NaN if unparseable."""
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

po = pd.read_csv("po_master_anonymized.csv")
cpbg = pd.read_csv("cpbg_info_anonymized.csv")
diff = pd.read_csv("cpbg_intimation_diff_anonymized.csv")

# Clean the lead-time deviation column
po["D(LT-STD LT)_clean"] = po["D(LT-STD LT)"].apply(clean_trailing_minus_number)

# Parse dates explicitly (already ISO format, but coerce errors to NaT rather
# than silently failing later in SQL)
DATE_COLS_PO = ["PO DATE", "PR Date", "USER HOD Release DT", "C&P Release Date",
                 "Schedule Delivery Da", "FOI DATE", "TBO DATE", "BG EXP."]
for col in DATE_COLS_PO:
    if col in po.columns:
        po[col] = pd.to_datetime(po[col], errors="coerce").dt.strftime("%Y-%m-%d")

DATE_COLS_CPBG = ["PO Date", "FOI Date", "Intimation Date", "Entered On",
                   "Entered On.1", "Start of Term", "Term End", "BG claim Expiry date"]
for col in DATE_COLS_CPBG:
    if col in cpbg.columns:
        cpbg[col] = pd.to_datetime(cpbg[col], errors="coerce").dt.strftime("%Y-%m-%d")

for col in ["Intimation Date", "Entered On"]:
    if col in diff.columns:
        diff[col] = pd.to_datetime(diff[col], errors="coerce").dt.strftime("%Y-%m-%d")

# Derive the 30-day compliance flag ourselves from Difference, since the
# manual BEYOND 30 DAYS column is unreliable/blank in the source data
diff["Difference_num"] = pd.to_numeric(diff["Difference"], errors="coerce")
diff["beyond_30_derived"] = diff["Difference_num"] > 30

conn = sqlite3.connect("gail_procurement.db")
po.to_sql("po_master", conn, if_exists="replace", index=False)
cpbg.to_sql("cpbg_info", conn, if_exists="replace", index=False)
diff.to_sql("cpbg_intimation_diff", conn, if_exists="replace", index=False)
conn.commit()
conn.close()

print("Loaded into gail_procurement.db:")
print(f"  po_master:            {po.shape}")
print(f"  cpbg_info:             {cpbg.shape}")
print(f"  cpbg_intimation_diff:  {diff.shape}")
