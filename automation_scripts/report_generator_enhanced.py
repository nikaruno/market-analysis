"""
Enhanced Executive Summary Report Generator
Combines market regime, fundamental analysis, and technical analysis
Maximum 3 pages with charts
"""

import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime

# Paths
DATA_DIR = Path("data")
REPORT_PATH = DATA_DIR / "executive_summary.md"

def format_pct(value):
    """Format percentage values."""
    if pd.isna(value):
        return "N/A"
    return f"{value*100:.1f}%"

def format_number(value):
    """Format numerical values."""
    if pd.isna(value):
        return "N/A"
    return f"{value:.2f}"

def generate_report():
    """Generate comprehensive executive summary report."""
    
    lines = []
    
    # ===== HEADER =====
    lines.append("# 📊 Market & Investment Analysis Executive Summary")
    lines.append(f"*Generated: {datetime.now().strftime('%B %d, %Y at %I:%M %p')}*")
    lines.append("")
    lines.append("---")
    lines.append("")
    
    # ===== SECTION 1: MARKET REGIME =====
    lines.append("## 🎯 Section 1: Current Market Environment")
    lines.append("")
    
    try:
        regime_df = pd.read_csv(DATA_DIR / "market_data_with_regimes.csv", index_col=0, parse_dates=True)
        latest = regime_df.iloc[-1]
        last_30 = regime_df.tail(30)
        
        if "Market_Regime" in regime_df.columns:
            market_regime = latest["Market_Regime"]
            market_score = latest["Market_RegimeScore"]
            
            emoji = "🟢" if market_regime == "Risk-On" else ("🔴" if market_regime == "Risk-Off" else "🟡")
            lines.append(f"**Overall Market Regime:** {emoji} **{market_regime}** (Score: {market_score:.2f})")
            lines.append("")
        
        lines.append("**Asset-Level Regimes:**")
        lines.append("")
        lines.append("| Asset | Current Regime | Score | Price Trend |")
        lines.append("|-------|---------------|-------|-------------|")
        
        for asset in ["SP500", "NASDAQ", "Gold", "Bitcoin"]:
            regime_col = f"{asset}_Regime"
            score_col = f"{asset}_RegimeScore"
            close_col = f"{asset}_Close"
            
            if regime_col in regime_df.columns:
                regime = latest[regime_col]
                score = latest[score_col]
                
                # Calculate trend
                price_30d_ago = regime_df[close_col].iloc[-30]
                price_now = latest[close_col]
                trend = ((price_now / price_30d_ago) - 1) * 100
                
                emoji = "🟢" if regime == "Risk-On" else ("🔴" if regime == "Risk-Off" else "🟡")
                trend_arrow = "📈" if trend > 0 else "📉"
                
                lines.append(f"| {asset} | {emoji} {regime} | {score:.2f} | {trend_arrow} {trend:+.1f}% |")
        
        lines.append("")
        
    except Exception as e:
        lines.append(f"*Market regime data unavailable: {e}*")
        lines.append("")
    
    # ===== SECTION 2: FUNDAMENTAL QUALITY =====
    lines.append("---")
    lines.append("")
    lines.append("## 🏆 Section 2: Top Fundamental Quality Stocks")
    lines.append("")
    
    try:
        scores_df = pd.read_csv(DATA_DIR / "fundamentals" / "absolute_scores.csv")
        
        # Split by region
        if 'region' in scores_df.columns:
            global_scores = scores_df[scores_df['region'] != 'turkey']
            bist_scores = scores_df[scores_df['region'] == 'turkey']
        else:
            global_scores = scores_df
            bist_scores = pd.DataFrame()
        
        lines.append("### 🌐 Global / US Stocks")
        lines.append("")
        lines.append("| # | Ticker | Category | Quality | ROIC | FCF % | Growth |")
        lines.append("|---|--------|----------|---------|------|-------|--------|")
        
        top_15 = global_scores.nlargest(15, 'quality_score')
        
        for idx, row in enumerate(top_15.itertuples(), 1):
            ticker = row.ticker
            category = getattr(row, 'category', 'N/A')[:10]
            quality = row.quality_score
            roic = format_pct(getattr(row, 'roic_avg', np.nan))
            fcf = format_pct(getattr(row, 'fcf_margin', np.nan))
            growth = format_pct(getattr(row, 'revenue_cagr', np.nan))
            
            lines.append(f"| {idx} | **{ticker}** | {category} | {quality:.0f} | {roic} | {fcf} | {growth} |")
        
        lines.append("")
        
        # Category leaders (global)
        if 'category' in global_scores.columns:
            lines.append("**Best in Each Category (Global):**")
            lines.append("")
            lines.append("| Category | Leader | Quality | ROIC |")
            lines.append("|----------|--------|---------|------|")
            
            for category in sorted(global_scores['category'].dropna().unique()):
                cat_df = global_scores[global_scores['category'] == category]
                best = cat_df.nlargest(1, 'quality_score').iloc[0]
                lines.append(f"| {category} | **{best['ticker']}** | {best['quality_score']:.0f} | {format_pct(best.get('roic_avg', np.nan))} |")
            lines.append("")
        
        # BIST section
        if len(bist_scores) > 0:
            lines.append("### 🇹🇷 BIST Stocks (Borsa Istanbul — fundamentals in USD)")
            lines.append("")
            lines.append("*Quality metrics computed on USD-converted statements for fair comparison with US peers. "
                         "Technical analysis uses native TL prices (see Section 3).*")
            lines.append("")
            lines.append("| # | Ticker | Sector | Quality | ROIC | FCF % | Growth |")
            lines.append("|---|--------|--------|---------|------|-------|--------|")
            
            bist_top = bist_scores.nlargest(min(15, len(bist_scores)), 'quality_score')
            for idx, row in enumerate(bist_top.itertuples(), 1):
                ticker = row.ticker
                category = getattr(row, 'category', 'N/A')
                quality = row.quality_score
                roic = format_pct(getattr(row, 'roic_avg', np.nan))
                fcf = format_pct(getattr(row, 'fcf_margin', np.nan))
                growth = format_pct(getattr(row, 'revenue_cagr', np.nan))
                lines.append(f"| {idx} | **{ticker}** | {category} | {quality:.0f} | {roic} | {fcf} | {growth} |")
            lines.append("")
        
    except Exception as e:
        lines.append(f"*Fundamental data unavailable: {e}*")
        lines.append("")
    
    # ===== SECTION 3: TECHNICAL ANALYSIS =====
    lines.append("---")
    lines.append("")
    lines.append("## 📈 Section 3: Technical Analysis Signals")
    lines.append("")
    
    try:
        tech_df = pd.read_csv(DATA_DIR / "technical_analysis.csv")
        
        lines.append("**Top 10 Combined Scores (Fundamentals + Technicals):**")
        lines.append("")
        lines.append("| # | Ticker | Combined | Quality | Technical | Rating | RSI | Trend |")
        lines.append("|---|--------|----------|---------|-----------|--------|-----|-------|")
        
        tech_df['combined_score'] = (tech_df['quality_score'] + tech_df['technical_score']) / 2
        top_combined = tech_df.nlargest(10, 'combined_score')
        
        for idx, row in enumerate(top_combined.itertuples(), 1):
            ticker = row.ticker
            combined = row.combined_score
            quality = row.quality_score
            technical = row.technical_score
            rating = row.technical_rating
            rsi = row.rsi
            trend = row.ma_trend
            
            # Color code rating
            rating_emoji = "🟢" if "Buy" in rating else ("🔴" if "Sell" in rating else "🟡")
            
            lines.append(f"| {idx} | **{ticker}** | {combined:.0f} | {quality:.0f} | {technical:.0f} | {rating_emoji} {rating} | {rsi:.0f} | {trend} |")
        
        lines.append("")
        
        # Technical signals breakdown
        lines.append("**Current Technical Signals:**")
        lines.append("")
        
        # Oversold/Overbought opportunities
        oversold = tech_df[tech_df['rsi'] < 30].nlargest(5, 'quality_score')
        overbought = tech_df[tech_df['rsi'] > 70].nlargest(5, 'quality_score')
        
        if len(oversold) > 0:
            lines.append("*Oversold Opportunities (RSI < 30):*")
            for _, row in oversold.iterrows():
                lines.append(f"- **{row['ticker']}**: RSI {row['rsi']:.0f}, Quality {row['quality_score']:.0f}")
            lines.append("")
        
        if len(overbought) > 0:
            lines.append("*Overbought Warnings (RSI > 70):*")
            for _, row in overbought.iterrows():
                lines.append(f"- **{row['ticker']}**: RSI {row['rsi']:.0f}, Quality {row['quality_score']:.0f}")
            lines.append("")
        
        # Bullish MACD crossovers
        bullish_macd = tech_df[tech_df['macd_crossover'] == 'Bullish'].nlargest(5, 'quality_score')
        if len(bullish_macd) > 0:
            lines.append("*Recent Bullish MACD Crossovers:*")
            for _, row in bullish_macd.iterrows():
                lines.append(f"- **{row['ticker']}**: Quality {row['quality_score']:.0f}, Technical {row['technical_score']:.0f}")
            lines.append("")
        
        # Strong trends
        strong_uptrends = tech_df[
            (tech_df['ma_trend'] == 'Uptrend') & 
            (tech_df['trend_strength'] == 'Strong')
        ].nlargest(5, 'quality_score')
        
        if len(strong_uptrends) > 0:
            lines.append("*Strong Uptrends (ADX > 25):*")
            for _, row in strong_uptrends.iterrows():
                adx = row.get('adx', np.nan)
                lines.append(f"- **{row['ticker']}**: ADX {adx:.0f}, Quality {row['quality_score']:.0f}")
            lines.append("")
        
        # Technical rating distribution
        lines.append("**Technical Rating Distribution:**")
        lines.append("")
        rating_counts = tech_df['technical_rating'].value_counts()
        for rating, count in rating_counts.items():
            emoji = "🟢" if "Buy" in rating else ("🔴" if "Sell" in rating else "🟡")
            lines.append(f"- {emoji} {rating}: {count} stocks")
        lines.append("")

        # BIST dual rating (TL primary, USD secondary)
        if 'technical_score_usd' in tech_df.columns:
            bist_tech = tech_df[
                (tech_df['ticker'].str.upper().str.endswith('.IS')) &
                (tech_df['technical_score_usd'].notna())
            ]
            if len(bist_tech) > 0:
                lines.append("**🇹🇷 BIST Dual Rating — TL (primary) vs USD (secondary):**")
                lines.append("")
                lines.append("*USD ratings tend to be lower because TRY depreciation pulls "
                             "moving-average voters toward Sell. The TL view matches "
                             "TradingView; the USD view shows what a USD-based investor sees.*")
                lines.append("")
                lines.append("| Ticker | TL Score | TL Rating | USD Score | USD Rating | Δ |")
                lines.append("|--------|----------|-----------|-----------|------------|---|")
                bist_sorted = bist_tech.sort_values('technical_score', ascending=False)
                for _, row in bist_sorted.iterrows():
                    tl_score = row['technical_score']
                    tl_rating = row['technical_rating']
                    usd_score = row['technical_score_usd']
                    usd_rating = row.get('technical_rating_usd', 'N/A')
                    delta = usd_score - tl_score
                    lines.append(f"| **{row['ticker']}** | {tl_score:.0f} | {tl_rating} | "
                                 f"{usd_score:.0f} | {usd_rating} | {delta:+.0f} |")
                lines.append("")

    except Exception as e:
        lines.append(f"*Technical analysis data unavailable: {e}*")
        lines.append("")
    
    # ===== SECTION 4: ACTION ITEMS =====
    lines.append("---")
    lines.append("")
    lines.append("## 💡 Section 4: Investment Recommendations")
    lines.append("")
    
    try:
        if 'regime_df' in locals() and 'scores_df' in locals() and 'tech_df' in locals():
            market_regime = latest.get("Market_Regime", "Neutral")
            
            lines.append(f"**Current Strategy: Based on {market_regime} Market**")
            lines.append("")
            
            # Best opportunities (high quality + good technicals)
            best_opps = tech_df[
                (tech_df['quality_score'] > 70) & 
                (tech_df['technical_score'] > 60)
            ].nlargest(5, 'combined_score')
            
            if len(best_opps) > 0:
                lines.append("### 🎯 **Top 5 Buy Candidates** (High Quality + Good Technicals):")
                lines.append("")
                for idx, row in enumerate(best_opps.itertuples(), 1):
                    ticker = row.ticker
                    category = row.category
                    quality = row.quality_score
                    technical = row.technical_score
                    rsi = row.rsi
                    rating = row.technical_rating
                    
                    lines.append(f"{idx}. **{ticker}** ({category})")
                    lines.append(f"   - Quality: {quality:.0f}/100, Technical: {technical:.0f}/100")
                    lines.append(f"   - RSI: {rsi:.0f}, Rating: {rating}")
                    
                    # Add specific entry logic
                    if rsi < 40:
                        lines.append(f"   - 💡 *Entry signal: RSI showing value*")
                    if row.ma_trend == 'Uptrend':
                        lines.append(f"   - 📈 *Trend: Price above key moving averages*")
                    
                    lines.append("")
            
            # Avoid list
            avoid = tech_df[
                (tech_df['technical_score'] < 40) |
                ((tech_df['rsi'] > 75) & (tech_df['technical_score'] < 60))
            ].nsmallest(3, 'technical_score')
            
            if len(avoid) > 0:
                lines.append("### ⚠️ **Caution List** (Poor Technicals):")
                lines.append("")
                for _, row in avoid.iterrows():
                    reason = "Extended (RSI > 75)" if row['rsi'] > 75 else "Weak technicals"
                    lines.append(f"- **{row['ticker']}**: {reason}, Technical Score: {row['technical_score']:.0f}")
                lines.append("")
            
            # Portfolio allocation suggestion
            lines.append("### 📊 **Suggested Portfolio Allocation:**")
            lines.append("")
            
            if market_regime == "Risk-On":
                lines.append("- **60%** Core positions (Top 5 combined scores)")
                lines.append("- **30%** Growth opportunities (High revenue CAGR + good technicals)")
                lines.append("- **10%** Cash / Defensive hedge")
            elif market_regime == "Risk-Off":
                lines.append("- **40%** High quality defensive (Low debt, high cash flow)")
                lines.append("- **30%** Oversold quality names (RSI < 30, Quality > 70)")
                lines.append("- **30%** Cash / Safe haven assets")
            else:  # Neutral
                lines.append("- **50%** Top combined scores (balanced approach)")
                lines.append("- **30%** Sector diversification (best in each category)")
                lines.append("- **20%** Opportunistic / Cash")
            
            lines.append("")
            
    except Exception as e:
        lines.append(f"*Recommendations unavailable: {e}*")
        lines.append("")
    
    # ===== SECTION 5: CHARTS & VISUALIZATIONS =====
    lines.append("---")
    lines.append("")
    lines.append("## 📊 Section 5: Key Charts")
    lines.append("")
    
    lines.append("**Available Visualizations:**")
    lines.append("")
    lines.append("1. **Market Regime Charts:**")
    lines.append("   - `data/regime_comparison.png` - Multi-asset regime comparison")
    lines.append("   - `data/regime_heatmap.png` - Regime timeline heatmap")
    lines.append("   - `data/plots/[asset]_regime.png` - Individual asset charts")
    lines.append("")
    lines.append("2. **Technical Analysis Charts:**")
    lines.append("   - `data/technical_charts/technical_summary.png` - Quality vs Technical scores")
    lines.append("   - `data/technical_charts/[ticker]_technical.png` - Individual stock technical charts")
    lines.append("      - Price with Bollinger Bands & Moving Averages")
    lines.append("      - Volume analysis")
    lines.append("      - RSI, MACD, Stochastic indicators")
    lines.append("")
    
    # ===== APPENDIX: METHODOLOGY =====
    lines.append("---")
    lines.append("")
    lines.append("## 📚 Appendix: Methodology")
    lines.append("")
    
    lines.append("### Quality Score Components (0-100, EMA-weighted, v3):")
    lines.append("- 20% ROIC (Return on Invested Capital)")
    lines.append("- 15% FCF Margin (Free Cash Flow / Revenue)")
    lines.append("- 15% Leverage (lower Net Debt/EBITDA = better)")
    lines.append("- 10% Revenue Growth (CAGR)")
    lines.append("- 10% Net Income Growth")
    lines.append("- 10% Cash Quality (CFO / Net Income)")
    lines.append("- 10% Operating Margin Trend")
    lines.append("- 10% Margin Volatility (lower = better)")
    lines.append("")
    lines.append("ROIC, FCF, Leverage, and Cash Quality use **EMA averaging** "
                 "across the latest 4 years of data (weights ≈ 10%/17%/28%/46% "
                 "from oldest to newest). Recent years dominate, which deflates "
                 "cyclical peaks and rewards turnarounds.")
    lines.append("")

    lines.append("### Technical Score (0-100, TradingView-style):")
    lines.append("- 15 Moving Average indicators (SMA/EMA at 10-200 periods + Hull/VWMA/Ichimoku)")
    lines.append("- 11 Oscillator indicators (RSI, MACD, Stochastic, CCI, ADX, etc.)")
    lines.append("- Each indicator votes Buy(+1) / Neutral(0) / Sell(-1)")
    lines.append("- Strong Buy ≥ 75, Buy ≥ 55, Hold 45-55, Sell ≥ 25, Strong Sell < 25")
    lines.append("")

    lines.append("### 🇹🇷 BIST / USD Conversion:")
    lines.append("- **Fundamentals**: TRY-denominated statements are converted to USD before "
                 "computing metrics. Income statement & cash flow use yearly-average "
                 "USD/TRY rates; balance sheet uses year-end rates. This makes ROIC, FCF, "
                 "and growth comparable to US peers (a 50% TRY revenue CAGR is often "
                 "only ~20% in real USD terms).")
    lines.append("- **Technicals (dual rating)**: the primary rating uses native TRY prices "
                 "(matches TradingView). A secondary USD-converted rating is also computed "
                 "and stored — TRY depreciation typically pulls USD ratings lower because "
                 "moving averages flip from Buy to Sell.")
    lines.append("- FX rates from yfinance (USDTRY=X), cached daily in `data/fx/`. "
                 "If FX is unavailable, the system falls back to TRY with a warning.")
    lines.append("")

    lines.append("### Market Regime Calculation:")
    lines.append("- 50% Trend (200-day MA)")
    lines.append("- 30% Momentum (12-month ROC)")
    lines.append("- 20% Volatility (20-day vs 3-year avg)")
    lines.append("- Score ≥ 0.5: Risk-On | Score ≤ -0.5: Risk-Off | Between: Neutral")
    lines.append("")
    
    # ===== FOOTER =====
    lines.append("---")
    lines.append("")
    lines.append("*This report combines technical market regime analysis, fundamental quality scoring, and technical analysis.*")
    lines.append("*For detailed data, see CSV files in `data/`*")
    lines.append(f"*Report generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*")
    
    # Write report
    report_text = "\n".join(lines)
    
    with open(REPORT_PATH, "w") as f:
        f.write(report_text)
    
    print(f"\n{'='*80}")
    print(f"Enhanced executive summary saved to: {REPORT_PATH}")
    print(f"{'='*80}\n")
    
    # Print report to console
    print(report_text)
    
    return report_text

if __name__ == "__main__":
    generate_report()
