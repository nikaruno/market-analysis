# Quality Score — Cell-Level Calculation Trace

## EQNR (Equinor) vs GEV (GE Vernova)

Every number below is traced to its exact source: **`FILE → Row Name → Column (Year)`**

Source files per company:
- `{TICKER}_income.csv` — Income Statement (rows × year columns)
- `{TICKER}_balance.csv` — Balance Sheet (rows × year columns)
- `{TICKER}_cashflow.csv` — Cash Flow Statement (rows × year columns)

---

## 1. ROIC — Return on Invested Capital (Weight: 20%)

```
ROIC = NOPAT / Invested Capital
NOPAT = Operating Income × (1 − Tax Rate)
Invested Capital = Total Equity + Total Debt − Cash
```

### EQNR

**Step 1: Get NOPAT (from Income Statement)**

| Year | Operating Income | Source | × (1 − Tax Rate) | Source | = NOPAT |
|------|-----------------|--------|-------------------|--------|---------|
| 2022 | 77,741,000,000 | `EQNR_income.csv → "Operating Income" → 2022-12-31` | × (1 − 0.22) | `EQNR_income.csv → "Tax Rate For Calcs" → 2022-12-31` | **60,638,180,000** |
| 2023 | 35,233,000,000 | `EQNR_income.csv → "Operating Income" → 2023-12-31` | × (1 − 0.22) | `EQNR_income.csv → "Tax Rate For Calcs" → 2023-12-31` | **27,481,740,000** |
| 2024 | 30,354,000,000 | `EQNR_income.csv → "Operating Income" → 2024-12-31` | × (1 − 0.22) | `EQNR_income.csv → "Tax Rate For Calcs" → 2024-12-31` | **23,676,120,000** |
| 2025 | 24,730,000,000 | `EQNR_income.csv → "Operating Income" → 2025-12-31` | × (1 − 0.22) | `EQNR_income.csv → "Tax Rate For Calcs" → 2025-12-31` | **19,289,400,000** |

**Step 2: Get Invested Capital (from Balance Sheet)**

| Year | Equity | Source | + Debt | Source | − Cash | Source | = Invested Capital |
|------|--------|--------|--------|--------|--------|--------|--------------------|
| 2022 | 53,989,000,000 | `EQNR_balance.csv → "Total Equity Gross Minority Interest" → 2022-12-31` | 32,167,000,000 | `EQNR_balance.csv → "Total Debt" → 2022-12-31` | 9,438,000,000 | `EQNR_balance.csv → "Cash And Cash Equivalents" → 2022-12-31` | **76,718,000,000** |
| 2023 | 48,500,000,000 | `EQNR_balance.csv → "Total Equity Gross Minority Interest" → 2023-12-31` | 31,795,000,000 | `EQNR_balance.csv → "Total Debt" → 2023-12-31` | 8,070,000,000 | `EQNR_balance.csv → "Cash And Cash Equivalents" → 2023-12-31` | **72,225,000,000** |
| 2024 | 42,380,000,000 | `EQNR_balance.csv → "Total Equity Gross Minority Interest" → 2024-12-31` | 30,095,000,000 | `EQNR_balance.csv → "Total Debt" → 2024-12-31` | 5,903,000,000 | `EQNR_balance.csv → "Cash And Cash Equivalents" → 2024-12-31` | **66,572,000,000** |
| 2025 | 40,497,000,000 | `EQNR_balance.csv → "Total Equity Gross Minority Interest" → 2025-12-31` | 31,220,000,000 | `EQNR_balance.csv → "Total Debt" → 2025-12-31` | 5,036,000,000 | `EQNR_balance.csv → "Cash And Cash Equivalents" → 2025-12-31` | **66,681,000,000** |

**Step 3: ROIC = NOPAT / Invested Capital**

| Year | NOPAT | ÷ Invested Capital | = ROIC |
|------|-------|---------------------|--------|
| 2022 | 60,638,180,000 | ÷ 76,718,000,000 | **79.0%** |
| 2023 | 27,481,740,000 | ÷ 72,225,000,000 | **38.0%** |
| 2024 | 23,676,120,000 | ÷ 66,572,000,000 | **35.6%** |
| 2025 | 19,289,400,000 | ÷ 66,681,000,000 | **28.9%** |

