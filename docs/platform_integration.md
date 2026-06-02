# Platform Integration


## 中文摘要

- 用途：本文档围绕 `Platform Integration`，用于理解 `HkEquityStrategies` 的配置、运行、部署、研究或验收边界。
- 主要覆盖：`Supported platforms`、`Required platform mode`、`InteractiveBrokersPlatform`、`LongBridgePlatform`、`Contract boundaries`。
- 阅读顺序：先确认边界、输入输出和权限要求，再执行文档里的命令、CI、dry-run、发布或切换步骤。
- 风险提示：涉及实盘、密钥、权限、Cloud Run、交易所或券商 API 的变更，必须先在测试环境或 dry-run 验证；不要只凭示例直接修改生产。
- 英文正文保留更完整的命令、字段名和配置键；如果摘要和正文不一致，以正文中的实际命令和配置为准。

## Supported platforms

The HK strategy surface is split by input style:

- Runtime non-snapshot/direct `market_history`: `hk_listed_global_etf_rotation`, `hk_high_dividend_low_vol_trend`.
- Research/backtest-only: `hk_index_mean_reversion`, `hk_etf_regime_rotation`; they are not runtime catalog profiles.
- Snapshot-backed scaffold: `hk_blue_chip_leader_rotation`, `hk_low_vol_dividend_quality`, `hk_liquid_momentum_quality`, `hk_residual_momentum_quality`, `hk_shareholder_yield_quality`, `hk_composite_factor_quality_value_momentum`, `hk_factor_mix_qvlm_risk_parity`, `hk_central_soe_value_quality_select`, `hk_free_cash_flow_quality`, `hk_southbound_flow_momentum`, `hk_ah_premium_relative_value`, `hk_index_rebalance_event`; their artifact contracts, strategy helpers, and publication flow live in `HkEquitySnapshotPipelines`.

The runtime catalog profiles declare structural support for:

- `ibkr` (`InteractiveBrokersPlatform`)
- `longbridge` (`LongBridgePlatform`)

The strategy package does not import platform code. Platforms load it through the same catalog/runtime-adapter contract used by `UsEquityStrategies`. `hk_listed_global_etf_rotation` and `hk_high_dividend_low_vol_trend` are HK runtime catalog profiles. `hk_blue_chip_leader_rotation`, `hk_low_vol_dividend_quality`, `hk_liquid_momentum_quality`, `hk_residual_momentum_quality`, `hk_shareholder_yield_quality`, `hk_composite_factor_quality_value_momentum`, `hk_factor_mix_qvlm_risk_parity`, `hk_central_soe_value_quality_select`, `hk_free_cash_flow_quality`, `hk_southbound_flow_momentum`, `hk_ah_premium_relative_value`, and `hk_index_rebalance_event` are snapshot scaffolds in `HkEquitySnapshotPipelines`; `hk_index_mean_reversion` and `hk_etf_regime_rotation` are research/backtest-only candidates. Platform repositories should expose only runtime-enabled HK profiles as selectable runtime targets. Research and snapshot-scaffold profiles remain in docs/backtests until they are explicitly promoted.

Integration tooling can call `get_external_snapshot_scaffold_profiles()` to display these snapshot-backed names as non-selectable scaffolds. Do not merge that helper with `get_runtime_enabled_profiles()`; the former is documentation/guardrail metadata, the latter is the platform selection surface.

## Live-enable matrix

Use the strategy-package matrix as the machine-readable source for platform UI/status/switch-plan decisions:

```bash
python scripts/print_hk_live_enablement_matrix.py --json
python scripts/print_hk_live_enablement_matrix.py --profile hk_high_dividend_low_vol_trend --json
python scripts/print_hk_live_enablement_matrix.py --profile hk_shareholder_yield_quality --json
```

Matrix semantics:

- `selectable_by_platform=true` means the profile is a strategy-package runtime profile. It still requires platform dry-run/paper/live mode, account scope, and operator approval to be handled by the platform repository.
- `live_enablement_gate=requires_runtime_live_enablement_evidence` means a non-snapshot runtime profile must pass `validate_hk_runtime_live_enablement.py` evidence validation before dry-run can be removed.
- `live_enablement_gate=requires_snapshot_promotion_matrix_and_production_evidence` means the profile is only a snapshot scaffold. It must not be selectable until the snapshot repository promotion matrix, artifact-pack validation, live-evidence validation, and a later strategy-package runtime promotion all pass.
- `live_enablement_gate=research_backtest_only_not_platform_selectable` means the profile stays in research docs only.

