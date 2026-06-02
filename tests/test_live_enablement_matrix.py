from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from hk_equity_strategies.catalog import (
    HK_HIGH_DIVIDEND_LOW_VOL_TREND_PROFILE,
    HK_LISTED_GLOBAL_ETF_ROTATION_PROFILE,
    get_external_snapshot_scaffold_profiles,
    get_research_backtest_only_profiles,
    get_runtime_enabled_profiles,
)
from hk_equity_strategies.live_enablement_matrix import (
    RESEARCH_ONLY_GATE,
    RUNTIME_LIVE_GATE,
    SNAPSHOT_SCAFFOLD_GATE,
    SNAPSHOT_FUTURE_RESEARCH_LIVE_ENABLEMENT_POLICY_VERSION,
    build_live_enablement_matrix,
    build_live_enablement_row,
    build_snapshot_future_research_live_enablement_policy,
)

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "print_hk_live_enablement_matrix.py"


def test_live_enablement_matrix_keeps_selectable_surface_to_runtime_profiles():
    matrix = build_live_enablement_matrix()

    assert set(matrix["selectable_profiles"]) == get_runtime_enabled_profiles()
    assert matrix["selectable_profile_count"] == 2
    assert matrix["blocked_profile_count"] == len(get_external_snapshot_scaffold_profiles()) + len(
        get_research_backtest_only_profiles()
    )
    assert matrix["first_snapshot_candidates"] == [
        "hk_low_vol_dividend_quality",
        "hk_shareholder_yield_quality",
        "hk_free_cash_flow_quality",
    ]
    assert matrix["evidence_uri_policy"]["allowed_schemes"] == ["gs://", "https://", "s3://"]
    assert "token=" in matrix["evidence_uri_policy"]["rejected_query_markers"]
    assert matrix["evidence_freshness_policy"]["required_field"] == "evidence_generated_at"
    assert matrix["backtest_validation_policy"]["policy_version"] == "hk_backtest_validation_policy.v1"
    assert matrix["backtest_validation_policy"]["max_allowed_drawdown"] == 0.30
    assert "max_drawdown_at_or_below_30_percent" in (
        matrix["backtest_validation_policy"]["required_risk_constraints"]
    )
    assert "no_full_sample_parameter_selection" in (
        matrix["backtest_validation_policy"]["required_boolean_fields"]
    )
    assert matrix["execution_capacity_policy"]["max_single_order_adv_fraction"] == 0.025
    assert matrix["rollout_risk_policy"]["max_initial_capital_fraction"] == 0.25
    assert matrix["runtime_etf_product_policy"]["policy_version"] == "hk_runtime_etf_product_due_diligence.v2"
    assert "etf_nav_or_inav_source_verified" in matrix["runtime_market_data_policy"]["required_boolean_fields"]
    assert matrix["notification_audit_policy"]["schema_version"] == "hk_live_enablement_notification.v1"
    assert matrix["dry_run_order_preview_policy"]["required"] is True
    assert "raw_order_preview_sha256" in matrix["dry_run_order_preview_policy"]["required_sha256_fields"]
    assert "future_research_live_enablement_policy" in matrix["snapshot_required_repository_policies"]
    assert "baseline_rotation_live_enablement_policy" in matrix["snapshot_required_repository_policies"]
    assert "factor_mix_live_enablement_policy" in matrix["snapshot_required_repository_policies"]
    assert "policy_value_live_enablement_policy" in matrix["snapshot_required_repository_policies"]
    assert matrix["snapshot_future_research_live_enablement_policy"]["policy_version"] == (
        SNAPSHOT_FUTURE_RESEARCH_LIVE_ENABLEMENT_POLICY_VERSION
    )
    assert matrix["snapshot_future_research_live_enablement_policy"]["live_enablement_allowed"] is False


