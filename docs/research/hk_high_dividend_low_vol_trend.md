# HK High Dividend Low-Volatility Trend Research Candidate


## 中文摘要

- 用途：本文档记录 `hk_high_dividend_low_vol_trend` 的研究回测、参数和上线边界。
- 主要覆盖：`Scope`、`Data and methodology`、`Selected version`、`Backtest results`、`Decision`。
- 阅读顺序：先看策略边界和输入，再看回测指标和暂不 live-enable 的原因。
- 风险提示：涉及实盘、密钥、权限、Cloud Run、交易所或券商 API 的变更，必须先在测试环境或 dry-run 验证；不要只凭示例直接修改生产。
- 英文正文保留更完整的命令、字段名和配置键；如果摘要和正文不一致，以正文中的实际命令和配置为准。

## Scope

This research evaluates a simple non-snapshot `hk_equity` candidate:
`hk_high_dividend_low_vol_trend`.

The strategy rotates between two HK-listed defensive sleeves:

- `03110` / `3110.HK`: Global X Hang Seng High Dividend Yield ETF, used as the HK high-dividend equity sleeve.
- `02840` / `2840.HK`: SPDR Gold Shares, used as the defensive diversifier.

This remains research/backtest-only and is not registered as a runtime catalog
profile. The current result is strong, but it is still heavily influenced by the
2024-2026 gold/high-dividend regime.

## Data and methodology

- Price source: Yahoo Finance adjusted daily close via `yfinance` for `2840.HK` and `3110.HK`.
- Sample used for scoring: `2021-09-01` to `2026-05-29`.
- Cost assumption: 10 bps per 100% turnover.
- Split discipline:
  - Train / parameter selection: `2021-09-01` to `2023-12-29`.
  - Out-of-sample check: `2024-01-01` to `2026-05-29`.
- The parameter grid was deliberately small: 63/126/252 day momentum, 100/150/200 day trend windows, high-dividend/gold pair variants, and inverse-volatility or top-1 weighting.
- Selected version favors positive train-period return, low drawdown, and simple explainability rather than maximum out-of-sample return.

Reference pages:

- Global X Hang Seng High Dividend Yield ETF `3110`: https://www.globalxetfs.com.hk/funds/hang-seng-high-dividend-yield-etf/
- Hang Seng High Dividend Yield Index factsheet: https://www.hsi.com.hk/static/uploads/contents/en/dl_centre/factsheets/hshdyie.pdf
- SPDR Gold Shares `2840`: https://www.ssga.com/hk/en/institutional/etfs/funds/spdr-gold-shares-2840
- SPDR Gold Shares factsheet: https://www.ssga.com/library-content/products/factsheets/etfs/apac/factsheet-hk-en-2840.pdf

## Selected version

Current research defaults:

| Parameter | Value |
| --- | ---: |
| Rebalance review | monthly |
| Momentum window | 63 trading days |
| Trend filter | price above 100-day moving average |
| Volatility window | 63 trading days |
| Selected ETFs | top 2 eligible ETFs |
| Minimum momentum | > 0 |
| Weighting | inverse volatility |
| Cost assumption | 10 bps turnover |

Signal summary:

- Compute 63-day momentum, 100-day trend, and 63-day annualized volatility for `02840` and `03110`.
- Eligible ETFs must have positive momentum and trade above the trend moving average.
- Rank eligible ETFs by momentum divided by volatility.
- Hold up to two ETFs using inverse-volatility weights.
- If no ETF is eligible, hold cash.

## Backtest results

Strategy metrics from `scripts/research_hk_high_dividend_low_vol_trend_backtest.py`:

| Period | Annualized return | Max drawdown | Total return |
| --- | ---: | ---: | ---: |
| Full sample, 2021-09-01 to 2026-05-29 | 17.94% | -11.28% | 113.89% |
| Train, 2021-09-01 to 2023-12-29 | 3.07% | -11.28% | 7.11% |
| Out-of-sample, 2024-01-01 to 2026-05-29 | 34.43% | -10.70% | 99.69% |
| Trailing 1Y, 2025-05-30 to 2026-05-29 | 36.64% | -10.09% | 35.46% |
| Trailing 3Y, 2023-05-30 to 2026-05-29 | 27.40% | -10.70% | 102.64% |
| 2022 | -0.97% | -11.28% | -0.95% |
| 2023 | 8.57% | -9.87% | 8.25% |
| 2024 | 27.40% | -8.74% | 26.67% |
| 2025 | 48.27% | -7.12% | 46.65% |
| 2026 YTD to 2026-05-29 | 20.43% | -10.09% | 7.50% |

Benchmarks over the full sample:

| Benchmark | Annualized return | Max drawdown | Total return |
| --- | ---: | ---: | ---: |
| `03110` high-dividend ETF buy-and-hold | 11.10% | -32.75% | 62.42% |
| `02840` gold ETF buy-and-hold | 21.76% | -23.34% | 147.67% |
| Static 50/50 `02840` / `03110` | 17.16% | -23.23% | 107.44% |

Other diagnostics:

| Metric | Value |
| --- | ---: |
| Average gross exposure | 74.85% |
| Average daily turnover | 1.60% |
| Latest target weights on 2026-05-29 | `03110`: 100.00% |

## 中文研究结论

- 这个策略是目前港股 research-only 候选里风险收益比最好的一个：full sample 年化 17.94%，最大回撤 -11.28%。
- 训练期 2021-2023 也保持正收益 3.07%，比 `hk_etf_regime_rotation` 的训练期表现更稳。
- 相比单持 `03110`，它显著降低最大回撤；相比单持黄金，它牺牲部分收益换取更低回撤。
- 风险是样本仍短，且 2024-2026 对黄金和高股息都非常友好，不能直接推断长期稳定。

## Decision

Keep this strategy as research/backtest-only; do not register it as a runtime
catalog profile yet.

Reasons to continue research:

- Full-sample return, train-period return, and drawdown are all materially better than the simple HK equity benchmarks.
- Turnover is low enough for HK's higher fee/spread environment.
- The implementation uses the same direct `market_history` contract as other non-snapshot HK research candidates.

Reasons not to promote yet:

- The result depends on only two ETFs and a short regime window.
- Gold exposure contributed heavily to the defensive profile; validate behavior in non-gold-led markets.
- ETF-specific spread, lot size, dividend treatment, and platform tradability must be validated per broker.
- Cash handling must be validated with both IBKR and LongBridge if no ETF passes the filter.

Promotion requirements before live trading:

1. Validate platform `market_history` feed for `02840` and `03110` on both IBKR and LongBridge.
2. Re-run with broker-realistic fees, spreads/slippage, lot sizes, trading suspensions, and dividend treatment.
3. Add paper-trading evidence across at least one additional regime.
4. Keep it out of the runtime catalog until platform dry run confirms symbol tradability and order sizing.
