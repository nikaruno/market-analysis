# BIST USD Conversion + Dual Technical Rating — Change Summary

This update implements the FX conversion item from the project handoff. Quality
metrics for BIST stocks are now computed on **USD-converted** financial
statements, while technical analysis provides a **dual rating**: a primary TL
(native) rating that matches TradingView and a secondary USD rating for what a
USD-based investor experiences.

## Files added

### `src/exMarket/fx_rates.py` (new, ~250 lines)
Helper module that downloads daily USD/TRY rates from yfinance (`USDTRY=X`)
and caches them in `data/fx/usdtry_daily.csv` with a 24-hour TTL.

Public functions:
- `load_or_download_rates(force_refresh=False)` — main entry; returns DataFrame
  indexed by date with column `usdtry`. Returns empty DataFrame on irrecoverable
  failure (callers should fall back to no conversion).
- `is_available()` — quick yes/no check before calling other functions.
- `get_yearly_avg(year)` / `get_year_end(year)` — for income/balance respectively.
- `get_rate_for_period_end(date)` — last available rate on or before a date.
- `convert_statement_columns(df, method)` — divides every numeric column by
  the appropriate rate (`yearly_avg` for income/cashflow, `period_end` for
  balance).
- `convert_price_series(prices)` / `convert_ohlcv(df)` — daily-spot price
  conversion for technical analysis. Volume is preserved unchanged.

Stale cache is reused if a fresh download fails. If FX is fully unavailable,
returns the original (TRY) values unchanged so downstream code keeps working.

## Files modified

### `src/exMarket/compute_detailed_metrics.py`
Lazy-imports `fx_rates`. Inside `compute_metrics`, after putting statements
into chronological order:
- if `region == "turkey"` and FX is available, converts:
  - **Income statement** → `yearly_avg` rate
  - **Cash flow** → `yearly_avg` rate
  - **Balance sheet** → `period_end` rate
- adds a `currency` field to the output dict so each row is auditable
  (e.g. `"USD (from TRY)"`, `"TRY (FX unavailable)"`, `"USD"` for non-BIST).

The conversion fixes the main BIST fairness problem: Revenue/NI CAGR
in TRY include ~30%/yr currency depreciation (a 50% TRY CAGR can be only
~20% in real USD terms). Margin ratios (ROIC, FCF margin) are unit-free and
remain virtually unchanged.

### `src/exMarket/technical_analysis.py`
- Lazy-imports `fx_rates`.
- Adds `_compute_ratings_only(df)` — extracts the voting-system computation
  from `get_technical_signals` so it can be reused on any OHLCV frame.
- After computing the primary (TL for BIST) ratings, if the ticker ends with
  `.IS` and FX is available, also runs `_compute_ratings_only` on
  `fx_rates.convert_ohlcv(df)` and merges the result into the output as
  `*_usd` columns (`technical_score_usd`, `technical_rating_usd`,
  `ma_buy_usd`, `ma_sell_usd`, `osc_buy_usd`, `osc_sell_usd`,
  `ma_rating_usd`, `osc_rating_usd`, `overall_rating_usd`).
- Adds two new flag columns: `currency` (`"TRY"` or `"USD"`) and
  `has_usd_rating` (bool).

The primary rating path is **completely unchanged** for non-BIST stocks. For
BIST, the primary (TL) rating is also unchanged — the USD figures are added
in a second pass and stored alongside.

### `gui/app.py`
- **Tab 3 (Technical Analysis)**: BIST table now shows `Tech (TL) | Rating (TL)
  | Tech (USD) | Rating (USD)` columns when USD ratings are available.
  Subheader is updated to "Dual Rating (TL primary, USD secondary)" with a
  caption explaining why USD ratings tend to be lower.
- **Tab 4 (Company Lookup)**: for BIST tickers with USD ratings, a second
  metric row shows "Tech Score (USD), Rating (USD), Δ vs TL" so users can
  see the gap.
- **Tab 1/2 BIST sections**: relabeled "BIST Stocks (TL)" → "BIST Stocks
  (fundamentals in USD)" since quality scores now use converted statements.
- **Tab 5 (Help)**: new "🇹🇷 BIST / USD Conversion" expander documenting
  what gets converted with which rate.
- Footer: "BIST Support" → "BIST USD Conversion".

### `automation_scripts/automate_analysis_with_tech.py`
Adds a small FX warm-up at the start of the pipeline that pre-fetches the
USD/TRY cache (or warns clearly if it's unavailable). This way users see FX
status before the long fundamentals/technical steps run.

### `automation_scripts/report_generator_enhanced.py`
- Methodology section updated from v2 to v3 (8 metrics, EMA-weighted, no
  Interest Coverage).
- Added a new methodology subsection documenting BIST USD conversion.
- BIST report header changed from "Borsa Istanbul — TL" to "Borsa
  Istanbul — fundamentals in USD" with a caveat that technicals stay in TL.
- Added a new "🇹🇷 BIST Dual Rating" table in Section 3 that compares
  TL vs USD scores and ratings side by side.

## Behavior summary

| Scenario | What happens |
|---|---|
| US stock, FX available | No change — exactly as before |
| US stock, FX unavailable | No change — exactly as before |
| BIST stock, FX available | Fundamentals computed on USD, primary tech in TL, secondary tech in USD |
| BIST stock, FX unavailable | Fundamentals fall back to TRY (with warning + audit tag), tech stays TL only |

## Things to verify after deploying

1. **First run will download ~7 years of USD/TRY** (one yfinance call,
   cached to `data/fx/usdtry_daily.csv`). Subsequent runs reuse for 24h.
2. **BIST quality scores will change** vs the previous version because
   revenue/NI CAGR are now realistic. Expect BIST stocks with high TRY-CAGR
   but flat USD growth to drop.
3. **BIST technical TL ratings should be identical** to the previous
   version — only the secondary USD columns are new. If TL ratings change,
   that's a regression to investigate.
4. **The "currency" column in `company_metrics.csv`** is the audit trail.
   Spot-check one BIST row to confirm it says `"USD (from TRY)"`.
5. **`technical_analysis.csv` for BIST tickers** should have populated
   `*_usd` columns. For non-BIST, those columns will be NaN.
