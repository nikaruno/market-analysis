"""
Technical Analysis Module v2
TradingView-style scoring with 26 indicators:
  - 15 Moving Averages (SMA/EMA at 10/20/30/50/100/200, Hull MA, VWMA, Ichimoku)
  - 11 Oscillators (RSI, Stochastic, CCI, ADX, AO, Momentum, MACD, StochRSI, Williams%R, BBP, UO)

Each indicator votes Buy (+1), Neutral (0), or Sell (-1).
MA score and Oscillator score are averaged → overall rating.
Final technical_score is mapped to 0-100 scale for compatibility.
"""

import yfinance as yf
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime, timedelta

# FX conversion for BIST stocks (lazy import — failures don't kill the module).
try:
    import fx_rates  # type: ignore
    _FX_AVAILABLE = True
except Exception as _e:  # pragma: no cover
    print(f"  [WARN] fx_rates module not available in technical_analysis: {_e}")
    fx_rates = None
    _FX_AVAILABLE = False

# Paths
SCORES_PATH = Path("data/fundamentals/absolute_scores.csv")
OUTPUT_PATH = Path("data/technical_analysis.csv")
LOOKBACK_DAYS = 300  # Need enough data for SMA200 + buffer


# ============================================================================
# INDICATOR CALCULATIONS (kept as public functions for technical_charts.py)
# ============================================================================

def calculate_rsi(prices, period=14):
    """Calculate Relative Strength Index."""
    delta = prices.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

def calculate_macd(prices, fast=12, slow=26, signal=9):
    """Calculate MACD (Moving Average Convergence Divergence)."""
    ema_fast = prices.ewm(span=fast, adjust=False).mean()
    ema_slow = prices.ewm(span=slow, adjust=False).mean()
    macd_line = ema_fast - ema_slow
    signal_line = macd_line.ewm(span=signal, adjust=False).mean()
    histogram = macd_line - signal_line
    return macd_line, signal_line, histogram

def calculate_bollinger_bands(prices, period=20, num_std=2):
    """Calculate Bollinger Bands."""
    sma = prices.rolling(window=period).mean()
    std = prices.rolling(window=period).std()
    upper_band = sma + (std * num_std)
    lower_band = sma - (std * num_std)
    return upper_band, sma, lower_band

def calculate_atr(high, low, close, period=14):
    """Calculate Average True Range."""
    high_low = high - low
    high_close = np.abs(high - close.shift())
    low_close = np.abs(low - close.shift())
    true_range = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
    atr = true_range.rolling(window=period).mean()
    return atr

def calculate_stochastic(high, low, close, k_period=14, d_period=3):
    """Calculate Stochastic Oscillator."""
    lowest_low = low.rolling(window=k_period).min()
    highest_high = high.rolling(window=k_period).max()
    k_percent = 100 * ((close - lowest_low) / (highest_high - lowest_low))
    d_percent = k_percent.rolling(window=d_period).mean()
    return k_percent, d_percent

def calculate_adx(high, low, close, period=14):
    """Calculate Average Directional Index with +DI and -DI."""
    high_diff = high.diff()
    low_diff = -low.diff()
    
    plus_dm = high_diff.where((high_diff > low_diff) & (high_diff > 0), 0)
    minus_dm = low_diff.where((low_diff > high_diff) & (low_diff > 0), 0)
    
    atr = calculate_atr(high, low, close, period)
    
    plus_di = 100 * (plus_dm.rolling(window=period).mean() / atr)
    minus_di = 100 * (minus_dm.rolling(window=period).mean() / atr)
    
    dx = 100 * np.abs(plus_di - minus_di) / (plus_di + minus_di)
    adx = dx.rolling(window=period).mean()
    
    return adx, plus_di, minus_di

def calculate_cci(high, low, close, period=20):
    """Calculate Commodity Channel Index."""
    tp = (high + low + close) / 3
    sma_tp = tp.rolling(window=period).mean()
    mad = tp.rolling(window=period).apply(lambda x: np.mean(np.abs(x - np.mean(x))), raw=True)
    cci = (tp - sma_tp) / (0.015 * mad)
    return cci

def calculate_williams_r(high, low, close, period=14):
    """Calculate Williams %R."""
    highest_high = high.rolling(window=period).max()
    lowest_low = low.rolling(window=period).min()
    wr = -100 * (highest_high - close) / (highest_high - lowest_low)
    return wr

