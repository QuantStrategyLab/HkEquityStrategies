"""Declarative JSON policy catalog loader and builders for HK equity strategies."""

from __future__ import annotations

import json
from collections.abc import Mapping
from functools import lru_cache
from importlib.resources import files
from typing import Any


@lru_cache(maxsize=1)
def _load_policies() -> dict[str, Any]:
    raw_text = files(__package__).joinpath("policies", "policies.json").read_text(encoding="utf-8")
    data = json.loads(raw_text)
    if not isinstance(data, dict):
        raise ValueError("Policy catalog file 'policies.json' must contain a JSON object")
    return data


def get_policy_spec(policy_name: str) -> Mapping[str, Any]:
    policies = _load_policies()
    try:
        spec = policies[policy_name]
    except KeyError as exc:
        raise KeyError(f"Unknown policy {policy_name!r}") from exc
    if not isinstance(spec, Mapping):
        raise ValueError(f"Policy {policy_name!r} must be a mapping")
    return spec


def build_backtest_validation_policy() -> dict[str, Any]:
    spec = get_policy_spec("backtest_validation")
    return {
        "required": bool(spec["required"]),
        "policy_version": str(spec["policy_version"]),
        "scope": str(spec["scope"]),
        "live_enablement_allowed_without_policy_evidence": bool(
            spec["live_enablement_allowed_without_policy_evidence"]
        ),
        "max_allowed_drawdown": float(spec["max_allowed_drawdown"]),
        "min_return_to_drawdown_ratio": float(spec["min_return_to_drawdown_ratio"]),
        "min_required_oos_fold_count": int(spec["min_required_oos_fold_count"]),
        "max_single_period_return_contribution": float(spec["max_single_period_return_contribution"]),
        "required_boolean_fields": list(spec["required_boolean_fields"]),
        "required_risk_constraints": list(spec["required_risk_constraints"]),
        "required_metrics": list(spec["required_metrics"]),
        "reject_criteria": list(spec["reject_criteria"]),
        "description": str(spec["description"]),
    }


def build_dry_run_order_preview_policy() -> dict[str, Any]:
    spec = get_policy_spec("dry_run_order_preview")
    return {
        "required": bool(spec["required"]),
        "policy_version": str(spec["policy_version"]),
        "required_fields": list(spec["required_fields"]),
        "required_uri_fields": list(spec["required_uri_fields"]),
        "required_sha256_fields": list(spec["required_sha256_fields"]),
        "required_boolean_fields": list(spec["required_boolean_fields"]),
        "source_reference_urls": list(spec["source_reference_urls"]),
        "description": str(spec["description"]),
    }


def build_evidence_freshness_policy() -> dict[str, Any]:
    spec = get_policy_spec("evidence_freshness")
    return {
        "required": bool(spec["required"]),
        "required_field": str(spec["required_field"]),
        "max_allowed_age_days_by_section": dict(spec["max_allowed_age_days_by_section"]),
    }


def build_evidence_uri_policy() -> dict[str, Any]:
    spec = get_policy_spec("evidence_uri")
    return {
        "required": bool(spec["required"]),
        "allowed_schemes": [f"{scheme}://" for scheme in spec["allowed_schemes"]],
        "rejected_query_markers": list(spec["rejected_query_markers"]),
        "description": str(spec["description"]),
    }


def get_min_median_daily_turnover_hkd(profile: str) -> int:
    spec = get_policy_spec("execution_capacity")
    by_profile = spec["min_median_daily_turnover_hkd_by_profile"]
    normalized = str(profile or "").strip()
    return int(by_profile.get(normalized, spec["default_min_median_daily_turnover_hkd"]))


def get_required_execution_capacity_fields(profile: str) -> tuple[str, ...]:
    spec = get_policy_spec("execution_capacity")
    if str(profile or "").strip() == str(spec["equity_profile"]):
        return tuple(spec["required_equity_boolean_fields"])
    return tuple(spec["required_boolean_fields"])


def build_execution_capacity_policy(profile: str) -> dict[str, Any]:
    spec = get_policy_spec("execution_capacity")
    is_equity_profile = str(profile or "").strip() == str(spec["equity_profile"])
    descriptions = spec["descriptions"]
    return {
        "required": bool(spec["required"]),
        "min_adv_window_trading_days": int(spec["default_min_adv_window_trading_days"]),
        "min_median_daily_turnover_hkd": get_min_median_daily_turnover_hkd(profile),
        "max_single_order_adv_fraction": float(spec["default_max_single_order_adv_fraction"]),
        "max_rebalance_adv_fraction": float(spec["default_max_rebalance_adv_fraction"]),
        "required_boolean_fields": list(get_required_execution_capacity_fields(profile)),
        "source_reference_urls": list(spec["source_reference_urls"]),
        "description": str(descriptions["equity"] if is_equity_profile else descriptions["default"]),
    }


