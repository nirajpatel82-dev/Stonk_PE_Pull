import yfinance as yf
import csv
import os
import time
import pandas as pd
from datetime import datetime, timedelta

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
        marketCap = info.get('marketCap', 'N/A')

        return trailing_pe, forward_pe, marketCap
    except Exception as e:
        print(f"Error fetching {symbol}: {e}, trying again after 5s...")
        time.sleep(5)
        try:
            ticker = yf.Ticker(symbol)
            info = ticker.info

            # Yahoo Finance provides two types of PE ratios
            trailing_pe = info.get('trailingPE', 'N/A')
            forward_pe = info.get('forwardPE', 'N/A')
            marketCap = info.get('marketCap', 'N/A')

            return trailing_pe, forward_pe, marketCap
        except Exception as e:
            print(f"Error fetching {symbol}: {e}, failing, moving on...")
            time.sleep(5)
            return "Error", "Error", "Error"


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
        trailing, forward, market_cap = get_pe_data(symbol)
        results.append({
            'date': today,
            'ticker': symbol,
            'trailing_pe': trailing,
            'forward_pe': forward,
            'marketCap': market_cap,
        })
        print(f"{symbol} -> Trailing: {trailing}, Forward: {forward}, Market Cap: {market_cap}")
        time.sleep(1)

    # 3. Append to or Create output file
    file_exists = os.path.isfile(OUTPUT_FILE)
    fieldnames = ['date', 'ticker', 'trailing_pe', 'forward_pe', 'marketCap']

    with open(OUTPUT_FILE, mode='a', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        if not file_exists:
            writer.writeheader()
        writer.writerows(results)

    print(f"\nDone! Results saved to {OUTPUT_FILE}")

    # 1. Load the dataset
    file_name = OUTPUT_FILE
    df = pd.read_csv(file_name)

    # 2. Convert the 'date' column to actual datetime objects
    df['date'] = pd.to_datetime(df['date'])

    # 3. Calculate the cutoff date (365 days ago from today)
    cutoff_date = datetime.now() - timedelta(days=365)

    # 4. Filter the dataframe to keep only rows newer than the cutoff
    # We use .copy() to avoid any SettingWithCopy warnings later
    filtered_df = df[df['date'] >= cutoff_date].copy()

    # 5. Optional: Convert the date back to the original string format "YYYY-MM-DD"
    filtered_df['date'] = filtered_df['date'].dt.strftime('%Y-%m-%d')

    # 6. Rewrite the CSV file
    filtered_df.to_csv(file_name, index=False)


def update_missing_prices(file_path):

    # 1. Load the data
    df = pd.read_csv(file_path)

    # 2. Convert date column to datetime objects for math operations
    df['date'] = pd.to_datetime(df['date'])

    # 3. Filter for rows where price is NaN
    # (Assuming 'price' column is named exactly 'price')
    missing_indices = df[df['price'].isna()].index

    if len(missing_indices) == 0:
        print("No missing prices to fill.")
        return

    print(f"Updating {len(missing_indices)} missing entries...")

    for idx in missing_indices:
        ticker = df.at[idx, 'ticker']
        target_date = df.at[idx, 'date']

        # yfinance needs a range: [target_date, target_date + 1 day]
        next_day = target_date + timedelta(days=1)

        try:
            # Fetch data
            data = yf.download(
                ticker,
                start=target_date.strftime('%Y-%m-%d'),
                end=next_day.strftime('%Y-%m-%d'),
                progress=False
            )

            if not data.empty:
                # Extract the Close price
                price = data['Close'].iloc[0][ticker]
                df.at[idx, 'price'] = round(float(price), 2)
                print(f"Found {ticker} on {target_date.date()}: {price:.2f}")
            else:
                print(f"No data for {ticker} on {target_date.date()} (Market might be closed).")

        except Exception as e:
            print(f"Failed to fetch {ticker}: {e}, trying again after 5s...")
            time.sleep(5)
            try:
                # Fetch data
                data = yf.download(
                    ticker,
                    start=target_date.strftime('%Y-%m-%d'),
                    end=next_day.strftime('%Y-%m-%d'),
                    progress=False
                )

                if not data.empty:
                    # Extract the Close price
                    price = data['Close'].iloc[0][ticker]
                    print(price)
                    df.at[idx, 'price'] = round(float(price), 2)
                    print(f"Found {ticker} on {target_date.date()}: {price:.2f}")
                else:
                    print(f"No data for {ticker} on {target_date.date()} (Market might be closed).")

            except Exception as e:
                print(f"Failed to fetch {ticker}: {e}, failed")
                time.sleep(5)


    # 4. Save back to CSV
    # We convert date back to string format to keep the CSV clean
    df['date'] = df['date'].dt.strftime('%Y-%m-%d')
    df.to_csv(file_path, index=False)
    print("Update complete.")

if __name__ == "__main__":
    main()
    update_missing_prices(OUTPUT_FILE)