def calculate_momentum(close, period=10):
    """Calculate Momentum indicator."""
    return close - close.shift(period)

def calculate_awesome_oscillator(high, low):
    """Calculate Awesome Oscillator."""
    midpoint = (high + low) / 2
    ao = midpoint.rolling(window=5).mean() - midpoint.rolling(window=34).mean()
    return ao

def calculate_stoch_rsi(close, rsi_period=14, stoch_period=14, k_period=3, d_period=3):
    """Calculate Stochastic RSI."""
    rsi = calculate_rsi(close, rsi_period)
    rsi_low = rsi.rolling(window=stoch_period).min()
    rsi_high = rsi.rolling(window=stoch_period).max()
    stoch_rsi = (rsi - rsi_low) / (rsi_high - rsi_low)
    k = stoch_rsi.rolling(window=k_period).mean()
    d = k.rolling(window=d_period).mean()
    return k, d

def calculate_bull_bear_power(high, low, close, period=13):
    """Calculate Bull Bear Power (Elder-Ray)."""
    ema = close.ewm(span=period, adjust=False).mean()
    bull_power = high - ema
    bear_power = low - ema
    return bull_power, bear_power

def calculate_ultimate_oscillator(high, low, close, p1=7, p2=14, p3=28):
    """Calculate Ultimate Oscillator."""
    prev_close = close.shift(1)
    bp = close - pd.concat([low, prev_close], axis=1).min(axis=1)
    tr = pd.concat([high, prev_close], axis=1).max(axis=1) - pd.concat([low, prev_close], axis=1).min(axis=1)
    
    avg1 = bp.rolling(p1).sum() / tr.rolling(p1).sum()
    avg2 = bp.rolling(p2).sum() / tr.rolling(p2).sum()
    avg3 = bp.rolling(p3).sum() / tr.rolling(p3).sum()
    
    uo = 100 * (4 * avg1 + 2 * avg2 + avg3) / 7
    return uo

def calculate_hull_ma(close, period=9):
    """Calculate Hull Moving Average."""
    half_period = int(period / 2)
    sqrt_period = int(np.sqrt(period))
    wma_half = close.rolling(window=half_period).mean()
    wma_full = close.rolling(window=period).mean()
    diff = 2 * wma_half - wma_full
    hull = diff.rolling(window=sqrt_period).mean()
    return hull

def calculate_vwma(close, volume, period=20):
    """Calculate Volume Weighted Moving Average."""
    vwma = (close * volume).rolling(window=period).sum() / volume.rolling(window=period).sum()
    return vwma

def calculate_ichimoku(high, low, close, conv_period=9, base_period=26, span_period=52):
    """Calculate Ichimoku Cloud components."""
    # Conversion Line (Tenkan-sen)
    conv_high = high.rolling(window=conv_period).max()
    conv_low = low.rolling(window=conv_period).min()
    conversion = (conv_high + conv_low) / 2
    
    # Base Line (Kijun-sen)
    base_high = high.rolling(window=base_period).max()
    base_low = low.rolling(window=base_period).min()
    base = (base_high + base_low) / 2
    
    # Leading Span A (Senkou Span A)
    span_a = ((conversion + base) / 2).shift(base_period)
    
    # Leading Span B (Senkou Span B)
    span_b_high = high.rolling(window=span_period).max()
    span_b_low = low.rolling(window=span_period).min()
    span_b = ((span_b_high + span_b_low) / 2).shift(base_period)
    
    return conversion, base, span_a, span_b


# ============================================================================
# TRADINGVIEW-STYLE RATING SYSTEM
# ============================================================================

def _safe(val):
    """Return True if val is a valid number."""
    if val is None:
        return False
    try:
        return not (pd.isna(val) or np.isinf(val))
    except (TypeError, ValueError):
        return False


