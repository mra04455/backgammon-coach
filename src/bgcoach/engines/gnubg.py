"""GNU Backgammon backend.

Drives the ``gnubg`` command-line program with a command file and parses
the text output of ``hint``. Validated against gnubg 1.07.001 (2024).

Why a command file rather than the Python bindings: it works with any
stock gnubg install (brew, apt, the Windows ``gnubg-cli.exe``) and needs
nothing compiled. Swapping in the ``gnubg`` PyPI bindings later is a
contained change inside this module.

Two gnubg CLI quirks this module handles for you:

1. ``set xgid`` only takes effect once a game exists, so we issue
   ``new match 0`` first. gnubg then prints a stray opening roll and an
   ASCII board; both are ignored.
2. Move filters. A move filter whose *accept* count is 0 is treated as
   "skip this ply" by the CLI, which silently drops every move to 0-ply
   even when you asked for 2-ply. We always set positive accept counts.
   Verified empirically: with ``accept 0, extra 8`` every move came back
   ``0-ply``; with ``accept 8`` they came back ``2-ply``.
"""

from __future__ import annotations

import os
import re
import shutil
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path

from bgcoach.engines.base import (
    CubeEval,
    EngineError,
    Evaluation,
    MoveEval,
    Probs,
    StaticEval,
)
from bgcoach.position import Position

DEFAULT_BINARY_CANDIDATES = ("gnubg", "gnubg-cli", "/usr/games/gnubg")


def find_gnubg() -> str | None:
    """Locate the gnubg executable: $BGCOACH_GNUBG, then common names."""
    env = os.environ.get("BGCOACH_GNUBG")
    if env:
        return env if Path(env).exists() or shutil.which(env) else None
    for cand in DEFAULT_BINARY_CANDIDATES:
        if shutil.which(cand) or Path(cand).exists():
            return cand
    return None


@dataclass(frozen=True)
class MoveFilter:
    """How many candidate moves survive to the deeper plies.

    ``accept`` moves are always searched at the next ply; up to ``extra``
    more are added if within ``threshold`` equity of the best. Must be
    positive (see module docstring).
    """

    accept: int = 8
    extra: int = 4
    threshold: float = 0.16


_MOVE_RE = re.compile(
    r"^\s*(?P<rank>\d+)\.\s+(?P<cubeful>Cubeful|Cubeless)\s+(?P<ply>\S+)\s+"
    r"(?P<move>.+?)\s+(?:Eq\.|MWC):\s*(?P<eq>[+-]?\d+\.\d+)%?"
    r"(?:\s*\(\s*(?P<err>[+-]?\d+\.\d+)%?\s*\))?\s*$"
)
_PROBS_RE = re.compile(
    r"^\s*(\d\.\d+)\s+(\d\.\d+)\s+(\d\.\d+)\s+-\s+(\d\.\d+)\s+(\d\.\d+)\s+(\d\.\d+)\s*$"
)
_CUBE_EQ_RE = re.compile(
    r"^\s*\d\.\s+(?P<label>No (?:re)?double|(?:Re)?[Dd]ouble, take|(?:Re)?[Dd]ouble, pass)\s+"
    r"(?P<eq>[+-]?\d+\.\d+)"
)
_CUBELESS_RE = re.compile(r"^\s*(?P<ply>\S+)\s+cubeless equity\s+(?P<eq>[+-]?\d+\.\d+)")
_PROPER_RE = re.compile(r"^\s*Proper cube action:\s*(?P<action>.+?)\s*(?:\([^)]*\))?\s*$")
# Rows of the `eval` table: "static:" / " 1 ply:" / " 2 ply:" then
# Win W(g) W(bg) L(g) L(bg) Equity Cubeful
_EVAL_ROW_RE = re.compile(
    r"^\s*(?P<ply>static|\d+ ply):\s+"
    r"(?P<win>\d\.\d+)\s+(?P<wg>\d\.\d+)\s+(?P<wbg>\d\.\d+)\s+"
    r"(?P<lg>\d\.\d+)\s+(?P<lbg>\d\.\d+)\s+"
    r"(?P<eq>[+-]?\d+\.\d+)\s+(?P<cubeful>[+-]?\d+\.\d+)"
)
_CANNOT_DOUBLE_RE = re.compile(r"cannot double", re.IGNORECASE)


