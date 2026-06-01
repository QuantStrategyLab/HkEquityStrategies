# Platform Integration


## 中文摘要

- 用途：本文档围绕 `Platform Integration`，用于理解 `HkEquityStrategies` 的配置、运行、部署、研究或验收边界。
- 主要覆盖：`Supported platforms`、`Required platform mode`、`InteractiveBrokersPlatform`、`LongBridgePlatform`、`Contract boundaries`。
- 阅读顺序：先确认边界、输入输出和权限要求，再执行文档里的命令、CI、dry-run、发布或切换步骤。
- 风险提示：涉及实盘、密钥、权限、Cloud Run、交易所或券商 API 的变更，必须先在测试环境或 dry-run 验证；不要只凭示例直接修改生产。
- 英文正文保留更完整的命令、字段名和配置键；如果摘要和正文不一致，以正文中的实际命令和配置为准。

## Supported platforms

The HK strategy surface is split by input style:

- Runtime non-snapshot/direct `market_history`: `hk_listed_global_etf_rotation`.
- Research/backtest-only: `hk_index_mean_reversion`, `hk_etf_regime_rotation`; they are not runtime catalog profiles.
- Snapshot-backed scaffold: `hk_blue_chip_leader_rotation`; its artifact contract, strategy helper, and publication flow live in `HkEquitySnapshotPipelines`.

The runtime catalog profile declares structural support for:

- `ibkr` (`InteractiveBrokersPlatform`)
- `longbridge` (`LongBridgePlatform`)

The strategy package does not import platform code. Platforms load it through the same catalog/runtime-adapter contract used by `UsEquityStrategies`. `hk_listed_global_etf_rotation` is the only HK runtime catalog profile. `hk_blue_chip_leader_rotation` is a snapshot scaffold in `HkEquitySnapshotPipelines`; `hk_index_mean_reversion` and `hk_etf_regime_rotation` are research/backtest-only candidates. Platform repositories should expose only runtime-enabled HK profiles as selectable runtime targets. Research and snapshot-scaffold profiles remain in docs/backtests until they are explicitly promoted.

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
IBKR_DRY_RUN_ONLY=true
```

Snapshot-backed profiles additionally require snapshot artifacts. The current HK snapshot profile is scaffold-only, so these variables are examples for future rollout, not current production settings:

```bash
IBKR_FEATURE_SNAPSHOT_PATH=<published/hk_blue_chip_leader_rotation_feature_snapshot_latest.csv>
IBKR_FEATURE_SNAPSHOT_MANIFEST_PATH=<published/hk_blue_chip_leader_rotation_feature_snapshot_latest.csv.manifest.json>
```

### LongBridgePlatform

Runtime variables required for HK deployment:

```bash
ACCOUNT_REGION=HK
ACCOUNT_PREFIX=HK
LONGBRIDGE_DRY_RUN_ONLY=true
# or explicit overrides:
LONGBRIDGE_MARKET=HK
LONGBRIDGE_MARKET_CALENDAR=XHKG
LONGBRIDGE_MARKET_TIMEZONE=Asia/Hong_Kong
LONGBRIDGE_SYMBOL_SUFFIX=.HK
LONGBRIDGE_TRADING_CURRENCY=HKD
```

Snapshot-backed profiles additionally require snapshot artifacts. The current HK snapshot profile is scaffold-only, so these variables are examples for future rollout, not current production settings:

```bash
LONGBRIDGE_FEATURE_SNAPSHOT_PATH=<published/hk_blue_chip_leader_rotation_feature_snapshot_latest.csv>
LONGBRIDGE_FEATURE_SNAPSHOT_MANIFEST_PATH=<published/hk_blue_chip_leader_rotation_feature_snapshot_latest.csv.manifest.json>
```

## Runtime readiness checklist

Render the strategy-package readiness plan before changing either platform:

```bash
python scripts/print_hk_runtime_readiness.py --profile hk_listed_global_etf_rotation --platform ibkr --json
python scripts/print_hk_runtime_readiness.py --profile hk_listed_global_etf_rotation --platform longbridge --json
```

The plan is intentionally `dry_run_only=true` by default and does not deploy Cloud Run. It records:

- HK market defaults: `HK` / `XHKG` / `Asia/Hong_Kong` / `SEHK` / `HKD` / `.HK`.
- Managed symbols and required direct `market_history` inputs.
- Platform target conversion: IBKR accepts weight targets directly; LongBridge needs a portfolio snapshot for weight-to-value conversion.
- Dry-run checks for market-data permission, order preview, integer-share and broker lot-size validation, HKD cash lines, and notifications.

## Contract boundaries

- `HkEquityStrategies` owns non-snapshot strategy metadata, entrypoint evaluation, and runtime adapter declarations.
- `HkEquitySnapshotPipelines` owns snapshot-backed artifact contracts, raw data normalization, snapshot publication, and research/backtest-only work that is not platform-selectable.
- Platform repositories own broker connection, market symbols, order sizing, notification delivery, and runtime reports.

## Runtime profile boundary

Do not set `STRATEGY_PROFILE=hk_blue_chip_leader_rotation`, `STRATEGY_PROFILE=hk_index_mean_reversion`, or `STRATEGY_PROFILE=hk_etf_regime_rotation` in Cloud Run while the profiles are not `runtime_enabled`. Platform status and switch-plan tooling should not expose these profiles as selectable runtime targets. `hk_listed_global_etf_rotation` is runtime-enabled at the strategy-package level and can be selected by Cloud Run through `RUNTIME_TARGET_JSON` / `STRATEGY_PROFILE`; dry-run versus live execution remains a platform runtime setting.

## Risks before live trading

- Validate account permissions for SEHK/HKD or LongBridge HK trading before enabling real orders.
- Validate `XHKG` calendar availability in the deployment image.
- Validate lot-size behavior with a dry run; the strategy exposes `lot_size`, but platform order-sizing remains responsible for enforcing broker-specific lot rules.

## Non-snapshot market-history candidate

`hk_index_mean_reversion` uses direct `market_history` rather than snapshot artifacts. Platforms must supply overlapping daily close history for `02800` and `03033`; no snapshot CSV or manifest is required. See `docs/research/hk_index_mean_reversion.md` for the backtest and current non-promotion decision.

`hk_etf_regime_rotation` also uses direct `market_history`. Platforms must supply overlapping daily close history for `02800`, `02822`, `02840`, `03033`, `03110`, and `03188`; no snapshot CSV or manifest is required. See `docs/research/hk_etf_regime_rotation.md` for the backtest and current non-promotion decision.

`hk_listed_global_etf_rotation` uses direct `market_history` for `02800`, `02822`, `03188`, `03033`, `02834`, `02840`, `03175`, and `03110`; no snapshot CSV or manifest is required. It is the first runtime-enabled HK non-snapshot profile and can be selected by a platform Cloud Run deployment.
