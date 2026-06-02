from __future__ import annotations

from typing import Any

DRY_RUN_ORDER_PREVIEW_POLICY_VERSION = "hk_dry_run_order_preview_provenance.v1"

REQUIRED_DRY_RUN_ORDER_PREVIEW_FIELDS: tuple[str, ...] = ("dry_run_session_id",)

REQUIRED_DRY_RUN_ORDER_PREVIEW_URI_FIELDS: tuple[str, ...] = (
    "raw_order_preview_uri",
    "quote_snapshot_uri",
    "fee_breakdown_uri",
)

REQUIRED_DRY_RUN_ORDER_PREVIEW_SHA256_FIELDS: tuple[str, ...] = (
    "raw_order_preview_sha256",
    "quote_snapshot_sha256",
    "fee_breakdown_sha256",
)

REQUIRED_DRY_RUN_ORDER_PREVIEW_BOOLEAN_FIELDS: tuple[str, ...] = (
    "order_preview_artifact_not_sample",
    "order_preview_redacts_sensitive_fields",
    "quote_snapshot_covers_all_symbols",
    "fee_breakdown_reconciled_to_broker_preview",
    "order_preview_reconciled_to_strategy_decision",
)

DRY_RUN_ORDER_PREVIEW_REFERENCE_URLS: tuple[str, ...] = (
    "https://www.hkex.com.hk/Services/Trading/Securities/Overview/Trading-Mechanism?sc_lang=en",
    "https://www.hkex.com.hk/Services/Rules-and-Forms-and-Fees/Fees/Securities-%28Hong-Kong%29/Trading/Transaction?sc_lang=en",
    "https://www.hkex.com.hk/Global/Exchange/FAQ/Securities-Market/Trading/VCM?sc_lang=en",
    "https://apps.sfc.hk/edistributionWeb/api/circular/list-content/circular/intermediaries/supervision/doc?lang=EN&refNo=16EC67",
)


def build_dry_run_order_preview_policy() -> dict[str, Any]:
    return {
        "required": True,
        "policy_version": DRY_RUN_ORDER_PREVIEW_POLICY_VERSION,
        "required_fields": list(REQUIRED_DRY_RUN_ORDER_PREVIEW_FIELDS),
        "required_uri_fields": list(REQUIRED_DRY_RUN_ORDER_PREVIEW_URI_FIELDS),
        "required_sha256_fields": list(REQUIRED_DRY_RUN_ORDER_PREVIEW_SHA256_FIELDS),
        "required_boolean_fields": list(REQUIRED_DRY_RUN_ORDER_PREVIEW_BOOLEAN_FIELDS),
        "source_reference_urls": list(DRY_RUN_ORDER_PREVIEW_REFERENCE_URLS),
        "description": "Dry-run order previews must preserve raw preview, quote snapshot, fee breakdown, and sha256 provenance before live enablement.",
    }
