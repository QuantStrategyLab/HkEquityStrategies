from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from typing import Any

from hk_equity_strategies.backtest_validation_policy import (
    BACKTEST_VALIDATION_POLICY_VERSION,
    build_backtest_validation_policy,
)
from hk_equity_strategies.catalog import (
    HK_HIGH_DIVIDEND_LOW_VOL_TREND_PROFILE,
    HK_LISTED_GLOBAL_ETF_ROTATION_PROFILE,
    HK_LOW_VOL_DIVIDEND_QUALITY_PROFILE,
    get_direct_market_history_profiles,
    get_external_snapshot_scaffold_profiles,
    get_research_backtest_only_profiles,
    get_runtime_enabled_profiles,
    get_snapshot_backed_profiles,
    get_strategy_definition,
    get_strategy_metadata,
)
from hk_equity_strategies.evidence_freshness_policy import build_evidence_freshness_policy
from hk_equity_strategies.evidence_uri_policy import build_evidence_uri_policy
from hk_equity_strategies.execution_capacity_policy import build_execution_capacity_policy
from hk_equity_strategies.dry_run_order_preview_policy import build_dry_run_order_preview_policy
from hk_equity_strategies.notification_audit_policy import (
    RUNTIME_DRY_RUN_NOTIFICATION_EVENT_TYPE,
    build_notification_audit_policy,
)
from hk_equity_strategies.rollout_risk_policy import build_rollout_risk_policy
from hk_equity_strategies.runtime_etf_product_policy import build_runtime_etf_product_policy
from hk_equity_strategies.runtime_market_data_policy import build_runtime_market_data_policy
from hk_equity_strategies.runtime_readiness import (
    PROFILE_LIVE_ENABLEMENT_THRESHOLDS,
    REQUIRED_LIVE_EVIDENCE_FIELDS,
)

HK_STRATEGY_LIVE_ENABLEMENT_MATRIX_VERSION = "hk_equity_strategies.live_enablement_matrix.v1"
RUNTIME_LIVE_GATE = "requires_runtime_live_enablement_evidence"
SNAPSHOT_SCAFFOLD_GATE = "requires_snapshot_promotion_matrix_and_production_evidence"
RESEARCH_ONLY_GATE = "research_backtest_only_not_platform_selectable"
SUPPORTED_PLATFORMS = ("ibkr", "longbridge")

FIRST_SNAPSHOT_CANDIDATES = (HK_LOW_VOL_DIVIDEND_QUALITY_PROFILE,)

SNAPSHOT_PROMOTION_MATRIX_COMMAND = "hkeq-print-snapshot-promotion-matrix --json"
RUNTIME_EVIDENCE_TEMPLATE_COMMAND = "python scripts/validate_hk_runtime_live_enablement.py --print-template --profile <profile> --platform <platform> --json"
SNAPSHOT_FUTURE_RESEARCH_LIVE_ENABLEMENT_POLICY_VERSION = "hk_snapshot_future_research_live_enablement_policy.v1"

SNAPSHOT_REQUIRED_REPOSITORY_POLICIES: tuple[str, ...] = (
    "baseline_rotation_live_enablement_policy",
    "quality_yield_live_enablement_policy",
    "quality_growth_live_enablement_policy",
    "factor_mix_live_enablement_policy",
    "policy_value_live_enablement_policy",
    "momentum_live_enablement_policy",
    "special_situation_live_enablement_policy",
    "future_research_live_enablement_policy",
)

SNAPSHOT_FUTURE_RESEARCH_CANDIDATES: tuple[str, ...] = (
    "hk_earnings_revision_quality_overlay",
    "hk_low_size_quality_liquidity_premium",
    "hk_stock_connect_inclusion_event_flow",
    "hk_short_selling_pressure_risk_overlay",
    "hk_director_dealing_disclosure_quality_overlay",
    "hk_dually_traded_liquid_reversal_overlay",
    "hk_earnings_announcement_drift_overlay",
    "hk_lottery_stock_risk_exclusion_overlay",
    "hk_equity_financing_dilution_risk_overlay",
    "hk_connected_transaction_governance_risk_overlay",
    "hk_takeover_privatization_event_spread_overlay",
    "hk_distribution_ex_date_entitlement_overlay",
    "hk_ipo_lockup_overhang_event_overlay",
    "hk_audit_opinion_suspension_risk_overlay",
    "hk_share_repurchase_execution_signal_overlay",
    "hk_liquid_pairs_cointegration_stat_arb_overlay",
    "hk_macro_liquidity_inflation_rate_sensitivity_overlay",
    "hk_turn_of_month_lunar_new_year_calendar_overlay",
    "hk_etf_premium_discount_tracking_quality_overlay",
    "hk_asset_growth_net_issuance_quality_overlay",
    "hk_accrual_quality_earnings_persistence_overlay",
    "hk_fscore_gross_profitability_quality_overlay",
    "hk_shareholding_concentration_free_float_risk_overlay",
    "hk_amihud_liquidity_risk_capacity_overlay",
    "hk_analyst_dispersion_coverage_risk_overlay",
    "hk_financial_distress_deleveraging_risk_overlay",
    "hk_downside_beta_tail_risk_volatility_overlay",
    "hk_structured_product_warrant_cbbc_flow_risk_overlay",
    "hk_index_derivatives_futures_options_sentiment_basis_overlay",
    "hk_vcm_cas_microstructure_shock_risk_overlay",
    "hk_reit_dividend_spread_rate_sensitivity_overlay",
    "hk_regulatory_enforcement_disciplinary_risk_overlay",
    "hk_margin_financing_collateral_forced_selling_risk_overlay",
    "hk_liquid_largecap_weekly_reversal_cost_aware_overlay",
    "hk_us_adr_hk_secondary_listing_lead_lag_overlay",
    "hk_smart_beta_factor_regime_rotation_overlay",
    "hk_esg_downside_risk_quality_overlay",
)

SNAPSHOT_FUTURE_RESEARCH_CURATED_CANDIDATES: tuple[str, ...] = (
    "hk_earnings_revision_quality_overlay",
    "hk_stock_connect_inclusion_event_flow",
    "hk_share_repurchase_execution_signal_overlay",
    "hk_etf_premium_discount_tracking_quality_overlay",
    "hk_amihud_liquidity_risk_capacity_overlay",
    "hk_downside_beta_tail_risk_volatility_overlay",
    "hk_smart_beta_factor_regime_rotation_overlay",
)

SNAPSHOT_FUTURE_RESEARCH_DEPRIORITIZED_CANDIDATES: tuple[str, ...] = tuple(
    profile for profile in SNAPSHOT_FUTURE_RESEARCH_CANDIDATES if profile not in SNAPSHOT_FUTURE_RESEARCH_CURATED_CANDIDATES
)

SNAPSHOT_FUTURE_RESEARCH_PRE_SCAFFOLD_GATES: tuple[str, ...] = (
    "new_snapshot_profile_name_and_contract_version",
    "candidate_specific_production_source_audit_policy",
    "same_universe_ablation_vs_existing_snapshot_profiles",
    "point_in_time_consensus_estimate_and_revision_history",
    "point_in_time_market_cap_liquidity_and_capacity_history",
    "stock_connect_eligibility_change_event_history",
    "short_selling_turnover_shortable_status_and_short_interest_history",
    "director_dealing_disclosure_notice_and_blackout_context_history",
    "dually_traded_security_mapping_reversal_cost_and_capacity_history",
    "earnings_announcement_timestamp_profit_warning_and_pead_event_history",
    "lottery_feature_ivol_iskew_max_price_and_regime_history",
    "equity_financing_rights_open_offer_placement_convertible_dilution_event_history",
    "connected_transaction_related_party_tunneling_propping_and_governance_event_history",
    "takeover_privatization_possible_offer_firm_intention_offer_period_and_completion_risk_history",
    "distribution_ex_date_entitlement_record_date_payment_price_adjustment_and_settlement_history",
    "ipo_listing_cornerstone_pre_ipo_lockup_expiry_overhang_and_stabilization_history",
    "audit_opinion_disclaimer_adverse_qualified_going_concern_suspension_resumption_history",
    "share_repurchase_execution_treasury_share_resale_mandate_and_undervaluation_history",
    "pairs_cointegration_spread_stability_borrow_shorting_tick_rule_and_capacity_history",
    "macro_inflation_hibor_base_rate_release_lag_sector_sensitivity_and_capacity_history",
    "calendar_turn_of_month_lunar_new_year_hkex_trading_settlement_and_short_sale_history",
    "etf_premium_discount_tracking_nav_inav_liquidity_complex_product_and_permission_history",
    "asset_growth_net_share_issuance_reporting_date_restatement_and_sector_exception_history",
    "accrual_quality_earnings_persistence_reporting_date_restatement_sector_exception_and_liquidity_history",
    "fscore_gross_profitability_reporting_date_restatement_sector_exception_and_liquidity_history",
    "shareholding_concentration_ccass_free_float_ramp_dump_red_flag_and_liquidity_history",
    "amihud_liquidity_risk_market_wide_shock_capacity_and_execution_history",
    "analyst_forecast_dispersion_coverage_recommendation_target_price_and_vendor_history",
    "financial_distress_zscore_debt_maturity_interest_coverage_and_deleveraging_history",
    "downside_beta_semivariance_var_cvar_tail_risk_and_volatility_regime_history",
    "derivative_warrant_cbbc_flow_mce_liquidity_provider_and_underlying_ablation_history",
    "index_derivatives_futures_options_basis_put_call_open_interest_and_expiry_roll_history",
    "vcm_cas_microstructure_shock_cooling_off_auction_and_execution_ablation_history",
    "reit_dividend_spread_distribution_nav_gearing_rate_sensitivity_and_ablation_history",
    "regulatory_enforcement_disciplinary_sanction_misconduct_and_governance_ablation_history",
    "margin_financing_collateral_haircut_pledge_forced_selling_and_liquidity_ablation_history",
    "weekly_reversal_extreme_return_cost_slippage_vcm_cas_and_momentum_ablation_history",
    "adr_hk_secondary_listing_lead_lag_fx_conversion_and_execution_ablation_history",
    "smart_beta_factor_regime_rotation_market_cycle_sentiment_and_factor_ablation_history",
    "esg_downside_risk_rating_ungc_controversy_tilt_and_downside_ablation_history",
    "survivorship_safe_walk_forward_backtest_vs_02800_and_candidate_benchmark",
    "artifact_provenance_dry_run_order_preview_bilingual_notifications_and_rollout_controls",
    "operator_approval_reference",
)

