from __future__ import annotations

from typing import Any

from hk_equity_strategies.strategies import etf_rotation_core as base

HK_EQUITY_DOMAIN = base.HK_EQUITY_DOMAIN
SIGNAL_SOURCE = base.SIGNAL_SOURCE
STATUS_ICON = base.STATUS_ICON
PROFILE_NAME = "hk_global_etf_tactical_rotation"

HSI_ETF_SYMBOL = base.HSI_ETF_SYMBOL
A50_ETF_SYMBOL = base.A50_ETF_SYMBOL
CSI300_ETF_SYMBOL = base.CSI300_ETF_SYMBOL
HSTECH_ETF_SYMBOL = base.HSTECH_ETF_SYMBOL
NASDAQ100_ETF_SYMBOL = "02834"
GOLD_ETF_SYMBOL = base.GOLD_ETF_SYMBOL
CRUDE_OIL_ETF_SYMBOL = "03175"
HIGH_DIVIDEND_ETF_SYMBOL = base.HIGH_DIVIDEND_ETF_SYMBOL

DEFAULT_UNIVERSE_SYMBOLS = (
    HSI_ETF_SYMBOL,
    A50_ETF_SYMBOL,
    CSI300_ETF_SYMBOL,
    HSTECH_ETF_SYMBOL,
    NASDAQ100_ETF_SYMBOL,
    GOLD_ETF_SYMBOL,
    CRUDE_OIL_ETF_SYMBOL,
    HIGH_DIVIDEND_ETF_SYMBOL,
)
DEFAULT_MOMENTUM_WINDOW_DAYS = 252
DEFAULT_TREND_WINDOW_DAYS = 200
DEFAULT_VOLATILITY_WINDOW_DAYS = 63
DEFAULT_TOP_N = 2
DEFAULT_MIN_MOMENTUM = 0.0
DEFAULT_REBALANCE_FREQUENCY = "monthly"
DEFAULT_WEIGHTING_MODE = "inverse_volatility"
DEFAULT_TARGET_ANNUAL_VOLATILITY = 0.16
DEFAULT_MAX_GROSS_EXPOSURE = 1.0
DEFAULT_MIN_HISTORY_DAYS = 260
DEFAULT_EXECUTION_CASH_RESERVE_RATIO = 0.02

normalize_symbol = base.normalize_symbol
normalize_universe_symbols = base.normalize_universe_symbols
build_close_matrix = base.build_close_matrix
apply_portfolio_volatility_target = base.apply_portfolio_volatility_target


def compute_latest_signal(market_history: Any, **kwargs: Any) -> dict[str, object]:
    kwargs.setdefault("universe_symbols", DEFAULT_UNIVERSE_SYMBOLS)
    kwargs.setdefault("momentum_window_days", DEFAULT_MOMENTUM_WINDOW_DAYS)
    kwargs.setdefault("trend_window_days", DEFAULT_TREND_WINDOW_DAYS)
    kwargs.setdefault("volatility_window_days", DEFAULT_VOLATILITY_WINDOW_DAYS)
    kwargs.setdefault("top_n", DEFAULT_TOP_N)
    kwargs.setdefault("min_momentum", DEFAULT_MIN_MOMENTUM)
    kwargs.setdefault("weighting_mode", DEFAULT_WEIGHTING_MODE)
    kwargs.setdefault("target_annual_volatility", DEFAULT_TARGET_ANNUAL_VOLATILITY)
    kwargs.setdefault("max_gross_exposure", DEFAULT_MAX_GROSS_EXPOSURE)
    kwargs.setdefault("min_history_days", DEFAULT_MIN_HISTORY_DAYS)
    return base.compute_latest_signal(market_history, **kwargs)


def build_target_weights(market_history: Any, **kwargs: Any) -> tuple[dict[str, float], dict[str, object]]:
    signal = compute_latest_signal(market_history, **kwargs)
    return dict(signal["weights"]), signal


def extract_managed_symbols(*_args: Any, **kwargs: Any) -> tuple[str, ...]:
    return base.normalize_universe_symbols(kwargs.get("universe_symbols") or DEFAULT_UNIVERSE_SYMBOLS)


def compute_signals(market_history: Any, _current_holdings: Any = None, **kwargs: Any):
    kwargs.pop("translator", None)
    kwargs.pop("signal_text_fn", None)
    kwargs.pop("execution_cash_reserve_ratio", None)
    kwargs.pop("rebalance_frequency", None)
    weights, metadata = build_target_weights(market_history, **kwargs)
    selected = ",".join(weights) if weights else "cash"
    target_vol = metadata.get("target_annual_volatility")
    target_vol_text = "none" if target_vol is None else f"{float(target_vol):.0%}"
    signal_desc = (
        f"hk listed global etf rotation state={metadata['signal_state']} selected={selected} "
        f"gross={metadata['gross_exposure']:.0%} cash={metadata['cash_weight']:.0%} target_vol={target_vol_text}"
    )
    status_desc = (
        f"state={metadata['signal_state']} | selected={selected} | "
        f"momentum={metadata['momentum_window_days']}d | trend={metadata['trend_window_days']}d | "
        f"target_vol={target_vol_text}"
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