The matrix currently reports the first snapshot candidates as `hk_low_vol_dividend_quality`, `hk_shareholder_yield_quality`, and `hk_free_cash_flow_quality`. Treat this as evidence-collection priority, not permission to deploy them. The snapshot repository's `recommended_live_enablement_sequence` is the detailed promotion order; `hk_free_cash_flow_quality` must also prove HSI/S&P-style FCF formula lineage, EV market-cap/debt/cash/FX inputs, reporting-date/restatement/as-of controls, sector normalization, and financial/real-estate/negative-FCF exceptions before platform selection. Momentum-factor profiles stay in later research stages until residual, liquid, and composite variants are compared and HSI close-to-high descriptors are reconciled with MSCI-style 6/12-month one-month-skip risk-adjusted momentum, volatility normalization, turnover buffers, sector/capacity controls, and momentum-crash stress.

For snapshot scaffolds, `research_evidence_urls` now includes profile-specific external sources in addition to the internal research note. Platform status pages can display those URLs to explain the promotion thesis, but they must still keep `selectable_by_platform=false` until the snapshot promotion and live-evidence gates pass.

The matrix also exposes `evidence_uri_policy`, `evidence_freshness_policy`, `runtime_etf_product_policy`, `runtime_market_data_policy`, `execution_capacity_policy`, `dry_run_order_preview_policy`, `rollout_risk_policy`, and `notification_audit_policy`. Platform switch-plan tooling should apply them before accepting an evidence pack: evidence URIs must use `https://`, `gs://`, or `s3://`, links containing token/password/signature-like query parameters must be rejected before they are logged, stored, or displayed, non-approval evidence sections must be fresh, runtime `market_history` must prove source name, coverage dates, stable source / quality-report / point-in-time data-dictionary URIs, adjusted prices, distributions, corporate actions, stale-quote controls, trading status, ETF NAV/iNAV, and stamp-duty/exemption sources, ETF product due diligence must prove per-symbol HKEX ETP/ETF classification, current official product document URI, underlying index or reference-asset source URI, NAV/iNAV source URI, tracking error/difference review, ETF Connect / Stock Connect eligible or sell-only status, Southbound ETF daily turnover / fund-flow trend, broker Southbound ETF buy-route availability, cross-boundary settlement / holiday / eligibility-change review, leveraged/inverse/synthetic/futures-based or complex-product review, market-maker/liquidity-provider check, KID/prospectus risk review, multi-counter currency and creation/redemption handling, distribution/tax/fee treatment, broker product permission, trading-currency/board-lot/distribution/corporate-action handling, dry-run order previews must satisfy ADV / liquidity / board-lot / odd-lot / VCM capacity checks, preserve raw order-preview / quote-snapshot / fee-breakdown artifact URIs with sha256 provenance and broker fee reconciliation, plus bilingual EN/ZH-Hans notification audit logs with a correlation id and stable delivery-log URI, and live rollout must start with capital caps, tripwires, kill switch, SWT/VCM runbooks, and a pre-scale observation window.

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

Snapshot-backed profiles additionally require snapshot artifacts. The current HK snapshot profiles are scaffold-only, so these variables are examples for future rollout, not current production settings:

```bash
IBKR_FEATURE_SNAPSHOT_PATH=<published/hk_blue_chip_leader_rotation_feature_snapshot_latest.csv>
IBKR_FEATURE_SNAPSHOT_MANIFEST_PATH=<published/hk_blue_chip_leader_rotation_feature_snapshot_latest.csv.manifest.json>
```

Use the profile-specific artifact names from `HkEquitySnapshotPipelines/docs/artifact_contract.md` when promoting `hk_low_vol_dividend_quality`, `hk_liquid_momentum_quality`, `hk_residual_momentum_quality`, `hk_shareholder_yield_quality`, `hk_composite_factor_quality_value_momentum`, `hk_factor_mix_qvlm_risk_parity`, `hk_central_soe_value_quality_select`, `hk_free_cash_flow_quality`, `hk_southbound_flow_momentum`, `hk_ah_premium_relative_value`, or `hk_index_rebalance_event`; do not reuse the blue-chip filenames.

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

Snapshot-backed profiles additionally require snapshot artifacts. The current HK snapshot profiles are scaffold-only, so these variables are examples for future rollout, not current production settings:

```bash
LONGBRIDGE_FEATURE_SNAPSHOT_PATH=<published/hk_blue_chip_leader_rotation_feature_snapshot_latest.csv>
LONGBRIDGE_FEATURE_SNAPSHOT_MANIFEST_PATH=<published/hk_blue_chip_leader_rotation_feature_snapshot_latest.csv.manifest.json>
```

