"""BacktestRunner adapter for HK ETF rotation strategies."""

from __future__ import annotations

import hashlib
import math
from collections.abc import Mapping
from datetime import UTC, date, datetime, timezone
from typing import Any, cast

import pandas as pd

from hk_equity_strategies.backtest.combo_simulator import ComboMode, HkComboBacktestConfig, run_combo_backtest
from hk_equity_strategies.backtest.etf_rotation_simulator import HkRotationBacktestConfig, run_etf_rotation_backtest
from hk_equity_strategies.strategies.hk_equity_combo import PROFILE_NAME as HK_EQUITY_COMBO_PROFILE
from hk_equity_strategies.strategies.hk_global_etf_tactical_rotation import (
    DEFAULT_MIN_HISTORY_DAYS,
    DEFAULT_UNIVERSE_SYMBOLS,
    build_target_weights,
    extract_managed_symbols,
)
from hk_equity_strategies.strategies.hk_global_etf_tactical_rotation import (
    PROFILE_NAME as HK_GLOBAL_ETF_TACTICAL_ROTATION_PROFILE,
)

try:
    from quant_platform_kit.strategy_lifecycle.contracts import BacktestResult
except ImportError:  # pragma: no cover
    BacktestResult = None  # type: ignore[misc, assignment]


SUPPORTED_PROFILES = frozenset({HK_GLOBAL_ETF_TACTICAL_ROTATION_PROFILE, HK_EQUITY_COMBO_PROFILE})
SYNTHETIC_MARKET_HISTORY_GENERATOR_VERSION = "hk_equity_market_history.v1"


def _synthetic_path_parameter(*, seed: int, symbol: str, label: str) -> float:
    material = "\x1f".join((SYNTHETIC_MARKET_HISTORY_GENERATOR_VERSION, str(seed), symbol, label)).encode("utf-8")
    return int.from_bytes(hashlib.sha256(material).digest(), "big", signed=False) / (1 << 256)


def _synthetic_market_history(
    *,
    days: int = 900,
    start: str = "2022-01-03",
    symbols: tuple[str, ...] | None = None,
    seed: int = 0,
) -> pd.DataFrame:
    dates = pd.bdate_range(start, periods=days)
    symbols = symbols if symbols is not None else tuple(extract_managed_symbols(universe_symbols=DEFAULT_UNIVERSE_SYMBOLS))
    rows: list[dict[str, object]] = []
    for symbol in symbols:
        price = 12.0 + 8.0 * _synthetic_path_parameter(seed=seed, symbol=symbol, label="initial_price")
        rate = 1.00015 + 0.0002 * _synthetic_path_parameter(seed=seed, symbol=symbol, label="growth_rate")
        cycle_amplitude = 0.01 + 0.02 * _synthetic_path_parameter(
            seed=seed, symbol=symbol, label="cycle_amplitude"
        )
        cycle_period = 8.0 + 8.0 * _synthetic_path_parameter(seed=seed, symbol=symbol, label="cycle_period")
        cycle_phase = 2.0 * math.pi * _synthetic_path_parameter(seed=seed, symbol=symbol, label="cycle_phase")
        for idx, day in enumerate(dates):
            price *= rate
            close = price * (1.0 + cycle_amplitude * math.sin((2.0 * math.pi * idx / cycle_period) + cycle_phase))
            rows.append({"date": day, "symbol": symbol, "close": close})
    history = pd.DataFrame(rows)
    history.attrs["synthetic_generator_version"] = SYNTHETIC_MARKET_HISTORY_GENERATOR_VERSION
    history.attrs["synthetic_seed"] = seed
    return history


