"""Explicit runtime-selectable profiles for HK equity strategies."""

RUNTIME_SELECTABLE_ALLOWLIST_V1 = frozenset(
    {"hk_global_etf_tactical_rotation", "hk_low_vol_dividend_quality_snapshot"}
)


def get_runtime_selectable_profiles() -> frozenset[str]:
    return RUNTIME_SELECTABLE_ALLOWLIST_V1
