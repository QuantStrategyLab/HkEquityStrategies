# HK Index Mean Reversion Research Candidate


## 中文摘要

- 用途：本文档围绕 `HK Index Mean Reversion Research Candidate`，用于理解 `HkEquityStrategies` 的配置、运行、部署、研究或验收边界。
- 主要覆盖：`Scope`、`Data and methodology`、`Selected version`、`Backtest results`、`Decision`。
- 阅读顺序：先确认边界、输入输出和权限要求，再执行文档里的命令、CI、dry-run、发布或切换步骤。
- 风险提示：涉及实盘、密钥、权限、Cloud Run、交易所或券商 API 的变更，必须先在测试环境或 dry-run 验证；不要只凭示例直接修改生产。
- 英文正文保留更完整的命令、字段名和配置键；如果摘要和正文不一致，以正文中的实际命令和配置为准。

## Scope

This research evaluates a first non-snapshot `hk_equity` research/backtest candidate: `hk_index_mean_reversion`.

The strategy is a long-only relative mean-reversion sleeve between:

- `02800` / `2800.HK`: Tracker Fund of Hong Kong, used as the HSI anchor.
- `03033` / `3033.HK`: CSOP Hang Seng TECH Index ETF, used as the Hang Seng TECH satellite.

This remains research/backtest-only and is not registered as a runtime catalog profile. The backtest does not justify production trading yet.

## Data and methodology

- Price source: Yahoo Finance adjusted daily close via `yfinance` for `2800.HK` and `3033.HK`.
- Sample: `2020-08-27` to `2026-05-29`, constrained by available `3033.HK` history.
- Cost assumption: 10 bps per 100% turnover.
- Split discipline:
  - Train / parameter selection: `2020-08-27` to `2023-12-29`.
  - Out-of-sample check: `2024-01-01` to `2026-05-29`.
- The parameter grid was deliberately small: 40/60/80/120 day spread windows, simple z-score thresholds, weekly/monthly cadence, coarse allocation bands, and a small set of 200-day moving-average regime filters.
- Selected version favors drawdown control and parameter simplicity rather than the highest out-of-sample number.

Reference pages:

- Tracker Fund of Hong Kong: https://www.trahk.com.hk/en-hk/trahk-fund/
- CSOP Hang Seng TECH Index ETF `3033`: https://csop.onlineminisite.com/thematicetf/en/3033.php
- Yahoo Finance history for `2800.HK`: https://finance.yahoo.com/quote/2800.HK/history/
- Yahoo Finance history for `3033.HK`: https://finance.yahoo.com/quote/3033.HK/history/
- CSOP HSI 2x leveraged product `7200`: https://stockanalysis.com/quote/hkg/7200/
- CSOP HSI -2x inverse product `7500`: https://hk.investing.com/etfs/csop-hang-seng-index-daily-2x-inv
- CSOP Hang Seng TECH 2x leveraged product `7226`: https://www.csopasset.com/en/products/hk-hst-l
- HKEX circular listing Hang Seng TECH 2x / -2x products `7226` and `7552`: https://www.hkex.com.hk/-/media/HKEX-Market/Services/Circulars-and-Notices/Participant-and-Members-Circulars/SEHK/2020/ce_SEHK_CT_137_2020.pdf

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
| Defensive trigger | `02800` below its 200-day moving average |
| Defensive gross exposure | 35% |
| Defensive satellite weight | 0% |
| Cost assumption | 10 bps turnover |

Signal summary:

- Compute `z = zscore(log(03033 / 02800))`.
- If `z <= -1.0`, treat Hang Seng TECH as relatively cheap and overweight `03033`.
- If `z >= 1.0`, treat Hang Seng TECH as relatively rich and mostly hold `02800`.
- If the HSI anchor `02800` is below its 200-day moving average, cut gross exposure to 35% and keep the satellite at 0%.

## Backtest results

Strategy metrics from `scripts/research_hk_index_mean_reversion_backtest.py`.

The `full` row includes the early warmup period, when the script holds a 50/50
placeholder until enough overlapping history is available. The `post-warmup`
row is the cleaner comparison window for this direct-market-history strategy.

| Period | Annualized return | Max drawdown | Total return |
| --- | ---: | ---: | ---: |
| Full sample, 2020-08-27 to 2026-05-29 | 0.72% | -47.58% | 4.10% |
| Post-warmup, 2021-09-01 to 2026-05-29 | 1.77% | -29.93% | 8.39% |
| Train, 2020-08-27 to 2023-12-29 | -8.96% | -46.16% | -26.37% |
| Train post-warmup, 2021-09-01 to 2023-12-29 | -11.05% | -28.04% | -23.33% |
| Out-of-sample, 2024-01-01 to 2026-05-29 | 15.97% | -22.93% | 41.38% |
| Trailing 1Y, 2025-05-30 to 2026-05-29 | -0.83% | -17.17% | -0.81% |
| Trailing 3Y, 2023-05-30 to 2026-05-29 | 10.09% | -22.93% | 32.37% |
| 2021 | -17.17% | -33.72% | -16.86% |
| 2022 | -4.90% | -14.98% | -4.78% |
| 2023 | -16.04% | -28.04% | -15.52% |
| 2024 | 21.72% | -16.95% | 21.16% |
| 2025 | 26.30% | -22.93% | 25.48% |
| 2026 YTD to 2026-05-29 | -17.03% | -15.35% | -7.00% |