def _slice_history(
    market_history: pd.DataFrame,
    *,
    start_date: date | None,
    end_date: date | None,
    lookback_days: int = 0,
) -> pd.DataFrame:
    frame = market_history.copy()
    frame["date"] = pd.to_datetime(frame["date"], utc=False).dt.tz_localize(None).dt.normalize()
    if start_date is not None:
        effective_start = pd.Timestamp(start_date) - pd.tseries.offsets.BDay(max(int(lookback_days), 0))
        frame = frame[frame["date"] >= effective_start]
    if end_date is not None:
        frame = frame[frame["date"] <= pd.Timestamp(end_date)]
    return frame.sort_values(["date", "symbol"]).reset_index(drop=True)


def _signal_fn(history: Any, **kwargs: Any):
    return build_target_weights(history, **kwargs)


def _params_with_data_provenance(params: Mapping[str, Any], market_history: pd.DataFrame) -> dict[str, Any]:
    output = dict(params)
    synthetic_seed = market_history.attrs.get("synthetic_seed")
    if (
        market_history.attrs.get("synthetic_generator_version") == SYNTHETIC_MARKET_HISTORY_GENERATOR_VERSION
        and isinstance(synthetic_seed, int)
    ):
        output["data_provenance"] = {
            "synthetic_data": True,
            "synthetic_generator_version": SYNTHETIC_MARKET_HISTORY_GENERATOR_VERSION,
            "synthetic_seed": synthetic_seed,
        }
    return output


def _metrics_to_backtest_result(
    *,
    strategy_profile: str,
    params: Mapping[str, Any],
    metrics: Mapping[str, Any],
    start_date: date | None,
    end_date: date | None,
    run_duration_seconds: float,
) -> Any:
    if BacktestResult is None:
        raise ImportError("quant_platform_kit is required to build BacktestResult")
    annual_return = float(metrics.get("annual_return") or 0.0)
    max_drawdown = float(metrics.get("max_drawdown") or 0.0)
    calmar = abs(annual_return / max_drawdown) if max_drawdown else None
    return BacktestResult(
        strategy_profile=strategy_profile,
        domain="hk_equity",
        param_set_id="",
        params=dict(params),
        sharpe_ratio=float(metrics.get("sharpe_ratio") or 0.0),
        calmar_ratio=calmar,
        max_drawdown=max_drawdown,
        cagr=annual_return,
        volatility=float(metrics.get("annual_volatility") or 0.0),
        total_return=float(metrics.get("total_return") or 0.0),
        start_date=start_date,
        end_date=end_date,
        observation_count=int(metrics.get("days") or 0),
        source_script="hk_equity_strategies.backtest.orchestrator_runner",
        computed_at=datetime.now(UTC).isoformat(),
        run_duration_seconds=run_duration_seconds,
    )


class HkEtfRotationBacktestRunner:
    """Protocol-compatible BacktestRunner for HK global ETF rotation."""

    def __init__(
        self,
        *,
        market_history: pd.DataFrame | None = None,
        synthetic_days: int = 700,
    ) -> None:
        self._market_history = market_history
        self._synthetic_days = int(synthetic_days)

    def run(
        self,
        strategy_profile: str,
        params: Mapping[str, Any],
        start_date: date | None = None,
        end_date: date | None = None,
    ) -> Any:
        if strategy_profile not in SUPPORTED_PROFILES:
            raise ValueError(
                f"Unsupported strategy_profile={strategy_profile!r}; "
                f"supported={sorted(SUPPORTED_PROFILES)}"
            )

        min_history_days = int(params.get("min_history_days", DEFAULT_MIN_HISTORY_DAYS))
        history = self._market_history
        if history is None:
            history = _synthetic_market_history(days=max(self._synthetic_days, min_history_days + 400))
        sliced = _slice_history(
            history,
            start_date=start_date,
            end_date=end_date,
            lookback_days=min_history_days + 5,
        )
        if sliced.empty:
            raise ValueError("No market history rows for requested window")

        started = datetime.now(UTC)
        result = run_etf_rotation_backtest(
            sliced,
            _signal_fn,
            config=HkRotationBacktestConfig(min_history_days=min_history_days),
            strategy_kwargs={"min_history_days": min_history_days},
        )
        elapsed = (datetime.now(UTC) - started).total_seconds()
        eval_frame = sliced
        if start_date is not None:
            eval_frame = sliced[sliced["date"] >= pd.Timestamp(start_date)]
        return _metrics_to_backtest_result(
            strategy_profile=strategy_profile,
            params=_params_with_data_provenance(params, history),
            metrics=result.metrics,
            start_date=start_date or (eval_frame["date"].min().date() if not eval_frame.empty else None),
            end_date=end_date or (eval_frame["date"].max().date() if not eval_frame.empty else None),
            run_duration_seconds=elapsed,
        )


