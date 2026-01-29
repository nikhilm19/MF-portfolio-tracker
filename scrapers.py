# scrapers.py
import requests
import pandas as pd
import re
from bs4 import BeautifulSoup
from io import BytesIO
import calendar
import datetime
from config import FUND_CONFIG, HEADERS

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

# --- NIPPON ENGINE ---
def fetch_nippon(st, month, year):
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
                if requests.head(url, headers=HEADERS, timeout=1000).status_code == 200: target_url = url; break
            except: continue
            
        # 2. Try Regex
        if not target_url:
            resp = requests.get(conf["url"], headers=HEADERS, timeout=1000)
            regex = fr'href=["\']([^"\']*(?:monthly|portfolio)[^"\']*(?:{month}|{month_short})[^"\']*(?:{year}|{year_short})[^"\']*\.xls[x]?)["\']'
            matches = re.findall(regex, resp.text, re.IGNORECASE)
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