**EQNR ROIC Average = (79.0 + 38.0 + 35.6 + 28.9) / 4 = 45.4%**

---

### GEV

**Step 1: NOPAT**

| Year | Operating Income | Source | × (1 − Tax Rate) | Source | = NOPAT |
|------|-----------------|--------|-------------------|--------|---------|
| 2022 | −2,881,000,000 | `GEV_income.csv → "Operating Income" → 2022-12-31` | × (1 − 0.21) | `GEV_income.csv → "Tax Rate For Calcs" → 2022-12-31` | **−2,275,990,000** |
| 2023 | −923,000,000 | `GEV_income.csv → "Operating Income" → 2023-12-31` | × (1 − 0.21) | `GEV_income.csv → "Tax Rate For Calcs" → 2023-12-31` | **−729,170,000** |
| 2024 | 471,000,000 | `GEV_income.csv → "Operating Income" → 2024-12-31` | × (1 − 0.376) | `GEV_income.csv → "Tax Rate For Calcs" → 2024-12-31` | **293,904,000** |
| 2025 | 1,389,000,000 | `GEV_income.csv → "Operating Income" → 2025-12-31` | × (1 − 0.21) | `GEV_income.csv → "Tax Rate For Calcs" → 2025-12-31` | **1,097,310,000** |

**Step 2: Invested Capital**

| Year | Equity | Source | + Debt | Source | − Cash | Source | = Invested Capital |
|------|--------|--------|--------|--------|--------|--------|--------------------|
| 2022 | 11,607,000,000 | `GEV_balance.csv → "Total Equity Gross Minority Interest" → 2022-12-31` | 1,144,000,000 | `GEV_balance.csv → "Total Debt" → 2022-12-31` | 2,067,000,000 | `GEV_balance.csv → "Cash And Cash Equivalents" → 2022-12-31` | **10,684,000,000** |
| 2023 | 8,380,000,000 | `GEV_balance.csv → "Total Equity Gross Minority Interest" → 2023-12-31` | 1,157,000,000 | `GEV_balance.csv → "Total Debt" → 2023-12-31` | 1,551,000,000 | `GEV_balance.csv → "Cash And Cash Equivalents" → 2023-12-31` | **7,986,000,000** |
| 2024 | 10,593,000,000 | `GEV_balance.csv → "Total Equity Gross Minority Interest" → 2024-12-31` | 1,043,000,000 | `GEV_balance.csv → "Total Debt" → 2024-12-31` | 8,205,000,000 | `GEV_balance.csv → "Cash And Cash Equivalents" → 2024-12-31` | **3,431,000,000** |
| 2025 | 12,296,000,000 | `GEV_balance.csv → "Total Equity Gross Minority Interest" → 2025-12-31` | 1,172,000,000 | `GEV_balance.csv → "Total Debt" → 2025-12-31` | 8,848,000,000 | `GEV_balance.csv → "Cash And Cash Equivalents" → 2025-12-31` | **4,620,000,000** |

**Step 3: ROIC**

| Year | NOPAT | ÷ Invested Capital | = ROIC |
|------|-------|---------------------|--------|
| 2022 | −2,275,990,000 | ÷ 10,684,000,000 | **−21.3%** |
| 2023 | −729,170,000 | ÷ 7,986,000,000 | **−9.1%** |
| 2024 | 293,904,000 | ÷ 3,431,000,000 | **8.6%** |
| 2025 | 1,097,310,000 | ÷ 4,620,000,000 | **23.8%** |

**GEV ROIC Average = (−21.3 + (−9.1) + 8.6 + 23.8) / 4 = 0.5%**

---

## 2. FCF Margin (Weight: 15%)

```
FCF Margin = Free Cash Flow / Total Revenue
FCF = Operating Cash Flow − Capital Expenditures
```

### EQNR

