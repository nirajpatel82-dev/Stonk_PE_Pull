import yfinance as yf
import csv
import os
from datetime import datetime
import time

# Configuration
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
INPUT_FILE = os.path.join(BASE_DIR, 'tickers.csv')
OUTPUT_FILE = os.path.join(BASE_DIR, 'pe_ratios_log.csv')


def get_pe_data(symbol):
    """Fetches P/E ratios using the yfinance library."""
    try:
        ticker = yf.Ticker(symbol)
        info = ticker.info

        # Yahoo Finance provides two types of PE ratios
        trailing_pe = info.get('trailingPE', 'N/A')
        forward_pe = info.get('forwardPE', 'N/A')

        return trailing_pe, forward_pe
    except Exception as e:
        print(f"Error fetching {symbol}: {e}, trying again after 5s...")
        time.sleep(5)
        try:
            ticker = yf.Ticker(symbol)
            info = ticker.info

            # Yahoo Finance provides two types of PE ratios
            trailing_pe = info.get('trailingPE', 'N/A')
            forward_pe = info.get('forwardPE', 'N/A')

            return trailing_pe, forward_pe
        except Exception as e:
            print(f"Error fetching {symbol}: {e}, failing, moving on...")
            time.sleep(5)
            return "Error", "Error"


def main():
    today = datetime.now().strftime('%Y-%m-%d')
    results = []

    # 1. Read tickers from CSV
    if not os.path.exists(INPUT_FILE):
        print(f"Error: {INPUT_FILE} not found.")
        return

    with open(INPUT_FILE, mode='r') as f:
        reader = csv.DictReader(f)
        # Handles potential whitespace in headers
        tickers = [row['ticker'].strip() for row in reader]

    # 2. Fetch Data
    print(f"Fetching data for {len(tickers)} tickers via yfinance...")
    for symbol in tickers:
        trailing, forward = get_pe_data(symbol)
        results.append({
            'date': today,
            'ticker': symbol,
            'trailing_pe': trailing,
            'forward_pe': forward
        })
        print(f"{symbol} -> Trailing: {trailing}, Forward: {forward}")
        time.sleep(1)

    # 3. Append to or Create output file
    file_exists = os.path.isfile(OUTPUT_FILE)
    fieldnames = ['date', 'ticker', 'trailing_pe', 'forward_pe']

    with open(OUTPUT_FILE, mode='a', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        if not file_exists:
            writer.writeheader()
        writer.writerows(results)

    print(f"\nDone! Results saved to {OUTPUT_FILE}")


if __name__ == "__main__":
    main()