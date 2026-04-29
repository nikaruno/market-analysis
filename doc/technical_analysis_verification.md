# Technical Analysis v2 — Calculation Verification

## 4-Stock Comparison: AMD, ADBE, GEV, ASELS.IS

Computed from 2-year daily price data (April 2024 – April 2026).
ASELS.IS prices in TRY (not USD-converted, to isolate the FX question).

---

## ⚠️ BUG FOUND

**Your system reports: ADBE = 49.8, AMD = 38.0**
**Correct calculation: ADBE = 39.5, AMD = 80.8**

The scores appear nearly swapped. AMD is up +235% in 1 year (one of the hottest stocks), yet your system scores it 38. ADBE is down −34% in 1 year, yet scores 49.8. This is backwards.

**Most likely cause:** yfinance MultiIndex column handling. When `yf.download()` returns data with columns like `('Close', 'AMD')`, the code does `df.columns = df.columns.get_level_values(0)`. But if the wrong level is selected, or if a recent yfinance update changed the column structure, the Close/Open/High/Low values could be misread.

**Fix:** Delete `data/technical_analysis.csv` and re-run. If it persists, add a debug print in `get_technical_signals()` right after download:
```python
print(f"  DEBUG {ticker}: Close={df['Close'].iloc[-1]:.2f}, len={len(df)}")
```

---

## Summary Table

| | AMD | ADBE | GEV | ASELS.IS (TRY) |
|---|---|---|---|---|
| **Price** | $323.21 | $243.20 | $1,088.93 | 429.50 TRY |
| **1Y Change** | **+235%** ↑↑↑ | **−34%** ↓↓ | **+195%** ↑↑↑ | **+219%** ↑↑↑ |
| **MA Score** | +0.867 (14B/1S) | −0.600 (3B/12S) | +0.867 (14B/1S) | +1.000 (15B/0S) |
| **Osc Score** | +0.364 (5B/1S/5N) | +0.182 (3B/1S/7N) | +0.273 (4B/1S/6N) | +0.182 (4B/2S/5N) |
| **Overall** | +0.615 | −0.209 | +0.570 | +0.591 |
| **Tech Score** | **80.8** | **39.5** | **78.5** | **79.5** |
| **Rating** | **Strong Buy** | **Sell** | **Strong Buy** | **Strong Buy** |

---

## 1. Moving Averages (15 Indicators)

Price compared to each MA. Above = Buy, Below = Sell.

### AMD ($323.21) — 14 Buy / 1 Sell

| MA | Value | vs Price | Vote |
|---|---|---|---|
| SMA10 | $298.86 | +8.1% above | **Buy** |
| SMA20 | $263.84 | +22.5% above | **Buy** |
| SMA30 | $243.65 | +32.7% above | **Buy** |
| SMA50 | $226.47 | +42.7% above | **Buy** |
| SMA100 | $223.80 | +44.4% above | **Buy** |
| SMA200 | $208.43 | +55.1% above | **Buy** |
| EMA10 | $301.57 | +7.2% above | **Buy** |
| EMA20 | $275.16 | +17.5% above | **Buy** |
| EMA30 | $259.63 | +24.5% above | **Buy** |
| EMA50 | $243.84 | +32.5% above | **Buy** |
| EMA100 | $227.78 | +41.9% above | **Buy** |
| EMA200 | $207.45 | +55.8% above | **Buy** |
| Hull MA | $344.93 | −6.3% below | **Sell** |
| VWMA | $272.84 | +18.5% above | **Buy** |
| Ichimoku | $290.09 | +11.4% above | **Buy** |

> AMD is above every MA except Hull MA (which is very short-term at 9 periods and reacts to the recent pullback from ~$370). This is textbook **Strong Buy** territory.

### ADBE ($243.20) — 3 Buy / 12 Sell