def test_runtime_rows_include_thresholds_evidence_commands_and_sources():
    row = build_live_enablement_row(HK_HIGH_DIVIDEND_LOW_VOL_TREND_PROFILE)

    assert row["profile_type"] == "runtime_market_history"
    assert row["selectable_by_platform"] is True
    assert row["runtime_enabled"] is True
    assert row["live_enablement_gate"] == RUNTIME_LIVE_GATE
    assert row["benchmark"] == "03110"
    assert row["supported_platforms"] == ["ibkr", "longbridge"]
    assert any("max_allowed_backtest_drawdown=0.12" in item for item in row["required_evidence"])
    assert any("validate_hk_runtime_live_enablement.py" in command for command in row["evidence_commands"])
    assert row["evidence_uri_policy"]["required"] is True
    assert row["backtest_validation_policy"]["max_allowed_drawdown"] == 0.30
    assert "transaction_cost_slippage_lot_size_and_suspension_model_included" in (
        row["backtest_validation_policy"]["required_boolean_fields"]
    )
    assert "signature=" in row["evidence_uri_policy"]["rejected_query_markers"]
    assert row["evidence_freshness_policy"]["required"] is True
    assert row["execution_capacity_policy"]["min_median_daily_turnover_hkd"] == 10_000_000
    assert row["rollout_risk_policy"]["required"] is True
    assert row["runtime_etf_product_policy"]["required"] is True
    assert "etf_product_universe_audit_uri" in row["runtime_etf_product_policy"]["required_uri_fields"]
    assert "official_product_document_uri" in row["runtime_etf_product_policy"]["required_uri_fields"]
    assert "stock_connect_etf_eligibility_source_uri" in row["runtime_etf_product_policy"]["required_uri_fields"]
    assert "southbound_etf_turnover_and_fund_flow_source_uri" in (
        row["runtime_etf_product_policy"]["required_uri_fields"]
    )
    assert "underlying_index_or_reference_asset_verified" in (
        row["runtime_etf_product_policy"]["required_boolean_fields"]
    )
    assert "etf_connect_daily_turnover_and_fund_flow_trend_reviewed" in (
        row["runtime_etf_product_policy"]["required_boolean_fields"]
    )
    assert row["runtime_market_data_policy"]["required"] is True
    assert "market_history_source_uri" in row["runtime_market_data_policy"]["required_uri_fields"]
    assert "runtime_etf_product_due_diligence_verified" in row["required_evidence"]
    assert "etf_connect_eligibility_and_southbound_flow_review_verified" in row["required_evidence"]
    assert "runtime_market_data_audit_verified" in row["required_evidence"]
    assert "runtime_market_history_source_provenance_verified" in row["required_evidence"]
    assert "execution_capacity_and_liquidity_limits_verified" in row["required_evidence"]
    assert "dry_run_order_preview_artifact_provenance_verified" in row["required_evidence"]
    assert "staged_rollout_tripwires_and_rollback_ready" in row["required_evidence"]
    assert "bilingual_notification_delivery_log_verified" in row["required_evidence"]
    assert row["notification_audit_policy"]["expected_event_type"] == "hk_runtime_live_enablement_dry_run"
    assert row["dry_run_order_preview_policy"]["policy_version"] == "hk_dry_run_order_preview_provenance.v1"
    assert any("exchange-traded-products/overview" in url for url in row["research_evidence_urls"])
    assert any("Market-Makers/Overview" in url for url in row["research_evidence_urls"])
    assert any("Inclusion-of-ETFs-in-Stock-Connect" in url for url in row["research_evidence_urls"])
    assert any("view-all-eligible-securities" in url for url in row["research_evidence_urls"])
    assert any("Historical-Daily" in url for url in row["research_evidence_urls"])
    assert any("globalxetfs.com.hk/funds/hang-seng-high-dividend-yield-etf" in url for url in row["research_evidence_urls"])
    assert any("IM_hshdyie.pdf" in url for url in row["research_evidence_urls"])
    assert any("spdr-gold-shares-2840" in url for url in row["research_evidence_urls"])
    assert any("ird.gov.hk/eng/faq/ETFs.htm" in url for url in row["research_evidence_urls"])
    assert any("hkex.com.hk/News/Market-Communications/2015/150204news" in url for url in row["research_evidence_urls"])
    assert any("capital-distribution risk" in note for note in row["notes"])
    assert any("single-commodity trust" in note for note in row["notes"])
    assert any("Southbound turnover/fund-flow" in note for note in row["notes"])