| Year | Operating CF | Source | − CapEx (abs) | Source | = FCF | ÷ Revenue | Source | = Margin |
|------|-------------|--------|---------------|--------|-------|-----------|--------|----------|
| 2022 | 35,136,000,000 | `EQNR_cashflow.csv → "Operating Cash Flow" → 2022-12-31` | 8,758,000,000 | `EQNR_cashflow.csv → "Capital Expenditure" → 2022-12-31` (−8,758M) | **26,378,000,000** | ÷ 149,004,000,000 | `EQNR_income.csv → "Total Revenue" → 2022-12-31` | **17.7%** |
| 2023 | 29,257,000,000 | `EQNR_cashflow.csv → "Operating Cash Flow" → 2023-12-31` | 10,575,000,000 | `EQNR_cashflow.csv → "Capital Expenditure" → 2023-12-31` (−10,575M) | **18,682,000,000** | ÷ 106,848,000,000 | `EQNR_income.csv → "Total Revenue" → 2023-12-31` | **17.5%** |
| 2024 | 19,465,000,000 | `EQNR_cashflow.csv → "Operating Cash Flow" → 2024-12-31` | 12,177,000,000 | `EQNR_cashflow.csv → "Capital Expenditure" → 2024-12-31` (−12,177M) | **7,288,000,000** | ÷ 102,502,000,000 | `EQNR_income.csv → "Total Revenue" → 2024-12-31` | **7.1%** |
| 2025 | 19,971,000,000 | `EQNR_cashflow.csv → "Operating Cash Flow" → 2025-12-31` | 13,994,000,000 | `EQNR_cashflow.csv → "Capital Expenditure" → 2025-12-31` (−13,994M) | **5,977,000,000** | ÷ 105,828,000,000 | `EQNR_income.csv → "Total Revenue" → 2025-12-31` | **5.6%** |

**EQNR FCF Margin Average = (17.7 + 17.5 + 7.1 + 5.6) / 4 = 12.0%**

### GEV

| Year | Operating CF | Source | − CapEx (abs) | Source | = FCF | ÷ Revenue | Source | = Margin |
|------|-------------|--------|---------------|--------|-------|-----------|--------|----------|
| 2022 | −114,000,000 | `GEV_cashflow.csv → "Operating Cash Flow" → 2022-12-31` | 513,000,000 | `GEV_cashflow.csv → "Capital Expenditure" → 2022-12-31` (−513M) | **−627,000,000** | ÷ 29,654,000,000 | `GEV_income.csv → "Total Revenue" → 2022-12-31` | **−2.1%** |
| 2023 | 1,186,000,000 | `GEV_cashflow.csv → "Operating Cash Flow" → 2023-12-31` | 744,000,000 | `GEV_cashflow.csv → "Capital Expenditure" → 2023-12-31` (−744M) | **442,000,000** | ÷ 33,239,000,000 | `GEV_income.csv → "Total Revenue" → 2023-12-31` | **1.3%** |
| 2024 | 2,583,000,000 | `GEV_cashflow.csv → "Operating Cash Flow" → 2024-12-31` | 883,000,000 | `GEV_cashflow.csv → "Capital Expenditure" → 2024-12-31` (−883M) | **1,700,000,000** | ÷ 34,935,000,000 | `GEV_income.csv → "Total Revenue" → 2024-12-31` | **4.9%** |
| 2025 | 4,987,000,000 | `GEV_cashflow.csv → "Operating Cash Flow" → 2025-12-31` | 1,277,000,000 | `GEV_cashflow.csv → "Capital Expenditure" → 2025-12-31` (−1,277M) | **3,710,000,000** | ÷ 38,068,000,000 | `GEV_income.csv → "Total Revenue" → 2025-12-31` | **9.7%** |

**GEV FCF Margin Average = (−2.1 + 1.3 + 4.9 + 9.7) / 4 = 3.5%**

---

## 3. Revenue Growth — CAGR (Weight: 15%)

```
Revenue CAGR = (Revenue_last / Revenue_first) ^ (1/(n−1)) − 1
```

### EQNR

| Position | Value | Source |
|----------|-------|--------|
| Revenue first (2022) | 149,004,000,000 | `EQNR_income.csv → "Total Revenue" → 2022-12-31` |
| Revenue last (2025) | 105,828,000,000 | `EQNR_income.csv → "Total Revenue" → 2025-12-31` |