Use the profile-specific artifact names from `HkEquitySnapshotPipelines/docs/artifact_contract.md` when promoting `hk_low_vol_dividend_quality`, `hk_liquid_momentum_quality`, `hk_residual_momentum_quality`, `hk_shareholder_yield_quality`, `hk_composite_factor_quality_value_momentum`, `hk_factor_mix_qvlm_risk_parity`, `hk_central_soe_value_quality_select`, `hk_free_cash_flow_quality`, `hk_southbound_flow_momentum`, `hk_ah_premium_relative_value`, or `hk_index_rebalance_event`; do not reuse the blue-chip filenames.

## Runtime readiness checklist

Render the strategy-package readiness plan before changing either platform:

```bash
python scripts/print_hk_runtime_readiness.py --profile hk_listed_global_etf_rotation --platform ibkr --json
python scripts/print_hk_runtime_readiness.py --profile hk_listed_global_etf_rotation --platform longbridge --json
python scripts/print_hk_runtime_readiness.py --profile hk_high_dividend_low_vol_trend --platform ibkr --json
python scripts/print_hk_runtime_readiness.py --profile hk_high_dividend_low_vol_trend --platform longbridge --json
```

The plan is intentionally `dry_run_only=true` by default and does not deploy Cloud Run. It records:

- HK market defaults: `HK` / `XHKG` / `Asia/Hong_Kong` / `SEHK` / `HKD` / `.HK`.
- Managed symbols and required direct `market_history` inputs.
- Platform target conversion: IBKR accepts weight targets directly; LongBridge needs a portfolio snapshot for weight-to-value conversion.
- Dry-run checks for market-data permission, order preview, integer-share and broker lot-size validation, HKD cash lines, and bilingual operator notifications.
- ETF live-enable checks for stamp-duty / levy / minimum-commission treatment, bid/ask spread, slippage, distribution handling, stale quotes, NAV, market-maker liquidity, and suspension status.
- Profile-specific optimization checks. `hk_high_dividend_low_vol_trend` is the preferred lower-drawdown first HK live candidate; `hk_listed_global_etf_rotation` remains the broader higher-return candidate and needs per-symbol product evidence for all eight ETFs, with extra review for `03175` futures roll/margin/curve and complex-product suitability risk.
- Machine-readable live thresholds and evidence fields. `hk_listed_global_etf_rotation` currently requires max drawdown <= 30%, at least 3 OOS folds, max single-period return contribution <= 60%, and annualized turnover <= 150%; `hk_high_dividend_low_vol_trend` requires max drawdown <= 12%, at least 3 OOS folds, max single-period return contribution <= 60%, and annualized turnover <= 100%.
- Machine-readable `evidence_uri_policy`, `evidence_freshness_policy`, `runtime_etf_product_policy` with per-symbol ETF product due-diligence and ETF Connect / Southbound route requirements, `runtime_market_data_policy` with market-history provenance URI requirements, `execution_capacity_policy`, `dry_run_order_preview_policy`, `rollout_risk_policy`, and `notification_audit_policy`, shared with the live-enable matrix, readiness output, evidence template, and validation result.

HK ETF transfers are generally stamp-duty exempt under the Inland Revenue Department's ETF FAQ, but platform live approval must still capture broker order-preview evidence for the specific symbols because HKEX/broker fees, minimum commission, bid/ask spread, and product permission are separate from stamp duty.

Before removing dry-run from a runtime-enabled non-snapshot profile, generate and validate the runtime evidence pack:

```bash
python scripts/validate_hk_runtime_live_enablement.py --print-template --profile hk_high_dividend_low_vol_trend --platform longbridge --json > runtime-live-enable-evidence.json
python scripts/validate_hk_runtime_live_enablement.py --evidence-file runtime-live-enable-evidence.json --json
```

