"""bgcoach: hypothesis-driven backgammon position analysis.

The core loop this package supports:

1. A position is described by an XGID string (:mod:`bgcoach.position`).
2. An analyst (Claude) proposes an explanation for why a play or cube
   action is correct.
3. The analyst designs small variants of the position that would come out
   differently if the explanation were wrong (:mod:`bgcoach.perturb`).
4. An engine evaluates the variants (:mod:`bgcoach.engines`).
5. The analyst compares equities and keeps, refines, or discards the
   explanation.

Everything here is engine-agnostic. GNU Backgammon is the first backend;
eXtreme Gammon can be added behind the same :class:`bgcoach.engines.Engine`
protocol later.
"""

from bgcoach.position import Position, parse_xgid

__all__ = ["Position", "parse_xgid"]
__version__ = "0.1.0"
