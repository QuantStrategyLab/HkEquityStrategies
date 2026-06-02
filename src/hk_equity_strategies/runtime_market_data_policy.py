from __future__ import annotations

from typing import Any

REQUIRED_RUNTIME_MARKET_DATA_PROVENANCE_FIELDS: tuple[str, ...] = (
    "market_history_source_name",
    "market_history_coverage_start",
    "market_history_coverage_end",
)

REQUIRED_RUNTIME_MARKET_DATA_URI_FIELDS: tuple[str, ...] = (
    "market_history_source_uri",
    "market_history_quality_report_uri",
    "point_in_time_data_dictionary_uri",
)

REQUIRED_RUNTIME_MARKET_DATA_AUDIT_FIELDS: tuple[str, ...] = (
    "point_in_time_market_history",
    "adjusted_price_history",
    "distribution_history",
    "corporate_action_history",
    "stale_quote_checks",
    "suspension_and_trading_status_checks",
    "holiday_and_half_day_calendar_checks",
    "symbol_mapping_history",
    "etf_nav_or_inav_source_verified",
    "stamp_duty_or_etf_exemption_source_verified",
)

RUNTIME_MARKET_DATA_REFERENCE_URLS: tuple[str, ...] = (
    "https://www.hkex.com.hk/Market-Data/Securities-Prices/Exchange-Traded-Products?sc_lang=en",
    "https://www.hkex.com.hk/products/securities/exchange-traded-products/overview?sc_lang=en",
    "https://www.hkex.com.hk/-/media/HKEX-Market/Products/Securities/Exchange-Traded-Products/Launch/HKEX_ETF-Handbook.pdf",
    "https://www.ird.gov.hk/eng/faq/ETFs.htm",
    "https://www2.hkexnews.hk/exchange-reports/status-report-on-delisting-proceeding-and-suspensions?p=1&sc_lang=en",
)


def build_runtime_market_data_policy() -> dict[str, Any]:
    return {
        "required": True,
        "required_fields": list(REQUIRED_RUNTIME_MARKET_DATA_PROVENANCE_FIELDS),
        "required_uri_fields": list(REQUIRED_RUNTIME_MARKET_DATA_URI_FIELDS),
        "required_boolean_fields": list(REQUIRED_RUNTIME_MARKET_DATA_AUDIT_FIELDS),
        "source_reference_urls": list(RUNTIME_MARKET_DATA_REFERENCE_URLS),
        "description": "Runtime ETF market_history feeds must prove point-in-time adjusted prices, distributions, corporate actions, trading status, stale-quote controls, stable market-history source provenance, ETF NAV/iNAV references, and stamp-duty/exemption sources before live enablement.",
    }
