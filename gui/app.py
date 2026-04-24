"""
Market Analysis System - Streamlit GUI v2.2
Interactive interface for running analysis and viewing results
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path
import subprocess
import sys
import json
import time
import os
import numpy as np

# Ensure we're in the correct directory
if Path.cwd().name == 'gui':
    os.chdir('..')
if not (Path('gui').exists() and Path('src').exists()):
    st.error(f"Wrong directory! Current: {os.getcwd()}")
    st.info("Please run from the market-analysis directory")
    st.stop()

# Auto-detect Docker or local
if os.path.exists('/app/automate_analysis_with_tech.py'):
    BASE_DIR = Path('/app')
    DATA_DIR = Path('/app/data')
    ANALYSIS_SCRIPT = '/app/automate_analysis_with_tech.py'
    sys.path.insert(0, '/app/src/exMarket')
    sys.path.insert(0, '/app')
else:
    BASE_DIR = Path.cwd()
    DATA_DIR = BASE_DIR / 'data'
    ANALYSIS_SCRIPT = str(BASE_DIR / 'automation_scripts' / 'automate_analysis_with_tech.py')
    sys.path.insert(0, str(BASE_DIR / 'src' / 'exMarket'))
    sys.path.insert(0, str(BASE_DIR))

st.set_page_config(page_title="Market Analysis System", page_icon="📊", layout="wide", initial_sidebar_state="expanded")

# Paths
SCORES_PATH = DATA_DIR / "fundamentals" / "absolute_scores.csv"
TECH_PATH = DATA_DIR / "technical_analysis.csv"
REPORT_PATH = DATA_DIR / "executive_summary.md"
METRICS_PATH = DATA_DIR / "fundamentals" / "company_metrics.csv"

# ============================================================================
# HELPERS
# ============================================================================

def split_by_region(df):
    if 'region' in df.columns:
        bist_df = df[df['region'] == 'turkey'].copy()
        global_df = df[df['region'] != 'turkey'].copy()
    elif 'category' in df.columns:
        bist_mask = df['category'].str.startswith('bist', na=False)
        bist_df = df[bist_mask].copy()
        global_df = df[~bist_mask].copy()
    else:
        global_df = df.copy()
        bist_df = pd.DataFrame()
    return global_df, bist_df, len(bist_df) > 0

def load_tech_lookup():
    if TECH_PATH.exists():
        tech = pd.read_csv(TECH_PATH)
        return dict(zip(tech['ticker'], tech['technical_rating']))
    return {}

RATING_COLORS = {
    'Strong Buy': '#00c853', 'Buy': '#69f0ae', 'Hold': '#ffd600',
    'Sell': '#ff5252', 'Strong Sell': '#b71c1c',
}
RATING_ORDER = ['Strong Buy', 'Buy', 'Hold', 'Sell', 'Strong Sell']

if not SCORES_PATH.exists():
    st.sidebar.warning("🔍 Debug Info")
    st.sidebar.caption(f"Looking for: {SCORES_PATH}")
    st.sidebar.caption(f"Current dir: {os.getcwd()}")

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
    existing_config = {
        "companies_per_sector": 10,
        "weights": {
            "roic": 0.20, "fcf": 0.15, "cash_quality": 0.10, "leverage": 0.10,
            "growth": 0.15, "margin_trend": 0.10, "interest_coverage": 0.10, "margin_volatility": 0.10
        }
    }

st.sidebar.subheader("📊 Data Collection")
companies_per_sector = st.sidebar.slider("Companies per Sector", 5, 30, existing_config.get("companies_per_sector", 10), 5)

sectors_file = Path("sectors.json")
if sectors_file.exists():
    with open(sectors_file, 'r') as f:
        sectors_config = json.load(f)
    active_sectors = [k for k, v in sectors_config["sectors"].items() if v["enabled"]]
    st.sidebar.subheader("🏢 Active Sectors")
    scraped = [k for k, v in sectors_config["sectors"].items() if v.get("enabled") and v.get("type", "scraped") == "scraped"]
    manual = [k for k, v in sectors_config["sectors"].items() if v.get("enabled") and v.get("type") == "manual"]
    st.sidebar.info(f"✓ {len(active_sectors)}/{len(sectors_config['sectors'])} sectors ({len(scraped)} scraped, {len(manual)} manual)")
    with st.sidebar.expander("View sectors", expanded=False):
        for key, info in sectors_config["sectors"].items():
            status = "✓" if info.get("enabled", True) else "✗"
            t_icon = "🌐" if info.get("type", "scraped") == "scraped" else "📝"
            r_flag = " 🇹🇷" if info.get("region", "global") == "turkey" else ""
            extra = f" ({len(info.get('tickers', []))} tickers)" if info.get("type") == "manual" else ""
            st.caption(f"{status} {t_icon} {info['name']}{r_flag}{extra}")
else:
    st.sidebar.warning("⚠️ sectors.json not found")
    active_sectors = ["electricity", "oil-gas", "semiconductors", "software", "energy", "defense"]

st.sidebar.markdown("---")
st.sidebar.subheader("⚖️ Quality Score Weights")
st.sidebar.caption("Adjust metric contributions:")
ew = existing_config.get("weights", {})
weights = {}
weights['roic'] = st.sidebar.slider("ROIC", 0.0, 0.40, ew.get('roic', 0.20), 0.05)
weights['fcf'] = st.sidebar.slider("FCF Margin", 0.0, 0.30, ew.get('fcf', 0.15), 0.05)
weights['growth'] = st.sidebar.slider("Revenue Growth", 0.0, 0.30, ew.get('growth', 0.15), 0.05)
weights['leverage'] = st.sidebar.slider("Leverage (inv)", 0.0, 0.20, ew.get('leverage', 0.10), 0.05)
weights['cash_quality'] = st.sidebar.slider("Cash Quality", 0.0, 0.20, ew.get('cash_quality', 0.10), 0.05)
weights['margin_trend'] = st.sidebar.slider("Margin Trend", 0.0, 0.20, ew.get('margin_trend', 0.10), 0.05)
weights['interest_coverage'] = st.sidebar.slider("Interest Cov.", 0.0, 0.20, ew.get('interest_coverage', 0.10), 0.05)
weights['margin_volatility'] = st.sidebar.slider("Margin Stab. (inv)", 0.0, 0.20, ew.get('margin_volatility', 0.10), 0.05)

tw = sum(weights.values())
normalized_weights = {k: v/tw for k, v in weights.items()} if tw > 0 else weights
st.sidebar.caption(f"Total: {tw:.0%} → Normalized to 100%")

if st.sidebar.button("🔄 Reset to Defaults"):
    st.rerun()

st.sidebar.markdown("---")
run_button = st.sidebar.button("▶️ Run Analysis", type="primary", use_container_width=True)

if run_button:
    config = {
        'companies_per_sector': companies_per_sector,
        'active_sectors': active_sectors if 'active_sectors' in dir() else [],
        'weights': normalized_weights,
    }
    with open('config.json', 'w') as f:
        json.dump(config, f, indent=2)
    
    with st.spinner("🔄 Running analysis..."):
        progress = st.progress(0)
        status = st.empty()
        try:
            process = subprocess.Popen(
                [sys.executable, ANALYSIS_SCRIPT],
                stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1
            )
            output_lines = []
            for line in iter(process.stdout.readline, ''):
                output_lines.append(line.strip())
                if "Step" in line or "step" in line:
                    status.text(line.strip())
            process.wait()
            progress.progress(100)
            if process.returncode == 0:
                st.success("✅ Analysis completed!")
            else:
                st.error("❌ Analysis failed.")
            with st.expander("View Output", expanded=False):
                st.code('\n'.join(output_lines[-100:]))
        except Exception as e:
            st.error(f"Error: {e}")
    st.rerun()

# ============================================================================
# TABS
# ============================================================================

tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📈 Overview & Report", "🏆 Top Companies", "📊 Technical Analysis",
    "🔍 Company Lookup", "📚 Help"
])

# ============================================================================
# TAB 1: Overview & Report (merged)
# ============================================================================

with tab1:
    st.header("📈 Market Overview")
    
    if not SCORES_PATH.exists():
        st.warning("⚠️ No data found. Click **▶️ Run Analysis** in the sidebar.")
    else:
        scores_df = pd.read_csv(SCORES_PATH)
        global_df, bist_df, has_bist = split_by_region(scores_df)
        
        # ---- GLOBAL ----
        st.subheader("🌐 Global / US Stocks")
        c1, c2, c3, c4 = st.columns(4)
        with c1: st.metric("Companies", len(global_df))
        with c2: st.metric("Top Tier", len(global_df[global_df['quality_tier'] == 'Top 25%']))
        with c3: st.metric("Avg Quality", f"{global_df['quality_score'].mean():.1f}")
        with c4:
            if 'category' in global_df.columns:
                st.metric("Categories", global_df['category'].nunique())
        
        c1, c2, c3 = st.columns(3)
        with c1:
            fig = px.histogram(global_df, x='quality_score', nbins=20, title="Score Distribution")
            fig.update_layout(showlegend=False, margin=dict(t=30, b=20, l=20, r=20), height=230)
            st.plotly_chart(fig, use_container_width=True)
        with c2:
            if 'quality_tier' in global_df.columns:
                tc = global_df['quality_tier'].value_counts()
                fig = px.pie(values=tc.values, names=tc.index, title="Tiers")
                fig.update_layout(margin=dict(t=30, b=20, l=20, r=20), height=230)
                st.plotly_chart(fig, use_container_width=True)
        with c3:
            if 'category' in global_df.columns:
                ca = global_df.groupby('category')['quality_score'].mean().round(1).sort_values(ascending=True)
                fig = px.bar(x=ca.values, y=ca.index, orientation='h', title="Avg by Category")
                fig.update_layout(margin=dict(t=30, b=20, l=20, r=20), height=230)
                st.plotly_chart(fig, use_container_width=True)
        
        # ---- BIST ----
        if has_bist:
            st.markdown("---")
            st.subheader("🇹🇷 BIST Stocks (TL)")
            c1, c2, c3, c4 = st.columns(4)
            with c1: st.metric("Companies", len(bist_df))
            with c2: st.metric("Top Tier", len(bist_df[bist_df['quality_tier'] == 'Top 25%']))
            with c3: st.metric("Avg Quality", f"{bist_df['quality_score'].mean():.1f}")
            with c4:
                if 'category' in bist_df.columns:
                    st.metric("Sectors", bist_df['category'].nunique())
            
            c1, c2, c3 = st.columns(3)
            with c1:
                fig = px.histogram(bist_df, x='quality_score', nbins=15, title="Score Distribution")
                fig.update_layout(showlegend=False, margin=dict(t=30, b=20, l=20, r=20), height=230)
                st.plotly_chart(fig, use_container_width=True)
            with c2:
                if 'quality_tier' in bist_df.columns:
                    tc = bist_df['quality_tier'].value_counts()
                    fig = px.pie(values=tc.values, names=tc.index, title="Tiers")
                    fig.update_layout(margin=dict(t=30, b=20, l=20, r=20), height=230)
                    st.plotly_chart(fig, use_container_width=True)
            with c3:
                if 'category' in bist_df.columns:
                    ca = bist_df.groupby('category')['quality_score'].mean().round(1).sort_values(ascending=True)
                    fig = px.bar(x=ca.values, y=ca.index, orientation='h', title="Avg by Sector")
                    fig.update_layout(margin=dict(t=30, b=20, l=20, r=20), height=230)
                    st.plotly_chart(fig, use_container_width=True)
        
        # ---- REPORT ----
        st.markdown("---")
        st.subheader("📄 Executive Summary Report")
        if REPORT_PATH.exists():
            with open(REPORT_PATH, 'r') as f:
                report_content = f.read()
            with st.expander("View Full Report", expanded=False):
                st.markdown(report_content)
        else:
            st.info("Report not generated yet. Run analysis to generate.")

# ============================================================================
# TAB 2: Top Companies (+ technical_rating column)
# ============================================================================

with tab2:
    st.header("🏆 Top Quality Companies")
    
    if not SCORES_PATH.exists():
        st.warning("⚠️ No data available. Run analysis first.")
    else:
        scores_df = pd.read_csv(SCORES_PATH)
        global_df, bist_df, has_bist = split_by_region(scores_df)
        tech_lookup = load_tech_lookup()
        pctl_col = 'quality_percentile_regional' if 'quality_percentile_regional' in scores_df.columns else 'quality_percentile'
        
        def format_scores_table(df):
            cols = ['ticker', 'category', 'quality_score', pctl_col]
            for c in ['roic_avg', 'fcf_margin', 'revenue_cagr']:
                if c in df.columns: cols.append(c)
            cols = [c for c in cols if c in df.columns]
            out = df[cols].copy()
            for c in ['roic_avg', 'fcf_margin', 'revenue_cagr']:
                if c in out.columns:
                    out[c] = out[c].apply(lambda x: f"{x*100:.1f}%" if pd.notna(x) else "N/A")
            out['Technical'] = out['ticker'].map(tech_lookup).fillna('No Data')
            return out
        
        # ---- GLOBAL ----
        st.subheader("🌐 Global / US Stocks (USD)")
        top_n = st.slider("Companies to display", 5, 50, 20, key="top_n_q")
        st.dataframe(format_scores_table(global_df.nlargest(top_n, 'quality_score')), use_container_width=True, hide_index=True)
        
        if 'category' in global_df.columns:
            st.markdown("---")
            st.caption("🎖️ Best in Each Category (Global)")
            best_per = []
            for cat in sorted(global_df['category'].dropna().unique()):
                cat_df = global_df[global_df['category'] == cat]
                if len(cat_df) > 0:
                    b = cat_df.nlargest(1, 'quality_score').iloc[0]
                    best_per.append({
                        'Category': cat, 'Company': b['ticker'],
                        'Quality': f"{b['quality_score']:.1f}",
                        'ROIC': f"{b.get('roic_avg',0)*100:.1f}%" if pd.notna(b.get('roic_avg')) else "N/A",
                        'Technical': tech_lookup.get(b['ticker'], 'No Data'),
                    })
            st.dataframe(pd.DataFrame(best_per), use_container_width=True, hide_index=True)
        
        # ---- BIST ----
        if has_bist:
            st.markdown("---")
            st.subheader("🇹🇷 BIST Stocks — Borsa Istanbul (TL)")
            st.caption("Ranked independently. Values in Turkish Lira.")
            c1, c2, c3 = st.columns(3)
            with c1: st.metric("Companies", len(bist_df))
            with c2: st.metric("Avg Quality", f"{bist_df['quality_score'].mean():.1f}")
            with c3: st.metric("Top Tier", len(bist_df[bist_df['quality_tier'] == 'Top 25%']))
            
            st.dataframe(format_scores_table(bist_df.sort_values('quality_score', ascending=False)), use_container_width=True, hide_index=True)
            
            if 'category' in bist_df.columns:
                st.caption("🎖️ Best in Each BIST Sector")
                best_bist = []
                for cat in sorted(bist_df['category'].dropna().unique()):
                    cat_df = bist_df[bist_df['category'] == cat]
                    if len(cat_df) > 0:
                        b = cat_df.nlargest(1, 'quality_score').iloc[0]
                        best_bist.append({
                            'Sector': cat, 'Company': b['ticker'],
                            'Quality': f"{b['quality_score']:.1f}",
                            'ROIC': f"{b.get('roic_avg',0)*100:.1f}%" if pd.notna(b.get('roic_avg')) else "N/A",
                            'Technical': tech_lookup.get(b['ticker'], 'No Data'),
                        })
                st.dataframe(pd.DataFrame(best_bist), use_container_width=True, hide_index=True)

# ============================================================================
# TAB 3: Technical Analysis (table-first like Top Companies, + quality_score)
# ============================================================================

with tab3:
    st.header("📊 Technical Analysis")
    
    if not TECH_PATH.exists():
        st.info("ℹ️ Technical data not available yet. Run full analysis to generate.")
    else:
        tech_df = pd.read_csv(TECH_PATH)
        tech_global, tech_bist, tech_has_bist = split_by_region(tech_df)
        
        def format_tech_table(df):
            cols = ['ticker', 'category', 'technical_score', 'technical_rating']
            if 'ma_buy' in df.columns:
                cols += ['ma_buy', 'ma_sell', 'osc_buy', 'osc_sell']
            if 'rsi' in df.columns: cols.append('rsi')
            if 'ma_trend' in df.columns: cols.append('ma_trend')
            if 'quality_score' in df.columns: cols.append('quality_score')
            cols = [c for c in cols if c in df.columns]
            out = df[cols].copy()
            for c in ['technical_score', 'rsi', 'quality_score']:
                if c in out.columns: out[c] = out[c].round(1)
            return out.sort_values('technical_score', ascending=False)
        
        def render_tech_section(df, label, currency_note=""):
            if len(df) == 0:
                st.info(f"No {label} stocks in technical analysis.")
                return
            
            c1, c2, c3, c4 = st.columns(4)
            with c1: st.metric("Stocks", len(df))
            with c2: st.metric("Buy Signals", len(df[df['technical_rating'].str.contains('Buy', na=False)]))
            with c3: st.metric("Sell Signals", len(df[df['technical_rating'].str.contains('Sell', na=False)]))
            with c4:
                if 'rsi' in df.columns:
                    st.metric("Oversold (RSI<30)", len(df[df['rsi'] < 30]))
            
            # Main table first
            st.dataframe(format_tech_table(df), use_container_width=True, hide_index=True)
            
            # Charts in expander
            with st.expander("📊 Charts & Distributions", expanded=False):
                if 'quality_score' in df.columns and 'technical_score' in df.columns:
                    suffix = f" ({currency_note})" if currency_note else ""
                    st.caption(f"Quality vs Technical Scores{suffix}")
                    fig = px.scatter(
                        df, x='quality_score', y='technical_score',
                        hover_data=['ticker', 'category', 'technical_rating'],
                        text='ticker', color='technical_rating',
                        color_discrete_map=RATING_COLORS, title="",
                        labels={'quality_score': 'Quality Score', 'technical_score': 'Technical Score'}
                    )
                    fig.add_hline(y=75, line_dash="dash", line_color="green", opacity=0.4, annotation_text="Strong Buy")
                    fig.add_hline(y=55, line_dash="dot", line_color="lightgreen", opacity=0.3)
                    fig.add_hline(y=45, line_dash="dot", line_color="orange", opacity=0.3)
                    fig.add_hline(y=25, line_dash="dash", line_color="red", opacity=0.4, annotation_text="Strong Sell")
                    fig.update_layout(margin=dict(t=10), height=400)
                    st.plotly_chart(fig, use_container_width=True)
                
                c1, c2 = st.columns(2)
                with c1:
                    if 'technical_rating' in df.columns:
                        rc = df['technical_rating'].value_counts()
                        rc = rc.reindex([r for r in RATING_ORDER if r in rc.index])
                        fig = px.bar(x=rc.index, y=rc.values, title="Ratings", color=rc.index, color_discrete_map=RATING_COLORS)
                        fig.update_layout(showlegend=False, margin=dict(t=30, b=20), height=230)
                        st.plotly_chart(fig, use_container_width=True)
                with c2:
                    if 'rsi' in df.columns:
                        fig = px.histogram(df, x='rsi', nbins=15, title="RSI")
                        fig.add_vline(x=30, line_dash="dash", line_color="green")
                        fig.add_vline(x=70, line_dash="dash", line_color="red")
                        fig.update_layout(margin=dict(t=30, b=20), height=230)
                        st.plotly_chart(fig, use_container_width=True)
        
        # ---- GLOBAL ----
        st.subheader("🌐 Global / US Stocks (USD)")
        render_tech_section(tech_global, "Global", "USD")
        
        # ---- BIST ----
        if tech_has_bist:
            st.markdown("---")
            st.subheader("🇹🇷 BIST Stocks (TL)")
            st.caption("TL-denominated indicators. Not comparable to USD stocks.")
            render_tech_section(tech_bist, "BIST", "TL")

# ============================================================================
# TAB 4: Company Lookup
# ============================================================================

with tab4:
    st.header("🔍 Company Lookup")
    st.caption("Enter a ticker to see all raw metric values and score contributions.")
    
    if not SCORES_PATH.exists() or not METRICS_PATH.exists():
        st.warning("⚠️ No data available. Run analysis first.")
    else:
        scores_df = pd.read_csv(SCORES_PATH)
        if 'ticker' not in scores_df.columns:
            scores_df = scores_df.reset_index()
        metrics_df = pd.read_csv(METRICS_PATH, index_col=0)
        
        scores_dedup = scores_df.drop_duplicates(subset='ticker', keep='first')
        all_tickers = sorted(scores_dedup['ticker'].dropna().unique().tolist())
        
        c1, c2 = st.columns([2, 3])
        with c1:
            search_text = st.text_input("Type a ticker:", placeholder="e.g. ASML, NVDA, KCHOL.IS")
        with c2:
            filtered = [t for t in all_tickers if search_text.upper() in t.upper()] if search_text else all_tickers
            selected_ticker = st.selectbox("Or select:", filtered if filtered else all_tickers)
        
        ticker = search_text.strip().upper() if search_text.strip() else selected_ticker
        
        if ticker and ticker in all_tickers:
            row_scores = scores_dedup[scores_dedup['ticker'] == ticker].iloc[0]
            row_metrics = metrics_df.loc[ticker] if ticker in metrics_df.index else None
            if isinstance(row_metrics, pd.DataFrame):
                row_metrics = row_metrics.iloc[0]
            
            region = row_scores.get('region', 'global')
            flag = "🇹🇷" if region == 'turkey' else "🌐"
            category = row_scores.get('category', 'N/A')
            quality = row_scores.get('quality_score', 0)
            tier = row_scores.get('quality_tier', '?')
            completeness = row_scores.get('data_completeness', 100)
            
            st.markdown(f"### {flag} {ticker}")
            c1, c2, c3, c4 = st.columns(4)
            with c1: st.metric("Quality Score", f"{quality:.1f}")
            with c2: st.metric("Tier", tier)
            with c3: st.metric("Category", category)
            with c4: st.metric("Data Complete", f"{completeness:.0f}%")
            
            st.markdown("---")
            st.subheader("📊 Raw Metric Values")
            
            metric_info = [
                ('roic_avg', 'ROIC (Avg)', 'pct', False, 0.20),
                ('fcf_margin', 'FCF Margin', 'pct', False, 0.15),
                ('revenue_cagr', 'Revenue Growth (CAGR)', 'pct', False, 0.15),
                ('margin_volatility', 'Margin Volatility', 'pct', True, 0.10),
                ('net_debt_ebitda', 'Net Debt / EBITDA', 'ratio', True, 0.10),
                ('cfo_to_ni', 'Cash Quality (CFO/NI)', 'ratio', False, 0.10),
                ('interest_coverage', 'Interest Coverage', 'ratio', False, 0.10),
                ('op_margin_trend', 'Op Margin Trend', 'pct', False, 0.10),
            ]
            
            table_rows = []
            for col, label, fmt, inverse, weight in metric_info:
                raw_val = row_metrics[col] if row_metrics is not None and col in row_metrics.index else None
                if raw_val is None or pd.isna(raw_val):
                    raw_str, rank_str, contrib_str, status = "—", "—", "—", "⚠️ Missing"
                elif np.isinf(raw_val):
                    raw_str, rank_str, contrib_str, status = "∞", "—", "—", "⚠️ Inf"
                else:
                    raw_str = f"{raw_val*100:.1f}%" if fmt == 'pct' else f"{raw_val:.2f}x"
                    all_vals = metrics_df[col].replace([np.inf, -np.inf], np.nan).dropna()
                    pct_rank = (100 - (all_vals < raw_val).sum() / len(all_vals) * 100) if inverse else ((all_vals <= raw_val).sum() / len(all_vals) * 100)
                    rank_str, contrib_str, status = f"{pct_rank:.0f}th", f"{pct_rank * weight:.1f}", "✓"
                
                table_rows.append({
                    'Status': status, 'Metric': label, 'Value': raw_str,
                    'Percentile': rank_str, 'Weight': f"{weight:.0%}",
                    'Contribution': contrib_str,
                    'Direction': "↓ lower=better" if inverse else "↑ higher=better",
                })
            
            st.dataframe(pd.DataFrame(table_rows), use_container_width=True, hide_index=True)
            st.caption("**Percentile**: rank among all companies (100th = best). **Contribution**: percentile × weight.")
            
            # Peers
            st.markdown("---")
            st.subheader(f"📊 Category Peers: {category}")
            peers = scores_dedup[scores_dedup['category'] == category].sort_values('quality_score', ascending=False)
            peer_cols = ['ticker', 'quality_score', 'quality_tier']
            for extra in ['roic_avg', 'fcf_margin', 'revenue_cagr']:
                if extra in peers.columns: peer_cols.append(extra)
            peer_cols = [c for c in peer_cols if c in peers.columns]
            peers_display = peers[peer_cols].copy()
            peers_display.insert(0, '', peers_display['ticker'].apply(lambda t: '→' if t == ticker else ''))
            st.dataframe(peers_display, use_container_width=True, hide_index=True)
            
            # Technical
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
            st.warning(f"Ticker '{ticker}' not found. {len(all_tickers)} companies available.")

# ============================================================================
# TAB 5: Help
# ============================================================================

with tab5:
    st.header("📚 Help & Documentation")
    with st.expander("⚖️ Quality Score Formula", expanded=True):
        st.markdown("""
        **Formula (v2 — PCA-optimized weights):**
        ```
        Quality Score = ROIC × 20% + FCF Margin × 15% + Revenue Growth × 15% +
          Margin Stability × 10% + Leverage × 10% + Cash Quality × 10% +
          Interest Coverage × 10% + Margin Trend × 10%
        ```
        *Weights derived from PCA analysis (50%) + financial theory (50%)*
        """)
    with st.expander("📊 Technical Indicators (TradingView-style)"):
        st.markdown("""
        **26 indicators** vote Buy/Neutral/Sell. 15 Moving Averages + 11 Oscillators.
        
        Strong Buy ≥ 75 · Buy ≥ 55 · Hold 45-55 · Sell ≥ 25 · Strong Sell < 25
        """)
    with st.expander("🎮 How to Use"):
        st.markdown("""
        1. **Configure** in sidebar → **▶️ Run Analysis**
        2. **Overview & Report**: Charts + executive summary
        3. **Top Companies**: Quality rankings (last column = technical rating)
        4. **Technical Analysis**: Technical rankings (last column = quality score)
        5. **Company Lookup**: Deep-dive into any ticker
        """)

st.markdown("---")
st.caption("Market Analysis System v2.2 | BIST Support | PCA-optimized Weights")
