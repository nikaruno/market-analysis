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

def _data_signature():
    """Return a (mtime, size) tuple for fundamentals_raw.csv. Used as a
    cache key so the lookups invalidate automatically when the pipeline
    re-runs."""
    try:
        s = Path("data/fundamentals_raw.csv").stat()
        return (s.st_mtime, s.st_size)
    except Exception:
        return None


def load_tech_lookup():
    if TECH_PATH.exists():
        t = pd.read_csv(TECH_PATH)
        return dict(zip(t['ticker'], t['technical_rating']))
    return {}

@st.cache_data(show_spinner=False)
def _load_mcap_lookup_cached(_sig):
    return _load_mcap_lookup_impl()

def load_mcap_lookup():
    return _load_mcap_lookup_cached(_data_signature())

def _load_mcap_lookup_impl():
    """
    Build a {ticker → market cap in USD billions} dict.

    Sources market_cap and currency from data/fundamentals_raw.csv (populated
    by scrape_fundamentals.py). TRY market caps are converted to USD using
    the latest USD/TRY spot rate; everything else is treated as USD-equivalent.
    Returns {} if the file is missing or unreadable.
    """
    try:
        raw_path = Path("data/fundamentals_raw.csv")
        if not raw_path.exists():
            return {}
        raw = pd.read_csv(raw_path)
        if "ticker" not in raw.columns or "market_cap" not in raw.columns:
            return {}
        raw["market_cap"] = pd.to_numeric(raw["market_cap"], errors="coerce")

        try_rate = None
        try:
            import fx_rates  # noqa: WPS433
            if fx_rates.is_available():
                spot = fx_rates.get_spot_series()
                if not spot.empty:
                    try_rate = float(spot.iloc[-1])
        except Exception:
            pass

        def _to_usd_b(row):
            mc = row.get("market_cap")
            if pd.isna(mc) or mc <= 0:
                return float("nan")
            cur = str(row.get("currency", "USD")).upper()
            if cur == "TRY":
                if try_rate is None or try_rate <= 0:
                    return float("nan")
                return mc / try_rate / 1e9
            return mc / 1e9

        raw["mcap_usd_b"] = raw.apply(_to_usd_b, axis=1)
        # Deduplicate (a ticker may appear in multiple sectors); keep the
        # row with the largest non-null mcap.
        dedup = (raw.dropna(subset=["mcap_usd_b"])
                    .sort_values("mcap_usd_b", ascending=False)
                    .drop_duplicates(subset="ticker", keep="first"))
        return dict(zip(dedup["ticker"], dedup["mcap_usd_b"]))
    except Exception as e:
        print(f"[GUI] load_mcap_lookup failed: {e}")
        return {}

@st.cache_data(show_spinner=False)
def _load_pe_lookup_cached(_sig):
    return _load_pe_lookup_impl()

def load_pe_lookup():
    return _load_pe_lookup_cached(_data_signature())

def _load_pe_lookup_impl():
    """
    Build a {ticker → P/E ratio} dict from data/fundamentals_raw.csv.

    P/E = market_cap / net_income. Both numerator and denominator are in the
    company's native currency, so the ratio is unit-free — no FX conversion
    is needed. A 25x P/E means the same thing on BIST as on NYSE.

    Edge cases:
      - net_income missing or <= 0 → omitted from the dict (P/E is undefined
        or negative for loss-making companies, and showing a negative P/E is
        misleading rather than informative).
      - net_income tiny (P/E > 999) → capped at 999.0 to keep the column readable.
      - duplicate tickers → kept once, with the largest valid market_cap.

    Returns {} if the file is missing or unreadable.
    """
    try:
        raw_path = Path("data/fundamentals_raw.csv")
        if not raw_path.exists():
            return {}
        raw = pd.read_csv(raw_path)
        needed = {"ticker", "market_cap", "net_income"}
        if not needed.issubset(raw.columns):
            return {}
        raw["market_cap"] = pd.to_numeric(raw["market_cap"], errors="coerce")
        raw["net_income"] = pd.to_numeric(raw["net_income"], errors="coerce")

        def _pe(row):
            mc = row.get("market_cap")
            ni = row.get("net_income")
            if pd.isna(mc) or pd.isna(ni) or mc <= 0 or ni <= 0:
                return float("nan")
            pe = mc / ni
            return min(pe, 999.0)  # cap astronomical P/Es

        raw["pe"] = raw.apply(_pe, axis=1)
        # Pick the row with the largest market_cap for each ticker (matches
        # the dedup strategy used by load_mcap_lookup).
        dedup = (raw.dropna(subset=["pe"])
                    .sort_values("market_cap", ascending=False)
                    .drop_duplicates(subset="ticker", keep="first"))
        return dict(zip(dedup["ticker"], dedup["pe"]))
    except Exception as e:
        print(f"[GUI] load_pe_lookup failed: {e}")
        return {}


