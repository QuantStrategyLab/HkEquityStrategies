from __future__ import annotations

import argparse
import json
from collections.abc import Mapping
from datetime import datetime
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from hk_equity_strategies.backtest_validation_policy import (
    MAX_ALLOWED_HK_STRATEGY_DRAWDOWN,
    REQUIRED_BACKTEST_VALIDATION_BOOLEAN_FIELDS,
    build_backtest_validation_policy,
)
from hk_equity_strategies.evidence_freshness_policy import (
    EVIDENCE_GENERATED_AT_FIELD,
    MAX_ALLOWED_EVIDENCE_AGE_DAYS_BY_SECTION,
    build_evidence_freshness_policy,
)
from hk_equity_strategies.evidence_uri_policy import (
    ALLOWED_EVIDENCE_URI_SCHEMES,
    SENSITIVE_EVIDENCE_URI_MARKERS,
    build_evidence_uri_policy,
)
from hk_equity_strategies.execution_capacity_policy import (
    REQUIRED_EXECUTION_CAPACITY_FIELDS,
    build_execution_capacity_policy,
    get_min_median_daily_turnover_hkd,
)
from hk_equity_strategies.dry_run_order_preview_policy import (
    REQUIRED_DRY_RUN_ORDER_PREVIEW_BOOLEAN_FIELDS,
    REQUIRED_DRY_RUN_ORDER_PREVIEW_FIELDS,
    REQUIRED_DRY_RUN_ORDER_PREVIEW_SHA256_FIELDS,
    REQUIRED_DRY_RUN_ORDER_PREVIEW_URI_FIELDS,
    build_dry_run_order_preview_policy,
)
from hk_equity_strategies.notification_audit_policy import (
    NOTIFICATION_SCHEMA_VERSION,
    REQUIRED_NOTIFICATION_AUDIT_BOOLEAN_FIELDS,
    REQUIRED_NOTIFICATION_AUDIT_FIELDS,
    RUNTIME_DRY_RUN_NOTIFICATION_EVENT_TYPE,
    build_notification_audit_policy,
)
from hk_equity_strategies.catalog import (
    get_runtime_enabled_profiles,
    get_strategy_metadata,
    resolve_canonical_profile,
)
from hk_equity_strategies.runtime_adapters import SUPPORTED_RUNTIME_PLATFORMS
from hk_equity_strategies.runtime_readiness import (
    PROFILE_LIVE_ENABLEMENT_THRESHOLDS,
    REQUIRED_LIVE_EVIDENCE_FIELDS,
    build_hk_runtime_readiness,
)
from hk_equity_strategies.runtime_etf_product_policy import (
    REQUIRED_RUNTIME_ETF_PRODUCT_BOOLEAN_FIELDS,
    REQUIRED_RUNTIME_ETF_PRODUCT_FIELDS,
    REQUIRED_RUNTIME_ETF_PRODUCT_URI_FIELDS,
    build_runtime_etf_product_policy,
)
from hk_equity_strategies.runtime_market_data_policy import (
    REQUIRED_RUNTIME_MARKET_DATA_AUDIT_FIELDS,
    REQUIRED_RUNTIME_MARKET_DATA_PROVENANCE_FIELDS,
    REQUIRED_RUNTIME_MARKET_DATA_URI_FIELDS,
    build_runtime_market_data_policy,
)
from hk_equity_strategies.rollout_risk_policy import REQUIRED_ROLLOUT_RISK_FIELDS, build_rollout_risk_policy

EVIDENCE_TYPE = "hk_runtime_live_enablement"
REQUIRED_SECTIONS: tuple[str, ...] = (
    "strategy_backtest",
    "runtime_readiness",
    "platform_dry_run_order_preview",
    "broker_permission_and_fee_verification",
    "runtime_switch_plan",
    "risk_approval",
)


def _as_mapping(value: Any) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _number(value: Any) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _drawdown_abs(value: Any) -> float | None:
    number = _number(value)
    if number is None:
        return None
    return abs(number)


def _parse_iso_date(value: Any) -> datetime | None:
    try:
        return datetime.fromisoformat(str(value).strip()[:10])
    except (TypeError, ValueError):
        return None


def _resolve_validation_as_of(evidence: Mapping[str, Any], validation_as_of: str | None) -> tuple[datetime, list[str]]:
    raw_value = validation_as_of if validation_as_of is not None else evidence.get("validation_as_of")
    if raw_value is None or not str(raw_value).strip():
        return datetime.now(), []
    parsed_value = _parse_iso_date(raw_value)
    if parsed_value is None:
        return datetime.now(), ["validation_as_of must be an ISO date"]
    return parsed_value, []


def _is_passed(section: Mapping[str, Any]) -> bool:
    return str(section.get("status", "")).strip().lower() == "passed"


def _bool_is_true(section: Mapping[str, Any], field: str) -> bool:
    return section.get(field) is True