class HkEquityComboBacktestRunner:
    """Protocol-compatible BacktestRunner for HK equity combo research."""

    def __init__(
        self,
        *,
        market_history: pd.DataFrame | None = None,
        synthetic_days: int = 700,
    ) -> None:
        self._market_history = market_history
        self._synthetic_days = int(synthetic_days)

    def run(
        self,
        strategy_profile: str,
        params: Mapping[str, Any],
        start_date: date | None = None,
        end_date: date | None = None,
    ) -> Any:
        if strategy_profile != HK_EQUITY_COMBO_PROFILE:
            raise ValueError(
                f"Unsupported strategy_profile={strategy_profile!r}; "
                f"supported={HK_EQUITY_COMBO_PROFILE!r}"
            )

        min_history_days = int(params.get("min_history_days", DEFAULT_MIN_HISTORY_DAYS))
        combo_mode = str(params.get("combo_mode", "dynamic"))
        if combo_mode not in {"static", "dynamic"}:
            raise ValueError("combo_mode must be 'static' or 'dynamic'")

        history = self._market_history
        if history is None:
            history = _synthetic_market_history(days=max(self._synthetic_days, min_history_days + 400))
        sliced = _slice_history(
            history,
            start_date=start_date,
            end_date=end_date,
            lookback_days=min_history_days + 5,
        )
        if sliced.empty:
            raise ValueError("No market history rows for requested window")

        started = datetime.now(UTC)
        result = run_combo_backtest(
            sliced,
            _signal_fn,
            combo_config=HkComboBacktestConfig(
                combo_mode=cast(ComboMode, combo_mode),
                min_history_days=min_history_days,
            ),
            rotation_config=HkRotationBacktestConfig(min_history_days=min_history_days),
            strategy_kwargs={"min_history_days": min_history_days},
        )
        elapsed = (datetime.now(UTC) - started).total_seconds()
        eval_frame = sliced
        if start_date is not None:
            eval_frame = sliced[sliced["date"] >= pd.Timestamp(start_date)]
        return _metrics_to_backtest_result(
            strategy_profile=strategy_profile,
            params=_params_with_data_provenance(params, history),
            metrics=result.metrics,
            start_date=start_date or (eval_frame["date"].min().date() if not eval_frame.empty else None),
            end_date=end_date or (eval_frame["date"].max().date() if not eval_frame.empty else None),
            run_duration_seconds=elapsed,
        )


def build_backtest_runner(
    strategy_profile: str,
    *,
    market_history: pd.DataFrame | None = None,
    synthetic_days: int = 700,
) -> HkEtfRotationBacktestRunner | HkEquityComboBacktestRunner:
    if strategy_profile == HK_EQUITY_COMBO_PROFILE:
        return HkEquityComboBacktestRunner(
            market_history=market_history,
            synthetic_days=synthetic_days,
        )
    return HkEtfRotationBacktestRunner(
        market_history=market_history,
        synthetic_days=synthetic_days,
    )


__all__ = [
    "SUPPORTED_PROFILES",
    "SYNTHETIC_MARKET_HISTORY_GENERATOR_VERSION",
    "HkEquityComboBacktestRunner",
    "HkEtfRotationBacktestRunner",
    "build_backtest_runner",
]
