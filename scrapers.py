# scrapers.py
import requests
import pandas as pd
import re
from bs4 import BeautifulSoup
from io import BytesIO
import calendar
import datetime
from config import FUND_CONFIG, HEADERS, MONTH_ABBR
# ... inside scrapers.py ...

# --- HELPER: Date Ordinal (e.g., 1st, 2nd, 3rd, 4th) ---
def get_date_suffix(day):
    if 4 <= day <= 20 or 24 <= day <= 30:
        return "th"
    else:
        return ["st", "nd", "rd"][day % 10 - 1]

# --- SBI ENGINE ---

# ... imports ...

# --- GENERIC SBI ENGINE ---
def fetch_sbi_generic(fund_name, month, year):
    try:
        # 1. Get Config
        conf = FUND_CONFIG[fund_name]
        target_sheet_code = conf["sheet_code"]  # e.g., "SMCDF"
        
        # 2. Construct Master URL
        month_num = datetime.datetime.strptime(month, "%B").month
        last_day = calendar.monthrange(year, month_num)[1]
        suffix = "th" if 11 <= last_day <= 13 else {1: "st", 2: "nd", 3: "rd"}.get(last_day % 10, "th")
        date_str = f"{last_day}{suffix}-{month.lower()}-{year}"
        
        base_url = f"https://www.sbimf.com/docs/default-source/scheme-portfolios/all-schemes-monthly-portfolio---as-on-{date_str}.xlsx"
        
        print(f"   🔍 SBI: Checking Master File...")
        resp = requests.get(base_url, headers=HEADERS, timeout=60, verify=False)
        
        if resp.status_code != 200:
            print(f"   ❌ Master file unavailable for {month} {year}")
            return None

        # 3. Load Excel & Find Exact Sheet
        xls = pd.ExcelFile(BytesIO(resp.content))
        
        actual_sheet = None
        # Try exact match first, then case-insensitive
        if target_sheet_code in xls.sheet_names:
            actual_sheet = target_sheet_code
        else:
            # Fallback: Look for code inside sheet name (e.g. "SMCDF " with space)
            for s in xls.sheet_names:
                if target_sheet_code.lower() == s.strip().lower():
                    actual_sheet = s
                    break
        
        if not actual_sheet:
            print(f"   ❌ Sheet '{target_sheet_code}' not found in master file.")
            # Optional: Print available sheets for debugging
            # print(f"Available: {xls.sheet_names[:5]}...") 
            return None
            
        print(f"   ✅ Found Sheet: {actual_sheet}")
        df = pd.read_excel(xls, sheet_name=actual_sheet, header=None)
        
        # 4. Find Header Row (Standard logic)
        header_idx = None
        for idx, row in df.iterrows():
            row_str = row.astype(str).str.cat(sep=' ').lower()
            if "name of instrument" in row_str or "isin" in row_str:
                header_idx = idx
                break
        
        if header_idx is None: return None

        df.columns = df.iloc[header_idx]
        df = df.iloc[header_idx+1:].copy()
        
        # 5. Map Columns
        col_map = {}
        for c in df.columns:
            c_lower = str(c).lower().strip()
            if "name" in c_lower and "instrument" in c_lower: col_map[c] = "Stock Name"
            elif "isin" in c_lower: col_map[c] = "ISIN"
            elif "quantity" in c_lower or "qty" in c_lower: col_map[c] = f"Qty_{month}_{year}"
            elif "market" in c_lower and "value" in c_lower: col_map[c] = f"MarketValue_{month}_{year}"
            elif ("nav" in c_lower or "net assets" in c_lower) and "quantity" not in c_lower: col_map[c] = f"NavPct_{month}_{year}"
        
        df = df.rename(columns=col_map)
        
        if f"Qty_{month}_{year}" not in df.columns: return None
        
        # 6. Parse Rows
        valid_rows = []
        for _, row in df.iterrows():
            try:
                isin = str(row.get("ISIN", "")).upper().strip()
                name = str(row.get("Stock Name", "")).strip()
                
                # Equity Filter: Must have valid ISIN
                if not isin.startswith("INE"): continue

                qty = float(row.get(f"Qty_{month}_{year}", 0))
                if qty <= 0: continue
                
                record = { "Stock Name": name, "ISIN": isin, f"Qty_{month}_{year}": qty }
                
                if f"MarketValue_{month}_{year}" in df.columns:
                    record[f"MarketValue_{month}_{year}"] = float(row.get(f"MarketValue_{month}_{year}", 0))
                if f"NavPct_{month}_{year}" in df.columns:
                    record[f"NavPct_{month}_{year}"] = float(row.get(f"NavPct_{month}_{year}", 0))
                    
                valid_rows.append(record)
            except: continue
            
        return pd.DataFrame(valid_rows)

    except Exception as e:
        print(f"   ❌ Error in SBI {fund_name}: {e}")
        return None
