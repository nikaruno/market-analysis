import pandas as pd
from market_regime import compute_regime
from visualize import (
    plot_price_and_regime,
    plot_all_assets,
    plot_regime_comparison,
    plot_regime_heatmap
)

DATA_PATH = "data/market_data.csv"

def main():
    # Load the multi-asset data
    df = pd.read_csv(
        DATA_PATH,
        index_col=0,
        parse_dates=True,
        date_format="%Y-%m-%d"
    )
    
    print("Loaded data shape:", df.shape)
    print("Assets:", [col.replace("_Close", "") for col in df.columns if col.endswith("_Close")])
    
    # Compute regimes for all assets
    print("\n" + "="*80)
    print("COMPUTING MARKET REGIMES...")
    print("="*80)
    df = compute_regime(df)
    
    # Display latest regime information for each asset
    print("\n" + "="*80)
    print("LATEST REGIME DATA (Last 10 days)")
    print("="*80)
    
    assets = ["SP500", "NASDAQ", "Gold", "Bitcoin"]
    
    for asset in assets:
        regime_col = f"{asset}_Regime"
        score_col = f"{asset}_RegimeScore"
        close_col = f"{asset}_Close"
        
        if regime_col in df.columns:
            print(f"\n{asset}:")
            print(df[[close_col, score_col, regime_col]].tail(10))
    
    # Display overall market regime
    if "Market_Regime" in df.columns:
        print("\n" + "="*80)
        print("OVERALL MARKET REGIME:")
        print("="*80)
        print(df[["Market_RegimeScore", "Market_Regime"]].tail(10))
    
    # Regime distribution summary
    print("\n" + "="*80)
    print("REGIME DISTRIBUTION (Full History)")
    print("="*80)
    for asset in assets:
        regime_col = f"{asset}_Regime"
        if regime_col in df.columns:
            print(f"\n{asset}:")
            print(df[regime_col].value_counts())
    
    if "Market_Regime" in df.columns:
        print("\nOverall Market:")
        print(df["Market_Regime"].value_counts())
    
    # Save processed data
    output_path = DATA_PATH.replace(".csv", "_with_regimes.csv")
    df.to_csv(output_path, index=True)
    print(f"\n" + "="*80)
    print(f"Processed data saved to: {output_path}")
    print("="*80)
    
    # Generate all visualizations
    print("\n" + "="*80)
    print("GENERATING VISUALIZATIONS...")
    print("="*80)
    
    # 1. Individual asset plots
    print("\n1. Creating individual asset plots...")
    plot_all_assets(df, output_dir="data/plots")
    
    # 2. Multi-panel comparison plot
    print("\n2. Creating multi-asset comparison plot...")
    plot_regime_comparison(df, output_path="data/regime_comparison.png")
    
    # 3. Regime heatmap
    print("\n3. Creating regime heatmap...")
    plot_regime_heatmap(df, output_path="data/regime_heatmap.png")
    
    # 4. Optional: Create a single combined plot for quick viewing
    print("\n4. Creating legacy format plot (SP500 only)...")
    if "SP500_Close" in df.columns and "SP500_Regime" in df.columns:
        sp500_df = df[["SP500_Close", "SP500_Regime"]].copy()
        sp500_df.columns = ["Close", "Regime"]
        sp500_df["RegimeScore"] = df["SP500_RegimeScore"]
        plot_price_and_regime(
            sp500_df, 
            title="S&P 500 Price with Market Regime Overlay",
            output_path="data/market_regime.png"
        )
    
    print("\n" + "="*80)
    print("ALL VISUALIZATIONS COMPLETED!")
    print("="*80)
    print("\nGenerated files:")
    print("  - data/plots/sp500_regime.png")
    print("  - data/plots/nasdaq_regime.png")
    print("  - data/plots/gold_regime.png")
    print("  - data/plots/bitcoin_regime.png")
    print("  - data/regime_comparison.png")
    print("  - data/regime_heatmap.png")
    print("  - data/market_regime.png (SP500 legacy)")
    print("="*80)

if __name__ == "__main__":
    main()