COMMON_PLATFORM_EVIDENCE_REQUIREMENTS: tuple[str, ...] = (
    "platform_dry_run_order_preview",
    "broker_hk_market_data_and_trading_permission",
    "hk_fees_levies_and_stamp_duty_or_etf_exemption_verified",
    "bid_ask_spread_and_slippage_captured",
    "lot_size_and_integer_share_rounding_verified",
    "runtime_etf_product_due_diligence_verified",
    "etf_connect_eligibility_and_southbound_flow_review_verified",
    "runtime_market_data_audit_verified",
    "runtime_market_history_source_provenance_verified",
    "backtest_validation_policy_evidence",
    "point_in_time_no_lookahead_and_no_overfit_controls",
    "per_fold_drawdown_parameter_stability_and_regime_stress_controls",
    "dry_run_order_preview_artifact_provenance_verified",
    "execution_capacity_and_liquidity_limits_verified",
    "fresh_section_evidence_generated_at",
    "staged_rollout_tripwires_and_rollback_ready",
    "bilingual_notification_delivery_log_verified",
    "operator_approval_reference",
)

CURATED_LIVE_ENABLEMENT_STRATEGY_RANKING_VERSION = "hk_equity_strategies.curated_live_enablement_ranking.v1"

CURATED_LIVE_ENABLEMENT_STRATEGY_RANKING: tuple[dict[str, object], ...] = (
    {
        "rank": 1,
        "profile": HK_HIGH_DIVIDEND_LOW_VOL_TREND_PROFILE,
        "profile_type": "runtime_market_history",
        "decision": "keep_runtime_enabled_preferred",
        "annualized_return": 0.1716,
        "max_drawdown": -0.0806,
        "why": (
            "Best current risk-adjusted HK runtime candidate: simple 03110/02840 universe, "
            "12% volatility target, positive train period, and the lowest verified drawdown."
        ),
        "next_action": "Keep live-enable capable, but require broker dry-run evidence before real order submission.",
    },
    {
        "rank": 2,
        "profile": HK_LISTED_GLOBAL_ETF_ROTATION_PROFILE,
        "profile_type": "runtime_market_history",
        "decision": "keep_runtime_enabled_secondary",
        "annualized_return": 0.1884,
        "max_drawdown": -0.2051,
        "why": (
            "Highest current annualized return among implemented HK strategies while staying below the 30% "
            "drawdown limit; broader ETF universe improves diversification but adds product-complexity risk."
        ),
        "next_action": "Use dry-run/paper mode until every ETF sleeve has product, spread, lot-size, and platform checks.",
    },
    {
        "rank": 3,
        "profile": HK_LOW_VOL_DIVIDEND_QUALITY_PROFILE,
        "profile_type": "runtime_snapshot_backed",
        "decision": "runtime_enabled_pending_evidence",
        "annualized_return": None,
        "max_drawdown": None,
        "why": (
            "First promoted snapshot-backed runtime profile; it consumes production low-volatility/dividend "
            "factor snapshots while keeping snapshot generation in HkEquitySnapshotPipelines."
        ),
        "next_action": (
            "Keep dry-run only until artifact-pack validation, point-in-time walk-forward evidence, "
            "broker order preview, bilingual notification logs, and operator approval all pass."
        ),
    },
    {
        "rank": 4,
        "profile": "hk_shareholder_yield_quality",
        "profile_type": "external_snapshot_scaffold",
        "decision": "first_snapshot_candidate",
        "annualized_return": None,
        "max_drawdown": None,
        "why": "Observable HKEX buyback disclosures plus dividend/share-count quality can complement low-vol dividend.",
        "next_action": "Audit HKEX repurchase, treasury-share, dilution, blackout, and share-count reconciliation evidence.",
    },
    {
        "rank": 5,
        "profile": "hk_free_cash_flow_quality",
        "profile_type": "external_snapshot_scaffold",
        "decision": "first_snapshot_candidate",
        "annualized_return": None,
        "max_drawdown": None,
        "why": "FCF yield is a robust quality/value extension, but only after point-in-time reporting-date evidence is audited.",
        "next_action": "Build fundamentals lineage, EV/FCF formula audit, restatement controls, and sector exceptions.",
    },
    {
        "rank": 6,
        "profile": "hk_residual_momentum_quality",
        "profile_type": "external_snapshot_scaffold",
        "decision": "stage_after_quality_yield",
        "annualized_return": None,
        "max_drawdown": None,
        "why": "Closest HK analogue to US-style momentum factor selection, but turnover and crash risk must be proven first.",
        "next_action": "Run residual/liquid/composite momentum ablations after the first quality/yield profiles.",
    },
    {
        "rank": 7,
        "profile": "hk_factor_mix_qvlm_risk_parity",
        "profile_type": "external_snapshot_scaffold",
        "decision": "stage_after_single_factor_ablation",
        "annualized_return": None,
        "max_drawdown": None,
        "why": "Diversified QVLM factor mix can reduce single-factor regime risk if factor history and covariance are point-in-time.",
        "next_action": "Prove Q/V/L/M leave-one-out contribution and factor-correlation stress before promotion.",
    },
)

DEPRIORITIZED_LIVE_ENABLEMENT_PROFILES: tuple[dict[str, str], ...] = (
    {
        "profile": "hk_index_mean_reversion",
        "decision": "exclude_from_live_enablement_shortlist",
        "reason": "Full-sample return is close to flat and drawdown/warmup behavior is not competitive despite OOS improvement.",
    },
    {
        "profile": "hk_etf_regime_rotation",
        "decision": "exclude_from_live_enablement_shortlist",
        "reason": "Superseded by hk_high_dividend_low_vol_trend and hk_listed_global_etf_rotation with cleaner promotion evidence.",
    },
    {
        "profile": "snapshot_future_research_long_tail",
        "decision": "exclude_from_live_enablement_shortlist",
        "reason": "Non-curated future-research ideas remain raw research only because data, derivative, shorting, event, or capacity risk is too high.",
    },
)

