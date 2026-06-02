#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
QPK_SRC = ROOT.parent / "QuantPlatformKit" / "src"
for candidate in (SRC, QPK_SRC):
    candidate_str = str(candidate)
    if candidate_str not in sys.path:
        sys.path.insert(0, candidate_str)

from hk_equity_strategies.live_enablement_matrix import main  # noqa: E402


if __name__ == "__main__":
    raise SystemExit(main())