The runtime evidence template and validation result expose the same `evidence_uri_policy`, `evidence_freshness_policy`, `runtime_etf_product_policy`, `runtime_market_data_policy`, `execution_capacity_policy`, `dry_run_order_preview_policy`, `rollout_risk_policy`, and `notification_audit_policy` as the readiness and matrix outputs. The runtime evidence validator rejects non-positive annual return, less than three out-of-sample years, benchmark mismatch versus strategy metadata, non-positive excess return, missing survivorship/look-ahead controls, max drawdown or annualized turnover above the profile threshold, failed readiness checks, missing production market-history source provenance or market-data audit fields, missing broker fee/exemption/product-permission proof, missing per-symbol ETF product audit id, managed-symbol audit count below the strategy universe size, missing stable product-universe / official-product-document / underlying-index-or-reference-asset / NAV-or-iNAV / market-maker-or-liquidity-provider / distribution-tax-fee / fee-and-stamp-duty / broker-permission audit URIs, missing Stock Connect ETF eligibility / sell-only status and Southbound ETF turnover/fund-flow evidence, missing HKEX ETP classification, missing leveraged/inverse/synthetic/futures-based or complex-product review, missing market-maker/liquidity-provider check, missing KID/prospectus risk review, missing current official product-document review, missing NAV/iNAV reconciliation, missing tracking-difference review, missing ETF Connect / Stock Connect eligible or sell-only status, missing Southbound ETF turnover/fund-flow trend and broker route review, missing cross-boundary settlement / holiday / eligibility-change review, missing multi-counter currency / creation-redemption review, missing distribution/capital-distribution risk review, missing commodity-trust single-asset/storage risk review, missing high-dividend concentration/yield-trap review, missing trading-currency/board-lot/distribution/corporate-action verification, missing dry-run session id, missing stable raw order-preview / quote-snapshot / fee-breakdown artifact URI and 64-character hex sha256 provenance, missing non-sample/redaction/quote-coverage/broker-fee-reconciliation/strategy-decision-reconciliation proof, missing dry-run order-preview notification audit fields (`hk_live_enablement_notification.v1`, `hk_runtime_live_enablement_dry_run`, EN/ZH-Hans locales, correlation id, redaction, stable delivery-log URI), missing rollback/switch plan, missing staged-rollout/tripwire/kill-switch/SWT-runbook proof, missing section-level stable `evidence_uri` (`https://`, `gs://`, or `s3://`), missing/stale/future-dated `evidence_generated_at`, over-capacity ADV/order previews, missing HK board-lot / odd-lot / session-routing / VCM controls, secret-like query parameters in evidence URIs, or missing operator approval reference.

## Contract boundaries

- `HkEquityStrategies` owns non-snapshot strategy metadata, entrypoint evaluation, and runtime adapter declarations.
- `HkEquitySnapshotPipelines` owns snapshot-backed artifact contracts, raw data normalization, snapshot publication, and research/backtest-only work that is not platform-selectable.
- Platform repositories own broker connection, market symbols, order sizing, notification delivery, and runtime reports.

Before any HK profile is made live-selectable, the platform must also satisfy `backtest_validation_policy`: max drawdown <= 30% unless a stricter profile threshold applies, point-in-time inputs only, no look-ahead / survivorship bias, no full-sample return-based parameter selection, walk-forward or OOS evidence, multi-period robustness, at least 3 independent OOS folds, each OOS fold max drawdown <= 30%, max single-period return contribution <= 60%, annual-return-to-max-drawdown ratio >= 0.50, parameter-sensitivity / holdout stability, net-of-cost return validation, benchmark/cost/slippage alignment, lot-size/suspension/VCM/CAS handling, leverage/shorting/margin feasibility, liquidity/capacity controls, fee/slippage/spread stress that preserves positive excess return, worst-month / worst-rebalance-loss and time-under-water recovery limits, cross-strategy correlation and aggregate drawdown-budget controls, and staged rollout tripwires.

