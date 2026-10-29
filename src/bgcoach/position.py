"""Position model and XGID codec.

XGID is the position notation used by eXtreme Gammon and accepted by
GNU Backgammon (``set xgid``). It looks like::

    XGID=-b----E-C---eE---c-e----B-:0:0:1:31:0:0:0:0:10

Fields, colon-separated after the 26-character board string:

    1. board      26 chars (see below)
    2. cube       log2 of the cube value (0 = 1, 1 = 2, 2 = 4, ...)
    3. owner      0 = centered, 1 = bottom player owns, -1 = top player owns
    4. turn       1 = bottom player on roll, -1 = top player on roll
    5. dice       two digits ("31"), "00" if not rolled, or a cube action
                  letter: "D" double offered, "B" beaver, "R" raccoon
    6. score      bottom player's score
    7. score      top player's score
    8. flag       match play: 1 = Crawford game. Money play: bit 0 = Jacoby,
                  bit 1 = beavers allowed.
    9. length     match length, 0 = money game
   10. max cube   log2 of the cube cap (10 = 1024). Optional; defaults to 10.

Board string: index 0 is the TOP player's bar, indices 1..24 are points
1..24 numbered from the BOTTOM player's point of view, index 25 is the
BOTTOM player's bar. Uppercase A..O = 1..15 bottom-player checkers,
lowercase a..o = 1..15 top-player checkers, '-' = empty. Checkers borne
off are not encoded; each side has 15 total.

Within this package the bottom player is ``+1`` and the top player is
``-1``. "Bottom" and "top" are just the two sides of the XGID frame; who is
on roll is the separate ``turn`` field.

The field semantics above were checked against several real XGIDs
(starting position, a mid-match position with an owned cube, a bear-off).
The money-play meaning of field 8 (Jacoby/beaver bits) is the least
certain part and is worth confirming against an XGID exported from XG
with beavers on.
"""

from __future__ import annotations

import re
from collections.abc import Iterator
from dataclasses import dataclass, replace

BOTTOM = 1
TOP = -1
CHECKERS_PER_SIDE = 15

_XGID_RE = re.compile(r"^(?:XGID=)?([A-Oa-o-]{26})((?::[^:]*){8,9})$")


class XGIDError(ValueError):
    """Raised when an XGID string cannot be parsed."""


