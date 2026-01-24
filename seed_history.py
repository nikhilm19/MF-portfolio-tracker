import pandas as pd
import requests
from bs4 import BeautifulSoup
from io import BytesIO
import re
import os
import time
import xlsxwriter

# --- CONFIGURATION ---
DISCLOSURE_PAGE_URL = "https://amc.ppfas.com/downloads/portfolio-disclosure/"
OUTPUT_FILE = "PPFCF_Portfolio_Dashboard_2025.xlsx"
YEARS_TO_PROCESS = [2025] 
MONTHS = [
    "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December"
]

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
}

# ===========================
# 1. URL FINDER
# ===========================
def get_dynamic_url(month, year):
    print(f"🔎 Scanning for: {month} {year}...")
    try:
        response = requests.get(DISCLOSURE_PAGE_URL, headers=HEADERS, timeout=15)
        soup = BeautifulSoup(response.content, 'html.parser')
        links = soup.find_all('a', href=True)
        
        short_month = month[:3].lower()
        search_terms = [short_month, str(year), "ppfcf"]
        
        for link in links:
            href = link['href']
            text = link.text.strip().lower()
            full_str = (href + text).lower()
            
            if all(term in full_str for term in search_terms):
                if re.search(r'\.xlsx?($|\?)', href, re.IGNORECASE):
                    final_url = href if href.startswith('http') else f"https://amc.ppfas.com{href}"
                    return final_url
        return None
    except Exception as e:
        print(f"   ⚠️ Connection Error: {e}")
        return None

# ===========================
# 2. NUCLEAR DATA EXTRACTION (REGEX HUNTER)
# ===========================
def fetch_month_data(month, year):
    url = get_dynamic_url(month, year)
    if not url: 
        print(f"   ⚠️ URL not found for {month} {year}")
        return None
    
    try:
        resp = requests.get(url, headers=HEADERS, timeout=30)
        
        # Load Raw Data (No Header assumption)
        try: 
            all_sheets = pd.read_excel(BytesIO(resp.content), header=None, sheet_name=None, engine='openpyxl')
        except: 
            all_sheets = pd.read_excel(BytesIO(resp.content), header=None, sheet_name=None, engine='xlrd')

        # We will merge ALL sheets into one big search space to be safe
        full_df = pd.concat(all_sheets.values(), ignore_index=True)
        
        valid_holdings = []
        
        # Iterate through every single row in the raw file
        for idx, row in full_df.iterrows():
            # Convert row to a list of strings
            row_vals = [str(x).strip() for x in row.values if pd.notna(x)]
            row_str = " ".join(row_vals)
            
            # 1. STOP IF ARBITRAGE/TOTAL FOUND
            # This prevents us from reading the wrong sections
            if "arbitrage" in row_str.lower() or "grand total" in row_str.lower():
                # If we already found data, stop. If not, keep looking (it might be a top header).
                if len(valid_holdings) > 0:
                    break

            # 2. FIND ISIN (The Anchor)
            # Regex: Starts with INE/INF, followed by 9 alphanumeric chars, ends with a digit
            isin_match = re.search(r'\b(INE|INF)[A-Z0-9]{9}\b', row_str)
            
            if isin_match:
                isin = isin_match.group(0)
                
                # 3. FIND STOCK NAME (Strategy: It's usually the longest text string in the row)
                # Filter out the ISIN itself and short headers
                possible_names = [s for s in row_vals if len(s) > 4 and s != isin and not re.search(r'\d', s)]
                stock_name = possible_names[0] if possible_names else "Unknown Stock"
                
                # 4. FIND QUANTITY (Strategy: Look for large numbers)
                # We assume Quantity is a number > 100 (to avoid percentages or face value)
                qty = 0
                for val in row_vals:
                    # Remove commas
                    clean_val = val.replace(",", "")
                    try:
                        num = float(clean_val)
                        # Heuristic: Quantity is usually an integer > 0. 
                        # We pick the largest integer-like number in the row to be safe.
                        if num > 0 and num.is_integer(): 
                             # If we found a bigger number, assume that's the quantity (Quantity > Market Value usually)
                             # BUT: Sometimes Market Value (in Lakhs) is smaller than Quantity. 
                             # Heuristic: The FIRST large number after the ISIN is often Quantity.
                             qty = num
                             break # Take the first valid quantity found
                    except:
                        continue
                
                if qty > 0:
                    valid_holdings.append({
                        "Stock Name": stock_name,
                        "ISIN": isin,
                        f"Qty_{month}_{year}": qty
                    })

        if not valid_holdings:
            print(f"   ⚠️ Nuclear scan failed for {month} {year}")
            return None
            
        print(f"   ☢️ Nuclear scan found {len(valid_holdings)} stocks in {month} {year}")
        
        # Create DataFrame
        df = pd.DataFrame(valid_holdings)
        
        # Dedup
        qty_col = f"Qty_{month}_{year}"
        df = df.groupby("ISIN", as_index=False).agg({"Stock Name": "first", qty_col: "sum"})
        
        return df

    except Exception as e:
        print(f"   ⚠️ Error processing {month} {year}: {e}")
        return None