class GnubgEngine:
    name = "gnubg"

    def __init__(
        self,
        binary: str | None = None,
        *,
        move_filter: MoveFilter = MoveFilter(),
        timeout: float = 600.0,
    ) -> None:
        self.binary = binary or find_gnubg()
        if self.binary is None:
            raise EngineError(
                "gnubg not found. Install GNU Backgammon (brew install gnubg / "
                "apt install gnubg / the Windows installer, which provides gnubg-cli.exe) "
                "or set BGCOACH_GNUBG to the executable path."
            )
        self.move_filter = move_filter
        self.timeout = timeout

    # ------------------------------------------------------------------

    def build_commands(self, position: Position, *, plies: int) -> str:
        if not 0 <= plies <= 4:
            raise ValueError("plies must be 0..4")
        mf = self.move_filter
        lines = [
            "set lang C",
            "set output mwc off",
            "set output rawboard off",
            "set player 0 human",
            "set player 1 human",
            f"set evaluation chequerplay evaluation plies {plies}",
            "set evaluation chequerplay evaluation cubeful on",
            f"set evaluation cubedecision evaluation plies {plies}",
            "set evaluation cubedecision evaluation cubeful on",
        ]
        # Positive accept counts at every ply; even plies filter, odd plies
        # pass everything through (gnubg's own convention).
        for ply in range(1, 5):
            for level in range(ply):
                if level % 2 == 0:
                    lines.append(
                        f"set evaluation movefilter {ply} {level} "
                        f"{mf.accept} {mf.extra} {mf.threshold}"
                    )
                else:
                    lines.append(f"set evaluation movefilter {ply} {level} -1 0 0")
        lines += [
            "new match 0",
            f"set xgid {position.xgid()}",
            "hint",
        ]
        if position.dice is None:
            # For cube positions also ask for the plain position evaluation,
            # which is all gnubg will give when the cube is dead or owned by
            # the opponent ("You cannot double").
            lines.append("eval")
        return "\n".join(lines) + "\n"

    def run_raw(self, commands: str) -> str:
        with tempfile.TemporaryDirectory(prefix="bgcoach-gnubg-") as tmp:
            cmd_path = Path(tmp) / "commands.txt"
            cmd_path.write_text(commands)
            try:
                proc = subprocess.run(
                    [self.binary, "-t", "-q", "-c", str(cmd_path)],
                    capture_output=True,
                    text=True,
                    timeout=self.timeout,
                    check=False,
                )
            except FileNotFoundError as e:
                raise EngineError(f"could not run {self.binary}: {e}") from e
            except subprocess.TimeoutExpired as e:
                raise EngineError(f"gnubg timed out after {self.timeout}s") from e
        out = proc.stdout + ("\n" + proc.stderr if proc.stderr.strip() else "")
        if proc.returncode not in (0, None) and not out.strip():
            raise EngineError(f"gnubg exited {proc.returncode} with no output")
        return out

    def evaluate(self, position: Position, *, plies: int = 2) -> Evaluation:
        raw = self.run_raw(self.build_commands(position, plies=plies))
        kind = "checker" if position.dice is not None else "cube"
        level = f"gnubg {plies}-ply"
        if kind == "checker":
            moves = parse_checker_hint(raw)
            if not moves:
                raise EngineError(_diagnose(raw, "no move list in gnubg output"))
            return Evaluation(position, "checker", self.name, level, moves=moves, raw=raw)
        cube = parse_cube_hint(raw)
        static = parse_eval_table(raw, prefer_ply=plies)
        if cube is not None:
            return Evaluation(position, "cube", self.name, level, cube=cube, static=static, raw=raw)
        if static is not None:
            # Dead cube (Crawford, 1-point match, opponent owns it): no cube
            # decision exists, but the position still has a value.
            return Evaluation(position, "static", self.name, level, static=static, raw=raw)
        raise EngineError(_diagnose(raw, "no cube analysis in gnubg output"))


# ----------------------------------------------------------------------
# Parsers (public so tests and other backends can reuse them)
# ----------------------------------------------------------------------


