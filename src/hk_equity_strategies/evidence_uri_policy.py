from __future__ import annotations

from .policy_catalog import build_evidence_uri_policy, get_policy_spec

_SPEC = get_policy_spec("evidence_uri")

ALLOWED_EVIDENCE_URI_SCHEMES: tuple[str, ...] = tuple(_SPEC["allowed_schemes"])
SENSITIVE_EVIDENCE_URI_MARKERS: tuple[str, ...] = tuple(_SPEC["rejected_query_markers"])

__all__ = [
    "ALLOWED_EVIDENCE_URI_SCHEMES",
    "SENSITIVE_EVIDENCE_URI_MARKERS",
    "build_evidence_uri_policy",
]