Before a platform exposes any snapshot-backed profile, review the snapshot repository promotion matrix so the profile has an explicit priority, recommended live-enable stage/action, research evidence, production-data dependency list, profile-specific production-source audit policy, production source coverage/provenance URI requirements, and live-enable threshold set. For the first quality/yield snapshot candidates, also read `quality_yield_live_enablement_policy`: it requires low-vol dividend / shareholder-yield / FCF same-universe ablation, forecast-dividend-yield versus trailing-yield ablation, stale estimate-revision controls, yield-trap controls, HSHYLV/HSSCHYS-style Southbound eligibility, three-year cash-dividend records, payout-ratio bounds, price-crash screens, high-volatility exclusion, financial-soundness screens, buyback spend versus share-count reduction, HKEX next-day repurchase returns, treasury-share retention/cancellation/resale, treasury-share resale/dilution, moratorium/blackout/connected-person controls, post-buyback financing review, FCF formula/EV input/reporting-date/restatement/sector-exception handling, sector/rate-cycle stress, and order-preview provenance before dry-run removal. For HK momentum stock selection, also read the matrix fields `momentum_live_enablement_comparison` and `momentum_live_enablement_policy`: they rank `hk_residual_momentum_quality` as the closest US-style residual/industry-neutral momentum analogue, `hk_liquid_momentum_quality` as the simpler price-momentum fallback, and `hk_composite_factor_quality_value_momentum` as a multi-factor candidate requiring factor ablation before live evidence; they also require residual/liquid/composite ablation, quality/value/low-volatility sleeve comparison, HSI/MSCI descriptor reconciliation, 52-week-high versus 12-1 momentum comparison, 6/12-month one-month-skip risk-adjusted momentum, volatility normalization, industry-neutral and quality-screen ablation, turnover-buffer and capacity checks, reversal/high-beta/suspension/Southbound stress windows, and dry-run order-preview provenance before any momentum profile can remove dry-run. For HK-specific flow/valuation/event scaffolds, also read `special_situation_live_enablement_policy`: it requires official HKEX / Hang Seng source provenance, Stock Connect calendar/historical daily turnover/top-10 turnover/CCASS shareholding/eligible-security/data-dissemination/raw-vs-vendor reconciliation coverage, AH close-time / price-ratio / FX alignment, AH Smart switch-threshold comparison, A-share access / shorting / settlement constraint review, extreme-premium false-reversal stress, HSI methodology/operation-guide versioning, schedule-file versions, next-review notice scope, review-result press-release timestamps, constituent weight/pro-forma provenance, index review announcement-to-effective windows, add/delete labels, MOC-vs-next-open and pro-forma-weighted ablations, fast-entry / suspension / buffer-rule exceptions, HKEX CAS / market-on-close random-close / two-stage price-limit / order-rejection / passive-flow imbalance controls, signal-decay ablation, crowding/slippage stress, and dry-run order-preview provenance before Southbound-flow, AH-premium, or index-rebalance profiles can remove dry-run. The matrix field `quality_growth_live_enablement_policy` gates the active `hk_quality_growth_low_volatility` scaffold with quality/growth/low-vol ablation, HSI QGLV four-component lineage (ROE, accruals ratio, cash-flow-to-debt, Growth in ROA adjusted by P/B), winsorized z-score / Financials / negative-equity / missing-factor handling, MSCI quality and MSCI HK-listed Southbound Quality ROE / stable-earnings / low-leverage reconciliation, HSI low-volatility quality-screen checks, minimum-volatility optimizer constraints, cash-conversion / accrual quality-trap controls, Southbound and sector-neutral checks, real-estate/financial concentration, growth-deceleration, valuation/regulation/low-vol crowding stress, and production fundamentals provenance. The matrix field `factor_mix_live_enablement_policy` gates the active `hk_factor_mix_qvlm_risk_parity` scaffold with Q/V/L/M factor-history, HSI QVLM parent universe, component-index returns, risk-parity weight / 12% cap lineage, factor-volatility and covariance/correlation provenance, HSI equal-weight factor-mix benchmark, MSCI Factor Mix A-Series equal-weight Q/V/L component and capped-methodology controls, equal-weight/composite-QVM/leave-one-out/component-overlap ablations, factor-crowding / factor-correlation-breakdown / cap-induced-turnover and low-vol/momentum/value stress windows, HK costs/capacity, and dry-run order-preview provenance. The matrix field `policy_value_live_enablement_policy` gates the active `hk_central_soe_value_quality_select` scaffold with central-SOE ownership provenance, SASAC/MOF source-list effective dates and effective-date drift, largest-shareholder look-through chain, HKEX Southbound eligibility history, HSI value/quality factor-index reconciliation, HSI Z-score / missing-measure / 40% screening / buffer-rule / 5% and 10% capping provenance, broad value-quality / HSI value-quality / existing quality-yield ablations, concentration / cap-turnover / policy-event stress, HK costs/capacity, and dry-run order-preview provenance. The matrix field `baseline_rotation_live_enablement_policy` gates the HK blue-chip baseline rotation scaffold; `future_research_backlog` now contains research-only `hk_earnings_revision_quality_overlay`, `hk_low_size_quality_liquidity_premium`, `hk_stock_connect_inclusion_event_flow`, `hk_short_selling_pressure_risk_overlay`, `hk_director_dealing_disclosure_quality_overlay`, `hk_dually_traded_liquid_reversal_overlay`, `hk_earnings_announcement_drift_overlay`, `hk_lottery_stock_risk_exclusion_overlay`, `hk_equity_financing_dilution_risk_overlay`, `hk_connected_transaction_governance_risk_overlay`, `hk_takeover_privatization_event_spread_overlay`, `hk_distribution_ex_date_entitlement_overlay`, `hk_ipo_lockup_overhang_event_overlay`, `hk_audit_opinion_suspension_risk_overlay`, `hk_share_repurchase_execution_signal_overlay`, `hk_liquid_pairs_cointegration_stat_arb_overlay`, `hk_macro_liquidity_inflation_rate_sensitivity_overlay`, `hk_turn_of_month_lunar_new_year_calendar_overlay`, `hk_etf_premium_discount_tracking_quality_overlay`, `hk_asset_growth_net_issuance_quality_overlay`, `hk_accrual_quality_earnings_persistence_overlay`, `hk_fscore_gross_profitability_quality_overlay`, `hk_shareholding_concentration_free_float_risk_overlay`, `hk_amihud_liquidity_risk_capacity_overlay`, `hk_analyst_dispersion_coverage_risk_overlay`, and `hk_financial_distress_deleveraging_risk_overlay`, and platform tooling can read the mirrored `snapshot_future_research_live_enablement_policy` from the HK strategy live-enable matrix and must also read the snapshot matrix nested `future_research_live_enablement_policy`; keep these and any newly discovered non-scaffolded ideas non-selectable until new snapshot contracts, candidate-specific production source audits, point-in-time consensus estimate/revision history, free-float market-cap/size-factor history, Stock Connect eligibility-change history, designated short-selling security / short-turnover history, disclosed-interest / director-dealing notice history, filing-lag / correction / blackout / moratorium context, dual-listing mapping / reversal cost history, HKEXnews announcement / profit-warning / PEAD event history, lottery-feature IVOL/ISKEW/MAX/price history, equity-financing rights/open-offer/placement/convertible dilution history, connected-transaction announcement/circular/shareholder-approval and governance-risk history, takeover possible-offer/firm-intention/offer-period/spread/completion-risk history, distribution ex-date/record-date/payment/price-adjustment/settlement history, IPO listing/cornerstone/pre-IPO lock-up expiry/overhang/stabilization history, audit-opinion disclaimer/adverse/qualified/going-concern/suspension/resumption/delisting history, share-repurchase daily execution / mandate / treasury-share retention-resale / post-buyback dilution history, pairs cointegration / spread stability / borrow-shortability / pair-leg cost history, CPI / inflation / base-rate / HIBOR / aggregate-balance history, macro release-lag / revision / currency-peg history, sector rate-beta / inflation-beta / property-financial sensitivity history, HKEX trading-calendar / turn-of-month / Chinese Lunar New Year / severe-weather / settlement / short-sale-turnover history, HK-listed ETF NAV/iNAV / premium-discount / tracking-difference / market-maker / complex-product history, asset-growth / net-share-issuance / reporting-date / restatement / sector-exception history, operating-accrual / cash-conversion / earnings-persistence / qualified-opinion history, Piotroski FSCORE / gross-profitability / reporting-lag history, SFC high-shareholding-concentration / CCASS concentration / free-float / ramp-and-dump red-flag history, Amihud illiquidity / market-wide liquidity-shock / liquidity-beta / VCM-CAS / price-impact history, analyst forecast dispersion / coverage / recommendation-target-price / staleness history, financial distress / Z-score / debt-maturity / interest-coverage / deleveraging history, analyst coverage/vendor, HSICS, official eligible-security methodology, HKEX regulated-short-selling controls, or SFC/HKEX DI-notice controls, liquidity/capacity controls, same-universe ablations, walk-forward evidence, dry-run order previews, bilingual notifications, rollout controls, and operator approval exist.

