"""GNU Backgammon backend.

Drives the ``gnubg`` command-line program with a command file and parses
the text output of ``hint`` (evaluations) and ``analyse rollout``
(rollouts). Validated against gnubg 1.07.001 (2024) and 1.08.003 (built by
``scripts/build-gnubg.sh``).

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

Rollouts (gnubg 1.08, checked in the source):

3. The bare ``rollout`` command takes no arguments, rolls out only the
   current position, and prints its result table only when stdout is a
   terminal. So checker plays are rolled out through the analysis path:
   play a move, step back, ``analyse move``, then ``analyse rollout move
   <ranks>``; cube decisions through ``double``, step back, ``analyse
   move``, ``analyse rollout cube``. Both print their results in command
   file mode. Ranks refer to the analysed move list, so a checker rollout
   is two passes: an evaluation to learn the ranks, then the rollout with
   analysis settings mirroring the evaluation settings. When the player
   on roll has no cube decision (the opponent owns the cube, or the cube
   is dead) there is nothing to ``double``, so the bare ``rollout`` is
   used after all, under a pseudo-terminal so that it prints.
4. gnubg ships with JSD early stopping switched *off*; :class:`RolloutSettings`
   switches it on by default (DESIGN.md: "early stop when settled"). With
   a single alternative nothing can be compared, so a one-move rollout
   runs to the full trial count.
5. ``set xgid`` refuses a position with a double pending ("D"). Such a
   position is rolled out as the doubler's decision instead; the taker's
   verdict is derived from double/take against double/pass.
"""

from __future__ import annotations

import os
import re
import select
import shutil
import subprocess
import tempfile
from dataclasses import dataclass, replace
from pathlib import Path

from bgcoach.engines.base import (
    CubeEval,
    EngineError,
    Evaluation,
    MoveEval,
    Probs,
    RolloutInfo,
    StaticEval,
)
from bgcoach.position import Position

# The binary built from source by scripts/build-gnubg.sh lands here.
REPO_LOCAL_BINARY = Path(__file__).resolve().parents[3] / ".gnubg" / "bin" / "gnubg"
DEFAULT_BINARY_CANDIDATES = (str(REPO_LOCAL_BINARY), "gnubg", "gnubg-cli", "/usr/games/gnubg")


def find_gnubg() -> str | None:
    """Locate the gnubg executable: $BGCOACH_GNUBG, the repo-local build,
    then common names on PATH."""
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

    def commands(self, scope: str) -> list[str]:
        """``set <scope> movefilter`` lines for plies 1..4.

        Positive accept counts at every even level; odd levels pass
        everything through (gnubg's own convention). ``scope`` is
        ``evaluation`` (for ``hint``/``eval``) or ``analysis`` (for
        ``analyse``); the two must match for rollout ranks to line up.
        """
        lines: list[str] = []
        for ply in range(1, 5):
            for level in range(ply):
                if level % 2 == 0:
                    lines.append(
                        f"set {scope} movefilter {ply} {level} "
                        f"{self.accept} {self.extra} {self.threshold}"
                    )
                else:
                    lines.append(f"set {scope} movefilter {ply} {level} -1 0 0")
        return lines


