"""MCP server exposing the engine and perturbation tools to Claude Code.

Run with ``python -m bgcoach.mcp_server`` (stdio transport). The repo's
``.mcp.json`` already points at this, so inside the project Claude Code
picks it up automatically after you approve the server once.

Tool design notes
-----------------
* Positions are passed as XGID strings everywhere. They're short, exact,
  and the same string XG and gnubg both understand.
* ``perturb`` is deliberately separate from ``evaluate`` so the analyst
  can inspect a variant (and the ASCII board) before spending engine time.
* ``sweep`` is the workhorse for hypothesis testing: one base position,
  several labelled variants, everything evaluated, deltas summarised.
"""

from __future__ import annotations

import os
from functools import lru_cache
from typing import Any

try:  # mcp SDK 2.x
    from mcp.server.mcpserver import MCPServer as _Server
except ImportError:  # mcp SDK 1.x
    from mcp.server.fastmcp import FastMCP as _Server  # type: ignore[no-redef]

from bgcoach import analysis, perturb
from bgcoach.engines import EngineError, get_engine
from bgcoach.position import BOTTOM, TOP, XGIDError, parse_xgid

mcp = _Server(
    "bg-engine",
    instructions=(
        "Backgammon position tools for hypothesis-driven analysis. Positions are "
        "XGID strings. Player +1 is the bottom player (uppercase letters in the XGID), "
        "-1 is the top player. Points in perturbation ops are in the acting player's own "
        "numbering (1 = their ace point); 25 = bar, 0 = off. Typical loop: show_position, "
        "evaluate the base, state a hypothesis, build 2-4 variants that would distinguish "
        "it from alternatives, run sweep, read the deltas."
    ),
)

DEFAULT_ENGINE = os.environ.get("BGCOACH_ENGINE", "gnubg")
DEFAULT_PLIES = int(os.environ.get("BGCOACH_PLIES", "2"))
MAX_PLIES = 4


@lru_cache(maxsize=4)
def _engine(name: str):
    return get_engine(name)


def _plies(p: int | None) -> int:
    p = DEFAULT_PLIES if p is None else p
    if not 0 <= p <= MAX_PLIES:
        raise ValueError(f"plies must be 0..{MAX_PLIES}")
    return p


def _err(e: Exception) -> dict:
    return {"error": f"{type(e).__name__}: {e}"}


@mcp.tool()
def show_position(xgid: str) -> dict:
    """Parse an XGID and return an ASCII board plus structured facts.

    Includes pip counts, checkers off, who is on roll, dice or pending cube
    action, cube value/owner, and match score. Use this first to make sure
    you and the engine are looking at the same position.
    """
    try:
        p = parse_xgid(xgid)
    except XGIDError as e:
        return _err(e)
    return {
        "xgid": p.xgid(),
        "ascii": p.ascii(),
        "on_roll": "bottom (+1)" if p.turn == BOTTOM else "top (-1)",
        "dice": list(p.dice) if p.dice else None,
        "cube_action": p.cube_action,
        "cube": {"value": p.cube_value, "owner": p.cube_owner},
        "score": {"bottom": p.score[0], "top": p.score[1], "match_length": p.match_length,
                  "crawford": p.crawford, "money": p.is_money_game,
                  "jacoby": p.jacoby, "beaver": p.beaver},
        "pips": {"bottom": p.pip_count(BOTTOM), "top": p.pip_count(TOP)},
        "off": {"bottom": p.off(BOTTOM), "top": p.off(TOP)},
        "bar": {"bottom": p.bar[0], "top": p.bar[1]},
        "points": {
            "bottom": {pt: n for pt, n in _points(p, BOTTOM)},
            "top": {pt: n for pt, n in _points(p, TOP)},
        },
    }


def _points(p, player):
    from bgcoach.position import iter_points

    return sorted(iter_points(p, player))


