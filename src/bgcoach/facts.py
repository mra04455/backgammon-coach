"""Position facts: the counts an account relies on, computed rather than read
off the diagram.

``facts(pos)`` describes both sides: made points, home board (own points 1
to 6 only; a point in front of it is a block, not board strength), open
home points, blots, spares, the longest prime, anchors, bar, off, pips and
entering numbers. ``play_facts(pos, play)`` applies a candidate play and
adds what the opponent can then do about it (shots at each blot, entering
numbers) and what the mover can do next turn (point-making numbers for
open home points, covering numbers for slots).
"""

from __future__ import annotations

from typing import Any

from bgcoach import moves as mv
from bgcoach.position import BOTTOM, TOP, Position, own_point_to_index

HOME = range(1, 7)


def _count(pos: Position, player: int, point: int) -> int:
    v = pos.board[own_point_to_index(player, point)]
    return v if player == BOTTOM else -v


def side_facts(pos: Position, player: int) -> dict[str, Any]:
    """Facts about one side, in that side's own numbering."""
    counts = {p: _count(pos, player, p) for p in range(1, 25)}
    own = {p: c for p, c in counts.items() if c > 0}
    made = sorted(p for p, c in own.items() if c >= 2)
    opp_counts = {p: -c for p, c in counts.items() if c < 0}
    home_made = [p for p in made if p in HOME]
    home_open = [p for p in HOME if p not in home_made]
    blots = sorted(p for p, c in own.items() if c == 1)
    spares = {p: c - 2 for p, c in own.items() if c >= 3}
    # longest run of consecutive made points anywhere
    best: tuple[int, int] | None = None
    run_start = None
    for p in range(1, 26):
        if p in made and p < 25:
            run_start = p if run_start is None else run_start
        else:
            if run_start is not None:
                length = p - run_start
                if best is None or length > best[1] - best[0] + 1:
                    best = (run_start, p - 1)
                run_start = None
    prime = None
    if best is not None and best[1] - best[0] + 1 >= 3:
        prime = {"from": best[0], "to": best[1], "length": best[1] - best[0] + 1}
    anchors = [p for p in made if p >= 19]
    out: dict[str, Any] = {
        "player": player,
        "label": "X (bottom)" if player == BOTTOM else "O (top)",
        "pips": pos.pip_count(player),
        "on_bar": pos.on_bar(player),
        "off": pos.off(player),
        "checkers": own,
        "made_points": made,
        "home_board": {"made": home_made, "count": len(home_made), "open": home_open},
        "blots": blots,
        "spares": spares,
        "prime": prime,
        "anchors": anchors,
        "opponent_checkers_in_my_home": {p: n for p, n in opp_counts.items() if p in HOME},
    }
    if pos.on_bar(player):
        out["entering"] = mv.entering_rolls(pos, player)
    return out


def facts(pos: Position) -> dict[str, Any]:
    x, o = side_facts(pos, BOTTOM), side_facts(pos, TOP)
    lead = o["pips"] - x["pips"]
    d: dict[str, Any] = {
        "xgid": pos.xgid(),
        "on_roll": pos.turn,
        "dice": list(pos.dice) if pos.dice else None,
        "cube": {"value": pos.cube_value, "owner": pos.cube_owner},
        "race": {"X": x["pips"], "O": o["pips"], "X_leads_by": lead},
        "X": x,
        "O": o,
    }
    if pos.dice is not None:
        d["legal_plays"] = len(mv.legal_plays(pos))
    return d


def threats(pos: Position, attacker: int) -> dict[str, Any]:
    """What ``attacker`` can do on the coming roll: shots at each of the
    defender's blots (defender's own numbering), and entering numbers if
    the attacker has checkers on the bar."""
    defender = -attacker
    out: dict[str, Any] = {"attacker": attacker, "shots": []}
    for blot in side_facts(pos, defender)["blots"]:
        n, rolls = mv.hitting_rolls(pos, attacker, blot)
        if n:
            out["shots"].append(
                {"blot_on_defender_point": blot, "rolls": n, "of": 36, "dice": rolls}
            )
    any_hit, _ = mv.rolls_where(pos, attacker, lambda p: any(s.hit for s in p.steps))
    out["rolls_hitting_anything"] = any_hit
    if pos.on_bar(attacker):
        out["entering"] = mv.entering_rolls(pos, attacker)
    return out


def next_turn_chances(pos: Position, player: int) -> dict[str, Any]:
    """What ``player`` can do if the opponent does nothing to the position:
    rolls that make each open home point, and rolls that cover each blot."""
    side = side_facts(pos, player)
    out: dict[str, Any] = {"player": player, "make_home_point": {}, "cover_blot": {}}
    for p in side["home_board"]["open"]:
        n, _ = mv.point_making_rolls(pos, player, p)
        out["make_home_point"][p] = n
    for b in side["blots"]:
        n, _ = mv.point_making_rolls(pos, player, b)
        out["cover_blot"][b] = n
    return out


def play_facts(pos: Position, play: str) -> dict[str, Any]:
    """Facts after ``play`` by the player on roll: the resulting position,
    the opponent's threats against it, and the mover's chances next turn
    (computed as if the opponent's roll changed nothing)."""
    mover = pos.turn
    after = mv.apply_play(pos, play).with_(turn=-mover, dice=None)
    legal = mv.find_play(pos, play) is not None
    mine_next = after.with_(turn=mover)
    return {
        "play": play,
        "legal": legal,
        "after": facts(after),
        "opponent_threats": threats(after, -mover),
        "my_next_turn": next_turn_chances(mine_next, mover),
    }