EVIDENCE_URI_POLICY: dict[str, Any] = build_evidence_uri_policy()
EVIDENCE_FRESHNESS_POLICY: dict[str, Any] = build_evidence_freshness_policy()
HSI_MOMENTUM_METHODOLOGY_URL = "https://www.hsi.com.hk/static/uploads/contents/en/dl_centre/methodologies/IM_hssbisme.pdf"
HSI_SMART_BETA_MOMENTUM_INDEX_URL = "https://www.hsi.com.hk/eng/indexes/all-indexes/hssbism"
HSI_MOMENTUM_RESEARCH_PAPER_URL = (
    "https://www.hsi.com.hk/static/uploads/contents/en/dl_centre/research_paper/20191216T000000.pdf"
)
MSCI_MOMENTUM_INDEXES_URL = "https://www.msci.com/indexes/group/momentum-indexes"
MSCI_HK_MOMENTUM_INDEX_URL = "https://www.msci.com/indexes/index/711028"
MSCI_MOMENTUM_METHODOLOGY_URL = (
    "https://www.msci.com/indexes/documents/methodology/2_MSCI_Momentum_Indexes_Methodology_20250417.pdf"
)
MSCI_HK_LISTED_SOUTHBOUND_MOMENTUM_FACTSHEET_URL = (
    "https://www.msci.com/documents/10199/a79b1588-26c8-5224-d68b-269b256ba22c"
)
MSCI_QUALITY_INDEXES_URL = "https://www.msci.com/indexes/group/quality-indexes"
MSCI_HK_QUALITY_INDEX_URL = "https://www.msci.com/indexes/index/721604"
MSCI_HK_LISTED_SOUTHBOUND_QUALITY_FACTSHEET_URL = (
    "https://www.msci.com/documents/10199/60ebccab-109f-6a16-8451-557498ea39fb"
)
MSCI_MINIMUM_VOLATILITY_INDEXES_URL = "https://www.msci.com/indexes/group/minimum-volatility-indexes/"
MSCI_HK_LISTED_SOUTHBOUND_MIN_VOL_FACTSHEET_URL = (
    "https://www.msci.com/documents/10199/1396fa66-b4bd-40f3-8dfb-0109895d94ac"
)
HSI_RISK_PARITY_FACTOR_MIX_QVLM_FACTSHEET_URL = (
    "https://www.hsi.com.hk/static/uploads/contents/en/dl_centre/factsheets/hssbmfrpe.pdf"
)
HSI_RISK_PARITY_FACTOR_MIX_QVLM_METHODOLOGY_URL = (
    "https://www.hsi.com.hk/static/uploads/contents/en/dl_centre/methodologies/IM_hssbmfrpe.pdf"
)
HSI_EQUAL_WEIGHT_FACTOR_MIX_INDEX_URL = "https://www.hsi.com.hk/eng/indexes/all-indexes/hssbmfew"
MSCI_FACTOR_MIX_A_SERIES_INDEXES_URL = "https://www.msci.com/indexes/factor-indexes/factor-mix-a-series-indexes"
MSCI_HK_FACTOR_MIX_A_SERIES_URL = "https://www.msci.com/indexes/index/705097"
MSCI_HK_FACTOR_MIX_A_SERIES_FACTSHEET_URL = (
    "https://www.msci.com/documents/10199/e56a62f4-3ff6-40a7-a8e6-54a6de8e6763"
)
MSCI_FACTOR_MIX_A_SERIES_METHODOLOGY_URL = (
    "https://www.msci.com/eqb/methodology/meth_docs/MSCI_Factor_Mix_Indexes_Methodology_Apr16.pdf"
)
MSCI_QUALITY_MIX_INDEXES_PAPER_URL = "https://www.msci.com/research-and-insights/paper/the-msci-quality-mix-indexes"
HSI_SCHK_CENTRAL_SOES_FACTOR_METHODOLOGY_URL = (
    "https://www.hsi.com.hk/static/uploads/contents/en/dl_centre/methodologies/IM_hssccsme.pdf"
)
HSI_SCHK_CENTRAL_SOES_METHODOLOGY_URL = (
    "https://www.hsi.com.hk/static/uploads/contents/en/dl_centre/methodologies/IM_hsscsoee.pdf"
)
HSI_SCHK_CENTRAL_SOES_FACTSHEET_URL = (
    "https://www.hsi.com.hk/static/uploads/contents/en/dl_centre/factsheets/hsscsoee.pdf"
)
HSI_SCHK_CENTRAL_SOES_VALUE_FACTSHEET_URL = (
    "https://www.hsi.com.hk/static/uploads/contents/en/dl_centre/factsheets/hssccsve.pdf"
)
HSI_SCHK_CENTRAL_SOES_QUALITY_FACTSHEET_URL = (
    "https://www.hsi.com.hk/static/uploads/contents/en/dl_centre/factsheets/hssccsqe.pdf"
)
SASAC_CENTRAL_SOE_DIRECTORY_URL = "https://www.sasac.gov.cn/n2588045/n27271785/n27271792/index.html"
MOF_CENTRAL_FINANCIAL_SOE_DIRECTORY_RULES_URL = "https://www.mof.gov.cn/zcsjtsgb/gfxwj/202007/t20200713_3583827.htm"
HSI_SCHK_FREE_CASH_FLOW_INDEX_URL = "https://www.hsi.com.hk/eng/indexes/all-indexes/hsscfcf"
HSI_SCHK_FREE_CASH_FLOW_FACTSHEET_URL = (
    "https://www.hsi.com.hk/static/uploads/contents/en/dl_centre/factsheets/hsscfcfe.pdf"
)
HSI_SCHK_FREE_CASH_FLOW_METHODOLOGY_URL = (
    "https://www.hsi.com.hk/static/uploads/contents/en/dl_centre/methodologies/IM_hsscfcfe.pdf"
)
SP_ACCESS_HK_FCF_50_INDEX_URL = (
    "https://www.spglobal.com/spdji/en/indices/dividends-factors/"
    "sp-access-hong-kong-free-cash-flow-50-index/"
)
SP_ACCESS_HK_FCF_50_METHODOLOGY_URL = (
    "https://www.spglobal.com/spdji/en/documents/methodologies/methodology-sp-access-hk-fcf-50-index.pdf"
)
HKEX_STOCK_CONNECT_STATISTICS_URL = "https://www.hkex.com.hk/mutual-market/stock-connect/statistics?sc_lang=en"
HKEX_STOCK_CONNECT_HISTORICAL_DAILY_URL = (
    "https://www.hkex.com.hk/Mutual-Market/Stock-Connect/Statistics/Historical-Daily?sc_lang=en"
)
HKEX_SOUTHBOUND_CCASS_SHAREHOLDING_URL = "https://www3.hkexnews.hk/sdw/search/mutualmarket.aspx?t=hk"
HKEX_STOCK_CONNECT_ELIGIBLE_SECURITIES_URL = (
    "https://www.hkex.com.hk/mutual-market/stock-connect/eligible-stocks/view-all-eligible-securities?sc_lang=en"
)
HKEX_ETF_CONNECT_INCLUSION_URL = (
    "https://www.hkex.com.hk/Mutual-Market/Stock-Connect/Reference-Materials/Inclusion-of-ETFs-in-Stock-Connect?sc_lang=en"
)
HKEX_STOCK_CONNECT_DATA_DISSEMINATION_URL = (
    "https://www.hkex.com.hk/News/Market-Communications/2024/2404122news?sc_lang=en"
)
SOUTHBOUND_FLOW_RETURN_PREDICTABILITY_SSRN_URL = "https://papers.ssrn.com/sol3/papers.cfm?abstract_id=5128472"
HSI_AH_PREMIUM_INDEX_URL = "https://www.hsi.com.hk/eng/indexes/all-indexes/ahpremium"
HSI_CHINA_AH_INDEX_SERIES_URL = "https://www.hsi.com.hk/eng/indexes/all-indexes/chinaah"
HSI_AH_PREMIUM_FACTSHEET_URL = "https://www.hsi.com.hk/static/uploads/contents/en/dl_centre/factsheets/ahpremiume.pdf"
HSI_AH_PREMIUM_INDEX_FLASH_URL = (
    "https://www.hsi.com.hk/static/uploads/contents/en/dl_centre/index_flash/20240124T000000.pdf"
)
HSI_AH_SMART_INDEX_BLOG_URL = "https://www.hsi.com.hk/static/uploads/contents/en/dl_centre/blog/20210914T000000.pdf"
SSE_SH_HK_AH_PREMIUM_METHODOLOGY_URL = (
    "https://english.sse.com.cn/indices/indices/list/indexmethods/c/H50066_h50066hbooken_EN.pdf"
)
HSI_INDEX_METHODOLOGY_GUIDE_URL = (
    "https://www.hsi.com.hk/static/uploads/contents/en/dl_centre/methodologies/index_methodology_guide_e.pdf"
)
HSI_INDEX_OPERATION_GUIDE_URL = (
    "https://www.hsi.com.hk/static/uploads/contents/en/dl_centre/methodologies/index_operation_guide_e.pdf"
)
HSI_INDEX_REBALANCE_SCHEDULE_URL = "https://www.hsi.com.hk/static/uploads/contents/en/products/is_update.xlsx"
HSI_INDEX_NEXT_REVIEW_NOTICE_20260102_URL = (
    "https://www.hsi.com.hk/static/uploads/contents/en/news/indexChgNotice/20260102T163000.pdf"
)
HSI_INDEX_REVIEW_RESULT_20260213_URL = (
    "https://www.hsi.com.hk/static/uploads/contents/en/news/pressRelease/20260213T174500.pdf"
)
HSI_INDEX_REVIEW_RESULT_20260522_URL = (
    "https://www.hsi.com.hk/static/uploads/contents/en/news/pressRelease/20260522T174500.pdf"
)
HKEX_CLOSING_AUCTION_SESSION_FAQ_URL = (
    "https://www.hkex.com.hk/Global/Exchange/FAQ/Securities-Market/Trading/CAS?sc_lang=en"
)
HKEX_TRADING_MECHANISM_URL = (
    "https://www.hkex.com.hk/Services/Trading/Securities/Overview/Trading-Mechanism?sc_lang=en"
)
GLOBAL_X_HANG_SENG_HIGH_DIVIDEND_ETF_URL = (
    "https://www.globalxetfs.com.hk/funds/hang-seng-high-dividend-yield-etf/"
)
HSI_HIGH_DIVIDEND_YIELD_INDEX_URL = "https://www.hsi.com.hk/eng/indexes/all-indexes/hshdyi"
HSI_HIGH_DIVIDEND_YIELD_FACTSHEET_URL = (
    "https://www.hsi.com.hk/static/uploads/contents/en/dl_centre/factsheets/hshdyie.pdf"
)
HSI_HIGH_DIVIDEND_YIELD_METHODOLOGY_URL = (
    "https://www.hsi.com.hk/static/uploads/contents/en/dl_centre/methodologies/IM_hshdyie.pdf"
)
SSGA_SPDR_GOLD_SHARES_2840_URL = "https://www.ssga.com/hk/en/institutional/etfs/funds/spdr-gold-shares-2840"
SSGA_SPDR_GOLD_SHARES_2840_FACTSHEET_URL = (
    "https://www.ssga.com/library-content/products/factsheets/etfs/apac/factsheet-hk-en-2840.pdf"
)
SPDR_GOLD_SHARES_HK_FINANCIAL_INFO_URL = "https://www.spdrgoldshares.com/hong-kong/english/financial-information/"
TRAHK_PRODUCT_URL = "https://www.trahk.com.hk/en-hk/trahk-fund/"
CSOP_A50_ETF_URL = "https://www.csopasset.com/en/products/china_A50_etf.php"
CHINAAMC_CSI300_ETF_URL = "https://www.chinaamc.com.hk/product/chinaamc-csi-300-index-etf-3188-hk-83188-hk/"
CSOP_HANG_SENG_TECH_ETF_URL = "https://csop.onlineminisite.com/thematicetf/en/3033.php"
ISHARES_NASDAQ100_HKEX_IFP_URL = "https://ifp.hkex.com.hk/fund/BHG161"
BLACKROCK_ISHARES_NASDAQ100_ETF_URL = (
    "https://www.blackrock.com/hk/en/products/282238/ishares-nasdaq-100-etf?switchLocale=Y"
)
SAMSUNG_CRUDE_OIL_FUTURES_ETF_URL = "https://www.samsungetfhk.com/en/product/3175/"

