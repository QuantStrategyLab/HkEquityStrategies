from __future__ import annotations

from dataclasses import replace

from quant_platform_kit.strategy_contracts import (
    StrategyRuntimeAdapter,
    validate_strategy_runtime_adapter,
)

from hk_equity_strategies.catalog import (
    HK_HIGH_DIVIDEND_LOW_VOL_TREND_PROFILE,
    HK_LISTED_GLOBAL_ETF_ROTATION_PROFILE,
    HK_LOW_VOL_DIVIDEND_QUALITY_PROFILE,
    get_strategy_definition,
    get_strategy_definitions,
    resolve_canonical_profile,
)
from hk_equity_strategies.strategies import hk_high_dividend_low_vol_trend as high_dividend_strategy
from hk_equity_strategies.strategies import hk_listed_global_etf_rotation as global_etf_strategy
from hk_equity_strategies.strategies import hk_low_vol_dividend_quality as low_vol_dividend_strategy

IBKR_PLATFORM = "ibkr"
LONGBRIDGE_PLATFORM = "longbridge"
SUPPORTED_RUNTIME_PLATFORMS = frozenset({IBKR_PLATFORM, LONGBRIDGE_PLATFORM})

PLATFORM_NATIVE_TARGET_MODES: dict[str, str] = {
    IBKR_PLATFORM: "weight",
    LONGBRIDGE_PLATFORM: "value",
}

BASE_RUNTIME_ADAPTERS: dict[str, StrategyRuntimeAdapter] = {
    HK_LISTED_GLOBAL_ETF_ROTATION_PROFILE: StrategyRuntimeAdapter(
        status_icon=global_etf_strategy.STATUS_ICON,
        managed_symbols_extractor=global_etf_strategy.extract_managed_symbols,
    ),
    HK_HIGH_DIVIDEND_LOW_VOL_TREND_PROFILE: StrategyRuntimeAdapter(
        status_icon=high_dividend_strategy.STATUS_ICON,
        managed_symbols_extractor=high_dividend_strategy.extract_managed_symbols,
    ),
    HK_LOW_VOL_DIVIDEND_QUALITY_PROFILE: StrategyRuntimeAdapter(
        status_icon=low_vol_dividend_strategy.STATUS_ICON,
        available_inputs=frozenset({"feature_snapshot"}),
        required_feature_columns=low_vol_dividend_strategy.REQUIRED_FACTOR_COLUMNS,
        require_snapshot_manifest=low_vol_dividend_strategy.REQUIRE_SNAPSHOT_MANIFEST,
        snapshot_contract_version=low_vol_dividend_strategy.SNAPSHOT_CONTRACT_VERSION,
        managed_symbols_extractor=low_vol_dividend_strategy.extract_managed_symbols,
    ),
}


def _build_runtime_adapter_for_platform(
    profile: str,
    *,
    platform_id: str,
) -> StrategyRuntimeAdapter:
    canonical_profile = resolve_canonical_profile(profile)
    normalized_platform = str(platform_id).strip().lower()
    if normalized_platform not in SUPPORTED_RUNTIME_PLATFORMS:
        raise ValueError(f"Unsupported platform runtime adapter lookup for {platform_id!r}")

    definition = get_strategy_definition(canonical_profile)
    if normalized_platform not in definition.supported_platforms:
        raise ValueError(
            f"Strategy profile {canonical_profile!r} does not declare support for platform {platform_id!r}"
        )

    try:
        base_adapter = BASE_RUNTIME_ADAPTERS[canonical_profile]
    except KeyError as exc:
        raise ValueError(f"Strategy profile {canonical_profile!r} has no runtime adapter spec") from exc

    available_inputs = set(base_adapter.available_inputs or definition.required_inputs)
    available_inputs.update(definition.required_inputs)

    native_target_mode = PLATFORM_NATIVE_TARGET_MODES[normalized_platform]
    if definition.target_mode != native_target_mode:
        available_inputs.add("portfolio_snapshot")

    portfolio_input_name = base_adapter.portfolio_input_name
    if "portfolio_snapshot" in available_inputs:
        portfolio_input_name = portfolio_input_name or "portfolio_snapshot"

    available_capabilities = set(base_adapter.available_capabilities)
    if normalized_platform == IBKR_PLATFORM:
        available_capabilities.add("broker_client")

    return validate_strategy_runtime_adapter(
        replace(
            base_adapter,
            available_inputs=frozenset(available_inputs),
            available_capabilities=frozenset(available_capabilities),
            portfolio_input_name=portfolio_input_name,
        )
    )