def _add_missing_bool_errors(errors: list[str], section_name: str, section: Mapping[str, Any], fields: tuple[str, ...]) -> None:
    for field in fields:
        if not _bool_is_true(section, field):
            errors.append(f"{section_name}.{field} must be true")


def _require_evidence_uri(errors: list[str], section_name: str, section: Mapping[str, Any]) -> None:
    raw_uri = str(section.get("evidence_uri", "")).strip()
    if not raw_uri:
        errors.append(f"{section_name}.evidence_uri is required")
        return
    parsed_uri = urlparse(raw_uri)
    if parsed_uri.scheme.lower() not in ALLOWED_EVIDENCE_URI_SCHEMES or not parsed_uri.netloc or not parsed_uri.path:
        allowed = ", ".join(f"{scheme}://" for scheme in ALLOWED_EVIDENCE_URI_SCHEMES)
        errors.append(f"{section_name}.evidence_uri must be a stable URI using one of: {allowed}")
    lowered_uri = raw_uri.lower()
    if any(marker in lowered_uri for marker in SENSITIVE_EVIDENCE_URI_MARKERS):
        errors.append(f"{section_name}.evidence_uri must not contain secret-like query parameters")


def _require_stable_uri_field(errors: list[str], section_name: str, section: Mapping[str, Any], field: str) -> None:
    raw_uri = str(section.get(field, "")).strip()
    if not raw_uri:
        errors.append(f"{section_name}.{field} is required")
        return
    parsed_uri = urlparse(raw_uri)
    if parsed_uri.scheme.lower() not in ALLOWED_EVIDENCE_URI_SCHEMES or not parsed_uri.netloc or not parsed_uri.path:
        allowed = ", ".join(f"{scheme}://" for scheme in ALLOWED_EVIDENCE_URI_SCHEMES)
        errors.append(f"{section_name}.{field} must be a stable URI using one of: {allowed}")
    lowered_uri = raw_uri.lower()
    if any(marker in lowered_uri for marker in SENSITIVE_EVIDENCE_URI_MARKERS):
        errors.append(f"{section_name}.{field} must not contain secret-like query parameters")


def _sha256_is_hex(value: Any) -> bool:
    text = str(value or "").strip()
    if len(text) != 64:
        return False
    return all(char in "0123456789abcdefABCDEF" for char in text)


def _validate_dry_run_order_preview_provenance(
    errors: list[str],
    section_name: str,
    section: Mapping[str, Any],
) -> None:
    for field in REQUIRED_DRY_RUN_ORDER_PREVIEW_FIELDS:
        if not str(section.get(field, "")).strip():
            errors.append(f"{section_name}.{field} is required")
    for field in REQUIRED_DRY_RUN_ORDER_PREVIEW_URI_FIELDS:
        _require_stable_uri_field(errors, section_name, section, field)
    for field in REQUIRED_DRY_RUN_ORDER_PREVIEW_SHA256_FIELDS:
        if not _sha256_is_hex(section.get(field)):
            errors.append(f"{section_name}.{field} must be a 64-character hex sha256")
    _add_missing_bool_errors(errors, section_name, section, REQUIRED_DRY_RUN_ORDER_PREVIEW_BOOLEAN_FIELDS)


def _validate_runtime_etf_product_due_diligence(
    errors: list[str],
    section_name: str,
    section: Mapping[str, Any],
    *,
    expected_symbol_count: int,
) -> None:
    for field in REQUIRED_RUNTIME_ETF_PRODUCT_FIELDS:
        if not str(section.get(field, "")).strip():
            errors.append(f"{section_name}.{field} is required")
    audited_count = _number(section.get("managed_etf_symbols_audited_count"))
    if audited_count is None or audited_count < expected_symbol_count:
        errors.append(f"{section_name}.managed_etf_symbols_audited_count must be >= {expected_symbol_count}")
    for field in REQUIRED_RUNTIME_ETF_PRODUCT_URI_FIELDS:
        _require_stable_uri_field(errors, section_name, section, field)
    _add_missing_bool_errors(errors, section_name, section, REQUIRED_RUNTIME_ETF_PRODUCT_BOOLEAN_FIELDS)


def _validate_notification_audit(
    errors: list[str],
    section_name: str,
    section: Mapping[str, Any],
    *,
    expected_event_type: str,
) -> None:
    for field in REQUIRED_NOTIFICATION_AUDIT_FIELDS:
        if not str(section.get(field, "")).strip():
            errors.append(f"{section_name}.{field} is required")
    if section.get("notification_schema_version") != NOTIFICATION_SCHEMA_VERSION:
        errors.append(
            f"{section_name}.notification_schema_version must be {NOTIFICATION_SCHEMA_VERSION!r}: "
            f"got {section.get('notification_schema_version')!r}"
        )
    if section.get("notification_event_type") != expected_event_type:
        errors.append(
            f"{section_name}.notification_event_type must be {expected_event_type!r}: "
            f"got {section.get('notification_event_type')!r}"
        )
    _add_missing_bool_errors(errors, section_name, section, REQUIRED_NOTIFICATION_AUDIT_BOOLEAN_FIELDS)
    _require_stable_uri_field(errors, section_name, section, "notification_delivery_log_uri")