def rate_moving_averages(close, high, low, volume):
    """
    Rate 15 Moving Average indicators: each votes +1 (Buy), 0 (Neutral), -1 (Sell).
    Returns (ma_score, votes_dict) where ma_score is average of all votes (-1 to +1).
    
    TradingView logic: Price > MA → Buy, Price < MA → Sell.
    """
    price = close.iloc[-1]
    votes = {}
    
    # 6 SMAs
    for period in [10, 20, 30, 50, 100, 200]:
        sma = close.rolling(window=period).mean()
        val = sma.iloc[-1]
        key = f'SMA{period}'
        if _safe(val):
            votes[key] = 1 if price > val else -1
    
    # 6 EMAs
    for period in [10, 20, 30, 50, 100, 200]:
        ema = close.ewm(span=period, adjust=False).mean()
        val = ema.iloc[-1]
        key = f'EMA{period}'
        if _safe(val):
            votes[key] = 1 if price > val else -1
    
    # Hull MA (9)
    hull = calculate_hull_ma(close, 9)
    val = hull.iloc[-1]
    prev = hull.iloc[-2] if len(hull) > 1 else None
    if _safe(val) and _safe(prev):
        votes['HullMA9'] = 1 if val > prev else -1
    
    # VWMA (20)
    vwma = calculate_vwma(close, volume, 20)
    val = vwma.iloc[-1]
    if _safe(val):
        votes['VWMA20'] = 1 if price > val else -1
    
    # Ichimoku Cloud
    conv, base, span_a, span_b = calculate_ichimoku(high, low, close)
    conv_v = conv.iloc[-1]
    base_v = base.iloc[-1]
    span_a_v = span_a.iloc[-1]
    span_b_v = span_b.iloc[-1]
    
    if all(_safe(v) for v in [conv_v, base_v, span_a_v, span_b_v]):
        # Buy: span_a > span_b, base > span_a, conv > base, price > conv
        if span_a_v > span_b_v and base_v > span_a_v and conv_v > base_v and price > conv_v:
            votes['Ichimoku'] = 1
        elif span_a_v < span_b_v and base_v < span_a_v and conv_v < base_v and price < conv_v:
            votes['Ichimoku'] = -1
        else:
            votes['Ichimoku'] = 0
    
    if votes:
        ma_score = sum(votes.values()) / len(votes)
    else:
        ma_score = 0
    
    return ma_score, votes