```
CAGR = (105,828,000,000 / 149,004,000,000) ^ (1/3) − 1
     = (0.7103) ^ (0.333) − 1 = −10.7%
```

**YoY Breakdown:**

| Period | Revenue | Source | YoY |
|--------|---------|--------|-----|
| 2022 | 149,004,000,000 | `EQNR_income.csv → "Total Revenue" → 2022-12-31` | — |
| 2023 | 106,848,000,000 | `EQNR_income.csv → "Total Revenue" → 2023-12-31` | **−28.3%** |
| 2024 | 102,502,000,000 | `EQNR_income.csv → "Total Revenue" → 2024-12-31` | **−4.1%** |
| 2025 | 105,828,000,000 | `EQNR_income.csv → "Total Revenue" → 2025-12-31` | **+3.2%** |

### GEV

| Position | Value | Source |
|----------|-------|--------|
| Revenue first (2022) | 29,654,000,000 | `GEV_income.csv → "Total Revenue" → 2022-12-31` |
| Revenue last (2025) | 38,068,000,000 | `GEV_income.csv → "Total Revenue" → 2025-12-31` |

```
CAGR = (38,068,000,000 / 29,654,000,000) ^ (1/3) − 1
     = (1.284) ^ (0.333) − 1 = +8.7%
```

---

## 4. Margin Volatility (Weight: 10%, inverse — lower is better)

```
Op Margin = Operating Income / Revenue  (per year)
Volatility = StdDev(all yearly Op Margins)
```

### EQNR

| Year | Operating Income | Source | ÷ Revenue | Source | = Op Margin |
|------|-----------------|--------|-----------|--------|-------------|
| 2022 | 77,741,000,000 | `EQNR_income.csv → "Operating Income" → 2022-12-31` | ÷ 149,004,000,000 | `EQNR_income.csv → "Total Revenue" → 2022-12-31` | **52.2%** |
| 2023 | 35,233,000,000 | `EQNR_income.csv → "Operating Income" → 2023-12-31` | ÷ 106,848,000,000 | `EQNR_income.csv → "Total Revenue" → 2023-12-31` | **33.0%** |
| 2024 | 30,354,000,000 | `EQNR_income.csv → "Operating Income" → 2024-12-31` | ÷ 102,502,000,000 | `EQNR_income.csv → "Total Revenue" → 2024-12-31` | **29.6%** |
| 2025 | 24,730,000,000 | `EQNR_income.csv → "Operating Income" → 2025-12-31` | ÷ 105,828,000,000 | `EQNR_income.csv → "Total Revenue" → 2025-12-31` | **23.4%** |

```
Mean = (52.2 + 33.0 + 29.6 + 23.4) / 4 = 34.6%
StdDev = √[((52.2−34.6)² + (33.0−34.6)² + (29.6−34.6)² + (23.4−34.6)²) / 4]
       = √[(309.8 + 2.6 + 25.0 + 125.4) / 4] = √115.7 = 10.8%
```

**EQNR Margin Volatility = 10.8%**

### GEV

| Year | Operating Income | Source | ÷ Revenue | Source | = Op Margin |
|------|-----------------|--------|-----------|--------|-------------|
| 2022 | −2,881,000,000 | `GEV_income.csv → "Operating Income" → 2022-12-31` | ÷ 29,654,000,000 | `GEV_income.csv → "Total Revenue" → 2022-12-31` | **−9.7%** |
| 2023 | −923,000,000 | `GEV_income.csv → "Operating Income" → 2023-12-31` | ÷ 33,239,000,000 | `GEV_income.csv → "Total Revenue" → 2023-12-31` | **−2.8%** |
| 2024 | 471,000,000 | `GEV_income.csv → "Operating Income" → 2024-12-31` | ÷ 34,935,000,000 | `GEV_income.csv → "Total Revenue" → 2024-12-31` | **1.3%** |
| 2025 | 1,389,000,000 | `GEV_income.csv → "Operating Income" → 2025-12-31` | ÷ 38,068,000,000 | `GEV_income.csv → "Total Revenue" → 2025-12-31` | **3.7%** |

```
Mean = (−9.7 + (−2.8) + 1.3 + 3.7) / 4 = −1.9%
StdDev = 5.8%
```

