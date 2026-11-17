from __future__ import annotations

from .policy_catalog import (
    build_notification_audit_policy as build_notification_audit_policy,
    get_policy_spec,
)

_SPEC = get_policy_spec("notification_audit")

NOTIFICATION_SCHEMA_VERSION = str(_SPEC["schema_version"])
RUNTIME_DRY_RUN_NOTIFICATION_EVENT_TYPE = str(_SPEC["default_event_type"])
REQUIRED_NOTIFICATION_AUDIT_FIELDS: tuple[str, ...] = tuple(_SPEC["required_fields"])
REQUIRED_NOTIFICATION_AUDIT_BOOLEAN_FIELDS: tuple[str, ...] = tuple(_SPEC["required_boolean_fields"])
NOTIFICATION_AUDIT_REFERENCE_URLS: tuple[str, ...] = tuple(_SPEC["source_reference_urls"])