def build_notification_audit_policy(expected_event_type: str | None = None) -> dict[str, Any]:
    spec = get_policy_spec("notification_audit")
    return {
        "required": bool(spec["required"]),
        "schema_version": str(spec["schema_version"]),
        "expected_event_type": expected_event_type or str(spec["default_event_type"]),
        "supported_event_types": list(spec["supported_event_types"]),
        "required_fields": list(spec["required_fields"]),
        "required_boolean_fields": list(spec["required_boolean_fields"]),
        "required_uri_fields": list(spec["required_uri_fields"]),
        "source_reference_urls": list(spec["source_reference_urls"]),
        "description": str(spec["description"]),
    }


def build_rollout_risk_policy() -> dict[str, Any]:
    spec = get_policy_spec("rollout_risk")
    return {
        "required": bool(spec["required"]),
        "max_initial_capital_fraction": float(spec["max_initial_capital_fraction"]),
        "max_per_symbol_capital_fraction": float(spec["max_per_symbol_capital_fraction"]),
        "max_intraday_drawdown_tripwire": float(spec["max_intraday_drawdown_tripwire"]),
        "max_cumulative_drawdown_tripwire": float(spec["max_cumulative_drawdown_tripwire"]),
        "min_observation_trading_days_before_scale_up": int(spec["min_observation_trading_days_before_scale_up"]),
        "required_boolean_fields": list(spec["required_boolean_fields"]),
        "source_reference_urls": list(spec["source_reference_urls"]),
        "description": str(spec["description"]),
    }


def _build_field_provenance_policy(policy_name: str, *, include_version: bool) -> dict[str, Any]:
    spec = get_policy_spec(policy_name)
    payload: dict[str, Any] = {
        "required": bool(spec["required"]),
    }
    if include_version:
        payload["policy_version"] = str(spec["policy_version"])
    payload.update(
        {
            "required_fields": list(spec["required_fields"]),
            "required_uri_fields": list(spec["required_uri_fields"]),
            "required_boolean_fields": list(spec["required_boolean_fields"]),
            "source_reference_urls": list(spec["source_reference_urls"]),
            "description": str(spec["description"]),
        }
    )
    return payload


def build_runtime_equity_product_policy() -> dict[str, Any]:
    return _build_field_provenance_policy("runtime_equity_product", include_version=True)


def build_runtime_etf_product_policy() -> dict[str, Any]:
    return _build_field_provenance_policy("runtime_etf_product", include_version=True)


def build_runtime_market_data_policy() -> dict[str, Any]:
    return _build_field_provenance_policy("runtime_market_data", include_version=False)


def build_shared_runtime_policies(
    profile: str = "",
    *,
    include_backtest_validation: bool = True,
    expected_notification_event_type: str | None = None,
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "evidence_uri_policy": build_evidence_uri_policy(),
        "evidence_freshness_policy": build_evidence_freshness_policy(),
        "execution_capacity_policy": build_execution_capacity_policy(profile),
        "dry_run_order_preview_policy": build_dry_run_order_preview_policy(),
        "rollout_risk_policy": build_rollout_risk_policy(),
        "runtime_etf_product_policy": build_runtime_etf_product_policy(),
        "runtime_equity_product_policy": build_runtime_equity_product_policy(),
        "runtime_market_data_policy": build_runtime_market_data_policy(),
    }
    if include_backtest_validation:
        payload["backtest_validation_policy"] = build_backtest_validation_policy()
    payload["notification_audit_policy"] = build_notification_audit_policy(expected_notification_event_type)
    return payload


__all__ = [
    "build_backtest_validation_policy",
    "build_dry_run_order_preview_policy",
    "build_evidence_freshness_policy",
    "build_evidence_uri_policy",
    "build_execution_capacity_policy",
    "build_notification_audit_policy",
    "build_rollout_risk_policy",
    "build_runtime_equity_product_policy",
    "build_runtime_etf_product_policy",
    "build_runtime_market_data_policy",
    "build_shared_runtime_policies",
    "get_min_median_daily_turnover_hkd",
    "get_policy_spec",
    "get_required_execution_capacity_fields",
]
