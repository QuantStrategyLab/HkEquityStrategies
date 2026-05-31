# Platform Integration

## Supported platforms

`hk_blue_chip_leader_rotation` and `hk_index_mean_reversion` declare future support for:

- `ibkr` (`InteractiveBrokersPlatform`)
- `longbridge` (`LongBridgePlatform`)

The strategy package does not import platform code. Platforms load it through the same catalog/runtime-adapter contract used by `UsEquityStrategies`. `hk_blue_chip_leader_rotation` is `architecture_scaffold`; `hk_index_mean_reversion` is `research_candidate`. Platforms should show both as eligible-but-disabled until a profile is promoted to `runtime_enabled`.

## Required platform mode

### InteractiveBrokersPlatform

Future runtime variables after the profile is promoted:

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

Future runtime variables after the profile is promoted:

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

## Do not enable yet

Do not set `STRATEGY_PROFILE=hk_blue_chip_leader_rotation` or `STRATEGY_PROFILE=hk_index_mean_reversion` in Cloud Run while the profiles are not `runtime_enabled`. The current package is only for integration wiring, catalog validation, adapter compatibility checks, and research replay.

## Risks before live trading

- Validate account permissions for SEHK/HKD or LongBridge HK trading before enabling real orders.
- Validate `XHKG` calendar availability in the deployment image.
- Validate lot-size behavior with a dry run; the strategy exposes `lot_size`, but platform order-sizing remains responsible for enforcing broker-specific lot rules.

## Non-snapshot market-history candidate

`hk_index_mean_reversion` uses direct `market_history` rather than snapshot artifacts. Platforms must supply overlapping daily close history for `02800` and `03033`; no snapshot CSV or manifest is required. See `docs/research/hk_index_mean_reversion.md` for the backtest and current non-promotion decision.