# --- PPFAS ENGINE ---
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
                qty = next((float(v.replace(",","")) for v in row_vals if v.replace(",","").replace(".","").isdigit() and float(v.replace(",","")) > 0), 0)
                if qty > 0: valid_holdings.append({"Stock Name": name, "ISIN": isin, f"Qty_{month}_{year}": qty})
        
        if not valid_holdings: return None
        return pd.DataFrame(valid_holdings).groupby("ISIN", as_index=False).agg({"Stock Name": "first", f"Qty_{month}_{year}": "sum"})
    except: return None

# ... imports ...

# --- GENERIC NIPPON ENGINE ---
# ... inside scrapers.py ...

# --- GENERIC NIPPON ENGINE (Updated with Day-Specific Pattern) ---
def fetch_nippon_generic(fund_name, month, year):
    print(month)
    if month == "August" or month == "July":
        print(f"Skipping {month} as it's not supported.")
        return None

    try:
        conf = FUND_CONFIG[fund_name]
        target_sheet_code = conf["sheet_code"] # e.g., "SC" or "GF"
        
        # 1. Prepare Date Variables
        
        mon_abbr = MONTH_ABBR.get(month, month[:3]) # "Dec"
        yy = str(year)[-2:] # "25"
        
        # Calculate Last Day of Month (e.g., 31, 30, 28)
        month_num = datetime.datetime.strptime(month, "%B").month
        last_day = calendar.monthrange(year, month_num)[1]
        
        target_url = None
        
        # 2. Define URL Patterns
        base_paths = [
            # Pattern 1: With Day (e.g., NIMF-MONTHLY-PORTFOLIO-31-Dec-25)
            f"https://mf.nipponindiaim.com/InvestorServices/FactsheetsDocuments/NIMF-MONTHLY-PORTFOLIO-{last_day}-{mon_abbr}-{yy}",
            f"https://mf.nipponindiaim.com/InvestorServices/FactsheetsDocuments/NIMF-MONTHLY-PORTFOLIO-{last_day}-{month}-{yy}"
            ]
        
        urls_to_try = []
        for p in base_paths:
            urls_to_try.append(p + ".xls")
            urls_to_try.append(p + ".xlsx")

        # 3. Find File
        print(f"   🔍 Nippon: Searching for master file ({month} {year})...")
        for u in urls_to_try:
            try:
                # verify=False is critical for some Nippon servers
                print(f"   🔍 Checking URL: {u}")
                status = requests.head(u, headers=HEADERS, timeout=5, verify=False).status_code
                print(f"   🔍 Status Code: {status}")
                if status == 200:
                    target_url = u
                    break
            except: continue

        print(f"   🔍 Nippon: Target URL: {target_url}" )

        if not target_url: 
            print(f"   ❌ Nippon: Master file not found.")
            return None

        print(f"   ✅ Found: {target_url}")
        resp = requests.get(target_url, headers=HEADERS, timeout=45, verify=False)
        
        # 4. Load Excel & Find Exact Sheet
        xls = pd.ExcelFile(BytesIO(resp.content))
        
        actual_sheet = None
        # Try exact match first (Case sensitive is safer for codes like "SC")
        if target_sheet_code in xls.sheet_names:
            actual_sheet = target_sheet_code
        else:
            # Fallback: Case insensitive match
            for s in xls.sheet_names:
                if target_sheet_code.lower() == s.strip().lower():
                    actual_sheet = s
                    break
        
        if not actual_sheet:
            print(f"   ❌ Sheet '{target_sheet_code}' not found in master file.")
            return None
            
        print(f"   📄 Parsing Sheet: {actual_sheet}")
        df = pd.read_excel(xls, sheet_name=actual_sheet, header=None)

        # 5. Standard Parsing Logic
        header_idx = None
        for idx, row in df.iterrows():
            row_str = row.astype(str).str.cat(sep=' ').lower()
            if "name of the instrument" in row_str or ("isin" in row_str and "qty" in row_str): 
                header_idx = idx
                break
        
        if header_idx is None: return None

        df.columns = df.iloc[header_idx]
        df = df.iloc[header_idx+1:].copy()
        
        col_map = {}
        for c in df.columns:
            c_lower = str(c).lower().strip()
            if "name" in c_lower and "instrument" in c_lower: col_map[c] = "Stock Name"
            elif "isin" in c_lower: col_map[c] = "ISIN"
            elif "quantity" in c_lower or "qty" in c_lower: col_map[c] = f"Qty_{month}_{year}"
            elif "market" in c_lower and "value" in c_lower: col_map[c] = f"MarketValue_{month}_{year}"
            elif ("nav" in c_lower or "net assets" in c_lower) and "quantity" not in c_lower: col_map[c] = f"NavPct_{month}_{year}"
                
        df = df.rename(columns=col_map)
        
        if f"Qty_{month}_{year}" not in df.columns: return None
        
        valid_rows = []
        for _, row in df.iterrows():
            try:
                isin = str(row.get("ISIN", "")).upper().strip()
                name = str(row.get("Stock Name", "")).strip()
                
                # Equity Filter
                if (not isin.startswith("INE")) and (len(name) < 3 or "Total" in name): continue

                qty = float(row.get(f"Qty_{month}_{year}", 0))
                if qty <= 0: continue
                
                record = { "Stock Name": name, "ISIN": isin, f"Qty_{month}_{year}": qty }
                
                if f"MarketValue_{month}_{year}" in df.columns:
                    record[f"MarketValue_{month}_{year}"] = float(row.get(f"MarketValue_{month}_{year}", 0))
                if f"NavPct_{month}_{year}" in df.columns:
                    record[f"NavPct_{month}_{year}"] = float(row.get(f"NavPct_{month}_{year}", 0))
                        
                valid_rows.append(record)
            except: continue
            
        return pd.DataFrame(valid_rows)

    except Exception as e:
        print(f"   ❌ Error processing Nippon {fund_name}: {e}")
        return None
