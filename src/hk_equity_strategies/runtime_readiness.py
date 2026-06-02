from __future__ import annotations

from typing import Any

from hk_equity_strategies.backtest_validation_policy import (
    MAX_SINGLE_PERIOD_RETURN_CONTRIBUTION,
    MIN_REQUIRED_OOS_FOLD_COUNT,
)
from hk_equity_strategies.evidence_freshness_policy import build_evidence_freshness_policy
from hk_equity_strategies.evidence_uri_policy import build_evidence_uri_policy
from hk_equity_strategies.execution_capacity_policy import build_execution_capacity_policy
from hk_equity_strategies.dry_run_order_preview_policy import build_dry_run_order_preview_policy
from hk_equity_strategies.notification_audit_policy import (
    RUNTIME_DRY_RUN_NOTIFICATION_EVENT_TYPE,
    build_notification_audit_policy,
)
from hk_equity_strategies.rollout_risk_policy import build_rollout_risk_policy
from hk_equity_strategies.runtime_equity_product_policy import build_runtime_equity_product_policy
from hk_equity_strategies.runtime_etf_product_policy import build_runtime_etf_product_policy
from hk_equity_strategies.runtime_market_data_policy import build_runtime_market_data_policy
from hk_equity_strategies.catalog import (
    HK_EQUITY_DOMAIN,
    HK_HIGH_DIVIDEND_LOW_VOL_TREND_PROFILE,
    HK_LISTED_GLOBAL_ETF_ROTATION_PROFILE,
    HK_LOW_VOL_DIVIDEND_QUALITY_PROFILE,
    get_runtime_enabled_profiles,
    get_strategy_definition,
    get_strategy_metadata,
    resolve_canonical_profile,
)
from hk_equity_strategies.runtime_adapters import (
    PLATFORM_NATIVE_TARGET_MODES,
    SUPPORTED_RUNTIME_PLATFORMS,
    describe_platform_runtime_requirements,
    get_platform_runtime_adapter,
)

HK_MARKET_DEFAULTS: dict[str, str] = {
    "market": "HK",
    "market_calendar": "XHKG",
    "market_timezone": "Asia/Hong_Kong",
    "market_exchange": "SEHK",
    "trading_currency": "HKD",
    "symbol_suffix": ".HK",
    "quantity_type": "integer_shares",
}

PLATFORM_HK_DRY_RUN_ENV: dict[str, dict[str, str]] = {
    "ibkr": {
        "IBKR_DRY_RUN_ONLY": "true",
        "IBKR_MARKET": "HK",
        "IBKR_MARKET_CALENDAR": "XHKG",
        "IBKR_MARKET_CURRENCY": "HKD",
        "IBKR_MARKET_DATA_SYMBOL_SUFFIX": ".HK",
        "IBKR_MARKET_EXCHANGE": "SEHK",
        "IBKR_MARKET_TIMEZONE": "Asia/Hong_Kong",
    },
    "longbridge": {
        "ACCOUNT_REGION": "HK",
        "ACCOUNT_PREFIX": "HK",
        "LONGBRIDGE_DRY_RUN_ONLY": "true",
        "LONGBRIDGE_MARKET": "HK",
        "LONGBRIDGE_MARKET_CALENDAR": "XHKG",
        "LONGBRIDGE_MARKET_TIMEZONE": "Asia/Hong_Kong",
        "LONGBRIDGE_SYMBOL_SUFFIX": ".HK",
        "LONGBRIDGE_TRADING_CURRENCY": "HKD",
    },
}

HK_DRY_RUN_CHECKS: tuple[str, ...] = (
    "Load HK market-history data for every managed symbol before evaluating the strategy.",
    "Confirm the broker account has HK/SEHK market data and trading permission.",
    "Preview generated orders only; do not submit live orders during dry-run validation.",
    "Verify all generated quantities are integer shares and then apply broker lot-size validation.",
    "Verify HKD cash/currency lines, fees, and reserved-cash behavior before any live rollout.",
    "Run on the XHKG calendar/timezone and check holiday or half-day behavior.",
)