def test_global_etf_row_mentions_complex_etf_risk():
    row = build_live_enablement_row(HK_LISTED_GLOBAL_ETF_ROTATION_PROFILE)

    assert row["live_enablement_gate"] == RUNTIME_LIVE_GATE
    assert any("03175" in note for note in row["notes"])
    assert any("trahk.com.hk" in url for url in row["research_evidence_urls"])
    assert any("china_A50_etf.php" in url for url in row["research_evidence_urls"])
    assert any("chinaamc-csi-300-index-etf" in url for url in row["research_evidence_urls"])
    assert any("3033.php" in url for url in row["research_evidence_urls"])
    assert any("ifp.hkex.com.hk/fund/BHG161" in url for url in row["research_evidence_urls"])
    assert any("samsungetfhk.com/en/product/3175" in url for url in row["research_evidence_urls"])
    assert any("Inclusion-of-ETFs-in-Stock-Connect" in url for url in row["research_evidence_urls"])
    assert any("All eight ETF symbols require" in note for note in row["notes"])
    assert any("A-share sleeves 02822 and 03188" in note for note in row["notes"])
    assert any("futures-roll/margin/curve" in note for note in row["notes"])
    assert any("Southbound ETF route evidence" in note for note in row["notes"])


def test_snapshot_scaffold_row_is_blocked_and_points_to_snapshot_gates():
    row = build_live_enablement_row("hk_shareholder_yield_quality")

    assert row["profile_type"] == "external_snapshot_scaffold"
    assert row["selectable_by_platform"] is False
    assert row["live_enablement_gate"] == SNAPSHOT_SCAFFOLD_GATE
    assert "hkeq-print-snapshot-promotion-matrix --json" in row["evidence_commands"]
    assert "snapshot_live_enablement_evidence_validation" in row["required_evidence"]
    assert "snapshot_repository_required_policy_review" in row["required_evidence"]
    assert "snapshot_future_research_live_enablement_policy_review" in row["required_evidence"]
    assert any("Prioritized" in note for note in row["notes"])
    assert any("newsletter_202506.pdf" in url for url in row["research_evidence_urls"])
    assert any("repurchase-securities-and-treasury-shares" in url for url in row["research_evidence_urls"])
    assert any("240412news" in url for url in row["research_evidence_urls"])
    assert any("forecast-dividend-yield-strategy" in url for url in row["research_evidence_urls"])
    assert any("estimate cuts" in note for note in row["notes"])
    assert any("post-buyback financing review" in note for note in row["notes"])


def test_momentum_snapshot_scaffold_rows_include_current_hsi_momentum_methodology():
    row = build_live_enablement_row("hk_residual_momentum_quality")

    assert row["profile_type"] == "external_snapshot_scaffold"
    assert row["selectable_by_platform"] is False
    assert any("IM_hssbisme.pdf" in url for url in row["research_evidence_urls"])
    assert any("all-indexes/hssbism" in url for url in row["research_evidence_urls"])
    assert any("msci.com/indexes/index/711028" in url for url in row["research_evidence_urls"])
    assert any("MSCI_Momentum_Indexes_Methodology" in url for url in row["research_evidence_urls"])
    assert any("one-month-skip risk-adjusted momentum" in note for note in row["notes"])


def test_liquid_and_composite_momentum_rows_include_descriptor_reconciliation_notes():
    liquid = build_live_enablement_row("hk_liquid_momentum_quality")
    composite = build_live_enablement_row("hk_composite_factor_quality_value_momentum")

    assert any("711028" in url for url in liquid["research_evidence_urls"])
    assert any("6/12-month risk-adjusted momentum" in note for note in liquid["notes"])
    assert any("Momentum_Indexes_Methodology" in url for url in composite["research_evidence_urls"])
    assert any("momentum sleeve adds excess return" in note for note in composite["notes"])


