from __future__ import annotations

from .policy_catalog import (
    build_runtime_etf_product_policy as build_runtime_etf_product_policy,
    get_policy_spec,
)

_SPEC = get_policy_spec("runtime_etf_product")

RUNTIME_ETF_PRODUCT_POLICY_VERSION = str(_SPEC["policy_version"])
REQUIRED_RUNTIME_ETF_PRODUCT_FIELDS: tuple[str, ...] = tuple(_SPEC["required_fields"])
REQUIRED_RUNTIME_ETF_PRODUCT_URI_FIELDS: tuple[str, ...] = tuple(_SPEC["required_uri_fields"])
REQUIRED_RUNTIME_ETF_PRODUCT_BOOLEAN_FIELDS: tuple[str, ...] = tuple(_SPEC["required_boolean_fields"])
RUNTIME_ETF_PRODUCT_REFERENCE_URLS: tuple[str, ...] = tuple(_SPEC["source_reference_urls"])