def rate_oscillators(close, high, low, volume):
    """
    Rate 11 Oscillator indicators following TradingView methodology.
    Returns (osc_score, votes_dict).
    """
    votes = {}
    
    # 1. RSI (14)
    rsi = calculate_rsi(close, 14)
    rsi_v = rsi.iloc[-1]
    rsi_prev = rsi.iloc[-2] if len(rsi) > 1 else None
    if _safe(rsi_v):
        if rsi_v < 30 and _safe(rsi_prev) and rsi_v > rsi_prev:
            votes['RSI'] = 1  # Oversold and turning up
        elif rsi_v > 70 and _safe(rsi_prev) and rsi_v < rsi_prev:
            votes['RSI'] = -1  # Overbought and turning down
        else:
            votes['RSI'] = 0
    
    # 2. Stochastic (14, 3, 3)
    stoch_k, stoch_d = calculate_stochastic(high, low, close, 14, 3)
    sk = stoch_k.iloc[-1]
    sd = stoch_d.iloc[-1]
    if _safe(sk) and _safe(sd):
        if sk < 20 and sk > sd:
            votes['Stochastic'] = 1
        elif sk > 80 and sk < sd:
            votes['Stochastic'] = -1
        else:
            votes['Stochastic'] = 0
    
    # 3. CCI (20)
    cci = calculate_cci(high, low, close, 20)
    cci_v = cci.iloc[-1]
    cci_prev = cci.iloc[-2] if len(cci) > 1 else None
    if _safe(cci_v):
        if cci_v > 100:
            votes['CCI'] = 1
        elif cci_v < -100:
            votes['CCI'] = -1
        else:
            votes['CCI'] = 0
    
    # 4. ADX (14, 14) with +DI / -DI
    adx, plus_di, minus_di = calculate_adx(high, low, close, 14)
    adx_v = adx.iloc[-1]
    pdi = plus_di.iloc[-1]
    mdi = minus_di.iloc[-1]
    if _safe(adx_v) and _safe(pdi) and _safe(mdi) and adx_v > 20:
        if pdi > mdi:
            votes['ADX'] = 1
        elif pdi < mdi:
            votes['ADX'] = -1
        else:
            votes['ADX'] = 0
    else:
        votes['ADX'] = 0
    
    # 5. Awesome Oscillator
    ao = calculate_awesome_oscillator(high, low)
    ao_v = ao.iloc[-1]
    ao_prev = ao.iloc[-2] if len(ao) > 1 else None
    if _safe(ao_v) and _safe(ao_prev):
        if ao_v > 0 and ao_v > ao_prev:
            votes['AO'] = 1
        elif ao_v < 0 and ao_v < ao_prev:
            votes['AO'] = -1
        else:
            votes['AO'] = 0
    
    # 6. Momentum (10)
    mom = calculate_momentum(close, 10)
    mom_v = mom.iloc[-1]
    mom_prev = mom.iloc[-2] if len(mom) > 1 else None
    if _safe(mom_v) and _safe(mom_prev):
        if mom_v > mom_prev:
            votes['Momentum'] = 1
        elif mom_v < mom_prev:
            votes['Momentum'] = -1
        else:
            votes['Momentum'] = 0
    
    # 7. MACD (12, 26, 9)
    macd_line, signal_line, histogram = calculate_macd(close, 12, 26, 9)
    macd_v = macd_line.iloc[-1]
    sig_v = signal_line.iloc[-1]
    if _safe(macd_v) and _safe(sig_v):
        if macd_v > sig_v:
            votes['MACD'] = 1
        elif macd_v < sig_v:
            votes['MACD'] = -1
        else:
            votes['MACD'] = 0
    
    # 8. Stochastic RSI (3, 3, 14, 14)
    srsi_k, srsi_d = calculate_stoch_rsi(close, 14, 14, 3, 3)
    srsi_kv = srsi_k.iloc[-1]
    srsi_dv = srsi_d.iloc[-1]
    if _safe(srsi_kv) and _safe(srsi_dv):
        if srsi_kv < 0.2 and srsi_kv > srsi_dv:
            votes['StochRSI'] = 1
        elif srsi_kv > 0.8 and srsi_kv < srsi_dv:
            votes['StochRSI'] = -1
        else:
            votes['StochRSI'] = 0
    
    # 9. Williams %R (14)
    wr = calculate_williams_r(high, low, close, 14)
    wr_v = wr.iloc[-1]
    wr_prev = wr.iloc[-2] if len(wr) > 1 else None
    if _safe(wr_v):
        if wr_v < -80 and _safe(wr_prev) and wr_v > wr_prev:
            votes['WilliamsR'] = 1
        elif wr_v > -20 and _safe(wr_prev) and wr_v < wr_prev:
            votes['WilliamsR'] = -1
        else:
            votes['WilliamsR'] = 0
    
    # 10. Bull Bear Power (13)
    bull_p, bear_p = calculate_bull_bear_power(high, low, close, 13)
    bp_v = bull_p.iloc[-1]
    brp_v = bear_p.iloc[-1]
    if _safe(bp_v) and _safe(brp_v):
        bbp = bp_v + brp_v
        if bbp > 0:
            votes['BBPower'] = 1
        elif bbp < 0:
            votes['BBPower'] = -1
        else:
            votes['BBPower'] = 0
    
    # 11. Ultimate Oscillator (7, 14, 28)
    uo = calculate_ultimate_oscillator(high, low, close, 7, 14, 28)
    uo_v = uo.iloc[-1]
    if _safe(uo_v):
        if uo_v > 70:
            votes['UO'] = 1
        elif uo_v < 30:
            votes['UO'] = -1
        else:
            votes['UO'] = 0
    
    if votes:
        osc_score = sum(votes.values()) / len(votes)
    else:
        osc_score = 0
    
    return osc_score, votes


def compute_technical_rating(overall_score):
    """Convert overall score (-1 to +1) to rating string (TradingView thresholds)."""
    if overall_score >= 0.5:
        return 'Strong Buy'
    elif overall_score >= 0.1:
        return 'Buy'
    elif overall_score > -0.1:
        return 'Hold'
    elif overall_score > -0.5:
        return 'Sell'
    else:
        return 'Strong Sell'


def score_to_100(score_neg1_to_1):
    """Map score from [-1, +1] to [0, 100] scale for backward compatibility."""
    return (score_neg1_to_1 + 1) * 50


