# 🌊 FundFlow Analytics

> **Decode the strategy behind the NAV.**

[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://mf-portfolio-tracker.streamlit.app//)
![Python](https://img.shields.io/badge/Python-3.9%2B-blue?style=flat&logo=python&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-green?style=flat)
![Status](https://img.shields.io/badge/Status-Active-orange?style=flat)

---

## 📖 Overview

**FundFlow Analytics** is a modern, AI-powered dashboard designed to bring transparency to Mutual Fund investing. While most tools only track returns (NAV), FundFlow tracks **decisions**.

By parsing monthly portfolio disclosures, this tool visualizes exactly *how* a fund manager is deploying capital—identifying fresh entries, complete exits, and conviction shifts—all wrapped in a **Soft Minimalist SaaS** interface.
![alt text](image.png)
---

## ✨ Key Features

### 🌊 Whale Watcher (Fund Flow)
Stop guessing. Instantly identify the **"Smart Money"** moves:
* **Fresh Entries:** See which new stocks were added to the portfolio this month.
* **Complete Exits:** Identify stocks the manager has lost faith in and sold off entirely.
* **Volume Velocity:** Track sector accumulation trends before they hit the news.

### ⚔️ Overlap Clash
True diversification is mathematically proven, not just assumed.
* **Venn-Style Analysis:** Compare any two funds to reveal hidden overlaps.
* **Redundancy Check:** Ensure you aren't paying double expense ratios for the exact same underlying assets.

### 📈 Trend Trajectory
* **Conviction tracking:** Visualize the month-on-month quantity changes of any specific stock using smooth **Spline Analytics**.
* **Historical Context:** See if a manager is buying the dip or panic selling.

### 🎨 Modern SaaS Architecture
* **CogniAI-Inspired UI:** Features a "Bento-box" layout, glassmorphism effects, and a warm Orange/Charcoal palette.
* **Mobile First:** Fully responsive layouts with touch-optimized navigation.

---

## 🛠️ Tech Stack

* **Core:** [Python 3.9+](https://www.python.org/)
* **Frontend:** [Streamlit](https://streamlit.io/) (Custom CSS Theming)
* **Visualization:** [Plotly Express](https://plotly.com/python/) & Graph Objects
* **Data Processing:** Pandas & NumPy
* **Data Storage:** Local Excel Database (`.xlsx`) for lightweight portability.

---

## ⚡ Quick Start

### Prerequisites
* Python 3.8 or higher
* pip

### Installation

1.  **Clone the repository**
    ```bash
    git clone [https://github.com/nikhilm19/MF-portfolio-tracker.git](https://github.com/nikhilm19/MF-portfolio-tracker.git)
    cd MF-portfolio-tracker
    ```

2.  **Create a virtual environment** (Recommended)
    ```bash
    python -m venv venv
    # Windows
    venv\Scripts\activate
    # macOS/Linux
    source venv/bin/activate
    ```

3.  **Install dependencies**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Launch the Dashboard**
    ```bash
    streamlit run app.py
    ```

---

## 📂 Project Structure

```text
MF-portfolio-tracker/
├── app.py              # 🚀 Main entry point & state management
├── ui.py               # 🎨 UI Component library (CSS, Cards, Animations)
├── scrapers.py         # 🕷️ Logic to fetch/parse monthly disclosures
├── analysis.py         # 🧮 Algorithms for Overlap & Flow calculations
├── config.py           # ⚙️ Configuration for Funds & File paths
├── requirements.txt    # 📦 Project dependencies
└── data/               # 💾 Directory for local Excel storage