def _build_platform_runtime_adapter_map(platform_id: str) -> dict[str, StrategyRuntimeAdapter]:
    normalized_platform = str(platform_id).strip().lower()
    adapters: dict[str, StrategyRuntimeAdapter] = {}
    for profile, definition in get_strategy_definitions().items():
        if normalized_platform not in definition.supported_platforms:
            continue
        adapters[profile] = _build_runtime_adapter_for_platform(
            profile,
            platform_id=normalized_platform,
        )
    return adapters


PLATFORM_RUNTIME_ADAPTERS: dict[str, dict[str, StrategyRuntimeAdapter]] = {
    platform_id: _build_platform_runtime_adapter_map(platform_id)
    for platform_id in sorted(SUPPORTED_RUNTIME_PLATFORMS)
}


def derive_runtime_input_mode(required_inputs: frozenset[str] | set[str] | tuple[str, ...]) -> str:
    normalized = frozenset(str(value).strip() for value in required_inputs)
    if normalized == frozenset({"feature_snapshot"}):
        return "feature_snapshot"
    if normalized == frozenset({"market_history"}):
        return "market_history"
    return "+".join(sorted(normalized)) or "none"


def describe_platform_runtime_requirements(profile: str | None, *, platform_id: str) -> dict[str, object]:
    canonical_profile = resolve_canonical_profile(profile)
    definition = get_strategy_definition(canonical_profile)
    adapter = get_platform_runtime_adapter(canonical_profile, platform_id=platform_id)
    requires_snapshot_artifacts = "feature_snapshot" in frozenset(definition.required_inputs)
    return {
        "input_mode": derive_runtime_input_mode(definition.required_inputs),
        "requires_snapshot_artifacts": requires_snapshot_artifacts,
        "requires_snapshot_manifest_path": bool(
            requires_snapshot_artifacts and adapter.require_snapshot_manifest
        ),
        "requires_strategy_config_path": False,
        "config_source_policy": "none",
        "reconciliation_output_policy": "optional",
        "profile_group": "snapshot_backed" if requires_snapshot_artifacts else "direct_runtime_inputs",
    }


def get_platform_runtime_adapter(profile: str | None, *, platform_id: str) -> StrategyRuntimeAdapter:
    canonical_profile = resolve_canonical_profile(profile)
    adapters = PLATFORM_RUNTIME_ADAPTERS.get(str(platform_id).strip().lower())
    if adapters is None:
        raise ValueError(f"Unsupported platform runtime adapter lookup for {platform_id!r}")
    try:
        adapter = adapters[canonical_profile]
    except KeyError as exc:
        raise ValueError(
            f"Strategy profile {canonical_profile!r} has no runtime adapter for platform {platform_id!r}"
        ) from exc
    return validate_strategy_runtime_adapter(adapter)


__all__ = [
    "BASE_RUNTIME_ADAPTERS",
    "IBKR_PLATFORM",
    "LONGBRIDGE_PLATFORM",
    "PLATFORM_NATIVE_TARGET_MODES",
    "PLATFORM_RUNTIME_ADAPTERS",
    "SUPPORTED_RUNTIME_PLATFORMS",
    "derive_runtime_input_mode",
    "describe_platform_runtime_requirements",
    "get_platform_runtime_adapter",
]
