from __future__ import annotations

import hashlib
import os
import subprocess
import sys
import tempfile
import unittest
from datetime import date
from pathlib import Path

import pandas as pd

from hk_equity_strategies.backtest.orchestrator_runner import (
    SUPPORTED_PROFILES,
    SYNTHETIC_MARKET_HISTORY_GENERATOR_VERSION,
    HkEquityComboBacktestRunner,
    HkEtfRotationBacktestRunner,
    _synthetic_market_history,
    _synthetic_path_parameter,
    build_backtest_runner,
)
from hk_equity_strategies.strategies.hk_equity_combo import PROFILE_NAME as HK_EQUITY_COMBO_PROFILE
from hk_equity_strategies.strategies.hk_global_etf_tactical_rotation import (
    DEFAULT_MIN_HISTORY_DAYS,
    PROFILE_NAME,
)


def _synthetic_history_digest(history: pd.DataFrame) -> str:
    return hashlib.sha256(pd.util.hash_pandas_object(history, index=True).values.tobytes()).hexdigest()


def _symbol_path(history: pd.DataFrame, symbol: str) -> pd.DataFrame:
    return history.loc[history["symbol"] == symbol].sort_values("date").reset_index(drop=True)


def test_synthetic_history_digest_is_stable_across_hash_seeds() -> None:
    root = Path(__file__).resolve().parents[1]
    code = (
        f"import hashlib, sys; sys.path.insert(0, {str(root / 'src')!r}); "
        "from hk_equity_strategies.backtest.orchestrator_runner import _synthetic_market_history; "
        "import pandas as pd; "
        "print(hashlib.sha256(pd.util.hash_pandas_object(_synthetic_market_history(days=8, symbols=('B', 'C'), seed=4), "
        "index=True).values.tobytes()).hexdigest())"
    )

    def digest(hash_seed: int) -> str:
        env = {**os.environ, "PYTHONHASHSEED": str(hash_seed)}
        return subprocess.check_output([sys.executable, "-c", code], env=env, text=True).strip()

    assert digest(1) == digest(2)
    assert digest(1) == digest(1)


def test_synthetic_history_symbol_paths_are_order_independent() -> None:
    ordered = _synthetic_market_history(days=8, symbols=("A", "B"), seed=4)
    reordered = _synthetic_market_history(days=8, symbols=("B", "A"), seed=4)

    assert ordered["symbol"].tolist() != reordered["symbol"].tolist()
    for symbol in ("A", "B"):
        pd.testing.assert_frame_equal(_symbol_path(ordered, symbol), _symbol_path(reordered, symbol))


def test_synthetic_history_symbol_and_seed_changes_change_fixed_counterexample_paths() -> None:
    base = _synthetic_market_history(days=8, symbols=("B",), seed=4)
    changed_symbol = _synthetic_market_history(days=8, symbols=("C",), seed=4)
    changed_seed = _synthetic_market_history(days=8, symbols=("B",), seed=5)

    assert not _symbol_path(base, "B")["close"].equals(_symbol_path(changed_symbol, "C")["close"])
    assert not _symbol_path(base, "B")["close"].equals(_symbol_path(changed_seed, "B")["close"])


def test_synthetic_path_parameters_are_high_precision_for_fixed_collision_counterexamples() -> None:
    values = {
        (seed, symbol, label): _synthetic_path_parameter(seed=seed, symbol=symbol, label=label)
        for seed in (4, 5)
        for symbol in ("B", "C")
        for label in ("initial_price", "growth_rate", "cycle_amplitude", "cycle_period", "cycle_phase")
    }

    assert all(0.0 <= value < 1.0 for value in values.values())
    assert len(set(values.values())) == len(values)


class HkEtfRotationBacktestRunnerTests(unittest.TestCase):
    def test_supported_profile_includes_global_etf(self) -> None:
        self.assertIn(PROFILE_NAME, SUPPORTED_PROFILES)

    def test_supported_profile_includes_equity_combo(self) -> None:
        self.assertIn(HK_EQUITY_COMBO_PROFILE, SUPPORTED_PROFILES)

    def test_build_backtest_runner_dispatches_combo(self) -> None:
        runner = build_backtest_runner(HK_EQUITY_COMBO_PROFILE, synthetic_days=500)
        self.assertIsInstance(runner, HkEquityComboBacktestRunner)

    def test_run_returns_backtest_result(self) -> None:
        runner = HkEtfRotationBacktestRunner(synthetic_days=500)
        result = runner.run(
            PROFILE_NAME,
            {"min_history_days": DEFAULT_MIN_HISTORY_DAYS},
            start_date=date(2023, 6, 1),
            end_date=date(2024, 6, 1),
        )
        self.assertEqual(result.strategy_profile, PROFILE_NAME)
        self.assertEqual(result.domain, "hk_equity")
        self.assertIsNotNone(result.sharpe_ratio)
        self.assertGreater(result.observation_count, 0)

    def test_synthetic_result_has_controlled_data_provenance(self) -> None:
        result = HkEtfRotationBacktestRunner(synthetic_days=500).run(
            PROFILE_NAME,
            {
                "min_history_days": DEFAULT_MIN_HISTORY_DAYS,
                "data_provenance": {"synthetic_data": False, "synthetic_seed": 999},
            },
            start_date=date(2023, 6, 1),
            end_date=date(2024, 6, 1),
        )

        self.assertEqual(
            result.params["data_provenance"],
            {
                "synthetic_data": True,
                "synthetic_generator_version": SYNTHETIC_MARKET_HISTORY_GENERATOR_VERSION,
                "synthetic_seed": 0,
            },
        )

    def test_external_history_cannot_claim_synthetic_data_provenance(self) -> None:
        history = _synthetic_market_history(days=500)
        result = HkEtfRotationBacktestRunner(market_history=history).run(
            PROFILE_NAME,
            {
                "min_history_days": DEFAULT_MIN_HISTORY_DAYS,
                "data_provenance": {"synthetic_data": True, "synthetic_seed": 999},
            },
            start_date=date(2023, 6, 1),
            end_date=date(2024, 6, 1),
        )

        self.assertNotIn("data_provenance", result.params)

    def test_unsupported_profile_raises(self) -> None:
        runner = HkEtfRotationBacktestRunner(synthetic_days=100)
        with self.assertRaises(ValueError):
            runner.run("unknown_profile", {})


