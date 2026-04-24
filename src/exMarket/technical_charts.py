"""
Technical Analysis Visualization
Creates comprehensive technical charts for stocks
"""

import yfinance as yf
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
from datetime import datetime, timedelta
from pathlib import Path
import numpy as np

OUTPUT_DIR = Path("data/technical_charts")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

def plot_technical_chart(ticker, days=180):
    """
    Create comprehensive technical analysis chart with multiple indicators.
    """
    try:
        # Download data
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days + 100)
        
        df = yf.download(ticker, start=start_date, end=end_date, progress=False)
        
        if df.empty or len(df) < 50:
            print(f"  [WARN] Insufficient data for {ticker}")
            return None
        
        # Handle multi-level columns
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
        
        # Calculate indicators (import from technical_analysis module)
        from technical_analysis import (
            calculate_rsi, calculate_macd, calculate_bollinger_bands,
            calculate_atr, calculate_stochastic
        )
        
        close = df['Close']
        high = df['High']
        low = df['Low']
        volume = df['Volume']
        
        # Indicators
        rsi = calculate_rsi(close)
        macd_line, signal_line, histogram = calculate_macd(close)
        bb_upper, bb_middle, bb_lower = calculate_bollinger_bands(close)
        stoch_k, stoch_d = calculate_stochastic(high, low, close)
        sma_50 = close.rolling(window=50).mean()
        sma_200 = close.rolling(window=200).mean()
        
        # Trim to requested days
        df = df.tail(days)
        close = close.tail(days)
        high = high.tail(days)
        low = low.tail(days)
        volume = volume.tail(days)
        rsi = rsi.tail(days)
        macd_line = macd_line.tail(days)
        signal_line = signal_line.tail(days)
        histogram = histogram.tail(days)
        bb_upper = bb_upper.tail(days)
        bb_middle = bb_middle.tail(days)
        bb_lower = bb_lower.tail(days)
        stoch_k = stoch_k.tail(days)
        stoch_d = stoch_d.tail(days)
        sma_50 = sma_50.tail(days)
        sma_200 = sma_200.tail(days)
        
        # Create figure with subplots
        fig = plt.figure(figsize=(16, 12))
        gs = gridspec.GridSpec(5, 1, height_ratios=[3, 1, 1, 1, 1], hspace=0.3)
        
        # === SUBPLOT 1: Price with Bollinger Bands and MAs ===
        ax1 = plt.subplot(gs[0])
        
        # Plot price and Bollinger Bands
        ax1.plot(df.index, close, label='Close Price', color='black', linewidth=1.5, zorder=3)
        ax1.plot(df.index, bb_upper, label='BB Upper', color='gray', linestyle='--', linewidth=1, alpha=0.7)
        ax1.plot(df.index, bb_middle, label='BB Middle (SMA 20)', color='blue', linestyle='--', linewidth=1)
        ax1.plot(df.index, bb_lower, label='BB Lower', color='gray', linestyle='--', linewidth=1, alpha=0.7)
        ax1.fill_between(df.index, bb_lower, bb_upper, alpha=0.1, color='gray')
        
        # Plot moving averages
        if not sma_50.isna().all():
            ax1.plot(df.index, sma_50, label='SMA 50', color='orange', linewidth=1.5, alpha=0.8)
        if not sma_200.isna().all():
            ax1.plot(df.index, sma_200, label='SMA 200', color='red', linewidth=1.5, alpha=0.8)
        
        ax1.set_title(f'{ticker} - Technical Analysis', fontsize=14, fontweight='bold')
        ax1.set_ylabel('Price ($)', fontsize=11)
        ax1.legend(loc='upper left', fontsize=9)
        ax1.grid(True, alpha=0.3)
        
        # === SUBPLOT 2: Volume ===
        ax2 = plt.subplot(gs[1], sharex=ax1)
        colors = ['green' if close.iloc[i] >= close.iloc[i-1] else 'red' 
                  for i in range(1, len(close))]
        colors = ['gray'] + colors  # First bar gray
        ax2.bar(df.index, volume, color=colors, alpha=0.5, width=0.8)
        ax2.set_ylabel('Volume', fontsize=10)
        ax2.grid(True, alpha=0.3)
        
        # === SUBPLOT 3: RSI ===
        ax3 = plt.subplot(gs[2], sharex=ax1)
        ax3.plot(df.index, rsi, label='RSI (14)', color='purple', linewidth=1.5)
        ax3.axhline(y=70, color='red', linestyle='--', linewidth=1, alpha=0.7, label='Overbought (70)')
        ax3.axhline(y=30, color='green', linestyle='--', linewidth=1, alpha=0.7, label='Oversold (30)')
        ax3.fill_between(df.index, 30, 70, alpha=0.1, color='gray')
        ax3.set_ylabel('RSI', fontsize=10)
        ax3.set_ylim(0, 100)
        ax3.legend(loc='upper left', fontsize=8)
        ax3.grid(True, alpha=0.3)
        
        # === SUBPLOT 4: MACD ===
        ax4 = plt.subplot(gs[3], sharex=ax1)
        ax4.plot(df.index, macd_line, label='MACD', color='blue', linewidth=1.5)
        ax4.plot(df.index, signal_line, label='Signal', color='red', linewidth=1.5)
        
        # Histogram with colors
        colors = ['green' if h > 0 else 'red' for h in histogram]
        ax4.bar(df.index, histogram, label='Histogram', color=colors, alpha=0.5, width=0.8)
        
        ax4.axhline(y=0, color='black', linestyle='-', linewidth=0.5)
        ax4.set_ylabel('MACD', fontsize=10)
        ax4.legend(loc='upper left', fontsize=8)
        ax4.grid(True, alpha=0.3)
        
        # === SUBPLOT 5: Stochastic ===
        ax5 = plt.subplot(gs[4], sharex=ax1)
        ax5.plot(df.index, stoch_k, label='%K', color='blue', linewidth=1.5)
        ax5.plot(df.index, stoch_d, label='%D', color='red', linewidth=1.5)
        ax5.axhline(y=80, color='red', linestyle='--', linewidth=1, alpha=0.7)
        ax5.axhline(y=20, color='green', linestyle='--', linewidth=1, alpha=0.7)
        ax5.fill_between(df.index, 20, 80, alpha=0.1, color='gray')
        ax5.set_ylabel('Stochastic', fontsize=10)
        ax5.set_xlabel('Date', fontsize=10)
        ax5.set_ylim(0, 100)
        ax5.legend(loc='upper left', fontsize=8)
        ax5.grid(True, alpha=0.3)
        
        # Format x-axis
        plt.setp(ax1.get_xticklabels(), visible=False)
        plt.setp(ax2.get_xticklabels(), visible=False)
        plt.setp(ax3.get_xticklabels(), visible=False)
        plt.setp(ax4.get_xticklabels(), visible=False)
        
        # Rotate date labels
        plt.xticks(rotation=45)
        
        # Save
        output_path = OUTPUT_DIR / f"{ticker}_technical.png"
        plt.tight_layout()
        plt.savefig(output_path, dpi=150, bbox_inches='tight')
        plt.close(fig)
        
        print(f"  ✓ Chart saved: {output_path}")
        return output_path
        
    except Exception as e:
        print(f"  [ERROR] Failed to create chart for {ticker}: {e}")
        return None