RUNTIME_RESEARCH_EVIDENCE_URLS: dict[str, tuple[str, ...]] = {
    HK_HIGH_DIVIDEND_LOW_VOL_TREND_PROFILE: (
        "docs/research/hk_high_dividend_low_vol_trend.md",
        GLOBAL_X_HANG_SENG_HIGH_DIVIDEND_ETF_URL,
        HSI_HIGH_DIVIDEND_YIELD_INDEX_URL,
        HSI_HIGH_DIVIDEND_YIELD_FACTSHEET_URL,
        HSI_HIGH_DIVIDEND_YIELD_METHODOLOGY_URL,
        SSGA_SPDR_GOLD_SHARES_2840_URL,
        SSGA_SPDR_GOLD_SHARES_2840_FACTSHEET_URL,
        SPDR_GOLD_SHARES_HK_FINANCIAL_INFO_URL,
        "https://www.hkex.com.hk/products/securities/exchange-traded-products/overview?sc_lang=en",
        "https://www.hkex.com.hk/Products/Securities/Exchange-Traded-Products/Market-Makers/Overview?sc_lang=en",
        HKEX_ETF_CONNECT_INCLUSION_URL,
        HKEX_STOCK_CONNECT_ELIGIBLE_SECURITIES_URL,
        HKEX_STOCK_CONNECT_STATISTICS_URL,
        HKEX_STOCK_CONNECT_HISTORICAL_DAILY_URL,
        "https://www.hkex.com.hk/-/media/HKEX-Market/Mutual-Market/Stock-Connect/Reference-Materials/Inclusion-of-ETFs-in-Stock-Connect/Inclusion_of_ETFs_in_Stock_Connect_Useful_Information_for_Issuers_Eng.pdf",
        "https://www.ird.gov.hk/eng/faq/ETFs.htm",
        "https://www.hkex.com.hk/News/Market-Communications/2015/150204news",
        "https://www.hkex.com.hk/Services/Rules-and-Forms-and-Fees/Fees/Securities-%28Hong-Kong%29/Trading/Transaction?sc_lang=en",
    ),
    HK_LISTED_GLOBAL_ETF_ROTATION_PROFILE: (
        "docs/research/hk_listed_global_etf_rotation.md",
        TRAHK_PRODUCT_URL,
        CSOP_A50_ETF_URL,
        CHINAAMC_CSI300_ETF_URL,
        CSOP_HANG_SENG_TECH_ETF_URL,
        ISHARES_NASDAQ100_HKEX_IFP_URL,
        BLACKROCK_ISHARES_NASDAQ100_ETF_URL,
        GLOBAL_X_HANG_SENG_HIGH_DIVIDEND_ETF_URL,
        SSGA_SPDR_GOLD_SHARES_2840_URL,
        SSGA_SPDR_GOLD_SHARES_2840_FACTSHEET_URL,
        SPDR_GOLD_SHARES_HK_FINANCIAL_INFO_URL,
        SAMSUNG_CRUDE_OIL_FUTURES_ETF_URL,
        "https://www.hkex.com.hk/products/securities/exchange-traded-products/overview?sc_lang=en",
        "https://www.hkex.com.hk/Products/Securities/Exchange-Traded-Products/Market-Makers/Overview?sc_lang=en",
        HKEX_ETF_CONNECT_INCLUSION_URL,
        HKEX_STOCK_CONNECT_ELIGIBLE_SECURITIES_URL,
        HKEX_STOCK_CONNECT_STATISTICS_URL,
        HKEX_STOCK_CONNECT_HISTORICAL_DAILY_URL,
        "https://www.hkex.com.hk/-/media/HKEX-Market/Mutual-Market/Stock-Connect/Reference-Materials/Inclusion-of-ETFs-in-Stock-Connect/Inclusion_of_ETFs_in_Stock_Connect_Useful_Information_for_Issuers_Eng.pdf",
        "https://www.ird.gov.hk/eng/faq/ETFs.htm",
        "https://www.hkex.com.hk/News/Market-Communications/2015/150204news",
        "https://www.hkex.com.hk/Services/Rules-and-Forms-and-Fees/Fees/Securities-%28Hong-Kong%29/Trading/Transaction?sc_lang=en",
    ),
}

RUNTIME_PROFILE_NOTES: dict[str, tuple[str, ...]] = {
    HK_HIGH_DIVIDEND_LOW_VOL_TREND_PROFILE: (
        "Preferred lower-drawdown first HK runtime profile; keep dry-run until evidence pack passes.",
        "Managed symbols are limited to 02840 and 03110, so platform validation should be simpler than broad ETF rotation.",
        "03110 evidence must include current Global X product documents, Hang Seng High Dividend Yield Index methodology, NAV/iNAV, distribution and capital-distribution risk policy, and high-dividend concentration/yield-trap review.",
        "02840 evidence must include current SSGA/SPDR Gold Shares product documents, NAV/iNAV, tracking difference, multi-counter currency, USD creation/redemption, and single-commodity trust/storage-risk review.",
        "If either ETF is routed through Stock Connect / Southbound ETF paths, evidence must include ETF Connect eligibility or sell-only status, Southbound turnover/fund-flow trend, broker route availability, and cross-boundary settlement/holiday review.",
    ),
    HK_LISTED_GLOBAL_ETF_ROTATION_PROFILE: (
        "Broader ETF rotation candidate with higher universe complexity; start with reduced capital if promoted after evidence.",
        "03175 is a crude-oil futures ETF and must be removed if product permission, spread, or suitability checks fail.",
        "All eight ETF symbols require issuer product-document, NAV/iNAV, underlying-index/reference-asset, tracking-difference, multi-counter, market-maker, fee/tax, and broker-permission evidence before dry-run removal.",
        "A-share sleeves 02822 and 03188 require RQFII/Stock Connect, RMB base-currency, A-share trading-hour/price-band, cross-market holiday, FX, and premium/discount review.",
        "Overseas/commodity sleeves 02834, 02840, and 03175 require Nasdaq trading-hour, gold trust, futures-roll/margin/curve, USD creation/redemption, and complex-product suitability review.",
        "ETF Connect / Southbound ETF route evidence must prove current eligibility or sell-only status, daily turnover/fund-flow trend, broker buy-order availability, and cross-boundary settlement/holiday handling before dry-run removal.",
        "ETF premium/discount and tracking-quality overlay evidence should prove NAV/iNAV freshness, tracking-difference history, spread/depth, market-maker coverage, product-structure risk, and same-universe ETF-rotation ablation before changing live weights.",
    ),
}