class HkEquityComboBacktestRunnerTests(unittest.TestCase):
    def test_run_returns_backtest_result(self) -> None:
        runner = HkEquityComboBacktestRunner(synthetic_days=500)
        result = runner.run(
            HK_EQUITY_COMBO_PROFILE,
            {"min_history_days": DEFAULT_MIN_HISTORY_DAYS, "combo_mode": "dynamic"},
            start_date=date(2023, 6, 1),
            end_date=date(2024, 6, 1),
        )
        self.assertEqual(result.strategy_profile, HK_EQUITY_COMBO_PROFILE)
        self.assertEqual(result.domain, "hk_equity")
        self.assertGreater(result.observation_count, 0)
        self.assertEqual(
            result.params["data_provenance"],
            {
                "synthetic_data": True,
                "synthetic_generator_version": SYNTHETIC_MARKET_HISTORY_GENERATOR_VERSION,
                "synthetic_seed": 0,
            },
        )

    def test_external_history_cannot_claim_synthetic_data_provenance(self) -> None:
        history = _synthetic_market_history(days=500)
        result = HkEquityComboBacktestRunner(market_history=history).run(
            HK_EQUITY_COMBO_PROFILE,
            {
                "min_history_days": DEFAULT_MIN_HISTORY_DAYS,
                "combo_mode": "dynamic",
                "data_provenance": {"synthetic_data": True, "synthetic_seed": 999},
            },
            start_date=date(2023, 6, 1),
            end_date=date(2024, 6, 1),
        )

        self.assertNotIn("data_provenance", result.params)

    def test_walk_forward_combo_profile(self) -> None:
        from pathlib import Path

        from quant_platform_kit.strategy_lifecycle.backtest_orchestrator import BacktestOrchestrator
        from quant_platform_kit.strategy_lifecycle.performance_store import PerformanceStore

        with tempfile.TemporaryDirectory() as tmp:
            store = PerformanceStore(local_root=Path(tmp))
            orchestrator = BacktestOrchestrator(store=store)
            orchestrator.register_runner(
                "hk_equity",
                HkEquityComboBacktestRunner(synthetic_days=700),
            )
            windows = (
                (date(2023, 6, 1), date(2023, 12, 31)),
                (date(2024, 1, 1), date(2024, 6, 30)),
            )
            results = orchestrator.walk_forward(
                HK_EQUITY_COMBO_PROFILE,
                domain="hk_equity",
                params={"min_history_days": DEFAULT_MIN_HISTORY_DAYS, "combo_mode": "dynamic"},
                windows=windows,
            )
            self.assertEqual(len(results), 2)
            self.assertTrue(all(item.strategy_profile == HK_EQUITY_COMBO_PROFILE for item in results))


class WalkForwardPilotTests(unittest.TestCase):
    def test_walk_forward_produces_one_result_per_window(self) -> None:
        from pathlib import Path

        from quant_platform_kit.strategy_lifecycle.backtest_orchestrator import BacktestOrchestrator
        from quant_platform_kit.strategy_lifecycle.performance_store import PerformanceStore

        with tempfile.TemporaryDirectory() as tmp:
            store = PerformanceStore(local_root=Path(tmp))
            orchestrator = BacktestOrchestrator(store=store)
            orchestrator.register_runner("hk_equity", HkEtfRotationBacktestRunner(synthetic_days=700))
            windows = (
                (date(2023, 6, 1), date(2023, 12, 31)),
                (date(2024, 1, 1), date(2024, 6, 30)),
            )
            results = orchestrator.walk_forward(
                PROFILE_NAME,
                domain="hk_equity",
                params={"min_history_days": DEFAULT_MIN_HISTORY_DAYS},
                windows=windows,
            )
            self.assertEqual(len(results), 2)
            self.assertTrue(all(item.strategy_profile == PROFILE_NAME for item in results))


if __name__ == "__main__":
    unittest.main()