HK_ETF_LIVE_ENABLEMENT_CHECKS: tuple[str, ...] = (
    "Confirm every managed symbol is an HKEX-listed ETP/ETF and capture the product audit record.",
    "Review leveraged, inverse, synthetic, futures-based, or otherwise complex ETF flags before operator approval.",
    "Capture current official product factsheet/KFS/prospectus links for every managed ETF before operator approval.",
    "Reconcile each ETF's underlying index or reference asset against the strategy thesis and market-history source.",
    "Reconcile ETF NAV/iNAV, tracking difference or tracking error, and quote source before using broker order preview.",
    "Review multi-counter currency, creation/redemption currency, and residual HKD cash handling for every product.",
    "Review underlying-market trading-hour gaps, ETF premium/discount behavior, cross-market holidays, FX, and settlement mismatches.",
    "For futures-based commodity ETFs, review futures roll, margin, curve/contango/backwardation, and operator suitability evidence.",
    "Confirm per-symbol HK stamp-duty, levy, trading-fee, and minimum-commission treatment from broker order preview.",
    "Review KID/prospectus risk disclosures, distribution treatment, board lot, trading currency, and corporate-action rules per symbol.",
    "Capture bid/ask spread, indicative fees, and expected slippage for every managed ETF before enabling real orders.",
    "Confirm ETF distribution and corporate-action handling because research backtests use total-return-adjusted history only when data provides it.",
    "Block order submission when quotes, NAV, lot size, market-maker liquidity, or trading status cannot be verified for the order date.",
)

HK_EQUITY_LIVE_ENABLEMENT_CHECKS: tuple[str, ...] = (
    "Confirm every managed symbol is an HKEX-listed single-name equity and capture the equity universe audit record.",
    "Confirm Stock Connect eligibility or a direct broker route for every managed symbol before operator approval.",
    "Capture current board lot, trading currency, suspension/trading-status, and corporate-action source evidence per symbol.",
    "Reconcile dividend yield and payout-ratio source lineage against point-in-time factor snapshot inputs.",
    "Verify sector caps, single-name caps, spread/depth, ADV capacity, and forced cash residual behavior before order preview.",
    "Confirm HK stamp duty, levies, broker commission, odd-lot handling, VCM, CAS, and market-session routing before dry-run removal.",
    "Block order submission when quote freshness, trading status, corporate-action treatment, board lot, or broker permission cannot be verified for the order date.",
)

ORDER_CONVERSION_CHECKS: tuple[str, ...] = (
    "Map HK numeric symbols to broker-native symbols using the .HK suffix or SEHK exchange mapping.",
    "Convert target weights with the latest portfolio equity or broker positions when the platform needs value targets.",
    "Round orders conservatively; never round fractional HK shares up without a lot-size check.",
    "Keep dry-run notifications and runtime reports enabled so operator review sees the exact order preview.",
)

LIVE_ENABLEMENT_REQUIREMENTS: tuple[str, ...] = (
    "Strategy metadata status must be runtime_enabled.",
    "Platform switch plan must keep dry_run_only=true until operator approval is recorded.",
    "Broker-side HK market-data, trading permission, and account-region settings must be verified.",
    "Order preview must show no fractional share, symbol suffix, currency, or lot-size mismatch.",
    "Dry-run order-preview notification must use the shared bilingual EN/ZH-Hans audit schema and stable delivery-log URI.",
    "Runtime target volatility, max exposure, and universe overrides must match the reviewed research profile unless explicitly re-approved.",
    "Production Cloud Run must not be changed by package merge alone; rollout requires an explicit deploy step.",
)

REQUIRED_LIVE_EVIDENCE_FIELDS: tuple[str, ...] = (
    "walk_forward_backtest_min_three_oos_years",
    "walk_forward_backtest_min_three_oos_folds",
    "walk_forward_backtest_single_period_return_contribution_below_60_percent",
    "walk_forward_backtest_positive_annual_return",
    "profile_benchmark_symbol_matched",
    "strategy_excess_return_vs_benchmark_positive",
    "runtime_market_data_audit_verified",
    "runtime_market_history_source_provenance_verified",
    "survivorship_and_lookahead_bias_controls_verified",
    "backtest_validation_policy_evidence",
    "point_in_time_no_lookahead_and_no_overfit_controls",
    "max_drawdown_within_profile_threshold",
    "annualized_turnover_within_profile_threshold",
    "runtime_etf_product_due_diligence_verified",
    "hk_fees_levies_and_stamp_duty_or_etf_exemption_verified",
    "bid_ask_spread_and_slippage_captured",
    "lot_size_and_integer_share_rounding_verified",
    "dry_run_order_preview_artifact_provenance_verified",
    "execution_capacity_and_liquidity_limits_verified",
    "fresh_section_evidence_generated_at",
    "staged_rollout_tripwires_and_rollback_ready",
    "broker_order_preview_notification_captured",
    "bilingual_notification_delivery_log_verified",
    "operator_approval_reference",
)