```bash
cd ../HkEquitySnapshotPipelines
PYTHONPATH=src python scripts/print_snapshot_promotion_matrix.py --json
```

Before a platform exposes any snapshot-backed profile, run the snapshot repository gate:

```bash
PYTHONPATH=src python scripts/print_snapshot_readiness.py --all --platform longbridge --json
```

The matrix must no longer report `live_enable_gate=blocked_until_production_evidence` before platform switch-plan tooling can expose a snapshot profile.

After artifacts are published, validate the published directory before setting platform env vars:

```bash
hkeq-validate-snapshot-artifact-pack --profile hk_low_vol_dividend_quality --artifact-dir <published-artifact-dir> --json
```

Do not set `IBKR_FEATURE_SNAPSHOT_PATH` or `LONGBRIDGE_FEATURE_SNAPSHOT_PATH` to a directory that fails artifact-pack validation.

The final pre-live gate is the evidence pack validator:

```bash
hkeq-validate-live-enable-evidence --print-template --profile hk_low_vol_dividend_quality --platform longbridge --json > live-enable-evidence.json
hkeq-validate-live-enable-evidence --evidence-file <live-enable-evidence.json> --json
```

Do not remove platform dry-run mode or mark a snapshot-backed profile as `runtime_enabled` unless this evidence validator passes. The validator now rejects non-positive annual return, less than three out-of-sample years, benchmark mismatch, non-positive excess return, max drawdown above 30%, rolling OOS fold max drawdown above 30%, annual-return-to-max-drawdown ratio below 0.50, fewer than 3 OOS folds, max single-period return contribution above 60%, annualized turnover above the profile cap, missing HK cost-model coverage, missing survivorship/look-ahead bias controls, missing dry-run order-preview artifact provenance (`dry_run_session_id`, stable raw order-preview / quote-snapshot / fee-breakdown URIs, sha256 values, redaction, quote coverage, broker-fee reconciliation, and strategy-decision reconciliation), missing bilingual notification audit fields, missing section-level stable `evidence_uri` (`https://`, `gs://`, or `s3://`), secret-like query parameters in evidence URIs, missing operator approval reference, or insufficient paper/dry-run windows.

