# Quality Score v3 — Cell-Level Calculation Trace

## EQNR (Equinor) vs GEV (GE Vernova)

**v3 changes from v2:**
- ✅ **EMA averaging** for ROIC, FCF, Leverage, Cash Quality (recent years weighted more: 10% → 17% → 28% → 46%)
- ✅ **Net Income Growth** added as new metric (10% weight)
- ❌ **Interest Coverage removed** (too noisy — NaN for low-debt companies, range −246x to +303x)

Every number traced to: **`FILE → Row Name → Column (Year)`**

---

## 1. ROIC — Return on Invested Capital (Weight: 20%, EMA)

```
ROIC = NOPAT / Invested Capital
NOPAT = Operating Income × (1 − Tax Rate)
Invested Capital = Total Equity + Total Debt − Cash
Averaging: EMA (weights: 2022=10%, 2023=17%, 2024=28%, 2025=46%)
```

### EQNR

**Step 1: NOPAT (from Income Statement)**

| Year | Operating Income | Source | × (1 − Tax Rate) | Source | = NOPAT |
|------|-----------------|--------|-------------------|--------|---------|
| 2022 | 77,741,000,000 | `EQNR_income.csv → "Operating Income" → 2022-12-31` | × (1 − 0.22) | `→ "Tax Rate For Calcs" → 2022-12-31` | **60,638,180,000** |
| 2023 | 35,233,000,000 | `EQNR_income.csv → "Operating Income" → 2023-12-31` | × (1 − 0.22) | `→ "Tax Rate For Calcs" → 2023-12-31` | **27,481,740,000** |
| 2024 | 30,354,000,000 | `EQNR_income.csv → "Operating Income" → 2024-12-31` | × (1 − 0.22) | `→ "Tax Rate For Calcs" → 2024-12-31` | **23,676,120,000** |
| 2025 | 24,730,000,000 | `EQNR_income.csv → "Operating Income" → 2025-12-31` | × (1 − 0.22) | `→ "Tax Rate For Calcs" → 2025-12-31` | **19,289,400,000** |

**Step 2: Invested Capital (from Balance Sheet)**

| Year | Equity | Source | + Debt | Source | − Cash | Source | = Inv. Capital |
|------|--------|--------|--------|--------|--------|--------|----------------|
| 2022 | 53,989M | `EQNR_balance.csv → "Total Equity Gross Minority Interest" → 2022` | 32,167M | `→ "Total Debt" → 2022` | 9,438M | `→ "Cash And Cash Equivalents" → 2022` | **76,718M** |
| 2023 | 48,500M | `→ 2023` | 31,795M | `→ 2023` | 8,070M | `→ 2023` | **72,225M** |
| 2024 | 42,380M | `→ 2024` | 30,095M | `→ 2024` | 5,903M | `→ 2024` | **66,572M** |
| 2025 | 40,497M | `→ 2025` | 31,220M | `→ 2025` | 5,036M | `→ 2025` | **66,681M** |

**Step 3: Yearly ROIC → EMA Average**

| Year | NOPAT ÷ Inv. Capital | = ROIC | × EMA Weight |
|------|----------------------|--------|--------------|
| 2022 | 60,638M ÷ 76,718M | **79.0%** | × 10% |
| 2023 | 27,482M ÷ 72,225M | **38.1%** | × 17% |
| 2024 | 23,676M ÷ 66,572M | **35.6%** | × 28% |
| 2025 | 19,289M ÷ 66,681M | **28.9%** | × 46% |

```
v2 (SMA): (79.0 + 38.1 + 35.6 + 28.9) / 4 = 45.4%
v3 (EMA): 79.0×10% + 38.1×17% + 35.6×28% + 28.9×46% = 37.2%  ← 2022 spike matters less
```

**EQNR ROIC = 37.2% (EMA)**  ↓ from 45.4% (SMA)

### GEV

**Step 1–2: NOPAT and Invested Capital**

| Year | Op Income | Source | × (1−Tax) | Equity | Debt | Cash | Inv. Capital | ROIC |
|------|-----------|--------|-----------|--------|------|------|--------------|------|
| 2022 | −2,881M | `GEV_income.csv → "Operating Income" → 2022` | × 0.79 | 11,607M | 1,144M | 2,067M | 10,684M | **−21.3%** |
| 2023 | −923M | `→ 2023` | × 0.79 | 8,380M | 1,157M | 1,551M | 7,986M | **−9.1%** |
| 2024 | 471M | `→ 2024` | × 0.624 | 10,593M | 1,043M | 8,205M | 3,431M | **8.6%** |
| 2025 | 1,389M | `→ 2025` | × 0.79 | 12,296M | 1,172M | 8,848M | 4,620M | **23.8%** |