# Row-matching key lists, mirrored from compute_detailed_metrics.py.
# Kept local rather than imported so the GUI module has no compile-time
# dependency on the scoring module (matters when the pipeline hasn't run yet).
_EQUITY_KEYS = ["Total Equity Gross Minority Interest", "Stockholders Equity",
                "Total Stockholder Equity", "Common Stock Equity"]
_DEBT_KEYS = ["Total Debt", "Long Term Debt And Capital Lease Obligation",
              "Total Liabilities Net Minority Interest"]
_CASH_KEYS = ["Cash And Cash Equivalents",
              "Cash Cash Equivalents And Short Term Investments"]
_EBITDA_KEYS = ["EBITDA", "Normalized EBITDA"]


def _statement_path(ticker: str, kind: str) -> Path:
    """Resolve a statement CSV path, handling both ASELS_IS_balance.csv
    and ASELS.IS_balance.csv naming conventions."""
    raw_dir = Path("data/fundamentals/raw")
    candidates = [
        raw_dir / f"{ticker}_{kind}.csv",
        raw_dir / f"{ticker.replace('.', '_')}_{kind}.csv",
    ]
    return next((p for p in candidates if p.exists()), None)


def _get_latest_row_value(df, names):
    """Find a row by trying the candidate names in order; return the latest
    (right-most) column value, parsed as a float, or NaN if not found."""
    for n in names:
        if n in df.index:
            row = df.loc[n]
            try:
                v = pd.to_numeric(row, errors="coerce")
                v = v.dropna()
                if len(v) > 0:
                    # yfinance returns columns newest-first → leftmost is latest
                    return float(v.iloc[0])
            except Exception:
                continue
    return float("nan")


@st.cache_data(show_spinner=False)
def _load_pb_lookup_cached(_sig):
    return _load_pb_lookup_impl()

def load_pb_lookup():
    return _load_pb_lookup_cached(_data_signature())

def _load_pb_lookup_impl():
    """
    Build a {ticker → P/B ratio} dict.

    P/B = market_cap / stockholders_equity. Both are in the company's native
    currency, so the ratio is currency-neutral (no FX conversion needed).

    Edge cases:
      - Equity ≤ 0 → omitted (some buyback-heavy companies have negative
        book value; P/B is misleading in that case).
      - Astronomical P/B (>99) → capped at 99 to keep the column readable.
        P/B over 100 is rare and almost always indicates either a data
        error or an extremely asset-light business; either way the exact
        number isn't informative.
      - Missing balance sheet → ticker omitted.
    """
    try:
        raw_path = Path("data/fundamentals_raw.csv")
        if not raw_path.exists():
            return {}
        raw = pd.read_csv(raw_path)
        if "ticker" not in raw.columns or "market_cap" not in raw.columns:
            return {}
        raw["market_cap"] = pd.to_numeric(raw["market_cap"], errors="coerce")

        result = {}
        # Iterate tickers in market_cap-descending order so dedup keeps the
        # row with the largest market cap when a ticker appears in multiple
        # sectors.
        seen = set()
        for _, row in raw.sort_values("market_cap", ascending=False).iterrows():
            ticker = row.get("ticker")
            if not ticker or ticker in seen:
                continue
            mc = row.get("market_cap")
            if pd.isna(mc) or mc <= 0:
                continue

            balance_path = _statement_path(ticker, "balance")
            if balance_path is None:
                continue
            try:
                balance = pd.read_csv(balance_path, index_col=0)
            except Exception:
                continue
            equity = _get_latest_row_value(balance, _EQUITY_KEYS)
            if pd.isna(equity) or equity <= 0:
                continue

            pb = mc / equity
            result[ticker] = min(pb, 99.0)
            seen.add(ticker)
        return result
    except Exception as e:
        print(f"[GUI] load_pb_lookup failed: {e}")
        return {}


