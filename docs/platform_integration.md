# Platform Integration

## Supported platforms

`hk_blue_chip_leader_rotation` declares future support for:

- `ibkr` (`InteractiveBrokersPlatform`)
- `longbridge` (`LongBridgePlatform`)

The strategy package does not import platform code. Platforms load it through the same catalog/runtime-adapter contract used by `UsEquityStrategies`. The profile status is `architecture_scaffold`, so platforms should show it as eligible-but-disabled until it is promoted to `runtime_enabled`.

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

Do not set `STRATEGY_PROFILE=hk_blue_chip_leader_rotation` in Cloud Run while the status is `architecture_scaffold`. The current package is only for integration wiring, catalog validation, and adapter compatibility checks.

## Risks before live trading

- Validate account permissions for SEHK/HKD or LongBridge HK trading before enabling real orders.
- Validate `XHKG` calendar availability in the deployment image.
- Validate lot-size behavior with a dry run; the strategy exposes `lot_size`, but platform order-sizing remains responsible for enforcing broker-specific lot rules.
