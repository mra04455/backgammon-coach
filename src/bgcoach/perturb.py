"""Perturbations: small, named edits to a position for hypothesis testing.

Every function takes a :class:`Position` and returns a new one; nothing is
mutated. Points are always given in the *acting player's own numbering*
(1 = their ace point, 24 = their opponent's ace point), with ``BAR`` (25)
and ``OFF`` (0) as special values, so an analyst can say "move the
checker from the 20-point to the 18-point" without thinking about which
side of the XGID frame that player is on.

Perturbations can also be described as plain dicts (``{"op": "move",
"player": 1, "src": 13, "dst": 11}``) and applied with :func:`apply`, which
is what the MCP server exposes.
"""

from __future__ import annotations

from dataclasses import replace
from typing import Any, Callable

from bgcoach.position import BOTTOM, TOP, Position, own_point_to_index

BAR = 25
OFF = 0


class PerturbError(ValueError):
    """The requested edit is impossible (no checker there, point blocked, ...)."""


# ----------------------------------------------------------------------
# Checker edits
# ----------------------------------------------------------------------


def _sign(player: int) -> int:
    if player not in (BOTTOM, TOP):
        raise PerturbError("player must be +1 (bottom) or -1 (top)")
    return player


def _take_from(pos: Position, player: int, point: int) -> Position:
    """Remove one of ``player``'s checkers from ``point`` (own numbering), into limbo."""
    sign = _sign(player)
    if point == BAR:
        if pos.on_bar(player) == 0:
            raise PerturbError(f"player {player} has no checker on the bar")
        bar = list(pos.bar)
        bar[0 if player == BOTTOM else 1] -= 1
        return replace(pos, bar=tuple(bar))
    if point == OFF:
        if pos.off(player) == 0:
            raise PerturbError(f"player {player} has no checkers off")
        return pos  # off is implicit; nothing to change yet
    idx = own_point_to_index(player, point)
    if pos.board[idx] * sign <= 0:
        raise PerturbError(f"player {player} has no checker on their {point}-point")
    board = list(pos.board)
    board[idx] -= sign
    return replace(pos, board=tuple(board))


def _put_on(pos: Position, player: int, point: int) -> Position:
    sign = _sign(player)
    if point == BAR:
        bar = list(pos.bar)
        bar[0 if player == BOTTOM else 1] += 1
        return replace(pos, bar=tuple(bar))
    if point == OFF:
        return pos  # off is implicit
    idx = own_point_to_index(player, point)
    if pos.board[idx] * sign < 0:
        raise PerturbError(
            f"player {player}'s {point}-point is occupied by the opponent; "
            f"remove or move that checker first"
        )
    board = list(pos.board)
    board[idx] += sign
    return replace(pos, board=tuple(board))


def move_checker(pos: Position, player: int, src: int, dst: int) -> Position:
    """Move one of ``player``'s checkers from ``src`` to ``dst`` (own numbering).

    Not a legal-move check: any source with a checker and any destination
    not held by the opponent is allowed. ``BAR``/``OFF`` are valid endpoints.
    """
    if src == dst:
        return pos
    return _put_on(_take_from(pos, player, src), player, dst)


def move_point(pos: Position, player: int, src: int, dst: int) -> Position:
    """Move *all* of ``player``'s checkers on ``src`` to ``dst``."""
    n = pos.on_bar(player) if src == BAR else pos.checkers_on(player, src) if src != OFF else 0
    if n == 0:
        raise PerturbError(f"player {player} has nothing on {src}")
    out = pos
    for _ in range(n):
        out = move_checker(out, player, src, dst)
    return out


def add_checker(pos: Position, player: int, point: int) -> Position:
    """Bring one of ``player``'s borne-off checkers back onto ``point``."""
    if pos.off(player) == 0:
        raise PerturbError(f"player {player} has all 15 checkers in play; remove one first")
    return _put_on(pos, player, point)


def remove_checker(pos: Position, player: int, point: int) -> Position:
    """Take one of ``player``'s checkers off the board (counts as borne off)."""
    return _take_from(pos, player, point)


def swap_blot_for_point(pos: Position, player: int, point: int) -> Position:
    """Turn a blot on ``point`` into a made point by adding a second checker from off."""
    if pos.checkers_on(player, point) != 1:
        raise PerturbError(f"player {player} does not have exactly one checker on {point}")
    return add_checker(pos, player, point)


# ----------------------------------------------------------------------
# Cube, score, dice, turn
# ----------------------------------------------------------------------


def set_cube(pos: Position, value: int | None = None, owner: int | None = None) -> Position:
    """Change cube value and/or owner. ``owner``: 0 centered, +1 bottom, -1 top."""
    changes: dict[str, Any] = {}
    if value is not None:
        changes["cube_value"] = value
    if owner is not None:
        changes["cube_owner"] = owner
    return replace(pos, **changes)