@dataclass(frozen=True)
class Position:
    """An immutable backgammon position in the XGID frame.

    ``board[i]`` is the number of checkers on point ``i + 1`` (bottom
    player's numbering). Positive values are bottom-player checkers,
    negative values are top-player checkers. ``bar`` is ``(bottom, top)``.
    """

    board: tuple[int, ...]
    bar: tuple[int, int] = (0, 0)
    cube_value: int = 1
    cube_owner: int = 0  # 0 centered, +1 bottom, -1 top
    turn: int = BOTTOM
    dice: tuple[int, int] | None = None
    cube_action: str | None = None  # "D", "B", or "R" when a cube is offered
    score: tuple[int, int] = (0, 0)  # (bottom, top)
    match_length: int = 0  # 0 = money game
    crawford: bool = False
    jacoby: bool = False
    beaver: bool = False
    max_cube: int = 1024

    # ------------------------------------------------------------------
    # Validation
    # ------------------------------------------------------------------

    def __post_init__(self) -> None:
        if len(self.board) != 24:
            raise ValueError("board must have 24 points")
        if any(b < 0 for b in self.bar):
            raise ValueError("bar counts cannot be negative")
        for player in (BOTTOM, TOP):
            total = self.on_board(player) + self.on_bar(player)
            if total > CHECKERS_PER_SIDE:
                raise ValueError(
                    f"player {player} has {total} checkers; max is {CHECKERS_PER_SIDE}"
                )
        if self.turn not in (BOTTOM, TOP):
            raise ValueError("turn must be +1 (bottom) or -1 (top)")
        if self.cube_owner not in (0, BOTTOM, TOP):
            raise ValueError("cube_owner must be 0, +1 or -1")
        if self.cube_value < 1 or self.cube_value & (self.cube_value - 1):
            raise ValueError("cube_value must be a power of two")
        if self.dice is not None and self.cube_action is not None:
            raise ValueError("a position has either dice or a pending cube action, not both")
        if self.cube_action is not None and self.cube_action not in ("D", "B", "R"):
            raise ValueError("cube_action must be 'D', 'B' or 'R'")

    # ------------------------------------------------------------------
    # Derived quantities
    # ------------------------------------------------------------------

    def on_board(self, player: int) -> int:
        """Checkers on the 24 points for ``player``."""
        if player == BOTTOM:
            return sum(b for b in self.board if b > 0)
        return sum(-b for b in self.board if b < 0)

    def on_bar(self, player: int) -> int:
        return self.bar[0] if player == BOTTOM else self.bar[1]

    def off(self, player: int) -> int:
        """Checkers already borne off by ``player``."""
        return CHECKERS_PER_SIDE - self.on_board(player) - self.on_bar(player)

    def checkers_on(self, player: int, point: int) -> int:
        """Checkers ``player`` has on ``point`` in *their own* numbering (1..24)."""
        idx = own_point_to_index(player, point)
        v = self.board[idx]
        return v if player == BOTTOM else -v

    def pip_count(self, player: int) -> int:
        pips = 25 * self.on_bar(player)
        for idx, v in enumerate(self.board):
            point = idx + 1
            if player == BOTTOM and v > 0:
                pips += v * point
            elif player == TOP and v < 0:
                pips += (-v) * (25 - point)
        return pips

    @property
    def on_roll(self) -> int:
        return self.turn

    @property
    def is_money_game(self) -> bool:
        return self.match_length == 0

    def away(self, player: int) -> int | None:
        """Points ``player`` still needs to win the match, or None in money play."""
        if self.is_money_game:
            return None
        s = self.score[0] if player == BOTTOM else self.score[1]
        return self.match_length - s

    # ------------------------------------------------------------------
    # Transformations (the perturbation library builds on these)
    # ------------------------------------------------------------------

    def with_(self, **changes) -> Position:
        return replace(self, **changes)

    def mirror(self) -> Position:
        """The same position seen from the other side of the board.

        Swaps which player is "bottom": the board is reversed and negated,
        bars and scores are swapped, and cube owner / turn are negated.
        Useful for engines that want the player on roll at the bottom.
        """
        return Position(
            board=tuple(-b for b in reversed(self.board)),
            bar=(self.bar[1], self.bar[0]),
            cube_value=self.cube_value,
            cube_owner=-self.cube_owner,
            turn=-self.turn,
            dice=self.dice,
            cube_action=self.cube_action,
            score=(self.score[1], self.score[0]),
            match_length=self.match_length,
            crawford=self.crawford,
            jacoby=self.jacoby,
            beaver=self.beaver,
            max_cube=self.max_cube,
        )

    # ------------------------------------------------------------------
    # Serialisation
    # ------------------------------------------------------------------

    def xgid(self, *, prefix: bool = True) -> str:
        """Encode as an XGID string."""
        chars = ["-"] * 26
        chars[0] = _encode_cell(-self.bar[1])  # top bar, lowercase
        for idx, v in enumerate(self.board):
            chars[idx + 1] = _encode_cell(v)
        chars[25] = _encode_cell(self.bar[0])  # bottom bar, uppercase

        if self.cube_action is not None:
            dice = self.cube_action
        elif self.dice is None:
            dice = "00"
        else:
            dice = f"{self.dice[0]}{self.dice[1]}"

        if self.is_money_game:
            flag = (1 if self.jacoby else 0) | (2 if self.beaver else 0)
        else:
            flag = 1 if self.crawford else 0

        fields = [
            "".join(chars),
            str(self.cube_value.bit_length() - 1),
            str(self.cube_owner),
            str(self.turn),
            dice,
            str(self.score[0]),
            str(self.score[1]),
            str(flag),
            str(self.match_length),
            str(self.max_cube.bit_length() - 1),
        ]
        body = ":".join(fields)
        return f"XGID={body}" if prefix else body

    def __str__(self) -> str:
        return self.xgid()

    def ascii(self) -> str:
        """A simple ASCII board, bottom player's home board at lower right."""
        return render_ascii(self)