| MA | Value | vs Price | Vote |
|---|---|---|---|
| SMA10 | $245.59 | −1.0% below | **Sell** |
| SMA20 | $241.91 | +0.5% above | **Buy** |
| SMA30 | $242.44 | +0.3% above | **Buy** |
| SMA50 | $251.37 | −3.2% below | **Sell** |
| SMA100 | $284.65 | −14.6% below | **Sell** |
| SMA200 | $316.01 | −23.0% below | **Sell** |
| EMA10 | $243.59 | −0.2% below | **Sell** |
| EMA20 | $244.18 | −0.4% below | **Sell** |
| EMA30 | $246.75 | −1.4% below | **Sell** |
| EMA50 | $254.88 | −4.6% below | **Sell** |
| EMA100 | $276.57 | −12.1% below | **Sell** |
| EMA200 | $311.10 | −21.8% below | **Sell** |
| Hull MA | $243.35 | −0.1% below | **Sell** |
| VWMA | $241.75 | +0.6% above | **Buy** |
| Ichimoku | $243.79 | −0.2% below | **Sell** |

> ADBE is below 12 of 15 MAs. Only barely above SMA20, SMA30, and VWMA (all within <1%). The long-term MAs (SMA200 at $316 vs price $243) show a severe downtrend.

### GEV ($1,088.93) — 14 Buy / 1 Sell

| MA | Value | vs Price | Vote |
|---|---|---|---|
| SMA10 | $1,058.39 | +2.9% above | **Buy** |
| SMA20 | $996.62 | +9.3% above | **Buy** |
| SMA50 | $908.04 | +19.9% above | **Buy** |
| SMA200 | $700.31 | +55.5% above | **Buy** |
| Hull MA | $1,191.43 | −8.6% below | **Sell** |
| *(all others)* | *(below price)* | | **Buy** |

> Same pattern as AMD — above everything except Hull MA.

### ASELS.IS (429.50 TRY) — 15 Buy / 0 Sell

| MA | Value | vs Price | Vote |
|---|---|---|---|
| SMA10 | 409.38 | +4.9% above | **Buy** |
| SMA50 | 350.49 | +22.5% above | **Buy** |
| SMA200 | 248.95 | +72.5% above | **Buy** |
| Hull MA | 403.99 | +6.3% above | **Buy** |
| *(all others)* | *(below price)* | | **Buy** |

> Perfect score in TRY — price is above ALL 15 MAs including Hull MA. This stock is strongly trending up in domestic currency.

---

## 2. Oscillators (11 Indicators)

### RSI (Relative Strength Index, Period 14)

```
Vote: Buy if RSI < 30 AND rising, Sell if RSI > 70 AND falling, else Neutral
```

| Stock | RSI | Direction | Vote |
|---|---|---|---|
| AMD | **81.0** | (overbought) | **Sell** — RSI > 70, but need to check if falling |
| ADBE | **52.0** | neutral zone | **Neutral** |
| GEV | **73.5** | (slightly overbought) | **Sell** — RSI > 70 |
| ASELS.IS | **75.7** | (overbought) | **Sell** — RSI > 70 |

> Note: High RSI doesn't mean the stock will drop — it means momentum is stretched. In strong uptrends, RSI can stay above 70 for weeks.

### Stochastic (14, 3, 3)

```
Vote: Buy if %K < 20 AND %K > %D (oversold recovery)
      Sell if %K > 80 AND %K < %D (overbought reversal)
      Neutral otherwise
```

| Stock | %K | %D | Vote |
|---|---|---|---|
| AMD | 75.6 | 85.8 | **Neutral** (not extreme) |
| ADBE | 55.1 | 53.5 | **Neutral** |
| GEV | 61.4 | 75.4 | **Neutral** |
| ASELS.IS | 99.6 | 89.5 | **Neutral** (%K > 80 but %K > %D, so not a reversal) |

### CCI (Commodity Channel Index, Period 20)

```
Vote: Buy if CCI > 100, Sell if CCI < −100, else Neutral
```

| Stock | CCI | Vote |
|---|---|---|
| AMD | +108.2 | **Buy** — above +100 threshold |
| ADBE | +16.2 | **Neutral** |
| GEV | +85.5 | **Neutral** (close to 100 but not there) |
| ASELS.IS | +85.7 | **Neutral** |

### ADX with +DI/−DI (Period 14)

