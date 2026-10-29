# HK Strategy Selection Ranking - 2026-06-03

This note is the current promotion ranking for Hong Kong strategies. It is based on rerun local backtests on 2026-06-03 and replaces the earlier broad backlog as the package-level decision record.

Risk notice: this is engineering and research evidence only. It is not investment advice and does not authorize real order submission.

## Selection rules

A strategy can stay in the runtime or snapshot package surface only when it has current evidence for all of the following:

- long/full-cycle max drawdown stays within 30%;
- train and out-of-sample windows are not both dependent on one lucky regime;
- net returns include a basic HK cost assumption from the research script;
- the implementation is simple enough to validate through IBKR and LongBridge dry-run evidence;
- snapshot-backed strategies have a concrete artifact contract and production-data path.

## Final retained profiles

| Rank | Profile | Type | Full annualized return | Full max drawdown | Train annualized return | OOS annualized return | Decision |
| ---: | --- | --- | ---: | ---: | ---: | ---: | --- |
| 1 | `hk_global_etf_tactical_rotation` | non-snapshot runtime | 18.84% | -20.51% | 3.69% | 35.62% | Keep as the retained direct market-history runtime candidate; product checks are heavier. |
| 2 | `hk_low_vol_dividend_quality_snapshot` | snapshot-backed runtime | 13.34% | -23.05% | needs production PIT rerun | needs production PIT rerun | Keep as the only retained snapshot profile; artifact evidence remains mandatory. |

`hk_dividend_gold_defensive_rotation` was removed after review because its strong result was heavily dependent on the 2024-2026 gold/high-dividend regime and the fixed two-ETF universe looked too hindsight-selected for live promotion.

## Rejected ordinary-strategy candidates

| Candidate | Latest evidence | Decision |
| --- | --- | --- |
| HSI/HSTECH mean reversion | Full annualized return 0.72%, max drawdown -47.58%; the leveraged relative-pair variants had negative full/OOS annualized returns. | Removed from the package surface and source tree. |
| Broad six-ETF regime rotation baseline | Full annualized return 13.55%, max drawdown -21.56%, but train annualized return -7.24%. | Removed as a public profile; reusable ETF-rotation primitives remain in `hk_global_etf_tactical_rotation`. |
| High-dividend/gold pair variants | Full-sample metrics looked strong, but train-period return was weak and OOS performance concentrated in the favorable 2024-2026 gold/high-dividend regime. | Removed from runtime surface and source tree to avoid hindsight-selected two-ETF overfit. |

## Rejected snapshot candidates

| Candidate group | Decision |
| --- | --- |
| `hk_quality_growth_low_volatility` | Proxy drawdown passed, but it lacks production point-in-time fundamentals, same-universe ablation and live evidence. Keep out of package surface until a new research PR proves it. |
| `hk_shareholder_yield_quality`, `hk_free_cash_flow_quality` | Proxy long-cycle drawdowns exceeded 30%; removed from active contracts and default evidence queues. |
| Momentum, AH-premium, event, flow, central-SOE and multi-factor snapshot scaffolds | Removed from active contracts because long-cycle drawdown exceeded 30% or the data/execution assumptions were too weak for near-term live enablement. |

## Verification commands used

```bash
PYTHONPATH=src .venv/bin/python scripts/research_hk_global_etf_tactical_rotation_backtest.py --json-output data/output/hk_strategy_selection_20260603/listed_global_etf_rotation.json
```

The rejected mean-reversion, broad-baseline, and high-dividend/gold metrics were captured before deleting those research entrypoints. The retained backtest scripts remain in this repository for future reruns.

## Operational status

`runtime_enabled` in this strategy package means the profile can be selected by platform runtimes for dry-run/paper wiring. It does not mean production order submission is approved. Real orders still require platform evidence, broker permission checks, dry-run order previews, bilingual notification logs, rollout controls and operator approval.
