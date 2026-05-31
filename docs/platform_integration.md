# Platform Integration

## Supported platforms

`hk_blue_chip_leader_rotation`, `hk_index_mean_reversion`, `hk_etf_regime_rotation`, and `hk_listed_global_etf_rotation` declare support for:

- `ibkr` (`InteractiveBrokersPlatform`)
- `longbridge` (`LongBridgePlatform`)

The strategy package does not import platform code. Platforms load it through the same catalog/runtime-adapter contract used by `UsEquityStrategies`. `hk_blue_chip_leader_rotation` is `architecture_scaffold`; `hk_index_mean_reversion` and `hk_etf_regime_rotation` are `research_candidate`; `hk_listed_global_etf_rotation` is `runtime_enabled`. Platforms may allow `hk_listed_global_etf_rotation`, but production Cloud Run remains unchanged until an explicit rollout changes `RUNTIME_TARGET_JSON` / `STRATEGY_PROFILE`.

## Required platform mode

### InteractiveBrokersPlatform

Runtime variables required for HK deployment:

```bash
IBKR_MARKET=HK
IBKR_MARKET_CALENDAR=XHKG
IBKR_MARKET_TIMEZONE=Asia/Hong_Kong
IBKR_MARKET_EXCHANGE=SEHK
IBKR_MARKET_CURRENCY=HKD
IBKR_MARKET_DATA_SYMBOL_SUFFIX=.HK
IBKR_FEATURE_SNAPSHOT_PATH=<published/hk_blue_chip_leader_rotation_feature_snapshot_latest.csv>
IBKR_FEATURE_SNAPSHOT_MANIFEST_PATH=<published/hk_blue_chip_leader_rotation_feature_snapshot_latest.csv.manifest.json>
```

### LongBridgePlatform

Runtime variables required for HK deployment:

```bash
ACCOUNT_REGION=HK
# or explicit overrides:
LONGBRIDGE_MARKET=HK
LONGBRIDGE_MARKET_CALENDAR=XHKG
LONGBRIDGE_MARKET_TIMEZONE=Asia/Hong_Kong
LONGBRIDGE_SYMBOL_SUFFIX=.HK
LONGBRIDGE_TRADING_CURRENCY=HKD
LONGBRIDGE_FEATURE_SNAPSHOT_PATH=<published/hk_blue_chip_leader_rotation_feature_snapshot_latest.csv>
LONGBRIDGE_FEATURE_SNAPSHOT_MANIFEST_PATH=<published/hk_blue_chip_leader_rotation_feature_snapshot_latest.csv.manifest.json>
```

## Contract boundaries

- `HkEquityStrategies` owns strategy metadata, feature requirements, entrypoint evaluation, and runtime adapter declarations.
- `HkEquitySnapshotPipelines` owns raw data normalization and snapshot artifact publication.
- Platform repositories own broker connection, market symbols, order sizing, notification delivery, and runtime reports.

## Production rollout guard

Do not set `STRATEGY_PROFILE=hk_blue_chip_leader_rotation`, `STRATEGY_PROFILE=hk_index_mean_reversion`, or `STRATEGY_PROFILE=hk_etf_regime_rotation` in Cloud Run while the profiles are not `runtime_enabled`. `hk_listed_global_etf_rotation` is runtime-enabled at the strategy-package level, but production Cloud Run should still remain on the existing configured profile until HK account permissions, HK market overrides, and broker dry-run checks are explicitly approved.

## Risks before live trading

- Validate account permissions for SEHK/HKD or LongBridge HK trading before enabling real orders.
- Validate `XHKG` calendar availability in the deployment image.
- Validate lot-size behavior with a dry run; the strategy exposes `lot_size`, but platform order-sizing remains responsible for enforcing broker-specific lot rules.

## Non-snapshot market-history candidate

`hk_index_mean_reversion` uses direct `market_history` rather than snapshot artifacts. Platforms must supply overlapping daily close history for `02800` and `03033`; no snapshot CSV or manifest is required. See `docs/research/hk_index_mean_reversion.md` for the backtest and current non-promotion decision.

`hk_etf_regime_rotation` also uses direct `market_history`. Platforms must supply overlapping daily close history for `02800`, `02822`, `02840`, `03033`, `03110`, and `03188`; no snapshot CSV or manifest is required. See `docs/research/hk_etf_regime_rotation.md` for the backtest and current non-promotion decision.

`hk_listed_global_etf_rotation` uses direct `market_history` for `02800`, `02822`, `03188`, `03033`, `02834`, `02840`, `03175`, and `03110`; no snapshot CSV or manifest is required. It is the first runtime-enabled HK non-snapshot profile, but production deployment still requires an explicit platform rollout.
