from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from hk_equity_strategies.catalog import HK_LISTED_GLOBAL_ETF_ROTATION_PROFILE
from hk_equity_strategies.runtime_readiness import build_hk_runtime_readiness

SCRIPT_PATH = Path(__file__).resolve().parents[1] / "scripts" / "print_hk_runtime_readiness.py"


def test_ibkr_global_etf_readiness_uses_hk_market_defaults():
    plan = build_hk_runtime_readiness(
        HK_LISTED_GLOBAL_ETF_ROTATION_PROFILE,
        platform_id="ibkr",
    )

    assert plan["runtime_enabled"] is True
    assert plan["dry_run_only"] is True
    assert plan["market_defaults"] == {
        "market": "HK",
        "market_calendar": "XHKG",
        "market_timezone": "Asia/Hong_Kong",
        "market_exchange": "SEHK",
        "trading_currency": "HKD",
        "symbol_suffix": ".HK",
        "quantity_type": "integer_shares",
    }
    assert plan["platform_dry_run_env"]["IBKR_DRY_RUN_ONLY"] == "true"
    assert plan["platform_dry_run_env"]["IBKR_MARKET_EXCHANGE"] == "SEHK"
    assert plan["managed_symbols"] == [
        "02800",
        "02822",
        "03188",
        "03033",
        "02834",
        "02840",
        "03175",
        "03110",
    ]
    assert plan["target_conversion"] == {
        "strategy_target_mode": "weight",
        "platform_native_target_mode": "weight",
        "requires_portfolio_snapshot": False,
        "portfolio_input_name": None,
    }
    assert any("lot-size" in check for check in plan["dry_run_checks"])
    assert any("Cloud Run" in note for note in plan["risk_notes"])


def test_longbridge_global_etf_readiness_requires_portfolio_snapshot_conversion():
    plan = build_hk_runtime_readiness(
        "hk_global_etf_rotation",
        platform_id="longbridge",
    )

    assert plan["canonical_profile"] == HK_LISTED_GLOBAL_ETF_ROTATION_PROFILE
    assert plan["platform_dry_run_env"]["ACCOUNT_REGION"] == "HK"
    assert plan["platform_dry_run_env"]["LONGBRIDGE_SYMBOL_SUFFIX"] == ".HK"
    assert plan["target_conversion"] == {
        "strategy_target_mode": "weight",
        "platform_native_target_mode": "value",
        "requires_portfolio_snapshot": True,
        "portfolio_input_name": "portfolio_snapshot",
    }
    assert "portfolio_snapshot" in plan["available_inputs"]


def test_print_hk_runtime_readiness_json():
    completed = subprocess.run(
        [
            sys.executable,
            str(SCRIPT_PATH),
            "--profile",
            HK_LISTED_GLOBAL_ETF_ROTATION_PROFILE,
            "--platform",
            "ibkr",
            "--json",
        ],
        check=True,
        capture_output=True,
        text=True,
    )

    payload = json.loads(completed.stdout)
    assert payload["platform"] == "ibkr"
    assert payload["canonical_profile"] == HK_LISTED_GLOBAL_ETF_ROTATION_PROFILE
    assert payload["platform_dry_run_env"]["IBKR_MARKET_DATA_SYMBOL_SUFFIX"] == ".HK"


def test_smoke_hk_listed_global_etf_rotation_dry_run_json():
    script = Path(__file__).resolve().parents[1] / "scripts" / "smoke_hk_listed_global_etf_rotation_dry_run.py"
    completed = subprocess.run(
        [sys.executable, str(script), "--json"],
        check=True,
        capture_output=True,
        text=True,
    )

    payload = json.loads(completed.stdout)
    assert payload["status"] == "pass"
    assert payload["profile"] == HK_LISTED_GLOBAL_ETF_ROTATION_PROFILE
    assert payload["checks"] == {
        "strategy_actionable": True,
        "uses_direct_market_history": True,
        "weights_non_empty": True,
        "gross_exposure_lte_one": True,
        "ibkr_dry_run_only": True,
        "longbridge_dry_run_only": True,
        "longbridge_requires_portfolio_snapshot": True,
        "ibkr_weight_native": True,
    }
    assert 0.0 < payload["gross_exposure"] <= 1.0
    assert payload["platforms"]["ibkr"]["market_defaults"]["market_exchange"] == "SEHK"
    assert payload["platforms"]["longbridge"]["market_defaults"]["symbol_suffix"] == ".HK"
