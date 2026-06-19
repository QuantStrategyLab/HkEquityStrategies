from __future__ import annotations

from typing import Any

DEFAULT_MIN_ADV_WINDOW_TRADING_DAYS = 20
DEFAULT_MIN_MEDIAN_DAILY_TURNOVER_HKD = 10_000_000
DEFAULT_MAX_SINGLE_ORDER_ADV_FRACTION = 0.025
DEFAULT_MAX_REBALANCE_ADV_FRACTION = 0.10

MIN_MEDIAN_DAILY_TURNOVER_HKD_BY_PROFILE: dict[str, int] = {
    "hk_global_etf_tactical_rotation": 20_000_000,
    "hk_low_vol_dividend_quality_snapshot": 30_000_000,
}

REQUIRED_EXECUTION_CAPACITY_FIELDS: tuple[str, ...] = (
    "liquidity_cap_verified",
    "board_lot_rounding_verified",
    "odd_lot_avoidance_verified",
    "market_session_routing_verified",
    "vcm_price_band_controls_verified",
    "etf_nav_or_spread_guard_verified",
)

REQUIRED_EQUITY_EXECUTION_CAPACITY_FIELDS: tuple[str, ...] = (
    "liquidity_cap_verified",
    "board_lot_rounding_verified",
    "odd_lot_avoidance_verified",
    "market_session_routing_verified",
    "vcm_price_band_controls_verified",
    "equity_spread_and_trading_status_guard_verified",
)

EXECUTION_CAPACITY_REFERENCE_URLS: tuple[str, ...] = (
    "https://www.hkex.com.hk/Services/Trading/Securities/Overview/Trading-Mechanism?sc_lang=en",
    "https://www.hkex.com.hk/Global/Exchange/FAQ/Securities-Market/Trading?sc_lang=en",
    "https://www.ird.gov.hk/eng/faq/ETFs.htm",
    "https://www.hkex.com.hk/Mutual-Market/Connect-Hub/Stock-Connect-White-Paper?sc_lang=en",
)


def get_min_median_daily_turnover_hkd(profile: str) -> int:
    return MIN_MEDIAN_DAILY_TURNOVER_HKD_BY_PROFILE.get(
        str(profile or "").strip(),
        DEFAULT_MIN_MEDIAN_DAILY_TURNOVER_HKD,
    )


def get_required_execution_capacity_fields(profile: str) -> tuple[str, ...]:
    if str(profile or "").strip() == "hk_low_vol_dividend_quality_snapshot":
        return REQUIRED_EQUITY_EXECUTION_CAPACITY_FIELDS
    return REQUIRED_EXECUTION_CAPACITY_FIELDS


def build_execution_capacity_policy(profile: str) -> dict[str, Any]:
    is_equity_profile = str(profile or "").strip() == "hk_low_vol_dividend_quality_snapshot"
    return {
        "required": True,
        "min_adv_window_trading_days": DEFAULT_MIN_ADV_WINDOW_TRADING_DAYS,
        "min_median_daily_turnover_hkd": get_min_median_daily_turnover_hkd(profile),
        "max_single_order_adv_fraction": DEFAULT_MAX_SINGLE_ORDER_ADV_FRACTION,
        "max_rebalance_adv_fraction": DEFAULT_MAX_REBALANCE_ADV_FRACTION,
        "required_boolean_fields": list(get_required_execution_capacity_fields(profile)),
        "source_reference_urls": list(EXECUTION_CAPACITY_REFERENCE_URLS),
        "description": (
            "Runtime dry-run evidence must prove HK single-name equity liquidity, board-lot routing, "
            "odd-lot avoidance, VCM/price-band controls, trading-status checks, and conservative ADV "
            "capacity before live enablement."
            if is_equity_profile
            else "Runtime dry-run evidence must prove HK ETF liquidity, board-lot routing, odd-lot avoidance, VCM/price-band controls, and conservative ADV capacity before live enablement."
        ),
    }