def parse_checker_hint(text: str) -> list[MoveEval]:
    """Parse gnubg's checker-play ``hint`` listing.

    Expected shape (gnubg 1.07)::

        1. Cubeful 2-ply    8/5 6/5                      Eq.: +0.218
           0.551 0.174 0.013 - 0.449 0.124 0.005
            2-ply cubeful prune [world class]
        2. Cubeful 2-ply    24/23 13/10                  Eq.: -0.011 (-0.229)
           ...
    """
    moves: list[MoveEval] = []
    lines = text.splitlines()
    i = 0
    while i < len(lines):
        m = _MOVE_RE.match(lines[i])
        if m:
            probs = None
            if i + 1 < len(lines):
                pm = _PROBS_RE.match(lines[i + 1])
                if pm:
                    probs = Probs(*(float(x) for x in pm.groups()))
            eq = float(m.group("eq"))
            err = float(m.group("err")) if m.group("err") is not None else 0.0
            moves.append(
                MoveEval(
                    rank=int(m.group("rank")),
                    move=m.group("move").strip(),
                    equity=eq,
                    error=err,
                    probs=probs,
                    ply=m.group("ply"),
                )
            )
        i += 1
    return moves


def parse_cube_hint(text: str) -> CubeEval | None:
    """Parse gnubg's cube ``hint`` block.

    Expected shape (gnubg 1.07)::

        Cube analysis
        2-ply cubeless equity -2.238 (Money: -2.039)
          0.086 0.000 0.000 - 0.914 0.771 0.440
        Cubeful equities:
        1. No double           -2.058
        2. Double, pass        +1.000  (+3.058)
        3. Double, take        -2.430  (-0.372)
        Proper cube action: No double, take (10.9%)
    """
    if "Cube analysis" not in text:
        return None
    block = text[text.index("Cube analysis"):]
    probs = None
    cubeless = None
    ply = "?"
    eqs: dict[str, float] = {}
    proper = None
    for line in block.splitlines():
        if (m := _CUBELESS_RE.match(line)):
            ply = m.group("ply")
            cubeless = float(m.group("eq"))
            continue
        if probs is None and (m := _PROBS_RE.match(line)):
            probs = Probs(*(float(x) for x in m.groups()))
            continue
        if (m := _CUBE_EQ_RE.match(line)):
            label = m.group("label").lower()
            key = "no_double" if label.startswith("no") else ("double_take" if "take" in label else "double_pass")
            eqs[key] = float(m.group("eq"))
            continue
        if (m := _PROPER_RE.match(line)):
            proper = m.group("action").strip()
    if not {"no_double", "double_take", "double_pass"} <= eqs.keys() or proper is None:
        return None
    return CubeEval(
        no_double=eqs["no_double"],
        double_take=eqs["double_take"],
        double_pass=eqs["double_pass"],
        proper_action=proper,
        probs=probs,
        cubeless_equity=cubeless,
        ply=ply,
    )


def parse_eval_table(text: str, *, prefer_ply: int = 2) -> StaticEval | None:
    """Parse gnubg's ``eval`` table and return the deepest row up to ``prefer_ply``.

    Expected shape (gnubg 1.07)::

        Evaluator:  Contact
                Win     W(g)    W(bg)   L(g)    L(bg)   Equity    Cubeful
        static: 0.521   0.154   0.008   0.130   0.008   +0.043    +0.043
         1 ply: 0.527   0.147   0.008   0.129   0.005   +0.053    +0.053
         2 ply: 0.525   0.149   0.007   0.124   0.005   +0.050    +0.050
    """
    rows: dict[int, StaticEval] = {}
    for line in text.splitlines():
        m = _EVAL_ROW_RE.match(line)
        if not m:
            continue
        ply_label = m.group("ply")
        ply_num = 0 if ply_label == "static" else int(ply_label.split()[0])
        win = float(m.group("win"))
        probs = Probs(
            win=win,
            win_g=float(m.group("wg")),
            win_bg=float(m.group("wbg")),
            lose=round(1.0 - win, 3),
            lose_g=float(m.group("lg")),
            lose_bg=float(m.group("lbg")),
        )
        rows[ply_num] = StaticEval(
            probs=probs,
            cubeless_equity=float(m.group("eq")),
            cubeful_equity=float(m.group("cubeful")),
            ply=f"{ply_num}-ply",
        )
    if not rows:
        return None
    best = max(p for p in rows if p <= prefer_ply) if any(p <= prefer_ply for p in rows) else max(rows)
    return rows[best]


def cube_is_dead_message(text: str) -> bool:
    return bool(_CANNOT_DOUBLE_RE.search(text))


def _diagnose(raw: str, default: str) -> str:
    tail = "\n".join(raw.strip().splitlines()[-15:])
    for needle in ("Illegal", "illegal", "Unknown", "unknown", "Error", "error", "not"):
        if needle in tail:
            return f"{default}. gnubg said:\n{tail}"
    return f"{default}. Last lines of gnubg output:\n{tail}"
