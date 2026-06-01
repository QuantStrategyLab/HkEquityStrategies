# HK ETF Regime Rotation Research Candidate


## 中文摘要

- 用途：本文档围绕 `HK ETF Regime Rotation Research Candidate`，用于理解 `HkEquityStrategies` 的配置、运行、部署、研究或验收边界。
- 主要覆盖：`Scope`、`Data and methodology`、`Selected version`、`Backtest results`、`Decision`。
- 阅读顺序：先确认边界、输入输出和权限要求，再执行文档里的命令、CI、dry-run、发布或切换步骤。
- 风险提示：涉及实盘、密钥、权限、Cloud Run、交易所或券商 API 的变更，必须先在测试环境或 dry-run 验证；不要只凭示例直接修改生产。
- 英文正文保留更完整的命令、字段名和配置键；如果摘要和正文不一致，以正文中的实际命令和配置为准。

## Scope

This research evaluates a low-turnover non-snapshot `hk_equity` profile candidate: `hk_etf_regime_rotation`.

The strategy rotates across a small HK-listed ETF universe:

- `02800` / `2800.HK`: Tracker Fund of Hong Kong, HSI exposure.
- `02822` / `2822.HK`: CSOP FTSE China A50 ETF.
- `02840` / `2840.HK`: SPDR Gold Shares.
- `03033` / `3033.HK`: CSOP Hang Seng TECH Index ETF.
- `03110` / `3110.HK`: Global X Hang Seng High Dividend Yield ETF.
- `03188` / `3188.HK`: ChinaAMC CSI 300 Index ETF.

This remains research/backtest-only and is not registered as a runtime catalog profile. The results are more promising than `hk_index_mean_reversion`, but the default six-ETF train period is still negative.

## Data and methodology

- Price source: Yahoo Finance adjusted daily close via `yfinance` for the six HK-listed ETFs above.
- Sample used for scoring: `2021-09-01` to `2026-05-29`, after the 252 trading-day warmup window.
- Cost assumption: 10 bps per 100% turnover.
- Split discipline:
  - Train / parameter selection: `2021-09-01` to `2023-12-29`.
  - Out-of-sample check: `2024-01-01` to `2026-05-29`.
- The tested grid was deliberately small: 63/126/252 day momentum, 100/200 day trend filter, 63/126 day volatility, top 1/2/3 ETFs, monthly/weekly cadence, equal/inverse-volatility weighting.
- Selected version favors lower turnover and drawdown control rather than the highest out-of-sample return.

Reference pages:

- Yahoo Finance history for `2800.HK`: https://finance.yahoo.com/quote/2800.HK/history/
- Yahoo Finance history for `2822.HK`: https://finance.yahoo.com/quote/2822.HK/history/
- Yahoo Finance history for `2840.HK`: https://finance.yahoo.com/quote/2840.HK/history/
- Yahoo Finance history for `3033.HK`: https://finance.yahoo.com/quote/3033.HK/history/
- Yahoo Finance history for `3110.HK`: https://finance.yahoo.com/quote/3110.HK/history/
- Yahoo Finance history for `3188.HK`: https://finance.yahoo.com/quote/3188.HK/history/

## Selected version

Current defaults:

| Parameter | Value |
| --- | ---: |
| Rebalance review | monthly |
| Momentum window | 252 trading days |
| Trend filter | price above 200-day moving average |
| Volatility window | 63 trading days |
| Selected ETFs | top 2 eligible ETFs |
| Minimum momentum | > 0 |
| Weighting | inverse volatility |
| Cost assumption | 10 bps turnover |

Signal summary:

- Compute 252-day momentum, 200-day trend, and 63-day realized volatility for each ETF.
- Eligible ETFs must have positive 252-day momentum and trade above the 200-day moving average.
- Rank eligible ETFs by momentum divided by volatility.
- Hold the top 2 ETFs using inverse-volatility weights.
- If no ETF is eligible, hold cash.

## Backtest results

Strategy metrics from `scripts/research_hk_etf_regime_rotation_backtest.py`:

| Period | Annualized return | Max drawdown | Total return |
| --- | ---: | ---: | ---: |
| Full sample, 2021-09-01 to 2026-05-29 | 13.55% | -21.56% | 79.57% |
| Train, 2021-09-01 to 2023-12-29 | -7.24% | -21.56% | -15.68% |
| Out-of-sample, 2024-01-01 to 2026-05-29 | 38.18% | -8.74% | 112.95% |
| Trailing 1Y, 2025-05-30 to 2026-05-29 | 40.91% | -8.07% | 39.58% |
| Trailing 3Y, 2023-05-30 to 2026-05-29 | 27.77% | -11.95% | 104.37% |
| 2021 warmup-truncated | 0.00% | 0.00% | 0.00% |
| 2022 | -10.54% | -13.66% | -10.30% |
| 2023 | -6.21% | -18.74% | -5.99% |
| 2024 | 26.11% | -8.74% | 25.42% |
| 2025 | 50.04% | -7.12% | 48.35% |
| 2026 YTD to 2026-05-29 | 41.50% | -8.07% | 14.45% |

Benchmarks over the full sample:

| Benchmark | Annualized return | Max drawdown |
| --- | ---: | ---: |
| `02800` HSI ETF buy-and-hold | 2.76% | -41.66% |
| `03033` HSTECH ETF buy-and-hold | -6.87% | -59.53% |
| `02840` gold ETF buy-and-hold | 21.76% | -23.34% |
| `03110` high-dividend ETF buy-and-hold | 11.10% | -32.75% |
| Static equal-weight ETF basket | 6.04% | -35.92% |

Other diagnostics:

| Metric | Value |
| --- | ---: |
| Average gross exposure | 75.02% |
| Average daily turnover | 1.46% |
| Latest target weights on 2026-05-29 | `03110`: 53.02%, `03188`: 46.98% |

Robustness variants from the same script:

| Variant | Full annualized return | Full max drawdown | Train annualized return | OOS annualized return | Notes |
| --- | ---: | ---: | ---: | ---: | --- |
| Default six-ETF version | 13.55% | -21.56% | -7.24% | 38.18% | Selected low-turnover baseline, but train period is negative. |
| No-gold, same parameters | 6.59% | -24.69% | -9.85% | 25.42% | Still profitable, but materially worse than the version with `02840`. |
| Top-1 with gold | 11.04% | -17.51% | -5.16% | 29.40% | Lower drawdown than default, but train period remains negative. |
| 126-day momentum | 13.53% | -19.87% | -7.27% | 38.19% | Similar full-sample return, but train period remains negative. |
| High-dividend / gold pair | 17.94% | -11.28% | 3.07% | 34.43% | Strongest risk-adjusted raw variant; implemented separately as `hk_high_dividend_low_vol_trend`. |
| High-dividend / gold pair, 12% vol target | 17.16% | -8.06% | 3.18% | 32.54% | Lower drawdown; promoted separately as the live-enabled `hk_high_dividend_low_vol_trend` profile. |

## Decision

Keep this strategy as research/backtest-only; do not register it as a runtime catalog profile.

Reasons to continue research:

- Full-sample return and drawdown are materially better than `02800`, `03033`, and a static equal-weight ETF basket.
- Turnover is low enough for HK's higher cost structure.
- The implementation uses the same direct `market_history` contract as `hk_index_mean_reversion`, so platform integration risk is contained.
- Variant checks show the idea does not depend only on one exact parameter set, but gold exposure remains important.

Reasons not to promote yet:

- Default train period `2021-09-01` to `2023-12-29` was negative.
- The strong out-of-sample result is heavily influenced by the 2024-2026 regime.
- The conservative optimization sweep did not find a broad six-ETF variant with positive train-period return under the current constraints.
- The strongest high-dividend / gold variant has only two ETFs and is promoted through its own simpler profile instead of this broader profile.
- ETF-specific fee, stamp-duty exemption, spread, lot size, and platform tradability must be validated per symbol.
- Cash handling must be validated with both IBKR and LongBridge if no ETF passes the filter.

Promotion requirements before live trading:

1. Validate platform `market_history` feed for all six ETFs on both IBKR and LongBridge.
2. Re-run with broker-realistic fees, spread/slippage, lot sizes, trading suspensions, and dividend treatment.
3. Add paper-trading evidence across at least one additional regime.
4. Keep it out of the runtime catalog until the platform dry run confirms symbol tradability and order sizing.