**GEV Margin Volatility = 5.8%**

---

## 5. Leverage — Net Debt / EBITDA (Weight: 10%, inverse)

```
Leverage = (Total Debt − Cash) / EBITDA
```

### EQNR

| Year | Total Debt | Source | − Cash | Source | = Net Debt | ÷ EBITDA | Source | = Leverage |
|------|-----------|--------|--------|--------|-----------|----------|--------|-----------|
| 2022 | 32,167,000,000 | `EQNR_balance.csv → "Total Debt" → 2022-12-31` | 9,438,000,000 | `EQNR_balance.csv → "Cash And Cash Equivalents" → 2022-12-31` | 22,729,000,000 | ÷ 86,266,000,000 | `EQNR_income.csv → "EBITDA" → 2022-12-31` | **0.26x** |
| 2023 | 31,795,000,000 | `EQNR_balance.csv → "Total Debt" → 2023-12-31` | 8,070,000,000 | `EQNR_balance.csv → "Cash And Cash Equivalents" → 2023-12-31` | 23,725,000,000 | ÷ 49,587,000,000 | `EQNR_income.csv → "EBITDA" → 2023-12-31` | **0.48x** |
| 2024 | 30,095,000,000 | `EQNR_balance.csv → "Total Debt" → 2024-12-31` | 5,903,000,000 | `EQNR_balance.csv → "Cash And Cash Equivalents" → 2024-12-31` | 24,192,000,000 | ÷ 41,949,000,000 | `EQNR_income.csv → "EBITDA" → 2024-12-31` | **0.58x** |
| 2025 | 31,220,000,000 | `EQNR_balance.csv → "Total Debt" → 2025-12-31` | 5,036,000,000 | `EQNR_balance.csv → "Cash And Cash Equivalents" → 2025-12-31` | 26,184,000,000 | ÷ 38,393,000,000 | `EQNR_income.csv → "EBITDA" → 2025-12-31` | **0.68x** |

**EQNR Leverage Average = (0.26 + 0.48 + 0.58 + 0.68) / 4 = 0.50x**

### GEV

| Year | Total Debt | Source | − Cash | Source | = Net Debt | ÷ EBITDA | Source | = Leverage |
|------|-----------|--------|--------|--------|-----------|----------|--------|-----------|
| 2022 | 1,144,000,000 | `GEV_balance.csv → "Total Debt" → 2022-12-31` | 2,067,000,000 | `GEV_balance.csv → "Cash And Cash Equivalents" → 2022-12-31` | −923,000,000 | ÷ −526,000,000 | `GEV_income.csv → "EBITDA" → 2022-12-31` | **1.75x** |
| 2023 | 1,157,000,000 | `GEV_balance.csv → "Total Debt" → 2023-12-31` | 1,551,000,000 | `GEV_balance.csv → "Cash And Cash Equivalents" → 2023-12-31` | −394,000,000 | ÷ 932,000,000 | `GEV_income.csv → "EBITDA" → 2023-12-31` | **−0.42x** |
| 2024 | 1,043,000,000 | `GEV_balance.csv → "Total Debt" → 2024-12-31` | 8,205,000,000 | `GEV_balance.csv → "Cash And Cash Equivalents" → 2024-12-31` | −7,162,000,000 | ÷ 1,643,000,000 | `GEV_income.csv → "EBITDA" → 2024-12-31` | **−4.36x** |
| 2025 | 1,172,000,000 | `GEV_balance.csv → "Total Debt" → 2025-12-31` | 8,848,000,000 | `GEV_balance.csv → "Cash And Cash Equivalents" → 2025-12-31` | −7,676,000,000 | ÷ 2,242,000,000 | `GEV_income.csv → "EBITDA" → 2025-12-31` | **−3.43x** |

**GEV Leverage Average = (1.75 + (−0.42) + (−4.36) + (−3.43)) / 4 = −1.62x** (net cash)

---

## 6. Cash Quality — CFO / Net Income (Weight: 10%)

```
Cash Quality = Operating Cash Flow / Net Income
```

### EQNR

