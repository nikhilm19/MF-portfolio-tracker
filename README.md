# FundFlow Analytics

**Decode the strategy behind the NAV.** A modern, AI-powered dashboard to track, visualize, and analyze Mutual Fund portfolios. Move beyond simple returns and understand *how* your fund manager is managing your money.

[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://share.streamlit.io/) 
![Python](https://img.shields.io/badge/Python-3.9%2B-blue)
![License](https://img.shields.io/badge/License-MIT-green)

---

## 🚀 Features

FundFlow Analytics transforms raw monthly portfolio disclosures into actionable insights using a **Soft Minimalist SaaS** interface.

### 1. 🌊 Whale Watcher (Fund Flow)
* **Track Smart Money:** Instantly spot **Fresh Entries** (new stocks bought this month) and **Complete Exits** (stocks sold off entirely).
* **Volume Velocity:** See which sectors the fund manager is aggressively accumulating.

### 2. ⚔️ Overlap Clash
* **True Diversification Check:** Compare any two funds to identify **hidden redundancies**.
* **Venn-Style Logic:** See stocks unique to Fund A, unique to Fund B, and common holdings.
* **Prevent Over-Exposure:** Avoid paying double fees for the same portfolio.

### 3. 📈 Trend Trajectory
* **Historical Conviction:** Visualize the month-on-month quantity changes of any specific stock.
* **Spline Analytics:** Smooth, interactive charts powered by Plotly to track holding patterns over time.

### 4. 🎨 Modern SaaS UI
* **CogniAI Inspired Design:** Clean "Bento-box" layout, glassmorphism effects, and a warm Orange/Charcoal color palette.
* **Mobile Responsive:** optimized card layouts and navigation for mobile devices.

---

## 🛠️ Tech Stack

* **Frontend:** [Streamlit](https://streamlit.io/) (Python-based web framework)
* **Visualization:** [Plotly Express](https://plotly.com/python/) & Graph Objects
* **Data Manipulation:** Pandas & NumPy
* **Data Storage:** Excel (`.xlsx`) as a lightweight local database
* **Theme:** Custom CSS (Plus Jakarta Sans typography, Soft UI shadows)

---

## ⚙️ Installation

1.  **Clone the repository:**
    ```bash
    git clone [https://github.com/nikhilm19/MF-portfolio-tracker.git](https://github.com/nikhilm19/MF-portfolio-tracker.git)
    cd MF-portfolio-tracker
    ```

2.  **Create a virtual environment (Optional but recommended):**
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```

3.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Run the application:**
    ```bash
    streamlit run app.py
    ```

---

## 📂 Project Structure

```text
MF-portfolio-tracker/
├── app.py              # Main application entry point & logic controller
├── ui.py               # UI Component library (CSS, Cards, Charts, Landing Page)
├── scrapers.py         # Logic to fetch/parse monthly fund disclosures
├── analysis.py         # Algorithms for Overlap & Fund Flow calculations
├── config.py           # Configuration for Fund Names & Excel file paths
├── requirements.txt    # Python dependencies
└── data/               # Folder where scraped Excel sheets are stored