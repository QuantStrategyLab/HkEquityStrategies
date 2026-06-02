from __future__ import annotations

from typing import Any

RUNTIME_EQUITY_PRODUCT_POLICY_VERSION = "hk_runtime_equity_product_due_diligence.v1"

REQUIRED_RUNTIME_EQUITY_PRODUCT_FIELDS: tuple[str, ...] = (
    "equity_universe_audit_id",
    "managed_equity_symbols_audited_count",
)

REQUIRED_RUNTIME_EQUITY_PRODUCT_URI_FIELDS: tuple[str, ...] = (
    "equity_universe_audit_uri",
    "stock_connect_eligibility_source_uri",
    "board_lot_source_uri",
    "corporate_action_source_uri",
    "suspension_trading_status_source_uri",
    "dividend_payout_source_uri",
    "fee_and_stamp_duty_audit_uri",
    "broker_product_permission_audit_uri",
)

REQUIRED_RUNTIME_EQUITY_PRODUCT_BOOLEAN_FIELDS: tuple[str, ...] = (
    "single_name_equity_trading_permission_verified",
    "all_managed_symbols_confirmed_hk_equity",
    "stock_connect_eligibility_or_broker_route_reviewed",
    "broker_trading_permission_per_symbol_verified",
    "currency_and_board_lot_per_symbol_verified",
    "distribution_and_corporate_action_treatment_verified",
    "suspension_and_trading_status_verified",
    "dividend_yield_and_payout_source_verified",
    "sector_and_single_name_caps_verified",
)

RUNTIME_EQUITY_PRODUCT_REFERENCE_URLS: tuple[str, ...] = (
    "https://www.hkex.com.hk/Market-Data/Securities-Prices/Equities?sc_lang=en",
    "https://www.hkex.com.hk/Services/Trading/Securities/Overview/Trading-Mechanism?sc_lang=en",
    "https://www.hkex.com.hk/Services/Rules-and-Forms-and-Fees/Fees/Securities-%28Hong-Kong%29/Trading/Transaction?sc_lang=en",
    "https://www.hkex.com.hk/mutual-market/stock-connect/eligible-stocks/view-all-eligible-securities?sc_lang=en",
)


def build_runtime_equity_product_policy() -> dict[str, Any]:
    return {
        "required": True,
        "policy_version": RUNTIME_EQUITY_PRODUCT_POLICY_VERSION,
        "required_fields": list(REQUIRED_RUNTIME_EQUITY_PRODUCT_FIELDS),
        "required_uri_fields": list(REQUIRED_RUNTIME_EQUITY_PRODUCT_URI_FIELDS),
        "required_boolean_fields": list(REQUIRED_RUNTIME_EQUITY_PRODUCT_BOOLEAN_FIELDS),
        "source_reference_urls": list(RUNTIME_EQUITY_PRODUCT_REFERENCE_URLS),
        "description": (
            "Snapshot-backed HK single-name runtime evidence must prove HK equity eligibility, broker route, "
            "board-lot/currency handling, corporate-action and suspension treatment, dividend/payout source "
            "lineage, fees/stamp duty, and per-symbol trading permission before live enablement."
        ),
    }


__all__ = [
    "REQUIRED_RUNTIME_EQUITY_PRODUCT_BOOLEAN_FIELDS",
    "REQUIRED_RUNTIME_EQUITY_PRODUCT_FIELDS",
    "REQUIRED_RUNTIME_EQUITY_PRODUCT_URI_FIELDS",
    "RUNTIME_EQUITY_PRODUCT_POLICY_VERSION",
    "build_runtime_equity_product_policy",
]