def _require_evidence_freshness(
    errors: list[str],
    section_name: str,
    section: Mapping[str, Any],
    *,
    validation_as_of: datetime,
) -> None:
    max_allowed_age_days = MAX_ALLOWED_EVIDENCE_AGE_DAYS_BY_SECTION[section_name]
    raw_generated_at = section.get(EVIDENCE_GENERATED_AT_FIELD)
    if raw_generated_at is None or not str(raw_generated_at).strip():
        errors.append(f"{section_name}.{EVIDENCE_GENERATED_AT_FIELD} is required")
        return
    generated_at = _parse_iso_date(raw_generated_at)
    if generated_at is None:
        errors.append(f"{section_name}.{EVIDENCE_GENERATED_AT_FIELD} must be an ISO date")
        return
    generated_date = generated_at.date()
    validation_date = validation_as_of.date()
    if generated_date > validation_date:
        errors.append(
            f"{section_name}.{EVIDENCE_GENERATED_AT_FIELD} must not be after validation_as_of: "
            f"got {generated_date.isoformat()}, validation_as_of={validation_date.isoformat()}"
        )
        return
    age_days = (validation_date - generated_date).days
    if age_days > max_allowed_age_days:
        errors.append(
            f"{section_name}.{EVIDENCE_GENERATED_AT_FIELD} is stale: "
            f"age_days={age_days}, max_allowed_age_days={max_allowed_age_days}"
        )


def _validate_strategy_backtest(
    errors: list[str],
    evidence: Mapping[str, Any],
    *,
    profile: str,
    thresholds: Mapping[str, float],
) -> None:
    section_name = "strategy_backtest"
    section = _as_mapping(evidence.get(section_name))
    _require_evidence_uri(errors, section_name, section)
    if not _is_passed(section):
        errors.append(f"{section_name}.status must be 'passed'")
    if section.get("out_of_sample") is not True:
        errors.append(f"{section_name}.out_of_sample must be true")
    for field in ("period_start", "period_end"):
        if not str(section.get(field, "")).strip():
            errors.append(f"{section_name}.{field} is required")
    period_start = _parse_iso_date(section.get("period_start"))
    period_end = _parse_iso_date(section.get("period_end"))
    if period_start is not None and period_end is not None:
        walk_forward_years = (period_end - period_start).days / 365.25
        min_years = float(thresholds["min_required_walk_forward_years"])
        if walk_forward_years < min_years:
            errors.append(f"{section_name}.period must cover at least {min_years:.1f} years: got {walk_forward_years:.2f}")

    min_return = float(thresholds["min_required_annual_return"])
    annual_return = _number(section.get("annual_return"))
    if annual_return is None:
        errors.append(f"{section_name}.annual_return is required")
    elif annual_return <= min_return:
        errors.append(f"{section_name}.annual_return must be greater than {min_return:.2%}")

    max_drawdown_limit = min(float(thresholds["max_allowed_backtest_drawdown"]), MAX_ALLOWED_HK_STRATEGY_DRAWDOWN)
    max_drawdown = _drawdown_abs(section.get("max_drawdown"))
    if max_drawdown is None:
        errors.append(f"{section_name}.max_drawdown is required")
    elif max_drawdown > max_drawdown_limit:
        errors.append(f"{section_name}.max_drawdown exceeds {max_drawdown_limit:.0%}: got {max_drawdown:.2%}")

    max_turnover = float(thresholds["max_allowed_annualized_turnover"])
    annualized_turnover = _number(section.get("annualized_turnover"))
    if annualized_turnover is None:
        errors.append(f"{section_name}.annualized_turnover is required")
    elif annualized_turnover > max_turnover:
        errors.append(f"{section_name}.annualized_turnover exceeds {max_turnover:.0%}: got {annualized_turnover:.2%}")
    _add_missing_bool_errors(
        errors,
        section_name,
        section,
        REQUIRED_BACKTEST_VALIDATION_BOOLEAN_FIELDS,
    )
    benchmark_symbol = str(section.get("benchmark_symbol", "")).strip()
    required_benchmark_symbol = str(get_strategy_metadata(profile).benchmark or "").strip()
    if not benchmark_symbol:
        errors.append(f"{section_name}.benchmark_symbol is required")
    elif benchmark_symbol != required_benchmark_symbol:
        errors.append(
            f"{section_name}.benchmark_symbol must be {required_benchmark_symbol!r}: got {benchmark_symbol!r}"
        )
    if _number(section.get("benchmark_annual_return")) is None:
        errors.append(f"{section_name}.benchmark_annual_return is required")
    strategy_excess_return = _number(section.get("strategy_excess_return"))
    if strategy_excess_return is None:
        errors.append(f"{section_name}.strategy_excess_return is required")
    elif strategy_excess_return <= 0:
        errors.append(f"{section_name}.strategy_excess_return must be positive")


