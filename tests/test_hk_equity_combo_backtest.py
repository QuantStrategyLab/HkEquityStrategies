from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import pytest

SCRIPTS_DIR = Path(__file__).resolve().parents[1] / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from research_hk_equity_combo_backtest import (  # noqa: E402
    ComboConfig,
    _breadth_regime,
    _dynamic_leg_weights,
)


def _close_frame(rate: float, *, periods: int = 260) -> pd.DataFrame:
    dates = pd.bdate_range("2024-01-02", periods=periods)
    data = {}
    for idx, symbol in enumerate(("02800", "03110", "03188", "03033")):
        start = 20.0 + idx
        data[symbol] = [start * (rate**step) for step in range(periods)]
    return pd.DataFrame(data, index=dates)


def test_breadth_regime_uses_enough_history_for_risk_on():
    close = _close_frame(1.002)

    assert _breadth_regime(close, close.index[-1]) == "risk_on"


def test_breadth_regime_detects_hard_defense():
    close = _close_frame(0.998)

    assert _breadth_regime(close, close.index[-1]) == "hard_defense"


def test_dynamic_leg_weights_match_production_combo_semantics():
    combo = ComboConfig(etf_weight=0.60, dividend_weight=0.40)

    assert _dynamic_leg_weights(combo, "risk_on") == pytest.approx((0.60, 0.40))
    assert _dynamic_leg_weights(combo, "soft_defense") == pytest.approx((0.51, 0.49))
    assert _dynamic_leg_weights(combo, "hard_defense") == pytest.approx((0.30, 0.70))
