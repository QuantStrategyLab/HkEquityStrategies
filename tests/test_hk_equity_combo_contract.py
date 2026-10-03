from __future__ import annotations

import pytest

from hk_equity_strategies.catalog import (
    HK_EQUITY_COMBO_PROFILE,
    STRATEGY_DEFAULT_CONFIG,
)
from hk_equity_strategies.combo_entrypoints import evaluate_hk_equity_combo
from hk_equity_strategies.strategies import hk_equity_combo as combo
from quant_platform_kit.common.strategy_contracts import StrategyContext


@pytest.fixture
def fixed_sublegs(monkeypatch):
    etf_weights = {"SHARED": 0.5, "ETF_ONLY": 0.3}
    dividend_weights = {"SHARED": 0.2, "DIV_ONLY": 0.5}
    monkeypatch.setattr(
        combo._etf,
        "build_target_weights",
        lambda _history, **_kwargs: (etf_weights, {"cash_weight": 0.2}),
    )
    monkeypatch.setattr(
        combo._dividend,
        "build_target_weights",
        lambda _snapshot, **_kwargs: (dividend_weights, None, {"cash_weight": 0.3}),
    )
    return etf_weights, dividend_weights


def _build(config=None):
    return combo.build_target_weights("history", "snapshot", config=config)


def test_legacy_dividend_weight_is_ignored_and_reported_as_deprecated(fixed_sublegs):
    weights, metadata = _build({"etf_weight": 0.60, "dividend_weight": 0.20})

    assert metadata["etf_weight"] == pytest.approx(0.60)
    assert metadata["dividend_weight"] == pytest.approx(0.40)
    assert metadata["raw_dividend_weight"] == pytest.approx(0.20)
    assert metadata["raw_dividend_weight_status"] == "deprecated_ignored"
    assert weights["ETF_ONLY"] == pytest.approx(0.18)
    assert weights["DIV_ONLY"] == pytest.approx(0.20)


def test_default_uses_only_etf_weight_and_catalog_has_no_dividend_default(fixed_sublegs):
    weights, metadata = _build()

    assert STRATEGY_DEFAULT_CONFIG[HK_EQUITY_COMBO_PROFILE]["etf_weight"] == pytest.approx(0.60)
    assert "dividend_weight" not in STRATEGY_DEFAULT_CONFIG[HK_EQUITY_COMBO_PROFILE]
    assert metadata["raw_dividend_weight"] is None
    assert metadata["raw_dividend_weight_status"] == "deprecated_ignored"
    assert metadata["dividend_weight"] == pytest.approx(0.40)
    assert weights["ETF_ONLY"] == pytest.approx(0.18)
    assert weights["DIV_ONLY"] == pytest.approx(0.20)


@pytest.mark.parametrize(
    ("regime", "expected_etf", "expected_dividend"),
    (
        ("risk_on", 0.60, 0.40),
        ("soft_defense", 0.51, 0.49),
        ("hard_defense", 0.30, 0.70),
    ),
)
def test_regime_complement_preserves_component_cash_and_combines_overlap(
    fixed_sublegs, regime, expected_etf, expected_dividend
):
    etf_weights, dividend_weights = fixed_sublegs
    weights, metadata = _build(
        {"etf_weight": 0.60, "dividend_weight": 0.20, "dividend_regime": regime}
    )

    assert metadata["etf_weight"] == pytest.approx(expected_etf)
    assert metadata["dividend_weight"] == pytest.approx(expected_dividend)
    assert sum(etf_weights.values()) == pytest.approx(0.80)
    assert sum(dividend_weights.values()) == pytest.approx(0.70)
    assert weights["ETF_ONLY"] == pytest.approx(0.30 * expected_etf)
    assert weights["DIV_ONLY"] == pytest.approx(0.50 * expected_dividend)
    assert weights["SHARED"] == pytest.approx(
        0.50 * expected_etf + 0.20 * expected_dividend
    )
    assert sum(weights.values()) == pytest.approx(0.80 * expected_etf + 0.70 * expected_dividend)
    assert sum(weights.values()) < 1.0


@pytest.mark.parametrize(
    ("runtime_config", "expected_description"),
    (
        (
            {"etf_weight": 0.60, "dividend_weight": 0.20},
            "etf=60% div=40%",
        ),
        (
            {"etf_weight": 0.60, "dividend_weight": 0.20, "dividend_regime": "soft_defense"},
            "etf=51% div=49%",
        ),
    ),
)
def test_entrypoint_describes_effective_weights_not_legacy_request(
    fixed_sublegs, runtime_config, expected_description
):
    decision = evaluate_hk_equity_combo(
        StrategyContext(
            as_of="2026-10-03",
            market_data={"market_history": "history", "dividend_snapshot": "snapshot"},
            runtime_config=runtime_config,
        )
    )

    assert decision.diagnostics["raw_dividend_weight"] == pytest.approx(0.20)
    assert decision.diagnostics["raw_dividend_weight_status"] == "deprecated_ignored"
    assert decision.diagnostics["signal_description"] == expected_description
    assert decision.diagnostics["status_description"] == expected_description