def _validate_runtime_readiness(
    errors: list[str],
    evidence: Mapping[str, Any],
    *,
    profile: str,
    platform: str,
) -> None:
    section_name = "runtime_readiness"
    section = _as_mapping(evidence.get(section_name))
    _require_evidence_uri(errors, section_name, section)
    if not _is_passed(section):
        errors.append(f"{section_name}.status must be 'passed'")
    if section.get("profile") != profile:
        errors.append(f"{section_name}.profile mismatch: expected {profile!r}, got {section.get('profile')!r}")
    if section.get("platform") != platform:
        errors.append(f"{section_name}.platform mismatch: expected {platform!r}, got {section.get('platform')!r}")
    _add_missing_bool_errors(
        errors,
        section_name,
        section,
        (
            "market_history_feed_verified",
            "managed_symbols_verified",
            "target_conversion_verified",
            "dry_run_only_before_approval",
        ),
    )
    for field in REQUIRED_RUNTIME_MARKET_DATA_PROVENANCE_FIELDS:
        if not str(section.get(field, "")).strip():
            errors.append(f"{section_name}.{field} is required")
    coverage_start = _parse_iso_date(section.get("market_history_coverage_start"))
    coverage_end = _parse_iso_date(section.get("market_history_coverage_end"))
    if section.get("market_history_coverage_start") and coverage_start is None:
        errors.append(f"{section_name}.market_history_coverage_start must be an ISO date")
    if section.get("market_history_coverage_end") and coverage_end is None:
        errors.append(f"{section_name}.market_history_coverage_end must be an ISO date")
    if coverage_start is not None and coverage_end is not None and coverage_end < coverage_start:
        errors.append(f"{section_name}.market_history_coverage_end must not be before market_history_coverage_start")
    for field in REQUIRED_RUNTIME_MARKET_DATA_URI_FIELDS:
        _require_stable_uri_field(errors, section_name, section, field)
    _add_missing_bool_errors(errors, section_name, section, REQUIRED_RUNTIME_MARKET_DATA_AUDIT_FIELDS)


def _validate_dry_run(errors: list[str], evidence: Mapping[str, Any], *, profile: str) -> None:
    section_name = "platform_dry_run_order_preview"
    section = _as_mapping(evidence.get(section_name))
    _require_evidence_uri(errors, section_name, section)
    if not _is_passed(section):
        errors.append(f"{section_name}.status must be 'passed'")
    orders_previewed = _number(section.get("orders_previewed"))
    if orders_previewed is None or orders_previewed <= 0:
        errors.append(f"{section_name}.orders_previewed must be positive")
    for field in ("fractional_share_errors", "lot_size_errors", "currency_errors", "symbol_mapping_errors"):
        value = _number(section.get(field))
        if value is None or value != 0:
            errors.append(f"{section_name}.{field} must be 0")
    _add_missing_bool_errors(
        errors,
        section_name,
        section,
        (
            "bid_ask_spread_captured",
            "slippage_estimate_captured",
            "notification_sent",
            "order_submission_blocked_during_dry_run",
        ),
    )
    execution_capacity_policy = build_execution_capacity_policy(profile)
    adv_window_trading_days = _number(section.get("adv_window_trading_days"))
    min_adv_window_trading_days = int(execution_capacity_policy["min_adv_window_trading_days"])
    if adv_window_trading_days is None or adv_window_trading_days < min_adv_window_trading_days:
        errors.append(f"{section_name}.adv_window_trading_days must be >= {min_adv_window_trading_days}")
    median_daily_turnover_hkd = _number(section.get("median_daily_turnover_hkd"))
    min_median_daily_turnover_hkd = get_min_median_daily_turnover_hkd(profile)
    if median_daily_turnover_hkd is None or median_daily_turnover_hkd < min_median_daily_turnover_hkd:
        errors.append(f"{section_name}.median_daily_turnover_hkd must be >= {min_median_daily_turnover_hkd}")
    for field, threshold_key in (
        ("max_single_order_adv_fraction", "max_single_order_adv_fraction"),
        ("rebalance_adv_fraction", "max_rebalance_adv_fraction"),
    ):
        value = _number(section.get(field))
        threshold = float(execution_capacity_policy[threshold_key])
        if value is None:
            errors.append(f"{section_name}.{field} is required")
        elif value > threshold:
            errors.append(f"{section_name}.{field} exceeds {threshold:.2%}: got {value:.2%}")
    _add_missing_bool_errors(errors, section_name, section, REQUIRED_EXECUTION_CAPACITY_FIELDS)
    _validate_dry_run_order_preview_provenance(errors, section_name, section)
    _validate_notification_audit(
        errors,
        section_name,
        section,
        expected_event_type=RUNTIME_DRY_RUN_NOTIFICATION_EVENT_TYPE,
    )


