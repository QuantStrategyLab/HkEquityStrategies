#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
QPK_SRC = ROOT.parent / "QuantPlatformKit" / "src"
for candidate in (SRC, QPK_SRC):
    candidate_str = str(candidate)
    if candidate_str not in sys.path:
        sys.path.insert(0, candidate_str)

from hk_equity_strategies.catalog import HK_GLOBAL_ETF_TACTICAL_ROTATION_PROFILE  # noqa: E402
from hk_equity_strategies.runtime_adapters import SUPPORTED_RUNTIME_PLATFORMS  # noqa: E402
from hk_equity_strategies.runtime_readiness import build_hk_runtime_readiness  # noqa: E402


def _print_plan(plan: dict[str, object]) -> None:
    print(f"platform: {plan['platform']}")
    print(f"profile: {plan['canonical_profile']} ({plan['display_name']})")
    print(f"status: {plan['status']}  runtime_enabled: {plan['runtime_enabled']}")
    print(f"dry_run_only: {plan['dry_run_only']}")
    print(f"required_inputs: {', '.join(plan['required_inputs'])}")
    print(f"managed_symbols: {', '.join(plan['managed_symbols']) or '<runtime input required>'}")
    print(f"market_defaults: {json.dumps(plan['market_defaults'], sort_keys=True)}")
    print(f"target_conversion: {json.dumps(plan['target_conversion'], sort_keys=True)}")
    print("\nplatform_dry_run_env:")
    for key, value in plan["platform_dry_run_env"].items():
        print(f"  {key}={value}")
    print("\ndry_run_checks:")
    for check in plan["dry_run_checks"]:
        print(f"  - {check}")
    print("\norder_conversion_checks:")
    for check in plan["order_conversion_checks"]:
        print(f"  - {check}")
    print("\nrisk_notes:")
    for note in plan["risk_notes"]:
        print(f"  - {note}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--profile", default=HK_GLOBAL_ETF_TACTICAL_ROTATION_PROFILE)
    parser.add_argument("--platform", required=True, choices=sorted(SUPPORTED_RUNTIME_PLATFORMS))
    parser.add_argument("--live", action="store_true", help="Render a live-mode checklist; does not deploy anything.")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    plan = build_hk_runtime_readiness(
        args.profile,
        platform_id=args.platform,
        dry_run_only=not args.live,
    )
    if args.json:
        print(json.dumps(plan, indent=2, sort_keys=True))
        return 0
    _print_plan(plan)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
