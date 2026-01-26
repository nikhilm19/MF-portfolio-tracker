# analysis.py
import pandas as pd
import os
import re
from config import FUND_CONFIG, YEARS, MONTHS

def load_fund_data(fund_name):
    """Helper to load a specific fund's excel file"""
    file_path = FUND_CONFIG[fund_name]["file"]
    if not os.path.exists(file_path):
        return None
    
    df = pd.read_excel(file_path)
    # Clean ISIN - This is the primary key for matching
    if "ISIN" in df.columns:
        df["ISIN"] = df["ISIN"].astype(str).str.strip().str.upper()
    # Clean Stock Names - remove special characters and extra whitespace
    if "Stock Name" in df.columns:
        df["Stock Name"] = df["Stock Name"].astype(str).str.strip()
        # Remove special characters but keep alphanumeric, spaces, and hyphens
        df["Stock Name"] = df["Stock Name"].str.replace(r'[^\w\s\-&]', '', regex=True)
        df["Stock Name"] = df["Stock Name"].str.replace(r'\s+', ' ', regex=True)  # Collapse multiple spaces
    return df

def get_latest_month_column(df):
    """Finds the most recent data column in a dataframe"""
    qty_cols = [c for c in df.columns if "Qty_" in c]
    if not qty_cols:
        return None
        
    def get_month_index(col_name):
        m_name = col_name.replace("Qty_", "").replace(f"_{YEARS[0]}", "")
        return MONTHS.index(m_name) if m_name in MONTHS else -1
    
    return sorted(qty_cols, key=get_month_index)[-1]


def compare_portfolios(fund_a_name, fund_b_name):
    """
    Compares two funds and returns a FULL merged view of both portfolios.
    """
    # 1. Load Data
    df_a = load_fund_data(fund_a_name)
    df_b = load_fund_data(fund_b_name)
    
    if df_a is None or df_b is None:
        return {"error": "One or both fund files are missing. Please sync them first."}

    # 2. Get Latest Data Columns
    col_a = get_latest_month_column(df_a)
    col_b = get_latest_month_column(df_b)
    
    if not col_a or not col_b:
        return {"error": "No monthly data found in files."}

    # 3. Prepare Subsets (ISIN, Name, Qty)
    #    We rename cols immediately to avoid confusion during merge
    qty_a_label = f"Qty {fund_a_name}"
    qty_b_label = f"Qty {fund_b_name}"
    
    # Filter for active stocks (>0) before merging to keep it clean
    sub_a = df_a[df_a[col_a] > 0][["ISIN", "Stock Name", col_a]].rename(columns={col_a: qty_a_label})
    sub_b = df_b[df_b[col_b] > 0][["ISIN", "Stock Name", col_b]].rename(columns={col_b: qty_b_label})
    
    # 4. Perform Full Outer Merge (The "Master List")
    merged_df = pd.merge(sub_a, sub_b, on="ISIN", how="outer", suffixes=('_A', '_B'))
    
    # 5. Clean Up Data
    #    Coalesce Stock Names: If Name is missing in A (because it's unique to B), take it from B
    merged_df["Stock Name"] = merged_df["Stock Name_A"].fillna(merged_df["Stock Name_B"])
    merged_df.drop(columns=["Stock Name_A", "Stock Name_B"], inplace=True)
    
    #    Fill NaN Quantities with 0
    merged_df[[qty_a_label, qty_b_label]] = merged_df[[qty_a_label, qty_b_label]].fillna(0)
    
    # 6. Determine "Status" (Overlap vs Unique)
    def get_status(row):
        if row[qty_a_label] > 0 and row[qty_b_label] > 0:
            return "Overlap"
        elif row[qty_a_label] > 0:
            return f"Unique to {fund_a_name}"
        else:
            return f"Unique to {fund_b_name}"

    merged_df["Status"] = merged_df.apply(get_status, axis=1)
    
    # 7. Calculate Stats
    counts = merged_df["Status"].value_counts()
    
    return {
        "merged_df": merged_df,
        "stats": {
            "common": counts.get("Overlap", 0),
            "unique_a": counts.get(f"Unique to {fund_a_name}", 0),
            "unique_b": counts.get(f"Unique to {fund_b_name}", 0)
        },
        "col_a": qty_a_label,
        "col_b": qty_b_label
    }