def _validate_broker_permissions(
    errors: list[str],
    evidence: Mapping[str, Any],
    *,
    profile: str,
    platform: str,
) -> None:
    section_name = "broker_permission_and_fee_verification"
    section = _as_mapping(evidence.get(section_name))
    _require_evidence_uri(errors, section_name, section)
    if not _is_passed(section):
        errors.append(f"{section_name}.status must be 'passed'")
    _add_missing_bool_errors(
        errors,
        section_name,
        section,
        (
            "hk_market_data",
            "sehk_trading_permission",
            "hkd_cash_handling",
            "fees_levies_verified",
            "stamp_duty_or_etf_exemption_verified",
            "etf_product_permission_verified",
        ),
    )
    try:
        readiness = build_hk_runtime_readiness(profile, platform_id=platform)
    except ValueError as exc:
        errors.append(str(exc))
        return
    _validate_runtime_etf_product_due_diligence(
        errors,
        section_name,
        section,
        expected_symbol_count=len(readiness["managed_symbols"]),
    )


def _validate_switch_plan(errors: list[str], evidence: Mapping[str, Any]) -> None:
    section_name = "runtime_switch_plan"
    section = _as_mapping(evidence.get(section_name))
    rollout_policy = build_rollout_risk_policy()
    _require_evidence_uri(errors, section_name, section)
    if not _is_passed(section):
        errors.append(f"{section_name}.status must be 'passed'")
    _add_missing_bool_errors(
        errors,
        section_name,
        section,
        (
            "explicit_deploy_step_required",
            "rollback_plan_ready",
            "dry_run_first",
            "production_cloud_run_not_changed_by_package_merge",
        ),
    )
    _add_missing_bool_errors(errors, section_name, section, REQUIRED_ROLLOUT_RISK_FIELDS)
    for field, threshold_key in (
        ("initial_capital_fraction", "max_initial_capital_fraction"),
        ("per_symbol_capital_fraction", "max_per_symbol_capital_fraction"),
        ("intraday_drawdown_tripwire", "max_intraday_drawdown_tripwire"),
        ("cumulative_drawdown_tripwire", "max_cumulative_drawdown_tripwire"),
    ):
        value = _number(section.get(field))
        threshold = float(rollout_policy[threshold_key])
        if value is None:
            errors.append(f"{section_name}.{field} is required")
        elif value > threshold:
            errors.append(f"{section_name}.{field} exceeds {threshold:.2%}: got {value:.2%}")
    observation_days = _number(section.get("observation_trading_days_before_scale_up"))
    min_observation_days = int(rollout_policy["min_observation_trading_days_before_scale_up"])
    if observation_days is None or observation_days < min_observation_days:
        errors.append(f"{section_name}.observation_trading_days_before_scale_up must be >= {min_observation_days}")


def _validate_risk_approval(errors: list[str], evidence: Mapping[str, Any]) -> None:
    section_name = "risk_approval"
    section = _as_mapping(evidence.get(section_name))
    _add_missing_bool_errors(
        errors,
        section_name,
        section,
        ("operator_approved", "live_rollout_approved", "dry_run_removal_approved"),
    )
    if not str(section.get("approval_reference", "")).strip():
        errors.append(f"{section_name}.approval_reference is required")


