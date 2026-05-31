from __future__ import annotations

from typing import Any

from hk_equity_strategies.catalog import (
    HK_EQUITY_DOMAIN,
    HK_LISTED_GLOBAL_ETF_ROTATION_PROFILE,
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
    "Production Cloud Run must not be changed by package merge alone; rollout requires an explicit deploy step.",
)

HK_DERIVATIVE_OR_COMPLEX_ETF_SYMBOLS = frozenset({"03175"})


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


def _build_risk_notes(symbols: tuple[str, ...], *, runtime_enabled: bool) -> tuple[str, ...]:
    notes: list[str] = [
        "HK live trading remains blocked unless the platform dry-run plan is explicitly approved.",
        "This readiness plan is a configuration and validation checklist; it does not deploy Cloud Run.",
    ]
    if not runtime_enabled:
        notes.append("The profile is not runtime_enabled, so live order submission must remain disabled.")
    if HK_DERIVATIVE_OR_COMPLEX_ETF_SYMBOLS.intersection(symbols):
        notes.append("03175 is a crude-oil futures ETF; confirm suitability, spread, and product permission before live use.")
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
        "order_conversion_checks": list(ORDER_CONVERSION_CHECKS),
        "live_enablement_requirements": list(LIVE_ENABLEMENT_REQUIREMENTS),
        "risk_notes": list(_build_risk_notes(managed_symbols, runtime_enabled=runtime_enabled)),
    }


__all__ = [
    "HK_DRY_RUN_CHECKS",
    "HK_MARKET_DEFAULTS",
    "LIVE_ENABLEMENT_REQUIREMENTS",
    "ORDER_CONVERSION_CHECKS",
    "PLATFORM_HK_DRY_RUN_ENV",
    "build_hk_runtime_readiness",
]