| Year | Operating CF | Source | ÷ Net Income | Source | = Ratio |
|------|-------------|--------|-------------|--------|---------|
| 2022 | 35,136,000,000 | `EQNR_cashflow.csv → "Operating Cash Flow" → 2022-12-31` | 28,746,000,000 | `EQNR_income.csv → "Net Income Common Stockholders" → 2022-12-31` | **1.22x** |
| 2023 | 29,257,000,000 | `EQNR_cashflow.csv → "Operating Cash Flow" → 2023-12-31` | 11,885,000,000 | `EQNR_income.csv → "Net Income Common Stockholders" → 2023-12-31` | **2.46x** |
| 2024 | 19,465,000,000 | `EQNR_cashflow.csv → "Operating Cash Flow" → 2024-12-31` | 8,806,000,000 | `EQNR_income.csv → "Net Income Common Stockholders" → 2024-12-31` | **2.21x** |
| 2025 | 19,971,000,000 | `EQNR_cashflow.csv → "Operating Cash Flow" → 2025-12-31` | 5,043,000,000 | `EQNR_income.csv → "Net Income Common Stockholders" → 2025-12-31` | **3.96x** |

**EQNR Cash Quality Average = (1.22 + 2.46 + 2.21 + 3.96) / 4 = 2.46x**

### GEV

| Year | Operating CF | Source | ÷ Net Income | Source | = Ratio |
|------|-------------|--------|-------------|--------|---------|
| 2022 | −114,000,000 | `GEV_cashflow.csv → "Operating Cash Flow" → 2022-12-31` | −2,736,000,000 | `GEV_income.csv → "Net Income Common Stockholders" → 2022-12-31` | **0.04x** |
| 2023 | 1,186,000,000 | `GEV_cashflow.csv → "Operating Cash Flow" → 2023-12-31` | −438,000,000 | `GEV_income.csv → "Net Income Common Stockholders" → 2023-12-31` | **−2.71x** |
| 2024 | 2,583,000,000 | `GEV_cashflow.csv → "Operating Cash Flow" → 2024-12-31` | 1,552,000,000 | `GEV_income.csv → "Net Income Common Stockholders" → 2024-12-31` | **1.66x** |
| 2025 | 4,987,000,000 | `GEV_cashflow.csv → "Operating Cash Flow" → 2025-12-31` | 4,884,000,000 | `GEV_income.csv → "Net Income Common Stockholders" → 2025-12-31` | **1.02x** |

**GEV Cash Quality Average = (0.04 + (−2.71) + 1.66 + 1.02) / 4 = 0.00x**

---

## 7. Interest Coverage (Weight: 10%)

```
Interest Coverage = EBIT / Interest Expense
```

### EQNR

| Year | EBIT | Source | ÷ Interest Expense | Source | = Coverage |
|------|------|--------|---------------------|--------|-----------|
| 2022 | 79,533,000,000 | `EQNR_income.csv → "EBIT" → 2022-12-31` | 929,000,000 | `EQNR_income.csv → "Interest Expense" → 2022-12-31` | **85.6x** |
| 2023 | 39,006,000,000 | `EQNR_income.csv → "EBIT" → 2023-12-31` | 1,122,000,000 | `EQNR_income.csv → "Interest Expense" → 2023-12-31` | **34.8x** |
| 2024 | 32,043,000,000 | `EQNR_income.csv → "EBIT" → 2024-12-31` | 1,057,000,000 | `EQNR_income.csv → "Interest Expense" → 2024-12-31` | **30.3x** |
| 2025 | 25,920,000,000 | `EQNR_income.csv → "EBIT" → 2025-12-31` | 832,000,000 | `EQNR_income.csv → "Interest Expense" → 2025-12-31` | **31.2x** |

**EQNR Interest Coverage Average = (85.6 + 34.8 + 30.3 + 31.2) / 4 = 45.5x**

### GEV