def get_required_live_evidence_fields(profile: str) -> tuple[str, ...]:
    fields = list(REQUIRED_LIVE_EVIDENCE_FIELDS)
    if profile == HK_LOW_VOL_DIVIDEND_QUALITY_PROFILE:
        fields = [
            "runtime_equity_product_due_diligence_verified"
            if field == "runtime_etf_product_due_diligence_verified"
            else field
            for field in fields
        ]
        fields = [
            "hk_fees_levies_and_stamp_duty_verified"
            if field == "hk_fees_levies_and_stamp_duty_or_etf_exemption_verified"
            else field
            for field in fields
        ]
    return tuple(dict.fromkeys(fields))

HK_DERIVATIVE_OR_COMPLEX_ETF_SYMBOLS = frozenset({"03175"})
HK_DEFENSIVE_ETF_SYMBOLS = frozenset({"02840", "03110"})
MIN_REQUIRED_WALK_FORWARD_YEARS = 3.0

PROFILE_LIVE_ENABLEMENT_THRESHOLDS: dict[str, dict[str, float]] = {
    HK_LISTED_GLOBAL_ETF_ROTATION_PROFILE: {
        "max_allowed_backtest_drawdown": 0.30,
        "min_required_return_to_drawdown_ratio": 0.50,
        "max_allowed_annualized_turnover": 1.50,
        "min_required_annual_return": 0.0,
        "min_required_walk_forward_years": MIN_REQUIRED_WALK_FORWARD_YEARS,
        "min_required_oos_fold_count": MIN_REQUIRED_OOS_FOLD_COUNT,
        "max_single_period_return_contribution": MAX_SINGLE_PERIOD_RETURN_CONTRIBUTION,
    },
    HK_HIGH_DIVIDEND_LOW_VOL_TREND_PROFILE: {
        "max_allowed_backtest_drawdown": 0.12,
        "min_required_return_to_drawdown_ratio": 0.50,
        "max_allowed_annualized_turnover": 1.00,
        "min_required_annual_return": 0.0,
        "min_required_walk_forward_years": MIN_REQUIRED_WALK_FORWARD_YEARS,
        "min_required_oos_fold_count": MIN_REQUIRED_OOS_FOLD_COUNT,
        "max_single_period_return_contribution": MAX_SINGLE_PERIOD_RETURN_CONTRIBUTION,
    },
    HK_LOW_VOL_DIVIDEND_QUALITY_PROFILE: {
        "max_allowed_backtest_drawdown": 0.30,
        "min_required_return_to_drawdown_ratio": 0.50,
        "max_allowed_annualized_turnover": 1.00,
        "min_required_annual_return": 0.0,
        "min_required_walk_forward_years": MIN_REQUIRED_WALK_FORWARD_YEARS,
        "min_required_oos_fold_count": MIN_REQUIRED_OOS_FOLD_COUNT,
        "max_single_period_return_contribution": MAX_SINGLE_PERIOD_RETURN_CONTRIBUTION,
    },
}

PROFILE_LIVE_OPTIMIZATION_CHECKS: dict[str, tuple[str, ...]] = {
    HK_LISTED_GLOBAL_ETF_ROTATION_PROFILE: (
        "Treat this as the higher-return but broader ETF-rotation candidate; start with reduced capital versus the two-ETF defensive profile.",
        "03175 is a crude-oil futures ETF; if platform product permission, liquidity, or spread checks fail, remove it via universe override and re-run backtests/readiness.",
        "Verify all eight ETF symbols are supported by the selected platform feed before relying on cross-sectional ranking.",
        "Capture issuer factsheet/KFS/prospectus, NAV/iNAV, underlying index/reference-asset, and market-maker/liquidity-provider evidence for every ETF in the broader universe.",
        "For 02800, audit TraHK prospectus/factsheet, HSI concentration, NAV/tracking-difference, dual-counter, and HKSAR-government non-guarantee disclosures.",
        "For 02822 and 03188, audit A-share underlying index, RQFII/Stock Connect access, RMB base currency, A-share trading-hour/price-band gaps, and premium/discount risk.",
        "For 03033, audit Hang Seng TECH concentration, platform-regulation drawdown risk, NAV/iNAV, and HK technology-sector liquidity.",
        "For 02834, audit Nasdaq trading-hour gap, US-market FX, premium/discount, capital-distribution risk, and multi-counter currency handling.",
        "For 03175, audit futures-based complex-product status, WTI futures roll schedule, margin, curve/contango/backwardation, non-correlation with spot oil, and operator suitability; remove it if any check fails.",
    ),
    HK_HIGH_DIVIDEND_LOW_VOL_TREND_PROFILE: (
        "Treat this as the preferred lower-drawdown first live HK profile because the managed universe is only 02840 and 03110.",
        "Keep the documented 12% annual volatility target until a new walk-forward backtest and paper-trading window are reviewed.",
        "Verify 02840 and 03110 dividend/distribution treatment, lot sizes, and bid/ask spreads before increasing exposure.",
        "For 03110, audit Hang Seng High Dividend Yield Index methodology, distribution policy, capital-distribution risk, and high-dividend concentration/yield-trap risk.",
        "For 02840, audit SPDR Gold Shares trust structure, physical-gold single-asset risk, NAV/iNAV, tracking difference, multi-counter currency, and USD creation/redemption handling.",
    ),
    HK_LOW_VOL_DIVIDEND_QUALITY_PROFILE: (
        "Treat this as the first snapshot-backed HK runtime profile; the strategy package consumes snapshots but does not generate them.",
        "Require a published hk_low_vol_dividend_quality factor snapshot and manifest that pass HkEquitySnapshotPipelines artifact-pack validation.",
        "Keep dry-run until point-in-time dividend, payout-ratio, volatility, beta, drawdown, trend, suspension, and corporate-action controls are evidenced.",
        "Verify sector caps, single-name caps, safe-haven residual weight, lot sizes, bid/ask spreads, ADV capacity, and Southbound eligibility before order submission.",
        "Re-run same-universe walk-forward evidence whenever factor-source lineage, eligible universe, or scoring weights change.",
    ),
}


