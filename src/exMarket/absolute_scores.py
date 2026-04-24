import pandas as pd
import numpy as np
from pathlib import Path
import json

METRICS_PATH = Path("data/fundamentals/company_metrics.csv")
OUTPUT_PATH = Path("data/fundamentals/absolute_scores.csv")
CONFIG_FILE = Path("config.json")

def load_weights():
    """Load weights from config file or use defaults.
    
    New format (v2): individual weight per metric.
    Old format: 'other' key is split into margin_trend, interest_coverage, margin_volatility.
    """
    defaults = {
        'roic': 0.20,
        'fcf': 0.15,
        'cash_quality': 0.10,
        'leverage': 0.10,
        'growth': 0.15,
        'margin_trend': 0.10,
        'interest_coverage': 0.10,
        'margin_volatility': 0.10,
    }
    
    if CONFIG_FILE.exists():
        with open(CONFIG_FILE, 'r') as f:
            config = json.load(f)
            w = config.get('weights', {})
            
            # Backward compat: if old 'other' key exists, split it
            if 'other' in w and 'margin_trend' not in w:
                other = w.pop('other', 0.15)
                w['margin_trend'] = round(other * 0.40, 2)
                w['interest_coverage'] = round(other * 0.30, 2)
                w['margin_volatility'] = round(other * 0.30, 2)
            
            # Merge with defaults for any missing keys
            for k, v in defaults.items():
                if k not in w:
                    w[k] = v
            
            return w
    
    return defaults

def normalize_metric(series, reverse=False):
    """Normalize metric to 0-100 scale using percentile rank."""
    series_clean = series.replace([np.inf, -np.inf], np.nan)
    
    if reverse:
        scores = (1 - series_clean.rank(pct=True, na_option='keep')) * 100
    else:
        scores = series_clean.rank(pct=True, na_option='keep') * 100
    
    return scores

def cap_outliers(series, lower_percentile=5, upper_percentile=95):
    """Cap extreme outliers to reduce their impact."""
    lower_bound = series.quantile(lower_percentile / 100)
    upper_bound = series.quantile(upper_percentile / 100)
    return series.clip(lower=lower_bound, upper=upper_bound)

def compute_absolute_scores(df):
    """Compute absolute quality scores comparing all companies together."""
    df = df.copy()
    
    # Load weights from config
    weights = load_weights()
    print(f"\nUsing weights from config: {weights}")
    
    # Verify weights sum to ~1.0
    weight_sum = sum(weights.values())
    if abs(weight_sum - 1.0) > 0.01:
        print(f"  [WARN] Weights sum to {weight_sum:.3f}, normalizing to 1.0")
        weights = {k: v / weight_sum for k, v in weights.items()}
    
    print("\nComputing absolute quality scores (all companies together)...")
    
    # Cap extreme outliers
    metrics_to_cap = ['roic_avg', 'fcf_margin', 'cfo_to_ni', 'revenue_cagr', 
                      'net_debt_ebitda', 'interest_coverage', 'margin_volatility']
    
    for metric in metrics_to_cap:
        if metric in df.columns:
            df[f'{metric}_capped'] = cap_outliers(df[metric])
    
    # Define all metrics with their weight keys and direction
    # Positive: higher raw value = better quality
    # Negative (reverse=True): lower raw value = better quality
    all_metrics = [
        ('roic_avg_capped',           'roic',               False, 'ROIC'),
        ('fcf_margin_capped',         'fcf',                False, 'FCF Margin'),
        ('cfo_to_ni_capped',          'cash_quality',       False, 'Cash Quality'),
        ('revenue_cagr_capped',       'growth',             False, 'Growth'),
        ('op_margin_trend',           'margin_trend',       False, 'Margin Trend'),
        ('interest_coverage_capped',  'interest_coverage',  False, 'Interest Coverage'),
        ('net_debt_ebitda_capped',    'leverage',           True,  'Leverage'),
        ('margin_volatility_capped',  'margin_volatility',  True,  'Margin Volatility'),
    ]
    
    # Normalize each metric to 0-100 percentile scale
    score_columns = []
    for col, weight_key, reverse, label in all_metrics:
        w = weights.get(weight_key, 0)
        if col in df.columns and w > 0:
            normalized = normalize_metric(df[col], reverse=reverse)
            score_col = f'{col}_score'
            df[score_col] = normalized
            score_columns.append((score_col, weight_key))
            direction = " (inverse)" if reverse else ""
            print(f"  {label:25s} {w:5.0%} weight{direction}")
        elif w > 0:
            print(f"  {label:25s} {w:5.0%} weight — COLUMN MISSING: {col}")
    
    # Compute quality score with per-row weight redistribution for NaN values.
    # If a company is missing metric X (NaN), redistribute X's weight
    # proportionally across the metrics that ARE available for that company.
    # This ensures all companies get a fair score on a 0-100 scale.
    
    def compute_row_score(row):
        available_weight = 0.0
        weighted_sum = 0.0
        for score_col, weight_key in score_columns:
            w = weights.get(weight_key, 0)
            val = row.get(score_col, np.nan)
            if pd.notna(val) and w > 0:
                available_weight += w
                weighted_sum += val * w
        if available_weight > 0:
            # Scale up to compensate for missing weights
            return weighted_sum / available_weight * sum(weights[wk] for _, wk in score_columns)
        return np.nan
    
    df['quality_score'] = df.apply(compute_row_score, axis=1)
    
    # Track data completeness
    n_metrics = len(score_columns)
    df['metrics_available'] = df[[sc for sc, _ in score_columns]].notna().sum(axis=1)
    df['data_completeness'] = (df['metrics_available'] / n_metrics * 100).round(0)
    
    n_complete = (df['metrics_available'] == n_metrics).sum()
    n_partial = ((df['metrics_available'] < n_metrics) & (df['metrics_available'] > 0)).sum()
    n_empty = (df['metrics_available'] == 0).sum()
    print(f"\n  Data completeness: {n_complete} complete, {n_partial} partial, {n_empty} empty")
    
    # Compute GLOBAL percentile (across all companies)
    df['quality_percentile'] = df['quality_score'].rank(pct=True) * 100
    
    # Compute REGIONAL percentile (within each region separately)
    if 'region' in df.columns:
        df['quality_percentile_regional'] = (
            df.groupby('region')['quality_score']
              .rank(pct=True) * 100
        )
        print(f"\n  Regional percentiles computed for regions: {df['region'].unique().tolist()}")
    else:
        df['quality_percentile_regional'] = df['quality_percentile']
    
    # Assign tiers based on REGIONAL percentile (so BIST stocks are ranked among themselves)
    def assign_tier(percentile):
        if pd.isna(percentile):
            return 'Unknown'
        if percentile >= 75:
            return 'Top 25%'
        elif percentile >= 50:
            return 'Top 50%'
        elif percentile >= 25:
            return 'Bottom 50%'
        else:
            return 'Bottom 25%'
    
    df['quality_tier'] = df['quality_percentile_regional'].apply(assign_tier)
    
    return df

