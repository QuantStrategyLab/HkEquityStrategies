# Platform Integration

## Supported platforms

Runtime catalog profiles declare structural support for:

- `ibkr` (`InteractiveBrokersPlatform`)
- `longbridge` (`LongBridgePlatform`)

| Profile | Input | Runtime status | Notes |
| --- | --- | --- | --- |
| `hk_dividend_gold_defensive_rotation` | `market_history` | `runtime_enabled` | Preferred lower-drawdown non-snapshot candidate; 02840/03110 only. |
| `hk_global_etf_tactical_rotation` | `market_history` | `runtime_enabled` | Secondary ETF-rotation candidate; broader ETF product checks required. |
| `hk_low_vol_dividend_quality_snapshot` | `feature_snapshot` + manifest | `runtime_enabled` | First retained snapshot-backed profile; artifact generation stays in `HkEquitySnapshotPipelines`. |

Platforms should expose only `get_runtime_enabled_profiles()` as selectable runtime targets.

## Live-enable matrix

Use the strategy-package matrix as the machine-readable source for platform UI/status/switch-plan decisions:

```bash
python scripts/print_hk_live_enablement_matrix.py --json
python scripts/print_hk_live_enablement_matrix.py --profile hk_dividend_gold_defensive_rotation --json
python scripts/print_hk_live_enablement_matrix.py --profile hk_low_vol_dividend_quality_snapshot --json
```

Matrix semantics:

- `selectable_by_platform=true` means the profile is a strategy-package runtime profile. It still requires platform dry-run/paper/live mode, account scope, and operator approval to be handled by the platform repository.
- `live_enablement_gate=requires_runtime_live_enablement_evidence` means the profile must pass `validate_hk_runtime_live_enablement.py` evidence validation before dry-run can be removed.
- Rejected research and snapshot scaffold names should not appear as matrix rows or platform selectable targets.

## Required platform mode

### InteractiveBrokersPlatform

Required HK mode variables:

```bash
IBKR_MARKET=HK
IBKR_MARKET_EXCHANGE=SEHK
IBKR_MARKET_CURRENCY=HKD
IBKR_DRY_RUN_ONLY=true
```

For `hk_low_vol_dividend_quality_snapshot`, the platform must also provide:

```bash
IBKR_FEATURE_SNAPSHOT_PATH=<published-snapshot-path>
IBKR_FEATURE_SNAPSHOT_MANIFEST_PATH=<published-manifest-path>
```

### LongBridgePlatform

Required HK mode variables:

```bash
ACCOUNT_REGION=HK
LONGBRIDGE_MARKET=HK
LONGBRIDGE_TRADING_CURRENCY=HKD
LONGBRIDGE_DRY_RUN_ONLY=true
```

For `hk_low_vol_dividend_quality_snapshot`, the platform must also provide:

```bash
LONGBRIDGE_FEATURE_SNAPSHOT_PATH=<published-snapshot-path>
LONGBRIDGE_FEATURE_SNAPSHOT_MANIFEST_PATH=<published-manifest-path>
```

## Runtime profile boundary

Do not set `STRATEGY_PROFILE` to rejected research or removed snapshot scaffold profiles in Cloud Run. Current allowed strategy-package profiles are:

- `hk_dividend_gold_defensive_rotation`
- `hk_global_etf_tactical_rotation`
- `hk_low_vol_dividend_quality_snapshot`

Dry-run versus live execution remains a platform runtime setting. Strategy-package `runtime_enabled` is not approval for real order submission.

## Evidence requirements before live trading

Before removing dry-run, every profile must pass the packaged evidence validator and platform checks:

```bash
python scripts/validate_hk_runtime_live_enablement.py --print-template --profile hk_dividend_gold_defensive_rotation --platform longbridge --json
python scripts/validate_hk_runtime_live_enablement.py --print-template --profile hk_low_vol_dividend_quality_snapshot --platform longbridge --json
```

Required evidence includes:

- point-in-time backtest controls, no look-ahead and no overfit;
- max drawdown within profile gate, generally <= 30%;
- at least 3 independent OOS folds;
- HK fee, spread, lot-size, suspension, VCM/CAS and liquidity/capacity checks;
- broker permission and product due diligence;
- dry-run order preview with stable artifact URI and sha256 provenance;
- bilingual notification payload and delivery-log evidence;
- rollout tripwires, kill switch, rollback plan and operator approval.

## Profile notes

- `hk_dividend_gold_defensive_rotation`: uses direct `market_history` for `02840` and `03110`; no snapshot artifact required.
- `hk_global_etf_tactical_rotation`: uses direct `market_history` for the HK-listed ETF universe; every ETF sleeve needs issuer/product/NAV/iNAV/spread/permission review before dry-run removal.
- `hk_low_vol_dividend_quality_snapshot`: requires a published factor snapshot and manifest from `HkEquitySnapshotPipelines`; real orders require artifact validation plus runtime evidence.