RESEARCH_ONLY_PROFILES: dict[str, dict[str, object]] = {
    "hk_index_mean_reversion": {
        "display_name": "HK Index Mean Reversion",
        "profile_type": "research_backtest_only",
        "reason": "Research backtest kept this outside runtime catalog; not enough promotion evidence.",
        "research_evidence_urls": ("docs/research/hk_index_mean_reversion.md",),
        "required_next_evidence": (
            "robust_walk_forward_result_across_hsi_and_hstech_cycles",
            "cost_model_after_hk_etf_spreads_and_lot_sizes",
            "proof_strategy_not_overfit_to_range_bound_period",
        ),
    },
    "hk_etf_regime_rotation": {
        "display_name": "HK ETF Regime Rotation",
        "profile_type": "research_backtest_only",
        "reason": "Promising but train-period evidence was not strong enough; simpler promoted variants exist.",
        "research_evidence_urls": ("docs/research/hk_etf_regime_rotation.md",),
        "required_next_evidence": (
            "positive_train_and_oos_walk_forward_periods",
            "universe_cleaning_for_short_history_etfs",
            "comparison_against_runtime_enabled_etf_profiles",
        ),
    },
}


SNAPSHOT_RESEARCH_EVIDENCE_URLS: dict[str, tuple[str, ...]] = {
    "hk_low_vol_dividend_quality": (
        "../HkEquitySnapshotPipelines/docs/research/hk_snapshot_strategy_candidates.md",
        "https://www.spglobal.com/market-intelligence/en/news-insights/research/forecast-dividend-yield-strategy-outperforms-hong-kong-sar",
        "https://www.hsi.com.hk/static/uploads/contents/en/dl_centre/factsheets/hslvie.pdf",
        "https://www.hsi.com.hk/static/uploads/contents/en/dl_centre/factsheets/hshdyie.pdf",
        "https://www.hsi.com.hk/eng/indexes/all-indexes/hshylv",
        "https://www.hsi.com.hk/static/uploads/contents/en/dl_centre/factsheets/hshylve.pdf",
        "https://www.hsi.com.hk/static/uploads/contents/en/dl_centre/methodologies/IM_hshylve.pdf",
        "https://www.hsi.com.hk/eng/indexes/all-indexes/hsschys",
        "https://www.hsi.com.hk/static/uploads/contents/en/dl_centre/factsheets/hsschyse.pdf",
        "https://www.hsi.com.hk/static/uploads/contents/en/dl_centre/methodologies/IM_hsschkye.pdf",
        "https://www.hsi.com.hk/static/uploads/contents/en/dl_centre/research_paper/20231214T000000.pdf",
        "https://www.spglobal.com/spdji/en/education/article/navigating-dividend-yield-in-the-hong-kong-market-the-sp-access-hong-kong-low-volatility-high-dividend-index",
    ),
    "hk_shareholder_yield_quality": (
        "../HkEquitySnapshotPipelines/docs/research/hk_snapshot_strategy_candidates.md",
        "https://www.hkex.com.hk/-/media/HKEX-Market/Listing/Rules-and-Guidance/Other-Resources/Listed-Issuers/LIR-Newsletter/newsletter_202506.pdf",
        "https://www3.hkexnews.hk/reports/sharerepur/sbn.asp",
        "https://en-rules.hkex.com.hk/rulebook/9-repurchase-securities-and-treasury-shares",
        "https://en-rules.hkex.com.hk/entiresection/498",
        "https://www.hkex.com.hk/News/Regulatory-Announcements/2024/240412news?sc_lang=en",
        "https://www.hkex.com.hk/Listing/Education-Centre/Listed-Issuers/Share-Repurchase-and-Treasury-Shares?sc_lang=en",
        "https://www.spglobal.com/market-intelligence/en/news-insights/research/forecast-dividend-yield-strategy-outperforms-hong-kong-sar",
        "https://www.spglobal.com/spdji/en/indices/dividends-factors/sp-access-hong-kong-dividend-free-cash-flow-index/",
    ),
    "hk_free_cash_flow_quality": (
        "../HkEquitySnapshotPipelines/docs/research/hk_snapshot_strategy_candidates.md",
        HSI_SCHK_FREE_CASH_FLOW_INDEX_URL,
        HSI_SCHK_FREE_CASH_FLOW_FACTSHEET_URL,
        HSI_SCHK_FREE_CASH_FLOW_METHODOLOGY_URL,
        SP_ACCESS_HK_FCF_50_INDEX_URL,
        SP_ACCESS_HK_FCF_50_METHODOLOGY_URL,
        "https://www.spglobal.com/spdji/en/indices/dividends-factors/sp-access-hong-kong-dividend-free-cash-flow-index/",
    ),
    "hk_residual_momentum_quality": (
        "../HkEquitySnapshotPipelines/docs/research/hk_snapshot_strategy_candidates.md",
        HSI_MOMENTUM_METHODOLOGY_URL,
        HSI_SMART_BETA_MOMENTUM_INDEX_URL,
        HSI_MOMENTUM_RESEARCH_PAPER_URL,
        MSCI_MOMENTUM_INDEXES_URL,
        MSCI_HK_MOMENTUM_INDEX_URL,
        MSCI_MOMENTUM_METHODOLOGY_URL,
        MSCI_HK_LISTED_SOUTHBOUND_MOMENTUM_FACTSHEET_URL,
    ),
    "hk_liquid_momentum_quality": (
        "../HkEquitySnapshotPipelines/docs/research/hk_snapshot_strategy_candidates.md",
        HSI_MOMENTUM_METHODOLOGY_URL,
        HSI_SMART_BETA_MOMENTUM_INDEX_URL,
        HSI_MOMENTUM_RESEARCH_PAPER_URL,
        MSCI_MOMENTUM_INDEXES_URL,
        MSCI_HK_MOMENTUM_INDEX_URL,
        MSCI_MOMENTUM_METHODOLOGY_URL,
        MSCI_HK_LISTED_SOUTHBOUND_MOMENTUM_FACTSHEET_URL,
        "https://www.hsi.com.hk/static/uploads/contents/en/dl_centre/methodologies/IM_hsscsqe.pdf",
    ),
    "hk_central_soe_value_quality_select": (
        "../HkEquitySnapshotPipelines/docs/research/hk_snapshot_strategy_candidates.md",
        HSI_SCHK_CENTRAL_SOES_FACTOR_METHODOLOGY_URL,
        HSI_SCHK_CENTRAL_SOES_METHODOLOGY_URL,
        HSI_SCHK_CENTRAL_SOES_FACTSHEET_URL,
        HSI_SCHK_CENTRAL_SOES_VALUE_FACTSHEET_URL,
        HSI_SCHK_CENTRAL_SOES_QUALITY_FACTSHEET_URL,
        "https://www.hsi.com.hk/solutions/factor-indexes/",
        HKEX_STOCK_CONNECT_ELIGIBLE_SECURITIES_URL,
        SASAC_CENTRAL_SOE_DIRECTORY_URL,
        "https://en.sasac.gov.cn/directorynames.html",
        MOF_CENTRAL_FINANCIAL_SOE_DIRECTORY_RULES_URL,
    ),
    "hk_composite_factor_quality_value_momentum": (
        "../HkEquitySnapshotPipelines/docs/research/hk_snapshot_strategy_candidates.md",
        HSI_MOMENTUM_METHODOLOGY_URL,
        HSI_SMART_BETA_MOMENTUM_INDEX_URL,
        HSI_MOMENTUM_RESEARCH_PAPER_URL,
        MSCI_MOMENTUM_INDEXES_URL,
        MSCI_HK_MOMENTUM_INDEX_URL,
        MSCI_MOMENTUM_METHODOLOGY_URL,
        MSCI_HK_LISTED_SOUTHBOUND_MOMENTUM_FACTSHEET_URL,
        "https://www.hsi.com.hk/solutions/factor-indexes/",
        "https://www.hsi.com.hk/static/uploads/contents/en/dl_centre/methodologies/IM_hsscsqe.pdf",
    ),
    "hk_factor_mix_qvlm_risk_parity": (
        "../HkEquitySnapshotPipelines/docs/research/hk_snapshot_strategy_candidates.md",
        HSI_RISK_PARITY_FACTOR_MIX_QVLM_FACTSHEET_URL,
        HSI_RISK_PARITY_FACTOR_MIX_QVLM_METHODOLOGY_URL,
        HSI_EQUAL_WEIGHT_FACTOR_MIX_INDEX_URL,
        "https://www.hsi.com.hk/static/uploads/contents/en/dl_centre/methodologies/IM_hsscsqe.pdf",
        "https://www.hsi.com.hk/solutions/factor-indexes/",
        MSCI_FACTOR_MIX_A_SERIES_INDEXES_URL,
        MSCI_HK_FACTOR_MIX_A_SERIES_URL,
        MSCI_HK_FACTOR_MIX_A_SERIES_FACTSHEET_URL,
        MSCI_FACTOR_MIX_A_SERIES_METHODOLOGY_URL,
        MSCI_QUALITY_MIX_INDEXES_PAPER_URL,
    ),
    "hk_quality_growth_low_volatility": (
        "../HkEquitySnapshotPipelines/docs/research/hk_snapshot_strategy_candidates.md",
        "https://www.hsi.com.hk/static/uploads/contents/en/dl_centre/factsheets/hsqglve.pdf",
        "https://www.hsi.com.hk/static/uploads/contents/en/dl_centre/methodologies/IM_hsqglve.pdf",
        "https://www.hsi.com.hk/static/uploads/contents/en/dl_centre/methodologies/IM_hssbisve.pdf",
        "https://www.hsi.com.hk/solutions/factor-indexes/",
        MSCI_QUALITY_INDEXES_URL,
        MSCI_HK_QUALITY_INDEX_URL,
        MSCI_HK_LISTED_SOUTHBOUND_QUALITY_FACTSHEET_URL,
        MSCI_MINIMUM_VOLATILITY_INDEXES_URL,
        MSCI_HK_LISTED_SOUTHBOUND_MIN_VOL_FACTSHEET_URL,
    ),
    "hk_southbound_flow_momentum": (
        "../HkEquitySnapshotPipelines/docs/research/hk_snapshot_strategy_candidates.md",
        HKEX_STOCK_CONNECT_STATISTICS_URL,
        HKEX_STOCK_CONNECT_HISTORICAL_DAILY_URL,
        HKEX_SOUTHBOUND_CCASS_SHAREHOLDING_URL,
        HKEX_STOCK_CONNECT_ELIGIBLE_SECURITIES_URL,
        "https://www.hkex.com.hk/Mutual-Market/Connect-Hub/Stock-Connect-White-Paper?sc_lang=en",
        HKEX_STOCK_CONNECT_DATA_DISSEMINATION_URL,
        SOUTHBOUND_FLOW_RETURN_PREDICTABILITY_SSRN_URL,
    ),
    "hk_ah_premium_relative_value": (
        "../HkEquitySnapshotPipelines/docs/research/hk_snapshot_strategy_candidates.md",
        HSI_AH_PREMIUM_INDEX_URL,
        HSI_CHINA_AH_INDEX_SERIES_URL,
        HSI_AH_PREMIUM_FACTSHEET_URL,
        HSI_AH_PREMIUM_INDEX_FLASH_URL,
        HSI_AH_SMART_INDEX_BLOG_URL,
        "https://www.hsi.com.hk/static/uploads/contents/en/dl_centre/methodologies/index_operation_guide_e.pdf",
        SSE_SH_HK_AH_PREMIUM_METHODOLOGY_URL,
    ),
    "hk_index_rebalance_event": (
        "../HkEquitySnapshotPipelines/docs/research/hk_snapshot_strategy_candidates.md",
        HSI_INDEX_METHODOLOGY_GUIDE_URL,
        HSI_INDEX_OPERATION_GUIDE_URL,
        HSI_INDEX_REBALANCE_SCHEDULE_URL,
        HSI_INDEX_NEXT_REVIEW_NOTICE_20260102_URL,
        HSI_INDEX_REVIEW_RESULT_20260213_URL,
        HSI_INDEX_REVIEW_RESULT_20260522_URL,
        HKEX_CLOSING_AUCTION_SESSION_FAQ_URL,
        HKEX_TRADING_MECHANISM_URL,
    ),
}

