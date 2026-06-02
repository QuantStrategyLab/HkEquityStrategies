# HkEquityStrategies

[Chinese README](./README.zh-CN.md)

> Investment risk notice: this repository is for engineering, research, and operational review only. It is not investment advice.

`HkEquityStrategies` is the Hong Kong equity strategy layer for QuantStrategyLab platform runtimes.
It follows the same repository boundary as `UsEquityStrategies`: this repo owns pure strategy logic, catalog metadata, entrypoints, and runtime readiness checks; broker repositories own market data ingestion, account state, order routing, secrets, deployment, and notifications.

## Repository boundary

This repository owns:

- non-snapshot `hk_equity` strategy implementations that consume direct `market_history`
- promoted snapshot-backed runtime entrypoints that consume published `feature_snapshot` artifacts
- manifest/catalog-backed runtime entrypoints
- platform-neutral `StrategyDecision` generation
- HK runtime readiness and live-enable evidence validators
- research notes for non-snapshot HK strategies

This repository does not own:

- snapshot-backed strategy artifact generation and publication
- broker credentials or account reconciliation
- order placement or broker-specific order previews
- Cloud Run / Google Run service deployment
- Telegram or broker notification delivery

Snapshot-backed HK artifact generation is intentionally separated into [`../HkEquitySnapshotPipelines`](../HkEquitySnapshotPipelines). This repository may expose a promoted snapshot-backed strategy as a runtime entrypoint, but the artifact contract, production source lineage, and artifact-pack validation stay in the snapshot repository.

## Current runtime profiles

| Canonical profile | Display name | Input | Compatible platforms | Cadence | Benchmark | Status |
| --- | --- | --- | --- | --- | --- | --- |
| `hk_high_dividend_low_vol_trend` | HK High Dividend Low-Volatility Trend | `market_history` | `InteractiveBrokersPlatform`, `LongBridgePlatform` | monthly review | `03110` | `runtime_enabled` |
| `hk_listed_global_etf_rotation` | HK-listed Global ETF Rotation | `market_history` | `InteractiveBrokersPlatform`, `LongBridgePlatform` | monthly review | `02800` | `runtime_enabled` |
| `hk_low_vol_dividend_quality` | HK Low-Volatility Dividend Quality | `feature_snapshot` | `InteractiveBrokersPlatform`, `LongBridgePlatform` | monthly review | `02800` | `runtime_enabled` |

Research/backtest-only profiles stay out of the runtime catalog:

- `hk_index_mean_reversion`
- `hk_etf_regime_rotation`

Platform repositories should only expose profiles returned by `get_runtime_enabled_profiles()`.

## Strategy index

### `hk_high_dividend_low_vol_trend`

- Purpose: a lower-drawdown HK ETF rotation profile for the first live-enable candidate.
- Universe: HK-listed high-dividend and gold ETFs.
- Signal style: monthly trend rotation with volatility targeting.
- Risk target: 12% annual volatility target.
- Current role: preferred non-snapshot runtime candidate; real order submission still requires broker dry-run evidence and operator approval.

Research details: [`docs/research/hk_high_dividend_low_vol_trend.md`](./docs/research/hk_high_dividend_low_vol_trend.md)

### `hk_listed_global_etf_rotation`

- Purpose: diversified HK-listed ETF rotation across local equity, overseas equity, gold, and crude-oil ETF sleeves.
- Input: direct daily market history.
- Signal style: monthly review, momentum/trend filter, and volatility-targeted allocation.
- Current role: secondary non-snapshot runtime candidate; ETF product evidence, NAV/iNAV review, liquidity checks, and dry-run order previews are required before real orders.

Research details: [`docs/research/hk_listed_global_etf_rotation.md`](./docs/research/hk_listed_global_etf_rotation.md)

### `hk_low_vol_dividend_quality`

- Purpose: first promoted snapshot-backed HK single-name equity selector.
- Input: published `feature_snapshot` artifact plus manifest from `HkEquitySnapshotPipelines`.
- Signal style: monthly low-volatility / dividend-quality ranking with sector caps, single-name caps, breadth defense, and `02800` safe-haven residual allocation.
- Current role: runtime-enabled at the strategy-package level for IBKR and LongBridge dry-run wiring; real order submission still requires validated snapshot artifacts, point-in-time walk-forward evidence, broker order previews, bilingual notification logs, and operator approval.

## Runtime enablement gates

The live-enable ranking is a work queue, not an investment recommendation.
A profile must pass the evidence gates before production order submission:

- max drawdown gate: `<= 30%` unless the profile defines a stricter threshold
- point-in-time data and no look-ahead / survivorship-bias controls
- at least 3 independent out-of-sample folds
- net-of-cost and HK slippage / lot-size / suspension / VCM / CAS checks
- broker permission, ETF product, NAV/iNAV, fee, tax, and liquidity evidence
- dry-run order preview with stable artifact URIs and sha256 provenance
- bilingual notification and delivery-log evidence
- staged rollout, tripwire, kill switch, rollback plan, and operator approval

Use the packaged tools instead of manually interpreting README text:

```bash
python scripts/print_hk_live_enablement_matrix.py --json
python scripts/print_hk_runtime_readiness.py --profile hk_high_dividend_low_vol_trend --platform longbridge --json
python scripts/print_hk_runtime_readiness.py --profile hk_low_vol_dividend_quality --platform longbridge --json
python scripts/validate_hk_runtime_live_enablement.py --print-template --profile hk_high_dividend_low_vol_trend --platform longbridge --json
```

These commands are read-only unless you explicitly pass an evidence file to the validator. They do not mutate Cloud Run or broker state.

## Local smoke commands

```bash
python -m pytest -q
```

Run the synthetic dry-run smoke for the ETF rotation strategy:

```bash
python scripts/smoke_hk_listed_global_etf_rotation_dry_run.py --json
```

## Documentation

- [`docs/platform_integration.md`](./docs/platform_integration.md): platform integration notes for IBKR and LongBridge.
- [`docs/research/hk_high_dividend_low_vol_trend.md`](./docs/research/hk_high_dividend_low_vol_trend.md): high-dividend / gold trend-rotation research.
- [`docs/research/hk_listed_global_etf_rotation.md`](./docs/research/hk_listed_global_etf_rotation.md): HK-listed global ETF rotation research.
- [`docs/research/hk_index_mean_reversion.md`](./docs/research/hk_index_mean_reversion.md): Hang Seng / HSTECH mean-reversion research-only notes.
- [`docs/research/hk_etf_regime_rotation.md`](./docs/research/hk_etf_regime_rotation.md): earlier ETF regime-rotation research-only notes.
- [`docs/research/hk_quant_strategy_ideas.md`](./docs/research/hk_quant_strategy_ideas.md): broader HK strategy idea inventory.

## Related repositories

- [`../HkEquitySnapshotPipelines`](../HkEquitySnapshotPipelines): snapshot-backed HK equity strategy artifacts and scaffold helpers.
- [`../QuantPlatformKit`](../QuantPlatformKit): shared strategy contract and component loader.
- `InteractiveBrokersPlatform` / `LongBridgePlatform`: broker-specific runtime, deployment, order routing, and notification ownership.
