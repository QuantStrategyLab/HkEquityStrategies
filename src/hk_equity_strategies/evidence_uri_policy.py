from __future__ import annotations

from typing import Any

ALLOWED_EVIDENCE_URI_SCHEMES = ("gs", "https", "s3")
SENSITIVE_EVIDENCE_URI_MARKERS = (
    "access_token=",
    "api_key=",
    "auth=",
    "jwt=",
    "password=",
    "secret=",
    "signature=",
    "token=",
    "x-amz-signature=",
    "x-goog-signature=",
)


def build_evidence_uri_policy() -> dict[str, Any]:
    return {
        "required": True,
        "allowed_schemes": [f"{scheme}://" for scheme in ALLOWED_EVIDENCE_URI_SCHEMES],
        "rejected_query_markers": list(SENSITIVE_EVIDENCE_URI_MARKERS),
        "description": "Evidence sections must point to stable audit artifacts and must not embed secrets.",
    }


__all__ = [
    "ALLOWED_EVIDENCE_URI_SCHEMES",
    "SENSITIVE_EVIDENCE_URI_MARKERS",
    "build_evidence_uri_policy",
]