SNAPSHOT_SCAFFOLD_NOTES: dict[str, tuple[str, ...]] = {
    "hk_low_vol_dividend_quality": (
        "First snapshot candidate because HK low-volatility/dividend evidence is strong and turnover can be controlled.",
        "S&P forecast-dividend-yield research must be treated as a forward-yield candidate only after point-in-time estimate history, stale-revision controls, and trailing-yield ablation pass.",
        "HSHYLV-style evidence adds Southbound eligibility, three-year cash-dividend records, payout-ratio bounds, and price-crash screens to the live-enable source audit.",
        "HSSCHYS evidence adds large/mid-cap shortlisting, one-year high-volatility exclusion, and financial-soundness screens before platform selection.",
    ),
    "hk_shareholder_yield_quality": (
        "First snapshot candidate because HKEX buyback disclosure and dividend yield evidence support a low-turnover quality style.",
        "Forward dividend-yield estimates must be ablated against trailing dividend yield and stress-tested for estimate cuts plus financials-sector concentration before platform selection.",
        "HKEX treasury-share rules require next-day repurchase returns, cancellation/resale treatment, moratorium/blackout controls, and post-buyback financing review before platform selection.",
    ),
    "hk_free_cash_flow_quality": (
        "First snapshot candidate because FCF yield has HK/Southbound index support but needs audited fundamentals history.",
        "HSI/S&P FCF evidence requires auditable FCF formula lineage, EV market-cap/debt/cash/FX inputs, point-in-time reporting dates, restatement controls, sector caps, and financial/real-estate/negative-FCF exceptions before platform selection.",
    ),
    "hk_central_soe_value_quality_select": (
        "Central-SOE value-quality scaffold is active, but remains behind factor-mix and first quality/yield candidates until ownership provenance, concentration, and policy-event stresses pass.",
        "Platform selection requires SASAC/MOF central-SOE source-list effective dates and effective-date drift, largest-shareholder look-through chain audit, HKEX Southbound point-in-time eligibility, and HSI value/quality factor-index reconciliation.",
        "Platform selection must also reconcile HSI Z-score standardisation, missing-measure averaging, 40% factor screening with buffer rules, and 5% factor-index / 10% base-index capping lineage before dry-run removal.",
        "Dry-run removal must stress parent restructurings, source-list reclassifications, factor-screen/cap turnover spikes, Southbound eligibility removals, public-float pressure, connected transactions, sanctions, dividend cuts, and financials/energy/telecom/property concentration.",
    ),
    "hk_residual_momentum_quality": (
        "Momentum scaffold should remain behind low-turnover quality styles until residual-factor turnover and costs are proven.",
        "Platform selection requires HSI close-to-high descriptor and MSCI 6/12-month one-month-skip risk-adjusted momentum reconciliation, model-fit-window audit, sector neutralization, turnover buffers, and momentum-crash controls.",
    ),
    "hk_liquid_momentum_quality": (
        "Liquid price-momentum scaffold is the simpler fallback, but it must reconcile 52-week-high, 12-1 price momentum, and MSCI-style 6/12-month risk-adjusted momentum before platform selection.",
        "Hold buffers, liquidity caps, sector caps, suspension handling, and high-beta reversal stress are mandatory before dry-run removal.",
    ),
    "hk_composite_factor_quality_value_momentum": (
        "Composite QVM scaffold must prove its momentum sleeve adds excess return beyond quality/value/low-volatility on the same universe.",
        "Platform selection requires factor formula lineage, winsorization/neutralization audit, MSCI/HSI momentum descriptor reconciliation, and factor-turnover capacity controls.",
    ),
    "hk_quality_growth_low_volatility": (
        "Quality-growth low-volatility scaffold is active, but remains behind first quality/yield candidates until factor ablation and production fundamentals pass.",
        "Platform selection requires HSI QGLV four-component score lineage for ROE, accruals ratio, cash-flow-to-debt, and Growth in ROA adjusted by P/B, including winsorized z-scores, Financials-only handling, negative-equity treatment, and missing-factor policy.",
        "Platform selection must also reconcile MSCI quality ROE / stable-earnings / low-leverage descriptors, MSCI HK-listed Southbound Quality evidence, HSI low-volatility quality screens, minimum-volatility optimizer constraints, cash-conversion quality-trap controls, and real-estate/financial concentration stress.",
    ),
    "hk_factor_mix_qvlm_risk_parity": (
        "Risk-parity QVLM scaffold is active, but remains behind first quality/yield candidates until factor-volatility provenance and same-universe ablation pass.",
        "Platform selection requires HSI QVLM parent universe, Quality/Value/Low Volatility/Momentum component-index return history, 12% capping lineage, risk-parity weight formula and covariance history, HSI equal-weight factor-mix benchmark comparison, MSCI equal-weight Q/V/L component and capped-methodology controls, component-overlap / cap-induced turnover, turnover/capacity, and factor-correlation breakdown stress.",
    ),
    "hk_southbound_flow_momentum": (
        "Southbound flow scaffold is HK-specific research evidence, but platform selection requires audited HKEX historical daily turnover, top-10 turnover, CCASS shareholding, point-in-time eligibility, and market-data dissemination controls.",
        "Any vendor southbound-flow feed must be reconciled against raw HKEX/CCASS records and tested for signal decay, holiday gaps, CCASS reporting lag, and crowding reversal before dry-run removal.",
    ),
    "hk_ah_premium_relative_value": (
        "A/H premium scaffold is a long-only H-share valuation overlay unless A-share access, shorting, settlement, and FX constraints are explicitly approved.",
        "Platform selection requires AH pair/index-constituent history, A/H close alignment, AH price-ratio formula lineage, FX inputs, AH Smart switch-threshold comparison, and extreme-premium false-reversal stress.",
    ),
    "hk_index_rebalance_event": (
        "Index-rebalance event scaffold must ingest official HSI rebalancing schedules, next-review notices, and review-result press releases before platform selection.",
        "Platform selection requires HSI methodology / operation-guide versioning, schedule-file version / effective-date history, next-review notice scope, review-result press-release timestamps, constituent weight / pro-forma records, and add/delete event labels.",
        "Dry-run removal must ablate market-on-close versus next-open execution and pro-forma-weighted versus equal-weight event trades.",
        "Platform selection also requires announcement-to-effective timestamps, fast-entry/suspension/buffer-rule exception handling, CAS / market-on-close execution controls for random-close, two-stage price-limit, order-rejection, passive-flow imbalance, and crowding/slippage evidence.",
    ),
}