def _compute_ratings_only(df):
    """
    Compute just the TradingView-style voting ratings (MA + Oscillator) from
    an OHLCV DataFrame. Returns a dict with the rating-related fields, or
    None if data is insufficient.

    Used to compute a secondary 'USD-converted' rating for BIST stocks
    without re-downloading prices.
    """
    if df is None or df.empty or len(df) < 50:
        return None

    if isinstance(df.columns, pd.MultiIndex):
        df = df.copy()
        df.columns = df.columns.get_level_values(0)

    close = df["Close"]
    high = df["High"]
    low = df["Low"]
    volume = df["Volume"]

    try:
        ma_score, ma_votes = rate_moving_averages(close, high, low, volume)
        osc_score, osc_votes = rate_oscillators(close, high, low, volume)
    except Exception as e:
        print(f"    [WARN] Rating calc failed: {e}")
        return None

    overall_score = (ma_score + osc_score) / 2

    ma_buy = sum(1 for v in ma_votes.values() if v > 0)
    ma_sell = sum(1 for v in ma_votes.values() if v < 0)
    osc_buy = sum(1 for v in osc_votes.values() if v > 0)
    osc_sell = sum(1 for v in osc_votes.values() if v < 0)
    total_buy = ma_buy + osc_buy
    total_sell = ma_sell + osc_sell
    total_neutral = (len(ma_votes) + len(osc_votes)) - total_buy - total_sell

    return {
        "ma_rating": ma_score,
        "osc_rating": osc_score,
        "overall_rating": overall_score,
        "technical_score": score_to_100(overall_score),
        "technical_rating": compute_technical_rating(overall_score),
        "ma_buy": ma_buy,
        "ma_sell": ma_sell,
        "osc_buy": osc_buy,
        "osc_sell": osc_sell,
        "total_buy": total_buy,
        "total_sell": total_sell,
        "total_neutral": total_neutral,
    }


# ============================================================================
# MAIN SIGNAL FUNCTION
# ============================================================================

