import matplotlib.pyplot as plt
import pandas as pd
import os
import numpy as np

def plot_price_and_regime(df, title=None, output_path=None):
    """
    Plot price and regime for a single asset.
    Works with both single-asset and extracted asset dataframes.
    """
    if output_path is None:
        output_path = "data/market_regime.png"
    
    if title is None:
        title = "Market Price with Regime Overlay"
    
    fig, ax = plt.subplots(figsize=(12, 6))
    ax.plot(df.index, df["Close"], label="Close Price", linewidth=1, color="black")
    
    risk_on = df[df["Regime"] == "Risk-On"]
    risk_off = df[df["Regime"] == "Risk-Off"]
    neutral = df[df["Regime"] == "Neutral"]
    
    ax.scatter(risk_on.index, risk_on["Close"], color="green", s=10, label="Risk-On", alpha=0.6)
    ax.scatter(risk_off.index, risk_off["Close"], color="red", s=10, label="Risk-Off", alpha=0.6)
    ax.scatter(neutral.index, neutral["Close"], color="gray", s=5, label="Neutral", alpha=0.3)
    
    ax.set_title(title, fontsize=14, fontweight="bold")
    ax.set_ylabel("Price", fontsize=12)
    ax.set_xlabel("Date", fontsize=12)
    ax.legend(loc="best")
    ax.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig(output_path, dpi=150)
    plt.close(fig)
    print(f"Plot saved to {output_path}")

def plot_all_assets(df, output_dir="data/plots"):
    """
    Create individual plots for each asset in the multi-asset dataframe.
    """
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    # Get list of assets
    assets = [col.replace("_Close", "") for col in df.columns if col.endswith("_Close")]
    
    for asset in assets:
        close_col = f"{asset}_Close"
        regime_col = f"{asset}_Regime"
        
        if close_col not in df.columns or regime_col not in df.columns:
            print(f"Skipping {asset}: missing required columns")
            continue
        
        # Create asset-specific dataframe
        asset_df = df[[close_col, regime_col]].copy()
        asset_df.columns = ["Close", "Regime"]
        asset_df = asset_df.dropna()
        
        # Generate plot
        output_path = os.path.join(output_dir, f"{asset.lower()}_regime.png")
        plot_price_and_regime(
            asset_df,
            title=f"{asset} Price with Market Regime Overlay",
            output_path=output_path
        )

def plot_regime_comparison(df, output_path="data/regime_comparison.png"):
    """
    Create a multi-panel plot comparing all assets' regimes side by side.
    """
    assets = [col.replace("_Close", "") for col in df.columns if col.endswith("_Close")]
    n_assets = len(assets)
    
    if n_assets == 0:
        print("No assets found in dataframe")
        return
    
    fig, axes = plt.subplots(n_assets, 1, figsize=(14, 4 * n_assets), sharex=True)
    
    if n_assets == 1:
        axes = [axes]
    
    for idx, asset in enumerate(assets):
        close_col = f"{asset}_Close"
        regime_col = f"{asset}_Regime"
        
        if close_col not in df.columns or regime_col not in df.columns:
            continue
        
        ax = axes[idx]
        asset_df = df[[close_col, regime_col]].dropna()
        
        # Plot price line
        ax.plot(asset_df.index, asset_df[close_col], 
                label="Close Price", linewidth=1.5, color="black")
        
        # Overlay regime points
        risk_on = asset_df[asset_df[regime_col] == "Risk-On"]
        risk_off = asset_df[asset_df[regime_col] == "Risk-Off"]
        neutral = asset_df[asset_df[regime_col] == "Neutral"]
        
        ax.scatter(risk_on.index, risk_on[close_col], 
                  color="green", s=8, label="Risk-On", alpha=0.6)
        ax.scatter(risk_off.index, risk_off[close_col], 
                  color="red", s=8, label="Risk-Off", alpha=0.6)
        ax.scatter(neutral.index, neutral[close_col], 
                  color="gray", s=4, label="Neutral", alpha=0.3)
        
        ax.set_title(f"{asset}", fontsize=12, fontweight="bold")
        ax.set_ylabel("Price", fontsize=10)
        ax.legend(loc="best", fontsize=9)
        ax.grid(True, alpha=0.3)
    
    axes[-1].set_xlabel("Date", fontsize=12)
    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"Comparison plot saved to {output_path}")

def plot_regime_heatmap(df, output_path="data/regime_heatmap.png"):
    """
    Create a heatmap showing regime states across all assets over time.
    """
    assets = [col.replace("_Close", "") for col in df.columns if col.endswith("_Close")]
    
    # Create regime matrix (1 = Risk-On, 0 = Neutral, -1 = Risk-Off)
    regime_matrix = []
    labels = []
    
    for asset in assets:
        regime_col = f"{asset}_Regime"
        if regime_col in df.columns:
            regime_numeric = df[regime_col].map({
                "Risk-On": 1,
                "Neutral": 0,
                "Risk-Off": -1
            })
            regime_matrix.append(regime_numeric)
            labels.append(asset)
    
    if not regime_matrix:
        print("No regime data found for heatmap")
        return
    
    regime_df = pd.DataFrame(regime_matrix, index=labels).T
    
    # Sample data for visualization (every 5th day to avoid overcrowding)
    regime_df_sampled = regime_df.iloc[::5]
    
    fig, ax = plt.subplots(figsize=(16, 6))
    
    # Create heatmap
    im = ax.imshow(regime_df_sampled.T, aspect='auto', cmap='RdYlGn', 
                   vmin=-1, vmax=1, interpolation='nearest')
    
    ax.set_yticks(range(len(labels)))
    ax.set_yticklabels(labels)
    ax.set_xlabel("Date (sampled)", fontsize=12)
    ax.set_title("Market Regime Heatmap Across Assets", fontsize=14, fontweight="bold")
    
    # Add colorbar
    cbar = plt.colorbar(im, ax=ax)
    cbar.set_label("Regime", fontsize=12)
    cbar.set_ticks([-1, 0, 1])
    cbar.set_ticklabels(["Risk-Off", "Neutral", "Risk-On"])
    
    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"Heatmap saved to {output_path}")

if __name__ == "__main__":
    # Test the visualization functions
    df = pd.read_csv("data/market_data_with_regimes.csv", index_col=0, parse_dates=True)
    
    print("Creating individual asset plots...")
    plot_all_assets(df)
    
    print("\nCreating comparison plot...")
    plot_regime_comparison(df)
    
    print("\nCreating regime heatmap...")
    plot_regime_heatmap(df)
    
    print("\nAll visualizations complete!")