def build_snapshot_future_research_live_enablement_policy() -> dict[str, Any]:
    return {
        "required": True,
        "policy_version": SNAPSHOT_FUTURE_RESEARCH_LIVE_ENABLEMENT_POLICY_VERSION,
        "source_repository": "HkEquitySnapshotPipelines",
        "source_matrix_field": "future_research_backlog.future_research_live_enablement_policy",
        "live_enablement_allowed": False,
        "candidate_order": list(SNAPSHOT_FUTURE_RESEARCH_CANDIDATES),
        "curated_candidate_order": list(SNAPSHOT_FUTURE_RESEARCH_CURATED_CANDIDATES),
        "deprioritized_candidate_order": list(SNAPSHOT_FUTURE_RESEARCH_DEPRIORITIZED_CANDIDATES),
        "required_pre_scaffold_gates": list(SNAPSHOT_FUTURE_RESEARCH_PRE_SCAFFOLD_GATES),
        "required_reject_criteria": [
            "mutating_existing_snapshot_contract_in_place",
            "using_sample_artifacts_as_production_evidence",
            "missing_same_universe_ablation_or_walk_forward_evidence",
            "missing_platform_dry_run_order_preview_or_operator_approval",
        ],
        "description": (
            "Platform live-enable tooling must keep externally researched, non-scaffolded HK snapshot ideas "
            "non-selectable until "
            "the snapshot repository adds a new profile contract, candidate-specific source-audit policy, "
            "same-universe ablation, walk-forward evidence, artifact provenance, dry-run order preview, "
            "bilingual notifications, rollout controls, and operator approval."
        ),
    }


def build_curated_live_enablement_strategy_ranking() -> dict[str, Any]:
    return {
        "ranking_version": CURATED_LIVE_ENABLEMENT_STRATEGY_RANKING_VERSION,
        "selection_scope": "runtime_profiles_and_snapshot_scaffolds_only",
        "live_enablement_allowed_without_evidence": False,
        "max_allowed_drawdown": 0.30,
        "ranking": [dict(item) for item in CURATED_LIVE_ENABLEMENT_STRATEGY_RANKING],
        "deprioritized_profiles": [dict(item) for item in DEPRIORITIZED_LIVE_ENABLEMENT_PROFILES],
        "future_research_curated_candidate_order": list(SNAPSHOT_FUTURE_RESEARCH_CURATED_CANDIDATES),
        "future_research_deprioritized_candidate_order": list(SNAPSHOT_FUTURE_RESEARCH_DEPRIORITIZED_CANDIDATES),
        "notes": [
            "The ranking is the live-enable work queue, not an investment recommendation.",
            "Historical raw research candidates remain documented for auditability but are excluded from the live-enable shortlist.",
            "Every promoted profile must still pass the runtime evidence validator, <=30% drawdown gate, dry-run order preview, bilingual notification, and operator approval.",
        ],
    }


@dataclass(frozen=True)
class LiveEnablementRow:
    profile: str
    display_name: str
    profile_type: str
    selectable_by_platform: bool
    runtime_enabled: bool
    live_enablement_gate: str
    supported_platforms: tuple[str, ...]
    benchmark: str | None
    evidence_commands: tuple[str, ...]
    required_evidence: tuple[str, ...]
    research_evidence_urls: tuple[str, ...]
    notes: tuple[str, ...]

    def as_dict(self) -> dict[str, Any]:
        return {
            "profile": self.profile,
            "display_name": self.display_name,
            "profile_type": self.profile_type,
            "selectable_by_platform": self.selectable_by_platform,
            "runtime_enabled": self.runtime_enabled,
            "live_enablement_gate": self.live_enablement_gate,
            "supported_platforms": list(self.supported_platforms),
            "benchmark": self.benchmark,
            "evidence_commands": list(self.evidence_commands),
            "required_evidence": list(self.required_evidence),
            "research_evidence_urls": list(self.research_evidence_urls),
            "backtest_validation_policy": build_backtest_validation_policy(),
            "evidence_uri_policy": EVIDENCE_URI_POLICY,
            "evidence_freshness_policy": EVIDENCE_FRESHNESS_POLICY,
            "execution_capacity_policy": build_execution_capacity_policy(self.profile),
            "dry_run_order_preview_policy": build_dry_run_order_preview_policy(),
            "rollout_risk_policy": build_rollout_risk_policy(),
            "runtime_etf_product_policy": build_runtime_etf_product_policy(),
            "runtime_market_data_policy": build_runtime_market_data_policy(),
            "notification_audit_policy": build_notification_audit_policy(RUNTIME_DRY_RUN_NOTIFICATION_EVENT_TYPE),
            "notes": list(self.notes),
        }


def _dedupe(items: tuple[str, ...]) -> tuple[str, ...]:
    return tuple(dict.fromkeys(items))


def _runtime_row(profile: str) -> LiveEnablementRow:
    definition = get_strategy_definition(profile)
    metadata = get_strategy_metadata(profile)
    thresholds = PROFILE_LIVE_ENABLEMENT_THRESHOLDS[profile]
    threshold_evidence = tuple(f"{key}={value}" for key, value in sorted(thresholds.items()))
    snapshot_evidence = (
        (
            "feature_snapshot_artifact_pack_validation",
            "feature_snapshot_manifest_contract_version_matched",
            "feature_snapshot_point_in_time_lineage_verified",
        )
        if profile in get_snapshot_backed_profiles()
        else ()
    )
    evidence_commands = tuple(
        RUNTIME_EVIDENCE_TEMPLATE_COMMAND.replace("<profile>", profile).replace("<platform>", platform)
        for platform in sorted(definition.supported_platforms)
    )
    return LiveEnablementRow(
        profile=profile,
        display_name=metadata.display_name,
        profile_type="runtime_snapshot_backed"
        if profile in get_snapshot_backed_profiles()
        else "runtime_market_history",
        selectable_by_platform=True,
        runtime_enabled=profile in get_runtime_enabled_profiles(),
        live_enablement_gate=RUNTIME_LIVE_GATE,
        supported_platforms=tuple(sorted(definition.supported_platforms)),
        benchmark=metadata.benchmark,
        evidence_commands=evidence_commands,
        required_evidence=_dedupe(
            tuple(REQUIRED_LIVE_EVIDENCE_FIELDS)
            + snapshot_evidence
            + COMMON_PLATFORM_EVIDENCE_REQUIREMENTS
            + threshold_evidence
        ),
        research_evidence_urls=RUNTIME_RESEARCH_EVIDENCE_URLS.get(
            profile,
            SNAPSHOT_RESEARCH_EVIDENCE_URLS.get(profile, ()),
        ),
        notes=RUNTIME_PROFILE_NOTES.get(profile, SNAPSHOT_SCAFFOLD_NOTES.get(profile, ())),
    )


