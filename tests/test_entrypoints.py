from __future__ import annotations

import pandas as pd
import pytest

from quant_platform_kit.common.models import PortfolioSnapshot, Position
from quant_platform_kit.strategy_contracts import StrategyContext

from hk_equity_strategies import get_strategy_entrypoint
from hk_equity_strategies.catalog import HK_BLUE_CHIP_LEADER_ROTATION_PROFILE, HK_INDEX_MEAN_REVERSION_PROFILE
from hk_equity_strategies.strategies.hk_index_mean_reversion import HSI_ETF_SYMBOL, HSTECH_ETF_SYMBOL


def _snapshot() -> pd.DataFrame:
    rows = [
        ("02800", "ETF", 20.0, 120_000_000, 260, 0.02, 0.04, 0.08, 0.00, 0.01, 0.03, 0.12, -0.10),
        ("00700", "Technology", 320.0, 900_000_000, 260, 0.09, 0.20, 0.35, 0.16, 0.04, 0.12, 0.18, -0.18),
        ("03690", "Technology", 120.0, 300_000_000, 260, 0.08, 0.18, 0.22, 0.14, 0.03, 0.10, 0.20, -0.20),
        ("00941", "Telecom", 75.0, 500_000_000, 260, 0.05, 0.10, 0.16, 0.06, 0.02, 0.08, 0.10, -0.08),
    ]
    return pd.DataFrame(
        rows,
        columns=[
            "symbol",
            "sector",
            "close_hkd",
            "adv20_hkd",
            "history_days",
            "mom_3m",
            "mom_6m",
            "mom_12_1",
            "rel_mom_6m_vs_benchmark",
            "high_252_gap",
            "sma200_gap",
            "vol_63",
            "maxdd_126",
        ],
    ).assign(as_of="2026-04-30", eligible=True)


def test_entrypoint_returns_platform_neutral_weight_targets():
    entrypoint = get_strategy_entrypoint(HK_BLUE_CHIP_LEADER_ROTATION_PROFILE)
    portfolio = PortfolioSnapshot(
        as_of=pd.Timestamp("2026-05-04").to_pydatetime(),
        total_equity=200_000.0,
        positions=(Position(symbol="00941", quantity=1000, market_value=75_000.0),),
    )

    decision = entrypoint.evaluate(
        StrategyContext(
            as_of="2026-05-04",
            market_data={"feature_snapshot": _snapshot()},
            portfolio=portfolio,
            runtime_config={"holdings_count": 2, "min_adv20_hkd": 1},
        )
    )

    weights = {position.symbol: position.target_weight for position in decision.positions}
    assert set(weights) >= {"02800", "00700"}
    assert abs(sum(float(value) for value in weights.values()) - 1.0) < 1e-9
    assert decision.diagnostics["signal_source"] == "feature_snapshot"
    assert decision.diagnostics["actionable"] is True


def _index_history() -> pd.DataFrame:
    dates = pd.bdate_range("2025-01-02", periods=300)
    rows = []
    for idx, date in enumerate(dates):
        anchor = 20.0 + idx * 0.01
        ratio = 0.20 if idx < 295 else 0.14
        rows.append({"date": date, "symbol": HSI_ETF_SYMBOL, "close": anchor})
        rows.append({"date": date, "symbol": HSTECH_ETF_SYMBOL, "close": anchor * ratio})
    return pd.DataFrame(rows)


def test_index_mean_reversion_entrypoint_returns_direct_market_history_weight_targets():
    entrypoint = get_strategy_entrypoint(HK_INDEX_MEAN_REVERSION_PROFILE)

    decision = entrypoint.evaluate(
        StrategyContext(
            as_of="2026-02-25",
            market_data={"market_history": _index_history()},
            runtime_config={"min_history_days": 260},
        )
    )

    weights = {position.symbol: position.target_weight for position in decision.positions}
    assert weights[HSI_ETF_SYMBOL] == pytest.approx(0.35)
    assert weights[HSTECH_ETF_SYMBOL] == pytest.approx(0.65)
    assert decision.diagnostics["signal_source"] == "daily_market_history"
    assert decision.diagnostics["actionable"] is True
