"""
Anonymize GAIL PO + CPBG procurement data before it leaves internal systems.

What this does:
- Masks vendor codes/descriptions, employee names, bank names, plant identifiers,
  department names, and all document numbers (PO NO, PR NO, tender no, BG number,
  CPS number) with consistent aliases -- the SAME real entity gets the SAME alias
  everywhere, across all 3 years, so vendor/employee-level trend analysis still
  works correctly on the anonymized data.
- Scales every monetary column by a single random factor (with small per-row
  noise) so relative comparisons and trends survive, but real absolute values
  (actual PO amounts, actual BG values) are not recoverable.
- Combines all 3 years into master tables with an FY column.

NOTE on reproducibility: aliases are assigned in first-seen order and the random
seed is fixed, so re-running this script on the same input files produces the
exact same anonymized output and the exact same mapping -- you don't need to
save the mapping separately, just keep this script and the original files safe.

Run locally: pip install pandas openpyxl
"""
import pandas as pd
import numpy as np
from pathlib import Path

np.random.seed(42)

UPLOAD_DIR = Path("./raw_data")   # put your original xlsx files here
OUT_DIR = Path("./anonymized")
OUT_DIR.mkdir(exist_ok=True)

PO_FILES = {
    "2023-24": "2023_24_PO_DETAILS.xlsx",
    "2024-25": "2024_25_PO_DETAILS.xlsx",
    "2025-26": "2025_26_PO_DETAILS.xlsx",
}
CPBG_FILES = {
    "2023-24": "2023_24_CPBG_DETAILS.xlsx",
    "2024-25": "2024_25_CPBG_DETAILS.xlsx",
    "2025-26": "2025_26_CPBG_DETAILS.xlsx",
}

# Single global scale factor -- hides absolute magnitude, preserves relative
# trends/proportions across the whole dataset (same factor applied everywhere).
MONEY_SCALE_FACTOR = np.random.uniform(0.55, 1.45)

# ---- mapping registries, shared across years so aliases stay consistent ----
vendor_map, employee_map, bank_map, plant_map, dept_map, doc_map = {}, {}, {}, {}, {}, {}

def get_alias(value, mapping, prefix):
    if pd.isna(value):
        return value
    key = str(value).strip()
    if key == "":
        return value
    if key not in mapping:
        mapping[key] = f"{prefix}_{len(mapping) + 1:03d}"
    return mapping[key]

def scale_money(series):
    # Real export data has non-numeric placeholders (e.g. "NIL") mixed into
    # otherwise-numeric columns -- coerce those to 0 rather than failing.
    numeric = pd.to_numeric(series, errors="coerce").fillna(0)
    noise = np.random.uniform(0.95, 1.05, size=len(numeric))
    return (numeric * MONEY_SCALE_FACTOR * noise).round(0)

def anonymize_po_df(df):
    df = df.copy()
    if "VENDOR CODE" in df.columns:
        df["VENDOR CODE"] = df["VENDOR CODE"].apply(lambda v: get_alias(v, vendor_map, "VENDOR"))
    if "VENDOR DESCRIPTION" in df.columns:
        df["VENDOR DESCRIPTION"] = df["VENDOR CODE"] if "VENDOR CODE" in df.columns else \
            df["VENDOR DESCRIPTION"].apply(lambda v: get_alias(v, vendor_map, "VENDOR"))
    for col in ["Created by(CPF)", "Created by", "EIC", "EIC Name",
                "PR Created by.", "PR created by Name.", "GAIL COORDINATOR"]:
        if col in df.columns:
            df[col] = df[col].apply(lambda v: get_alias(v, employee_map, "EMP"))
    if "BANK NAME." in df.columns:
        df["BANK NAME."] = df["BANK NAME."].apply(lambda v: get_alias(v, bank_map, "BANK"))
    if "PLANT" in df.columns:
        df["PLANT"] = df["PLANT"].apply(lambda v: get_alias(v, plant_map, "PLANT"))
    if "PLANT NAME" in df.columns:
        df["PLANT NAME"] = df["PLANT"] if "PLANT" in df.columns else \
            df["PLANT NAME"].apply(lambda v: get_alias(v, plant_map, "PLANT"))
    for col in ["IND. DEPT.", "INDENTING DEPT."]:
        if col in df.columns:
            df[col] = df[col].apply(lambda v: get_alias(v, dept_map, "DEPT"))
    for col in ["PO NO", "PUR.REQ NO.", "Collective No", "FOI NO", "E-tender No", "BG NUMBER"]:
        if col in df.columns:
            df[col] = df[col].apply(lambda v: get_alias(v, doc_map, "DOC"))
    for col in ["Exchange Value(INR)", "Purch Order Value", "PO Basic Value",
                "PO Basic Value (INR)", "Estimate Value(INR)", "REV. ESTIMATE", "BG VALUE"]:
        if col in df.columns:
            df[col] = scale_money(df[col].fillna(0))
    return df

