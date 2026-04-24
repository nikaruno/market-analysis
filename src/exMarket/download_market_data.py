import yfinance as yf
import pandas as pd
import time

def download_index_data(symbol, start="2020-01-01", retries=3, delay=5):
    """Download market data for a given symbol with retry logic."""
    for attempt in range(retries):
        try:
            print(f"  Attempt {attempt + 1}/{retries}...", end=" ")
            df = yf.download(
                symbol,
                start=start,
                auto_adjust=True,
                progress=False
            )
            
            if df.empty:
                print(f"No data returned")
                if attempt < retries - 1:
                    time.sleep(delay)
                    continue
                return None
            
            # Force single-level columns
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = df.columns.get_level_values(0)
            df = df[["Close"]]
            df = df.astype(float)
            df.dropna(inplace=True)
            print(f"✓ Success ({len(df)} rows)")
            return df
            
        except Exception as e:
            print(f"✗ Error: {str(e)[:50]}")
            if attempt < retries - 1:
                print(f"  Waiting {delay} seconds before retry...")
                time.sleep(delay)
            else:
                print(f"  All retries failed for {symbol}")
                return None
    
    return None

if __name__ == "__main__":
    # Dictionary of symbols
    symbols = {
        "SP500": "^GSPC",
        "NASDAQ": "^IXIC",
        "Gold": "GC=F",
        "Bitcoin": "BTC-USD"
    }
    
    print("Downloading market data with rate limit protection...")
    print("=" * 70)
    
    # Download data for each symbol with delays
    dfs = {}
    for i, (name, symbol) in enumerate(symbols.items()):
        print(f"\n[{i+1}/{len(symbols)}] Downloading {name} ({symbol})...")
        
        df = download_index_data(symbol, retries=3, delay=10)
        
        if df is not None and not df.empty:
            dfs[name] = df
        else:
            print(f"  ⚠ Warning: Could not download {name}, skipping...")
        
        # Delay between symbols to avoid rate limiting
        if i < len(symbols) - 1:
            print(f"  Waiting 5 seconds before next download...")
            time.sleep(5)
    
    if not dfs:
        print("\n" + "=" * 70)
        print("✗ ERROR: No data downloaded. Possible reasons:")
        print("  1. Yahoo Finance API is rate limiting (HTTP 429)")
        print("  2. Network connectivity issues")
        print("  3. API temporarily down")
        print("\nSolutions:")
        print("  - Wait 10-15 minutes and try again")
        print("  - Check Yahoo Finance status: https://finance.yahoo.com")
        print("  - Try running outside Docker to test")
        print("=" * 70)
        exit(1)
    
    # Combine all dataframes
    print("\n" + "=" * 70)
    print(f"Successfully downloaded {len(dfs)}/{len(symbols)} assets")
    
    combined_df = pd.concat(dfs, axis=1)
    combined_df.columns = [f"{name}_Close" for name in dfs.keys()]
    combined_df = combined_df.dropna()
    
    # Save to CSV
    output_path = "data/market_data.csv"
    combined_df.to_csv(output_path, index=True)
    
    print("\nCombined data preview:")
    print(combined_df.head())
    print(f"\nShape: {combined_df.shape}")
    print(f"Date range: {combined_df.index.min()} to {combined_df.index.max()}")
    print(f"\nData saved to: {output_path}")
    print("=" * 70)