```
v2 (SMA): (−21.3 + (−9.1) + 8.6 + 23.8) / 4 = 0.5%
v3 (EMA): −21.3×10% + (−9.1)×17% + 8.6×28% + 23.8×46% = 9.7%  ← turnaround weighted more
```

**GEV ROIC = 9.7% (EMA)**  ↑ from 0.5% (SMA)

---

## 2. FCF Margin (Weight: 15%, EMA)

```
FCF Margin = (Operating Cash Flow − |Capital Expenditure|) / Total Revenue
Averaging: EMA
```

### EQNR

| Year | OCF | Source | − |CapEx| | Source | = FCF | ÷ Revenue | Source | = Margin | × EMA |
|------|-----|--------|-----------|--------|-------|-----------|--------|----------|-------|
| 2022 | 35,136M | `EQNR_cashflow.csv → "Operating Cash Flow" → 2022` | 8,758M | `→ "Capital Expenditure" → 2022` | 26,378M | ÷ 149,004M | `EQNR_income.csv → "Total Revenue" → 2022` | **17.7%** | ×10% |
| 2023 | 29,257M | `→ 2023` | 10,575M | `→ 2023` | 18,682M | ÷ 106,848M | `→ 2023` | **17.5%** | ×17% |
| 2024 | 19,465M | `→ 2024` | 12,177M | `→ 2024` | 7,288M | ÷ 102,502M | `→ 2024` | **7.1%** | ×28% |
| 2025 | 19,971M | `→ 2025` | 13,994M | `→ 2025` | 5,977M | ÷ 105,828M | `→ 2025` | **5.6%** | ×46% |

```
v2 (SMA): 12.0%  →  v3 (EMA): 9.2%
```

### GEV

| Year | OCF | − |CapEx| | = FCF | ÷ Revenue | = Margin | × EMA |
|------|-----|-----------| ------|-----------|----------|-------|
| 2022 | −114M | 513M | −627M | ÷ 29,654M | **−2.1%** | ×10% |
| 2023 | 1,186M | 744M | 442M | ÷ 33,239M | **1.3%** | ×17% |
| 2024 | 2,583M | 883M | 1,700M | ÷ 34,935M | **4.9%** | ×28% |
| 2025 | 4,987M | 1,277M | 3,710M | ÷ 38,068M | **9.7%** | ×46% |

```
v2 (SMA): 3.5%  →  v3 (EMA): 5.8%
```

---

## 3. Revenue Growth — CAGR (Weight: 10%, unchanged)

```
Revenue CAGR = (Revenue_last / Revenue_first) ^ (1/(n−1)) − 1
```

### EQNR

| Position | Value | Source |
|----------|-------|--------|
| First (2022) | 149,004,000,000 | `EQNR_income.csv → "Total Revenue" → 2022-12-31` |
| Last (2025) | 105,828,000,000 | `EQNR_income.csv → "Total Revenue" → 2025-12-31` |

```
CAGR = (105,828 / 149,004) ^ (1/3) − 1 = −10.8%
```

**YoY:** $149.0B → $106.8B (−28%) → $102.5B (−4%) → $105.8B (+3%)

### GEV

| Position | Value | Source |
|----------|-------|--------|
| First (2022) | 29,654,000,000 | `GEV_income.csv → "Total Revenue" → 2022-12-31` |
| Last (2025) | 38,068,000,000 | `GEV_income.csv → "Total Revenue" → 2025-12-31` |

```
CAGR = (38,068 / 29,654) ^ (1/3) − 1 = +8.7%
```

**YoY:** $29.7B → $33.2B (+12%) → $34.9B (+5%) → $38.1B (+9%)

---

## 4. Net Income Growth — NEW in v3 (Weight: 10%)

```
NI CAGR = (NI_last / NI_first) ^ (1/(n−1)) − 1     (when both positive)
        = +100%   (turnaround: loss → profit)
        = −100%   (deterioration: profit → loss)
```

### EQNR

