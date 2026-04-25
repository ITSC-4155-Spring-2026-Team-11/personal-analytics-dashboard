"""Put repo root on sys.path for `from backend...` imports (pytest + IDE runs)."""

from __future__ import annotations

import sys
from pathlib import Path

_root = Path(__file__).resolve().parent
_s = str(_root)
if _s not in sys.path:
    sys.path.insert(0, _s)