@dataclass(frozen=True)
class RolloutSettings:
    """gnubg rollout parameters.

    Defaults are gnubg's own (1296 trials, cubeful, variance reduction,
    0-ply chequer play, 2-ply cube decisions, no truncation) except JSD
    early stopping, which gnubg ships switched off and we switch on.
    ``truncation`` is a ply count; None rolls every game to the end.
    """

    trials: int = 1296
    cubeful: bool = True
    variance_reduction: bool = True
    truncation: int | None = None
    jsd_stop: bool = True
    jsd_limit: float = 2.33
    jsd_min_games: int = 324
    seed: int | None = None
    chequer_plies: int = 0
    cube_plies: int = 2

    def __post_init__(self) -> None:
        if self.trials < 1:
            raise ValueError("trials must be >= 1")
        if self.truncation is not None and self.truncation < 1:
            raise ValueError("truncation must be >= 1 ply or None")
        if not 0 <= self.chequer_plies <= 4 or not 0 <= self.cube_plies <= 4:
            raise ValueError("plies must be 0..4")

    def commands(self) -> list[str]:
        def on(b: bool) -> str:
            return "on" if b else "off"

        lines = [
            f"set rollout trials {self.trials}",
            f"set rollout cubeful {on(self.cubeful)}",
            f"set rollout varredn {on(self.variance_reduction)}",
            f"set rollout chequerplay plies {self.chequer_plies}",
            f"set rollout cubedecision plies {self.cube_plies}",
            "set rollout limit enable off",
            f"set rollout jsd stop {on(self.jsd_stop)}",
        ]
        if self.jsd_stop:
            lines.append(f"set rollout jsd limit {self.jsd_limit}")
            lines.append(f"set rollout jsd minimumgames {min(self.jsd_min_games, self.trials)}")
        if self.truncation is None:
            lines.append("set rollout truncation enable off")
        else:
            lines.append("set rollout truncation enable on")
            lines.append(f"set rollout truncation plies {self.truncation}")
        if self.seed is not None:
            lines.append(f"set rollout seed {self.seed}")
        return lines

    def info(self, engine_version: str | None) -> RolloutInfo:
        return RolloutInfo(
            trials=self.trials,
            seed=self.seed,
            cubeful=self.cubeful,
            variance_reduction=self.variance_reduction,
            truncation=self.truncation,
            jsd_stop=self.jsd_stop,
            jsd_limit=self.jsd_limit if self.jsd_stop else None,
            chequer_plies=self.chequer_plies,
            cube_plies=self.cube_plies,
            engine_version=engine_version,
        )