def set_dice(pos: Position, dice: tuple[int, int] | None) -> Position:
    return replace(pos, dice=dice, cube_action=None)


def set_cube_action(pos: Position, action: str | None) -> Position:
    """Mark a pending cube action: 'D' double offered, 'B' beaver, 'R' raccoon, or None."""
    return replace(pos, dice=None, cube_action=action)


def set_turn(pos: Position, player: int) -> Position:
    return replace(pos, turn=_sign(player))


def set_score(pos: Position, bottom: int, top: int, match_length: int | None = None,
              crawford: bool | None = None) -> Position:
    changes: dict[str, Any] = {"score": (bottom, top)}
    if match_length is not None:
        changes["match_length"] = match_length
    if crawford is not None:
        changes["crawford"] = crawford
    return replace(pos, **changes)


def at_away(pos: Position, bottom_away: int, top_away: int, *, crawford: bool = False) -> Position:
    """Put the position at a given match score expressed as points-away.

    Match length becomes ``max(bottom_away, top_away)``.
    """
    length = max(bottom_away, top_away)
    return replace(
        pos,
        match_length=length,
        score=(length - bottom_away, length - top_away),
        crawford=crawford,
        jacoby=False,
        beaver=False,
    )


def to_money(pos: Position, *, jacoby: bool = False, beaver: bool = False) -> Position:
    return replace(pos, match_length=0, score=(0, 0), crawford=False, jacoby=jacoby, beaver=beaver)


def to_dmp(pos: Position) -> Position:
    """Double match point: both players 1-away, cube dead."""
    return at_away(pos, 1, 1).with_(cube_value=1, cube_owner=0)


def gammon_go(pos: Position, player: int) -> Position:
    """A score where ``player``'s gammons count for a lot: they are 2-away, opponent 1-away (post-Crawford)."""
    if player == BOTTOM:
        return at_away(pos, 2, 1)
    return at_away(pos, 1, 2)


def gammon_save(pos: Position, player: int) -> Position:
    """A score where ``player`` must avoid being gammoned: they are 1-away, opponent 2-away."""
    return gammon_go(pos, -player)


# ----------------------------------------------------------------------
# Generic dispatch for the MCP layer
# ----------------------------------------------------------------------

OPS: dict[str, Callable[..., Position]] = {
    "move": move_checker,
    "move_point": move_point,
    "add": add_checker,
    "remove": remove_checker,
    "make_point": swap_blot_for_point,
    "cube": set_cube,
    "dice": lambda pos, dice: set_dice(pos, tuple(dice) if dice else None),
    "cube_action": set_cube_action,
    "turn": set_turn,
    "score": set_score,
    "away": at_away,
    "money": to_money,
    "dmp": to_dmp,
    "gammon_go": gammon_go,
    "gammon_save": gammon_save,
    "mirror": lambda pos: pos.mirror(),
}


def apply(pos: Position, operations: list[dict[str, Any]]) -> Position:
    """Apply a list of ``{"op": name, ...kwargs}`` edits in order.

    Example::

        apply(pos, [
            {"op": "move", "player": 1, "src": 13, "dst": 11},
            {"op": "cube", "owner": -1, "value": 2},
            {"op": "away", "bottom_away": 3, "top_away": 5},
        ])
    """
    out = pos
    for i, spec in enumerate(operations):
        spec = dict(spec)
        name = spec.pop("op", None)
        if name not in OPS:
            raise PerturbError(f"operation {i}: unknown op {name!r}; known: {sorted(OPS)}")
        try:
            out = OPS[name](out, **spec)
        except TypeError as e:
            raise PerturbError(f"operation {i} ({name}): bad arguments: {e}") from e
    return out


def describe(op: dict[str, Any]) -> str:
    """One-line human description of an operation dict, for logs and reports."""
    name = op.get("op")
    who = {BOTTOM: "X", TOP: "O"}.get(op.get("player"), "")
    pt = lambda p: "bar" if p == BAR else "off" if p == OFF else f"{p}-pt"  # noqa: E731
    if name == "move":
        return f"{who}: {pt(op['src'])} → {pt(op['dst'])}"
    if name == "move_point":
        return f"{who}: all from {pt(op['src'])} → {pt(op['dst'])}"
    if name == "add":
        return f"{who}: add checker on {pt(op['point'])}"
    if name == "remove":
        return f"{who}: remove checker from {pt(op['point'])}"
    if name == "make_point":
        return f"{who}: cover blot on {pt(op['point'])}"
    if name == "cube":
        parts = []
        if "value" in op:
            parts.append(f"cube={op['value']}")
        if "owner" in op:
            parts.append({0: "centered", BOTTOM: "X owns", TOP: "O owns"}[op["owner"]])
        return "cube: " + ", ".join(parts)
    if name == "away":
        return f"score: X {op['bottom_away']}-away, O {op['top_away']}-away"
    return name or "?"
