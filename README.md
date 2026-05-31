# HkEquityStrategies

Hong Kong equity strategy package for QuantStrategyLab platform runtimes.

## Scope

This repository owns strategy catalog metadata, runtime entrypoints, and runtime adapter contracts for `hk_equity` strategies. It does not own broker credentials, Cloud Run deployment, or snapshot publication.

The first profile is `hk_blue_chip_leader_rotation`, a monthly feature-snapshot strategy that can run on:

- `InteractiveBrokersPlatform` with `IBKR_MARKET=HK` / `SEHK` / `HKD`.
- `LongBridgePlatform` with `ACCOUNT_REGION=HK` or `LONGBRIDGE_MARKET=HK`.

## Architecture

```text
HkEquitySnapshotPipelines
  -> feature snapshot CSV + manifest
HkEquityStrategies
  -> catalog + entrypoint + runtime adapter
InteractiveBrokersPlatform / LongBridgePlatform
  -> load the strategy package, read the snapshot artifact, and execute broker orders
```

The package follows the same boundary as `UsEquityStrategies`: strategies return platform-neutral `StrategyDecision` objects; platform repositories own market data, portfolio snapshots, order conversion, notifications, and runtime reports.

## Runtime profile

| Profile | Domain | Inputs | Target mode | Platforms |
| --- | --- | --- | --- | --- |
| `hk_blue_chip_leader_rotation` | `hk_equity` | `feature_snapshot` | `weight` | `ibkr`, `longbridge` |

## Snapshot contract

Required feature columns:

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

Optional but recommended columns: `as_of`, `snapshot_date`, `market_cap_hkd`, `lot_size`, `eligible`.

## Local validation

```bash
python -m pytest -q
```