def build_runtime_live_enablement_evidence_template(profile: str, *, platform: str) -> dict[str, Any]:
    canonical_profile = resolve_canonical_profile(profile)
    normalized_platform = str(platform or "").strip().lower()
    if normalized_platform not in SUPPORTED_RUNTIME_PLATFORMS:
        raise ValueError(f"platform must be one of {sorted(SUPPORTED_RUNTIME_PLATFORMS)}")
    readiness = build_hk_runtime_readiness(canonical_profile, platform_id=normalized_platform)
    benchmark_symbol = str(get_strategy_metadata(canonical_profile).benchmark or "").strip()
    return {
        "evidence_type": EVIDENCE_TYPE,
        "template_status": "pending_operator_evidence",
        "profile": canonical_profile,
        "display_name": get_strategy_metadata(canonical_profile).display_name,
        "platform": normalized_platform,
        "live_enablement_thresholds": dict(PROFILE_LIVE_ENABLEMENT_THRESHOLDS[canonical_profile]),
        "evidence_uri_policy": build_evidence_uri_policy(),
        "evidence_freshness_policy": build_evidence_freshness_policy(),
        "execution_capacity_policy": build_execution_capacity_policy(canonical_profile),
        "dry_run_order_preview_policy": build_dry_run_order_preview_policy(),
        "rollout_risk_policy": build_rollout_risk_policy(),
        "runtime_etf_product_policy": build_runtime_etf_product_policy(),
        "runtime_market_data_policy": build_runtime_market_data_policy(),
        "backtest_validation_policy": build_backtest_validation_policy(),
        "notification_audit_policy": build_notification_audit_policy(RUNTIME_DRY_RUN_NOTIFICATION_EVENT_TYPE),
        "validation_as_of": "<YYYY-MM-DD>",
        "required_live_evidence_fields": list(REQUIRED_LIVE_EVIDENCE_FIELDS),
        "strategy_backtest": {
            "status": "pending",
            "out_of_sample": False,
            "period_start": "",
            "period_end": "",
            "annual_return": None,
            "max_drawdown": None,
            "annualized_turnover": None,
            "survivorship_bias_controls": False,
            "lookahead_bias_controls": False,
            "benchmark_period_aligned": False,
            "point_in_time_inputs_only": False,
            "signal_timestamp_before_trade_timestamp": False,
            "reporting_date_asof_lag_enforced": False,
            "no_future_constituent_universe": False,
            "train_validation_test_or_walk_forward_split_documented": False,
            "parameter_grid_pre_registered_and_small": False,
            "no_full_sample_parameter_selection": False,
            "multiple_period_robustness_checked": False,
            "transaction_cost_slippage_lot_size_and_suspension_model_included": False,
            "benchmark_symbol": benchmark_symbol,
            "benchmark_annual_return": None,
            "strategy_excess_return": None,
            EVIDENCE_GENERATED_AT_FIELD: "",
            "evidence_uri": "",
        },
        "runtime_readiness": {
            "status": "pending",
            "profile": canonical_profile,
            "platform": normalized_platform,
            "readiness_command": (
                f"python scripts/print_hk_runtime_readiness.py --profile {canonical_profile} "
                f"--platform {normalized_platform} --json"
            ),
            "managed_symbols": readiness["managed_symbols"],
            "market_history_feed_verified": False,
            "managed_symbols_verified": False,
            "target_conversion_verified": False,
            "dry_run_only_before_approval": False,
            "market_history_source_name": "",
            "market_history_coverage_start": "",
            "market_history_coverage_end": "",
            "market_history_source_uri": "",
            "market_history_quality_report_uri": "",
            "point_in_time_data_dictionary_uri": "",
            **{field: False for field in REQUIRED_RUNTIME_MARKET_DATA_AUDIT_FIELDS},
            EVIDENCE_GENERATED_AT_FIELD: "",
            "evidence_uri": "",
        },
        "platform_dry_run_order_preview": {
            "status": "pending",
            "orders_previewed": 0,
            "fractional_share_errors": None,
            "lot_size_errors": None,
            "currency_errors": None,
            "symbol_mapping_errors": None,
            "bid_ask_spread_captured": False,
            "slippage_estimate_captured": False,
            "notification_sent": False,
            "notification_schema_version": NOTIFICATION_SCHEMA_VERSION,
            "notification_event_type": RUNTIME_DRY_RUN_NOTIFICATION_EVENT_TYPE,
            "notification_correlation_id": "",
            "notification_locale_en": False,
            "notification_locale_zh_hans": False,
            "notification_contains_profile": False,
            "notification_contains_platform": False,
            "notification_contains_validation_status": False,
            "notification_contains_order_preview_summary": False,
            "notification_redacts_sensitive_fields": False,
            "notification_delivery_log_uri": "",
            "dry_run_session_id": "",
            "raw_order_preview_uri": "",
            "raw_order_preview_sha256": "",
            "quote_snapshot_uri": "",
            "quote_snapshot_sha256": "",
            "fee_breakdown_uri": "",
            "fee_breakdown_sha256": "",
            "order_preview_artifact_not_sample": False,
            "order_preview_redacts_sensitive_fields": False,
            "quote_snapshot_covers_all_symbols": False,
            "fee_breakdown_reconciled_to_broker_preview": False,
            "order_preview_reconciled_to_strategy_decision": False,
            "order_submission_blocked_during_dry_run": False,
            "adv_window_trading_days": 0,
            "median_daily_turnover_hkd": None,
            "max_single_order_adv_fraction": None,
            "rebalance_adv_fraction": None,
            "liquidity_cap_verified": False,
            "board_lot_rounding_verified": False,
            "odd_lot_avoidance_verified": False,
            "market_session_routing_verified": False,
            "vcm_price_band_controls_verified": False,
            "etf_nav_or_spread_guard_verified": False,
            EVIDENCE_GENERATED_AT_FIELD: "",
            "evidence_uri": "",
        },
        "broker_permission_and_fee_verification": {
            "status": "pending",
            "hk_market_data": False,
            "sehk_trading_permission": False,
            "hkd_cash_handling": False,
            "fees_levies_verified": False,
            "stamp_duty_or_etf_exemption_verified": False,
            "etf_product_permission_verified": False,
            "etf_product_audit_id": "",
            "managed_etf_symbols_audited_count": 0,
            "etf_product_universe_audit_uri": "",
            "official_product_document_uri": "",
            "underlying_index_or_reference_asset_source_uri": "",
            "nav_or_inav_source_uri": "",
            "market_maker_or_liquidity_provider_source_uri": "",
            "stock_connect_etf_eligibility_source_uri": "",
            "southbound_etf_turnover_and_fund_flow_source_uri": "",
            "distribution_tax_and_fee_treatment_source_uri": "",
            "etf_fee_and_stamp_duty_audit_uri": "",
            "broker_product_permission_audit_uri": "",
            "all_managed_symbols_confirmed_etp": False,
            "leveraged_inverse_or_synthetic_flags_audited": False,
            "complex_or_futures_based_products_operator_reviewed": False,
            "etf_stamp_duty_exemption_or_tax_treatment_verified": False,
            "market_maker_or_liquidity_provider_presence_checked": False,
            "product_kid_or_prospectus_risk_disclosure_reviewed": False,
            "official_product_documents_current": False,
            "underlying_index_or_reference_asset_verified": False,
            "nav_or_inav_reconciled_to_market_data": False,
            "tracking_error_or_tracking_difference_reviewed": False,
            "stock_connect_etf_eligibility_or_sell_only_status_reviewed": False,
            "etf_connect_daily_turnover_and_fund_flow_trend_reviewed": False,
            "stock_connect_holiday_eligibility_change_and_cross_boundary_settlement_reviewed": False,
            "southbound_buy_order_availability_and_broker_route_reviewed": False,
            "multi_counter_currency_and_creation_redemption_reviewed": False,
            "underlying_market_trading_hour_and_premium_discount_reviewed": False,
            "cross_market_holiday_fx_and_settlement_risk_reviewed": False,
            "futures_roll_margin_and_contango_backwardation_risk_reviewed": False,
            "distribution_policy_and_capital_distribution_risk_reviewed": False,
            "commodity_trust_single_asset_and_storage_risk_reviewed": False,
            "high_dividend_index_concentration_and_yield_trap_risk_reviewed": False,
            "broker_trading_permission_per_symbol_verified": False,
            "currency_and_board_lot_per_symbol_verified": False,
            "distribution_and_corporate_action_treatment_verified": False,
            EVIDENCE_GENERATED_AT_FIELD: "",
            "evidence_uri": "",
        },
        "runtime_switch_plan": {
            "status": "pending",
            "explicit_deploy_step_required": False,
            "rollback_plan_ready": False,
            "dry_run_first": False,
            "production_cloud_run_not_changed_by_package_merge": False,
            "staged_rollout_plan_ready": False,
            "initial_capital_fraction": None,
            "per_symbol_capital_fraction": None,
            "intraday_drawdown_tripwire": None,
            "cumulative_drawdown_tripwire": None,
            "observation_trading_days_before_scale_up": 0,
            "kill_switch_ready": False,
            "post_deploy_monitoring_ready": False,
            "operator_notification_ready": False,
            "severe_weather_trading_runbook_ready": False,
            "vcm_cooling_off_handling_ready": False,
            EVIDENCE_GENERATED_AT_FIELD: "",
            "evidence_uri": "",
        },
        "risk_approval": {
            "operator_approved": False,
            "live_rollout_approved": False,
            "dry_run_removal_approved": False,
            "approval_reference": "",
        },
    }