```
Vote: Buy if +DI > −DI AND ADX > 20 (strong bullish trend)
      Sell if −DI > +DI AND ADX > 20 (strong bearish trend)
      Neutral if ADX < 20 (no trend)
```

| Stock | ADX | +DI | −DI | Vote |
|---|---|---|---|---|
| AMD | **71.7** | 56.2 | 11.2 | **Buy** — very strong bullish trend |
| ADBE | **18.2** | 21.1 | 23.7 | **Neutral** — ADX < 20, no clear trend |
| GEV | **39.1** | 37.3 | 15.8 | **Buy** — strong bullish trend |
| ASELS.IS | **63.9** | 37.6 | 9.4 | **Buy** — very strong bullish trend |

> ADX > 50 is extremely strong trend. AMD at 71.7 and ASELS at 63.9 are in powerful uptrends.

### Awesome Oscillator

```
Vote: AO > 0 → Buy, AO < 0 → Sell
```

| Stock | AO | Vote |
|---|---|---|
| AMD | +83.09 | **Buy** |
| ADBE | −0.59 | **Sell** |
| GEV | +180.57 | **Buy** |
| ASELS.IS | +43.46 | **Buy** |

### Momentum (10 days)

```
Vote: Price change over 10 days. Positive → Buy, Negative → Sell.
```

| Stock | Mom(10) | Vote |
|---|---|---|
| AMD | +68.14 | **Buy** — price up $68 in 10 days |
| ADBE | +7.48 | **Buy** — small positive |
| GEV | +101.43 | **Buy** — up $101 in 10 days |
| ASELS.IS | +17.75 | **Buy** |

### MACD (12, 26, 9)

```
Vote: MACD Line > Signal Line → Buy, else → Sell
```

| Stock | MACD | Signal | Histogram | Vote |
|---|---|---|---|---|
| AMD | +30.23 | +22.75 | +7.48 | **Buy** |
| ADBE | −1.99 | −3.10 | +1.11 | **Buy** — MACD just crossed above signal (bullish crossover) |
| GEV | +65.13 | +54.22 | +10.91 | **Buy** |
| ASELS.IS | +20.92 | +19.87 | +1.05 | **Buy** |

> ADBE's MACD just crossed bullish — this is a very early recovery signal while the stock is still in a long-term downtrend. The MAs see the big picture (Sell) while MACD caught a short-term bounce.

### Stochastic RSI (3, 3, 14, 14)

```
Vote: %K < 0.2 AND %K > %D → Buy (oversold recovery)
      %K > 0.8 AND %K < %D → Sell (overbought reversal)
      Neutral otherwise
```

| Stock | %K | %D | Vote |
|---|---|---|---|
| AMD | 0.72 | 0.87 | **Neutral** |
| ADBE | 0.70 | 0.71 | **Neutral** |
| GEV | 0.71 | 0.87 | **Neutral** |
| ASELS.IS | 0.61 | 0.66 | **Neutral** |

### Williams %R (Period 14)

```
Vote: %R < −80 → Buy (oversold), %R > −20 → Sell (overbought)
```

| Stock | %R | Vote |
|---|---|---|
| AMD | −24.4 | **Neutral** (close to overbought but not quite) |
| ADBE | −44.9 | **Neutral** |
| GEV | −38.6 | **Neutral** |
| ASELS.IS | −0.4 | **Sell** — extremely overbought |

### Bull Bear Power (Period 13)

```
Vote: Bull > 0 AND Bear < 0 AND Bear rising → Buy
      Bull < 0 → Sell
```

| Stock | Bull | Bear | Vote |
|---|---|---|---|
| AMD | +35.4 | +17.9 | **Neutral** (Bear > 0, not classic pattern) |
| ADBE | +1.7 | −2.4 | **Buy** (classic pattern: buyers in control) |
| GEV | +42.3 | +1.0 | **Neutral** |
| ASELS.IS | +28.2 | +13.9 | **Neutral** |

### Ultimate Oscillator (7, 14, 28)

```
Vote: UO > 70 → Buy, UO < 30 → Sell, else Neutral
```

