import yfinance as yf
import pandas as pd
import os
from datetime import datetime

# Constants
CSV_PATH = 'assets/nifty500_list.csv'
DATA_DIR = 'backend/data'
START_DATE = (datetime.now().replace(year=datetime.now().year - 15)).strftime('%Y-%m-%d')
END_DATE = datetime.now().strftime('%Y-%m-%d')

# Ensure data folder exists
os.makedirs(DATA_DIR, exist_ok=True)

# Read stock list
nifty_df = pd.read_csv(CSV_PATH)

for _, row in nifty_df.iterrows():
    symbol = row['Symbol']
    print(f"📥 Downloading data for {symbol}...")

    try:
        ticker = yf.Ticker(symbol + ".NS")  # Add ".NS" for NSE symbols on Yahoo Finance
        hist = ticker.history(start=START_DATE, end=END_DATE)

        if hist.empty:
            print(f"⚠️ No data found for {symbol}")
            continue

        hist.reset_index(inplace=True)
        hist[['Date', 'Open', 'High', 'Low', 'Close', 'Volume']].to_csv(f"{DATA_DIR}/{symbol}.csv", index=False)
        print(f"✅ Saved {symbol}.csv")

    except Exception as e:
        print(f"❌ Error fetching {symbol}: {e}")
