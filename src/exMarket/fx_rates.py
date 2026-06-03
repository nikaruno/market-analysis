"""
FX rates helper for BIST USD conversion.

Downloads and caches daily USD/TRY rates from yfinance (USDTRY=X).
Provides utility functions to convert financial statements and price series
from TRY to USD using either:
  - Yearly average rate (for income statement and cash flow flows)
  - Year-end closing rate (for balance sheet point-in-time values)
  - Daily spot rate (for technical analysis price series)

Cache: data/fx/usdtry_daily.csv. Refreshes if older than 24 hours.

Design notes:
  - All conversion is "divide TRY value by USD/TRY rate" to get USD.
    e.g., 100 TRY at 32 TRY/USD = 100/32 = 3.125 USD.
  - If the FX cache cannot be loaded/refreshed, callers should fall back to
    not converting (the caller decides). All public functions return None or
    raise on failure rather than silently producing wrong numbers.
"""

import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime, timedelta

CACHE_DIR = Path("data/fx")
CACHE_PATH = CACHE_DIR / "usdtry_daily.csv"
CACHE_TTL_HOURS = 24
HISTORY_YEARS = 7  # enough for the 4-year fundamentals window plus buffer
TICKER = "USDTRY=X"

_in_memory_cache = None


def _is_cache_fresh() -> bool:
    """Return True if the cache file exists and is younger than CACHE_TTL_HOURS."""
    if not CACHE_PATH.exists():
        return False
    age = datetime.now() - datetime.fromtimestamp(CACHE_PATH.stat().st_mtime)
    return age < timedelta(hours=CACHE_TTL_HOURS)


def _download_rates() -> pd.DataFrame:
    """Download USD/TRY daily history from yfinance."""
    import yfinance as yf

    end = datetime.now()
    start = end - timedelta(days=365 * HISTORY_YEARS + 30)

    df = yf.download(TICKER, start=start, end=end, progress=False, auto_adjust=False)

    if df is None or df.empty:
        raise RuntimeError("yfinance returned no data for USDTRY=X")

    # yfinance can return MultiIndex columns
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)

    # We only need the Close (= official daily spot)
    out = pd.DataFrame({"usdtry": df["Close"]})
    out.index = pd.to_datetime(out.index).tz_localize(None)
    out.index.name = "date"
    out = out.dropna()

    if out.empty:
        raise RuntimeError("USDTRY=X returned only NaN values")

    return out


def load_or_download_rates(force_refresh: bool = False) -> pd.DataFrame:
    """
    Load USD/TRY daily rates. Uses cache if fresh, otherwise downloads and
    overwrites the cache. Returns a DataFrame indexed by date with one
    column 'usdtry'.

    Empty DataFrame is returned on irrecoverable failure (callers should
    treat empty as "FX unavailable, skip conversion").
    """
    global _in_memory_cache

    if _in_memory_cache is not None and not force_refresh:
        return _in_memory_cache

    CACHE_DIR.mkdir(parents=True, exist_ok=True)

    # Try cache first
    if _is_cache_fresh() and not force_refresh:
        try:
            df = pd.read_csv(CACHE_PATH, parse_dates=["date"], index_col="date")
            if not df.empty and "usdtry" in df.columns:
                _in_memory_cache = df
                return df
        except Exception as e:
            print(f"  [WARN] FX cache read failed ({e}); re-downloading.")

    # Download
    try:
        print(f"  Downloading USD/TRY rates ({HISTORY_YEARS} years)...")
        df = _download_rates()
        df.to_csv(CACHE_PATH)
        print(f"  ✓ FX rates cached: {len(df)} rows, "
              f"{df.index.min().date()} → {df.index.max().date()}")
        _in_memory_cache = df
        return df
    except Exception as e:
        print(f"  [ERROR] Could not download USD/TRY rates: {e}")
        # Last-ditch fallback: try stale cache if it exists
        if CACHE_PATH.exists():
            try:
                df = pd.read_csv(CACHE_PATH, parse_dates=["date"], index_col="date")
                print(f"  [WARN] Using stale FX cache ({len(df)} rows).")
                _in_memory_cache = df
                return df
            except Exception:
                pass
        _in_memory_cache = pd.DataFrame()
        return _in_memory_cache


def is_available() -> bool:
    """Quick check: can we actually do FX conversion?"""
    df = load_or_download_rates()
    return df is not None and not df.empty


def get_spot_series() -> pd.Series:
    """Return the full daily USD/TRY spot rate series, forward-filled
    so weekends/holidays have a value. Returns empty Series if FX unavailable."""
    df = load_or_download_rates()
    if df.empty:
        return pd.Series(dtype=float, name="usdtry")
    s = df["usdtry"].copy()
    s.index = pd.to_datetime(s.index).tz_localize(None)
    return s


def get_yearly_avg(year: int) -> float:
    """Average USD/TRY rate for a calendar year. NaN if unavailable."""
    s = get_spot_series()
    if s.empty:
        return float("nan")
    yearly = s[(s.index.year == year)]
    if yearly.empty:
        return float("nan")
    return float(yearly.mean())


