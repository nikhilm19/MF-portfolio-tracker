# config.py
SBI_EQUITY_SCHEMES = {
  "SMEEF": "SBI ESG Exclusionary Strategy Fund",
  "SLMF": "SBI Large and Midcap Fund",
  "SLTEF": "SBI ELSS Tax Saver Fund",
  "SMGLF": "SBI MNC Fund",
  "SEHF": "SBI Equity Hybrid Fund",
  "SMIF": "SBI Medium to Long Duration Fund (Erstwhile known as SBI Magnum Income Fund)",
  "SCOF": "SBI Consumption Opportunities Fund",
  "STOF": "SBI Technology Opportunities Fund",
  "SHOF": "SBI Healthcare Opportunities Fund",
  "SCF": "SBI Contra Fund",
  "SNIF": "SBI Nifty Index Fund",
  "SMCBF-SP": "SBI Children's Fund - Savings Plan (Erstwhile known as SBI Magnum Children's Benefit Fund-Svg P)",
  "SOF": "SBI Overnight Fund",
  "SMMDF": "SBI Medium Duration Fund (Erstwhile known as SBI Magnum Medium Duration Fund)",
  "SLF": "SBI Liquid Fund",
  "SDBF": "SBI Dynamic Bond Fund",
  "SSF": "SBI Savings Fund",
  "SCRF": "SBI Credit Risk Fund",
  "SFEF": "SBI Focused Fund",
  "SCHF": "SBI Conservative Hybrid Fund",
  "SMUSD": "SBI Ultra Short Duration Fund (Erstwhile known as SBI Magnum Ultra Short Duration Fund)",
  "SMIDCAP": "SBI Midcap Fund",
  "SMCMF": "SBI Constant Maturity 10-Year Gilt Fund (Erstwhile known as SBI Magnum Constant Maturity Fund)",
  "SMCOMMA": "SBI Comma Fund",
  "SMGF": "SBI Gilt Fund (Erstwhile known as SBI Magnum Gilt Fund)",
  "SFLEXI": "SBI Flexicap Fund",
  "SMAAF": "SBI Multi Asset Allocation Fund",
  "SBLUECHIP": "SBI Large Cap Fund"
}
NIPPON_EQUITY_SCHEMES = {
    "GF": "Nippon India Growth Mid Cap Fund",
    "GS": "Nippon India Vision Large & Mid Cap Fund",
    "BF": "Nippon India Banking & Financial Services Fund",
    "PS": "Nippon India Power & Infra Fund",
    "PH": "Nippon India Pharma Fund",
    "ME": "Nippon India Consumption Fund",
    "EO": "Nippon India Multi Cap Fund",
    "SE": "Nippon India Value Fund",
    "TS": "Nippon India ELSS Tax Saver Fund",
    "LE": "Nippon India Focused Fund",
    "EA": "Nippon India Large Cap Fund",
    "QP": "Nippon India Quant Fund",
    "NF": "Nippon India Index Fund - Nifty 50 Plan",
    "SC": "Nippon India Small Cap Fund",
    "SF": "Nippon India Index Fund - Sensex Plan",
    "CE": "Nippon India ETF Nifty 100",
    "CF": "Nippon India ETF Nifty India Consumption",
    "RD": "Nippon India ETF Nifty Dividend Opp 50",
    "JE": "Nippon India Japan Equity Fund",
    "SX": "Nippon India ETF BSE Sensex",
    "NX": "Nippon India ETF Nifty 50 Value 20",
    "UE": "Nippon India US Equity Opp Fund",
    "NB": "Nippon India ETF Nifty 50 BeES",
    "JZ": "Nippon India ETF Junior BeES",
    "PU": "Nippon India ETF PSU Bank BeES",
    "BB": "Nippon India ETF Bank BeES",
    "SB": "Nippon India ETF Shariah BeES",
    "HS": "Nippon India ETF Hang Seng BeES",
    "IB": "Nippon India ETF Infra BeES",
    "CC": "CPSE ETF",
    "NM": "Nippon India ETF Nifty Midcap 150",
    "SN": "Nippon India ETF Sensex Next 50",
    "NZ": "Nippon India ETF Nifty IT",
    "NS": "Nippon India Nifty Smallcap 250 Index Fund",
    "NP": "Nippon India Nifty Midcap 150 Index Fund",
    "NV": "Nippon India Nifty 50 Value 20 Index Fund",
    "NH": "Nippon India Nifty Pharma ETF",
    "LC": "Nippon India Flexi Cap Fund",
    "ET": "Nippon India Taiwan Equity Fund",
    "NO": "Nippon India Nifty Auto ETF",
    "NN": "Nippon India Nifty Alpha Low Vol 30 Index",
    "IT": "Nippon India Innovation Fund",
    "IX": "Nippon India Nifty IT Index Fund",
    "BX": "Nippon India Nifty Bank Index Fund",
    "EW": "Nippon India Nifty 500 Equal Weight Index",
    "MT": "Nippon India Nifty 500 Momentum 50 Index",
    "AN": "Nippon India Nifty Auto Index Fund",
    "RN": "Nippon India Nifty Realty Index Fund",
    "AM": "Nippon India Active Momentum Fund",
    "LV": "Nippon India Nifty 500 Low Vol 50 Index",
    "QI": "Nippon India Nifty 500 Quality 50 Index",
    "BS": "Nippon India BSE Sensex Next 30 Index",
    "MC": "Nippon India MNC Fund",
    "MG": "Nippon India Nifty India Manufacturing Index"
}
FUND_CONFIG = {
    "PPFAS Flexi Cap": {
        "file": "PPFCF_Portfolio_Dashboard_2025.xlsx",
        "url": "https://amc.ppfas.com/downloads/portfolio-disclosure/",
        "sheet": None
    },
    "Nippon India Small Cap": {
        "file": "Nippon_SC_Portfolio_2025.xlsx",
        "url": "https://mf.nipponindiaim.com/investor-service/downloads/factsheet-portfolio-and-other-disclosures",
        "base_url": "https://mf.nipponindiaim.com",
        "sheet": "SC"
    },
    "HDFC Nifty 50 Index": {
        "file": "HDFC_Nifty50_Portfolio_2025.xlsx",
        "base_url": "https://files.hdfcfund.com/s3fs-public",
        "fund_keyword": "nifty 50 index fund" 
    }
}

# 3. Auto-generate SBI Configs to avoid duplicates
for code, name in SBI_EQUITY_SCHEMES.items():
    FUND_CONFIG[name] = {
        "amc_code": "SBI",
        "sheet_code": code,  # This tells scraper which sheet to look for
        "file": f"data/sbi_{code.lower()}.xlsx" # Auto-generates unique filenames
    }

# 3. Auto-generate Nippon Configs
# for code, name in NIPPON_EQUITY_SCHEMES.items():
#     FUND_CONFIG[name] = {
#         "amc_code": "NIPPON",
#         "sheet_code": code,  # Crucial: This is "SC", "GF", etc.
#         "file": f"data/nippon_{code.lower()}.xlsx"
#     }

HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"}

YEARS = [2025]

MONTHS = [
    "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December"
]

MONTH_ABBR = {
    "January": "Jan",
    "February": "Feb",
    "March": "Mar",
    "April": "Apr",
    "May": "May",
    "June": "Jun",
    "July": "Jul",
    "August": "Aug",
    "September": "Sep",
    "October": "Oct",
    "November": "Nov",
    "December": "Dec"
}