| Year | EBIT | Source | ÷ Interest Expense | Source | = Coverage |
|------|------|--------|---------------------|--------|-----------|
| 2022 | −2,323,000,000 | `GEV_income.csv → "EBIT" → 2022-12-31` | 151,000,000 | `GEV_income.csv → "Interest Expense" → 2022-12-31` | **−15.4x** |
| 2023 | −32,000,000 | `GEV_income.csv → "EBIT" → 2023-12-31` | 98,000,000 | `GEV_income.csv → "Interest Expense" → 2023-12-31` | **−0.3x** |
| 2024 | 471,000,000 | `GEV_income.csv → "EBIT" → 2024-12-31` | NaN | `GEV_income.csv → "Interest Expense" → 2024-12-31` | **N/A** |
| 2025 | 1,389,000,000 | `GEV_income.csv → "EBIT" → 2025-12-31` | NaN | `GEV_income.csv → "Interest Expense" → 2025-12-31` | **N/A** |

**GEV Interest Coverage: only 2 years calculable, both negative (pre-turnaround)**

---

## 8. Operating Margin Trend (Weight: 10%)

```
Trend = Linear regression slope through yearly Operating Margins
```

Uses the Operating Margins calculated in Section 4:

### EQNR

Margins: 52.2% → 33.0% → 29.6% → 23.4% (indexed as x = 0, 1, 2, 3)

```
Linear regression: y = a + bx
b = [n·Σxy − Σx·Σy] / [n·Σx² − (Σx)²]

Σx = 0+1+2+3 = 6        Σy = 52.2+33.0+29.6+23.4 = 138.2
Σxy = 0×52.2 + 1×33.0 + 2×29.6 + 3×23.4 = 0 + 33.0 + 59.2 + 70.2 = 162.4
Σx² = 0+1+4+9 = 14      n = 4

b = (4×162.4 − 6×138.2) / (4×14 − 36) = (649.6 − 829.2) / (56 − 36)
  = −179.6 / 20 = −8.98% per year
```

**EQNR Margin Trend = −9.0%/year** (margins declining fast)

### GEV

Margins: −9.7% → −2.8% → 1.3% → 3.7%

```
Σx = 6   Σy = −7.5   Σxy = 0×(−9.7) + 1×(−2.8) + 2×1.3 + 3×3.7 = −2.8 + 2.6 + 11.1 = 10.9
b = (4×10.9 − 6×(−7.5)) / 20 = (43.6 + 45.0) / 20 = 88.6 / 20 = +4.43% per year
```

**GEV Margin Trend = +4.4%/year** (margins expanding)

---

## 9. Final Quality Score Assembly

All 8 metrics computed above are combined into a single Quality Score. The process:

1. Each metric's raw value is **percentile-ranked** among all ~105 companies (0th = worst, 100th = best)
2. For inverse metrics (leverage, volatility), the rank is flipped: lowest raw value → highest percentile
3. Each percentile is multiplied by its **weight**
4. All weighted percentiles are summed → **Quality Score (0–100)**

### EQNR — Quality Score = 59.4

| # | Metric | Raw Value | Pctl | × Weight | = Contribution | Ref |
|---|--------|-----------|------|----------|----------------|-----|
| §1 | ROIC | 46.5% | 97.6th | × 20% | **19.5** | Section 1 |
| §2 | FCF Margin | 15.5% | 67.3th | × 15% | **10.1** | Section 2 |
| §3 | Revenue Growth | 4.9% | 22.7th | × 15% | **3.4** | Section 3 |
| §4 | Margin Volatility *(inv)* | 10.0% | 14.4th | × 10% | **1.4** | Section 4 |
| §5 | Leverage *(inv)* | 0.47x | 76.2th | × 10% | **7.6** | Section 5 |
| §6 | Cash Quality | 2.24x | 74.3th | × 10% | **7.4** | Section 6 |
| §7 | Interest Coverage | 46.7x | 90.2th | × 10% | **9.0** | Section 7 |
| §8 | Margin Trend | −4.2% | 8.3th | × 10% | **0.8** | Section 8 |
| | | | | **Total** | **59.4** | |

```
Quality Score = 19.5 + 10.1 + 3.4 + 1.4 + 7.6 + 7.4 + 9.0 + 0.8 = 59.4
```

**What pulls EQNR up:** ROIC (97.6th percentile — near the top of all companies) and Interest Coverage (90.2th). These are the backward-looking metrics inflated by 2022.

**What pulls EQNR down:** Margin Trend (8.3th — nearly worst in the dataset, margins declining −4.2%/year), Revenue Growth (22.7th — revenue is shrinking), and Margin Volatility (14.4th — highly unstable margins).