def create_technical_summary_chart(tech_df, top_n=10):
    """
    Create summary chart showing technical scores vs quality scores.
    """
    try:
        top_stocks = tech_df.nlargest(top_n, 'combined_score')
        
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 6))
        
        # Chart 1: Quality vs Technical Scores
        ax1.scatter(top_stocks['quality_score'], top_stocks['technical_score'], 
                   s=100, alpha=0.6, c='blue')
        
        for idx, row in top_stocks.iterrows():
            ax1.annotate(row['ticker'], 
                        (row['quality_score'], row['technical_score']),
                        fontsize=9, ha='center', va='bottom')
        
        ax1.set_xlabel('Quality Score', fontsize=12)
        ax1.set_ylabel('Technical Score', fontsize=12)
        ax1.set_title('Quality vs Technical Scores', fontsize=14, fontweight='bold')
        ax1.grid(True, alpha=0.3)
        
        # Add quadrant lines
        ax1.axhline(y=50, color='gray', linestyle='--', alpha=0.5)
        ax1.axvline(x=50, color='gray', linestyle='--', alpha=0.5)
        
        # Chart 2: Combined Score Ranking
        top_stocks_sorted = top_stocks.sort_values('combined_score', ascending=True)
        
        colors = ['green' if score >= 60 else 'orange' if score >= 50 else 'red' 
                  for score in top_stocks_sorted['combined_score']]
        
        ax2.barh(range(len(top_stocks_sorted)), top_stocks_sorted['combined_score'], 
                color=colors, alpha=0.7)
        ax2.set_yticks(range(len(top_stocks_sorted)))
        ax2.set_yticklabels(top_stocks_sorted['ticker'])
        ax2.set_xlabel('Combined Score (Quality + Technical) / 2', fontsize=12)
        ax2.set_title(f'Top {top_n} Combined Scores', fontsize=14, fontweight='bold')
        ax2.grid(True, alpha=0.3, axis='x')
        
        plt.tight_layout()
        output_path = OUTPUT_DIR / "technical_summary.png"
        plt.savefig(output_path, dpi=150, bbox_inches='tight')
        plt.close(fig)
        
        print(f"\n✓ Summary chart saved: {output_path}")
        return output_path
        
    except Exception as e:
        print(f"[ERROR] Failed to create summary chart: {e}")
        return None

def generate_all_charts(tech_df, top_n=5):
    """
    Generate technical charts for top N stocks.
    """
    print(f"\n{'='*80}")
    print(f"GENERATING TECHNICAL CHARTS FOR TOP {top_n} STOCKS")
    print("="*80)
    
    # Get top stocks by combined score
    top_stocks = tech_df.nlargest(top_n, 'combined_score')
    
    charts_created = []
    
    for idx, row in top_stocks.iterrows():
        ticker = row['ticker']
        print(f"\n[{len(charts_created)+1}/{top_n}] Creating chart for {ticker}...")
        
        chart_path = plot_technical_chart(ticker, days=180)
        if chart_path:
            charts_created.append(chart_path)
    
    # Create summary chart
    print(f"\nCreating technical summary chart...")
    summary_path = create_technical_summary_chart(tech_df, top_n=10)
    
    print(f"\n{'='*80}")
    print(f"CHART GENERATION COMPLETE")
    print("="*80)
    print(f"Individual charts: {len(charts_created)}")
    print(f"Charts saved to: {OUTPUT_DIR}")
    print("="*80)
    
    return charts_created

if __name__ == "__main__":
    # Load technical analysis results
    import pandas as pd
    
    tech_path = Path("data/technical_analysis.csv")
    
    if not tech_path.exists():
        print("[ERROR] Technical analysis results not found.")
        print("Please run technical_analysis.py first.")
    else:
        tech_df = pd.read_csv(tech_path)
        generate_all_charts(tech_df, top_n=5)