# ----------------------------------------------------------------------
# Point numbering helpers
# ----------------------------------------------------------------------


def own_point_to_index(player: int, point: int) -> int:
    """Map a point in ``player``'s own numbering (1..24) to a board index."""
    if not 1 <= point <= 24:
        raise ValueError(f"point must be 1..24, got {point}")
    return point - 1 if player == BOTTOM else 24 - point


def index_to_own_point(player: int, idx: int) -> int:
    return idx + 1 if player == BOTTOM else 24 - idx


# ----------------------------------------------------------------------
# Parsing
# ----------------------------------------------------------------------


def _decode_cell(ch: str) -> int:
    if ch == "-":
        return 0
    if "A" <= ch <= "O":
        return ord(ch) - ord("A") + 1
    if "a" <= ch <= "o":
        return -(ord(ch) - ord("a") + 1)
    raise XGIDError(f"bad board character {ch!r}")


def _encode_cell(v: int) -> str:
    if v == 0:
        return "-"
    if v > 15 or v < -15:
        raise ValueError(f"too many checkers on one point: {v}")
    return chr(ord("A") + v - 1) if v > 0 else chr(ord("a") - v - 1)


def parse_xgid(text: str) -> Position:
    """Parse an XGID string (with or without the ``XGID=`` prefix)."""
    s = text.strip()
    m = _XGID_RE.match(s)
    if not m:
        raise XGIDError(f"not an XGID: {text!r}")
    board_str = m.group(1)
    rest = m.group(2).lstrip(":").split(":")
    if len(rest) == 8:
        rest.append("10")
    if len(rest) != 9:
        raise XGIDError(f"expected 8 or 9 fields after the board, got {len(rest)}")

    cells = [_decode_cell(c) for c in board_str]
    top_bar = -cells[0]
    bottom_bar = cells[25]
    board = tuple(cells[1:25])
    if top_bar < 0 or bottom_bar < 0:
        raise XGIDError("bar cells have the wrong case (index 0 must be lowercase, 25 uppercase)")

    try:
        cube_exp = int(rest[0])
        owner = int(rest[1])
        turn = int(rest[2])
        dice_str = rest[3]
        s1 = int(rest[4])
        s2 = int(rest[5])
        flag = int(rest[6])
        length = int(rest[7])
        max_exp = int(rest[8])
    except ValueError as e:
        raise XGIDError(f"bad numeric field in {text!r}: {e}") from e

    dice: tuple[int, int] | None = None
    cube_action: str | None = None
    if dice_str in ("D", "B", "R"):
        cube_action = dice_str
    elif dice_str == "00":
        dice = None
    elif re.fullmatch(r"[1-6][1-6]", dice_str):
        dice = (int(dice_str[0]), int(dice_str[1]))
    else:
        raise XGIDError(f"bad dice field {dice_str!r}")

    if length == 0:
        crawford, jacoby, beaver = False, bool(flag & 1), bool(flag & 2)
    else:
        crawford, jacoby, beaver = bool(flag), False, False

    try:
        return Position(
            board=board,
            bar=(bottom_bar, top_bar),
            cube_value=1 << cube_exp,
            cube_owner=owner,
            turn=turn,
            dice=dice,
            cube_action=cube_action,
            score=(s1, s2),
            match_length=length,
            crawford=crawford,
            jacoby=jacoby,
            beaver=beaver,
            max_cube=1 << max_exp,
        )
    except ValueError as e:
        raise XGIDError(str(e)) from e


