from __future__ import annotations

import math
from collections.abc import Mapping, Sequence
from typing import Any

import pandas as pd

HK_EQUITY_DOMAIN = "hk_equity"
SIGNAL_SOURCE = "daily_market_history"
STATUS_ICON = "🇭🇰"
PROFILE_NAME = "etf_rotation_core"

HSI_ETF_SYMBOL = "02800"
A50_ETF_SYMBOL = "02822"
HSTECH_ETF_SYMBOL = "03033"
CSI300_ETF_SYMBOL = "03188"
GOLD_ETF_SYMBOL = "02840"
HIGH_DIVIDEND_ETF_SYMBOL = "03110"

DEFAULT_UNIVERSE_SYMBOLS = (
    HSI_ETF_SYMBOL,
    A50_ETF_SYMBOL,
    GOLD_ETF_SYMBOL,
    HSTECH_ETF_SYMBOL,
    HIGH_DIVIDEND_ETF_SYMBOL,
    CSI300_ETF_SYMBOL,
)
DEFAULT_MOMENTUM_WINDOW_DAYS = 252
DEFAULT_TREND_WINDOW_DAYS = 200
DEFAULT_VOLATILITY_WINDOW_DAYS = 63
DEFAULT_TOP_N = 2
DEFAULT_MIN_MOMENTUM = 0.0
DEFAULT_REBALANCE_FREQUENCY = "monthly"
DEFAULT_WEIGHTING_MODE = "inverse_volatility"
DEFAULT_TARGET_ANNUAL_VOLATILITY: float | None = None
DEFAULT_MAX_GROSS_EXPOSURE = 1.0
DEFAULT_MIN_HISTORY_DAYS = 260
DEFAULT_EXECUTION_CASH_RESERVE_RATIO = 0.02

REQUIRED_MARKET_HISTORY_COLUMNS = frozenset({"date", "symbol", "close"})
OPTIONAL_MARKET_HISTORY_COLUMNS = frozenset({"open", "high", "low", "volume"})


def normalize_symbol(value: Any) -> str:
    text = str(value or "").strip().upper()
    if not text:
        return ""
    text = text.removesuffix(".HK")
    if text.isdigit():
        return text.zfill(5)
    return text


def normalize_universe_symbols(symbols: Sequence[Any] | None = None) -> tuple[str, ...]:
    raw_symbols = symbols or DEFAULT_UNIVERSE_SYMBOLS
    normalized: list[str] = []
    for value in raw_symbols:
        symbol = normalize_symbol(value)
        if symbol and symbol not in normalized:
            normalized.append(symbol)
    if not normalized:
        raise ValueError("universe_symbols must contain at least one valid symbol")
    return tuple(normalized)


def _history_to_frame(market_history: Any) -> pd.DataFrame:
    if isinstance(market_history, pd.DataFrame):
        frame = market_history.copy()
    elif isinstance(market_history, Mapping):
        frame = _mapping_history_to_frame(market_history)
    else:
        frame = pd.DataFrame(list(market_history))
    if frame.empty:
        raise ValueError("market_history must contain at least one row")

    if "date" not in frame.columns and "symbol" not in frame.columns and "close" not in frame.columns:
        frame = frame.reset_index(names="date").melt(id_vars="date", var_name="symbol", value_name="close")

    missing = REQUIRED_MARKET_HISTORY_COLUMNS - set(frame.columns)
    if missing:
        missing_text = ", ".join(sorted(missing))
        raise ValueError(f"market_history missing required columns: {missing_text}")

    output_columns = ["date", "symbol", "close", *sorted(OPTIONAL_MARKET_HISTORY_COLUMNS)]
    frame = frame.loc[:, [column for column in output_columns if column in frame.columns]].copy()
    frame["date"] = pd.to_datetime(frame["date"], utc=False).dt.tz_localize(None).dt.normalize()
    frame["symbol"] = frame["symbol"].map(normalize_symbol)
    frame["close"] = pd.to_numeric(frame["close"], errors="coerce")
    frame = frame.dropna(subset=["date", "symbol", "close"])
    frame = frame.loc[frame["symbol"] != ""]
    if frame.empty:
        raise ValueError("market_history has no valid date/symbol/close rows")
    return frame.sort_values(["date", "symbol"]).reset_index(drop=True)


def _mapping_history_to_frame(market_history: Mapping[Any, Any]) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    for raw_symbol, raw_history in market_history.items():
        symbol = normalize_symbol(raw_symbol)
        if isinstance(raw_history, pd.DataFrame):
            item_frame = raw_history.copy()
            if "date" not in item_frame.columns:
                item_frame = item_frame.reset_index(names="date")
            close_column = (
                "close"
                if "close" in item_frame.columns
                else "Close" if "Close" in item_frame.columns else None
            )
            if close_column is None:
                raise ValueError(f"market_history[{raw_symbol!r}] missing close column")
            for row in item_frame.itertuples(index=False):
                rows.append(
                    {"date": getattr(row, "date"), "symbol": symbol, "close": getattr(row, close_column)}
                )
            continue
        for item in raw_history:
            if isinstance(item, Mapping):
                date_value = item.get("date") or item.get("as_of") or item.get("timestamp")
                close_value = item.get("close") or item.get("Close")
            else:
                date_value = (
                    getattr(item, "date", None)
                    or getattr(item, "as_of", None)
                    or getattr(item, "timestamp", None)
                )
                close_value = getattr(item, "close", None) or getattr(item, "Close", None)
            rows.append({"date": date_value, "symbol": symbol, "close": close_value})
    return pd.DataFrame(rows)