@mcp.tool()
def perturb_position(xgid: str, operations: list[dict[str, Any]]) -> dict:
    """Apply a list of edits to a position and return the new XGID and board.

    Each operation is a dict with an "op" key. Points are in the acting
    player's own numbering; 25 = bar, 0 = off. Available ops:

      move        {player, src, dst}            move one checker
      move_point  {player, src, dst}            move every checker on src
      add         {player, point}               bring a borne-off checker back
      remove      {player, point}               take a checker off the board
      make_point  {player, point}               cover a blot (adds from off)
      cube        {value?, owner?}              owner: 0 centered, 1 bottom, -1 top
      dice        {dice: [a, b] | null}         set/clear the roll
      cube_action {action: "D"|"B"|"R"|null}    mark a pending double/beaver/raccoon
      turn        {player}
      score       {bottom, top, match_length?, crawford?}
      away        {bottom_away, top_away, crawford?}
      money       {jacoby?, beaver?}
      dmp         {}
      gammon_go   {player}      player 2-away vs 1-away (their gammons matter)
      gammon_save {player}      player 1-away vs 2-away (must not get gammoned)
      mirror      {}            swap which side is "bottom"

    Edits are not legality-checked beyond "a checker must exist there" and
    "the destination can't be held by the opponent". That is intentional:
    hypothesis tests often want positions that could not arise by a legal
    move from the base.
    """
    try:
        p = perturb.apply(parse_xgid(xgid), operations)
    except (XGIDError, perturb.PerturbError, ValueError) as e:
        return _err(e)
    return {
        "xgid": p.xgid(),
        "ascii": p.ascii(),
        "description": [perturb.describe(op) for op in operations],
    }


@mcp.tool()
def evaluate(xgid: str, plies: int | None = None, engine: str | None = None) -> dict:
    """Evaluate the decision the player on roll faces.

    If the XGID has dice, returns the ranked move list with equities,
    equity errors vs the best move, and win/gammon/backgammon probabilities.
    If it has no dice (or a pending cube action), returns the cube analysis:
    no-double / double-take / double-pass equities and the proper action.

    plies: 0-4 (default 2). 2-ply is roughly XG's "3-ply"; 3-ply is slow but
    noticeably better in volatile positions. Equities are cubeful and
    normalised, from the point of view of the player on roll.
    """
    try:
        p = parse_xgid(xgid)
        ev = _engine(engine or DEFAULT_ENGINE).evaluate(p, plies=_plies(plies))
    except (XGIDError, EngineError, ValueError) as e:
        return _err(e)
    d = ev.to_dict()
    d["headline"] = analysis.headline(ev)
    return d


@mcp.tool()
def sweep(
    xgid: str,
    variants: list[dict[str, Any]],
    plies: int | None = None,
    engine: str | None = None,
    workers: int = 2,
) -> dict:
    """Evaluate a base position and several perturbed variants, with deltas.

    variants: list of {"label": str, "operations": [...]} using the same
    operation dicts as perturb_position. The result includes a "summary"
    table with, per variant, the best move / cube action and its delta
    against the base. This is the main tool for testing a hypothesis:
    design variants where the hypothesis predicts a specific change and
    see whether the engine agrees.

    Keep sweeps to roughly 2-6 variants at a time so each result gets read
    rather than skimmed.
    """
    try:
        base = parse_xgid(xgid)
        spec = [(v.get("label", f"variant {i+1}"), v["operations"]) for i, v in enumerate(variants)]
        # Build first so a bad operation fails before any engine time is spent.
        for label, ops in spec:
            perturb.apply(base, ops)
        result = analysis.run_sweep(
            _engine(engine or DEFAULT_ENGINE), base, spec,
            plies=_plies(plies), workers=max(1, min(workers, 8)),
        )
    except (XGIDError, EngineError, perturb.PerturbError, ValueError, KeyError) as e:
        return _err(e)
    return result.to_dict()


@mcp.tool()
def engines() -> dict:
    """List available engine backends and whether each is usable right now."""
    from bgcoach.engines import REGISTRY
    from bgcoach.engines.gnubg import find_gnubg

    status = {}
    for name in REGISTRY:
        if name == "gnubg":
            path = find_gnubg()
            status[name] = {"available": path is not None, "path": path}
        else:
            status[name] = {"available": None}
    return {"default": DEFAULT_ENGINE, "default_plies": DEFAULT_PLIES, "engines": status}


def main() -> None:
    mcp.run()


if __name__ == "__main__":
    main()
