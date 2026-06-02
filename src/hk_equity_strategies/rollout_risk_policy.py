from __future__ import annotations

from typing import Any

MAX_INITIAL_CAPITAL_FRACTION = 0.25
MAX_PER_SYMBOL_CAPITAL_FRACTION = 0.15
MAX_INTRADAY_DRAWDOWN_TRIPWIRE = 0.03
MAX_CUMULATIVE_DRAWDOWN_TRIPWIRE = 0.05
MIN_OBSERVATION_TRADING_DAYS_BEFORE_SCALE_UP = 20

REQUIRED_ROLLOUT_RISK_FIELDS: tuple[str, ...] = (
    "staged_rollout_plan_ready",
    "kill_switch_ready",
    "rollback_plan_ready",
    "post_deploy_monitoring_ready",
    "operator_notification_ready",
    "severe_weather_trading_runbook_ready",
    "vcm_cooling_off_handling_ready",
)

ROLLOUT_RISK_REFERENCE_URLS: tuple[str, ...] = (
    "https://www.hkex.com.hk/Services/Trading-hours-and-Severe-Weather-Arrangements/Severe-Weather-Arrangements/Overview?sc_lang=en",
    "https://www.hkex.com.hk/Services/Trading/Securities/Overview/Trading-Mechanism?sc_lang=en",
    "https://www.sfc.hk/en/Published-resources/Consultations/sfc-proposes-to-enhance-the-regulatory-framework-for-electronic-trading",
)


def build_rollout_risk_policy() -> dict[str, Any]:
    return {
        "required": True,
        "max_initial_capital_fraction": MAX_INITIAL_CAPITAL_FRACTION,
        "max_per_symbol_capital_fraction": MAX_PER_SYMBOL_CAPITAL_FRACTION,
        "max_intraday_drawdown_tripwire": MAX_INTRADAY_DRAWDOWN_TRIPWIRE,
        "max_cumulative_drawdown_tripwire": MAX_CUMULATIVE_DRAWDOWN_TRIPWIRE,
        "min_observation_trading_days_before_scale_up": MIN_OBSERVATION_TRADING_DAYS_BEFORE_SCALE_UP,
        "required_boolean_fields": list(REQUIRED_ROLLOUT_RISK_FIELDS),
        "source_reference_urls": list(ROLLOUT_RISK_REFERENCE_URLS),
        "description": "HK live enablement must start with a capped rollout, explicit tripwires, operator notifications, SWT/VCM runbooks, and rollback controls before dry-run is removed or capital is scaled.",
    }
