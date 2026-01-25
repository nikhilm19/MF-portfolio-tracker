import pandas as pd
import requests
from io import BytesIO
import datetime
import calendar
from dateutil.relativedelta import relativedelta
import warnings
import os as os

warnings.filterwarnings("ignore")

# ===========================
# ⚙️ CONFIGURATION
# ===========================
FUND_NAME = "HDFC Nifty 50 Index Fund"
BASE_URL = "https://files.hdfcfund.com/s3fs-public"
OUTPUT_FILE = "HDFC_Nifty50_Dashboard.xlsx"

# Target Data
YEARS = [2025]
MONTHS = [
    "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December"
]

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
}

# ===========================
# 🧠 SMART URL GENERATOR
# ===========================
def generate_hdfc_url(month_str, year):
    # 1. Convert Month Name to Number (e.g., "December" -> 12)
    month_num = datetime.datetime.strptime(month_str, "%B").month
    
    # 2. Calculate the "Data Date" (Last day of the month)
    #    e.g., Feb 2025 -> 28th, Feb 2024 -> 29th
    last_day = calendar.monthrange(year, month_num)[1]
    
    # 3. Calculate "Folder Date" (Usually uploaded the NEXT month)
    #    e.g., Data for Dec 2025 is in '2026-01' folder
    date_obj = datetime.date(year, month_num, 1)
    upload_date = date_obj + relativedelta(months=1)
    
    folder_path = upload_date.strftime("%Y-%m") # "2026-01"
    
    # 4. Construct File Name
    # Pattern: Monthly HDFC Nifty 50 Index Fund - 31 December 2025.xlsx
    filename = f"Monthly {FUND_NAME} - {last_day} {month_str} {year}.xlsx"
    
    # URL 1: Standard Pattern (Next Month Folder)
    url1 = f"{BASE_URL}/{folder_path}/{filename.replace(' ', '%20')}"
    
    # URL 2: Fallback (Current Month Folder - sometimes they upload early)
    folder_fallback = date_obj.strftime("%Y-%m")
    url2 = f"{BASE_URL}/{folder_fallback}/{filename.replace(' ', '%20')}"
    
    return [url1, url2]

def fetch_file(month, year):
    urls = generate_hdfc_url(month, year)
    
    for url in urls:
        try:
            print(f"   🔎 Trying: {url} ...")
            # Use 'stream=True' to check headers without downloading huge files
            response = requests.get(url, headers=HEADERS, timeout=15, stream=True)
            
            if response.status_code == 200:
                print("   ✅ File found! Downloading...")
                return BytesIO(response.content)
        except Exception as e:
            print(f"   ⚠️ Error: {e}")
            
    print(f"   ❌ Could not find file for {month} {year}")
    return None

# ===========================
# ⚙️ EXCEL PARSER
# ===========================
def process_hdfc_data(file_content, month, year):
    try:
        # HDFC files often have sheet names like "HDFCNIFTY" or "Sheet1". 
        # We cannot guess it, so we load ALL sheets and search for the fund name.
        xls = pd.ExcelFile(file_content)
        
        target_df = None
        header_row = None
        
        for sheet in xls.sheet_names:
            df = pd.read_excel(xls, sheet_name=sheet, header=None)
            
            # Check first 5 rows for Fund Name
            # HDFC usually puts fund name in Row 1 or 2
            start_str = df.iloc[0:5].astype(str).to_string().lower()
            
            if "nifty 50 index fund" in start_str:
                target_df = df
                # Find the actual header row (contains "ISIN" and "Name")
                for idx, row in df.iterrows():
                    r_str = row.astype(str).str.cat(sep=" ").lower()
                    if "isin" in r_str and "name" in r_str and "quantity" in r_str:
                        header_row = idx
                        break
                break
        
        if target_df is None or header_row is None:
            print("   ⚠️ Could not identify Fund/Header in Excel.")
            return None

        # --- EXTRACT DATA ---
        # Set Header
        target_df.columns = target_df.iloc[header_row]
        df_clean = target_df.iloc[header_row+1:].copy()
        
        # Rename Columns (Normalize)
        col_map = {}
        for c in df_clean.columns:
            val = str(c).lower().strip()
            if "isin" in val: col_map[c] = "ISIN"
            elif "name" in val and "instrument" in val: col_map[c] = "Stock Name"
            elif "quantity" in val: col_map[c] = f"Qty_{month}_{year}"
            
        df_clean = df_clean.rename(columns=col_map)
        
        # Filter for Equity (ISIN starts with INE)
        valid_rows = []
        for idx, row in df_clean.iterrows():
            isin = str(row.get("ISIN", "")).strip().upper()
            name = str(row.get("Stock Name", "")).strip()
            
            if isin.startswith("INE"):
                try:
                    qty = float(str(row.get(f"Qty_{month}_{year}", 0)).replace(",", ""))
                    if qty > 0:
                        valid_rows.append({
                            "Stock Name": name,
                            "ISIN": isin,
                            f"Qty_{month}_{year}": qty
                        })
                except: continue
                
        if not valid_rows:
            print("   ⚠️ No valid equity rows found.")
            return None
            
        return pd.DataFrame(valid_rows)

    except Exception as e:
        print(f"   ⚠️ Parsing Error: {e}")
        return None

# ===========================
# 🚀 MAIN EXECUTION
# ===========================
if __name__ == "__main__":
    if os.path.exists(OUTPUT_FILE):
        master_df = pd.read_excel(OUTPUT_FILE)
    else:
        master_df = pd.DataFrame(columns=["ISIN", "Stock Name"])

    for year in YEARS:
        for month in MONTHS:
            col_name = f"Qty_{month}_{year}"
            if col_name in master_df.columns: continue

            print(f"Processing: {month} {year}")
            file_data = fetch_file(month, year)
            
            if file_data:
                new_df = process_hdfc_data(file_data, month, year)
                if new_df is not None:
                    # Merge Logic
                    master_df = pd.merge(master_df, new_df, on="ISIN", how="outer", suffixes=("", "_new"))
                    
                    # Fill Metadata
                    if "Stock Name_new" in master_df.columns:
                        master_df["Stock Name"] = master_df["Stock Name"].fillna(master_df["Stock Name_new"])
                        master_df.drop(columns=["Stock Name_new"], inplace=True)
                    
                    # Fill Quantity
                    if f"{col_name}_new" in master_df.columns:
                        master_df[col_name] = master_df[f"{col_name}_new"].fillna(0)
                        master_df.drop(columns=[f"{col_name}_new"], inplace=True)
                        
                    print(f"   ✅ Merged {len(new_df)} records.")

    master_df.to_excel(OUTPUT_FILE, index=False)
    print("🎉 Done!")