def is_xgid(text: str) -> bool:
    try:
        parse_xgid(text)
        return True
    except XGIDError:
        return False


# ----------------------------------------------------------------------
# Well-known positions
# ----------------------------------------------------------------------

STARTING_XGID = "XGID=-b----E-C---eE---c-e----B-:0:0:1:00:0:0:0:0:10"


def starting_position(**overrides) -> Position:
    return parse_xgid(STARTING_XGID).with_(**overrides)


# ----------------------------------------------------------------------
# Rendering
# ----------------------------------------------------------------------


def render_ascii(pos: Position) -> str:
    """Render like gnubg: top row is points 13..24, bottom row 12..1.

    Bottom player is 'X' (moves toward point 1), top player is 'O'.
    """

    def col(point: int) -> list[str]:
        v = pos.board[point - 1]
        sym = "X" if v > 0 else "O"
        n = abs(v)
        cells = [sym if i < min(n, 5) else " " for i in range(5)]
        if n > 5:
            cells[4] = str(n) if n < 10 else chr(ord("A") + n - 10)
        return cells

    def bar_cell(count: int, row: int, sym: str) -> str:
        if count > row:
            return sym if not (row == 4 and count > 5) else str(count)
        return " "

    def header(points: list[int]) -> str:
        return (
            " +"
            + "".join(f"{p:->3}" for p in points[:6])
            + "-+---+"
            + "".join(f"{p:->3}" for p in points[6:])
            + "-+"
        )

    def row_line(points: list[int], row: int, bar: str) -> str:
        left = "".join(f"{col(p)[row]:^3}" for p in points[:6])
        right = "".join(f"{col(p)[row]:^3}" for p in points[6:])
        return f" |{left} |{bar:^3}|{right} |"

    top_points = list(range(13, 25))
    bot_points = list(range(12, 0, -1))
    lines: list[str] = []
    lines.append(header(top_points))
    for row in range(5):
        lines.append(row_line(top_points, row, bar_cell(pos.bar[1], row, "O")))
    lines.append(" |" + " " * 18 + " |BAR|" + " " * 18 + " |")
    for row in range(4, -1, -1):
        lines.append(row_line(bot_points, row, bar_cell(pos.bar[0], row, "X")))
    lines.append(header(bot_points))

    who = "X (bottom)" if pos.turn == BOTTOM else "O (top)"
    if pos.cube_action:
        action = {"D": "double offered", "B": "beaver offered", "R": "raccoon offered"}[
            pos.cube_action
        ]
        dice = f"{action} by {who}"
    elif pos.dice:
        dice = f"{who} to play {pos.dice[0]}{pos.dice[1]}"
    else:
        dice = f"{who} on roll (cube decision)"
    owner = {0: "centered", BOTTOM: "owned by X", TOP: "owned by O"}[pos.cube_owner]
    if pos.is_money_game:
        rules = (
            "money game" + (", Jacoby" if pos.jacoby else "") + (", beavers" if pos.beaver else "")
        )
    else:
        rules = f"{pos.match_length}-pt match, X {pos.score[0]} - O {pos.score[1]}"
        if pos.crawford:
            rules += " (Crawford)"
    lines.append(f" {dice}. Cube {pos.cube_value} ({owner}). {rules}.")
    lines.append(
        f" Pips: X {pos.pip_count(BOTTOM)}, O {pos.pip_count(TOP)}."
        f" Off: X {pos.off(BOTTOM)}, O {pos.off(TOP)}."
    )
    lines.append(f" {pos.xgid()}")
    return "\n".join(lines)


def iter_points(pos: Position, player: int) -> Iterator[tuple[int, int]]:
    """Yield ``(own_point, count)`` for every point where ``player`` has checkers."""
    for idx, v in enumerate(pos.board):
        if player == BOTTOM and v > 0:
            yield idx + 1, v
        elif player == TOP and v < 0:
            yield 24 - idx, -v