def test_first_snapshot_candidates_expose_profile_specific_external_evidence():
    row = build_live_enablement_row("hk_free_cash_flow_quality")

    assert row["profile_type"] == "external_snapshot_scaffold"
    assert any("hsscfcfe.pdf" in url for url in row["research_evidence_urls"])
    assert any("IM_hsscfcfe.pdf" in url for url in row["research_evidence_urls"])
    assert any("methodology-sp-access-hk-fcf-50-index.pdf" in url for url in row["research_evidence_urls"])
    assert any("sp-access-hong-kong-dividend-free-cash-flow-index" in url for url in row["research_evidence_urls"])
    assert any("FCF formula lineage" in note for note in row["notes"])
    assert any("financial/real-estate/negative-FCF" in note for note in row["notes"])


def test_low_vol_dividend_snapshot_row_includes_hshylv_live_enablement_sources():
    row = build_live_enablement_row("hk_low_vol_dividend_quality")

    assert row["profile_type"] == "external_snapshot_scaffold"
    assert row["selectable_by_platform"] is False
    assert any("forecast-dividend-yield-strategy" in url for url in row["research_evidence_urls"])
    assert any("hshylve.pdf" in url for url in row["research_evidence_urls"])
    assert any("IM_hshylve.pdf" in url for url in row["research_evidence_urls"])
    assert any("hsschyse.pdf" in url for url in row["research_evidence_urls"])
    assert any("IM_hsschkye.pdf" in url for url in row["research_evidence_urls"])
    assert any("three-year cash-dividend" in note for note in row["notes"])
    assert any("point-in-time estimate history" in note for note in row["notes"])
    assert any("financial-soundness screens" in note for note in row["notes"])


def test_southbound_flow_snapshot_row_includes_hkex_flow_source_audit_evidence():
    row = build_live_enablement_row("hk_southbound_flow_momentum")

    assert row["profile_type"] == "external_snapshot_scaffold"
    assert row["selectable_by_platform"] is False
    assert any("Historical-Daily" in url for url in row["research_evidence_urls"])
    assert any("mutualmarket.aspx?t=hk" in url for url in row["research_evidence_urls"])
    assert any("view-all-eligible-securities" in url for url in row["research_evidence_urls"])
    assert any("2404122news" in url for url in row["research_evidence_urls"])
    assert any("abstract_id=5128472" in url for url in row["research_evidence_urls"])
    assert any("top-10 turnover" in note for note in row["notes"])
    assert any("raw HKEX/CCASS records" in note for note in row["notes"])


def test_ah_premium_snapshot_row_includes_hsi_sse_price_ratio_controls():
    row = build_live_enablement_row("hk_ah_premium_relative_value")

    assert row["profile_type"] == "external_snapshot_scaffold"
    assert row["selectable_by_platform"] is False
    assert any("all-indexes/ahpremium" in url for url in row["research_evidence_urls"])
    assert any("all-indexes/chinaah" in url for url in row["research_evidence_urls"])
    assert any("20240124T000000.pdf" in url for url in row["research_evidence_urls"])
    assert any("20210914T000000.pdf" in url for url in row["research_evidence_urls"])
    assert any("H50066_h50066hbooken_EN.pdf" in url for url in row["research_evidence_urls"])
    assert any("long-only H-share valuation overlay" in note for note in row["notes"])
    assert any("AH price-ratio formula lineage" in note for note in row["notes"])
    assert any("false-reversal stress" in note for note in row["notes"])


