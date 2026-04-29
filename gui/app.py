"""
Market Analysis System - Streamlit GUI v3
- Row coloring by quality/technical score
- Numeric formatting fix for sorting
- Stock price chart in Company Lookup
- Improved Overview tab
- No interest_coverage, EMA-weighted metrics
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path
import subprocess
import sys
import json
import os
import numpy as np

if Path.cwd().name == 'gui':
    os.chdir('..')
if not (Path('gui').exists() and Path('src').exists()):
    st.error(f"Wrong directory! Current: {os.getcwd()}")
    st.stop()

if os.path.exists('/app/automate_analysis_with_tech.py'):
    BASE_DIR = Path('/app'); DATA_DIR = Path('/app/data')
    ANALYSIS_SCRIPT = '/app/automate_analysis_with_tech.py'
    sys.path.insert(0, '/app/src/exMarket'); sys.path.insert(0, '/app')
else:
    BASE_DIR = Path.cwd(); DATA_DIR = BASE_DIR / 'data'
    ANALYSIS_SCRIPT = str(BASE_DIR / 'automation_scripts' / 'automate_analysis_with_tech.py')
    sys.path.insert(0, str(BASE_DIR / 'src' / 'exMarket')); sys.path.insert(0, str(BASE_DIR))

st.set_page_config(page_title="Market Analysis System", page_icon="📊", layout="wide", initial_sidebar_state="expanded")

SCORES_PATH = DATA_DIR / "fundamentals" / "absolute_scores.csv"
TECH_PATH = DATA_DIR / "technical_analysis.csv"
REPORT_PATH = DATA_DIR / "executive_summary.md"
METRICS_PATH = DATA_DIR / "fundamentals" / "company_metrics.csv"

# ============================================================================
# HELPERS
# ============================================================================

def split_by_region(df):
    if 'region' in df.columns:
        bist = df[df['region'] == 'turkey'].copy()
        glob = df[df['region'] != 'turkey'].copy()
    elif 'category' in df.columns:
        m = df['category'].str.startswith('bist', na=False)
        bist, glob = df[m].copy(), df[~m].copy()
    else:
        glob, bist = df.copy(), pd.DataFrame()
    return glob, bist, len(bist) > 0

def load_tech_lookup():
    if TECH_PATH.exists():
        t = pd.read_csv(TECH_PATH)
        return dict(zip(t['ticker'], t['technical_rating']))
    return {}

def score_color(score):
    if pd.isna(score): return '#555555'
    if score >= 65: return '#1b5e20'
    if score >= 50: return '#33691e'
    if score >= 35: return '#f57f17'
    return '#b71c1c'

def tech_color(rating):
    m = {'Strong Buy': '#1b5e20', 'Buy': '#33691e', 'Hold': '#f57f17', 'Sell': '#c62828', 'Strong Sell': '#b71c1c'}
    return m.get(rating, '#555555')

RATING_COLORS = {'Strong Buy': '#00c853', 'Buy': '#69f0ae', 'Hold': '#ffd600', 'Sell': '#ff5252', 'Strong Sell': '#b71c1c'}
RATING_ORDER = ['Strong Buy', 'Buy', 'Hold', 'Sell', 'Strong Sell']

# ============================================================================
# SIDEBAR
# ============================================================================

st.sidebar.title("⚙️ Configuration")
st.sidebar.markdown("---")

config_file = Path("config.json")
if config_file.exists():
    with open(config_file, 'r') as f:
        existing_config = json.load(f)
else:
    existing_config = {"companies_per_sector": 10, "weights": {
        "roic": 0.20, "fcf": 0.15, "cash_quality": 0.10, "leverage": 0.15,
        "growth": 0.20, "margin_trend": 0.10, "margin_volatility": 0.10}}

st.sidebar.subheader("📊 Data Collection")
companies_per_sector = st.sidebar.slider("Companies per Sector", 5, 30, existing_config.get("companies_per_sector", 10), 5)

sectors_file = Path("sectors.json")
if sectors_file.exists():
    with open(sectors_file, 'r') as f:
        sectors_config = json.load(f)
    active_sectors = [k for k, v in sectors_config["sectors"].items() if v["enabled"]]
    with st.sidebar.expander("🏢 Active Sectors", expanded=False):
        for key, info in sectors_config["sectors"].items():
            s = "✓" if info.get("enabled") else "✗"
            r = " 🇹🇷" if info.get("region") == "turkey" else ""
            st.caption(f"{s} {info['name']}{r}")
else:
    active_sectors = ["electricity", "oil-gas", "semiconductors", "software", "energy", "defense"]

st.sidebar.markdown("---")
st.sidebar.subheader("⚖️ Quality Weights (v3)")
ew = existing_config.get("weights", {})
weights = {}
weights['roic'] = st.sidebar.slider("ROIC (EMA)", 0.0, 0.40, ew.get('roic', 0.20), 0.05)
weights['fcf'] = st.sidebar.slider("FCF Margin (EMA)", 0.0, 0.30, ew.get('fcf', 0.15), 0.05)
weights['revenue_growth'] = st.sidebar.slider("Revenue Growth", 0.0, 0.20, ew.get('revenue_growth', 0.10), 0.05)
weights['income_growth'] = st.sidebar.slider("Net Income Growth", 0.0, 0.20, ew.get('income_growth', 0.10), 0.05)
weights['leverage'] = st.sidebar.slider("Leverage (EMA, inv)", 0.0, 0.25, ew.get('leverage', 0.15), 0.05)
weights['cash_quality'] = st.sidebar.slider("Cash Quality (EMA)", 0.0, 0.20, ew.get('cash_quality', 0.10), 0.05)
weights['margin_trend'] = st.sidebar.slider("Margin Trend", 0.0, 0.20, ew.get('margin_trend', 0.10), 0.05)
weights['margin_volatility'] = st.sidebar.slider("Margin Stab. (inv)", 0.0, 0.20, ew.get('margin_volatility', 0.10), 0.05)

tw = sum(weights.values())
normalized_weights = {k: v/tw for k, v in weights.items()} if tw > 0 else weights
st.sidebar.caption(f"Total: {tw:.0%}")

st.sidebar.markdown("---")
run_button = st.sidebar.button("▶️ Run Analysis", type="primary", use_container_width=True)

if run_button:
    config = {'companies_per_sector': companies_per_sector,
              'active_sectors': active_sectors if 'active_sectors' in dir() else [],
              'weights': normalized_weights}
    with open('config.json', 'w') as f:
        json.dump(config, f, indent=2)
    with st.spinner("🔄 Running analysis..."):
        progress = st.progress(0)
        try:
            proc = subprocess.Popen([sys.executable, ANALYSIS_SCRIPT],
                stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1)
            lines = []
            for line in iter(proc.stdout.readline, ''):
                lines.append(line.strip())
                if "Step" in line: st.text(line.strip())
            proc.wait(); progress.progress(100)
            if proc.returncode == 0: st.success("✅ Done!")
            else: st.error("❌ Failed.")
            with st.expander("Output", expanded=False): st.code('\n'.join(lines[-100:]))
        except Exception as e: st.error(str(e))
    st.rerun()

# ============================================================================
# TABS
# ============================================================================

tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📈 Overview & Report", "🏆 Top Companies", "📊 Technical Analysis",
    "🔍 Company Lookup", "📚 Help"
])

# ============================================================================
# TAB 1: Overview & Report
# ============================================================================

with tab1:
    st.header("📈 Market Overview")

    if not SCORES_PATH.exists():
        st.warning("⚠️ No data found. Click **▶️ Run Analysis**.")
    else:
        scores_df = pd.read_csv(SCORES_PATH)
        global_df, bist_df, has_bist = split_by_region(scores_df)
        tech_lookup = load_tech_lookup()

        def render_overview_section(df, label, flag="🌐"):
            st.subheader(f"{flag} {label}")
            c1, c2, c3, c4 = st.columns(4)
            with c1: st.metric("Companies", len(df))
            with c2: st.metric("Avg Quality", f"{df['quality_score'].mean():.1f}")
            with c3:
                buy = sum(1 for t in df['ticker'] if tech_lookup.get(t, '').endswith('Buy'))
                st.metric("Tech Buy Signals", buy)
            with c4:
                sell = sum(1 for t in df['ticker'] if 'Sell' in tech_lookup.get(t, ''))
                st.metric("Tech Sell Signals", sell)

            # Best & Worst — more actionable than pie charts
            c1, c2 = st.columns(2)
            with c1:
                st.caption("🟢 Top 5 by Quality")
                top5 = df.nlargest(5, 'quality_score')[['ticker', 'quality_score']].copy()
                top5['Technical'] = top5['ticker'].map(tech_lookup).fillna('No Data')
                top5['quality_score'] = top5['quality_score'].round(1)
                st.dataframe(top5, use_container_width=True, hide_index=True)
            with c2:
                st.caption("🔴 Bottom 5 by Quality")
                bot5 = df.nsmallest(5, 'quality_score')[['ticker', 'quality_score']].copy()
                bot5['Technical'] = bot5['ticker'].map(tech_lookup).fillna('No Data')
                bot5['quality_score'] = bot5['quality_score'].round(1)
                st.dataframe(bot5, use_container_width=True, hide_index=True)

            # Category comparison — compact bar chart
            if 'category' in df.columns and df['category'].nunique() > 1:
                ca = df.groupby('category')['quality_score'].mean().round(1).sort_values(ascending=True)
                fig = px.bar(x=ca.values, y=ca.index, orientation='h', title="Avg Quality by Category",
                            labels={'x': 'Score', 'y': ''})
                fig.update_layout(margin=dict(t=30, b=20, l=20, r=20), height=200)
                st.plotly_chart(fig, use_container_width=True)

        render_overview_section(global_df, "Global / US Stocks", "🌐")
        if has_bist:
            st.markdown("---")
            render_overview_section(bist_df, "BIST Stocks (TL)", "🇹🇷")
        else:
            # Check if BIST should exist but wasn't found
            sectors_path = Path("sectors.json")
            if sectors_path.exists():
                import json as _json
                with open(sectors_path) as _f:
                    _sc = _json.load(_f)
                has_turkey_sectors = any(v.get("region") == "turkey" for v in _sc.get("sectors", {}).values() if v.get("enabled"))
                if has_turkey_sectors:
                    st.markdown("---")
                    st.info("🇹🇷 BIST stocks are configured in sectors.json but not found in the data. Please **re-run the full analysis** to regenerate all CSV files.")

        st.markdown("---")
        st.subheader("📄 Executive Summary")
        if REPORT_PATH.exists():
            with open(REPORT_PATH, 'r') as f:
                with st.expander("View Full Report", expanded=False):
                    st.markdown(f.read())
        else:
            st.info("Report not generated yet.")

# ============================================================================
# TAB 2: Top Companies (numeric values, row colors, no percentile column)
# ============================================================================

with tab2:
    st.header("🏆 Top Quality Companies")

    if not SCORES_PATH.exists():
        st.warning("⚠️ No data available.")
    else:
        scores_df = pd.read_csv(SCORES_PATH)
        global_df, bist_df, has_bist = split_by_region(scores_df)
        tech_lookup = load_tech_lookup()

        def format_scores_table(df):
            """Numeric columns stay numeric for proper sorting."""
            cols = ['ticker', 'category', 'quality_score']
            for c in ['roic_avg', 'fcf_margin', 'revenue_cagr']:
                if c in df.columns: cols.append(c)
            cols = [c for c in cols if c in df.columns]
            out = df[cols].copy()
            out['quality_score'] = out['quality_score'].round(1)
            # Keep numeric for sorting — multiply by 100 for display as %
            for c in ['roic_avg', 'fcf_margin', 'revenue_cagr']:
                if c in out.columns:
                    out[c] = (out[c] * 100).round(1)
            out = out.rename(columns={'roic_avg': 'ROIC %', 'fcf_margin': 'FCF %', 'revenue_cagr': 'Growth %'})
            out['Technical'] = out['ticker'].map(tech_lookup).fillna('No Data')
            return out

        def add_quality_indicator(df):
            """Add a color indicator column based on quality_score."""
            out = df.copy()
            def indicator(s):
                if pd.isna(s): return '⚪'
                if s >= 65: return '🟢'
                if s >= 50: return '🟡'
                if s >= 35: return '🟠'
                return '🔴'
            out.insert(0, '🎯', out['quality_score'].apply(indicator))
            return out

        # GLOBAL
        st.subheader("🌐 Global / US Stocks (USD)")
        top_n = st.slider("Companies to display", 5, 50, 20, key="top_q")
        table = format_scores_table(global_df.nlargest(top_n, 'quality_score'))
        st.dataframe(add_quality_indicator(table), use_container_width=True, hide_index=True)

        if 'category' in global_df.columns:
            with st.expander("🎖️ Best in Each Category"):
                best = []
                for cat in sorted(global_df['category'].dropna().unique()):
                    b = global_df[global_df['category'] == cat].nlargest(1, 'quality_score').iloc[0]
                    best.append({'Category': cat, 'Company': b['ticker'],
                                 'Quality': round(b['quality_score'], 1),
                                 'Technical': tech_lookup.get(b['ticker'], 'No Data')})
                st.dataframe(pd.DataFrame(best), use_container_width=True, hide_index=True)

        # BIST
        if has_bist:
            st.markdown("---")
            st.subheader("🇹🇷 BIST Stocks (TL)")
            table = format_scores_table(bist_df.sort_values('quality_score', ascending=False))
            st.dataframe(add_quality_indicator(table), use_container_width=True, hide_index=True)

# ============================================================================
# TAB 3: Technical Analysis (table-first, row colors, quality_score column)
# ============================================================================

with tab3:
    st.header("📊 Technical Analysis")

    if not TECH_PATH.exists():
        st.info("ℹ️ Run analysis to generate technical data.")
    else:
        tech_df = pd.read_csv(TECH_PATH)
        tech_global, tech_bist, tech_has_bist = split_by_region(tech_df)

        def format_tech_table(df):
            cols = ['ticker', 'category', 'technical_score', 'technical_rating']
            if 'ma_buy' in df.columns: cols += ['ma_buy', 'ma_sell', 'osc_buy', 'osc_sell']
            if 'rsi' in df.columns: cols.append('rsi')
            if 'quality_score' in df.columns: cols.append('quality_score')
            cols = [c for c in cols if c in df.columns]
            out = df[cols].copy()
            for c in ['technical_score', 'rsi', 'quality_score']:
                if c in out.columns: out[c] = out[c].round(1)
            return out.sort_values('technical_score', ascending=False)

        def add_tech_indicator(df):
            """Add emoji indicator based on technical_rating."""
            out = df.copy()
            m = {'Strong Buy': '🟢', 'Buy': '🟢', 'Hold': '🟡', 'Sell': '🔴', 'Strong Sell': '🔴'}
            if 'technical_rating' in out.columns:
                out.insert(0, '📊', out['technical_rating'].map(m).fillna('⚪'))
            return out

        def render_tech_section(df, label, currency=""):
            if len(df) == 0:
                st.info(f"No {label} stocks.")
                return
            c1, c2, c3, c4 = st.columns(4)
            with c1: st.metric("Stocks", len(df))
            with c2: st.metric("Buy Signals", len(df[df['technical_rating'].str.contains('Buy', na=False)]))
            with c3: st.metric("Sell Signals", len(df[df['technical_rating'].str.contains('Sell', na=False)]))
            with c4:
                if 'rsi' in df.columns: st.metric("Oversold", len(df[df['rsi'] < 30]))
            st.dataframe(add_tech_indicator(format_tech_table(df)), use_container_width=True, hide_index=True)

            with st.expander("📊 Charts", expanded=False):
                if 'quality_score' in df.columns and 'technical_score' in df.columns:
                    fig = px.scatter(df, x='quality_score', y='technical_score', text='ticker',
                                    color='technical_rating', color_discrete_map=RATING_COLORS,
                                    hover_data=['ticker', 'category'], title="Quality vs Technical")
                    fig.add_hline(y=75, line_dash="dash", line_color="green", opacity=0.4)
                    fig.add_hline(y=25, line_dash="dash", line_color="red", opacity=0.4)
                    fig.update_layout(margin=dict(t=30), height=400)
                    st.plotly_chart(fig, use_container_width=True)

        st.subheader("🌐 Global / US Stocks")
        render_tech_section(tech_global, "Global", "USD")
        if tech_has_bist:
            st.markdown("---")
            st.subheader("🇹🇷 BIST Stocks (TL)")
            render_tech_section(tech_bist, "BIST", "TL")

# ============================================================================
# TAB 4: Company Lookup (+ stock price chart)
# ============================================================================

with tab4:
    st.header("🔍 Company Lookup")

    if not SCORES_PATH.exists() or not METRICS_PATH.exists():
        st.warning("⚠️ No data. Run analysis first.")
    else:
        scores_df = pd.read_csv(SCORES_PATH)
        if 'ticker' not in scores_df.columns: scores_df = scores_df.reset_index()
        metrics_df = pd.read_csv(METRICS_PATH, index_col=0)
        scores_dedup = scores_df.drop_duplicates(subset='ticker', keep='first')
        all_tickers = sorted(scores_dedup['ticker'].dropna().unique().tolist())

        c1, c2 = st.columns([2, 3])
        with c1: search_text = st.text_input("Type a ticker:", placeholder="e.g. ASML, NVDA")
        with c2:
            filtered = [t for t in all_tickers if search_text.upper() in t.upper()] if search_text else all_tickers
            selected_ticker = st.selectbox("Or select:", filtered if filtered else all_tickers)
        ticker = search_text.strip().upper() if search_text.strip() else selected_ticker

        if ticker and ticker in all_tickers:
            rs = scores_dedup[scores_dedup['ticker'] == ticker].iloc[0]
            rm = metrics_df.loc[ticker] if ticker in metrics_df.index else None
            if isinstance(rm, pd.DataFrame): rm = rm.iloc[0]

            region = rs.get('region', 'global')
            flag = "🇹🇷" if region == 'turkey' else "🌐"
            quality = rs.get('quality_score', 0)
            tier = rs.get('quality_tier', '?')
            category = rs.get('category', 'N/A')

            st.markdown(f"### {flag} {ticker}")
            c1, c2, c3, c4 = st.columns(4)
            with c1: st.metric("Quality Score", f"{quality:.1f}")
            with c2: st.metric("Tier", tier)
            with c3: st.metric("Category", category)
            with c4: st.metric("Data Complete", f"{rs.get('data_completeness', 100):.0f}%")

            # --- STOCK PRICE CHART ---
            st.markdown("---")
            st.subheader("📈 Stock Price (1 Year)")
            try:
                import yfinance as yf
                stock = yf.Ticker(ticker)
                hist = stock.history(period="1y")
                if len(hist) > 0:
                    fig = go.Figure()
                    fig.add_trace(go.Candlestick(
                        x=hist.index, open=hist['Open'], high=hist['High'],
                        low=hist['Low'], close=hist['Close'], name=ticker
                    ))
                    fig.update_layout(
                        title=f"{ticker} — 1 Year Price",
                        yaxis_title="Price",
                        xaxis_rangeslider_visible=False,
                        margin=dict(t=40, b=20, l=40, r=20),
                        height=350
                    )
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.info("No price data available for this ticker.")
            except ImportError:
                st.info("Install yfinance (`pip install yfinance`) to see price charts.")
            except Exception as e:
                st.info(f"Could not load price data: {e}")

            # --- METRICS TABLE ---
            st.markdown("---")
            st.subheader("📊 Raw Metric Values")

            metric_info = [
                ('roic_avg', 'ROIC (EMA)', 'pct', False, 0.20),
                ('fcf_margin', 'FCF Margin (EMA)', 'pct', False, 0.15),
                ('revenue_cagr', 'Revenue Growth (CAGR)', 'pct', False, 0.10),
                ('ni_cagr', 'Net Income Growth', 'pct', False, 0.10),
                ('net_debt_ebitda', 'Leverage (EMA)', 'ratio', True, 0.15),
                ('margin_volatility', 'Margin Volatility', 'pct', True, 0.10),
                ('cfo_to_ni', 'Cash Quality (EMA)', 'ratio', False, 0.10),
                ('op_margin_trend', 'Margin Trend', 'pct', False, 0.10),
            ]

            rows = []
            for col, label, fmt, inv, weight in metric_info:
                raw = rm[col] if rm is not None and col in rm.index else None
                if raw is None or pd.isna(raw):
                    rows.append({'Status': '⚠️', 'Metric': label, 'Value': '—',
                                 'Percentile': '—', 'Weight': f"{weight:.0%}", 'Contribution': '—',
                                 'Direction': "↓" if inv else "↑"})
                elif np.isinf(raw):
                    rows.append({'Status': '⚠️', 'Metric': label, 'Value': '∞',
                                 'Percentile': '—', 'Weight': f"{weight:.0%}", 'Contribution': '—',
                                 'Direction': "↓" if inv else "↑"})
                else:
                    raw_str = f"{raw*100:.1f}%" if fmt == 'pct' else f"{raw:.2f}x"
                    all_v = metrics_df[col].replace([np.inf, -np.inf], np.nan).dropna()
                    pct = (100 - (all_v < raw).sum() / len(all_v) * 100) if inv else ((all_v <= raw).sum() / len(all_v) * 100)
                    rows.append({'Status': '✓', 'Metric': label, 'Value': raw_str,
                                 'Percentile': f"{pct:.0f}th", 'Weight': f"{weight:.0%}",
                                 'Contribution': f"{pct * weight:.1f}",
                                 'Direction': "↓ lower=better" if inv else "↑ higher=better"})
            st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

            # --- PEERS ---
            st.markdown("---")
            st.subheader(f"📊 Peers: {category}")
            peers = scores_dedup[scores_dedup['category'] == category].sort_values('quality_score', ascending=False)
            pcols = ['ticker', 'quality_score']
            for e in ['roic_avg', 'fcf_margin', 'revenue_cagr']:
                if e in peers.columns: pcols.append(e)
            pcols = [c for c in pcols if c in peers.columns]
            pd_display = peers[pcols].copy()
            pd_display.insert(0, '', pd_display['ticker'].apply(lambda t: '→' if t == ticker else ''))
            pd_display['quality_score'] = pd_display['quality_score'].round(1)
            for c in ['roic_avg', 'fcf_margin', 'revenue_cagr']:
                if c in pd_display.columns:
                    pd_display[c] = (pd_display[c] * 100).round(1)
            pd_display = pd_display.rename(columns={'roic_avg': 'ROIC %', 'fcf_margin': 'FCF %', 'revenue_cagr': 'Growth %'})
            st.dataframe(pd_display, use_container_width=True, hide_index=True)

            # --- TECHNICAL ---
            if TECH_PATH.exists():
                tdf = pd.read_csv(TECH_PATH)
                tr = tdf[tdf['ticker'] == ticker]
                if len(tr) > 0:
                    st.markdown("---")
                    st.subheader("📈 Technical Analysis")
                    tr = tr.iloc[0]
                    c1, c2, c3, c4 = st.columns(4)
                    with c1: st.metric("Technical Score", f"{tr.get('technical_score', 0):.0f}")
                    with c2: st.metric("Rating", tr.get('technical_rating', 'N/A'))
                    with c3: st.metric("RSI", f"{tr.get('rsi', 0):.0f}")
                    with c4: st.metric("Trend", tr.get('ma_trend', 'N/A'))
                    if 'ma_buy' in tr.index:
                        st.caption(f"MA: {int(tr.get('ma_buy',0))}B / {int(tr.get('ma_sell',0))}S · Osc: {int(tr.get('osc_buy',0))}B / {int(tr.get('osc_sell',0))}S")
        elif ticker:
            st.warning(f"'{ticker}' not found. {len(all_tickers)} companies available.")

# ============================================================================
# TAB 5: Help
# ============================================================================

with tab5:
    st.header("📚 Help")
    with st.expander("⚖️ Quality Score Formula (v3)", expanded=True):
        st.markdown("""
        **8 metrics, EMA-weighted** (recent years count more):
        ```
        Quality Score = ROIC × 20% + FCF Margin × 15% + Revenue Growth × 10% +
          Net Income Growth × 10% + Leverage × 15% + Margin Stability × 10% +
          Cash Quality × 10% + Margin Trend × 10%
        ```
        - **EMA-weighted** (ROIC, FCF, Leverage, Cash Quality): 2022=10%, 2023=17%, 2024=28%, 2025=46%
        - **Net Income Growth**: CAGR when both endpoints positive; special handling for turnarounds
        - **Removed**: Interest Coverage (too noisy, redundant with Leverage)
        """)
    with st.expander("📊 Technical Indicators"):
        st.markdown("""
        **26 indicators** vote Buy/Neutral/Sell. 15 MAs + 11 Oscillators.
        Strong Buy ≥ 75 · Buy ≥ 55 · Hold 45-55 · Sell ≥ 25 · Strong Sell < 25
        """)
    with st.expander("🎮 How to Use"):
        st.markdown("""
        1. **Overview**: Top/bottom companies, category averages, report
        2. **Top Companies**: Quality rankings (green=high, red=low) + technical rating
        3. **Technical Analysis**: Technical rankings + quality score column
        4. **Company Lookup**: Deep-dive with stock price chart, metric breakdown, peers
        """)

st.markdown("---")
st.caption("Market Analysis System v3 | EMA Weights | BIST Support")