def get_technical_signals(ticker, lookback_days=LOOKBACK_DAYS):
    """
    Download price data and calculate all technical indicators for a ticker.
    Returns dict with current indicator values and TradingView-style scores.
    """
    try:
        end_date = datetime.now()
        start_date = end_date - timedelta(days=lookback_days + 100)
        
        print(f"  Analyzing {ticker}...")
        
        df = yf.download(ticker, start=start_date, end=end_date, progress=False)
        
        if df.empty or len(df) < 50:
            print(f"  [WARN] Insufficient data for {ticker}")
            return None
        
        # Handle multi-level columns from yfinance
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
        
        close = df['Close']
        high = df['High']
        low = df['Low']
        volume = df['Volume']
        
        # ---- Calculate display indicators (for CSV and charts) ----
        rsi = calculate_rsi(close)
        macd_line, signal_line, histogram = calculate_macd(close)
        bb_upper, bb_middle, bb_lower = calculate_bollinger_bands(close)
        atr = calculate_atr(high, low, close)
        stoch_k, stoch_d = calculate_stochastic(high, low, close)
        adx_val, plus_di, minus_di = calculate_adx(high, low, close)
        
        sma_50 = close.rolling(window=50).mean()
        sma_200 = close.rolling(window=200).mean()
        
        # ---- TradingView-style ratings ----
        ma_score, ma_votes = rate_moving_averages(close, high, low, volume)
        osc_score, osc_votes = rate_oscillators(close, high, low, volume)
        overall_score = (ma_score + osc_score) / 2
        
        # Count buy/sell votes
        all_votes = {**{f'ma_{k}': v for k, v in ma_votes.items()},
                     **{f'osc_{k}': v for k, v in osc_votes.items()}}
        buy_count = sum(1 for v in all_votes.values() if v > 0)
        sell_count = sum(1 for v in all_votes.values() if v < 0)
        neutral_count = sum(1 for v in all_votes.values() if v == 0)
        
        ma_buy = sum(1 for v in ma_votes.values() if v > 0)
        ma_sell = sum(1 for v in ma_votes.values() if v < 0)
        osc_buy = sum(1 for v in osc_votes.values() if v > 0)
        osc_sell = sum(1 for v in osc_votes.values() if v < 0)
        
        # Bollinger position for display
        bb_pos = (close.iloc[-1] - bb_lower.iloc[-1]) / (bb_upper.iloc[-1] - bb_lower.iloc[-1]) if (bb_upper.iloc[-1] - bb_lower.iloc[-1]) != 0 else 0.5
        
        current = {
            'ticker': ticker,
            'date': df.index[-1].strftime('%Y-%m-%d'),
            'price': close.iloc[-1],
            
            # RSI
            'rsi': rsi.iloc[-1],
            'rsi_signal': 'Oversold' if rsi.iloc[-1] < 30 else ('Overbought' if rsi.iloc[-1] > 70 else 'Neutral'),
            
            # MACD
            'macd': macd_line.iloc[-1],
            'macd_signal': signal_line.iloc[-1],
            'macd_histogram': histogram.iloc[-1],
            'macd_crossover': 'Bullish' if histogram.iloc[-1] > 0 and histogram.iloc[-2] <= 0 else (
                              'Bearish' if histogram.iloc[-1] < 0 and histogram.iloc[-2] >= 0 else 'None'),
            
            # Bollinger Bands
            'bb_upper': bb_upper.iloc[-1],
            'bb_middle': bb_middle.iloc[-1],
            'bb_lower': bb_lower.iloc[-1],
            'bb_position': bb_pos,
            'bb_signal': 'Near Upper' if close.iloc[-1] > bb_upper.iloc[-1] * 0.98 else (
                        'Near Lower' if close.iloc[-1] < bb_lower.iloc[-1] * 1.02 else 'Middle'),
            
            # Moving Averages
            'sma_50': sma_50.iloc[-1] if not pd.isna(sma_50.iloc[-1]) else None,
            'sma_200': sma_200.iloc[-1] if not pd.isna(sma_200.iloc[-1]) else None,
            'price_vs_sma50': ((close.iloc[-1] / sma_50.iloc[-1]) - 1) * 100 if not pd.isna(sma_50.iloc[-1]) else None,
            'price_vs_sma200': ((close.iloc[-1] / sma_200.iloc[-1]) - 1) * 100 if not pd.isna(sma_200.iloc[-1]) else None,
            'ma_trend': 'Uptrend' if (not pd.isna(sma_50.iloc[-1]) and not pd.isna(sma_200.iloc[-1])
                                      and sma_50.iloc[-1] > sma_200.iloc[-1]) else 'Downtrend',
            
            # ATR (Volatility)
            'atr': atr.iloc[-1],
            'atr_percent': (atr.iloc[-1] / close.iloc[-1]) * 100,
            
            # Stochastic
            'stoch_k': stoch_k.iloc[-1],
            'stoch_d': stoch_d.iloc[-1],
            'stoch_signal': 'Oversold' if stoch_k.iloc[-1] < 20 else ('Overbought' if stoch_k.iloc[-1] > 80 else 'Neutral'),
            
            # ADX
            'adx': adx_val.iloc[-1] if not pd.isna(adx_val.iloc[-1]) else None,
            'trend_strength': 'Strong' if (not pd.isna(adx_val.iloc[-1]) and adx_val.iloc[-1] > 25) else 'Weak',
            
            # Price momentum
            'return_1m': ((close.iloc[-1] / close.iloc[-20]) - 1) * 100 if len(close) >= 20 else None,
            'return_3m': ((close.iloc[-1] / close.iloc[-60]) - 1) * 100 if len(close) >= 60 else None,
            'return_6m': ((close.iloc[-1] / close.iloc[-120]) - 1) * 100 if len(close) >= 120 else None,
            
            # === NEW: TradingView-style scores ===
            'ma_rating': ma_score,                              # -1 to +1
            'osc_rating': osc_score,                            # -1 to +1
            'overall_rating': overall_score,                    # -1 to +1
            'technical_score': score_to_100(overall_score),     # 0-100 (backward compat)
            'technical_rating': compute_technical_rating(overall_score),
            
            # Vote counts
            'ma_buy': ma_buy,
            'ma_sell': ma_sell,
            'osc_buy': osc_buy,
            'osc_sell': osc_sell,
            'total_buy': buy_count,
            'total_sell': sell_count,
            'total_neutral': neutral_count,
        }

        # ---- Dual rating for BIST: also compute USD-converted ratings -------
        # The native (TRY) rating above is the primary one — TradingView shows
        # BIST charts in TRY too, and TRY depreciation distorts USD MAs heavily.
        # The USD rating is provided as a secondary signal so a USD-based
        # investor can see "this stock is up in TRY but flat/down in USD".
        is_bist = ticker.upper().endswith(".IS")
        if is_bist and _FX_AVAILABLE:
            try:
                if fx_rates.is_available():
                    df_usd = fx_rates.convert_ohlcv(df)
                    usd_ratings = _compute_ratings_only(df_usd)
                    if usd_ratings is not None:
                        for k, v in usd_ratings.items():
                            current[f"{k}_usd"] = v
                        current["currency"] = "TRY"  # primary is TRY
                        current["has_usd_rating"] = True
                        print(f"    + USD rating: "
                              f"{usd_ratings['technical_rating']} "
                              f"({usd_ratings['technical_score']:.0f})")
                    else:
                        current["has_usd_rating"] = False
                else:
                    current["has_usd_rating"] = False
            except Exception as fxe:
                print(f"    [WARN] USD rating failed for {ticker}: {fxe}")
                current["has_usd_rating"] = False
        else:
            current["currency"] = "USD"
            current["has_usd_rating"] = False
        # ---------------------------------------------------------------------

        return current
        
    except Exception as e:
        print(f"  [ERROR] Failed to analyze {ticker}: {e}")
        import traceback
        traceback.print_exc()
        return None