def fetch_nippon(st, month, year):
    print(month)
    if month != "August" or month!="July":

        try:
            
            conf = FUND_CONFIG["Nippon India Small Cap"]
            month_short, year_short = month[:3], str(year)[-2:]
            target_url = None
            
            # 1. Try Direct Patterns
            patterns = [
                f"https://mf.nipponindiaim.com/InvestorServices/FactsheetsDocuments/NIMF-MONTHLY-PORTFOLIO-{month_short}-{year_short}.xls",
                f"https://mf.nipponindiaim.com/InvestorServices/FactsheetsDocuments/NIMF-MONTHLY-PORTFOLIO-{month}-{year}.xls"
            ]
            for url in patterns:
                try: 
                    if requests.head(url, headers=HEADERS, timeout=10000).status_code == 200: target_url = url; break
                except: continue
                
            # 2. Try Regex
            if not target_url:
                resp = requests.get(conf["url"], headers=HEADERS, timeout=10000)
                st.toast(resp.status_code)
                regex = fr'href=["\']([^"\']*(?:monthly|portfolio)[^"\']*(?:{month}|{month_short})[^"\']*(?:{year}|{year_short})[^"\']*\.xls[x]?)["\']'
                matches = re.findall(regex, resp.text, re.IGNORECASE)
                st.toast(f"🔍 Nippon Regex found {len(matches)} links", icon="🔗")
                if matches:
                    st.toast(f"🔍 Nippon Regex matched {len(matches)} links", icon="🔗")
                    link = matches[0]
                    target_url = conf["base_url"] + link if link.startswith("/") else link
            
            print(f"   🔍 Nippon URL found: {target_url}")
            st.toast(f"🔍 Nippon URL not found for {month} {year}", icon="🔗")
            if not target_url: return None
        

            resp = requests.get(target_url, headers=HEADERS, timeout=30)
            try: df = pd.read_excel(BytesIO(resp.content), sheet_name=conf["sheet"], header=None, engine='openpyxl')
            except: df = pd.read_excel(BytesIO(resp.content), sheet_name=conf["sheet"], header=None, engine='xlrd')

            header_idx = None
            for idx, row in df.iterrows():
                if "name of the instrument" in row.astype(str).str.cat(sep=' ').lower(): header_idx = idx; break
            st.toast(f"🔍 Nippon Header found for {header_idx}", icon="🔗")
            if header_idx is None: return None

            df.columns = df.iloc[header_idx]
            df = df.iloc[header_idx+1:].copy()
            col_map = {c: "Stock Name" if "name of the instrument" in str(c).lower() else "ISIN" if "isin" in str(c).lower() else f"Qty_{month}_{year}" if "quantity" in str(c).lower() else c for c in df.columns}
            df = df.rename(columns=col_map)
            
            valid_rows = []
            for _, row in df.iterrows():
                isin = str(row.get("ISIN", "")).upper()
                if isin.startswith("INE") and "total" not in str(row.get("Stock Name", "")).lower():
                    try:
                        qty = float(str(row.get(f"Qty_{month}_{year}", 0)).replace(",", ""))
                        if qty > 0: valid_rows.append({"Stock Name": row["Stock Name"], "ISIN": isin, f"Qty_{month}_{year}": qty})
                    except: continue
            st.toast(f"✅ Secured Nippon data for {month} {year} valid rows: {len(valid_rows)}", icon="✨")
            return pd.DataFrame(valid_rows)
        except:
            print(f"   ❌ Error fetching Nippon data for {month} {year}") 
            st.toast(f"❌ Error fetching Nippon data for {month} {year}", icon="⚠️")
            return None

# --- HDFC ENGINE ---
def fetch_hdfc(month, year):
    try:
        conf = FUND_CONFIG["HDFC Nifty 50 Index"]
        month_num = datetime.datetime.strptime(month, "%B").month
        last_day = calendar.monthrange(year, month_num)[1]
        
        # Calculate folder date (Next month logic)
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
            val = str(c).lower().strip()
            if "isin" in val: col_map[c] = "ISIN"
            elif "name" in val and "instrument" in val: col_map[c] = "Stock Name"
            elif "quantity" in val: col_map[c] = f"Qty_{month}_{year}"
        df = df.rename(columns=col_map)
        
        valid_rows = []
        for _, row in df.iterrows():
            isin = str(row.get("ISIN", "")).upper()
            if isin.startswith("INE"):
                try:
                    qty = float(str(row.get(f"Qty_{month}_{year}", 0)).replace(",", ""))
                    if qty > 0: valid_rows.append({"Stock Name": row["Stock Name"], "ISIN": isin, f"Qty_{month}_{year}": qty})
                except: continue
        return pd.DataFrame(valid_rows)
    except: return None