from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

from hk_equity_strategies.catalog import (
    HK_EQUITY_COMBO_PROFILE,
    HK_GLOBAL_ETF_TACTICAL_ROTATION_PROFILE,
    HK_LOW_VOL_DIVIDEND_QUALITY_SNAPSHOT_PROFILE,
    get_external_snapshot_scaffold_profiles,
    get_research_backtest_only_profiles,
    get_runtime_enabled_profiles,
)
from hk_equity_strategies.live_enablement_matrix import (
    CURATED_LIVE_ENABLEMENT_STRATEGY_RANKING_VERSION,
    RUNTIME_LIVE_GATE,
    build_curated_live_enablement_strategy_ranking,
    build_live_enablement_matrix,
    build_live_enablement_row,
    build_snapshot_future_research_live_enablement_policy,
)

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "print_hk_live_enablement_matrix.py"


REMOVED_PROFILES = (
    "hk_index_mean_reversion",
    "hk_etf_regime_rotation",
    "hk_shareholder_yield_quality",
    "hk_free_cash_flow_quality",
    "hk_residual_momentum_quality",
    "hk_southbound_flow_momentum",
)


def test_live_enablement_matrix_keeps_only_runtime_profiles_selectable_or_listed():
    matrix = build_live_enablement_matrix()

    assert set(matrix["selectable_profiles"]) == get_runtime_enabled_profiles()
    assert matrix["selectable_profile_count"] == 2
    assert matrix["profile_count"] == 3
    assert matrix["blocked_profile_count"] == 1
    assert get_external_snapshot_scaffold_profiles() == frozenset()
    assert get_research_backtest_only_profiles() == frozenset({HK_EQUITY_COMBO_PROFILE})
    assert matrix["first_snapshot_candidates"] == [HK_LOW_VOL_DIVIDEND_QUALITY_SNAPSHOT_PROFILE]
    assert matrix["snapshot_required_repository_policies"] == ["quality_yield_live_enablement_policy"]
    assert matrix["backtest_validation_policy"]["policy_version"] == "hk_backtest_validation_policy.v1"
    assert matrix["backtest_validation_policy"]["max_allowed_drawdown"] == 0.30
    assert matrix["evidence_uri_policy"]["allowed_schemes"] == ["gs://", "https://", "s3://"]
    assert matrix["notification_audit_policy"]["schema_version"] == "hk_live_enablement_notification.v1"

    ranking = matrix["curated_live_enablement_strategy_ranking"]
    assert ranking["ranking_version"] == CURATED_LIVE_ENABLEMENT_STRATEGY_RANKING_VERSION
    assert [row["profile"] for row in ranking["ranking"]] == [
        HK_GLOBAL_ETF_TACTICAL_ROTATION_PROFILE,
        HK_LOW_VOL_DIVIDEND_QUALITY_SNAPSHOT_PROFILE,
    ]
    assert ranking["ranking"][1]["profile_type"] == "runtime_snapshot_backed"
    assert ranking["future_research_curated_candidate_order"] == []
    assert "hk_index_mean_reversion" in {row["profile"] for row in ranking["deprioritized_profiles"]}


def test_curated_live_enablement_ranking_excludes_weaker_research_profiles():
    ranking = build_curated_live_enablement_strategy_ranking()

    assert ranking["live_enablement_allowed_without_evidence"] is False
    assert ranking["max_allowed_drawdown"] == 0.30
    assert ranking["ranking"][0]["profile"] == HK_GLOBAL_ETF_TACTICAL_ROTATION_PROFILE
    assert ranking["ranking"][0]["max_drawdown"] == -0.2051
    assert ranking["ranking"][1]["profile"] == HK_LOW_VOL_DIVIDEND_QUALITY_SNAPSHOT_PROFILE
    assert ranking["ranking"][1]["max_drawdown"] == -0.2305
    assert all(item["decision"].startswith("exclude") for item in ranking["deprioritized_profiles"])


