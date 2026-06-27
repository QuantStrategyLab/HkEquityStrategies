# HK Low-Volatility Dividend Quality live-enable runbook

[简体中文](hk_low_vol_dividend_quality_snapshot_live_enablement.zh-CN.md)

This runbook is the operational gate for making `hk_low_vol_dividend_quality_snapshot` truly live-enable capable. The strategy is runtime-enabled in the HK strategy package, but real order submission must remain blocked until every evidence gate below passes.

## Repository merge order

1. `HkEquitySnapshotPipelines`: merge the snapshot proxy-cycle / promotion-evidence PR first.
2. `HkEquityStrategies`: merge the runtime strategy, readiness, and evidence-gate PR.
3. Create a release tag for `HkEquityStrategies` after merge.
4. `LongBridgePlatform` and `InteractiveBrokersPlatform`: update `requirements.txt` from the temporary HK strategy commit SHA to the release tag, then merge platform PRs.

Do not remove platform dry-run mode only because the package PRs merged.

## Runtime inputs

`hk_low_vol_dividend_quality_snapshot` is snapshot-backed and requires these runtime artifacts:

- `hk_low_vol_dividend_quality_snapshot_factor_snapshot_latest.csv`
- `hk_low_vol_dividend_quality_snapshot_factor_snapshot_latest.csv.manifest.json`
- point-in-time lineage / artifact-pack validation evidence from `HkEquitySnapshotPipelines`

Required platform env placeholders before real artifact publication:

```bash
# LongBridge
LONGBRIDGE_FEATURE_SNAPSHOT_PATH=<required>
LONGBRIDGE_FEATURE_SNAPSHOT_MANIFEST_PATH=<required>
LONGBRIDGE_DRY_RUN_ONLY=true

# IBKR
IBKR_FEATURE_SNAPSHOT_PATH=<required>
IBKR_FEATURE_SNAPSHOT_MANIFEST_PATH=<required>
IBKR_DRY_RUN_ONLY=true
```

After artifact publication, replace placeholders with stable `gs://`, `s3://`, or `https://` URIs that do not contain token, signature, password, or other secret-like query parameters.

## Pre-live validation commands

Render readiness for both platforms:

```bash
python scripts/print_hk_runtime_readiness.py --profile hk_low_vol_dividend_quality_snapshot --platform longbridge --json
python scripts/print_hk_runtime_readiness.py --profile hk_low_vol_dividend_quality_snapshot --platform ibkr --json
```

Generate the evidence template:

```bash
python scripts/validate_hk_runtime_live_enablement.py \
  --print-template \
  --profile hk_low_vol_dividend_quality_snapshot \
  --platform longbridge \
  --json > live-enable-evidence.longbridge.json

python scripts/validate_hk_runtime_live_enablement.py \
  --print-template \
  --profile hk_low_vol_dividend_quality_snapshot \
  --platform ibkr \
  --json > live-enable-evidence.ibkr.json
```

Validate completed evidence packs:

```bash
python scripts/validate_hk_runtime_live_enablement.py \
  --evidence-file live-enable-evidence.longbridge.json \
  --json

python scripts/validate_hk_runtime_live_enablement.py \
  --evidence-file live-enable-evidence.ibkr.json \
  --json
```

The result must be `validation_status=passed` and `live_enablement_allowed=true` before dry-run can be removed.

## Required evidence

The evidence pack must prove all of the following:

- out-of-sample / walk-forward backtest with at least three independent OOS folds
- max drawdown <= 30%
- annual-return-to-max-drawdown ratio >= 0.50
- max single-period return contribution <= 60%
- annualized turnover <= 100%
- positive annual return and positive excess return versus `02800`
- point-in-time factor snapshot lineage, no look-ahead, no survivorship bias, no full-sample parameter selection
- validated factor snapshot artifact, manifest, contract version, and lineage URIs
- HK single-name equity due diligence, not ETF due diligence
- Stock Connect eligibility or direct broker route evidence
- board lot, trading currency, corporate action, suspension/trading status, dividend/payout, fee/stamp-duty, and broker permission evidence
- dry-run order preview with no fractional-share, lot-size, currency, or symbol-mapping errors
- raw order preview, quote snapshot, and fee breakdown artifacts with sha256 provenance
- liquidity/ADV, board-lot, odd-lot, market-session, VCM/price-band, and equity spread/trading-status guards
- bilingual EN/ZH-Hans notification delivery log with redacted sensitive fields
- staged rollout, rollback, kill switch, tripwires, severe-weather trading, and VCM cooling-off handling
- explicit operator approval, live-rollout approval, and dry-run-removal approval references

## Platform switch-plan smoke checks

LongBridge:

```bash
cd ../LongBridgePlatform
.venv/bin/python scripts/print_strategy_switch_env_plan.py \
  --profile hk_low_vol_dividend_quality_snapshot \
  --account-region HK \
  --dry-run-only \
  --json
```

IBKR:

```bash
cd ../InteractiveBrokersPlatform
.venv/bin/python scripts/print_strategy_switch_env_plan.py \
  --profile hk_low_vol_dividend_quality_snapshot \
  --dry-run-only \
  --deployment-selector hk-verify \
  --account-scope HK \
  --service-name interactive-brokers-hk-verify-service \
  --json
```

Both commands must show:

- `enabled=true`
- `input_mode=feature_snapshot`
- required feature snapshot path and manifest path
- factor snapshot filename hints for `hk_low_vol_dividend_quality_snapshot_factor_snapshot_latest.csv`

## Final dry-run removal gate

Dry-run removal is allowed only after:

1. all four repository PRs are merged in dependency order;
2. platform dependencies point to a merged HK strategy release tag;
3. production factor snapshot artifact, manifest, and lineage are published;
4. both platform switch plans point to the published artifact URIs;
5. dry-run order previews and bilingual notifications are captured;
6. evidence packs pass the validator for the target platform;
7. operator approval references are recorded.

Until then, keep `LONGBRIDGE_DRY_RUN_ONLY=true` and `IBKR_DRY_RUN_ONLY=true`.
