"""Engine-agnostic evaluation types and the Engine protocol.

Every backend (gnubg today, XG later) returns the same :class:`Evaluation`
so the analyst layer never needs to know which engine answered.

Conventions
-----------
* All equities are **cubeful, normalised** (money-equivalent, +1 = win a
  single game) from the point of view of the player on roll. Match-play
  equities are normalised match equities, not MWC.
* Probabilities are ``(win, win_gammon, win_backgammon, lose, lose_gammon,
  lose_backgammon)``; gammon figures include backgammons, as gnubg and XG
  report them.
* ``error`` on a move is the equity lost relative to the best move
  (0.0 for the best move, negative otherwise).
* Rollout results carry a standard error (``se``) on the cubeful equity
  and the number of trials actually played; evaluations leave them None.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal, Protocol, runtime_checkable

from bgcoach.position import Position

Kind = Literal["checker", "cube", "static"]


@dataclass(frozen=True)
class Probs:
    win: float
    win_g: float
    win_bg: float
    lose: float
    lose_g: float
    lose_bg: float

    def as_tuple(self) -> tuple[float, ...]:
        return (self.win, self.win_g, self.win_bg, self.lose, self.lose_g, self.lose_bg)

    def cubeless_equity(self) -> float:
        """Money cubeless equity implied by the probabilities."""
        return self.win + self.win_g + self.win_bg - self.lose - self.lose_g - self.lose_bg


@dataclass(frozen=True)
class MoveEval:
    rank: int
    move: str  # e.g. "24/18 13/11", in the on-roll player's own numbering
    equity: float
    error: float  # <= 0; 0.0 for the best move
    probs: Probs | None
    ply: str  # e.g. "2-ply", "3-ply", "rollout"
    se: float | None = None  # standard error of ``equity`` (rollouts only)
    trials: int | None = None  # games actually played (rollouts only)
    cubeless_equity: float | None = None  # rollouts report it alongside cubeful


@dataclass(frozen=True)
class CubeEval:
    no_double: float
    double_take: float
    double_pass: float
    proper_action: str  # gnubg's phrase, e.g. "No double, take"
    probs: Probs | None
    cubeless_equity: float | None
    ply: str
    se_no_double: float | None = None  # rollouts only
    se_double_take: float | None = None  # rollouts only
    trials: int | None = None  # rollouts only

    @property
    def best_cube_action(self) -> str:
        """Normalised action: 'no double' | 'double/take' | 'double/pass' | 'too good'."""
        a = self.proper_action.lower()
        if "too good" in a:
            return "too good"
        if a.startswith(("no double", "no redouble")):
            return "no double"
        if "pass" in a:
            return "double/pass"
        return "double/take"

    @property
    def take_decision(self) -> str:
        """From the taker's side: 'take' if double/take beats double/pass for the doubler."""
        # The doubler prefers the larger equity; the taker therefore prefers the
        # smaller one. If double/take < double/pass the correct answer is take.
        return "take" if self.double_take < self.double_pass else "pass"


@dataclass(frozen=True)
class StaticEval:
    """Position value when there is no decision to make (dead cube, or
    the opponent owns the cube): probabilities plus cubeless and cubeful
    equity for the player on roll."""

    probs: Probs
    cubeless_equity: float
    cubeful_equity: float
    ply: str


@dataclass(frozen=True)
class RolloutInfo:
    """Provenance of a rollout: everything needed to reproduce or re-test it."""

    trials: int  # requested; per-item ``trials`` say how many were played
    seed: int | None
    cubeful: bool
    variance_reduction: bool
    truncation: int | None  # plies, None = full rollout
    jsd_stop: bool
    jsd_limit: float | None
    chequer_plies: int
    cube_plies: int
    engine_version: str | None = None

    def to_dict(self) -> dict:
        return {
            "trials": self.trials,
            "seed": self.seed,
            "cubeful": self.cubeful,
            "variance_reduction": self.variance_reduction,
            "truncation": self.truncation,
            "jsd_stop": self.jsd_stop,
            "jsd_limit": self.jsd_limit,
            "chequer_plies": self.chequer_plies,
            "cube_plies": self.cube_plies,
            "engine_version": self.engine_version,
        }


@dataclass(frozen=True)
class Evaluation:
    position: Position
    kind: Kind
    engine: str
    level: str  # human-readable, e.g. "gnubg 2-ply", "gnubg rollout"
    moves: list[MoveEval] = field(default_factory=list)
    cube: CubeEval | None = None
    static: StaticEval | None = None
    raw: str = ""  # engine's raw text, kept for debugging
    rollout: RolloutInfo | None = None  # set when the numbers come from a rollout

    @property
    def best_move(self) -> MoveEval | None:
        return self.moves[0] if self.moves else None

    @property
    def best_equity(self) -> float | None:
        if self.kind == "checker":
            return self.best_move.equity if self.best_move else None
        if self.kind == "static":
            return self.static.cubeful_equity if self.static else None
        if self.cube is None:
            return None
        return max(self.cube.no_double, min(self.cube.double_take, self.cube.double_pass))

    def to_dict(self) -> dict:
        d: dict = {
            "xgid": self.position.xgid(),
            "kind": self.kind,
            "engine": self.engine,
            "level": self.level,
        }
        if self.rollout is not None:
            d["rollout"] = self.rollout.to_dict()
        if self.static is not None:
            s = self.static
            d["static"] = {
                "cubeful_equity": s.cubeful_equity,
                "cubeless_equity": s.cubeless_equity,
                "probs": list(s.probs.as_tuple()),
                "ply": s.ply,
            }
        if self.kind == "checker":
            d["moves"] = [
                {
                    "rank": m.rank,
                    "move": m.move,
                    "equity": m.equity,
                    "error": m.error,
                    "ply": m.ply,
                    "probs": list(m.probs.as_tuple()) if m.probs else None,
                    "se": m.se,
                    "trials": m.trials,
                    "cubeless_equity": m.cubeless_equity,
                }
                for m in self.moves
            ]
        if self.cube is not None:
            c = self.cube
            d["cube"] = {
                "no_double": c.no_double,
                "double_take": c.double_take,
                "double_pass": c.double_pass,
                "proper_action": c.proper_action,
                "best_cube_action": c.best_cube_action,
                "take_decision": c.take_decision,
                "cubeless_equity": c.cubeless_equity,
                "probs": list(c.probs.as_tuple()) if c.probs else None,
                "ply": c.ply,
                "se_no_double": c.se_no_double,
                "se_double_take": c.se_double_take,
                "trials": c.trials,
            }
        return d


class EngineError(RuntimeError):
    """The engine could not evaluate the position."""


@runtime_checkable
class Engine(Protocol):
    name: str

    def evaluate(self, position: Position, *, plies: int = 2) -> Evaluation:
        """Evaluate the decision the player on roll faces.

        If the position has dice, this is a checker-play evaluation and
        ``moves`` is populated. If it has no dice (or a cube action is
        pending) it is a cube evaluation and ``cube`` is populated.
        """
        ...

    def rollout(
        self,
        position: Position,
        *,
        moves: list[str] | None = None,
        top: int = 2,
        settings: object | None = None,
    ) -> Evaluation:
        """Roll out the decision the player on roll faces.

        Checker play: roll out ``moves`` (engine move notation), or the
        ``top`` moves by the engine's own ranking when ``moves`` is None.
        Cube: roll out no-double against double/take. ``settings`` is
        engine-specific; None means the engine's defaults. The result has
        ``rollout`` set and ``se``/``trials`` filled in.
        """
        ...
