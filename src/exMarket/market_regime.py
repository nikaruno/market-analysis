import numpy as np
import pandas as pd

def compute_regime_single_asset(close_series):
    """Compute regime for a single asset's close prices."""
    df = pd.DataFrame({"Close": close_series})
    df["Close"] = pd.to_numeric(df["Close"], errors="coerce")
    df.dropna(subset=["Close"], inplace=True)
    
    # Trend: 200-day MA
    df["MA200"] = df["Close"].rolling(200).mean()
    df["TrendSignal"] = np.where(df["Close"] > df["MA200"], 1, -1)
    
    # Momentum: 12-month ROC
    df["ROC_12M"] = df["Close"] / df["Close"].shift(252) - 1
    df["MomentumSignal"] = 0
    df.loc[df["ROC_12M"] > 0, "MomentumSignal"] = 1
    df.loc[df["ROC_12M"] < -0.05, "MomentumSignal"] = -1
    
    # Volatility: 20-day vs 3-year average
    log_returns = np.log(df["Close"] / df["Close"].shift(1))
    df["Vol20"] = log_returns.rolling(20).std() * np.sqrt(252)
    vol_long = df["Vol20"].rolling(756).mean()
    df["VolatilitySignal"] = np.where(df["Vol20"] > 1.25 * vol_long, -1, 0)
    
    # Regime score
    df["RegimeScore"] = (
        0.5 * df["TrendSignal"]
        + 0.3 * df["MomentumSignal"]
        + 0.2 * df["VolatilitySignal"]
    )
    
    # Regime classification
    df["Regime"] = "Neutral"
    df.loc[df["RegimeScore"] >= 0.5, "Regime"] = "Risk-On"
    df.loc[df["RegimeScore"] <= -0.5, "Regime"] = "Risk-Off"
    
    return df

def compute_regime(df):
    """Compute regime for all assets in the multi-asset dataframe."""
    result_df = df.copy()
    
    # Get list of assets from column names
    assets = [col.replace("_Close", "") for col in df.columns if col.endswith("_Close")]
    
    # Compute regime for each asset
    for asset in assets:
        close_col = f"{asset}_Close"
        
        if close_col not in df.columns:
            continue
            
        # Compute regime for this asset
        regime_df = compute_regime_single_asset(df[close_col])
        
        # Add columns with asset prefix
        result_df[f"{asset}_MA200"] = regime_df["MA200"]
        result_df[f"{asset}_TrendSignal"] = regime_df["TrendSignal"]
        result_df[f"{asset}_ROC_12M"] = regime_df["ROC_12M"]
        result_df[f"{asset}_MomentumSignal"] = regime_df["MomentumSignal"]
        result_df[f"{asset}_Vol20"] = regime_df["Vol20"]
        result_df[f"{asset}_VolatilitySignal"] = regime_df["VolatilitySignal"]
        result_df[f"{asset}_RegimeScore"] = regime_df["RegimeScore"]
        result_df[f"{asset}_Regime"] = regime_df["Regime"]
    
    # Compute overall market regime (average of SP500 and NASDAQ)
    if "SP500_RegimeScore" in result_df.columns and "NASDAQ_RegimeScore" in result_df.columns:
        result_df["Market_RegimeScore"] = (
            result_df["SP500_RegimeScore"] + result_df["NASDAQ_RegimeScore"]
        ) / 2
        
        result_df["Market_Regime"] = "Neutral"
        result_df.loc[result_df["Market_RegimeScore"] >= 0.5, "Market_Regime"] = "Risk-On"
        result_df.loc[result_df["Market_RegimeScore"] <= -0.5, "Market_Regime"] = "Risk-Off"
    
    return result_df

if __name__ == "__main__":
    # Load the market data
    df = pd.read_csv("data/market_data.csv", index_col=0, parse_dates=True)
    
    # Compute regimes
    df_with_regimes = compute_regime(df)
    
    # Save to CSV
    df_with_regimes.to_csv("data/market_data_with_regimes.csv", index=True)
    
    # Display summary
    print("Regime analysis completed!")
    print("\nColumns added for each asset:")
    print("- MA200, TrendSignal, ROC_12M, MomentumSignal")
    print("- Vol20, VolatilitySignal, RegimeScore, Regime")
    print("\nOverall Market Regime (SP500 + NASDAQ average)")
    print(df_with_regimes["Market_Regime"].value_counts())
    print("\nLatest regimes:")
    regime_cols = [col for col in df_with_regimes.columns if col.endswith("_Regime")]
    print(df_with_regimes[regime_cols].tail())
