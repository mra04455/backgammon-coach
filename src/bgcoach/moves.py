"""Legal plays for one roll, and the arithmetic that depends on them.

Everything the analyst used to count by eye lives here: which plays are
legal, which rolls hit a blot, which rolls enter from the bar, which rolls
make a point. Counts are exact, from full legal-move generation, so they
include combination shots, blocked intermediate points and the rule that
a checker on the bar must enter before anything else moves.

Conventions follow :mod:`bgcoach.position`: ``player`` is ``+1`` (bottom)
or ``-1`` (top); points are in the acting player's own numbering (1 = ace
point); ``BAR = 25`` and ``OFF = 0``.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from itertools import combinations_with_replacement

from bgcoach.position import BOTTOM, Position, own_point_to_index

BAR = 25
OFF = 0

ALL_ROLLS: tuple[tuple[int, int], ...] = tuple(combinations_with_replacement(range(1, 7), 2))


def roll_weight(roll: tuple[int, int]) -> int:
    """How many of the 36 dice outcomes this unordered roll stands for."""
    return 1 if roll[0] == roll[1] else 2


@dataclass(frozen=True)
class Step:
    src: int  # own numbering; BAR for entering
    dst: int  # own numbering; OFF for bearing off
    hit: bool


@dataclass(frozen=True)
class Play:
    steps: tuple[Step, ...]
    result: Position

    def __str__(self) -> str:
        return format_play(self.steps)


# ----------------------------------------------------------------------
# Board scratch state
# ----------------------------------------------------------------------


class _State:
    """Mutable board for generation; converted back to Position at the end."""

    __slots__ = ("board", "bar", "player", "sign")

    def __init__(self, pos: Position, player: int) -> None:
        self.board = list(pos.board)
        self.bar = list(pos.bar)  # (bottom, top)
        self.player = player
        self.sign = 1 if player == BOTTOM else -1

    def copy(self) -> _State:
        s = _State.__new__(_State)
        s.board = self.board[:]
        s.bar = self.bar[:]
        s.player = self.player
        s.sign = self.sign
        return s

    def own(self, point: int) -> int:
        """Own checkers on own point 1..24 (negative means opponent's)."""
        return self.board[own_point_to_index(self.player, point)] * self.sign

    def on_bar(self) -> int:
        return self.bar[0 if self.player == BOTTOM else 1]

    def all_home(self) -> bool:
        if self.on_bar():
            return False
        return all(self.own(p) <= 0 for p in range(7, 25))

    def highest_point(self) -> int:
        for p in range(24, 0, -1):
            if self.own(p) > 0:
                return p
        return 0

    def step(self, src: int, die: int) -> Step | None:
        """Try to move one checker from ``src`` by ``die``; return the Step or None."""
        if self.on_bar() and src != BAR:
            return None
        if src == BAR:
            dst = 25 - die
        else:
            if self.own(src) <= 0:
                return None
            dst = src - die
        if dst <= 0:
            if not self.all_home():
                return None
            if dst < 0 and self.highest_point() != src:
                return None
            dst = OFF
        hit = False
        if dst != OFF:
            occ = self.own(dst)
            if occ <= -2:
                return None
            hit = occ == -1
        # apply
        if src == BAR:
            self.bar[0 if self.player == BOTTOM else 1] -= 1
        else:
            self.board[own_point_to_index(self.player, src)] -= self.sign
        if dst != OFF:
            idx = own_point_to_index(self.player, dst)
            if hit:
                self.board[idx] = 0
                self.bar[1 if self.player == BOTTOM else 0] += 1
            self.board[idx] += self.sign
        return Step(src, dst, hit)

    def to_position(self, pos: Position) -> Position:
        return pos.with_(board=tuple(self.board), bar=(self.bar[0], self.bar[1]))

    def key(self) -> tuple:
        return (tuple(self.board), tuple(self.bar))


def _sources(state: _State) -> list[int]:
    if state.on_bar():
        return [BAR]
    return [p for p in range(1, 25) if state.own(p) > 0]


def _extend(state: _State, dice: list[int], steps: list[Step], out: dict) -> None:
    """Depth-first over die orders; record every maximal sequence."""
    moved_any = False
    for i, die in enumerate(dice):
        if i > 0 and dice[i] in dice[:i]:
            continue  # same die value already tried at this depth
        for src in _sources(state):
            s2 = state.copy()
            st = s2.step(src, die)
            if st is None:
                continue
            moved_any = True
            rest = dice[:i] + dice[i + 1 :]
            _extend(s2, rest, steps + [st], out)
    if not moved_any:
        key = state.key()
        n = len(steps)
        prev = out.get(key)
        if prev is None or n > len(prev[0]):
            out[key] = (tuple(steps), state)


def legal_plays(
    pos: Position, player: int | None = None, dice: tuple[int, int] | None = None
) -> list[Play]:
    """All legal plays for ``player`` (default: the player on roll) with ``dice``
    (default: the position's dice). Plays leading to the same position are
    reported once. Includes the rules: enter first, use both dice if you
    can, otherwise the higher one, doubles move up to four times."""
    player = pos.turn if player is None else player
    dice = pos.dice if dice is None else dice
    if dice is None:
        raise ValueError("no dice: pass dice=(a, b)")
    a, b = dice
    dice_list = [a] * 4 if a == b else [a, b]
    out: dict = {}
    _extend(_State(pos, player), dice_list, [], out)
    if not out:
        return []
    max_len = max(len(steps) for steps, _ in out.values())
    kept = [(steps, st) for steps, st in out.values() if len(steps) == max_len]
    if max_len == 1 and a != b:
        hi = max(a, b)
        with_hi = [(s, st) for s, st in kept if _die_of(s[0]) == hi]
        if with_hi:
            kept = with_hi
    if max_len == 0:
        return []
    plays = [Play(steps, st.to_position(pos)) for steps, st in kept]
    plays.sort(key=lambda p: str(p))
    return plays


def _die_of(step: Step) -> int:
    if step.src == BAR:
        return 25 - step.dst
    if step.dst == OFF:
        return step.src  # exact or higher; only used to pick the higher die
    return step.src - step.dst


# ----------------------------------------------------------------------
# Notation
# ----------------------------------------------------------------------


def _pt(p: int) -> str:
    return "bar" if p == BAR else "off" if p == OFF else str(p)


def format_play(steps: tuple[Step, ...] | list[Step]) -> str:
    """gnubg-style notation: chains for one checker moving twice
    (``13/7*/5``), ``(n)`` for repeats, ``*`` on hits."""
    chains: list[list[Step]] = []
    for st in steps:
        for ch in chains:
            if ch[-1].dst == st.src and st.src not in (OFF,):
                ch.append(st)
                break
        else:
            chains.append([st])
    # gnubg's order: higher source point first (the bar counts as 25).
    chains.sort(key=lambda ch: (-ch[0].src, -ch[0].dst))
    parts: list[str] = []
    for ch in chains:
        text = _pt(ch[0].src)
        for st in ch:
            text += "/" + _pt(st.dst) + ("*" if st.hit else "")
        parts.append(text)
    counted: list[str] = []
    for part in parts:
        if counted and counted[-1].split("(")[0] == part:
            prev = counted[-1]
            m = re.search(r"\((\d+)\)$", prev)
            n = int(m.group(1)) + 1 if m else 2
            counted[-1] = f"{part}({n})"
        else:
            counted.append(part)
    return " ".join(counted)


def parse_play(text: str) -> list[tuple[int, int]]:
    """``"bar/24 13/7*/5 8/4(2)"`` -> [(25, 24), (13, 7), (7, 5), (8, 4), (8, 4)]."""
    out: list[tuple[int, int]] = []
    for tok in text.split():
        m = re.fullmatch(r"(.+?)(?:\((\d+)\))?", tok)
        body, rep = m.group(1), int(m.group(2) or 1)
        pts = [p.rstrip("*") for p in body.split("/")]
        nums = [BAR if p.lower() == "bar" else OFF if p.lower() == "off" else int(p) for p in pts]
        for _ in range(rep):
            for a, b in zip(nums, nums[1:], strict=False):
                out.append((a, b))
    return out


def apply_play(pos: Position, text: str, player: int | None = None) -> Position:
    """Apply a play in gnubg notation for ``player`` (default: on roll),
    hitting and bearing off as the board dictates. Does not check that the
    play is legal for the dice; use :func:`find_play` for that."""
    player = pos.turn if player is None else player
    state = _State(pos, player)
    for src, dst in parse_play(text):
        die = (25 - dst) if src == BAR else (src - dst if dst != OFF else src)
        if dst == OFF and state.step(src, die) is None:
            # bearing off with a higher die: find the die by brute force
            for d in range(src, 7):
                if state.copy().step(src, d) is not None:
                    state.step(src, d)
                    break
            else:
                raise ValueError(f"cannot bear off from {src} in {text!r}")
            continue
        if state.step(src, die) is None:
            raise ValueError(f"illegal step {_pt(src)}/{_pt(dst)} in {text!r}")
    return state.to_position(pos)


def find_play(pos: Position, text: str) -> Play | None:
    """The legal play whose result matches ``text`` applied to ``pos``, or None."""
    try:
        target = apply_play(pos, text)
    except ValueError:
        return None
    for p in legal_plays(pos):
        if p.result.board == target.board and p.result.bar == target.bar:
            return p
    return None


# ----------------------------------------------------------------------
# Counts
# ----------------------------------------------------------------------


def rolls_where(pos: Position, player: int, predicate) -> tuple[int, list[tuple[int, int]]]:
    """Number of the 36 dice outcomes for which some legal play by ``player``
    satisfies ``predicate(play)``, plus the unordered rolls that do."""
    total = 0
    rolls: list[tuple[int, int]] = []
    for roll in ALL_ROLLS:
        if any(predicate(p) for p in legal_plays(pos, player, roll)):
            total += roll_weight(roll)
            rolls.append(roll)
    return total, rolls


def hitting_rolls(
    pos: Position, attacker: int, target_defender_point: int
) -> tuple[int, list[tuple[int, int]]]:
    """Rolls with which ``attacker`` can hit the defender's blot on
    ``target_defender_point`` (defender's own numbering)."""
    attacker_point = 25 - target_defender_point
    return rolls_where(
        pos, attacker, lambda p: any(s.hit and s.dst == attacker_point for s in p.steps)
    )


def entering_rolls(pos: Position, player: int) -> dict:
    """For a player with checkers on the bar: which dice enter, how many of
    36 rolls enter at least one checker, and how many enter all of them."""
    sign = 1 if player == BOTTOM else -1
    on_bar = pos.on_bar(player)
    entering_dice = [
        d for d in range(1, 7) if pos.board[own_point_to_index(player, 25 - d)] * sign > -2
    ]
    if on_bar == 0:
        return {"on_bar": 0, "entering_dice": entering_dice}
    at_least_one, _ = rolls_where(pos, player, lambda p: any(s.src == BAR for s in p.steps))
    everyone, _ = rolls_where(
        pos, player, lambda p: sum(1 for s in p.steps if s.src == BAR) >= min(on_bar, 4)
    )
    return {
        "on_bar": on_bar,
        "entering_dice": entering_dice,
        "rolls_entering_one": at_least_one,
        "rolls_entering_all": everyone,
    }


def point_making_rolls(pos: Position, player: int, point: int) -> tuple[int, list[tuple[int, int]]]:
    """Rolls after which ``player`` can hold ``point`` (own numbering) with
    two or more checkers."""
    sign = 1 if player == BOTTOM else -1
    idx = own_point_to_index(player, point)
    return rolls_where(pos, player, lambda p: p.result.board[idx] * sign >= 2)