def _research_only_row(profile: str) -> LiveEnablementRow:
    info = RESEARCH_ONLY_PROFILES[profile]
    return LiveEnablementRow(
        profile=profile,
        display_name=str(info["display_name"]),
        profile_type=str(info["profile_type"]),
        selectable_by_platform=False,
        runtime_enabled=False,
        live_enablement_gate=RESEARCH_ONLY_GATE,
        supported_platforms=(),
        benchmark=None,
        evidence_commands=(),
        required_evidence=tuple(str(item) for item in info["required_next_evidence"]),
        research_evidence_urls=tuple(str(item) for item in info["research_evidence_urls"]),
        notes=(str(info["reason"]),),
    )


def _snapshot_scaffold_row(profile: str) -> LiveEnablementRow:
    is_first_candidate = profile in FIRST_SNAPSHOT_CANDIDATES
    notes = SNAPSHOT_SCAFFOLD_NOTES.get(profile, ())
    if is_first_candidate:
        notes = ("Prioritized by snapshot promotion matrix as a first snapshot candidate.", *notes)
    return LiveEnablementRow(
        profile=profile,
        display_name=profile.replace("hk_", "HK ").replace("_", " ").title(),
        profile_type="external_snapshot_scaffold",
        selectable_by_platform=False,
        runtime_enabled=False,
        live_enablement_gate=SNAPSHOT_SCAFFOLD_GATE,
        supported_platforms=SUPPORTED_PLATFORMS,
        benchmark="02800",
        evidence_commands=(
            SNAPSHOT_PROMOTION_MATRIX_COMMAND,
            f"hkeq-print-snapshot-readiness --profile {profile} --platform ibkr --json",
            f"hkeq-print-snapshot-readiness --profile {profile} --platform longbridge --json",
        ),
        required_evidence=(
            "snapshot_promotion_matrix_row",
            "snapshot_repository_required_policy_review",
            "snapshot_future_research_live_enablement_policy_review",
            "snapshot_artifact_pack_validation",
            "snapshot_live_enablement_evidence_validation",
            "strategy_package_runtime_enabled_promotion",
            *COMMON_PLATFORM_EVIDENCE_REQUIREMENTS,
        ),
        research_evidence_urls=SNAPSHOT_RESEARCH_EVIDENCE_URLS.get(
            profile,
            ("../HkEquitySnapshotPipelines/docs/research/hk_snapshot_strategy_candidates.md",),
        ),
        notes=notes,
    )


def build_live_enablement_row(profile: str) -> dict[str, Any]:
    if profile in get_runtime_enabled_profiles():
        return _runtime_row(profile).as_dict()
    if profile in get_research_backtest_only_profiles():
        return _research_only_row(profile).as_dict()
    if profile in get_external_snapshot_scaffold_profiles():
        return _snapshot_scaffold_row(profile).as_dict()
    known = sorted(
        set(get_runtime_enabled_profiles())
        | set(get_research_backtest_only_profiles())
        | set(get_external_snapshot_scaffold_profiles())
    )
    raise ValueError(f"Unknown HK live-enable matrix profile {profile!r}; known profiles: {', '.join(known)}")


def build_live_enablement_matrix() -> dict[str, Any]:
    runtime_profiles = set(get_direct_market_history_profiles()) | set(get_snapshot_backed_profiles())
    runtime_rows = [_runtime_row(profile).as_dict() for profile in sorted(runtime_profiles)]
    research_rows = [_research_only_row(profile).as_dict() for profile in sorted(get_research_backtest_only_profiles())]
    snapshot_rows = [
        _snapshot_scaffold_row(profile).as_dict() for profile in sorted(get_external_snapshot_scaffold_profiles())
    ]
    rows = runtime_rows + research_rows + snapshot_rows
    selectable_profiles = [row["profile"] for row in rows if row["selectable_by_platform"]]
    blocked_profiles = [row["profile"] for row in rows if not row["selectable_by_platform"]]
    return {
        "matrix_version": HK_STRATEGY_LIVE_ENABLEMENT_MATRIX_VERSION,
        "domain": "hk_equity",
        "selectable_profile_count": len(selectable_profiles),
        "blocked_profile_count": len(blocked_profiles),
        "profile_count": len(rows),
        "selectable_profiles": selectable_profiles,
        "blocked_profiles": blocked_profiles,
        "first_snapshot_candidates": list(FIRST_SNAPSHOT_CANDIDATES),
        "curated_live_enablement_strategy_ranking": build_curated_live_enablement_strategy_ranking(),
        "common_platform_evidence_requirements": list(COMMON_PLATFORM_EVIDENCE_REQUIREMENTS),
        "snapshot_required_repository_policies": list(SNAPSHOT_REQUIRED_REPOSITORY_POLICIES),
        "snapshot_future_research_live_enablement_policy": build_snapshot_future_research_live_enablement_policy(),
        "runtime_live_gate": RUNTIME_LIVE_GATE,
        "snapshot_scaffold_gate": SNAPSHOT_SCAFFOLD_GATE,
        "research_only_gate": RESEARCH_ONLY_GATE,
        "backtest_validation_policy": build_backtest_validation_policy(),
        "evidence_uri_policy": EVIDENCE_URI_POLICY,
        "evidence_freshness_policy": EVIDENCE_FRESHNESS_POLICY,
        "execution_capacity_policy": build_execution_capacity_policy(""),
        "dry_run_order_preview_policy": build_dry_run_order_preview_policy(),
        "rollout_risk_policy": build_rollout_risk_policy(),
        "runtime_etf_product_policy": build_runtime_etf_product_policy(),
        "runtime_market_data_policy": build_runtime_market_data_policy(),
        "notification_audit_policy": build_notification_audit_policy(RUNTIME_DRY_RUN_NOTIFICATION_EVENT_TYPE),
        "profiles": rows,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Print HK strategy live-enable matrix.")
    parser.add_argument("--profile", help="Print one profile row instead of the full matrix")
    parser.add_argument("--json", action="store_true", help="Print JSON payload")
    args = parser.parse_args(argv)

    payload = build_live_enablement_row(args.profile) if args.profile else build_live_enablement_matrix()
    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
        return 0
    if args.profile:
        print(f"profile={payload['profile']}")
        print(f"profile_type={payload['profile_type']}")
        print(f"selectable_by_platform={payload['selectable_by_platform']}")
        print(f"live_enablement_gate={payload['live_enablement_gate']}")
        return 0
    print(f"matrix_version={payload['matrix_version']}")
    print(f"selectable_profiles={','.join(payload['selectable_profiles'])}")
    print(f"blocked_profile_count={payload['blocked_profile_count']}")
    for row in payload["profiles"]:
        print(f"- {row['profile']}: selectable={row['selectable_by_platform']} gate={row['live_enablement_gate']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


__all__ = [
    "FIRST_SNAPSHOT_CANDIDATES",
    "BACKTEST_VALIDATION_POLICY_VERSION",
    "EVIDENCE_FRESHNESS_POLICY",
    "EVIDENCE_URI_POLICY",
    "HSI_MOMENTUM_METHODOLOGY_URL",
    "HK_STRATEGY_LIVE_ENABLEMENT_MATRIX_VERSION",
    "RESEARCH_ONLY_GATE",
    "RUNTIME_LIVE_GATE",
    "SNAPSHOT_RESEARCH_EVIDENCE_URLS",
    "SNAPSHOT_SCAFFOLD_GATE",
    "SNAPSHOT_REQUIRED_REPOSITORY_POLICIES",
    "SNAPSHOT_FUTURE_RESEARCH_CURATED_CANDIDATES",
    "SNAPSHOT_FUTURE_RESEARCH_DEPRIORITIZED_CANDIDATES",
    "SNAPSHOT_FUTURE_RESEARCH_LIVE_ENABLEMENT_POLICY_VERSION",
    "CURATED_LIVE_ENABLEMENT_STRATEGY_RANKING_VERSION",
    "build_curated_live_enablement_strategy_ranking",
    "build_snapshot_future_research_live_enablement_policy",
    "build_live_enablement_matrix",
    "build_live_enablement_row",
    "main",
]
