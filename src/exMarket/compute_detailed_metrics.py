import pandas as pd
import numpy as np
from pathlib import Path

RAW_DIR = Path("data/fundamentals/raw")
UNIVERSE_PATH = Path("data/fundamentals_raw.csv")
OUTPUT_PATH = Path("data/fundamentals/company_metrics.csv")

MIN_YEARS = 3

# Key variations for different financial statement line items
CFO_KEYS = ["Total Cash From Operating Activities", "Cash Flow From Continuing Operating Activities", 
            "Net Cash Provided by Operating Activities", "Operating Cash Flow"]
REVENUE_KEYS = ["Total Revenue", "Revenue"]
OP_INCOME_KEYS = ["Operating Income", "Operating Income Or Loss"]
NET_INCOME_KEYS = ["Net Income", "Net Income Common Stockholders"]
EQUITY_KEYS = ["Total Equity Gross Minority Interest", "Stockholders Equity", 
               "Total Stockholder Equity", "Common Stock Equity"]
DEBT_KEYS = ["Total Debt", "Long Term Debt And Capital Lease Obligation", "Total Liabilities Net Minority Interest"]
CASH_KEYS = ["Cash And Cash Equivalents", "Cash Cash Equivalents And Short Term Investments"]
EBITDA_KEYS = ["EBITDA", "Normalized EBITDA"]
INTEREST_KEYS = ["Interest Expense", "Interest Expense Non Operating"]
CAPEX_KEYS = ["Capital Expenditures", "Capital Expenditure"]

def get_row(df, names):
    """Try to find a row in dataframe using multiple possible names."""
    for n in names:
        if n in df.index:
            return df.loc[n]
    return None

def load_statements(ticker):
    """Load financial statements for a ticker."""
    # Sanitize ticker for filename (same as download_detailed_fundamentals)
    safe_ticker = ticker.replace('.', '_')
    try:
        income = pd.read_csv(RAW_DIR / f"{safe_ticker}_income.csv", index_col=0)
        balance = pd.read_csv(RAW_DIR / f"{safe_ticker}_balance.csv", index_col=0)
        cashflow = pd.read_csv(RAW_DIR / f"{safe_ticker}_cashflow.csv", index_col=0)
        return income, balance, cashflow
    except FileNotFoundError as e:
        print(f"  [WARN] Missing file for {ticker} (looked for {safe_ticker}_*.csv): {e}")
        return None, None, None

def compute_metrics(ticker, category=None, region=None, tax_rate=0.25):
    """Compute fundamental quality metrics for a company."""
    try:
        income, balance, cashflow = load_statements(ticker)
        
        if income is None or balance is None or cashflow is None:
            return None
        
        # Ensure chronological order (oldest to newest)
        income = income.iloc[:, ::-1]
        balance = balance.iloc[:, ::-1]
        cashflow = cashflow.iloc[:, ::-1]
        
        # Check available years
        years_available = min(income.shape[1], balance.shape[1], cashflow.shape[1])
        
        if years_available < MIN_YEARS:
            print(f"  [WARN] {ticker}: Only {years_available} years of data available (need {MIN_YEARS})")
            return None
        
        years_to_use = min(years_available, 4)
        print(f"  Using {years_to_use} years of data")
        
        # Extract metrics
        revenue = get_row(income, REVENUE_KEYS)
        op_income = get_row(income, OP_INCOME_KEYS)
        net_income = get_row(income, NET_INCOME_KEYS)
        equity = get_row(balance, EQUITY_KEYS)
        debt = get_row(balance, DEBT_KEYS)
        cash = get_row(balance, CASH_KEYS)
        cfo = get_row(cashflow, CFO_KEYS)
        capex = get_row(cashflow, CAPEX_KEYS)
        ebitda = get_row(income, EBITDA_KEYS)
        interest = get_row(income, INTEREST_KEYS)
        
        # Check for missing critical data
        if any(x is None for x in [revenue, op_income, net_income, equity, cfo, capex]):
            print(f"  [WARN] {ticker}: Missing critical financial data")
            return None
        
        # Get last N years
        revenue = revenue.iloc[-years_to_use:]
        op_income = op_income.iloc[-years_to_use:]
        net_income = net_income.iloc[-years_to_use:]
        equity = equity.iloc[-years_to_use:]
        cfo = cfo.iloc[-years_to_use:]
        capex = capex.iloc[-years_to_use:]
        
        # Optional metrics
        debt = debt.iloc[-years_to_use:] if debt is not None else pd.Series([0]*years_to_use)
        cash = cash.iloc[-years_to_use:] if cash is not None else pd.Series([0]*years_to_use)
        ebitda = ebitda.iloc[-years_to_use:] if ebitda is not None else op_income
        interest = interest.iloc[-years_to_use:] if interest is not None else pd.Series([1]*years_to_use)
        
        # PROFITABILITY
        nopat = op_income * (1 - tax_rate)
        invested_capital = equity + debt - cash
        invested_capital = invested_capital.replace(0, np.nan)
        roic = nopat / invested_capital
        roic_avg = roic.mean()
        
        op_margin = op_income / revenue
        op_margin_trend = np.polyfit(range(years_to_use), op_margin, 1)[0]
        
        # CASH FLOW
        fcf = cfo - capex.abs()
        fcf_margin = (fcf / revenue).mean()
        cfo_to_ni = (cfo / net_income).mean()
        
        # BALANCE SHEET
        net_debt = debt - cash
        net_debt_ebitda = (net_debt / ebitda).mean()
        interest_coverage = (op_income / interest.abs()).replace([np.inf, -np.inf], np.nan).mean()
        
        # DURABILITY
        revenue_cagr = (revenue.iloc[-1] / revenue.iloc[0]) ** (1/(years_to_use-1)) - 1
        margin_volatility = op_margin.std()
        
        return {
            "ticker": ticker,
            "category": category,
            "region": region or "global",
            "years_used": years_to_use,
            "roic_avg": roic_avg,
            "op_margin_trend": op_margin_trend,
            "fcf_margin": fcf_margin,
            "cfo_to_ni": cfo_to_ni,
            "net_debt_ebitda": net_debt_ebitda,
            "interest_coverage": interest_coverage,
            "revenue_cagr": revenue_cagr,
            "margin_volatility": margin_volatility
        }
        
    except Exception as e:
        print(f"  [ERROR] {ticker}: {e}")
        return None

