# HkEquityStrategies

> ⚠️ 投资有风险，不构成投资建议，仅供学习交流用途。

Hong Kong equity strategy package for QuantStrategyLab platform runtimes.

## Scope

This repository owns strategy catalog metadata, runtime entrypoints, and runtime adapter contracts for `hk_equity` strategies. It does not own broker credentials, Cloud Run deployment, or snapshot publication.

The first profile scaffold is `hk_blue_chip_leader_rotation`. This repo also contains direct `market_history` research candidates: `hk_index_mean_reversion` and `hk_etf_regime_rotation`. All profiles are **not `runtime_enabled` yet** and should not be used for live or scheduled trading.

It is intended to run later on:

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

`get_runtime_enabled_profiles()` intentionally returns an empty set until a real HK strategy and validated feed are ready. Platform repositories may list the profiles as eligible by capability, but should keep them disabled and reject `STRATEGY_PROFILE=hk_blue_chip_leader_rotation`, `STRATEGY_PROFILE=hk_index_mean_reversion`, or `STRATEGY_PROFILE=hk_etf_regime_rotation` in production.

## Local validation

```bash
python -m pytest -q
```

## Research notes

- `docs/research/hk_index_mean_reversion.md` records the HSI / Hang Seng TECH ETF mean-reversion backtest. Current conclusion: keep as `research_candidate`; do not enable live trading yet.
- `docs/research/hk_etf_regime_rotation.md` records the HK-listed ETF regime rotation backtest. Current conclusion: promising but still keep as `research_candidate` because the 2021-2023 train period was negative.
- `docs/research/hk_listed_global_etf_rotation.md` records a HK-listed global ETF rotation follow-up. Current conclusion: keep in research backlog because the conservative version improves return but has a materially worse drawdown than the current HK ETF basket.
