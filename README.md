# HkEquityStrategies

> ⚠️ 投资有风险，不构成投资建议，仅供学习交流用途。


## 中文摘要

- 用途：本文档围绕 `HkEquityStrategies`，用于理解 `HkEquityStrategies` 的配置、运行、部署、研究或验收边界。
- 主要覆盖：`Scope`、`Architecture`、`Runtime profile`、`Snapshot contract`、`Runtime enablement policy`。
- 阅读顺序：先确认边界、输入输出和权限要求，再执行文档里的命令、CI、dry-run、发布或切换步骤。
- 风险提示：涉及实盘、密钥、权限、Cloud Run、交易所或券商 API 的变更，必须先在测试环境或 dry-run 验证；不要只凭示例直接修改生产。
- 英文正文保留更完整的命令、字段名和配置键；如果摘要和正文不一致，以正文中的实际命令和配置为准。
Hong Kong equity strategy package for QuantStrategyLab platform runtimes.

## Scope

This repository owns strategy catalog metadata, runtime entrypoints, and runtime adapter contracts for `hk_equity` strategies. It does not own broker credentials, Cloud Run deployment, or snapshot publication.

The first profile scaffold is `hk_blue_chip_leader_rotation`. This repo also contains direct `market_history` profiles: `hk_index_mean_reversion`, `hk_etf_regime_rotation`, and `hk_listed_global_etf_rotation`. `hk_listed_global_etf_rotation` is `runtime_enabled` after the volatility-targeted backtest kept full-sample drawdown below 30%; the other HK profiles remain disabled.

Runtime-compatible platforms:

- `InteractiveBrokersPlatform` with `IBKR_MARKET=HK` / `SEHK` / `HKD`.
- `LongBridgePlatform` with `ACCOUNT_REGION=HK` or `LONGBRIDGE_MARKET=HK`.

## Architecture

```text
HkEquitySnapshotPipelines
  -> feature snapshot CSV + manifest for snapshot-backed profiles
Platform market-data feed
  -> direct market_history for non-snapshot profiles
HkEquityStrategies
  -> catalog + entrypoint + runtime adapter
InteractiveBrokersPlatform / LongBridgePlatform
  -> load the strategy package, provide required inputs, and execute broker orders
```

The package follows the same boundary as `UsEquityStrategies`: strategies return platform-neutral `StrategyDecision` objects; platform repositories own market data, portfolio snapshots, order conversion, notifications, and runtime reports.

## Runtime profile

| Profile | Domain | Inputs | Target mode | Platforms | Status |
| --- | --- | --- | --- | --- | --- |
| `hk_blue_chip_leader_rotation` | `hk_equity` | `feature_snapshot` | `weight` | `ibkr`, `longbridge` | `architecture_scaffold` |
| `hk_index_mean_reversion` | `hk_equity` | `market_history` | `weight` | `ibkr`, `longbridge` | `research_candidate` |
| `hk_etf_regime_rotation` | `hk_equity` | `market_history` | `weight` | `ibkr`, `longbridge` | `research_candidate` |
| `hk_listed_global_etf_rotation` | `hk_equity` | `market_history` | `weight` | `ibkr`, `longbridge` | `runtime_enabled` |

## Snapshot contract

Draft required feature columns:

- `symbol`
- `sector`
- `close_hkd`
- `adv20_hkd`
- `history_days`
- `mom_3m`
- `mom_6m`
- `mom_12_1`
- `rel_mom_6m_vs_benchmark`
- `high_252_gap`
- `sma200_gap`
- `vol_63`
- `maxdd_126`

Draft optional but recommended columns: `as_of`, `snapshot_date`, `market_cap_hkd`, `lot_size`, `eligible`.

## Runtime enablement policy

`get_runtime_enabled_profiles()` returns only profiles that are eligible for platform rollout. `hk_listed_global_etf_rotation` is currently runtime-enabled, while `hk_blue_chip_leader_rotation`, `hk_index_mean_reversion`, and `hk_etf_regime_rotation` remain disabled. Platform repositories still own the production rollout decision: do not change production Cloud Run `RUNTIME_TARGET_JSON` / `STRATEGY_PROFILE` to a HK profile unless the deployment account, HK market overrides, dry-run checks, and operator approval are in place.

## HK runtime readiness

Use the packaged readiness command before changing IBKR or LongBridge runtime settings:

```bash
python scripts/print_hk_runtime_readiness.py --profile hk_listed_global_etf_rotation --platform ibkr --json
python scripts/print_hk_runtime_readiness.py --profile hk_listed_global_etf_rotation --platform longbridge --json
```

The output is a dry-run checklist, not a deployment action. It covers HK market defaults, managed symbols, direct `market_history` requirements, LongBridge weight-to-value conversion, order preview, integer-share / lot-size checks, HKD cash lines, and the Cloud Run rollout guard.

Run the local smoke before broker-specific verification. It uses synthetic market history and does not connect to IBKR, LongBridge, Google Cloud, or any live account:

```bash
python scripts/smoke_hk_listed_global_etf_rotation_dry_run.py --json
```

## Local validation

```bash
python -m pytest -q
```

## Research notes

- `docs/research/hk_index_mean_reversion.md` records the HSI / Hang Seng TECH ETF mean-reversion backtest. Current conclusion: keep as `research_candidate`; do not enable live trading yet.
- `docs/research/hk_etf_regime_rotation.md` records the HK-listed ETF regime rotation backtest. Current conclusion: promising but still keep as `research_candidate` because the 2021-2023 train period was negative.
- `docs/research/hk_listed_global_etf_rotation.md` records the HK-listed global ETF rotation backtest. Current conclusion: mark `runtime_enabled` because the volatility-targeted version kept full-sample drawdown under 30%; production Cloud Run remains unchanged until an explicit rollout.
