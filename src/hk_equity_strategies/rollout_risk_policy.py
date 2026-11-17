from __future__ import annotations

from .policy_catalog import (
    build_rollout_risk_policy as build_rollout_risk_policy,
    get_policy_spec,
)

_SPEC = get_policy_spec("rollout_risk")

MAX_INITIAL_CAPITAL_FRACTION = float(_SPEC["max_initial_capital_fraction"])
MAX_PER_SYMBOL_CAPITAL_FRACTION = float(_SPEC["max_per_symbol_capital_fraction"])
MAX_INTRADAY_DRAWDOWN_TRIPWIRE = float(_SPEC["max_intraday_drawdown_tripwire"])
MAX_CUMULATIVE_DRAWDOWN_TRIPWIRE = float(_SPEC["max_cumulative_drawdown_tripwire"])
MIN_OBSERVATION_TRADING_DAYS_BEFORE_SCALE_UP = int(_SPEC["min_observation_trading_days_before_scale_up"])
REQUIRED_ROLLOUT_RISK_FIELDS: tuple[str, ...] = tuple(_SPEC["required_boolean_fields"])
ROLLOUT_RISK_REFERENCE_URLS: tuple[str, ...] = tuple(_SPEC["source_reference_urls"])
