# HK High Dividend Low-Volatility Trend Runtime Profile


## 中文摘要

- 用途：本文档记录 `hk_dividend_gold_defensive_rotation` 的研究回测、参数和上线边界。
- 主要覆盖：`Scope`、`Data and methodology`、`Selected version`、`Backtest results`、`Decision`。
- 阅读顺序：先看策略边界和输入，再看回测指标和 runtime enablement 边界。
- 风险提示：涉及实盘、密钥、权限、Cloud Run、交易所或券商 API 的变更，必须先在测试环境或 dry-run 验证；不要只凭示例直接修改生产。
- 英文正文保留更完整的命令、字段名和配置键；如果摘要和正文不一致，以正文中的实际命令和配置为准。

## Scope

This research evaluates a simple non-snapshot `hk_equity` candidate:
`hk_dividend_gold_defensive_rotation`.

The strategy rotates between two HK-listed defensive sleeves:

- `03110` / `3110.HK`: Global X Hang Seng High Dividend Yield ETF, used as the HK high-dividend equity sleeve.
- `02840` / `2840.HK`: SPDR Gold Shares, used as the defensive diversifier.

The 12% volatility-targeted version is registered as a runtime catalog profile.
The result is strong, but it is still heavily influenced by the 2024-2026
gold/high-dividend regime, so platform deployments should start in dry-run or
paper mode and validate broker execution before real orders.

## Data and methodology

- Price source: Yahoo Finance adjusted daily close via `yfinance` for `2840.HK` and `3110.HK`.
- Sample used for scoring: `2021-09-01` to `2026-05-29`.
- Cost assumption: 10 bps per 100% turnover.
- Split discipline:
  - Train / parameter selection: `2021-09-01` to `2023-12-29`.
  - Out-of-sample check: `2024-01-01` to `2026-05-29`.
- The parameter grid was deliberately small: 63/126/252 day momentum, 100/150/200 day trend windows, high-dividend/gold pair variants, inverse-volatility or top-1 weighting, and 10%/12%/16% volatility caps.
- Selected live-enabled version favors positive train-period return, drawdown control, and simple explainability rather than maximum out-of-sample return.

Reference pages:

- Global X Hang Seng High Dividend Yield ETF `3110`: https://www.globalxetfs.com.hk/funds/hang-seng-high-dividend-yield-etf/
- Hang Seng High Dividend Yield Index factsheet: https://www.hsi.com.hk/static/uploads/contents/en/dl_centre/factsheets/hshdyie.pdf
- Hang Seng High Dividend Yield Index methodology: https://www.hsi.com.hk/static/uploads/contents/en/dl_centre/methodologies/IM_hshdyie.pdf
- SPDR Gold Shares `2840`: https://www.ssga.com/hk/en/institutional/etfs/funds/spdr-gold-shares-2840
- SPDR Gold Shares factsheet: https://www.ssga.com/library-content/products/factsheets/etfs/apac/factsheet-hk-en-2840.pdf
- SPDR Gold Shares HK financial information / NAV source: https://www.spdrgoldshares.com/hong-kong/english/financial-information/

## Selected version

Current runtime defaults:

| Parameter | Value |
| --- | ---: |
| Rebalance review | monthly |
| Momentum window | 63 trading days |
| Trend filter | price above 100-day moving average |
| Volatility window | 63 trading days |
| Selected ETFs | top 2 eligible ETFs |
| Minimum momentum | > 0 |
| Weighting | inverse volatility |
| Target annual volatility | 12% |
| Maximum gross exposure | 100% |
| Cost assumption | 10 bps turnover |

Signal summary:

- Compute 63-day momentum, 100-day trend, and 63-day annualized volatility for `02840` and `03110`.
- Eligible ETFs must have positive momentum and trade above the trend moving average.
- Rank eligible ETFs by momentum divided by volatility.
- Hold up to two ETFs using inverse-volatility weights.
- Scale exposure down when the trailing 63-day realized portfolio volatility is above the 12% target.
- If no ETF is eligible, hold cash.

## Backtest results

Strategy metrics from `scripts/research_hk_dividend_gold_defensive_rotation_backtest.py`:

