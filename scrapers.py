import requests
import pandas as pd
import re
from bs4 import BeautifulSoup
from io import BytesIO
import calendar
import datetime
import warnings
from config import FUND_CONFIG, HEADERS

warnings.filterwarnings("ignore")

# --- HELPER: Month Mapping for Nippon ---
MONTH_ABBR = {
    "January": "Jan", "February": "Feb", "March": "Mar", "April": "Apr",
    "May": "May", "June": "Jun", "July": "Jul", "August": "Aug",
    "September": "Sep", "October": "Oct", "November": "Nov", "December": "Dec"
}

# --- PPFAS ENGINE (Restored from your working version) ---
def fetch_ppfas(month, year):
    try:
        conf = FUND_CONFIG["PPFAS Flexi Cap"]
        response = requests.get(conf["url"], headers=HEADERS, timeout=10)
        soup = BeautifulSoup(response.content, 'html.parser')
        
        target_url = None
        search_terms = [month[:3].lower(), str(year), "ppfcf"]
        for link in soup.find_all('a', href=True):
            full_str = (link['href'] + link.text).lower()
            if all(t in full_str for t in search_terms) and re.search(r'\.xlsx?($|\?)', link['href']):
                target_url = link['href'] if link['href'].startswith('http') else f"https://amc.ppfas.com{link['href']}"
                break
        
        if not target_url: return None

        resp = requests.get(target_url, headers=HEADERS, timeout=30)
        try: all_sheets = pd.read_excel(BytesIO(resp.content), header=None, sheet_name=None, engine='openpyxl')
        except: all_sheets = pd.read_excel(BytesIO(resp.content), header=None, sheet_name=None, engine='xlrd')
        
        full_df = pd.concat(all_sheets.values(), ignore_index=True)
        valid_holdings = []
        for _, row in full_df.iterrows():
            row_str = row.astype(str).str.cat(sep=" ").lower()
            if "arbitrage" in row_str or "grand total" in row_str:
                if valid_holdings: break
            
            isin_match = re.search(r'\b(ine|inf)[a-z0-9]{9}\b', row_str)
            if isin_match:
                row_vals = [str(x).strip() for x in row.values if pd.notna(x)]
                isin = isin_match.group(0)
                name = next((s for s in row_vals if len(s) > 4 and s != isin and not re.search(r'\d', s)), "Unknown")
                
                # Extract numbers
                numbers = []
                nav_pct = 0
                for v in row_vals:
                    if "%" in str(v):
                        try:
                            pct_val = float(str(v).replace(",","").replace("%","").strip())
                            if 0 < pct_val <= 100: nav_pct = pct_val
                        except: pass
                    else:
                        try:
                            num_val = float(str(v).replace(",",""))
                            if num_val > 0: numbers.append(num_val)
                        except: pass
                
                qty = numbers[0] if len(numbers) > 0 else 0
                market_val = numbers[1] if len(numbers) > 1 else 0
                
                if nav_pct == 0 and len(numbers) > 2:
                    nav_pct = numbers[2]
                    
                if qty > 0: valid_holdings.append({"Stock Name": name, "ISIN": isin, f"Qty_{month}_{year}": qty, f"MarketValue_{month}_{year}": market_val, f"NavPct_{month}_{year}": nav_pct})
        
        if not valid_holdings: return None
        df = pd.DataFrame(valid_holdings)
        agg_dict = {"Stock Name": "first", f"Qty_{month}_{year}": "sum"}
        # Optional columns aggregation
        if f"MarketValue_{month}_{year}" in df.columns: agg_dict[f"MarketValue_{month}_{year}"] = "sum"
        if f"NavPct_{month}_{year}" in df.columns: agg_dict[f"NavPct_{month}_{year}"] = "first"
        
        return df.groupby("ISIN", as_index=False).agg(agg_dict)
    except: return None