| Year | Net Income | Source | YoY |
|------|-----------|--------|-----|
| 2022 | 28,746,000,000 | `EQNR_income.csv → "Net Income Common Stockholders" → 2022-12-31` | — |
| 2023 | 11,885,000,000 | `→ 2023-12-31` | **−58.6%** |
| 2024 | 8,806,000,000 | `→ 2024-12-31` | **−25.9%** |
| 2025 | 5,043,000,000 | `→ 2025-12-31` | **−42.7%** |

```
Both positive: CAGR = (5,043 / 28,746) ^ (1/3) − 1 = −44.0%
```

**EQNR NI Growth = −44.0%** — Net income collapsed from $28.7B to $5.0B in 3 years.

### GEV

| Year | Net Income | Source | YoY |
|------|-----------|--------|-----|
| 2022 | −2,736,000,000 | `GEV_income.csv → "Net Income Common Stockholders" → 2022-12-31` | — |
| 2023 | −438,000,000 | `→ 2023-12-31` | losses shrinking |
| 2024 | 1,552,000,000 | `→ 2024-12-31` | **turned profitable** |
| 2025 | 4,884,000,000 | `→ 2025-12-31` | **+214.7%** |

```
Loss → Profit turnaround: capped at +100%
```

**GEV NI Growth = +100%** (capped) — Went from −$2.7B loss to $4.9B profit.

> This is the most dramatic difference between EQNR and GEV. EQNR's net income is in freefall (−44%/yr), GEV completed a full turnaround. The old v2 formula with only revenue growth couldn't capture this — revenue tells you the top line, but net income tells you the bottom line.

---

## 5. Leverage — Net Debt / EBITDA (Weight: 15%, EMA, inverse)

```
Leverage = (Total Debt − Cash) / EBITDA
Averaging: EMA     Direction: lower is better
```

### EQNR

| Year | Debt | Source | − Cash | Source | = Net Debt | ÷ EBITDA | Source | = Lev | × EMA |
|------|------|--------|--------|--------|-----------|----------|--------|-------|-------|
| 2022 | 32,167M | `EQNR_balance.csv → "Total Debt" → 2022` | 9,438M | `→ "Cash And Cash Equivalents" → 2022` | 22,729M | ÷ 86,266M | `EQNR_income.csv → "EBITDA" → 2022` | **0.26x** | ×10% |
| 2023 | 31,795M | `→ 2023` | 8,070M | `→ 2023` | 23,725M | ÷ 49,587M | `→ 2023` | **0.48x** | ×17% |
| 2024 | 30,095M | `→ 2024` | 5,903M | `→ 2024` | 24,192M | ÷ 41,949M | `→ 2024` | **0.58x** | ×28% |
| 2025 | 31,220M | `→ 2025` | 5,036M | `→ 2025` | 26,184M | ÷ 38,393M | `→ 2025` | **0.68x** | ×46% |

```
v2 (SMA): 0.50x  →  v3 (EMA): 0.58x  ← rising leverage weighted more
```

### GEV

| Year | Debt − Cash = Net Debt | ÷ EBITDA | = Lev | × EMA |
|------|------------------------|----------|-------|-------|
| 2022 | 1,144M − 2,067M = −923M | ÷ −526M | **1.75x** | ×10% |
| 2023 | 1,157M − 1,551M = −394M | ÷ 932M | **−0.42x** | ×17% |
| 2024 | 1,043M − 8,205M = −7,162M | ÷ 1,643M | **−4.36x** | ×28% |
| 2025 | 1,172M − 8,848M = −7,676M | ÷ 2,242M | **−3.43x** | ×46% |

```
v2 (SMA): −1.61x  →  v3 (EMA): −2.67x  ← recent net cash position weighted more
```

---

## 6. Cash Quality — CFO / Net Income (Weight: 10%, EMA)

```
Cash Quality = Operating Cash Flow / Net Income
Averaging: EMA
```

### EQNR

| Year | OCF | Source | ÷ Net Income | Source | = Ratio | × EMA |
|------|-----|--------|-------------|--------|---------|-------|
| 2022 | 35,136M | `EQNR_cashflow.csv → "Operating Cash Flow" → 2022` | 28,746M | `EQNR_income.csv → "Net Income Common Stockholders" → 2022` | **1.22x** | ×10% |
| 2023 | 29,257M | `→ 2023` | 11,885M | `→ 2023` | **2.46x** | ×17% |
| 2024 | 19,465M | `→ 2024` | 8,806M | `→ 2024` | **2.21x** | ×28% |
| 2025 | 19,971M | `→ 2025` | 5,043M | `→ 2025` | **3.96x** | ×46% |

