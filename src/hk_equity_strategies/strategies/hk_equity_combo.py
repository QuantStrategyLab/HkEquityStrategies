"""HK equity combo strategy — 60/40 blend of ETF momentum and dividend-quality."""

from __future__ import annotations

from typing import Any

from quant_platform_kit.common.strategies import compute_portfolio_drift

# HK sub-strategies
from hk_equity_strategies.strategies import (
    hk_global_etf_tactical_rotation as _etf,
    hk_low_vol_dividend_quality_snapshot as _dividend,
)

PROFILE_NAME = "hk_equity_combo"
SIGNAL_SOURCE = "combo"
STATUS_ICON = "\U0001f1ed\U0001f1f0"  # Hong Kong flag

DEFAULT_ETF_WEIGHT = 0.60
DEFAULT_DIVIDEND_WEIGHT = 0.40
DEFAULT_REBALANCE_THRESHOLD = 0.05  # 5% drift triggers rebalance


def _apply_dividend_regime(
    etf_weight: float,
    dividend_regime: str | None,
) -> tuple[float, float, str | None]:
    """Apply a dividend-regime override to derive effective ETF / dividend weights.

    Parameters
    ----------
    etf_weight : float
        Configured ETF weight before regime adjustment.
    dividend_regime : str | None
        Regime indicator from runtime config.  ``None`` or ``"risk_on"`` leaves
        weights unchanged.

    Returns
    -------
    tuple[float, float, str | None]
        ``(effective_etf_weight, effective_dividend_weight, label)`` where *label*
        is a human-readable regime name (or ``None`` when no adjustment applies).
    """
    if dividend_regime is None or str(dividend_regime).strip().lower() == "risk_on":
        return etf_weight, 1.0 - etf_weight, None

    regime = str(dividend_regime).strip().lower()

    if regime == "soft_defense":
        effective_etf = min(etf_weight * 0.85, 1.0)
    elif regime == "hard_defense":
        effective_etf = min(etf_weight * 0.50, 1.0)
    else:
        return etf_weight, 1.0 - etf_weight, None

    return effective_etf, 1.0 - effective_etf, regime


def build_target_weights(
    market_history: Any,
    dividend_snapshot: Any,
    config: dict[str, Any] | None = None,
    **kwargs: Any,
) -> tuple[dict[str, float], dict[str, Any]]:
    """Build a blended target-weight map by combining ETF momentum and dividend-
    quality sub-strategies at the configured ratio.

    Parameters
    ----------
    market_history : Any
        Market price / volume data passed through to the ETF momentum sub-strategy.
    dividend_snapshot : Any
        Factor snapshot passed through to the dividend-quality sub-strategy.
    config : dict[str, Any] | None
        Optional override dictionary.  Recognised keys:

        * ``etf_weight`` / ``dividend_weight`` (float, default 0.60 / 0.40)
        * ``dividend_regime`` (str | None) — dynamic regime override
          (``"risk_on"``, ``"soft_defense"``, or ``"hard_defense"``).
          When set, the ETF weight is scaled down: ``risk_on`` = normal (no
          change), ``soft_defense`` = ETF * 0.85, ``hard_defense`` = ETF * 0.50.
          The freed allocation shifts to the dividend leg.
        * ``etf_kwargs`` — forwarded to the ETF sub-strategy
        * ``dividend_kwargs`` — forwarded to the dividend sub-strategy

    **kwargs
        Additional keyword arguments forwarded to both sub-strategies.

    Returns
    -------
    tuple[dict[str, float], dict[str, object]]
        (combined_weight_map, metadata_dict).
    """
    if config is None:
        config = {}

    raw_etf_weight = config.get("etf_weight", DEFAULT_ETF_WEIGHT)
    raw_dividend_weight = config.get("dividend_weight", DEFAULT_DIVIDEND_WEIGHT)

    etf_weight, dividend_weight, regime_label = _apply_dividend_regime(
        raw_etf_weight,
        config.get("dividend_regime"),
    )

    etf_kwargs: dict[str, Any] = {**kwargs, **config.get("etf_kwargs", {})}
    dividend_kwargs: dict[str, Any] = {**kwargs, **config.get("dividend_kwargs", {})}

    etf_weights, etf_meta = _etf.build_target_weights(market_history, **etf_kwargs)
    div_weights, div_df, div_meta = _dividend.build_target_weights(
        dividend_snapshot, **dividend_kwargs
    )

    combined: dict[str, float] = {}
    for sym, w in etf_weights.items():
        combined[sym] = combined.get(sym, 0.0) + w * etf_weight
    for sym, w in div_weights.items():
        combined[sym] = combined.get(sym, 0.0) + w * dividend_weight

    metadata: dict[str, Any] = {
        "etf_meta": etf_meta,
        "dividend_meta": div_meta,
        "etf_weight": etf_weight,
        "dividend_weight": dividend_weight,
        "raw_etf_weight": raw_etf_weight,
        "raw_dividend_weight": raw_dividend_weight,
        "dividend_regime": regime_label,
        "profile": PROFILE_NAME,
        "rebalance": compute_portfolio_drift(
            combined,
            holdings=config.get("current_holdings_quantities", {}),
            prices=config.get("current_prices", {}),
            threshold=float(config.get("rebalance_threshold", DEFAULT_REBALANCE_THRESHOLD)),
        ),
    }

    return combined, metadata


# _check_drift removed — use quant_platform_kit.common.strategies.compute_portfolio_drift


def compute_signals(
    market_history: Any,
    dividend_snapshot: Any,
    config: dict[str, Any] | None = None,
    **kwargs: Any,
) -> Any:
    """Compute combined signals from both sub-strategies and produce a unified
    signal frame / dict.

    Parameters
    ----------
    market_history : Any
        Market data forwarded to the ETF momentum sub-strategy.
    dividend_snapshot : Any
        Factor snapshot forwarded to the dividend-quality sub-strategy.
    config : dict[str, Any] | None
        Optional override dictionary (same layout as
        :func:`build_target_weights`).
    **kwargs
        Additional keyword arguments forwarded to both sub-strategies.

    Returns
    -------
    Any
        Combines the sub-strategies' signal data into a single result.
    """
    if config is None:
        config = {}

    etf_kwargs: dict[str, Any] = {**kwargs, **config.get("etf_kwargs", {})}
    dividend_kwargs: dict[str, Any] = {**kwargs, **config.get("dividend_kwargs", {})}

    etf_signals = _etf.compute_signals(market_history, **etf_kwargs)
    div_signals = _dividend.compute_signals(
        dividend_snapshot, current_holdings=None, **dividend_kwargs
    )

    return {"etf": etf_signals, "dividend": div_signals, "profile": PROFILE_NAME}


def extract_managed_symbols(
    market_history: Any,
    dividend_snapshot: Any,
    **kwargs: Any,
) -> tuple[str, ...]:
    """Return the union of symbols managed by both sub-strategies.

    Parameters
    ----------
    market_history : Any
        Market data forwarded to the ETF sub-strategy.
    dividend_snapshot : Any
        Factor snapshot forwarded to the dividend sub-strategy.
    **kwargs
        Additional keyword arguments forwarded to both sub-strategies.

    Returns
    -------
    tuple[str, ...]
        Deduplicated tuple of managed ticker symbols.
    """
    etf_symbols = set(_etf.extract_managed_symbols(**kwargs))
    div_symbols = set(_dividend.extract_managed_symbols(dividend_snapshot, **kwargs))
    return tuple(sorted(etf_symbols | div_symbols))
