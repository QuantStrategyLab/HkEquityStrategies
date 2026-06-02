from __future__ import annotations

from typing import Any

NOTIFICATION_SCHEMA_VERSION = "hk_live_enablement_notification.v1"
RUNTIME_DRY_RUN_NOTIFICATION_EVENT_TYPE = "hk_runtime_live_enablement_dry_run"

REQUIRED_NOTIFICATION_AUDIT_FIELDS: tuple[str, ...] = (
    "notification_schema_version",
    "notification_event_type",
    "notification_correlation_id",
    "notification_delivery_log_uri",
)

REQUIRED_NOTIFICATION_AUDIT_BOOLEAN_FIELDS: tuple[str, ...] = (
    "notification_locale_en",
    "notification_locale_zh_hans",
    "notification_contains_profile",
    "notification_contains_platform",
    "notification_contains_validation_status",
    "notification_contains_order_preview_summary",
    "notification_redacts_sensitive_fields",
)

NOTIFICATION_AUDIT_REFERENCE_URLS: tuple[str, ...] = (
    "https://www.sfc.hk/en/faqs/intermediaries/supervision/Use-of-External-Electronic-Data-Storage/Use-of-External-Electronic-Data-Storage",
    "https://www.hkex.com.hk/Services/Trading-hours-and-Severe-Weather-Arrangements?sc_lang=en",
)


def build_notification_audit_policy(expected_event_type: str | None = None) -> dict[str, Any]:
    return {
        "required": True,
        "schema_version": NOTIFICATION_SCHEMA_VERSION,
        "expected_event_type": expected_event_type or RUNTIME_DRY_RUN_NOTIFICATION_EVENT_TYPE,
        "supported_event_types": [RUNTIME_DRY_RUN_NOTIFICATION_EVENT_TYPE],
        "required_fields": list(REQUIRED_NOTIFICATION_AUDIT_FIELDS),
        "required_boolean_fields": list(REQUIRED_NOTIFICATION_AUDIT_BOOLEAN_FIELDS),
        "required_uri_fields": ["notification_delivery_log_uri"],
        "source_reference_urls": list(NOTIFICATION_AUDIT_REFERENCE_URLS),
        "description": "HK live-enable notifications must be bilingual, schema-versioned, correlated to the evidence pack, secret-safe, and backed by a stable delivery log URI.",
    }