# "    1. Cubeful 2-ply    8/5 6/5    Eq.: +0.218 (-0.229)"  (hint)
# "*    1. Rollout          8/5 6/5    Eq.: +0.246"          (analyse rollout)
_MOVE_RE = re.compile(
    r"^\s*\*?\s*(?P<rank>\d+)\.\s+"
    r"(?:(?P<cubeful>Cubeful|Cubeless)\s+(?P<ply>\S+)|(?P<rollout>Rollout))\s+"
    r"(?P<move>.+?)\s+(?:Eq\.|MWC):\s*(?P<eq>[+-]?\d+\.\d+)%?"
    r"(?:\s*\(\s*(?P<err>[+-]?\d+\.\d+)%?\s*\))?\s*$"
)
# Probability line; rollouts append "CL <cubeless> CF <cubeful>".
_PROBS_RE = re.compile(
    r"^\s*(\d\.\d+)\s+(\d\.\d+)\s+(\d\.\d+)\s+-\s+(\d\.\d+)\s+(\d\.\d+)\s+(\d\.\d+)"
    r"(?:\s+CL\s+(?P<cl>[+-]?\d+\.\d+)(?:\s+CF\s+(?P<cf>[+-]?\d+\.\d+))?)?\s*$"
)
# Standard-error line under a rollout result: "[0.002 ... - ... CL 0.004 CF 0.011]".
_SD_RE = re.compile(
    r"^\s*\[\s*(\d\.\d+)\s+(\d\.\d+)\s+(\d\.\d+)\s+-\s+(\d\.\d+)\s+(\d\.\d+)\s+(\d\.\d+)"
    r"\s+CL\s+(?P<cl>\d+\.\d+)(?:\s+CF\s+(?P<cf>\d+\.\d+))?\s*\]"
)
_GAMES_RE = re.compile(r"^\s*(?P<n>\d+) games,.*?seed (?P<seed>\d+)")
_STATIC_HEADER = "Current Position:"
_VERSION_RE = re.compile(r"^GNU Backgammon (?P<version>\S+)", re.MULTILINE)
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
    # Class-level defaults so instances built without __init__ (tests) still work.
    threads: int | None = None
    rollout_settings: RolloutSettings = RolloutSettings()
    rollout_timeout: float = 4 * 3600.0
    analysis_plies: int = 2

    def __init__(
        self,
        binary: str | None = None,
        *,
        move_filter: MoveFilter | None = None,
        timeout: float = 600.0,
        threads: int | None = None,
        rollout_settings: RolloutSettings | None = None,
        rollout_timeout: float = 4 * 3600.0,
    ) -> None:
        self.binary = binary or find_gnubg()
        if self.binary is None:
            raise EngineError(
                "gnubg not found. Run scripts/build-gnubg.sh, install GNU Backgammon "
                "(brew install gnubg / apt install gnubg / the Windows installer, which "
                "provides gnubg-cli.exe), or set BGCOACH_GNUBG to the executable path."
            )
        self.move_filter = move_filter if move_filter is not None else MoveFilter()
        self.timeout = timeout
        # gnubg starts with one calculation thread; rollouts scale with cores.
        self.threads = threads if threads is not None else (os.cpu_count() or 1)
        self.rollout_settings = (
            rollout_settings if rollout_settings is not None else RolloutSettings()
        )
        self.rollout_timeout = rollout_timeout

    # ------------------------------------------------------------------

    def _prefix(self) -> list[str]:
        lines = [
            "set lang C",
            "set output mwc off",
            "set output rawboard off",
        ]
        if self.threads and self.threads > 1:
            lines.append(f"set threads {self.threads}")
        lines += ["set player 0 human", "set player 1 human"]
        return lines

    def _eval_settings(self, scope: str, plies: int) -> list[str]:
        """``set evaluation ...`` or ``set analysis ...`` lines for ``plies``."""
        if not 0 <= plies <= 4:
            raise ValueError("plies must be 0..4")
        return [
            f"set {scope} chequerplay evaluation plies {plies}",
            f"set {scope} chequerplay evaluation cubeful on",
            f"set {scope} cubedecision evaluation plies {plies}",
            f"set {scope} cubedecision evaluation cubeful on",
            *self.move_filter.commands(scope),
        ]

    def build_commands(self, position: Position, *, plies: int) -> str:
        lines = [
            *self._prefix(),
            *self._eval_settings("evaluation", plies),
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

    def build_rollout_commands(
        self,
        position: Position,
        *,
        settings: RolloutSettings,
        play: str | None,
        ranks: list[int] | None,
        static: bool = False,
    ) -> str:
        """Command file for a rollout.

        Checker play (``play`` and ``ranks`` given): play ``play`` so a move
        record exists, step back, analyse it at ``analysis_plies`` with the
        same move filter as :meth:`build_commands`, then roll out the moves
        at ``ranks`` in that analysed list. Cube (both None): offer the
        double, step back, analyse, roll out the cube decision. Position
        value (``static``): the bare ``rollout``; run it with a tty.
        """
        lines = [
            *self._prefix(),
            *self._eval_settings("analysis", self.analysis_plies),
            *settings.commands(),
            "new match 0",
            f"set xgid {position.xgid()}",
        ]
        if static:
            if play is not None or ranks:
                raise ValueError("a static rollout takes no play or ranks")
            lines.append("rollout")
        elif play is not None:
            if not ranks:
                raise ValueError("ranks must be given with play")
            lines += [
                f"move {move_for_command(play)}",
                "previous",
                "analyse move",
                "analyse rollout move " + " ".join(str(r) for r in sorted(ranks)),
            ]
        else:
            lines += ["double", "previous", "analyse move", "analyse rollout cube"]
        return "\n".join(lines) + "\n"

    def run_raw(self, commands: str, *, timeout: float | None = None, tty: bool = False) -> str:
        """Run gnubg on ``commands`` and return everything it printed.

        ``tty`` runs it under a pseudo-terminal. gnubg prints rollout
        progress and the bare ``rollout`` command's results only when
        stdout is a terminal; nothing else in this module needs it.
        """
        timeout = self.timeout if timeout is None else timeout
        with tempfile.TemporaryDirectory(prefix="bgcoach-gnubg-") as tmp:
            cmd_path = Path(tmp) / "commands.txt"
            cmd_path.write_text(commands)
            argv = [self.binary, "-t", "-q", "-c", str(cmd_path)]
            try:
                if tty:
                    return _run_under_pty(argv, timeout)
                proc = subprocess.run(
                    argv,
                    capture_output=True,
                    text=True,
                    timeout=timeout,
                    check=False,
                )
            except FileNotFoundError as e:
                raise EngineError(f"could not run {self.binary}: {e}") from e
            except subprocess.TimeoutExpired as e:
                raise EngineError(f"gnubg timed out after {timeout}s") from e
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

    # ------------------------------------------------------------------
    # Rollouts
    # ------------------------------------------------------------------

    def rollout(
        self,
        position: Position,
        *,
        moves: list[str] | None = None,
        top: int = 2,
        settings: RolloutSettings | None = None,
    ) -> Evaluation:
        """Roll out a checker play or cube decision; see :class:`Engine`.

        ``moves`` are matched to gnubg's notation loosely (order of the
        parts and ``(2)`` shorthand do not matter). A position with a
        double pending is rolled out as the doubler's decision (quirk 5).
        """
        rs = settings or self.rollout_settings
        if position.cube_action is not None:
            position = position.with_(cube_action=None)
        if position.dice is not None:
            return self._rollout_checker(position, moves, top, rs)
        if moves:
            raise ValueError("moves only apply to checker-play positions (with dice)")
        # Does the player on roll have a cube decision at all? gnubg knows
        # (opponent's cube, Crawford, dead cube in a short match); ask it.
        if self.evaluate(position, plies=0).kind == "static":
            return self._rollout_static(position, rs)
        return self._rollout_cube(position, rs)

    def _rollout_checker(
        self,
        position: Position,
        moves: list[str] | None,
        top: int,
        rs: RolloutSettings,
    ) -> Evaluation:
        ranked = self.evaluate(position, plies=self.analysis_plies).moves
        if moves is None:
            if top < 1:
                raise ValueError("top must be >= 1")
            wanted = ranked[:top]
        else:
            by_key = {canonical_move(m.move): m for m in ranked}
            wanted = []
            for text in moves:
                m = by_key.get(canonical_move(text))
                if m is None:
                    listed = ", ".join(x.move for x in ranked)
                    raise EngineError(
                        f"move {text!r} is not in gnubg's move list for this position. "
                        f"Available: {listed}"
                    )
                if m not in wanted:
                    wanted.append(m)
        ranks = [m.rank for m in wanted]
        commands = self.build_rollout_commands(
            position, settings=rs, play=ranked[0].move, ranks=ranks
        )
        raw = self.run_raw(commands, timeout=self.rollout_timeout)
        rolled = [m for m in parse_checker_hint(raw) if m.ply == "rollout"]
        if len(rolled) != len(ranks):
            raise EngineError(
                _diagnose(raw, f"expected {len(ranks)} rolled-out moves, found {len(rolled)}")
            )
        got = {canonical_move(m.move) for m in rolled}
        want = {canonical_move(m.move) for m in wanted}
        if got != want:
            raise EngineError(
                "gnubg's analysis ranked the moves differently from its evaluation; "
                f"wanted {[m.move for m in wanted]}, rolled out {[m.move for m in rolled]}"
            )
        rolled.sort(key=lambda m: -m.equity)
        best = rolled[0].equity
        rolled = [
            replace(m, rank=i + 1, error=round(m.equity - best, 3)) for i, m in enumerate(rolled)
        ]
        return Evaluation(
            position,
            "checker",
            self.name,
            f"gnubg rollout {rs.trials}",
            moves=rolled,
            raw=raw,
            rollout=rs.info(parse_version(raw)),
        )

    def _rollout_cube(self, position: Position, rs: RolloutSettings) -> Evaluation:
        commands = self.build_rollout_commands(position, settings=rs, play=None, ranks=None)
        raw = self.run_raw(commands, timeout=self.rollout_timeout)
        cube = parse_cube_rollout(raw)
        if cube is None:
            raise EngineError(
                _diagnose(
                    raw,
                    "no cube rollout in gnubg output (the player on roll may have no cube "
                    "decision here; dead-cube position rollouts are not supported yet)",
                )
            )
        return Evaluation(
            position,
            "cube",
            self.name,
            f"gnubg rollout {rs.trials}",
            cube=cube,
            raw=raw,
            rollout=rs.info(parse_version(raw)),
        )

    def _rollout_static(self, position: Position, rs: RolloutSettings) -> Evaluation:
        """Roll out the value of a position with no cube decision to make."""
        commands = self.build_rollout_commands(
            position, settings=rs, play=None, ranks=None, static=True
        )
        raw = self.run_raw(commands, timeout=self.rollout_timeout, tty=True)
        static = parse_static_rollout(raw)
        if static is None:
            raise EngineError(_diagnose(raw, "no position rollout in gnubg output"))
        return Evaluation(
            position,
            "static",
            self.name,
            f"gnubg rollout {rs.trials}",
            static=static,
            raw=raw,
            rollout=rs.info(parse_version(raw)),
        )


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

    Rolled-out entries (from ``analyse rollout move``) look like::

        *    1. Rollout          8/5 6/5                      Eq.: +0.246
               0.553 0.169 0.007 - 0.447 0.113 0.005 CL +0.163 CF +0.246
              [0.002 0.001 0.000 - 0.002 0.001 0.000 CL  0.004 CF  0.011]
                Full cubeful rollout with variance reduction
                1296 games, Mersenne Twister dice gen. with seed 12345 and quasi-random dice

    and come back with ``ply="rollout"``, ``se`` (standard error of the
    cubeful equity, or of the cubeless one in a cubeless rollout),
    ``trials`` and ``cubeless_equity`` filled in.
    """
    moves: list[MoveEval] = []
    lines = text.splitlines()
    i = 0
    while i < len(lines):
        m = _MOVE_RE.match(lines[i])
        if m:
            probs = None
            cubeless = None
            se = None
            trials = None
            if i + 1 < len(lines):
                pm = _PROBS_RE.match(lines[i + 1])
                if pm:
                    probs = Probs(*(float(x) for x in pm.groups()[:6]))
                    if pm.group("cl") is not None:
                        cubeless = float(pm.group("cl"))
            is_rollout = m.group("rollout") is not None
            if is_rollout:
                for line in lines[i + 2 : i + 8]:
                    if se is None and (sm := _SD_RE.match(line)):
                        se = float(sm.group("cf") or sm.group("cl"))
                    elif trials is None and (gm := _GAMES_RE.match(line)):
                        trials = int(gm.group("n"))
                    if _MOVE_RE.match(line):
                        break
            eq = float(m.group("eq"))
            err = float(m.group("err")) if m.group("err") is not None else 0.0
            moves.append(
                MoveEval(
                    rank=int(m.group("rank")),
                    move=m.group("move").strip(),
                    equity=eq,
                    error=err,
                    probs=probs,
                    ply="rollout" if is_rollout else m.group("ply"),
                    se=se,
                    trials=trials,
                    cubeless_equity=cubeless,
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
    block = text[text.index("Cube analysis") :]
    probs = None
    cubeless = None
    ply = "?"
    eqs: dict[str, float] = {}
    proper = None
    for line in block.splitlines():
        if m := _CUBELESS_RE.match(line):
            ply = m.group("ply")
            cubeless = float(m.group("eq"))
            continue
        if probs is None and (m := _PROBS_RE.match(line)):
            probs = Probs(*(float(x) for x in m.groups()[:6]))
            continue
        if m := _CUBE_EQ_RE.match(line):
            label = m.group("label").lower()
            key = (
                "no_double"
                if label.startswith("no")
                else ("double_take" if "take" in label else "double_pass")
            )
            eqs[key] = float(m.group("eq"))
            continue
        if m := _PROPER_RE.match(line):
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


def parse_cube_rollout(text: str) -> CubeEval | None:
    """Parse the output of ``analyse rollout cube``.

    The cube block is the one :func:`parse_cube_hint` reads (with
    ``Rollout cubeless equity`` in place of a ply), followed by::

        Rollout details:
        Centered 1-cube:
          0.524 0.163 0.007 - 0.476 0.127 0.005 CL +0.085 CF +0.131
         [0.009 0.008 0.001 - 0.009 0.006 0.001 CL  0.023 CF  0.051]
        gnubg owns 2-cube:
          0.526 0.164 0.006 - 0.474 0.127 0.002 CL +0.186 CF -0.192
         [0.010 0.010 0.001 - 0.010 0.005 0.003 CL  0.052 CF  0.061]
        Full cubeful rollout with variance reduction
        36 games, Mersenne Twister dice gen. with seed 12345 and quasi-random dice

    The first bracketed line is the no-double rollout's standard errors,
    the second the double/take rollout's.
    """
    cube = parse_cube_hint(text)
    if cube is None or "Rollout details" not in text:
        return None
    details = text[text.index("Rollout details") :]
    ses: list[float] = []
    trials = None
    for line in details.splitlines():
        if m := _SD_RE.match(line):
            ses.append(float(m.group("cf") or m.group("cl")))
        elif trials is None and (m := _GAMES_RE.match(line)):
            trials = int(m.group("n"))
    return replace(
        cube,
        ply="rollout",
        se_no_double=ses[0] if len(ses) > 0 else None,
        se_double_take=ses[1] if len(ses) > 1 else None,
        trials=trials,
    )


def parse_static_rollout(text: str) -> StaticEval | None:
    """Parse the bare ``rollout`` command's final result (tty output).

    gnubg prints progress tables every tenth of the trials and the final
    one after ``Rollout done``::

        Rollout done. Printing final results.

        Current Position:
          0.520 0.142 0.008 - 0.480 0.120 0.005 CL +0.064 CF -0.094
         [0.013 0.011 0.003 - 0.013 0.007 0.001 CL  0.035 CF  0.074] 1r
        Full cubeful rollout with variance reduction
        36 games, Mersenne Twister dice gen. with seed 1 and quasi-random dice

    Only the last ``Current Position:`` block is read.
    """
    start = text.rfind(_STATIC_HEADER)
    if start < 0:
        return None
    lines = text[start:].replace("\r", "").splitlines()[1:12]
    probs = None
    cubeless = None
    cubeful = None
    se = None
    trials = None
    for line in lines:
        if probs is None and (m := _PROBS_RE.match(line)):
            probs = Probs(*(float(x) for x in m.groups()[:6]))
            if m.group("cl") is not None:
                cubeless = float(m.group("cl"))
            cubeful = float(m.group("cf")) if m.group("cf") is not None else cubeless
        elif se is None and (m := _SD_RE.match(line)):
            se = float(m.group("cf") or m.group("cl"))
        elif trials is None and (m := _GAMES_RE.match(line)):
            trials = int(m.group("n"))
    if probs is None or cubeless is None or cubeful is None:
        return None
    return StaticEval(
        probs=probs,
        cubeless_equity=cubeless,
        cubeful_equity=cubeful,
        ply="rollout",
        se=se,
        trials=trials,
    )


def _run_under_pty(argv: list[str], timeout: float) -> str:
    """Run ``argv`` with a pseudo-terminal as stdout/stderr and return its output.

    POSIX only (``pty`` is unavailable on Windows); carriage returns from
    gnubg's progress display are stripped.
    """
    import time

    try:
        import pty
    except ImportError as e:  # pragma: no cover - Windows
        raise EngineError(
            "position rollouts need a pseudo-terminal, which is unavailable on this platform"
        ) from e
    master, slave = pty.openpty()
    try:
        proc = subprocess.Popen(
            argv, stdout=slave, stderr=slave, stdin=subprocess.DEVNULL, close_fds=True
        )
    finally:
        os.close(slave)
    chunks: list[bytes] = []
    deadline = time.monotonic() + timeout
    try:
        while True:
            if time.monotonic() > deadline:
                proc.kill()
                raise subprocess.TimeoutExpired(argv, timeout)
            ready, _, _ = select.select([master], [], [], 1.0)
            if ready:
                try:
                    chunk = os.read(master, 65536)
                except OSError:  # slave closed: gnubg exited
                    break
                if not chunk:
                    break
                chunks.append(chunk)
            elif proc.poll() is not None:
                break
    finally:
        os.close(master)
        proc.wait()
    return b"".join(chunks).decode("utf-8", errors="replace").replace("\r", "")


def parse_version(text: str) -> str | None:
    """The gnubg version from the banner, e.g. ``"1.08.003"``."""
    m = _VERSION_RE.search(text)
    return m.group("version") if m else None


def canonical_move(move: str) -> tuple[str, ...]:
    """A comparison key for a move in gnubg notation.

    Ignores hit markers, the order of the parts and ``(n)`` repetition
    shorthand, so ``"6/5 8/5"`` and ``"8/5 6/5"`` and ``"8/5(2)"`` vs
    ``"8/5 8/5"`` compare equal. Case-insensitive (``bar``/``Bar``).
    """
    parts: list[str] = []
    for tok in move.replace("*", "").split():
        m = re.fullmatch(r"(.+?)\((\d+)\)", tok)
        if m:
            parts.extend([m.group(1)] * int(m.group(2)))
        else:
            parts.append(tok)
    return tuple(sorted(p.lower() for p in parts))


def move_for_command(move: str) -> str:
    """Turn gnubg's printed notation into something its ``move`` command
    accepts: drop hit markers and expand ``(n)`` shorthand."""
    parts: list[str] = []
    for tok in move.replace("*", "").split():
        m = re.fullmatch(r"(.+?)\((\d+)\)", tok)
        if m:
            parts.extend([m.group(1)] * int(m.group(2)))
        else:
            parts.append(tok)
    return " ".join(parts)


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
    best = (
        max(p for p in rows if p <= prefer_ply) if any(p <= prefer_ply for p in rows) else max(rows)
    )
    return rows[best]


def cube_is_dead_message(text: str) -> bool:
    return bool(_CANNOT_DOUBLE_RE.search(text))


def _diagnose(raw: str, default: str) -> str:
    tail = "\n".join(raw.strip().splitlines()[-15:])
    for needle in ("Illegal", "illegal", "Unknown", "unknown", "Error", "error", "not"):
        if needle in tail:
            return f"{default}. gnubg said:\n{tail}"
    return f"{default}. Last lines of gnubg output:\n{tail}"
