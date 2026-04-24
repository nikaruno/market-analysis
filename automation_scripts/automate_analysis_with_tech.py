#!/usr/bin/env python3
"""
COMPLETE MARKET & FUNDAMENTAL & TECHNICAL ANALYSIS AUTOMATION
Includes technical indicators and enhanced 3-page report

Usage:
    python3 automate_analysis_with_tech.py
"""

import sys
import os
from pathlib import Path
from datetime import datetime
import pandas as pd

sys.path.insert(0, 'src/exMarket')

def main():
    """Run complete automated pipeline with technical analysis."""
    
    start_time = datetime.now()
    
    print("╔" + "="*78 + "╗")
    print("║" + "  AUTOMATED MARKET, FUNDAMENTAL & TECHNICAL ANALYSIS".center(78) + "║")
    print("╚" + "="*78 + "╝")
    print(f"\nStarted: {start_time.strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    steps = []
    
    # ===== STEP 1: Download Market Data =====
    try:
        print("▶ Step 1/9: Downloading Market Data...")
        from download_market_data import download_index_data
        import yfinance as yf
        import pandas as pd
        
        symbols = {
            "SP500": "^GSPC",
            "NASDAQ": "^IXIC",
            "Gold": "GC=F",
            "Bitcoin": "BTC-USD"
        }
        
        dfs = {}
        for name, symbol in symbols.items():
            print(f"  Downloading {name}...")
            dfs[name] = download_index_data(symbol, start="2020-01-01")
        
        combined_df = pd.concat(dfs, axis=1)
        combined_df.columns = [f"{name}_Close" for name in symbols.keys()]
        combined_df = combined_df.dropna()
        combined_df.to_csv("data/market_data.csv", index=True)
        
        print(f"  ✓ Downloaded {len(combined_df)} days of data")
        steps.append(("Download Market Data", "SUCCESS"))
    except Exception as e:
        print(f"  ✗ Failed: {e}")
        steps.append(("Download Market Data", "FAILED"))
    
    # ===== STEP 2: Compute Market Regimes =====
    try:
        print("\n▶ Step 2/9: Computing Market Regimes...")
        from market_regime import compute_regime
        
        df = pd.read_csv("data/market_data.csv", index_col=0, parse_dates=True)
        df_with_regimes = compute_regime(df)
        df_with_regimes.to_csv("data/market_data_with_regimes.csv", index=True)
        
        print(f"  ✓ Regimes computed")
        steps.append(("Compute Market Regimes", "SUCCESS"))
    except Exception as e:
        print(f"  ✗ Failed: {e}")
        steps.append(("Compute Market Regimes", "FAILED"))
    
    # ===== STEP 3: Generate Market Visualizations =====
    try:
        print("\n▶ Step 3/9: Generating Market Visualizations...")
        from visualize import plot_all_assets, plot_regime_comparison, plot_regime_heatmap
        
        df = pd.read_csv("data/market_data_with_regimes.csv", index_col=0, parse_dates=True)
        
        plot_all_assets(df, output_dir="data/plots")
        plot_regime_comparison(df, output_path="data/regime_comparison.png")
        plot_regime_heatmap(df, output_path="data/regime_heatmap.png")
        
        print(f"  ✓ Created visualization files")
        steps.append(("Generate Visualizations", "SUCCESS"))
    except Exception as e:
        print(f"  ✗ Failed: {e}")
        steps.append(("Generate Visualizations", "FAILED"))
    
    # ===== STEP 4: Scrape Fundamentals =====
    try:
        print("\n▶ Step 4/9: Scraping Top Companies...")
        
        fund_path = Path("data/fundamentals_raw.csv")
        if fund_path.exists():
            mod_time = datetime.fromtimestamp(fund_path.stat().st_mtime)
            age_hours = (datetime.now() - mod_time).total_seconds() / 3600
            
            if age_hours < 24:
                print(f"  ⚠ Using cached data from {age_hours:.1f} hours ago")
                steps.append(("Scrape Fundamentals", "CACHED"))
            else:
                from scrape_fundamentals import main as scrape_main
                scrape_main()
                steps.append(("Scrape Fundamentals", "SUCCESS"))
        else:
            from scrape_fundamentals import main as scrape_main
            scrape_main()
            steps.append(("Scrape Fundamentals", "SUCCESS"))
            
    except Exception as e:
        print(f"  ✗ Failed: {e}")
        steps.append(("Scrape Fundamentals", "FAILED"))
    
    # ===== STEP 5: Download Detailed Fundamentals =====
    try:
        print("\n▶ Step 5/9: Downloading Detailed Financial Statements...")
        
        detail_dir = Path("data/fundamentals/raw")
        fund_path = Path("data/fundamentals_raw.csv")
        CACHE_MAX_DAYS = 7  # Re-download all if data older than 7 days
        
        needs_full_download = False
        needs_incremental = False
        missing_tickers = []
        
        if not detail_dir.exists() or len(list(detail_dir.glob("*_income.csv"))) == 0:
            # No data at all
            needs_full_download = True
            print(f"  No cached data found — full download needed")
        else:
            # Check age of existing files
            income_files = list(detail_dir.glob("*_income.csv"))
            if income_files:
                oldest_file = min(income_files, key=lambda f: f.stat().st_mtime)
                oldest_age_days = (datetime.now() - datetime.fromtimestamp(oldest_file.stat().st_mtime)).total_seconds() / 86400
                
                if oldest_age_days > CACHE_MAX_DAYS:
                    needs_full_download = True
                    print(f"  ⚠ Cached data is {oldest_age_days:.1f} days old (limit: {CACHE_MAX_DAYS} days) — full re-download")
                else:
                    print(f"  Cache age: {oldest_age_days:.1f} days (limit: {CACHE_MAX_DAYS} days) — OK")
            
            # Check for missing tickers (e.g. newly added BIST stocks)
            if not needs_full_download and fund_path.exists():
                universe_df_check = pd.read_csv(fund_path)
                for _, row in universe_df_check.iterrows():
                    ticker = row['ticker']
                    safe_ticker = ticker.replace('.', '_')
                    if not (detail_dir / f"{safe_ticker}_income.csv").exists():
                        missing_tickers.append(ticker)
                
                if missing_tickers:
                    needs_incremental = True
                    print(f"  Found {len(missing_tickers)} new tickers to download: {missing_tickers}")
        
        if needs_full_download:
            # Full re-download
            from download_detailed_fundamentals import main as download_main
            download_main()
            steps.append(("Download Detailed Fundamentals", "SUCCESS"))
        
        elif needs_incremental:
            # Download only missing tickers
            from download_detailed_fundamentals import download_company
            
            universe_df_inc = pd.read_csv(fund_path)
            success_inc = 0
            fail_inc = 0
            
            for ticker in missing_tickers:
                row = universe_df_inc[universe_df_inc['ticker'] == ticker].iloc[0]
                category = row.get('category', None)
                region = row.get('region', 'global')
                print(f"  Downloading new ticker: {ticker} ({category}, {region})")
                
                if download_company(ticker, category, region=region):
                    success_inc += 1
                else:
                    fail_inc += 1
            
            print(f"  Incremental download: {success_inc} success, {fail_inc} failed")
            steps.append(("Download Detailed Fundamentals", f"INCREMENTAL ({success_inc} new)"))
        
        else:
            existing_count = len(list(detail_dir.glob("*_income.csv")))
            print(f"  ⚠ Using cached detailed fundamentals ({existing_count} companies)")
            steps.append(("Download Detailed Fundamentals", "CACHED"))
            
    except Exception as e:
        print(f"  ✗ Failed: {e}")
        import traceback
        traceback.print_exc()
        steps.append(("Download Detailed Fundamentals", "FAILED"))
    
    # ===== STEP 6: Compute Quality Metrics =====
    try:
        print("\n▶ Step 6/9: Computing Company Quality Metrics...")
        from compute_detailed_metrics import main as metrics_main
        metrics_main()
        
        steps.append(("Compute Quality Metrics", "SUCCESS"))
    except Exception as e:
        print(f"  ✗ Failed: {e}")
        steps.append(("Compute Quality Metrics", "FAILED"))
    
    # ===== STEP 7: Compute Absolute Rankings =====
    try:
        print("\n▶ Step 7/9: Computing Absolute Quality Rankings...")
        from absolute_scores import main as scores_main
        scores_main()
        
        steps.append(("Compute Absolute Rankings", "SUCCESS"))
    except Exception as e:
        print(f"  ✗ Failed: {e}")
        steps.append(("Compute Absolute Rankings", "FAILED"))
    
    # ===== STEP 8: Technical Analysis =====
    try:
        print("\n▶ Step 8/9: Performing Technical Analysis...")
        from technical_analysis import analyze_top_stocks
        
        tech_df = analyze_top_stocks(top_n=None)  # Analyze ALL stocks, not just top N
        
        if tech_df is not None:
            print(f"  ✓ Technical analysis completed for {len(tech_df)} stocks")
            steps.append(("Technical Analysis", "SUCCESS"))
            
            # Generate technical charts
            print("\n  Generating technical charts...")
            from technical_charts import generate_all_charts
            generate_all_charts(tech_df, top_n=5)
        else:
            steps.append(("Technical Analysis", "FAILED"))
            
    except Exception as e:
        print(f"  ✗ Failed: {e}")
        import traceback
        traceback.print_exc()
        steps.append(("Technical Analysis", "FAILED"))
    
    # ===== STEP 9: Generate Enhanced Report =====
    try:
        print("\n▶ Step 9/9: Generating Enhanced Executive Summary...")
        
        sys.path.insert(0, str(Path(__file__).parent))
        from report_generator_enhanced import generate_report
        
        generate_report()
        
        steps.append(("Generate Enhanced Report", "SUCCESS"))
    except Exception as e:
        print(f"  ✗ Failed: {e}")
        import traceback
        traceback.print_exc()
        steps.append(("Generate Enhanced Report", "FAILED"))
    
    # ===== SUMMARY =====
    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds()
    
    print("\n\n╔" + "="*78 + "╗")
    print("║" + "  PIPELINE COMPLETED".center(78) + "║")
    print("╚" + "="*78 + "╝")
    
    print(f"\nExecution Time: {duration:.0f} seconds ({duration/60:.1f} minutes)")
    print("\nResults:")
    print("-" * 80)
    
    for step, status in steps:
        symbol = "✓" if status == "SUCCESS" else ("⚠" if status == "CACHED" else "✗")
        print(f"  {symbol} {step}: {status}")
    
    print("-" * 80)
    
    successes = sum(1 for _, s in steps if s in ["SUCCESS", "CACHED"])
    total = len(steps)
    
    print(f"\nSuccess Rate: {successes}/{total} ({successes/total*100:.0f}%)")
    
    # Output files
    print("\n📁 Key Output Files:")
    print("-" * 80)
    
    output_files = [
        ("data/executive_summary.md", "Enhanced 3-page report"),
        ("data/technical_analysis.csv", "Technical indicators data"),
        ("data/fundamentals/absolute_scores.csv", "Quality rankings"),
        ("data/technical_charts/technical_summary.png", "Technical summary chart"),
    ]
    
    for filepath, description in output_files:
        path = Path(filepath)
        if path.exists():
            size = path.stat().st_size
            print(f"  ✓ {description}")
            print(f"    {filepath}")
        else:
            print(f"  ✗ {description} (not found)")
    
    print("-" * 80)
    
    # Final message
    report_path = Path("data/executive_summary.md")
    if report_path.exists():
        print(f"\n🎉 SUCCESS! Enhanced 3-page report ready:")
        print(f"   {report_path}")
        print("\n📊 Technical charts available in:")
        print(f"   data/technical_charts/")
    else:
        print("\n⚠️  Pipeline completed but report was not generated.")
    
    print("\n" + "="*80 + "\n")

if __name__ == "__main__":
    main()