def validate_runtime_live_enablement_evidence(
    evidence: Mapping[str, Any],
    *,
    validation_as_of: str | None = None,
) -> dict[str, Any]:
    errors: list[str] = []
    warnings: list[str] = []
    resolved_validation_as_of, validation_as_of_errors = _resolve_validation_as_of(evidence, validation_as_of)
    errors.extend(validation_as_of_errors)
    if evidence.get("evidence_type") != EVIDENCE_TYPE:
        errors.append(f"evidence_type must be {EVIDENCE_TYPE!r}")

    profile_input = str(evidence.get("profile", "")).strip()
    platform = str(evidence.get("platform", "")).strip().lower()
    try:
        profile = resolve_canonical_profile(profile_input)
    except Exception as exc:
        profile = profile_input
        errors.append(str(exc))
    if platform not in SUPPORTED_RUNTIME_PLATFORMS:
        errors.append(f"platform must be one of {sorted(SUPPORTED_RUNTIME_PLATFORMS)}")
    if profile and profile not in get_runtime_enabled_profiles():
        errors.append(f"profile {profile!r} is not runtime_enabled")

    thresholds = PROFILE_LIVE_ENABLEMENT_THRESHOLDS.get(profile, {})
    if not thresholds:
        errors.append(f"profile {profile!r} has no live enablement thresholds")

    missing_sections = [name for name in REQUIRED_SECTIONS if name not in evidence]
    for section in missing_sections:
        errors.append(f"missing required evidence section: {section}")

    if not missing_sections and thresholds:
        for section_name in MAX_ALLOWED_EVIDENCE_AGE_DAYS_BY_SECTION:
            _require_evidence_freshness(
                errors,
                section_name,
                _as_mapping(evidence.get(section_name)),
                validation_as_of=resolved_validation_as_of,
            )
        _validate_strategy_backtest(errors, evidence, profile=profile, thresholds=thresholds)
        _validate_runtime_readiness(errors, evidence, profile=profile, platform=platform)
        _validate_dry_run(errors, evidence, profile=profile)
        _validate_broker_permissions(errors, evidence, profile=profile, platform=platform)
        _validate_switch_plan(errors, evidence)
        _validate_risk_approval(errors, evidence)

    result = {
        "evidence_type": EVIDENCE_TYPE,
        "profile": profile,
        "platform": platform,
        "validation_as_of": resolved_validation_as_of.date().isoformat(),
        "validation_status": "failed",
        "live_enablement_allowed": False,
        "live_enablement_thresholds": dict(thresholds),
        "evidence_uri_policy": build_evidence_uri_policy(),
        "evidence_freshness_policy": build_evidence_freshness_policy(),
        "execution_capacity_policy": build_execution_capacity_policy(profile),
        "dry_run_order_preview_policy": build_dry_run_order_preview_policy(),
        "rollout_risk_policy": build_rollout_risk_policy(),
        "runtime_etf_product_policy": build_runtime_etf_product_policy(),
        "runtime_market_data_policy": build_runtime_market_data_policy(),
        "backtest_validation_policy": build_backtest_validation_policy(),
        "notification_audit_policy": build_notification_audit_policy(RUNTIME_DRY_RUN_NOTIFICATION_EVENT_TYPE),
        "required_sections": list(REQUIRED_SECTIONS),
        "required_live_evidence_fields": list(REQUIRED_LIVE_EVIDENCE_FIELDS),
        "errors": errors,
        "warnings": warnings,
    }
    if not errors:
        result["validation_status"] = "passed"
        result["live_enablement_allowed"] = True
    return result


