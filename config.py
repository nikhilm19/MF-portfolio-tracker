# config.py

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

HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"}

YEARS = [2025]

MONTHS = [
    "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December"
]