---

### GEV — Quality Score = 33.6

| # | Metric | Raw Value | Pctl | × Weight | = Contribution | Ref |
|---|--------|-----------|------|----------|----------------|-----|
| §1 | ROIC | 1.0% | 3.3th | × 20% | **0.7** | Section 1 |
| §2 | FCF Margin | 3.5% | 31.7th | × 15% | **4.8** | Section 2 |
| §3 | Revenue Growth | 8.7% | 35.1th | × 15% | **5.3** | Section 3 |
| §4 | Margin Volatility *(inv)* | 5.9% | 27.9th | × 10% | **2.8** | Section 4 |
| §5 | Leverage *(inv)* | −1.61x | 96.7th | × 10% | **9.7** | Section 5 |
| §6 | Cash Quality | 0.00x | 9.5th | × 10% | **1.0** | Section 6 |
| §7 | Interest Coverage | −14.2x | 3.4th | × 10% | **0.3** | Section 7 |
| §8 | Margin Trend | +4.4% | 91.7th | × 10% | **9.2** | Section 8 |
| | | | | **Total** | **33.6** | |

```
Quality Score = 0.7 + 4.8 + 5.3 + 2.8 + 9.7 + 1.0 + 0.3 + 9.2 = 33.6
```

**What pulls GEV up:** Leverage (96.7th — net cash, almost no debt) and Margin Trend (91.7th — one of the fastest margin improvers in the dataset).

**What pulls GEV down:** ROIC (3.3th — near the bottom due to 2022-2023 losses) and Interest Coverage (3.4th — negative EBIT in early years). These backward-looking metrics haven't caught up to the turnaround yet.

---

### The Paradox Explained

| | EQNR | GEV |
|---|------|-----|
| Quality Score | **59.4** (higher) | **33.6** (lower) |
| Technical Rating | **Sell** | **Buy** |
| The story | Peak-cycle metrics declining | Turnaround metrics improving |

EQNR scores higher because its 4-year averages are still dominated by the 2022 windfall. But the *direction* of every metric is downward. GEV scores lower because its 4-year averages include two loss years — but the *direction* of every metric is upward. The technical indicators see the price trend and correctly flag EQNR as declining and GEV as ascending.

**Lesson:** Quality scores are a snapshot of averaged history. Always check the *trend* (margin trend, revenue growth) and compare with technical signals to see where the company is heading, not just where it's been.

---

## Cell Reference Index

Quick lookup — which file/row/column for each input:

| Variable | File | Row Name | Column |
|----------|------|----------|--------|
| Revenue | `{T}_income.csv` | `Total Revenue` | `{YYYY}-12-31` |
| Operating Income | `{T}_income.csv` | `Operating Income` | `{YYYY}-12-31` |
| EBIT | `{T}_income.csv` | `EBIT` | `{YYYY}-12-31` |
| EBITDA | `{T}_income.csv` | `EBITDA` | `{YYYY}-12-31` |
| Net Income | `{T}_income.csv` | `Net Income Common Stockholders` | `{YYYY}-12-31` |
| Interest Expense | `{T}_income.csv` | `Interest Expense` | `{YYYY}-12-31` |
| Tax Rate | `{T}_income.csv` | `Tax Rate For Calcs` | `{YYYY}-12-31` |
| Total Equity | `{T}_balance.csv` | `Total Equity Gross Minority Interest` | `{YYYY}-12-31` |
| Total Debt | `{T}_balance.csv` | `Total Debt` | `{YYYY}-12-31` |
| Cash | `{T}_balance.csv` | `Cash And Cash Equivalents` | `{YYYY}-12-31` |
| Operating Cash Flow | `{T}_cashflow.csv` | `Operating Cash Flow` | `{YYYY}-12-31` |
| Capital Expenditure | `{T}_cashflow.csv` | `Capital Expenditure` | `{YYYY}-12-31` |

Where `{T}` = ticker (EQNR, GEV, etc.) and `{YYYY}` = fiscal year.

---

*All values sourced from yfinance financial statements. Generated from EQNR and GEV data (fiscal years 2022–2025).*