def main():
    """Main function to run scoring process"""
    print("Computing absolute quality scores...")
    
    if not METRICS_PATH.exists():
        print(f"Error: {METRICS_PATH} not found")
        return False
    
    # Load metrics
    df = pd.read_csv(METRICS_PATH, index_col=0)
    print(f"Loaded {len(df)} rows")
    
    # Deduplicate tickers that appear in multiple sectors.
    # Keep the row with the most non-NaN metric values; on tie, keep first.
    metric_cols = ['roic_avg', 'fcf_margin', 'cfo_to_ni', 'net_debt_ebitda',
                   'revenue_cagr', 'op_margin_trend', 'interest_coverage', 'margin_volatility']
    existing_cols = [c for c in metric_cols if c in df.columns]
    df['_n_valid'] = df[existing_cols].notna().sum(axis=1)
    
    before = len(df)
    # Sort so the row with most data comes first, then drop duplicates by ticker (index)
    df = df.sort_values('_n_valid', ascending=False)
    df = df[~df.index.duplicated(keep='first')]
    df = df.drop(columns=['_n_valid'])
    after = len(df)
    
    if before > after:
        print(f"Deduplicated: {before} → {after} unique tickers ({before - after} duplicates removed)")
    
    # Show region breakdown if available
    if 'region' in df.columns:
        print(f"Regions: {df['region'].value_counts().to_dict()}")
    
    # Compute scores
    df_scored = compute_absolute_scores(df)
    
    # Save results
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    df_scored.to_csv(OUTPUT_PATH)
    
    print(f"\nResults saved to {OUTPUT_PATH}")
    
    # Reset index to get ticker as a column for display
    df_display = df_scored.reset_index()
    
    # Show results by region
    if 'region' in df_display.columns:
        regions = df_display['region'].unique()
        for region in regions:
            region_df = df_display[df_display['region'] == region]
            print(f"\n{'='*60}")
            print(f"Top companies in region: {region.upper()} ({len(region_df)} companies)")
            print(f"{'='*60}")
            
            if 'ticker' in region_df.columns:
                top = region_df.nlargest(min(10, len(region_df)), 'quality_score')[
                    ['ticker', 'quality_score', 'quality_percentile_regional', 'quality_tier']
                ]
            else:
                top = region_df.nlargest(min(10, len(region_df)), 'quality_score')[
                    ['quality_score', 'quality_percentile_regional', 'quality_tier']
                ]
            print(top.to_string())
    else:
        print(f"\nTop 10 companies by quality score:")
        if 'ticker' in df_display.columns:
            top_10 = df_display.nlargest(10, 'quality_score')[['ticker', 'quality_score', 'quality_percentile', 'quality_tier']]
        else:
            top_10 = df_scored.nlargest(10, 'quality_score')[['quality_score', 'quality_percentile', 'quality_tier']]
        print(top_10.to_string())
    
    return True

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