def _normalize_platform(platform_id: str) -> str:
    normalized = str(platform_id).strip().lower()
    if normalized not in SUPPORTED_RUNTIME_PLATFORMS:
        raise ValueError(f"Unsupported HK runtime readiness platform {platform_id!r}")
    return normalized


def _extract_managed_symbols(profile: str, platform_id: str) -> tuple[str, ...]:
    definition = get_strategy_definition(profile)
    adapter = get_platform_runtime_adapter(profile, platform_id=platform_id)
    if adapter.managed_symbols_extractor is None:
        return ()
    try:
        return tuple(adapter.managed_symbols_extractor(**definition.default_config))
    except TypeError:
        return ()


def _build_risk_notes(profile: str, symbols: tuple[str, ...], *, runtime_enabled: bool) -> tuple[str, ...]:
    notes: list[str] = [
        "HK live trading remains blocked unless the platform dry-run plan is explicitly approved.",
        "This readiness plan is a configuration and validation checklist; it does not deploy Cloud Run.",
    ]
    if not runtime_enabled:
        notes.append("The profile is not runtime_enabled, so live order submission must remain disabled.")
    if HK_DERIVATIVE_OR_COMPLEX_ETF_SYMBOLS.intersection(symbols):
        notes.append("03175 is a crude-oil futures ETF; confirm suitability, spread, and product permission before live use.")
    if profile == HK_HIGH_DIVIDEND_LOW_VOL_TREND_PROFILE and HK_DEFENSIVE_ETF_SYMBOLS.issubset(symbols):
        notes.append("02840/03110 is the lower-drawdown live candidate, but it still requires ETF fee, spread, and distribution checks.")
    if profile == HK_LOW_VOL_DIVIDEND_QUALITY_PROFILE:
        notes.append(
            "This snapshot-backed profile requires a validated factor snapshot artifact and manifest at runtime."
        )
    return tuple(notes)