def validate_runtime_live_enablement_evidence_file(
    path: str | Path,
    *,
    validation_as_of: str | None = None,
) -> dict[str, Any]:
    evidence = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(evidence, Mapping):
        resolved_validation_as_of, validation_as_of_errors = _resolve_validation_as_of({}, validation_as_of)
        return {
            "evidence_type": EVIDENCE_TYPE,
            "profile": "",
            "platform": "",
            "validation_as_of": resolved_validation_as_of.date().isoformat(),
            "validation_status": "failed",
            "live_enablement_allowed": False,
            "live_enablement_thresholds": {},
            "evidence_uri_policy": build_evidence_uri_policy(),
            "evidence_freshness_policy": build_evidence_freshness_policy(),
            "execution_capacity_policy": build_execution_capacity_policy(""),
            "dry_run_order_preview_policy": build_dry_run_order_preview_policy(),
            "rollout_risk_policy": build_rollout_risk_policy(),
            "runtime_etf_product_policy": build_runtime_etf_product_policy(),
            "runtime_market_data_policy": build_runtime_market_data_policy(),
            "notification_audit_policy": build_notification_audit_policy(RUNTIME_DRY_RUN_NOTIFICATION_EVENT_TYPE),
            "required_sections": list(REQUIRED_SECTIONS),
            "required_live_evidence_fields": list(REQUIRED_LIVE_EVIDENCE_FIELDS),
            "errors": [*validation_as_of_errors, "evidence file must contain a JSON object"],
            "warnings": [],
        }
    return validate_runtime_live_enablement_evidence(evidence, validation_as_of=validation_as_of)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate an HK runtime live-enable evidence pack.")
    parser.add_argument("--evidence-file")
    parser.add_argument("--print-template", action="store_true", help="Print a fillable evidence-pack template")
    parser.add_argument("--profile")
    parser.add_argument("--platform", choices=tuple(sorted(SUPPORTED_RUNTIME_PLATFORMS)))
    parser.add_argument("--validation-as-of", help="Override validation date for evidence freshness checks")
    parser.add_argument("--json", action="store_true", help="Print JSON payload")
    args = parser.parse_args(argv)

    if args.print_template:
        if not args.profile or not args.platform:
            parser.error("--profile and --platform are required with --print-template")
        payload = build_runtime_live_enablement_evidence_template(args.profile, platform=args.platform)
        print(json.dumps(payload, indent=2, sort_keys=True))
        return 0

    if not args.evidence_file:
        parser.error("--evidence-file is required unless --print-template is set")

    payload = validate_runtime_live_enablement_evidence_file(args.evidence_file, validation_as_of=args.validation_as_of)
    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        print(f"validation_status={payload['validation_status']}")
        print(f"live_enablement_allowed={payload['live_enablement_allowed']}")
        for error in payload["errors"]:
            print(f"error: {error}")
    return 0 if payload["validation_status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())


__all__ = [
    "EVIDENCE_TYPE",
    "REQUIRED_SECTIONS",
    "build_runtime_live_enablement_evidence_template",
    "main",
    "validate_runtime_live_enablement_evidence",
    "validate_runtime_live_enablement_evidence_file",
]
