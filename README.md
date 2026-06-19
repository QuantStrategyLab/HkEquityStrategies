# HkEquityStrategies

[Chinese README](README.zh-CN.md)

> Investing involves risk. This project does not provide investment advice and is for education, research, and engineering review only.

## What this repository is

`HkEquityStrategies` is the Hong Kong equity strategy package for QuantStrategyLab. It contains reusable strategy implementations, manifests, catalog metadata, runtime adapters, and live-enablement checks shared by HK-capable platform repositories.

This repository is a strategy layer, not a broker or deployment layer. It does not store broker credentials, submit orders by itself, publish snapshot artifacts, or decide whether a profile is safe for live trading without external evidence.

## Current runtime surface

Canonical profile names were simplified in this branch. The old names are not kept as aliases, so platform repositories should reference the canonical names below through `STRATEGY_PROFILE` or `RUNTIME_TARGET_JSON`.

### Direct runtime strategies

These profiles use platform-provided `market_history` and do not require a separate snapshot artifact before the strategy entrypoint can produce target weights.

| Profile | Name | Input | Benchmark | Current role |
| --- | --- | --- | --- | --- |
| `hk_global_etf_tactical_rotation` | HK Global ETF Tactical Rotation | `market_history` | `02800` | Retained HK ETF runtime profile with broader ETF exposure and heavier product checks. |

### Snapshot-backed runtime strategy

The strategy package exposes one promoted snapshot-backed runtime entrypoint. `HkEquitySnapshotPipelines` owns the artifact contract, production data lineage, and promotion evidence.

| Profile | Name | Input | Benchmark | Current role |
| --- | --- | --- | --- | --- |
| `hk_low_vol_dividend_quality_snapshot` | HK Low-Vol Dividend Quality Snapshot | `feature_snapshot` + manifest | `02800` | Retained HK snapshot-backed runtime candidate; production point-in-time evidence is still required. |

### Removed research profiles

Rejected prototypes are no longer part of the public catalog, manifests, entrypoints, runtime adapters, or snapshot contracts. Platform repositories should only expose profiles returned by `get_runtime_enabled_profiles()`.

See [`docs/research/hk_strategy_selection_20260603.md`](docs/research/hk_strategy_selection_20260603.md) for retained and rejected strategy notes.

## Performance and evidence boundary

The research numbers in this repository are review evidence, not return promises. Before enabling or changing any live profile, rerun the relevant research/readiness commands and review short, medium, and long windows where applicable:

- return and benchmark-relative return
- maximum drawdown and drawdown stability
- turnover, costs, lot-size, slippage, suspension, VCM, and CAS behavior
- data freshness and artifact version
- broker dry-run order preview, bilingual notification logs, rollout controls, and operator approval

If evidence is stale, incomplete, or the profile is not returned by `get_runtime_enabled_profiles()`, keep it out of live runtime settings.

## Quick start

```bash
python -m pip install -e '.[test]'
python -m pytest -q
```

## Inspect runtime readiness

These commands are read-only unless you explicitly pass an evidence file to a validator:

```bash
python scripts/print_hk_live_enablement_matrix.py --json
python scripts/print_hk_runtime_readiness.py --profile hk_global_etf_tactical_rotation --platform longbridge --json
python scripts/print_hk_runtime_readiness.py --profile hk_low_vol_dividend_quality_snapshot --platform longbridge --json
python scripts/validate_hk_runtime_live_enablement.py --print-template --profile hk_global_etf_tactical_rotation --platform longbridge --json
```

For local smoke coverage of the ordinary ETF rotation path:

```bash
python scripts/smoke_hk_global_etf_tactical_rotation_dry_run.py --json
```

## How this connects to execution

Platform repositories consume this package through strategy loaders and runtime metadata. They own broker credentials, market-data access, account state, dry-run/live switches, order submission, notifications, deployment settings, and rollback controls.

Supported HK runtime platforms currently include:

- `InteractiveBrokersPlatform`
- `LongBridgePlatform`

## Deploy safely

1. Keep broker credentials and account identifiers outside Git.
2. Use platform repositories for dry-run, paper, or live execution switches.
3. Confirm strategy evidence and platform dry-run output before enabling scheduled execution.
4. Review generated orders, notifications, artifact URIs, and rollback settings.
5. Start with small staged exposure and keep kill-switch procedures documented in the platform repository.

## Repository layout

- `src/`: strategy implementations, manifests, catalog metadata, runtime adapters, and readiness policies.
- `tests/`: unit, contract, and regression tests.
- `docs/`: integration notes, strategy research, and live-enablement evidence guides.
- `scripts/`: local research, smoke, readiness, and evidence helpers.

## Useful docs

- [`docs/platform_integration.md`](docs/platform_integration.md)
- [`docs/research/hk_strategy_selection_20260603.md`](docs/research/hk_strategy_selection_20260603.md)
- [`docs/research/hk_global_etf_tactical_rotation.md`](docs/research/hk_global_etf_tactical_rotation.md)
- [`docs/hk_low_vol_dividend_quality_snapshot_live_enablement.md`](docs/hk_low_vol_dividend_quality_snapshot_live_enablement.md)

## Safety and contribution notes

- Do not commit secrets, tokens, cookies, broker credentials, account identifiers, or private order data.
- Keep behavior changes small and include tests or reproducible evidence commands.
- Do not promote a research profile into live runtime settings without the documented evidence gates.

## Community and security

- See [CONTRIBUTING.md](CONTRIBUTING.md) for pull request scope, local verification, and documentation expectations.
- Follow [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md) for maintainer and contributor conduct.
- Report credential, automation, broker, exchange, or cloud-resource vulnerabilities through [SECURITY.md](SECURITY.md); do not open public issues for secrets or live-execution risk.

## License

See [LICENSE](LICENSE).