def build_close_matrix(
    market_history: Any,
    *,
    universe_symbols: Sequence[Any] | None = None,
) -> pd.DataFrame:
    frame = _history_to_frame(market_history)
    symbols = normalize_universe_symbols(universe_symbols)
    close = (
        frame.loc[frame["symbol"].isin(symbols)]
        .pivot_table(index="date", columns="symbol", values="close", aggfunc="last")
        .sort_index()
    )
    missing = set(symbols) - set(close.columns)
    if missing:
        missing_text = ", ".join(sorted(missing))
        raise ValueError(f"market_history missing required strategy symbols: {missing_text}")
    close = close.loc[:, list(symbols)].ffill().dropna(how="any")
    close = close.loc[(close > 0).all(axis=1)]
    if close.empty:
        raise ValueError("market_history has no overlapping close history for the ETF universe")
    return close


def _finite_float(value: Any, *, default: float = float("nan")) -> float:
    try:
        output = float(value)
    except (TypeError, ValueError):
        return default
    return output if math.isfinite(output) else default


def compute_latest_signal(
    market_history: Any,
    *,
    universe_symbols: Sequence[Any] | None = None,
    momentum_window_days: int = DEFAULT_MOMENTUM_WINDOW_DAYS,
    trend_window_days: int = DEFAULT_TREND_WINDOW_DAYS,
    volatility_window_days: int = DEFAULT_VOLATILITY_WINDOW_DAYS,
    top_n: int = DEFAULT_TOP_N,
    min_momentum: float = DEFAULT_MIN_MOMENTUM,
    weighting_mode: str = DEFAULT_WEIGHTING_MODE,
    target_annual_volatility: float | None = DEFAULT_TARGET_ANNUAL_VOLATILITY,
    max_gross_exposure: float = DEFAULT_MAX_GROSS_EXPOSURE,
    min_history_days: int = DEFAULT_MIN_HISTORY_DAYS,
) -> dict[str, object]:
    if momentum_window_days <= 1:
        raise ValueError("momentum_window_days must be greater than 1")
    if trend_window_days <= 1:
        raise ValueError("trend_window_days must be greater than 1")
    if volatility_window_days <= 1:
        raise ValueError("volatility_window_days must be greater than 1")
    if top_n < 1:
        raise ValueError("top_n must be at least 1")
    if min_history_days <= max(momentum_window_days, trend_window_days, volatility_window_days):
        raise ValueError("min_history_days must be greater than all lookback windows")
    if target_annual_volatility is not None and float(target_annual_volatility) <= 0.0:
        raise ValueError("target_annual_volatility must be positive when set")
    if float(max_gross_exposure) <= 0.0:
        raise ValueError("max_gross_exposure must be positive")

    symbols = normalize_universe_symbols(universe_symbols)
    close = build_close_matrix(market_history, universe_symbols=symbols)
    if len(close) < int(min_history_days):
        raise ValueError(f"market_history requires at least {int(min_history_days)} overlapping trading days")

    returns = close.pct_change().fillna(0.0)
    momentum = close.pct_change(int(momentum_window_days))
    trend = close / close.rolling(int(trend_window_days)).mean() - 1.0
    volatility = returns.rolling(int(volatility_window_days)).std(ddof=0) * math.sqrt(252)
    score = momentum / volatility.replace(0.0, pd.NA)

    as_of = pd.Timestamp(close.index[-1]).date().isoformat()
    latest_rows: list[dict[str, object]] = []
    for symbol in symbols:
        symbol_momentum = _finite_float(momentum[symbol].iloc[-1])
        symbol_trend = _finite_float(trend[symbol].iloc[-1])
        symbol_volatility = _finite_float(volatility[symbol].iloc[-1])
        symbol_score = _finite_float(score[symbol].iloc[-1], default=float("-inf"))
        eligible = (
            math.isfinite(symbol_momentum)
            and math.isfinite(symbol_trend)
            and math.isfinite(symbol_volatility)
            and symbol_momentum > float(min_momentum)
            and symbol_trend > 0.0
            and symbol_volatility > 0.0
        )
        latest_rows.append(
            {
                "symbol": symbol,
                "momentum": symbol_momentum,
                "trend": symbol_trend,
                "volatility": symbol_volatility,
                "score": symbol_score,
                "eligible": eligible,
            }
        )

    ranked = sorted(
        (row for row in latest_rows if row["eligible"]),
        key=lambda row: float(row["score"]),
        reverse=True,
    )[: min(int(top_n), len(symbols))]

    weights: dict[str, float] = {}
    normalized_weighting_mode = str(weighting_mode or "").strip().lower().replace("-", "_")
    if ranked:
        if normalized_weighting_mode in {"inverse_volatility", "inverse_vol"}:
            inverse_vols = [1.0 / max(float(row["volatility"]), 1e-12) for row in ranked]
            total_inverse_vol = sum(inverse_vols)
            weights = {
                str(row["symbol"]): float(inverse_vol / total_inverse_vol)
                for row, inverse_vol in zip(ranked, inverse_vols)
            }
        elif normalized_weighting_mode == "equal":
            weights = {str(row["symbol"]): 1.0 / len(ranked) for row in ranked}
        else:
            raise ValueError("weighting_mode must be 'inverse_volatility' or 'equal'")

    realized_portfolio_volatility = 0.0
    if weights:
        weights, realized_portfolio_volatility = apply_portfolio_volatility_target(
            returns,
            weights,
            volatility_window_days=int(volatility_window_days),
            target_annual_volatility=target_annual_volatility,
            max_gross_exposure=float(max_gross_exposure),
        )

    cash_weight = max(0.0, 1.0 - sum(weights.values()))
    signal_state = "risk_on" if weights else "cash"
    return {
        "as_of": as_of,
        "universe_symbols": symbols,
        "selected_symbols": tuple(weights),
        "ranking": tuple(latest_rows),
        "signal_state": signal_state,
        "cash_weight": cash_weight,
        "gross_exposure": sum(weights.values()),
        "history_days": int(len(close)),
        "momentum_window_days": int(momentum_window_days),
        "trend_window_days": int(trend_window_days),
        "volatility_window_days": int(volatility_window_days),
        "top_n": int(top_n),
        "min_momentum": float(min_momentum),
        "weighting_mode": normalized_weighting_mode,
        "target_annual_volatility": (
            None if target_annual_volatility is None else float(target_annual_volatility)
        ),
        "max_gross_exposure": float(max_gross_exposure),
        "realized_portfolio_volatility": float(realized_portfolio_volatility),
        "weights": weights,
    }




