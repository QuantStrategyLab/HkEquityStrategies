from __future__ import annotations

from .policy_catalog import (
    build_dry_run_order_preview_policy as build_dry_run_order_preview_policy,
    get_policy_spec,
)

_SPEC = get_policy_spec("dry_run_order_preview")

DRY_RUN_ORDER_PREVIEW_POLICY_VERSION = str(_SPEC["policy_version"])
REQUIRED_DRY_RUN_ORDER_PREVIEW_FIELDS: tuple[str, ...] = tuple(_SPEC["required_fields"])
REQUIRED_DRY_RUN_ORDER_PREVIEW_URI_FIELDS: tuple[str, ...] = tuple(_SPEC["required_uri_fields"])
REQUIRED_DRY_RUN_ORDER_PREVIEW_SHA256_FIELDS: tuple[str, ...] = tuple(_SPEC["required_sha256_fields"])
REQUIRED_DRY_RUN_ORDER_PREVIEW_BOOLEAN_FIELDS: tuple[str, ...] = tuple(_SPEC["required_boolean_fields"])
DRY_RUN_ORDER_PREVIEW_REFERENCE_URLS: tuple[str, ...] = tuple(_SPEC["source_reference_urls"])