## Runtime profile boundary

Do not set `STRATEGY_PROFILE=hk_blue_chip_leader_rotation`, `STRATEGY_PROFILE=hk_low_vol_dividend_quality`, `STRATEGY_PROFILE=hk_liquid_momentum_quality`, `STRATEGY_PROFILE=hk_residual_momentum_quality`, `STRATEGY_PROFILE=hk_shareholder_yield_quality`, `STRATEGY_PROFILE=hk_composite_factor_quality_value_momentum`, `STRATEGY_PROFILE=hk_factor_mix_qvlm_risk_parity`, `STRATEGY_PROFILE=hk_central_soe_value_quality_select`, `STRATEGY_PROFILE=hk_free_cash_flow_quality`, `STRATEGY_PROFILE=hk_southbound_flow_momentum`, `STRATEGY_PROFILE=hk_ah_premium_relative_value`, `STRATEGY_PROFILE=hk_index_rebalance_event`, `STRATEGY_PROFILE=hk_index_mean_reversion`, or `STRATEGY_PROFILE=hk_etf_regime_rotation` in Cloud Run while the profiles are not `runtime_enabled`. Platform status and switch-plan tooling should not expose these profiles as selectable runtime targets. `hk_listed_global_etf_rotation` and `hk_high_dividend_low_vol_trend` are runtime-enabled at the strategy-package level and can be selected by Cloud Run through `RUNTIME_TARGET_JSON` / `STRATEGY_PROFILE`; dry-run versus live execution remains a platform runtime setting.

## Risks before live trading

- Validate account permissions for SEHK/HKD or LongBridge HK trading before enabling real orders.
- Validate `XHKG` calendar availability in the deployment image.
- Validate lot-size behavior with a dry run; the strategy exposes `lot_size`, but platform order-sizing remains responsible for enforcing broker-specific lot rules.
- Validate ETF-specific product permissions, HKEX ETP/ETF classification, complex-product flags, KID/prospectus risk disclosures, market-maker/liquidity-provider support, trading currency, board lot, distribution/corporate-action handling, and fee/tax treatment per symbol; do not assume all HK ETFs share the same stamp-duty, levy, or broker minimum-commission behavior.
- Validate broker quote freshness, spread, expected slippage, and market-maker liquidity for every target order before allowing live submission.

## Non-snapshot market-history candidate

`hk_index_mean_reversion` uses direct `market_history` rather than snapshot artifacts. Platforms must supply overlapping daily close history for `02800` and `03033`; no snapshot CSV or manifest is required. See `docs/research/hk_index_mean_reversion.md` for the backtest and current non-promotion decision.

`hk_etf_regime_rotation` also uses direct `market_history`. Platforms must supply overlapping daily close history for `02800`, `02822`, `02840`, `03033`, `03110`, and `03188`; no snapshot CSV or manifest is required. See `docs/research/hk_etf_regime_rotation.md` for the backtest and current non-promotion decision.

`hk_high_dividend_low_vol_trend` uses direct `market_history` for `02840` and `03110`; no snapshot CSV or manifest is required. It is runtime-enabled with a 12% annual volatility target and can be selected by a platform Cloud Run deployment after platform feed, fee, spread, lot-size, and dry-run checks.