| Period | Annualized return | Max drawdown | Total return |
| --- | ---: | ---: | ---: |
| Full sample, 2021-09-01 to 2026-05-29 | 17.16% | -8.06% | 107.41% |
| Train, 2021-09-01 to 2023-12-29 | 3.18% | -7.70% | 7.37% |
| Out-of-sample, 2024-01-01 to 2026-05-29 | 32.54% | -8.06% | 93.17% |
| Trailing 1Y, 2025-05-30 to 2026-05-29 | 34.53% | -7.32% | 33.43% |
| Trailing 3Y, 2023-05-30 to 2026-05-29 | 26.21% | -8.06% | 97.19% |
| 2022 | -0.60% | -7.70% | -0.58% |
| 2023 | 8.41% | -7.70% | 8.09% |
| 2024 | 26.56% | -8.06% | 25.86% |
| 2025 | 42.70% | -7.12% | 41.30% |
| 2026 YTD to 2026-05-29 | 23.72% | -7.32% | 8.63% |

Benchmarks over the full sample:

| Benchmark | Annualized return | Max drawdown | Total return |
| --- | ---: | ---: | ---: |
| `03110` high-dividend ETF buy-and-hold | 11.10% | -32.75% | 62.42% |
| `02840` gold ETF buy-and-hold | 21.76% | -23.34% | 147.67% |
| Static 50/50 `02840` / `03110` | 17.16% | -23.23% | 107.44% |

Other diagnostics:

| Metric | Value |
| --- | ---: |
| Average gross exposure | 62.96% |
| Average daily turnover | 1.34% |
| Latest target weights on 2026-05-29 | `03110`: 70.81%, cash: 29.19% |

## 中文研究结论

- 12% 波动率目标版本全样本年化 17.16%，最大回撤 -8.06%，比未加波动率目标版本牺牲少量收益但明显降低回撤。
- 训练期 2021-2023 保持正收益 3.18%，比已删除的 broad ETF baseline 训练期表现更稳。
- 相比单持 `03110`，它显著降低最大回撤；相比单持黄金，它牺牲部分收益换取更低回撤。
- 风险是样本仍短，且 2024-2026 对黄金和高股息都非常友好，不能直接推断长期稳定；runtime enablement 不等于直接实盘下单。

## Decision

Promote the 12% volatility-targeted version to `runtime_enabled`.

Reasons to promote:

- Full-sample return, train-period return, and drawdown are all materially better than the simple HK equity benchmarks.
- The 12% volatility target reduced full-sample max drawdown from roughly -11.28% to -8.06%.
- Turnover is low enough for HK's higher fee/spread environment.
- The implementation uses the same direct `market_history` and weight-target contract as existing non-snapshot HK runtime profiles.
- The two-ETF universe is operationally simpler than the removed broader ETF baseline.

Risks that still require platform validation:

- The result depends on only two ETFs and a short regime window.
- Gold exposure contributed heavily to the defensive profile; validate behavior in non-gold-led markets.
- ETF-specific spread, lot size, dividend treatment, and platform tradability must be validated per broker.
- Cash handling must be validated with both IBKR and LongBridge if no ETF passes the filter.

Requirements before real-money trading:

1. Validate platform `market_history` feed for `02840` and `03110` on both IBKR and LongBridge.
2. Re-run with broker-realistic fees, spreads/slippage, lot sizes, trading suspensions, and dividend treatment.
3. Add paper-trading evidence across at least one additional regime.
4. Keep platform dry-run enabled until order preview confirms symbol tradability, currency, cash residual, and order sizing.

## Product due-diligence additions

The live-enable evidence pack must now prove product-level lineage, not just
symbol tradability:

- For `03110`, archive current Global X product documents, the Hang Seng High
  Dividend Yield Index factsheet/methodology, NAV/iNAV evidence, distribution
  policy, and concentration / yield-trap review.
- For `02840`, archive current SSGA/SPDR product documents, NAV/iNAV and
  tracking-difference evidence, multi-counter currency handling, USD
  creation/redemption handling, and physical-gold single-asset / trust-storage
  risk review.
- For both ETFs, archive HKEX market-maker or liquidity-provider evidence,
  stamp-duty / ETF tax treatment, Stock Connect ETF eligibility or sell-only status, Southbound ETF turnover/fund-flow trend, broker Southbound ETF buy-route availability, broker product permission, board lot, trading
  currency, and product-document freshness before dry-run can be removed.