def build_hk_runtime_readiness(
    profile: str | None = HK_LISTED_GLOBAL_ETF_ROTATION_PROFILE,
    *,
    platform_id: str,
    dry_run_only: bool = True,
) -> dict[str, Any]:
    """Build a platform-neutral HK readiness plan for operator dry-run review."""

    normalized_platform = _normalize_platform(platform_id)
    canonical_profile = resolve_canonical_profile(profile)
    definition = get_strategy_definition(canonical_profile)
    if definition.domain != HK_EQUITY_DOMAIN:
        raise ValueError(f"Strategy profile {canonical_profile!r} is not an HK equity profile")
    if normalized_platform not in definition.supported_platforms:
        raise ValueError(
            f"Strategy profile {canonical_profile!r} does not declare support for {normalized_platform!r}"
        )

    metadata = get_strategy_metadata(canonical_profile)
    runtime_enabled = canonical_profile in get_runtime_enabled_profiles()
    runtime_requirements = describe_platform_runtime_requirements(
        canonical_profile,
        platform_id=normalized_platform,
    )
    adapter = get_platform_runtime_adapter(canonical_profile, platform_id=normalized_platform)
    platform_native_target_mode = PLATFORM_NATIVE_TARGET_MODES[normalized_platform]
    requires_portfolio_snapshot = "portfolio_snapshot" in adapter.available_inputs
    managed_symbols = _extract_managed_symbols(canonical_profile, normalized_platform)
    dry_run_env = dict(PLATFORM_HK_DRY_RUN_ENV[normalized_platform])
    dry_run_env[next(key for key in dry_run_env if key.endswith("DRY_RUN_ONLY"))] = "true" if dry_run_only else "false"
    if runtime_requirements["requires_snapshot_artifacts"]:
        prefix = "IBKR" if normalized_platform == "ibkr" else "LONGBRIDGE"
        dry_run_env[f"{prefix}_FEATURE_SNAPSHOT_PATH"] = "<required>"
        dry_run_env[f"{prefix}_FEATURE_SNAPSHOT_MANIFEST_PATH"] = "<required>"
    is_single_name_snapshot_profile = canonical_profile == HK_LOW_VOL_DIVIDEND_QUALITY_PROFILE
    equity_live_enablement_checks = (
        HK_EQUITY_LIVE_ENABLEMENT_CHECKS if is_single_name_snapshot_profile else ()
    )
    etf_live_enablement_checks = (
        () if is_single_name_snapshot_profile else HK_ETF_LIVE_ENABLEMENT_CHECKS
    )

    return {
        "platform": normalized_platform,
        "canonical_profile": canonical_profile,
        "display_name": metadata.display_name,
        "status": metadata.status,
        "runtime_enabled": runtime_enabled,
        "dry_run_only": bool(dry_run_only),
        "market_defaults": dict(HK_MARKET_DEFAULTS),
        "required_inputs": sorted(definition.required_inputs),
        "available_inputs": sorted(adapter.available_inputs),
        "managed_symbols": list(managed_symbols),
        "managed_symbols_source": "default_config" if managed_symbols else "runtime_input_required",
        "target_conversion": {
            "strategy_target_mode": definition.target_mode,
            "platform_native_target_mode": platform_native_target_mode,
            "requires_portfolio_snapshot": requires_portfolio_snapshot,
            "portfolio_input_name": adapter.portfolio_input_name,
        },
        "platform_dry_run_env": dry_run_env,
        "runtime_requirements": runtime_requirements,
        "dry_run_checks": list(HK_DRY_RUN_CHECKS),
        "etf_live_enablement_checks": list(etf_live_enablement_checks),
        "equity_live_enablement_checks": list(equity_live_enablement_checks),
        "product_live_enablement_checks": list(equity_live_enablement_checks or etf_live_enablement_checks),
        "order_conversion_checks": list(ORDER_CONVERSION_CHECKS),
        "live_enablement_requirements": list(LIVE_ENABLEMENT_REQUIREMENTS),
        "live_enablement_thresholds": dict(PROFILE_LIVE_ENABLEMENT_THRESHOLDS[canonical_profile]),
        "required_live_evidence_fields": list(get_required_live_evidence_fields(canonical_profile)),
        "evidence_uri_policy": build_evidence_uri_policy(),
        "evidence_freshness_policy": build_evidence_freshness_policy(),
        "execution_capacity_policy": build_execution_capacity_policy(canonical_profile),
        "dry_run_order_preview_policy": build_dry_run_order_preview_policy(),
        "rollout_risk_policy": build_rollout_risk_policy(),
        "runtime_equity_product_policy": build_runtime_equity_product_policy(),
        "runtime_etf_product_policy": build_runtime_etf_product_policy(),
        "runtime_market_data_policy": build_runtime_market_data_policy(),
        "notification_audit_policy": build_notification_audit_policy(RUNTIME_DRY_RUN_NOTIFICATION_EVENT_TYPE),
        "profile_live_optimization_checks": list(PROFILE_LIVE_OPTIMIZATION_CHECKS.get(canonical_profile, ())),
        "risk_notes": list(_build_risk_notes(canonical_profile, managed_symbols, runtime_enabled=runtime_enabled)),
    }


__all__ = [
    "HK_DRY_RUN_CHECKS",
    "HK_EQUITY_LIVE_ENABLEMENT_CHECKS",
    "HK_ETF_LIVE_ENABLEMENT_CHECKS",
    "HK_MARKET_DEFAULTS",
    "LIVE_ENABLEMENT_REQUIREMENTS",
    "ORDER_CONVERSION_CHECKS",
    "PLATFORM_HK_DRY_RUN_ENV",
    "PROFILE_LIVE_ENABLEMENT_THRESHOLDS",
    "REQUIRED_LIVE_EVIDENCE_FIELDS",
    "build_hk_runtime_readiness",
    "get_required_live_evidence_fields",
]