```
v2 (SMA): 2.46x  →  v3 (EMA): 2.96x
```

### GEV

| Year | OCF ÷ Net Income | = Ratio | × EMA |
|------|-------------------|---------|-------|
| 2022 | −114M ÷ −2,736M | **0.04x** | ×10% |
| 2023 | 1,186M ÷ −438M | **−2.71x** | ×17% |
| 2024 | 2,583M ÷ 1,552M | **1.66x** | ×28% |
| 2025 | 4,987M ÷ 4,884M | **1.02x** | ×46% |

```
v2 (SMA): 0.00x  →  v3 (EMA): 0.48x  ← recent healthy years weighted more
```

---

## 7. Margin Volatility (Weight: 10%, inverse, SMA — unchanged)

```
Op Margin = Operating Income / Revenue  (per year)
Volatility = StdDev(all yearly margins)         Direction: lower is better
```

### EQNR

| Year | Op Income ÷ Revenue | = Margin | Source |
|------|---------------------|----------|--------|
| 2022 | 77,741M ÷ 149,004M | **52.2%** | `EQNR_income.csv → "Operating Income" ÷ "Total Revenue" → 2022` |
| 2023 | 35,233M ÷ 106,848M | **33.0%** | `→ 2023` |
| 2024 | 30,354M ÷ 102,502M | **29.6%** | `→ 2024` |
| 2025 | 24,730M ÷ 105,828M | **23.4%** | `→ 2025` |

**Volatility = StdDev(52.2, 33.0, 29.6, 23.4) = 10.8%**

### GEV

| Year | Op Income ÷ Revenue | = Margin |
|------|---------------------|----------|
| 2022 | −2,881M ÷ 29,654M | **−9.7%** |
| 2023 | −923M ÷ 33,239M | **−2.8%** |
| 2024 | 471M ÷ 34,935M | **1.3%** |
| 2025 | 1,389M ÷ 38,068M | **3.6%** |

**Volatility = StdDev(−9.7, −2.8, 1.3, 3.6) = 5.1%**

---

## 8. Margin Trend (Weight: 10%, SMA — unchanged)

```
Trend = Linear regression slope through yearly Operating Margins
```

### EQNR: 52.2% → 33.0% → 29.6% → 23.4%

```
Slope = −9.0% per year  (margins compressing fast)
```

### GEV: −9.7% → −2.8% → 1.3% → 3.6%

```
Slope = +4.4% per year  (margins expanding)
```

---

## 9. Final Quality Score Assembly (v3)

**New formula — 8 metrics, EMA-weighted, no interest coverage:**

```
Quality Score = Σ(percentile_rank × weight) for each metric
```

Each metric's value is percentile-ranked among all ~105 companies (0th = worst, 100th = best).

### EQNR — Quality Score

| # | Metric | Raw (v3) | vs v2 | Pctl | × Weight | = Contribution |
|---|--------|----------|-------|------|----------|----------------|
| §1 | ROIC **(EMA)** | 37.2% | ↓ was 45.4% | ~92nd | × 20% | **~18.4** |
| §2 | FCF Margin **(EMA)** | 9.2% | ↓ was 12.0% | ~60th | × 15% | **~9.0** |
| §3 | Revenue Growth | −10.8% | same | ~8th | × 10% | **~0.8** |
| §4 | **NI Growth (NEW)** | **−44.0%** | *didn't exist* | ~3rd | × 10% | **~0.3** |
| §5 | Leverage **(EMA, inv)** | 0.58x | ↑ was 0.50x | ~74th | × 15% | **~11.1** |
| §6 | Margin Volatility *(inv)* | 10.8% | same | ~14th | × 10% | **~1.4** |
| §7 | Cash Quality **(EMA)** | 2.96x | ↑ was 2.46x | ~78th | × 10% | **~7.8** |
| §8 | Margin Trend | −9.0%/yr | same | ~5th | × 10% | **~0.5** |
| | | | | | **Total** | **~49** |

