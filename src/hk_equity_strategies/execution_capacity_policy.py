from __future__ import annotations

from .policy_catalog import (
    build_execution_capacity_policy as build_execution_capacity_policy,
    get_min_median_daily_turnover_hkd as get_min_median_daily_turnover_hkd,
    get_policy_spec,
    get_required_execution_capacity_fields as get_required_execution_capacity_fields,
)

_SPEC = get_policy_spec("execution_capacity")

DEFAULT_MIN_ADV_WINDOW_TRADING_DAYS = int(_SPEC["default_min_adv_window_trading_days"])
DEFAULT_MIN_MEDIAN_DAILY_TURNOVER_HKD = int(_SPEC["default_min_median_daily_turnover_hkd"])
DEFAULT_MAX_SINGLE_ORDER_ADV_FRACTION = float(_SPEC["default_max_single_order_adv_fraction"])
DEFAULT_MAX_REBALANCE_ADV_FRACTION = float(_SPEC["default_max_rebalance_adv_fraction"])
MIN_MEDIAN_DAILY_TURNOVER_HKD_BY_PROFILE: dict[str, int] = dict(_SPEC["min_median_daily_turnover_hkd_by_profile"])
REQUIRED_EXECUTION_CAPACITY_FIELDS: tuple[str, ...] = tuple(_SPEC["required_boolean_fields"])
REQUIRED_EQUITY_EXECUTION_CAPACITY_FIELDS: tuple[str, ...] = tuple(_SPEC["required_equity_boolean_fields"])
EXECUTION_CAPACITY_REFERENCE_URLS: tuple[str, ...] = tuple(_SPEC["source_reference_urls"])