Regime-filter comparison over the post-warmup window:

| Variant | Annualized return | Max drawdown | Total return |
| --- | ---: | ---: | ---: |
| Selected: anchor-below-200MA defensive 35% `02800` | 1.77% | -29.93% | 8.39% |
| Legacy: both ETFs below 200MA defensive 25% `02800` | 1.20% | -32.56% | 5.65% |
| No moving-average filter | -1.78% | -51.61% | -7.96% |

Benchmarks over the post-warmup window:

| Benchmark | Annualized return | Max drawdown |
| --- | ---: | ---: |
| `02800` HSI ETF buy-and-hold | 2.92% | -41.66% |
| `03033` HSTECH ETF buy-and-hold | -6.51% | -59.53% |
| Static 50/50 `02800` / `03033` | -1.49% | -50.67% |

## Leveraged / inverse product stress test

`scripts/research_hk_index_mean_reversion_leveraged_backtest.py` checks whether
the same spread signal improves when expressed through HK-listed 2x leveraged
and -2x inverse products:

- `7200.HK`: HSI daily 2x leveraged product.
- `7500.HK`: HSI daily -2x inverse product.
- `7226.HK`: Hang Seng TECH daily 2x leveraged product.
- `7552.HK`: Hang Seng TECH daily -2x inverse product.

Common product sample starts on `2020-12-10`, constrained by `7226.HK` and
`7552.HK`. Results below use the same 10 bps turnover cost assumption.

| Variant | Post-warmup annualized return | Post-warmup max drawdown | OOS annualized return | OOS max drawdown |
| --- | ---: | ---: | ---: | ---: |
| HSTECH directional 2x, anchor MA filter | -4.65% | -59.03% | -19.63% | -54.75% |
| HSTECH directional 2x, no MA filter | -20.71% | -75.96% | -24.00% | -58.16% |
| Relative 2x pair, anchor MA filter | -1.89% | -24.88% | -6.46% | -22.95% |
| Relative 2x pair, no MA filter | -4.76% | -26.69% | -8.96% | -24.65% |
| Relative 2x pair, require both ETFs bull for long leg | -2.86% | -23.67% | -8.03% | -21.03% |

The pair form means:

- HSTECH cheap: hold `50% 7226 + 50% 7500` when the long leg is allowed.
- HSTECH rich: hold `50% 7200 + 50% 7552`.
- Otherwise hold cash.

The directional form means:

- HSTECH cheap: hold `100% 7226` when the long leg is allowed.
- HSTECH rich: hold `100% 7552`.
- Otherwise hold cash.

The 2x products do not improve this mean-reversion idea. Directional HSTECH 2x
has unacceptable drawdown, while the relative 2x pair controls drawdown but
turns the strategy negative. Daily reset compounding, volatility drag, product
fees, and the persistent HSTECH downtrend dominate the simple spread signal.

## 中文研究结论

- 本轮改进把牛熊判断从“`02800` 和 `03033` 都跌破 200 日线才防守”改为“`02800` 跌破 200 日线即防守”。
- 防守时只保留 35% `02800`，不再因为 `03033` 相对便宜就继续抄底恒科，剩余仓位留作现金。
- post-warmup 窗口内，改进版年化 1.77%、最大回撤 -29.93%；旧版为 1.20% / -32.56%，无均线过滤为 -1.78% / -51.61%。
- 2x 做多/做空版本已经回测：恒科方向 2x 亏损和回撤都明显放大；相对 pair 版本最大回撤可控但收益为负，因此不建议纳入可部署策略。
- 这个过滤确实降低了“下跌趋势中越跌越买”的风险，但收益仍不够强，样本外也没有跑赢 `02800` buy-and-hold，所以仍保持 research-only。

## Decision

Do not promote this profile to `runtime_enabled` yet.

Reasons:

- The 200-day anchor regime filter materially improves drawdown versus both the legacy filter and no moving-average filter.
- The idea did show better drawdown than a static 50/50 mix and worked well in 2024-2025.
- But full-sample annualized return remains close to flat and the out-of-sample return still trails `02800` buy-and-hold.
- The train period remains negative, especially 2021 and 2023, so the edge is not stable enough for live deployment.
- Current implementation is useful as the first non-snapshot architecture candidate because it exercises direct `market_history` inputs without snapshot artifacts.

Promotion requirements before live trading:

1. Validate platform `market_history` feed for `02800` and `03033` on both IBKR and LongBridge.
2. Re-run with broker-realistic trading costs, lot sizes, stamp/levy/fee handling, and dividend treatment.
3. Add a true HKD cash or money-market parking instrument if the platform requires full target allocation.
4. Require at least one more out-of-sample year or paper trading period before setting `status=runtime_enabled`.
