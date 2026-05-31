# HK Index Mean Reversion Research Candidate


## 中文摘要

- 用途：本文档围绕 `HK Index Mean Reversion Research Candidate`，用于理解 `HkEquityStrategies` 的配置、运行、部署、研究或验收边界。
- 主要覆盖：`Scope`、`Data and methodology`、`Selected version`、`Backtest results`、`Decision`。
- 阅读顺序：先确认边界、输入输出和权限要求，再执行文档里的命令、CI、dry-run、发布或切换步骤。
- 风险提示：涉及实盘、密钥、权限、Cloud Run、交易所或券商 API 的变更，必须先在测试环境或 dry-run 验证；不要只凭示例直接修改生产。
- 英文正文保留更完整的命令、字段名和配置键；如果摘要和正文不一致，以正文中的实际命令和配置为准。

## Scope

This research evaluates a first non-snapshot `hk_equity` profile candidate: `hk_index_mean_reversion`.

The strategy is a long-only relative mean-reversion sleeve between:

- `02800` / `2800.HK`: Tracker Fund of Hong Kong, used as the HSI anchor.
- `03033` / `3033.HK`: CSOP Hang Seng TECH Index ETF, used as the Hang Seng TECH satellite.

The profile is intentionally marked `research_candidate`, not `runtime_enabled`. The backtest does not justify production trading yet.

## Data and methodology

- Price source: Yahoo Finance adjusted daily close via `yfinance` for `2800.HK` and `3033.HK`.
- Sample: `2020-08-27` to `2026-05-29`, constrained by available `3033.HK` history.
- Cost assumption: 10 bps per 100% turnover.
- Split discipline:
  - Train / parameter selection: `2020-08-27` to `2023-12-29`.
  - Out-of-sample check: `2024-01-01` to `2026-05-29`.
- The parameter grid was deliberately small: 40/60/80/120 day spread windows, simple z-score thresholds, weekly/monthly cadence, and coarse allocation bands.
- Selected version favors drawdown control and parameter simplicity rather than the highest out-of-sample number.

Reference pages:

- Tracker Fund of Hong Kong: https://www.trahk.com.hk/en-hk/trahk-fund/
- CSOP Hang Seng TECH Index ETF `3033`: https://csop.onlineminisite.com/thematicetf/en/3033.php
- Yahoo Finance history for `2800.HK`: https://finance.yahoo.com/quote/2800.HK/history/
- Yahoo Finance history for `3033.HK`: https://finance.yahoo.com/quote/3033.HK/history/

## Selected version

Current defaults:

| Parameter | Value |
| --- | ---: |
| Rebalance review | weekly |
| Spread lookback | 80 trading days |
| Entry z-score | 1.0 |
| Exit z-score | 0.25 |
| Neutral satellite weight | 50% |
| HSTECH oversold satellite weight | 65% |
| HSTECH rich satellite weight | 5% |
| Trend window | 200 trading days |
| Defensive gross exposure | 25% |
| Defensive satellite weight | 0% |
| Cost assumption | 10 bps turnover |

Signal summary:

- Compute `z = zscore(log(03033 / 02800))`.
- If `z <= -1.0`, treat Hang Seng TECH as relatively cheap and overweight `03033`.
- If `z >= 1.0`, treat Hang Seng TECH as relatively rich and mostly hold `02800`.
- If both ETFs are below 200-day moving averages, cut gross exposure to 25% and keep the satellite at 0%.

## Backtest results

Strategy metrics from `scripts/research_hk_index_mean_reversion_backtest.py`:

| Period | Annualized return | Max drawdown | Total return |
| --- | ---: | ---: | ---: |
| Full sample, 2020-08-27 to 2026-05-29 | 0.26% | -48.71% | 1.46% |
| Train, 2020-08-27 to 2023-12-29 | -9.51% | -46.95% | -27.83% |
| Out-of-sample, 2024-01-01 to 2026-05-29 | 15.69% | -22.93% | 40.58% |
| Trailing 1Y, 2025-05-30 to 2026-05-29 | -0.95% | -17.09% | -0.92% |
| Trailing 3Y, 2023-05-30 to 2026-05-29 | 8.58% | -22.93% | 27.13% |
| 2021 | -16.65% | -33.72% | -16.35% |
| 2022 | -3.89% | -10.87% | -3.80% |
| 2023 | -19.14% | -30.25% | -18.53% |
| 2024 | 21.16% | -16.95% | 20.61% |
| 2025 | 26.30% | -22.93% | 25.48% |
| 2026 YTD to 2026-05-29 | -17.27% | -15.27% | -7.11% |

Benchmarks over the full sample:

| Benchmark | Annualized return | Max drawdown |
| --- | ---: | ---: |
| `02800` HSI ETF buy-and-hold | 3.28% | -49.39% |
| `03033` HSTECH ETF buy-and-hold | -7.81% | -74.73% |
| Static 50/50 `02800` / `03033` | -1.94% | -63.55% |

## Decision

Do not promote this profile to `runtime_enabled` yet.

Reasons:

- The idea did show better drawdown than a static 50/50 mix and worked well in 2024-2025.
- But the full-sample annualized return is close to flat and below `02800` buy-and-hold.
- The train period was negative, especially 2021 and 2023, so the edge is not stable enough for live deployment.
- Current implementation is useful as the first non-snapshot architecture candidate because it exercises direct `market_history` inputs without snapshot artifacts.

Promotion requirements before live trading:

1. Validate platform `market_history` feed for `02800` and `03033` on both IBKR and LongBridge.
2. Re-run with broker-realistic trading costs, lot sizes, stamp/levy/fee handling, and dividend treatment.
3. Add a true HKD cash or money-market parking instrument if the platform requires full target allocation.
4. Require at least one more out-of-sample year or paper trading period before setting `status=runtime_enabled`.