`hk_listed_global_etf_rotation` uses direct `market_history` for `02800`, `02822`, `03188`, `03033`, `02834`, `02840`, `03175`, and `03110`; no snapshot CSV or manifest is required. It is the first runtime-enabled HK non-snapshot profile and can be selected by a platform Cloud Run deployment, but dry-run removal requires per-symbol issuer documents, NAV/iNAV, underlying-index/reference-asset, tracking-difference, market-maker/liquidity-provider, multi-counter, fee/tax, broker-permission, A-share trading-hour/price-band, Nasdaq time-zone, gold-trust, and crude-oil futures-roll evidence.

## 2026-06-02 downside-risk / volatility future gate

Platform integration now mirrors `hk_downside_beta_tail_risk_volatility_overlay` as a non-selectable snapshot future-research candidate. Platform switch-plan tooling must treat it as pre-scaffold only: no runtime profile, no broker order surface, and no Google Cloud / Cloud Run mutation should be inferred from this candidate. If promoted later, it must pass the snapshot repository's new-contract requirement plus point-in-time downside beta / semivariance / VaR-CVaR / tail-risk / volatility-regime provenance, same-universe ablation, HK cost/capacity evidence, dry-run order previews, bilingual notification logs, rollout controls, and operator approval.

平台集成现在镜像 `hk_downside_beta_tail_risk_volatility_overlay` 作为 non-selectable snapshot future-research 候选。平台 switch-plan tooling 必须把它视为 pre-scaffold：没有 runtime profile、没有券商下单入口，也不能从该候选推断任何 Google Cloud / Cloud Run 变更。若后续提升，必须先通过 snapshot 仓库的新 contract 要求，并补齐 point-in-time downside beta / semivariance / VaR-CVaR / tail-risk / volatility-regime provenance、同 universe ablation、港股成本/容量证据、dry-run order previews、双语通知日志、rollout controls 和 operator approval。

## 2026-06-02 structured-product warrant / CBBC future gate

Platform integration now mirrors `hk_structured_product_warrant_cbbc_flow_risk_overlay` as a non-selectable snapshot future-research candidate. Switch-plan tooling must treat it as pre-scaffold only: no runtime profile, no warrant/CBBC broker order surface, and no Cloud Run mutation should be inferred. If promoted later, it must pass the snapshot repository's new-contract requirement plus point-in-time HKEX derivative-warrant / CBBC listing, issuance, expiry, underlying, turnover, MCE-distance, liquidity-provider quote availability, VCM/CAS, suspension, same-universe ablation, HK cost/capacity evidence, dry-run order previews, bilingual notification logs, rollout controls, and operator approval.

平台集成现在镜像 `hk_structured_product_warrant_cbbc_flow_risk_overlay` 作为 non-selectable snapshot future-research 候选。Switch-plan tooling 必须把它视为 pre-scaffold：没有 runtime profile、没有权证/牛熊证券商下单入口，也不能从该候选推断任何 Cloud Run 变更。若后续提升，必须先通过 snapshot 仓库的新 contract 要求，并补齐 point-in-time HKEX derivative-warrant / CBBC 上市、发行、到期、正股映射、成交、MCE-distance、liquidity-provider quote availability、VCM/CAS、停牌、同 universe ablation、港股成本/容量证据、dry-run order previews、双语通知日志、rollout controls 和 operator approval。

## 2026-06-02 index futures / options sentiment-basis future gate

Platform integration now mirrors `hk_index_derivatives_futures_options_sentiment_basis_overlay` as a non-selectable snapshot future-research candidate. Switch-plan tooling must treat it as pre-scaffold only: no runtime profile, no futures/options broker order surface, and no Cloud Run mutation should be inferred. If promoted later, it must pass the snapshot repository's new-contract requirement plus point-in-time HKEX futures/options price, volume, open interest, basis, put-call ratio, implied-volatility skew, term structure, expiry-roll, night-session, cash/futures close alignment, same-universe ablation, HK cost/capacity evidence, dry-run order previews, bilingual notification logs, rollout controls, and operator approval.

平台集成现在镜像 `hk_index_derivatives_futures_options_sentiment_basis_overlay` 作为 non-selectable snapshot future-research 候选。Switch-plan tooling 必须把它视为 pre-scaffold：没有 runtime profile、没有期货/期权券商下单入口，也不能从该候选推断任何 Cloud Run 变更。若后续提升，必须先通过 snapshot 仓库的新 contract 要求，并补齐 point-in-time HKEX futures/options price、volume、open interest、basis、put-call ratio、implied-volatility skew、term structure、expiry-roll、night-session、cash/futures close alignment、同 universe ablation、港股成本/容量证据、dry-run order previews、双语通知日志、rollout controls 和 operator approval。