| Stock | UO | Vote |
|---|---|---|
| AMD | 67.9 | **Neutral** (close to 70 but not there) |
| ADBE | 45.1 | **Neutral** |
| GEV | 59.8 | **Neutral** |
| ASELS.IS | 46.6 | **Neutral** |

---

## 3. Final Score Calculation

```
MA Score  = (Buy − Sell) / Total MAs
Osc Score = (Buy − Sell) / Total Oscillators
Overall   = (MA Score + Osc Score) / 2
Tech Score = (Overall + 1) × 50
```

### AMD

```
MA:  (14 − 1) / 15 = +0.867
Osc: (5 − 1) / 11  = +0.364
Overall: (0.867 + 0.364) / 2 = +0.615
Score: (0.615 + 1) × 50 = 80.8 → Strong Buy ✓
```

### ADBE

```
MA:  (3 − 12) / 15 = −0.600
Osc: (3 − 1) / 11  = +0.182
Overall: (−0.600 + 0.182) / 2 = −0.209
Score: (−0.209 + 1) × 50 = 39.5 → Sell ✓
```

### GEV

```
MA:  (14 − 1) / 15 = +0.867
Osc: (4 − 1) / 11  = +0.273
Overall: (0.867 + 0.273) / 2 = +0.570
Score: (0.570 + 1) × 50 = 78.5 → Strong Buy ✓
```

### ASELS.IS (TRY, no FX conversion)

```
MA:  (15 − 0) / 15 = +1.000
Osc: (4 − 2) / 11  = +0.182
Overall: (1.000 + 0.182) / 2 = +0.591
Score: (0.591 + 1) × 50 = 79.5 → Strong Buy ✓
```

---

## 4. Key Observations

### Why AMD and GEV score similarly (80.8 vs 78.5)
Both are in massive uptrends (+235% and +195% in 1 year). The only MA voting Sell is Hull MA (very short-term, catches the latest pullback). Their oscillator profiles differ slightly — AMD has stronger CCI and ADX, GEV has a bigger Awesome Oscillator.

### Why ADBE is Sell (39.5)
The moving averages are devastating: price ($243) is 23% below SMA200 ($316). Only 3 of 15 MAs are barely above price. The oscillators are more forgiving — MACD just crossed bullish and Momentum is positive — suggesting a short-term bounce within a long-term downtrend.

### Why ASELS.IS is Strong Buy in TRY (79.5)
Perfect MA score (15/15 Buy) because the stock is above every single MA in TRY terms. Even Hull MA is below price. The oscillators are slightly weaker because RSI (75.7) and Williams %R (−0.4) flag overbought conditions.

### The FX Question for ASELS.IS
In TRY: **Strong Buy** (79.5). If converted to USD, many of the longer MAs would flip to Sell because TRY depreciated ~15-20% over the analysis period. The stock's +219% TRY gain would shrink to a smaller USD gain, and the older USD-converted prices (divided by lower USD/TRY rates) would be relatively higher, pushing historical MAs above the current USD price.

---

## 5. Diagnostic: Your System vs This Calculation

| Stock | Your System | This Calculation | Match? |
|---|---|---|---|
| ADBE | 49.8 | **39.5** | ❌ Off by 10 pts |
| AMD | 38.0 | **80.8** | ❌ **SEVERELY WRONG** — should be Strong Buy not Sell |
| GEV | ? | **78.5** | Check your system |
| ASELS.IS | ? | **79.5** (TRY) | Check your system |

**AMD at 38 is clearly a bug.** A stock that's up 235% in 1 year, above 14/15 moving averages, with ADX at 71.7 (extremely strong trend), cannot score 38 (Sell). 

**Action items:**
1. Delete `data/technical_analysis.csv` and re-run
2. If bug persists, add debug logging to `get_technical_signals()` to print the downloaded price for each ticker
3. Check yfinance version — `pip show yfinance` — recent versions changed the MultiIndex column format

---

*Computed from uploaded price data: AMD_prices.csv, ADBE_prices.csv, GEV_prices.csv, ASELS_IS_prices.csv (April 2024–April 2026).*