> **v3 score ≈ 49** (down from v2's 59). The net income growth metric (−44%, 3rd percentile) is devastating — it exposes what revenue growth alone couldn't: EQNR's bottom line is collapsing. EMA also deflates the 2022-inflated ROIC and FCF.

### GEV — Quality Score

| # | Metric | Raw (v3) | vs v2 | Pctl | × Weight | = Contribution |
|---|--------|----------|-------|------|----------|----------------|
| §1 | ROIC **(EMA)** | 9.7% | ↑ was 0.5% | ~25th | × 20% | **~5.0** |
| §2 | FCF Margin **(EMA)** | 5.8% | ↑ was 3.5% | ~38th | × 15% | **~5.7** |
| §3 | Revenue Growth | +8.7% | same | ~35th | × 10% | **~3.5** |
| §4 | **NI Growth (NEW)** | **+100%** | *didn't exist* | ~98th | × 10% | **~9.8** |
| §5 | Leverage **(EMA, inv)** | −2.67x | ↑ was −1.61x | ~97th | × 15% | **~14.6** |
| §6 | Margin Volatility *(inv)* | 5.1% | same | ~32nd | × 10% | **~3.2** |
| §7 | Cash Quality **(EMA)** | 0.48x | ↑ was 0.00x | ~15th | × 10% | **~1.5** |
| §8 | Margin Trend | +4.4%/yr | same | ~92nd | × 10% | **~9.2** |
| | | | | | **Total** | **~53** |

> **v3 score ≈ 53** (up from v2's 34). The turnaround story is now properly captured: NI Growth at +100% (98th percentile) adds 9.8 points. EMA boosts ROIC from 0.5% → 9.7%, FCF from 3.5% → 5.8%.

---

## v2 → v3 Impact Summary

| Metric | EQNR v2 → v3 | GEV v2 → v3 | What changed |
|--------|---------------|-------------|--------------|
| ROIC | 45.4% → **37.2%** | 0.5% → **9.7%** | EMA deflates peaks, boosts recency |
| FCF | 12.0% → **9.2%** | 3.5% → **5.8%** | EMA deflates peaks, boosts recency |
| Revenue Growth | −10.8% | +8.7% | Unchanged (CAGR) |
| **NI Growth** | — → **−44.0%** | — → **+100%** | **NEW: biggest differentiator** |
| Leverage | 0.50x → **0.58x** | −1.61x → **−2.67x** | EMA shows current leverage better |
| Cash Quality | 2.46x → **2.96x** | 0.00x → **0.48x** | EMA reduces noise from loss years |
| Margin Vol | 10.8% | 5.1% | Unchanged |
| Margin Trend | −9.0%/yr | +4.4%/yr | Unchanged |
| **Quality Score** | **59 → ~49** | **34 → ~53** | **Gap closed: GEV now scores HIGHER** |

### The v3 Verdict

In v2, EQNR scored 59 vs GEV's 34 — a 25-point gap driven by EQNR's inflated historical averages. In v3, **GEV overtakes EQNR** (~53 vs ~49). The three changes that made this happen:

1. **EMA** deflated EQNR's 2022 windfall year (−8 pts on ROIC alone) while boosting GEV's recent profitability
2. **Net Income Growth** is the killer metric: EQNR at −44%/yr (3rd percentile) vs GEV at +100% (98th percentile) — a 9.5 point swing
3. **Removing Interest Coverage** eliminated a noisy metric that randomly helped/hurt based on data availability

The quality score now agrees with the technical indicators: EQNR is declining, GEV is ascending.

---

## Cell Reference Index

| Variable | File | Row Name | Column |
|----------|------|----------|--------|
| Revenue | `{T}_income.csv` | `Total Revenue` | `{YYYY}-12-31` |
| Operating Income | `{T}_income.csv` | `Operating Income` | `{YYYY}-12-31` |
| EBITDA | `{T}_income.csv` | `EBITDA` | `{YYYY}-12-31` |
| Net Income | `{T}_income.csv` | `Net Income Common Stockholders` | `{YYYY}-12-31` |
| Tax Rate | `{T}_income.csv` | `Tax Rate For Calcs` | `{YYYY}-12-31` |
| Total Equity | `{T}_balance.csv` | `Total Equity Gross Minority Interest` | `{YYYY}-12-31` |
| Total Debt | `{T}_balance.csv` | `Total Debt` | `{YYYY}-12-31` |
| Cash | `{T}_balance.csv` | `Cash And Cash Equivalents` | `{YYYY}-12-31` |
| Operating Cash Flow | `{T}_cashflow.csv` | `Operating Cash Flow` | `{YYYY}-12-31` |
| Capital Expenditure | `{T}_cashflow.csv` | `Capital Expenditure` | `{YYYY}-12-31` |

---

*Quality Score v3 — EMA + Net Income Growth. Generated from EQNR and GEV financial statements (2022–2025).*