# --- NIPPON ENGINE (Fixed URL & Safer Column Parsing) ---
def fetch_nippon(month, year):
    try:
        conf = FUND_CONFIG["Nippon India Small Cap"]
        # Use precise mapping (e.g., July -> Jul, not July)
        mon_abbr = MONTH_ABBR.get(month, month[:3])
        yy = str(year)[-2:]
        target_url = None
        
        # 1. Try Specific URL Patterns (Fastest)
        urls = [
            f"https://mf.nipponindiaim.com/Funds/PortfolioDisclosures/MonthlyPortfolio/NIMF-MONTHLY-PORTFOLIO-{mon_abbr}-{yy}.xls",
            f"https://mf.nipponindiaim.com/Funds/PortfolioDisclosures/MonthlyPortfolio/NIMF-MONTHLY-PORTFOLIO-{mon_abbr.upper()}-{yy}.xls",
            f"https://mf.nipponindiaim.com/InvestorServices/FactsheetsDocuments/NIMF-MONTHLY-PORTFOLIO-{mon_abbr}-{yy}.xls"
        ]
        
        for u in urls:
            try:
                if requests.head(u, headers=HEADERS, timeout=5, verify=False).status_code == 200:
                    target_url = u
                    break
            except: continue

        # 2. Fallback: Regex Search on Website (If direct URLs fail)
        if not target_url:
            try:
                resp = requests.get(conf["url"], headers=HEADERS, timeout=10, verify=False)
                # Regex to find links matching month/year
                regex = fr'href=["\']([^"\']*(?:monthly|portfolio)[^"\']*(?:{month}|{mon_abbr})[^"\']*(?:{year}|{yy})[^"\']*\.xls[x]?)["\']'
                matches = re.findall(regex, resp.text, re.IGNORECASE)
                if matches:
                    link = matches[0]
                    target_url = conf["base_url"] + link if link.startswith("/") else link
            except: pass
        
        if not target_url: return None

        print(f"   Fetching Nippon from: {target_url}")
        resp = requests.get(target_url, headers=HEADERS, timeout=30, verify=False)
        
        # Parse Excel
        try: df = pd.read_excel(BytesIO(resp.content), sheet_name=conf["sheet"], header=None, engine='openpyxl')
        except: 
            try: df = pd.read_excel(BytesIO(resp.content), sheet_name=conf["sheet"], header=None, engine='xlrd')
            except:
                # Last resort: Try finding sheet by name if config name failed
                xls = pd.ExcelFile(BytesIO(resp.content))
                sheet = next((s for s in xls.sheet_names if "SC" in s or "Small" in s), xls.sheet_names[0])
                df = pd.read_excel(xls, sheet_name=sheet, header=None)

        # Locate Header Row
        header_idx = None
        for idx, row in df.iterrows():
            row_str = row.astype(str).str.cat(sep=' ').lower()
            if "name of the instrument" in row_str or "isin" in row_str: 
                header_idx = idx
                break
        
        if header_idx is None: return None

        df.columns = df.iloc[header_idx]
        df = df.iloc[header_idx+1:].copy()
        
        # Robust Column Mapping
        col_map = {}
        for c in df.columns:
            c_lower = str(c).lower().strip()
            if "name" in c_lower and "instrument" in c_lower:
                col_map[c] = "Stock Name"
            elif "isin" in c_lower:
                col_map[c] = "ISIN"
            elif "quantity" in c_lower or "qty" in c_lower:
                col_map[c] = f"Qty_{month}_{year}"
            # Optional Cols
            #elif "market" in c_lower and "value" in c_lower:
            #    col_map[c] = f"MarketValue_{month}_{year}"
            #elif ("nav" in c_lower or "net assets" in c_lower or "% to" in c_lower) and "quantity" not in c_lower:
            #    col_map[c] = f"NavPct_{month}_{year}"
                
        df = df.rename(columns=col_map)
        
        # Validation: We MUST have ISIN, Name, and Qty. Others are optional.
        req_cols = ["ISIN", "Stock Name", f"Qty_{month}_{year}"]
        if not all(col in df.columns for col in req_cols):
            return None
        
        valid_rows = []
        for _, row in df.iterrows():
            try:
                isin = str(row.get("ISIN", "")).upper().strip()
                # Basic validation
                if not isin.startswith("INE") or "total" in str(row.get("Stock Name", "")).lower():
                    continue
                
                # Parse Qty (Mandatory)
                qty = float(str(row.get(f"Qty_{month}_{year}", 0)).replace(",", "").replace("-", "0"))
                if qty <= 0: continue
                
                record = {
                    "Stock Name": row["Stock Name"], 
                    "ISIN": isin, 
                    f"Qty_{month}_{year}": qty
                }
                
                # Parse Optional Cols (Safely)
            #    if f"MarketValue_{month}_{year}" in df.columns:
            #        try: record[f"MarketValue_{month}_{year}"] = float(str(row[f"MarketValue_{month}_{year}"]).replace(",", ""))
            #        except: pass
                
            #    if f"NavPct_{month}_{year}" in df.columns:
            #        try: record[f"NavPct_{month}_{year}"] = float(str(row[f"NavPct_{month}_{year}"]).replace(",", "").replace("%", ""))
            #        except: pass
                    
                valid_rows.append(record)
            except: continue
            
        return pd.DataFrame(valid_rows)
    except Exception as e:
        print(f"Error in Nippon: {e}")
        return None