def test_index_rebalance_snapshot_row_includes_hsi_schedule_and_cas_controls():
    row = build_live_enablement_row("hk_index_rebalance_event")

    assert row["profile_type"] == "external_snapshot_scaffold"
    assert row["selectable_by_platform"] is False
    assert row["live_enablement_gate"] == SNAPSHOT_SCAFFOLD_GATE
    assert any("index_methodology_guide_e.pdf" in url for url in row["research_evidence_urls"])
    assert any("index_operation_guide_e.pdf" in url for url in row["research_evidence_urls"])
    assert any("is_update.xlsx" in url for url in row["research_evidence_urls"])
    assert any("20260102T163000.pdf" in url for url in row["research_evidence_urls"])
    assert any("20260213T174500.pdf" in url for url in row["research_evidence_urls"])
    assert any("20260522T174500.pdf" in url for url in row["research_evidence_urls"])
    assert any("Trading/CAS" in url for url in row["research_evidence_urls"])
    assert any("official HSI rebalancing schedules" in note for note in row["notes"])
    assert any("schedule-file version" in note for note in row["notes"])
    assert any("pro-forma records" in note for note in row["notes"])
    assert any("market-on-close versus next-open" in note for note in row["notes"])
    assert any("two-stage price-limit" in note for note in row["notes"])
    assert any("order-rejection" in note for note in row["notes"])
    assert any("market-on-close execution controls" in note for note in row["notes"])


def test_research_only_row_is_not_platform_selectable():
    row = build_live_enablement_row("hk_index_mean_reversion")

    assert row["profile_type"] == "research_backtest_only"
    assert row["selectable_by_platform"] is False
    assert row["live_enablement_gate"] == RESEARCH_ONLY_GATE
    assert row["supported_platforms"] == []


def test_snapshot_future_research_policy_blocks_non_scaffolded_ideas():
    policy = build_snapshot_future_research_live_enablement_policy()

    assert policy["policy_version"] == SNAPSHOT_FUTURE_RESEARCH_LIVE_ENABLEMENT_POLICY_VERSION
    assert policy["source_repository"] == "HkEquitySnapshotPipelines"
    assert policy["source_matrix_field"] == "future_research_backlog.future_research_live_enablement_policy"
    assert policy["live_enablement_allowed"] is False
    assert policy["candidate_order"] == [
        "hk_earnings_revision_quality_overlay",
        "hk_low_size_quality_liquidity_premium",
        "hk_stock_connect_inclusion_event_flow",
        "hk_short_selling_pressure_risk_overlay",
        "hk_director_dealing_disclosure_quality_overlay",
    ]
    assert "new_snapshot_profile_name_and_contract_version" in policy["required_pre_scaffold_gates"]
    assert "point_in_time_consensus_estimate_and_revision_history" in policy["required_pre_scaffold_gates"]
    assert "point_in_time_market_cap_liquidity_and_capacity_history" in policy["required_pre_scaffold_gates"]
    assert "stock_connect_eligibility_change_event_history" in policy["required_pre_scaffold_gates"]
    assert "short_selling_turnover_shortable_status_and_short_interest_history" in (
        policy["required_pre_scaffold_gates"]
    )
    assert "director_dealing_disclosure_notice_and_blackout_context_history" in (
        policy["required_pre_scaffold_gates"]
    )
    assert "mutating_existing_snapshot_contract_in_place" in policy["required_reject_criteria"]


def test_quality_growth_snapshot_scaffold_row_includes_live_policy_review_and_sources():
    row = build_live_enablement_row("hk_quality_growth_low_volatility")

    assert row["profile_type"] == "external_snapshot_scaffold"
    assert row["selectable_by_platform"] is False
    assert row["live_enablement_gate"] == SNAPSHOT_SCAFFOLD_GATE
    assert "snapshot_repository_required_policy_review" in row["required_evidence"]
    assert any("hsqglve.pdf" in url for url in row["research_evidence_urls"])
    assert any("msci.com/indexes/index/721604" in url for url in row["research_evidence_urls"])
    assert any("60ebccab" in url for url in row["research_evidence_urls"])
    assert any("quality-indexes" in url for url in row["research_evidence_urls"])
    assert any("minimum-volatility-indexes" in url for url in row["research_evidence_urls"])
    assert any("Quality-growth low-volatility scaffold is active" in note for note in row["notes"])
    assert any("Growth in ROA adjusted by P/B" in note for note in row["notes"])
    assert any("MSCI HK-listed Southbound Quality evidence" in note for note in row["notes"])
    assert any("minimum-volatility optimizer constraints" in note for note in row["notes"])



