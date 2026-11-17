from __future__ import annotations

from .policy_catalog import (
    build_evidence_freshness_policy as build_evidence_freshness_policy,
    get_policy_spec,
)

_SPEC = get_policy_spec("evidence_freshness")

EVIDENCE_GENERATED_AT_FIELD = str(_SPEC["required_field"])
MAX_ALLOWED_EVIDENCE_AGE_DAYS_BY_SECTION: dict[str, int] = dict(_SPEC["max_allowed_age_days_by_section"])
