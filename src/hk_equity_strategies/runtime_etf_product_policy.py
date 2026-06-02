from __future__ import annotations

from typing import Any

RUNTIME_ETF_PRODUCT_POLICY_VERSION = "hk_runtime_etf_product_due_diligence.v2"

REQUIRED_RUNTIME_ETF_PRODUCT_FIELDS: tuple[str, ...] = (
    "etf_product_audit_id",
    "managed_etf_symbols_audited_count",
)

REQUIRED_RUNTIME_ETF_PRODUCT_URI_FIELDS: tuple[str, ...] = (
    "etf_product_universe_audit_uri",
    "official_product_document_uri",
    "underlying_index_or_reference_asset_source_uri",
    "nav_or_inav_source_uri",
    "market_maker_or_liquidity_provider_source_uri",
    "stock_connect_etf_eligibility_source_uri",
    "southbound_etf_turnover_and_fund_flow_source_uri",
    "distribution_tax_and_fee_treatment_source_uri",
    "etf_fee_and_stamp_duty_audit_uri",
    "broker_product_permission_audit_uri",
)

REQUIRED_RUNTIME_ETF_PRODUCT_BOOLEAN_FIELDS: tuple[str, ...] = (
    "all_managed_symbols_confirmed_etp",
    "leveraged_inverse_or_synthetic_flags_audited",
    "complex_or_futures_based_products_operator_reviewed",
    "etf_stamp_duty_exemption_or_tax_treatment_verified",
    "market_maker_or_liquidity_provider_presence_checked",
    "product_kid_or_prospectus_risk_disclosure_reviewed",
    "official_product_documents_current",
    "underlying_index_or_reference_asset_verified",
    "nav_or_inav_reconciled_to_market_data",
    "tracking_error_or_tracking_difference_reviewed",
    "stock_connect_etf_eligibility_or_sell_only_status_reviewed",
    "etf_connect_daily_turnover_and_fund_flow_trend_reviewed",
    "stock_connect_holiday_eligibility_change_and_cross_boundary_settlement_reviewed",
    "southbound_buy_order_availability_and_broker_route_reviewed",
    "multi_counter_currency_and_creation_redemption_reviewed",
    "underlying_market_trading_hour_and_premium_discount_reviewed",
    "cross_market_holiday_fx_and_settlement_risk_reviewed",
    "futures_roll_margin_and_contango_backwardation_risk_reviewed",
    "distribution_policy_and_capital_distribution_risk_reviewed",
    "commodity_trust_single_asset_and_storage_risk_reviewed",
    "high_dividend_index_concentration_and_yield_trap_risk_reviewed",
    "broker_trading_permission_per_symbol_verified",
    "currency_and_board_lot_per_symbol_verified",
    "distribution_and_corporate_action_treatment_verified",
)

RUNTIME_ETF_PRODUCT_REFERENCE_URLS: tuple[str, ...] = (
    "https://www.hkex.com.hk/products/securities/exchange-traded-products/overview?sc_lang=en",
    "https://www.hkex.com.hk/Products/Securities/Exchange-Traded-Products/Market-Makers/Overview?sc_lang=en",
    "https://www.hkex.com.hk/Mutual-Market/Stock-Connect/Reference-Materials/Inclusion-of-ETFs-in-Stock-Connect?sc_lang=en",
    "https://www.hkex.com.hk/mutual-market/stock-connect/eligible-stocks/view-all-eligible-securities?sc_lang=en",
    "https://www.hkex.com.hk/mutual-market/stock-connect/statistics?sc_lang=en",
    "https://www.hkex.com.hk/Mutual-Market/Stock-Connect/Statistics/Historical-Daily?sc_lang=en",
    "https://www.hkex.com.hk/-/media/HKEX-Market/Mutual-Market/Stock-Connect/Reference-Materials/Inclusion-of-ETFs-in-Stock-Connect/Inclusion_of_ETFs_in_Stock_Connect_Useful_Information_for_Issuers_Eng.pdf",
    "https://www.ird.gov.hk/eng/faq/ETFs.htm",
    "https://www.hkex.com.hk/Services/Rules-and-Forms-and-Fees/Fees/Securities-%28Hong-Kong%29/Trading/Transaction?sc_lang=en",
    "https://www.hkex.com.hk/News/Market-Communications/2015/150204news",
)


def build_runtime_etf_product_policy() -> dict[str, Any]:
    return {
        "required": True,
        "policy_version": RUNTIME_ETF_PRODUCT_POLICY_VERSION,
        "required_fields": list(REQUIRED_RUNTIME_ETF_PRODUCT_FIELDS),
        "required_uri_fields": list(REQUIRED_RUNTIME_ETF_PRODUCT_URI_FIELDS),
        "required_boolean_fields": list(REQUIRED_RUNTIME_ETF_PRODUCT_BOOLEAN_FIELDS),
        "source_reference_urls": list(RUNTIME_ETF_PRODUCT_REFERENCE_URLS),
        "description": (
            "HK ETF runtime profiles must prove per-symbol ETP classification, official product-document and "
            "underlying-index/reference-asset lineage, NAV/iNAV reconciliation, tracking-difference review, "
            "ETF Connect eligibility or sell-only status, Southbound ETF turnover/fund-flow trend, broker "
            "southbound route availability, multi-counter currency and creation/redemption handling, "
            "underlying-market trading-hour and premium/discount risk, cross-market holiday/FX/settlement "
            "risk, Stock Connect holiday/eligibility-change/cross-boundary settlement risk, futures "
            "roll/margin/curve risk, "
            "distribution/tax/fee treatment, product permission, liquidity-provider support, board-lot/currency "
            "handling, and complex/single-asset product review."
        ),
    }
