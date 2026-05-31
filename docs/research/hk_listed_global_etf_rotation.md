# HK-listed Global ETF Rotation Research Note

## Scope

This note evaluates a Hong Kong-listed version of a global ETF rotation strategy. The goal is not to trade US ETFs directly, but to use ETFs listed and tradable on HKEX while still getting exposure to overseas / cross-asset regimes.

This research is now implemented as disabled profile `hk_listed_global_etf_rotation`. It remains a `research_candidate`, not `runtime_enabled`, because broker feed/tradability, spreads, lot sizes, derivative ETF suitability, and currency-line selection still need platform dry-run validation.

## ETF universe tested

Baseline universe with enough overlapping history from the Hang Seng TECH ETF launch window:

| Symbol | Yahoo symbol | Exposure | Notes |
| --- | --- | --- | --- |
| `02800` | `2800.HK` | Hong Kong / HSI | Local equity beta |
| `02822` | `2822.HK` | China A50 | Mainland large-cap equity beta |
| `03188` | `3188.HK` | CSI 300 | Mainland broad equity beta |
| `03033` | `3033.HK` | Hang Seng TECH | Hong Kong-listed technology beta |
| `02834` | `2834.HK` | Nasdaq 100 | HK-listed overseas growth equity exposure |
| `02840` | `2840.HK` | Gold | Defensive / inflation hedge |
| `03175` | `3175.HK` | Crude oil futures | Commodity trend exposure; derivative ETF |
| `03110` | `3110.HK` | HK high dividend | Defensive HK equity style exposure |

Watchlist / excluded from this baseline:

| Symbol | Reason |
| --- | --- |
| `03010` | iShares Core MSCI Asia ex Japan ETF is relevant, but the Yahoo-adjusted series had a large discontinuity in this run, so it needs data cleaning before use. |
| `03195` | Hang Seng S&P 500 Index ETF is relevant, but its HKEX authorisation / listing history only gives a short sample for this 2021-2026 backtest window. |
| `03040` | Global X MSCI China ETF has short public history in this data pull. |
| `03442` | CSOP Hang Seng HK-US TECH ETF has short public history in this data pull. |

Official listing references used to confirm the HK-listed instruments include HKEX IFP pages for iShares Nasdaq 100 ETF (`02834` / `09834`), Samsung S&P GSCI Crude Oil ER Futures ETF (`03175`), Global X Hang Seng High Dividend Yield ETF (`03110` / `83110`), iShares Core MSCI Asia ex Japan ETF (`03010` / `83010` / `09010`), Hang Seng S&P 500 Index ETF (`03195` / `09195`), and SPDR Gold Trust (`02840` / `09840` / `82840`).

Reference pages:

- HKEX IFP, iShares Nasdaq 100 ETF: https://ifp.hkex.com.hk/fund/BHG161
- HKEX IFP, Samsung S&P GSCI Crude Oil ER Futures ETF: https://ifp.hkex.com.hk/fund/BGT085
- HKEX IFP, Global X Hang Seng High Dividend Yield ETF: https://ifp.hkex.com.hk/fund/BAR386
- HKEX IFP, iShares Core MSCI Asia ex Japan ETF: https://ifp.hkex.com.hk/fund/ARO977
- HKEX IFP, Hang Seng S&P 500 Index ETF: https://ifp.hkex.com.hk/fund/BUP049
- HKEX IFP, SPDR Gold Trust: https://ifp.hkex.com.hk/fund/AQY071
- Yahoo Finance history for `2834.HK`: https://finance.yahoo.com/quote/2834.HK/history/
- Yahoo Finance history for `3175.HK`: https://finance.yahoo.com/quote/3175.HK/history/
- Yahoo Finance history for `3110.HK`: https://finance.yahoo.com/quote/3110.HK/history/
- Yahoo Finance history for `2800.HK`: https://finance.yahoo.com/quote/2800.HK/history/
- Yahoo Finance history for `2840.HK`: https://finance.yahoo.com/quote/2840.HK/history/

## Methodology

- Price source: Yahoo Finance adjusted daily close via `yfinance`.
- Backtest script: `scripts/research_hk_listed_global_etf_rotation_backtest.py`.
- Sample used for scoring: `2021-09-01` to `2026-05-29`, after a 252 trading-day warmup.
- Cost assumption: 10 bps per 100% turnover.
- Split discipline:
  - Train / parameter selection: `2021-09-01` to `2023-12-29`.
  - Out-of-sample check: `2024-01-01` to `2026-05-29`.
- Grid reviewed: 63/126/252 day momentum, 100/200 day trend filter, 63/126 day volatility, top 1/2/3 ETFs, monthly/weekly cadence, equal/inverse-volatility weighting.
- Selected version: monthly review, 252-day momentum, 200-day trend filter, 63-day volatility, top 2 ETFs, inverse-volatility weights, 16% target annual volatility, 100% max gross exposure.

The highest-return unscaled version had deeper drawdowns. The selected implementation keeps the same monthly top-2 structure but adds a 16% volatility target, which lowered full-sample max drawdown below 30% and kept train-period drawdown below 30%.

## Selected conservative version