def test_runtime_rows_include_thresholds_evidence_commands_and_sources():
    row = build_live_enablement_row(HK_GLOBAL_ETF_TACTICAL_ROTATION_PROFILE)

    assert row["profile_type"] == "runtime_market_history"
    assert row["selectable_by_platform"] is True
    assert row["runtime_enabled"] is True
    assert row["live_enablement_gate"] == RUNTIME_LIVE_GATE
    assert row["benchmark"] == "02800"
    assert row["supported_platforms"] == ["ibkr", "longbridge"]
    assert any("max_allowed_backtest_drawdown=0.3" in item for item in row["required_evidence"])
    assert any("validate_hk_runtime_live_enablement.py" in command for command in row["evidence_commands"])
    assert row["runtime_etf_product_policy"]["required"] is True
    assert row["runtime_market_data_policy"]["required"] is True
    assert "runtime_etf_product_due_diligence_verified" in row["required_evidence"]
    assert "bilingual_notification_delivery_log_verified" in row["required_evidence"]
    assert any("trahk.com.hk" in url for url in row["research_evidence_urls"])
    assert any("All eight ETF symbols require" in note for note in row["notes"])


def test_global_etf_row_mentions_complex_etf_risk():
    row = build_live_enablement_row(HK_GLOBAL_ETF_TACTICAL_ROTATION_PROFILE)

    assert row["live_enablement_gate"] == RUNTIME_LIVE_GATE
    assert any("03175" in note for note in row["notes"])
    assert any("trahk.com.hk" in url for url in row["research_evidence_urls"])
    assert any("samsungetfhk.com/en/product/3175" in url for url in row["research_evidence_urls"])
    assert any("All eight ETF symbols require" in note for note in row["notes"])


def test_low_vol_dividend_runtime_snapshot_row_includes_live_enablement_sources():
    row = build_live_enablement_row(HK_LOW_VOL_DIVIDEND_QUALITY_SNAPSHOT_PROFILE)

    assert row["profile_type"] == "runtime_snapshot_backed"
    assert row["selectable_by_platform"] is True
    assert row["runtime_enabled"] is True
    assert row["live_enablement_gate"] == RUNTIME_LIVE_GATE
    assert "feature_snapshot_artifact_pack_validation" in row["required_evidence"]
    assert "runtime_equity_product_due_diligence_verified" in row["required_evidence"]
    assert "runtime_etf_product_due_diligence_verified" not in row["required_evidence"]
    assert any("forecast-dividend-yield-strategy" in url for url in row["research_evidence_urls"])
    assert any("hshylve.pdf" in url for url in row["research_evidence_urls"])
    assert any("three-year cash-dividend" in note for note in row["notes"])


@pytest.mark.parametrize("profile", REMOVED_PROFILES)
def test_removed_profiles_are_not_platform_selectable_or_matrix_rows(profile: str):
    with pytest.raises(ValueError, match="Unknown HK live-enable matrix profile"):
        build_live_enablement_row(profile)


def test_snapshot_future_research_policy_is_empty_after_pruning():
    policy = build_snapshot_future_research_live_enablement_policy()

    assert policy["policy_version"] == "hk_snapshot_future_research_live_enablement_policy.v1"
    assert policy["live_enablement_allowed"] is False
    assert policy["candidate_order"] == []
    assert policy["curated_candidate_order"] == []
    assert policy["deprioritized_candidate_order"] == []
    assert "new_snapshot_profile_name_and_contract_version" in policy["required_pre_scaffold_gates"]


def test_print_hk_live_enablement_matrix_json():
    completed = subprocess.run([sys.executable, str(SCRIPT), "--json"], check=True, capture_output=True, text=True)
    payload = json.loads(completed.stdout)

    assert payload["profile_count"] == 3
    assert payload["blocked_profile_count"] == 1
    assert set(payload["selectable_profiles"]) == get_runtime_enabled_profiles()