# --- HDFC ENGINE (Restored from your working version) ---
def fetch_hdfc(month, year):
    try:
        conf = FUND_CONFIG["HDFC Nifty 50 Index"]
        month_num = datetime.datetime.strptime(month, "%B").month
        last_day = calendar.monthrange(year, month_num)[1]
        
        date_obj = datetime.date(year, month_num, 1)
        next_month = date_obj.replace(day=28) + datetime.timedelta(days=4)
        folder_path = next_month.strftime("%Y-%m")
        
        filename = f"Monthly HDFC Nifty 50 Index Fund - {last_day} {month} {year}.xlsx"
        url = f"{conf['base_url']}/{folder_path}/{filename.replace(' ', '%20')}"

        resp = requests.get(url, headers=HEADERS, timeout=30)
        if resp.status_code != 200: return None
        
        xls = pd.ExcelFile(BytesIO(resp.content))
        target_df, header_row = None, None
        
        for sheet in xls.sheet_names:
            df = pd.read_excel(xls, sheet_name=sheet, header=None)
            if conf['fund_keyword'] in df.iloc[0:5].astype(str).to_string().lower():
                target_df = df
                for idx, row in df.iterrows():
                    r_str = row.astype(str).str.cat(sep=" ").lower()
                    if "isin" in r_str and "name" in r_str and "quantity" in r_str: header_row = idx; break
                break
        
        if target_df is None or header_row is None: return None

        target_df.columns = target_df.iloc[header_row]
        df = target_df.iloc[header_row+1:].copy()
        
        col_map = {}
        for c in df.columns:
            c_lower = str(c).lower().strip()
            if "isin" in c_lower: col_map[c] = "ISIN"
            elif "name" in c_lower and ("instrument" in c_lower or "security" in c_lower): col_map[c] = "Stock Name"
            elif "quantity" in c_lower or "qty" in c_lower: col_map[c] = f"Qty_{month}_{year}"
            elif "market" in c_lower and "value" in c_lower: col_map[c] = f"MarketValue_{month}_{year}"
            elif ("nav" in c_lower or "net assets" in c_lower or "% to" in c_lower) and "quantity" not in c_lower: col_map[c] = f"NavPct_{month}_{year}"
        df = df.rename(columns=col_map)
        
        if "ISIN" not in df.columns or "Stock Name" not in df.columns or f"Qty_{month}_{year}" not in df.columns: return None
        
        valid_rows = []
        for _, row in df.iterrows():
            try:
                isin = str(row.get("ISIN", "")).upper().strip()
                if not isin.startswith("INE"): continue
                stock_name = str(row.get("Stock Name", "Unknown"))
                qty_val = str(row.get(f"Qty_{month}_{year}", "0")).replace(",", "").replace(" ", "")
                if not qty_val or qty_val.lower() in ["nan", "n/a", "none", ""]: continue
                qty = float(qty_val)
                if qty <= 0: continue
                
                record = {"Stock Name": stock_name, "ISIN": isin, f"Qty_{month}_{year}": qty}
                if f"MarketValue_{month}_{year}" in df.columns:
                    try: record[f"MarketValue_{month}_{year}"] = float(str(row.get(f"MarketValue_{month}_{year}", 0)).replace(",", ""))
                    except: record[f"MarketValue_{month}_{year}"] = 0
                if f"NavPct_{month}_{year}" in df.columns:
                    try: record[f"NavPct_{month}_{year}"] = float(str(row.get(f"NavPct_{month}_{year}", 0)))
                    except: record[f"NavPct_{month}_{year}"] = 0
                valid_rows.append(record)
            except: continue
        return pd.DataFrame(valid_rows)
    except: return None