# ===========================
# 3. MERGE LOGIC
# ===========================
def build_portfolio_history_data():
    if os.path.exists(OUTPUT_FILE):
        print(f"📂 Loading existing data from {OUTPUT_FILE}...")
        master_df = pd.read_excel(OUTPUT_FILE)
        if "ISIN" in master_df.columns:
             master_df["ISIN"] = master_df["ISIN"].astype(str).str.strip()
             master_df = master_df.drop_duplicates(subset=["ISIN"])
    else:
        print("🆕 Starting fresh data collection...")
        master_df = pd.DataFrame(columns=["ISIN", "Stock Name"])

    data_updated = False
    
    for year in YEARS_TO_PROCESS:
        for month in MONTHS:
            col_name = f"Qty_{month}_{year}"
            if col_name in master_df.columns: continue 
            
            monthly_df = fetch_month_data(month, year)
            
            if monthly_df is not None:
                print(f"   ➕ Merging Data: {month} {year}")
                master_df["ISIN"] = master_df["ISIN"].astype(str)
                monthly_df["ISIN"] = monthly_df["ISIN"].astype(str)
                
                try:
                    master_df = pd.merge(master_df, monthly_df, on="ISIN", how="outer", suffixes=("", "_new"))
                    
                    if "Stock Name_new" in master_df.columns:
                        master_df["Stock Name"] = master_df["Stock Name"].fillna(master_df["Stock Name_new"])
                        master_df.drop(columns=["Stock Name_new"], inplace=True)
                    
                    if f"{col_name}_new" in master_df.columns:
                            master_df[col_name] = master_df[f"{col_name}_new"]
                            master_df.drop(columns=[f"{col_name}_new"], inplace=True)
                    
                    data_updated = True
                except Exception as e: 
                    print(f"   ❌ Merge Failed: {e}")
                time.sleep(0.5)

    if data_updated:
        master_df.to_excel(OUTPUT_FILE, index=False)
        print("✅ Data collection complete.")
        return True
    else:
        print("✅ No new data found.")
        return False

# ===========================
# 4. VISUALIZATION
# ===========================
def create_dashboard_visuals(filename):
    print("\n🎨 Generating Visual Dashboard...")
    try:
        df = pd.read_excel(filename)
        qty_cols = [c for c in df.columns if c.startswith("Qty_")]
        for col in qty_cols: df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
        latest_col = qty_cols[-1] if qty_cols else None
        
        writer = pd.ExcelWriter(filename, engine='xlsxwriter')
        workbook = writer.book

        sheet_data = 'Portfolio History'
        df.to_excel(writer, sheet_name=sheet_data, index=False)
        ws_data = writer.sheets[sheet_data]
        if qty_cols:
            first_idx = df.columns.get_loc(qty_cols[0])
            last_idx = df.columns.get_loc(qty_cols[-1])
            ws_data.conditional_format(1, first_idx, len(df)+1, last_idx, {
                'type': '3_color_scale', 'min_color': "#FFFFFF", 'mid_color': "#EBF1DE", 'max_color': "#63C384"
            })
            ws_data.freeze_panes(1, 2)
            ws_data.set_column(1, 1, 40)

        if latest_col:
            top_holdings = df[['Stock Name', latest_col]].sort_values(by=latest_col, ascending=False).head(10)
            top_holdings = top_holdings[top_holdings[latest_col] > 0]
            sheet_dash = 'Dashboard'
            ws_dash = workbook.add_worksheet(sheet_dash)
            header_fmt = workbook.add_format({'bold': True, 'bg_color': '#D7E4BC', 'border': 1})
            
            ws_dash.write_string(0, 0, "Top 10 Holdings", header_fmt)
            ws_dash.write_row(1, 0, top_holdings.columns, header_fmt)
            for i, row in enumerate(top_holdings.values): ws_dash.write_row(i + 2, 0, row)

            chart = workbook.add_chart({'type': 'pie'})
            chart.add_series({
                'name': f'Top 10 Holdings ({latest_col})',
                'categories': [sheet_dash, 2, 0, 1 + len(top_holdings), 0],
                'values':     [sheet_dash, 2, 1, 1 + len(top_holdings), 1],
                'data_labels': {'value': False, 'percentage': True, 'position': 'outside'},
            })
            chart.set_title({'name': f"Top 10 Holdings\n(as of {latest_col.replace('Qty_', '').replace('_', ' ')})"})
            chart.set_size({'width': 600, 'height': 450})
            ws_dash.insert_chart('D2', chart)

        writer.close()
        print(f"🎉 Dashboard Updated: {filename}")
    except PermissionError:
        print(f"⚠️  ERROR: Close '{filename}' so I can save the dashboard!")

if __name__ == "__main__":
    if build_portfolio_history_data():
        create_dashboard_visuals(OUTPUT_FILE)
    elif os.path.exists(OUTPUT_FILE):
        create_dashboard_visuals(OUTPUT_FILE)