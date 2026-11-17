from __future__ import annotations

from .policy_catalog import (
    build_runtime_market_data_policy as build_runtime_market_data_policy,
    get_policy_spec,
)

_SPEC = get_policy_spec("runtime_market_data")

REQUIRED_RUNTIME_MARKET_DATA_PROVENANCE_FIELDS: tuple[str, ...] = tuple(_SPEC["required_fields"])
REQUIRED_RUNTIME_MARKET_DATA_URI_FIELDS: tuple[str, ...] = tuple(_SPEC["required_uri_fields"])
REQUIRED_RUNTIME_MARKET_DATA_AUDIT_FIELDS: tuple[str, ...] = tuple(_SPEC["required_boolean_fields"])
RUNTIME_MARKET_DATA_REFERENCE_URLS: tuple[str, ...] = tuple(_SPEC["source_reference_urls"])