| Parameter | Value |
| --- | ---: |
| Rebalance review | monthly |
| Momentum window | 252 trading days |
| Trend filter | price above 200-day moving average |
| Volatility window | 63 trading days |
| Selected ETFs | top 2 eligible ETFs |
| Minimum momentum | > 0 |
| Weighting | inverse volatility |
| Target annual volatility | 16% |
| Max gross exposure | 100% |
| Cost assumption | 10 bps turnover |

Signal summary:

- Compute 252-day momentum, 200-day trend, and 63-day realized volatility for each ETF.
- Eligible ETFs must have positive 252-day momentum and trade above the 200-day moving average.
- Rank eligible ETFs by momentum divided by volatility.
- Hold the top 2 ETFs using inverse-volatility weights.
- Scale the portfolio down if the trailing covariance estimate implies annualized volatility above 16%.
- If no ETF is eligible, hold cash.

## Backtest results

Strategy metrics from `scripts/research_hk_listed_global_etf_rotation_backtest.py`:

| Period | Annualized return | Max drawdown | Total return |
| --- | ---: | ---: | ---: |
| Full sample, 2021-09-01 to 2026-05-29 | 18.84% | -20.51% | 121.62% |
| Train, 2021-09-01 to 2023-12-29 | 3.69% | -20.51% | 8.58% |
| Out-of-sample, 2024-01-01 to 2026-05-29 | 35.62% | -8.07% | 104.10% |
| Trailing 1Y, 2025-05-30 to 2026-05-29 | 41.69% | -8.07% | 40.52% |
| Trailing 3Y, 2023-05-30 to 2026-05-29 | 29.32% | -10.37% | 111.91% |
| 2021 warmup-truncated | 26.94% | -8.02% | 8.17% |
| 2022 | -1.45% | -16.39% | -1.41% |
| 2023 | 1.88% | -13.73% | 1.81% |
| 2024 | 21.32% | -7.43% | 20.76% |
| 2025 | 46.23% | -7.12% | 44.92% |
| 2026 YTD to 2026-05-29 | 48.50% | -8.07% | 16.62% |

Benchmarks over the full sample:

| Benchmark | Annualized return | Max drawdown |
| --- | ---: | ---: |
| `02800` HSI ETF buy-and-hold | 2.76% | -41.66% |
| `02822` A50 ETF buy-and-hold | 1.58% | -40.48% |
| `03188` CSI 300 ETF buy-and-hold | 0.72% | -43.30% |
| `03033` Hang Seng TECH ETF buy-and-hold | -6.86% | -59.53% |
| `02834` Nasdaq 100 ETF buy-and-hold | 15.94% | -35.03% |
| `02840` gold ETF buy-and-hold | 21.74% | -23.34% |
| `03175` crude oil futures ETF buy-and-hold | 18.84% | -39.18% |
| `03110` high-dividend ETF buy-and-hold | 11.09% | -32.75% |
| Static equal-weight ETF basket | 10.03% | -27.81% |

Other diagnostics:

| Metric | Value |
| --- | ---: |
| Average gross exposure | 82.29% |
| Average daily turnover | 1.81% |
| Latest target weights on 2026-05-29 | `02834`: 35.43%, `03110`: 54.19% |

## Comparison with current `hk_etf_regime_rotation`

Current HK/China/gold/high-dividend ETF basket result:

| Strategy | Annualized return | Max drawdown | Train return | OOS return |
| --- | ---: | ---: | ---: | ---: |
| Existing `hk_etf_regime_rotation` | 13.55% | -21.56% | -7.24% | 38.18% |
| `hk_listed_global_etf_rotation` | 18.84% | -20.51% | 3.69% | 35.62% |

Interpretation:

- Adding HK-listed Nasdaq 100 and crude-oil ETF exposure plus a 16% volatility target improves the full-sample annualized return from 13.55% to 18.84%.
- Full-sample max drawdown improves from -21.56% to -20.51%, keeping the research target under 30%.
- Train period turns positive at 3.69% annualized, while OOS annualized return remains strong at 35.62%.
- The result is still not live-ready because ETF tradability, fees, spread, lot-size, derivative ETF treatment, and currency-line handling are not yet validated on both platforms.

## Decision

Add as disabled `research_candidate` profile `hk_listed_global_etf_rotation`.

Recommended status: eligible but disabled; do not mark `runtime_enabled` yet.

Reasons:

1. The selected volatility-targeted version keeps full-sample and train max drawdown below 30%.
2. It improves full-sample annualized return versus the existing HK ETF regime rotation while keeping turnover low.
3. Several important global exposures are still either too new (`03195`) or need data cleaning (`03010`).
4. Broker tradability, ETF spread, lot size, derivative ETF suitability, currency line selection, and stamp-duty exemption must be checked per symbol before any platform dry run.

Next low-risk step if we want to promote it later:

1. Clean and validate `03010` corporate-action / adjusted-price history.
2. Re-run after `03195` has a longer S&P 500 sample.
3. Add ETF-level liquidity and spread filters instead of treating all ETFs equally.
4. Keep `hk_listed_global_etf_rotation` disabled until both IBKR and LongBridge dry-run checks confirm symbol feed, sizing, and order conversion behavior.
