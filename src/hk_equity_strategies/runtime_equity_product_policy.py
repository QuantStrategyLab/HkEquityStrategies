from __future__ import annotations

from .policy_catalog import build_runtime_equity_product_policy, get_policy_spec

_SPEC = get_policy_spec("runtime_equity_product")

RUNTIME_EQUITY_PRODUCT_POLICY_VERSION = str(_SPEC["policy_version"])
REQUIRED_RUNTIME_EQUITY_PRODUCT_FIELDS: tuple[str, ...] = tuple(_SPEC["required_fields"])
REQUIRED_RUNTIME_EQUITY_PRODUCT_URI_FIELDS: tuple[str, ...] = tuple(_SPEC["required_uri_fields"])
REQUIRED_RUNTIME_EQUITY_PRODUCT_BOOLEAN_FIELDS: tuple[str, ...] = tuple(_SPEC["required_boolean_fields"])
RUNTIME_EQUITY_PRODUCT_REFERENCE_URLS: tuple[str, ...] = tuple(_SPEC["source_reference_urls"])

__all__ = [
    "REQUIRED_RUNTIME_EQUITY_PRODUCT_BOOLEAN_FIELDS",
    "REQUIRED_RUNTIME_EQUITY_PRODUCT_FIELDS",
    "REQUIRED_RUNTIME_EQUITY_PRODUCT_URI_FIELDS",
    "RUNTIME_EQUITY_PRODUCT_POLICY_VERSION",
    "build_runtime_equity_product_policy",
]