def get_year_end(year: int) -> float:
    """Last available USD/TRY rate of a calendar year. NaN if unavailable."""
    s = get_spot_series()
    if s.empty:
        return float("nan")
    yearly = s[(s.index.year == year)]
    if yearly.empty:
        return float("nan")
    return float(yearly.iloc[-1])


def get_latest_spot() -> float:
    """Most recent available USD/TRY spot rate. NaN if unavailable.
    Used to convert a current market cap (trading currency) into the
    financial-statement currency so valuation ratios don't mix currencies.
    """
    s = get_spot_series()
    if s.empty:
        return float("nan")
    return float(s.iloc[-1])


def get_rate_for_period_end(period_end) -> float:
    """
    USD/TRY rate as of a specific period-end date (or last available
    rate before it). period_end can be string, Timestamp, or datetime.
    NaN if FX unavailable.
    """
    s = get_spot_series()
    if s.empty:
        return float("nan")

    ts = pd.to_datetime(period_end)
    if hasattr(ts, "tz_localize") and ts.tz is not None:
        ts = ts.tz_localize(None)

    # Use the rate ON the date if present, otherwise last rate before it
    same_or_before = s[s.index <= ts]
    if same_or_before.empty:
        # period is before our history starts — fall back to first available
        return float(s.iloc[0])
    return float(same_or_before.iloc[-1])


def convert_statement_columns(df: pd.DataFrame, method: str) -> pd.DataFrame:
    """
    Divide each value in `df` by the appropriate USD/TRY rate to produce
    a USD-denominated copy. Columns are interpreted as period-end dates
    (the format yfinance returns for income/balance/cashflow CSVs).

    method:
      'yearly_avg'  – use the average rate of the calendar year of each
                      column (income statement and cash flow: flows
                      generated over the year)
      'period_end'  – use the spot rate at the period-end date
                      (balance sheet: point-in-time stock values)

    If FX is unavailable, returns the original DataFrame unchanged.
    """
    if not is_available():
        return df

    if method not in ("yearly_avg", "period_end"):
        raise ValueError(f"Unknown FX conversion method: {method}")

    converted = df.copy()
    for col in converted.columns:
        try:
            ts = pd.to_datetime(col)
        except Exception:
            # Column header isn't a date — leave it alone
            continue

        if method == "yearly_avg":
            rate = get_yearly_avg(ts.year)
        else:  # period_end
            rate = get_rate_for_period_end(ts)

        if pd.isna(rate) or rate <= 0:
            # Couldn't determine rate for this column — skip conversion
            # rather than zeroing it out
            continue

        converted[col] = pd.to_numeric(converted[col], errors="coerce") / rate

    return converted


def convert_price_series(prices: pd.Series) -> pd.Series:
    """
    Convert a TRY-denominated daily price series to USD using daily spot
    rates. Forward-fills weekends/holidays so every trading day has a rate.
    Returns the original series unchanged if FX is unavailable.
    """
    spot = get_spot_series()
    if spot.empty:
        return prices

    # Normalise indices to tz-naive datetimes
    p = prices.copy()
    p.index = pd.to_datetime(p.index).tz_localize(None) if p.index.tz is not None else pd.to_datetime(p.index)

    # Reindex spot rates onto the price dates and forward-fill
    aligned = spot.reindex(p.index.union(spot.index)).sort_index().ffill().reindex(p.index)

    # Avoid division by zero
    aligned = aligned.replace(0, np.nan)

    return p / aligned


def convert_ohlcv(df: pd.DataFrame) -> pd.DataFrame:
    """
    Convert an OHLCV DataFrame from TRY to USD. Open/High/Low/Close are
    divided by the daily spot rate; Volume is left alone (it's a count of
    shares). Returns the original DataFrame if FX is unavailable.
    """
    spot = get_spot_series()
    if spot.empty:
        return df

    out = df.copy()
    idx = pd.to_datetime(out.index)
    if idx.tz is not None:
        idx = idx.tz_localize(None)
    out.index = idx

    aligned = spot.reindex(out.index.union(spot.index)).sort_index().ffill().reindex(out.index)
    aligned = aligned.replace(0, np.nan)

    for col in ("Open", "High", "Low", "Close", "Adj Close"):
        if col in out.columns:
            out[col] = out[col] / aligned

    return out


if __name__ == "__main__":
    # Quick self-test
    df = load_or_download_rates()
    if df.empty:
        print("FX unavailable.")
    else:
        print(f"Loaded {len(df)} days of USD/TRY data.")
        print(f"Latest: {df.index[-1].date()} → {df['usdtry'].iloc[-1]:.4f}")
        for y in (2022, 2023, 2024, 2025):
            avg = get_yearly_avg(y)
            ye = get_year_end(y)
            if not pd.isna(avg):
                print(f"  {y}: avg={avg:.3f}, year-end={ye:.3f}")