def apply_portfolio_volatility_target(
    returns: pd.DataFrame,
    weights: Mapping[str, float],
    *,
    volatility_window_days: int,
    target_annual_volatility: float | None,
    max_gross_exposure: float,
) -> tuple[dict[str, float], float]:
    if not weights:
        return {}, 0.0

    selected_symbols = [symbol for symbol in weights if symbol in returns.columns]
    if not selected_symbols:
        return dict(weights), 0.0

    covariance = returns.loc[:, selected_symbols].tail(int(volatility_window_days)).cov() * 252
    portfolio_variance = 0.0
    for left in selected_symbols:
        for right in selected_symbols:
            portfolio_variance += float(weights[left]) * float(weights[right]) * float(covariance.loc[left, right])
    realized_volatility = math.sqrt(max(portfolio_variance, 0.0))

    gross_exposure = sum(float(value) for value in weights.values())
    scale = min(1.0, float(max_gross_exposure) / max(gross_exposure, 1e-12))
    if target_annual_volatility is not None and realized_volatility > 0.0:
        scale = min(scale, float(target_annual_volatility) / realized_volatility)
    if scale >= 1.0:
        return dict(weights), realized_volatility
    return {symbol: float(value) * scale for symbol, value in weights.items()}, realized_volatility

def build_target_weights(market_history: Any, **kwargs: Any) -> tuple[dict[str, float], dict[str, object]]:
    signal = compute_latest_signal(market_history, **kwargs)
    return dict(signal["weights"]), signal


def extract_managed_symbols(*_args: Any, **kwargs: Any) -> tuple[str, ...]:
    return normalize_universe_symbols(kwargs.get("universe_symbols"))


def compute_signals(market_history: Any, _current_holdings: Any = None, **kwargs: Any):
    kwargs.pop("translator", None)
    kwargs.pop("signal_text_fn", None)
    kwargs.pop("execution_cash_reserve_ratio", None)
    kwargs.pop("rebalance_frequency", None)
    weights, metadata = build_target_weights(market_history, **kwargs)
    selected = ",".join(weights) if weights else "cash"
    signal_desc = (
        f"hk etf regime rotation state={metadata['signal_state']} selected={selected} "
        f"gross={metadata['gross_exposure']:.0%} cash={metadata['cash_weight']:.0%}"
    )
    status_desc = (
        f"state={metadata['signal_state']} | selected={selected} | "
        f"momentum={metadata['momentum_window_days']}d | trend={metadata['trend_window_days']}d"
    )
    return (
        weights,
        signal_desc,
        bool(metadata["cash_weight"] > 1e-12),
        status_desc,
        {
            **metadata,
            "managed_symbols": extract_managed_symbols(**kwargs),
            "status_icon": STATUS_ICON,
            "signal_source": SIGNAL_SOURCE,
            "actionable": True,
        },
    )