@st.cache_data(show_spinner=False)
def _load_ev_ebitda_lookup_cached(_sig):
    return _load_ev_ebitda_lookup_impl()

def load_ev_ebitda_lookup():
    return _load_ev_ebitda_lookup_cached(_data_signature())

def _load_ev_ebitda_lookup_impl():
    """
    Build a {ticker → EV/EBITDA ratio} dict.

    Enterprise Value (EV) = Market Cap + Total Debt − Cash & Equivalents
    EV/EBITDA captures both equity and debt valuation, and uses an operating-
    profit measure that's less distorted by tax/interest/one-time items than
    net income. It's the default valuation ratio in professional finance.

    Currency-neutral: all components (market_cap, debt, cash, EBITDA) are in
    the company's native currency, so the ratio is unit-free.

    Edge cases:
      - EBITDA ≤ 0 → omitted (loss-making at the operating level; ratio is
        meaningless).
      - Missing debt → treated as 0 (companies legitimately reporting zero
        debt do exist; this is correct behavior).
      - Missing cash → treated as 0 (rare but harmless approximation).
      - Astronomical EV/EBITDA (>999) → capped at 999, matching P/E behavior.
    """
    try:
        raw_path = Path("data/fundamentals_raw.csv")
        if not raw_path.exists():
            return {}
        raw = pd.read_csv(raw_path)
        if "ticker" not in raw.columns or "market_cap" not in raw.columns:
            return {}
        raw["market_cap"] = pd.to_numeric(raw["market_cap"], errors="coerce")

        result = {}
        seen = set()
        for _, row in raw.sort_values("market_cap", ascending=False).iterrows():
            ticker = row.get("ticker")
            if not ticker or ticker in seen:
                continue
            mc = row.get("market_cap")
            if pd.isna(mc) or mc <= 0:
                continue

            balance_path = _statement_path(ticker, "balance")
            income_path = _statement_path(ticker, "income")
            if balance_path is None or income_path is None:
                continue
            try:
                balance = pd.read_csv(balance_path, index_col=0)
                income = pd.read_csv(income_path, index_col=0)
            except Exception:
                continue

            ebitda = _get_latest_row_value(income, _EBITDA_KEYS)
            if pd.isna(ebitda) or ebitda <= 0:
                continue
            debt = _get_latest_row_value(balance, _DEBT_KEYS)
            cash = _get_latest_row_value(balance, _CASH_KEYS)
            debt = 0.0 if pd.isna(debt) else debt
            cash = 0.0 if pd.isna(cash) else cash

            ev = mc + debt - cash
            ev_ebitda = ev / ebitda
            # EV can theoretically be negative (massive cash, tiny mcap) →
            # cap at 0 since a negative EV/EBITDA isn't a useful signal here.
            if ev_ebitda <= 0:
                continue
            result[ticker] = min(ev_ebitda, 999.0)
            seen.add(ticker)
        return result
    except Exception as e:
        print(f"[GUI] load_ev_ebitda_lookup failed: {e}")
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
            render_overview_section(bist_df, "BIST Stocks (fundamentals in USD)", "🇹🇷")
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
        mcap_lookup = load_mcap_lookup()
        pe_lookup = load_pe_lookup()
        pb_lookup = load_pb_lookup()
        ev_lookup = load_ev_ebitda_lookup()

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
            # Market cap (USD billions) — numeric for proper sorting
            if mcap_lookup:
                out['Mcap $B'] = out['ticker'].map(mcap_lookup).round(1)
            # Valuation ratios — currency-neutral, NaN for loss-makers / weird capital structures
            if pe_lookup:
                out['P/E'] = out['ticker'].map(pe_lookup).round(1)
            if pb_lookup:
                out['P/B'] = out['ticker'].map(pb_lookup).round(1)
            if ev_lookup:
                out['EV/EBITDA'] = out['ticker'].map(ev_lookup).round(1)
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
            st.subheader("🇹🇷 BIST Stocks (fundamentals in USD)")
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

        def format_tech_table(df, include_usd=False):
            cols = ['ticker', 'category', 'technical_score', 'technical_rating']
            if 'ma_buy' in df.columns: cols += ['ma_buy', 'ma_sell', 'osc_buy', 'osc_sell']
            if 'rsi' in df.columns: cols.append('rsi')
            # Dual rating columns for BIST (USD-converted secondary view)
            if include_usd and 'technical_score_usd' in df.columns:
                cols += ['technical_score_usd', 'technical_rating_usd']
            if 'quality_score' in df.columns: cols.append('quality_score')
            cols = [c for c in cols if c in df.columns]
            out = df[cols].copy()
            for c in ['technical_score', 'technical_score_usd', 'rsi', 'quality_score']:
                if c in out.columns: out[c] = out[c].round(1)
            # Friendlier column labels
            rename = {
                'technical_score': 'Tech (TL)' if include_usd else 'Tech',
                'technical_rating': 'Rating (TL)' if include_usd else 'Rating',
                'technical_score_usd': 'Tech (USD)',
                'technical_rating_usd': 'Rating (USD)',
            }
            out = out.rename(columns={k: v for k, v in rename.items() if k in out.columns})
            sort_col = 'Tech (TL)' if 'Tech (TL)' in out.columns else 'Tech'
            return out.sort_values(sort_col, ascending=False)

        def add_tech_indicator(df):
            """Add emoji indicator based on technical_rating."""
            out = df.copy()
            m = {'Strong Buy': '🟢', 'Buy': '🟢', 'Hold': '🟡', 'Sell': '🔴', 'Strong Sell': '🔴'}
            # Find the primary rating column under either of its possible names
            rating_col = next((c for c in ('Rating (TL)', 'Rating', 'technical_rating') if c in out.columns), None)
            if rating_col is not None:
                out.insert(0, '📊', out[rating_col].map(m).fillna('⚪'))
            return out

        def render_tech_section(df, label, currency="", include_usd=False):
            if len(df) == 0:
                st.info(f"No {label} stocks.")
                return
            c1, c2, c3, c4 = st.columns(4)
            with c1: st.metric("Stocks", len(df))
            with c2: st.metric("Buy Signals", len(df[df['technical_rating'].str.contains('Buy', na=False)]))
            with c3: st.metric("Sell Signals", len(df[df['technical_rating'].str.contains('Sell', na=False)]))
            with c4:
                if 'rsi' in df.columns: st.metric("Oversold", len(df[df['rsi'] < 30]))
            st.dataframe(add_tech_indicator(format_tech_table(df, include_usd=include_usd)),
                         use_container_width=True, hide_index=True)

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
            has_usd = 'technical_score_usd' in tech_bist.columns and tech_bist['technical_score_usd'].notna().any()
            if has_usd:
                st.subheader("🇹🇷 BIST Stocks — Dual Rating (TL primary, USD secondary)")
                st.caption("TL rating uses native prices (matches TradingView). USD rating shows what a USD-based investor sees — TRY depreciation typically pulls USD ratings lower.")
            else:
                st.subheader("🇹🇷 BIST Stocks (TL)")
            render_tech_section(tech_bist, "BIST", "TL", include_usd=has_usd)

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

            # --- VALUATION METRIC CARDS ---
            # Currency-neutral ratios; computed on demand from cached lookups.
            lookup_mcap = load_mcap_lookup()
            lookup_pe = load_pe_lookup()
            lookup_pb = load_pb_lookup()
            lookup_ev = load_ev_ebitda_lookup()
            v_mcap = lookup_mcap.get(ticker)
            v_pe = lookup_pe.get(ticker)
            v_pb = lookup_pb.get(ticker)
            v_ev = lookup_ev.get(ticker)
            v1, v2, v3, v4 = st.columns(4)
            with v1:
                st.metric("Market Cap", f"${v_mcap:.1f}B" if v_mcap is not None and pd.notna(v_mcap) else "—")
            with v2:
                st.metric("P/E", f"{v_pe:.1f}x" if v_pe is not None and pd.notna(v_pe) else "—",
                          help="Price / Earnings. N/A for loss-making companies.")
            with v3:
                st.metric("P/B", f"{v_pb:.1f}x" if v_pb is not None and pd.notna(v_pb) else "—",
                          help="Price / Book Value. N/A when equity is negative (heavy buybacks).")
            with v4:
                st.metric("EV/EBITDA", f"{v_ev:.1f}x" if v_ev is not None and pd.notna(v_ev) else "—",
                          help="Enterprise Value / EBITDA. Includes debt; less distorted by tax/one-time items than P/E.")

            # --- STOCK PRICE CHART (USD for BIST, native USD for global) ---
            st.markdown("---")
            is_bist = ticker.upper().endswith(".IS")
            price_currency = "USD"
            st.subheader(f"📈 Stock Price (1 Year, {price_currency})")
            try:
                import yfinance as yf
                stock = yf.Ticker(ticker)
                hist = stock.history(period="1y")
                if len(hist) > 0:
                    fx_note = ""
                    if is_bist:
                        # BIST tickers come from yfinance in TRY → convert to USD
                        try:
                            import fx_rates  # noqa: WPS433
                            if fx_rates.is_available():
                                hist = fx_rates.convert_ohlcv(hist)
                                fx_note = "Converted from TRY using daily USD/TRY spot rate."
                            else:
                                price_currency = "TRY"
                                fx_note = "⚠️ FX rates unavailable — showing native TRY."
                        except Exception as fxe:
                            price_currency = "TRY"
                            fx_note = f"⚠️ FX conversion failed ({fxe}); showing TRY."

                    fig = go.Figure()
                    fig.add_trace(go.Candlestick(
                        x=hist.index, open=hist['Open'], high=hist['High'],
                        low=hist['Low'], close=hist['Close'], name=ticker
                    ))
                    fig.update_layout(
                        title=f"{ticker} — 1 Year Price ({price_currency})",
                        yaxis_title=f"Price ({price_currency})",
                        xaxis_rangeslider_visible=False,
                        margin=dict(t=40, b=20, l=40, r=20),
                        height=350
                    )
                    st.plotly_chart(fig, use_container_width=True)
                    if fx_note:
                        st.caption(fx_note)
                else:
                    st.info("No price data available for this ticker.")
            except ImportError:
                st.info("Install yfinance (`pip install yfinance`) to see price charts.")
            except Exception as e:
                st.info(f"Could not load price data: {e}")

            # --- REVENUE & NET INCOME BAR CHART ---
            st.markdown("---")
            bar_currency = "USD"
            st.subheader(f"💰 Revenue & Net Income by Year ({bar_currency})")
            try:
                # Resolve income statement filename — handles both ASELS_IS_income.csv
                # (yfinance dot-replacement style) and direct ticker.csv naming.
                raw_dir = Path("data/fundamentals/raw")
                candidates = [
                    raw_dir / f"{ticker}_income.csv",
                    raw_dir / f"{ticker.replace('.', '_')}_income.csv",
                ]
                income_path = next((p for p in candidates if p.exists()), None)

                if income_path is None:
                    st.info("No income statement data found for this ticker. "
                            "Run the full analysis pipeline to download it.")
                else:
                    inc = pd.read_csv(income_path, index_col=0)

                    # Find Total Revenue and Net Income rows (using same key
                    # patterns as compute_detailed_metrics)
                    def find_row(df, candidates):
                        for name in candidates:
                            if name in df.index:
                                return df.loc[name]
                        return None

                    rev = find_row(inc, ["Total Revenue", "Revenue"])
                    ni = find_row(inc, ["Net Income", "Net Income Common Stockholders"])

                    if rev is None or ni is None:
                        st.info(f"Income statement is missing Revenue or Net Income rows. "
                                f"Available rows: {list(inc.index)[:8]}…")
                    else:
                        # Normalise column order to chronological (oldest first)
                        # and parse year from each period-end date column.
                        records = []
                        for col in inc.columns:
                            try:
                                year = pd.to_datetime(col).year
                            except Exception:
                                continue
                            r = pd.to_numeric(rev.get(col), errors="coerce")
                            n = pd.to_numeric(ni.get(col), errors="coerce")
                            records.append({"year": year, "revenue": r, "net_income": n})

                        if not records:
                            st.info("Income statement columns aren't dated — can't build the chart.")
                        else:
                            df_bar = pd.DataFrame(records).sort_values("year")
                            df_bar = df_bar.drop_duplicates(subset="year", keep="last")

                            # USD conversion for BIST
                            fx_caption = ""
                            if is_bist:
                                try:
                                    import fx_rates  # noqa: WPS433
                                    if fx_rates.is_available():
                                        rates = [fx_rates.get_yearly_avg(int(y)) for y in df_bar["year"]]
                                        df_bar["fx_rate"] = rates
                                        df_bar["revenue"] = df_bar["revenue"] / df_bar["fx_rate"]
                                        df_bar["net_income"] = df_bar["net_income"] / df_bar["fx_rate"]
                                        fx_caption = "Converted from TRY using yearly-average USD/TRY rates."
                                    else:
                                        bar_currency = "TRY"
                                        fx_caption = "⚠️ FX rates unavailable — showing native TRY."
                                except Exception as fxe:
                                    bar_currency = "TRY"
                                    fx_caption = f"⚠️ FX conversion failed ({fxe}); showing TRY."

                            # Pick a sensible scale (B for >= 1bn USD, M otherwise)
                            max_abs = max(
                                df_bar["revenue"].abs().max() if df_bar["revenue"].notna().any() else 0,
                                df_bar["net_income"].abs().max() if df_bar["net_income"].notna().any() else 0,
                            )
                            if max_abs >= 1e9:
                                scale, scale_label = 1e9, "Billions"
                            elif max_abs >= 1e6:
                                scale, scale_label = 1e6, "Millions"
                            else:
                                scale, scale_label = 1, ""

                            df_bar["Revenue"] = df_bar["revenue"] / scale
                            df_bar["Net Income"] = df_bar["net_income"] / scale

                            fig_bar = go.Figure()
                            fig_bar.add_trace(go.Bar(
                                x=df_bar["year"].astype(str),
                                y=df_bar["Revenue"],
                                name="Revenue",
                                marker_color="#3b82f6",
                                text=[f"{v:.2f}" if pd.notna(v) else "" for v in df_bar["Revenue"]],
                                textposition="outside",
                                cliponaxis=False,
                            ))
                            fig_bar.add_trace(go.Bar(
                                x=df_bar["year"].astype(str),
                                y=df_bar["Net Income"],
                                name="Net Income",
                                marker_color="#10b981",
                                text=[f"{v:.2f}" if pd.notna(v) else "" for v in df_bar["Net Income"]],
                                textposition="outside",
                                cliponaxis=False,
                            ))
                            y_label = f"{bar_currency}" + (f" ({scale_label})" if scale_label else "")

                            # Pad the y-axis so outside labels (top of bars and
                            # below zero for negative net income) aren't clipped.
                            all_vals = pd.concat([df_bar["Revenue"], df_bar["Net Income"]]).dropna()
                            if len(all_vals) > 0:
                                ymax = float(all_vals.max())
                                ymin = float(all_vals.min())
                                span = ymax - ymin if ymax != ymin else max(abs(ymax), 1.0)
                                pad = span * 0.18
                                y_low = min(0, ymin - pad)
                                y_high = ymax + pad
                            else:
                                y_low, y_high = 0, 1

                            fig_bar.update_layout(
                                barmode="group",
                                xaxis_title="Year",
                                yaxis_title=y_label,
                                yaxis=dict(range=[y_low, y_high]),
                                margin=dict(t=30, b=20, l=50, r=20),
                                height=420,
                                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
                            )
                            fig_bar.add_hline(y=0, line_color="rgba(128,128,128,0.4)", line_width=1)
                            st.plotly_chart(fig_bar, use_container_width=True)
                            if fx_caption:
                                st.caption(fx_caption)

                            # Compact YoY-growth table beneath the chart
                            df_bar["Rev YoY"] = df_bar["revenue"].pct_change()
                            df_bar["NI YoY"] = df_bar["net_income"].pct_change()
                            tbl = pd.DataFrame({
                                "Year": df_bar["year"].astype(str),
                                f"Revenue ({bar_currency} {scale_label})".strip():
                                    df_bar["Revenue"].round(2),
                                f"Net Income ({bar_currency} {scale_label})".strip():
                                    df_bar["Net Income"].round(2),
                                "Rev YoY":
                                    df_bar["Rev YoY"].apply(lambda v: f"{v*100:+.1f}%" if pd.notna(v) else "—"),
                                "NI YoY":
                                    df_bar["NI YoY"].apply(lambda v: f"{v*100:+.1f}%" if pd.notna(v) else "—"),
                            })
                            st.dataframe(tbl, use_container_width=True, hide_index=True)
            except Exception as e:
                st.info(f"Could not load Revenue/Net Income chart: {e}")

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
            # Market cap (USD billions) — numeric so the column sorts correctly
            peer_mcaps = load_mcap_lookup()
            if peer_mcaps:
                pd_display['Mcap $B'] = pd_display['ticker'].map(peer_mcaps).round(1)
            # Valuation ratios — currency-neutral, NaN for loss-makers / negative equity
            peer_pes = load_pe_lookup()
            if peer_pes:
                pd_display['P/E'] = pd_display['ticker'].map(peer_pes).round(1)
            peer_pbs = load_pb_lookup()
            if peer_pbs:
                pd_display['P/B'] = pd_display['ticker'].map(peer_pbs).round(1)
            peer_evs = load_ev_ebitda_lookup()
            if peer_evs:
                pd_display['EV/EBITDA'] = pd_display['ticker'].map(peer_evs).round(1)
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

                    # Dual rating for BIST: show USD-converted view
                    has_usd = ('technical_score_usd' in tr.index and pd.notna(tr.get('technical_score_usd')))
                    if has_usd:
                        st.caption("**USD-converted rating** (what a USD investor sees — TRY depreciation often pulls this lower):")
                        u1, u2, u3, u4 = st.columns(4)
                        with u1: st.metric("Tech Score (USD)", f"{tr.get('technical_score_usd', 0):.0f}")
                        with u2: st.metric("Rating (USD)", tr.get('technical_rating_usd', 'N/A'))
                        with u3:
                            delta = tr.get('technical_score_usd', 0) - tr.get('technical_score', 0)
                            st.metric("Δ vs TL", f"{delta:+.0f}")
                        with u4:
                            if 'ma_buy_usd' in tr.index:
                                st.caption(f"MA: {int(tr.get('ma_buy_usd',0))}B / {int(tr.get('ma_sell_usd',0))}S · Osc: {int(tr.get('osc_buy_usd',0))}B / {int(tr.get('osc_sell_usd',0))}S")
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
    with st.expander("💰 Valuation Ratios"):
        st.markdown("""
        Three currency-neutral valuation ratios are shown alongside quality
        scores. They are **not** baked into the quality score — they're a
        parallel signal so a great business at a bad price is still flagged
        as great quality, with valuation visible for context.

        - **P/E (Price / Earnings)** — `market_cap / net_income`.
          The classic valuation ratio. Shown as N/A for loss-making companies.
          Capped at 999x for stocks with very small earnings.

        - **P/B (Price / Book)** — `market_cap / stockholders_equity`.
          A "value investor" lens. Useful for capital-intensive businesses.
          Shown as N/A when equity is negative (some buyback-heavy companies
          like MCD have negative book value).

        - **EV/EBITDA** — `(market_cap + total_debt − cash) / EBITDA`.
          The professional-analyst default. Captures both equity and debt;
          less distorted by tax/interest/one-time items than P/E. Shown as
          N/A when EBITDA is negative.

        All three are **currency-neutral** (TRY/TRY cancels just like USD/USD),
        so BIST ratios are directly comparable to US peers — no FX conversion
        needed. A 13× P/E means the same thing on Borsa Istanbul as on NYSE.
        """)
    with st.expander("🇹🇷 BIST / USD Conversion"):
        st.markdown("""
        **Fundamentals (always converted to USD):**
        Income statement & cash flow are divided by the **yearly-average** USD/TRY rate.
        Balance sheet items are divided by the **year-end** USD/TRY rate.
        This makes ROIC, FCF, and especially growth metrics directly comparable to US peers
        (a 50% TRY revenue CAGR is often only ~20% in real USD terms).

        **Technical analysis (dual rating):**
        - **Primary (TL):** computed on native TRY prices — matches what TradingView shows.
        - **Secondary (USD):** the same 26 indicators run on USD-converted prices.
          Most BIST stocks rate lower in USD because TRY depreciation drags moving-average
          voters toward "Sell". Use this to see what a USD-based investor experiences.

        FX rates are downloaded from yfinance (USDTRY=X) and cached in `data/fx/`.
        If FX data is unavailable, the system falls back to TL with a warning — no values
        are silently corrupted.
        """)
    with st.expander("🎮 How to Use"):
        st.markdown("""
        1. **Overview**: Top/bottom companies, category averages, report
        2. **Top Companies**: Quality rankings (green=high, red=low) + technical rating
        3. **Technical Analysis**: Technical rankings + quality score column
        4. **Company Lookup**: Deep-dive with stock price chart, metric breakdown, peers
        """)

st.markdown("---")
st.caption("Market Analysis System v3 | EMA Weights | BIST USD Conversion")