def test_policy_value_snapshot_scaffold_row_includes_live_policy_review_and_sources():
    row = build_live_enablement_row("hk_central_soe_value_quality_select")

    assert row["profile_type"] == "external_snapshot_scaffold"
    assert row["selectable_by_platform"] is False
    assert row["live_enablement_gate"] == SNAPSHOT_SCAFFOLD_GATE
    assert "snapshot_repository_required_policy_review" in row["required_evidence"]
    assert any("IM_hssccsme.pdf" in url for url in row["research_evidence_urls"])
    assert any("hsscsoee.pdf" in url for url in row["research_evidence_urls"])
    assert any("hssccsve.pdf" in url for url in row["research_evidence_urls"])
    assert any("hssccsqe.pdf" in url for url in row["research_evidence_urls"])
    assert any("eligible-stocks" in url for url in row["research_evidence_urls"])
    assert any("sasac.gov.cn" in url for url in row["research_evidence_urls"])
    assert any("en.sasac.gov.cn" in url for url in row["research_evidence_urls"])
    assert any("mof.gov.cn" in url for url in row["research_evidence_urls"])
    assert any("Central-SOE value-quality scaffold is active" in note for note in row["notes"])
    assert any("SASAC/MOF central-SOE source-list" in note for note in row["notes"])
    assert any("effective-date drift" in note for note in row["notes"])
    assert any("missing-measure averaging" in note for note in row["notes"])
    assert any("factor-screen/cap turnover spikes" in note for note in row["notes"])
    assert any("Southbound eligibility removals" in note for note in row["notes"])


def test_factor_mix_snapshot_scaffold_row_includes_live_policy_review_and_sources():
    row = build_live_enablement_row("hk_factor_mix_qvlm_risk_parity")

    assert row["profile_type"] == "external_snapshot_scaffold"
    assert row["selectable_by_platform"] is False
    assert row["live_enablement_gate"] == SNAPSHOT_SCAFFOLD_GATE
    assert "snapshot_repository_required_policy_review" in row["required_evidence"]
    assert any("hssbmfrpe.pdf" in url for url in row["research_evidence_urls"])
    assert any("IM_hssbmfrpe.pdf" in url for url in row["research_evidence_urls"])
    assert any("all-indexes/hssbmfew" in url for url in row["research_evidence_urls"])
    assert any("msci.com/indexes/index/705097" in url for url in row["research_evidence_urls"])
    assert any("factor-mix-a-series-indexes" in url for url in row["research_evidence_urls"])
    assert any("MSCI_Factor_Mix_Indexes_Methodology" in url for url in row["research_evidence_urls"])
    assert any("Risk-parity QVLM scaffold is active" in note for note in row["notes"])
    assert any("component-index return history" in note for note in row["notes"])
    assert any("capped-methodology controls" in note for note in row["notes"])
    assert any("cap-induced turnover" in note for note in row["notes"])
    assert any("12% capping lineage" in note for note in row["notes"])
    assert any("factor-correlation breakdown stress" in note for note in row["notes"])


def test_print_hk_live_enablement_matrix_json():
    completed = subprocess.run(
        [sys.executable, str(SCRIPT), "--json"],
        check=True,
        capture_output=True,
        text=True,
    )
    payload = json.loads(completed.stdout)

    assert set(payload["selectable_profiles"]) == {
        HK_HIGH_DIVIDEND_LOW_VOL_TREND_PROFILE,
        HK_LISTED_GLOBAL_ETF_ROTATION_PROFILE,
    }
    assert any(row["profile"] == "hk_shareholder_yield_quality" for row in payload["profiles"])
    assert payload["snapshot_future_research_live_enablement_policy"]["live_enablement_allowed"] is False
