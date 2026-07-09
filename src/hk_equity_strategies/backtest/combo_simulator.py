"""Research combo backtest for HK ETF rotation + dividend proxy."""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any, Literal, Mapping

import pandas as pd

from hk_equity_strategies.backtest.etf_rotation_simulator import (
    HkRotationBacktestConfig,
    HkRotationBacktestResult,
    StrategySignalFn,
    build_rebalance_dates,
    build_rotation_target_weights,
    compute_backtest_metrics,
)
from hk_equity_strategies.strategies.etf_rotation_core import build_close_matrix
from hk_equity_strategies.strategies.hk_equity_combo import (
    DEFAULT_DIVIDEND_WEIGHT,
    DEFAULT_ETF_WEIGHT,
    _apply_dividend_regime,
)

ComboMode = Literal["static", "dynamic"]
DIVIDEND_SYMBOL = "03110"
DIVIDEND_ANNUAL_VOL_SCALE = 0.85


@dataclass(frozen=True)
class HkComboBacktestConfig:
    etf_weight: float = DEFAULT_ETF_WEIGHT
    dividend_weight: float = DEFAULT_DIVIDEND_WEIGHT
    combo_mode: ComboMode = "dynamic"
    min_history_days: int = 260
    cost_bps: float = 10.0
    rebalance_frequency: str = "monthly"
    volatility_window_days: int = 63


def _simulate_dividend_returns(close: pd.DataFrame, *, volatility_window_days: int) -> pd.Series:
    returns = close.pct_change().fillna(0.0)
    if DIVIDEND_SYMBOL in close.columns:
        raw = returns[DIVIDEND_SYMBOL]
    else:
        raw = returns.mean(axis=1)
    rolling_vol = raw.rolling(volatility_window_days).std(ddof=0) * math.sqrt(252)
    target_vol = rolling_vol * DIVIDEND_ANNUAL_VOL_SCALE
    scale = target_vol / rolling_vol.replace(0.0, pd.NA)
    return raw * scale.fillna(1.0).clip(upper=2.0)


def _breadth_regime(close: pd.DataFrame, as_of: pd.Timestamp) -> str:
    window = close.loc[:as_of]
    if len(window) < 100:
        return "risk_on"
    sma200 = window.rolling(200, min_periods=100).mean()
    above_sma = (window.iloc[-1] > sma200.iloc[-1]).sum()
    breadth = above_sma / max(len(close.columns), 1)
    if breadth < 0.30:
        return "hard_defense"
    if breadth < 0.45:
        return "soft_defense"
    return "risk_on"


def _combo_strategy_returns(
    market_history: pd.DataFrame,
    close: pd.DataFrame,
    *,
    signal_fn: StrategySignalFn,
    rotation_config: HkRotationBacktestConfig,
    combo_config: HkComboBacktestConfig,
    strategy_kwargs: Mapping[str, Any],
) -> pd.Series:
    etf_targets = build_rotation_target_weights(
        market_history,
        close,
        signal_fn=signal_fn,
        config=rotation_config,
        strategy_kwargs=strategy_kwargs,
    )
    dividend_returns = _simulate_dividend_returns(
        close,
        volatility_window_days=combo_config.volatility_window_days,
    )
    rebalance_dates = build_rebalance_dates(
        pd.DatetimeIndex(close.index),
        frequency=combo_config.rebalance_frequency,
    )
    rebalance_dates = rebalance_dates[rebalance_dates <= close.index[-1]]

    weight_schedule: list[dict[str, Any]] = []
    for target_date in rebalance_dates:
        pos = close.index.searchsorted(target_date, side="right") - 1
        if pos < 0:
            continue
        as_of = pd.Timestamp(close.index[pos])
        if combo_config.combo_mode == "static":
            etf_target_weight = combo_config.etf_weight
            div_target_weight = combo_config.dividend_weight
        else:
            regime = _breadth_regime(close, as_of)
            etf_target_weight, div_target_weight, _ = _apply_dividend_regime(
                combo_config.etf_weight,
                regime,
            )

        base_etf_weights = (
            etf_targets.loc[as_of]
            if as_of in etf_targets.index
            else pd.Series(0.0, index=close.columns)
        )
        etf_gross = float(base_etf_weights.sum())
        if etf_gross > 0.0:
            scaled_etf = base_etf_weights.multiply(etf_target_weight / etf_gross)
        else:
            scaled_etf = base_etf_weights * 0.0

        row: dict[str, float] = {
            symbol: float(scaled_etf.get(symbol, 0.0)) for symbol in close.columns
        }
        if DIVIDEND_SYMBOL not in row:
            row[DIVIDEND_SYMBOL] = 0.0
        row[DIVIDEND_SYMBOL] += div_target_weight
        weight_schedule.append({"date": as_of, **row})

    weights = pd.DataFrame(weight_schedule).set_index("date")
    weights = weights.reindex(close.index, method="ffill").fillna(0.0)
    weights = weights.shift(1).fillna(0.0)

    asset_returns = close.pct_change().fillna(0.0)
    if DIVIDEND_SYMBOL in asset_returns.columns:
        asset_returns[DIVIDEND_SYMBOL] = dividend_returns

    portfolio_returns = (weights * asset_returns).sum(axis=1)
    turnover = weights.diff().abs().sum(axis=1).fillna(0.0)
    return portfolio_returns - turnover * combo_config.cost_bps / 10_000.0


def run_combo_backtest(
    market_history: pd.DataFrame,
    strategy_signal_fn: StrategySignalFn,
    *,
    combo_config: HkComboBacktestConfig | None = None,
    rotation_config: HkRotationBacktestConfig | None = None,
    universe_symbols: Any = None,
    strategy_kwargs: Mapping[str, Any] | None = None,
) -> HkRotationBacktestResult:
    combo = combo_config or HkComboBacktestConfig()
    rotation = rotation_config or HkRotationBacktestConfig(
        min_history_days=combo.min_history_days,
        cost_bps=combo.cost_bps,
        rebalance_frequency=combo.rebalance_frequency,
    )
    close = build_close_matrix(market_history, universe_symbols=universe_symbols)
    if len(close) < int(combo.min_history_days):
        raise ValueError(
            f"market_history requires at least {int(combo.min_history_days)} overlapping trading days"
        )
    net = _combo_strategy_returns(
        market_history,
        close,
        signal_fn=strategy_signal_fn,
        rotation_config=rotation,
        combo_config=combo,
        strategy_kwargs=dict(strategy_kwargs or {}),
    )
    return HkRotationBacktestResult(daily_returns=net, metrics=compute_backtest_metrics(net))


__all__ = [
    "DIVIDEND_SYMBOL",
    "HkComboBacktestConfig",
    "run_combo_backtest",
]