# ============================================================================
# BATCH ANALYSIS
# ============================================================================

def analyze_top_stocks(top_n=None):
    """
    Perform technical analysis on stocks by quality score.
    If top_n is None, analyze ALL stocks.
    """
    print("="*80)
    print("TECHNICAL ANALYSIS OF QUALITY STOCKS (v2 — 26 indicators)")
    print("="*80)
    
    if not SCORES_PATH.exists():
        print(f"[ERROR] Quality scores not found at {SCORES_PATH}")
        print("Please run absolute_scores.py first.")
        return None
    
    scores_df = pd.read_csv(SCORES_PATH)
    
    if top_n is not None and top_n < len(scores_df):
        top_stocks = scores_df.nlargest(top_n, 'quality_score')
        print(f"\nAnalyzing top {top_n} of {len(scores_df)} stocks by quality score...")
    else:
        top_stocks = scores_df.sort_values('quality_score', ascending=False)
        top_n = len(top_stocks)
        print(f"\nAnalyzing ALL {top_n} stocks...")
    print(f"Using 26 indicators (15 MAs + 11 Oscillators)\n")
    
    results = []
    
    for idx, row in top_stocks.iterrows():
        ticker = row['ticker']
        category = row.get('category', 'N/A')
        quality_score = row['quality_score']
        
        print(f"[{len(results)+1}/{top_n}] {ticker} ({category}) - Quality: {quality_score:.1f}")
        
        technical = get_technical_signals(ticker)
        
        if technical:
            technical['category'] = category
            technical['quality_score'] = quality_score
            technical['quality_percentile'] = row.get('quality_percentile', None)
            technical['region'] = row.get('region', 'global')
            
            # Summary line
            rating = technical['technical_rating']
            score = technical['technical_score']
            ma_b = technical['ma_buy']
            ma_s = technical['ma_sell']
            osc_b = technical['osc_buy']
            osc_s = technical['osc_sell']
            print(f"    → {rating} ({score:.0f}) | MAs: {ma_b}B/{ma_s}S | Osc: {osc_b}B/{osc_s}S")
            
            results.append(technical)
    
    if results:
        tech_df = pd.DataFrame(results)
        
        tech_df.to_csv(OUTPUT_PATH, index=False)
        
        print(f"\n{'='*80}")
        print("TECHNICAL ANALYSIS COMPLETE")
        print("="*80)
        print(f"Analyzed: {len(tech_df)} stocks")
        print(f"Data saved to: {OUTPUT_PATH}")
        
        print(f"\n{'='*80}")
        print("TECHNICAL RATINGS DISTRIBUTION")
        print("="*80)
        print(tech_df['technical_rating'].value_counts())
        
        print(f"\n{'='*80}")
        print("TOP 10 BY TECHNICAL SCORE")
        print("="*80)
        top_tech = tech_df.nlargest(10, 'technical_score')[
            ['ticker', 'category', 'technical_score', 'technical_rating', 'ma_buy', 'ma_sell', 'osc_buy', 'osc_sell', 'rsi', 'ma_trend']
        ]
        print(top_tech.to_string(index=False))
        
        # Stocks with both high quality AND good technicals
        print(f"\n{'='*80}")
        print("BEST COMBINED SCORES (Quality + Technical)")
        print("="*80)
        tech_df['combined_score'] = (tech_df['quality_score'] + tech_df['technical_score']) / 2
        best_combined = tech_df.nlargest(10, 'combined_score')[
            ['ticker', 'category', 'quality_score', 'technical_score', 'combined_score', 'technical_rating']
        ]
        print(best_combined.to_string(index=False))
        
        return tech_df
    else:
        print("\n[ERROR] No technical analysis results generated")
        return None


if __name__ == "__main__":
    df = analyze_top_stocks(top_n=20)