def main():
    """Process all companies in the universe and compute quality metrics."""
    
    print("="*80)
    print("COMPUTING COMPANY QUALITY METRICS")
    print(f"(Using {MIN_YEARS}-4 years of data)")
    print("="*80)
    
    if not UNIVERSE_PATH.exists():
        print(f"[ERROR] Universe file not found at {UNIVERSE_PATH}")
        return
    
    universe_df = pd.read_csv(UNIVERSE_PATH)
    print(f"\nProcessing {len(universe_df)} companies...")
    
    rows = []
    success_count = 0
    fail_count = 0
    
    for idx, row in universe_df.iterrows():
        ticker = row['ticker']
        category = row.get('category', None)
        region = row.get('region', 'global')
        
        print(f"\n[{idx+1}/{len(universe_df)}] Computing metrics for {ticker} ({category})...")
        
        metrics = compute_metrics(ticker, category, region=region)
        
        if metrics:
            rows.append(metrics)
            success_count += 1
            print(f"  ✓ Success")
        else:
            fail_count += 1
            print(f"  ✗ Failed")
    
    if rows:
        df = pd.DataFrame(rows)
        
        OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(OUTPUT_PATH, index=False)
        
        print("\n" + "="*80)
        print("METRICS SUMMARY")
        print("="*80)
        print(f"\nTotal processed: {len(universe_df)}")
        print(f"Successful: {success_count}")
        print(f"Failed: {fail_count}")
        print(f"\nMetrics saved to: {OUTPUT_PATH}")
        
        print("\n" + "="*80)
        print("YEARS OF DATA USED")
        print("="*80)
        print(df['years_used'].value_counts().sort_index())
        
        print("\n" + "="*80)
        print("TOP 10 COMPANIES BY AVERAGE ROIC")
        print("="*80)
        top_roic = df.nlargest(10, 'roic_avg')[['ticker', 'category', 'years_used', 'roic_avg', 'fcf_margin', 'revenue_cagr']]
        print(top_roic.to_string(index=False))
        
        if 'category' in df.columns:
            print("\n" + "="*80)
            print("AVERAGE ROIC BY CATEGORY")
            print("="*80)
            category_stats = df.groupby('category').agg({
                'roic_avg': 'mean',
                'fcf_margin': 'mean',
                'revenue_cagr': 'mean',
                'years_used': 'mean'
            }).round(4)
            print(category_stats)
        
        return df
    else:
        print("\n[ERROR] No metrics computed successfully!")
        return None

if __name__ == "__main__":
    df = main()