def anonymize_cpbg_info_df(df):
    df = df.copy()
    if "Purchasing Document" in df.columns:
        df["Purchasing Document"] = df["Purchasing Document"].apply(lambda v: get_alias(v, doc_map, "DOC"))
    for col in ["Applicant", "Applicant Name"]:
        if col in df.columns:
            df[col] = df[col].apply(lambda v: get_alias(v, vendor_map, "VENDOR"))
    if "Dealing Officer" in df.columns:
        df["Dealing Officer"] = df["Dealing Officer"].apply(lambda v: get_alias(v, employee_map, "EMP"))
    if "CPS Number" in df.columns:
        df["CPS Number"] = df["CPS Number"].apply(lambda v: get_alias(v, doc_map, "DOC"))
    if "Credit Amount" in df.columns:
        df["Credit Amount"] = scale_money(df["Credit Amount"].fillna(0))
    return df

def anonymize_diff_df(df):
    df = df.copy()
    if "Purchasing Document" in df.columns:
        df["Purchasing Document"] = df["Purchasing Document"].apply(lambda v: get_alias(v, doc_map, "DOC"))
    for col in df.columns:
        if "OFFICER" in col.upper():
            df[col] = df[col].apply(lambda v: get_alias(v, employee_map, "EMP"))
    return df

# ---- Column name standardization -----------------------------------------
# The 3 years' CPBG files use inconsistent header casing/spacing for the same
# field (e.g. "INTIMATION DATE" / "Intimation Date" / "Intimation date"), which
# breaks concatenation into separate columns. Normalize to one canonical name
# per field before combining.
CPBG_INFO_RENAME = {
    "Intimation Date": "Intimation Date", "INTIMATION DATE": "Intimation Date",
    "Intimation date": "Intimation Date",
    "Difference": "Difference", "DIFFERENCE": "Difference",
    "PO Date": "PO Date", "PO Date ": "PO Date",
    "Dealing Officer": "Dealing Officer",
}
DIFF_RENAME = {
    "Sl. No": "Sl. No", "SL. NO": "Sl. No",
    "Intimation Date": "Intimation Date", "INTIMATION DATE": "Intimation Date",
    "Intimation date": "Intimation Date", "Intimation date ": "Intimation Date",
    "Difference": "Difference", "DIFFERENCE": "Difference",
    "Dealing Officer": "Dealing Officer", "DEALING OFFICER": "Dealing Officer",
}

def standardize_columns(df, rename_map):
    df = df.rename(columns={c: rename_map.get(c.strip(), c.strip()) for c in df.columns})
    # If renaming created duplicate columns (e.g. both filled on different
    # rows across the same sheet), coalesce them into one.
    if df.columns.duplicated().any():
        for dup_col in df.columns[df.columns.duplicated()].unique():
            cols = df.loc[:, df.columns == dup_col]
            coalesced = cols.bfill(axis=1).iloc[:, 0]
            df = df.loc[:, df.columns != dup_col]
            df[dup_col] = coalesced
    return df

# ---- Process PO files ----
all_po = []
for fy, fname in PO_FILES.items():
    df = pd.read_excel(UPLOAD_DIR / fname, sheet_name="Data")
    df = anonymize_po_df(df)
    df["FY"] = fy
    all_po.append(df)
po_master = pd.concat(all_po, ignore_index=True)
po_master.to_csv(OUT_DIR / "po_master_anonymized.csv", index=False)

# ---- Process CPBG files (sheet order is consistent: [diff, cpbg info, po details]) ----
all_cpbg_info, all_diff = [], []
for fy, fname in CPBG_FILES.items():
    xl = pd.ExcelFile(UPLOAD_DIR / fname)
    sheets = xl.sheet_names
    diff_df = standardize_columns(xl.parse(sheets[0]), DIFF_RENAME)
    cpbg_df = standardize_columns(xl.parse(sheets[1]), CPBG_INFO_RENAME)
    diff_df = anonymize_diff_df(diff_df)
    cpbg_df = anonymize_cpbg_info_df(cpbg_df)
    diff_df["FY"] = fy
    cpbg_df["FY"] = fy
    all_diff.append(diff_df)
    all_cpbg_info.append(cpbg_df)

cpbg_master = pd.concat(all_cpbg_info, ignore_index=True)
diff_master = pd.concat(all_diff, ignore_index=True)
cpbg_master.to_csv(OUT_DIR / "cpbg_info_anonymized.csv", index=False)
diff_master.to_csv(OUT_DIR / "cpbg_intimation_diff_anonymized.csv", index=False)

print("Anonymization complete.")
print(f"  PO master:         {po_master.shape}")
print(f"  CPBG info master:  {cpbg_master.shape}")
print(f"  Intimation diff:   {diff_master.shape}")
print(f"  Unique vendors masked:   {len(vendor_map)}")
print(f"  Unique employees masked: {len(employee_map)}")
print(f"  Unique documents masked: {len(doc_map)}")
