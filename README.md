# HkEquityStrategies

[Chinese README](README.zh-CN.md)

> Investing involves risk. This project does not provide investment advice and is for education, research, and engineering review only.

## What this repository is

`HkEquityStrategies` is the Hong Kong equity strategy package for QuantStrategyLab. It provides reusable strategy implementations, catalog metadata, runtime entrypoints, and readiness checks for HK-capable platform runtimes such as Interactive Brokers and LongBridge.

This repository is a strategy layer, not a broker or deployment layer. It does not store broker credentials, submit orders by itself, publish snapshot artifacts, or decide whether a profile is safe for live trading without external evidence.

## Strategy profiles

### Direct runtime strategies

These profiles run from market-history inputs and do not require a separate feature-snapshot artifact before the strategy entrypoint can produce target weights.

| Profile | Name | Input | Current role |
| --- | --- | --- | --- |
| `hk_high_dividend_low_vol_trend` | HK High Dividend Low-Volatility Trend | `market_history` | Runtime-enabled preferred HK ETF profile; dry-run and operator evidence are still required before live orders. |
| `hk_listed_global_etf_rotation` | HK-listed Global ETF Rotation | `market_history` | Runtime-enabled secondary HK ETF profile with broader ETF exposure and product-review requirements. |

### Snapshot-backed strategies

These profiles depend on validated artifacts from `HkEquitySnapshotPipelines`. The strategy package exposes the runtime entrypoint, but the snapshot repository owns the artifact contract, data lineage, and promotion evidence.

| Profile | Name | Input | Current role |
| --- | --- | --- | --- |
| `hk_low_vol_dividend_quality` | HK Low-Volatility Dividend Quality | `feature_snapshot` | Runtime-enabled at the strategy-package level; use dry-run only until artifact, broker, notification, and operator evidence pass. |

### Research-only and external scaffold profiles

The following profiles are kept for research reproducibility or future review and should not be exposed as current configurable live profiles:

- `hk_index_mean_reversion`
- `hk_etf_regime_rotation`
- external snapshot scaffold names such as `hk_shareholder_yield_quality`, `hk_free_cash_flow_quality`, and other candidates tracked by `HkEquitySnapshotPipelines`

Use `get_runtime_enabled_profiles()` as the source of truth for profiles that downstream platforms may present for runtime configuration.

## How this connects to execution

Platform repositories consume this package through strategy loaders and runtime metadata. They own broker credentials, market-data access, account state, dry-run/live switches, order submission, notifications, deployment settings, and rollback controls.

Supported HK runtime platforms currently include:

- `InteractiveBrokersPlatform`
- `LongBridgePlatform`

## Evidence and live enablement

README files are project maps, not fixed performance reports. Before enabling or changing a live profile, rerun the relevant research, snapshot, or readiness tooling and review short, medium, and long windows where applicable:

- return and benchmark-relative return
- maximum drawdown and drawdown stability
- turnover, costs, lot-size, slippage, suspension, VCM, and CAS behavior
- data freshness and artifact version
- dry-run order previews, bilingual notification logs, rollout controls, and operator approval

If evidence is stale, incomplete, or the profile is research-only, keep it out of live runtime settings.

## Quick start

```bash
python -m pip install -e '.[test]'
python -m pytest -q
```

## Inspect runtime readiness

These commands are read-only unless you explicitly pass an evidence file to a validator:

```bash
python scripts/print_hk_live_enablement_matrix.py --json
python scripts/print_hk_runtime_readiness.py --profile hk_high_dividend_low_vol_trend --platform longbridge --json
python scripts/print_hk_runtime_readiness.py --profile hk_low_vol_dividend_quality --platform longbridge --json
python scripts/validate_hk_runtime_live_enablement.py --print-template --profile hk_high_dividend_low_vol_trend --platform longbridge --json
```

For local smoke coverage of the ETF rotation path:

```bash
python scripts/smoke_hk_listed_global_etf_rotation_dry_run.py --json
```

## Deploy safely

1. Keep broker credentials and account identifiers outside Git.
2. Use platform repositories for dry-run, paper, or live execution switches.
3. Confirm strategy evidence and platform dry-run output before enabling scheduled execution.
4. Review generated orders, notifications, artifact URIs, and rollback settings.
5. Start with small staged exposure and keep kill-switch procedures documented in the platform repository.

## Repository layout

- `src/`: strategy implementations, catalog metadata, entrypoints, and readiness policies.
- `tests/`: unit, contract, and regression tests.
- `docs/`: integration notes and live-enablement evidence guides.
- `scripts/`: local research, smoke, readiness, and evidence helpers.

## Useful docs

- [`docs/platform_integration.md`](docs/platform_integration.md)
- [`docs/hk_low_vol_dividend_quality_live_enablement.md`](docs/hk_low_vol_dividend_quality_live_enablement.md)
- [`docs/research/hk_high_dividend_low_vol_trend.md`](docs/research/hk_high_dividend_low_vol_trend.md)
- [`docs/research/hk_listed_global_etf_rotation.md`](docs/research/hk_listed_global_etf_rotation.md)
- [`docs/research/hk_index_mean_reversion.md`](docs/research/hk_index_mean_reversion.md)
- [`docs/research/hk_etf_regime_rotation.md`](docs/research/hk_etf_regime_rotation.md)
- [`docs/research/hk_quant_strategy_ideas.md`](docs/research/hk_quant_strategy_ideas.md)

## Safety and contribution notes

- Do not commit secrets, tokens, cookies, broker credentials, account identifiers, or private order data.
- Keep behavior changes small and include tests or reproducible evidence commands.
- Do not promote a research profile into live runtime settings without the documented evidence gates.

## License

See [LICENSE](LICENSE).
