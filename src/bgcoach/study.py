"""A study: one position, its candidates at 2-ply, and the rollout that
settles them, written to ``studies/<date>-<slug>/`` as JSON (the source of
truth) and markdown (rendered from it).

This is the first end-to-end milestone from DESIGN.md: the oracle's
verdict on the original position, established before any explaining
starts. Hypotheses, variants and the written account are added to the
same JSON by later steps of the loop; the schema leaves room for them.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from bgcoach import __version__
from bgcoach.engines.base import Engine, Evaluation
from bgcoach.position import Position

SCHEMA_VERSION = 1

# Error-size words (money play, cubeful equity). Thresholds follow gnubg's
# own skill levels (doubtful 0.04, bad 0.08) and the research note:
# differences under 0.02 are inside what rollouts can order reliably at
# default trial counts.
SIZE_WORDS: tuple[tuple[float, str], ...] = (
    (0.02, "level"),
    (0.04, "small error"),
    (0.08, "error"),
    (0.16, "blunder"),
    (float("inf"), "huge blunder"),
)


def size_word(error: float) -> str:
    """Describe an equity loss in words. ``error`` may be signed; its size counts."""
    e = abs(error)
    for limit, word in SIZE_WORDS:
        if e < limit:
            return word
    return SIZE_WORDS[-1][1]


def slugify(text: str) -> str:
    s = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    return s or "study"


@dataclass
class Study:
    position: Position
    play: str | None = None
    reasoning: str | None = None
    candidates: Evaluation | None = None  # shallow evaluation of the decision
    rollout: Evaluation | None = None  # the oracle's verdict
    hypotheses: list[dict[str, Any]] = field(default_factory=list)
    variants: list[dict[str, Any]] = field(default_factory=list)
    account: str | None = None
    created: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    @property
    def decision(self) -> str:
        if self.position.dice is not None:
            return "checker"
        if self.position.cube_action is not None:
            return "take"
        if self.candidates is not None and self.candidates.kind == "static":
            return "position"  # no decision for the player on roll; its value is the subject
        return "cube"

    # ------------------------------------------------------------------

    def verdict(self) -> dict[str, Any]:
        """What the rollout says, in the shape the account is written from."""
        ro = self.rollout
        if ro is None:
            return {"status": "not rolled out"}
        if ro.kind == "checker":
            best = ro.best_move
            assert best is not None
            v: dict[str, Any] = {
                "best_play": best.move,
                "best_equity": best.equity,
                "best_se": best.se,
                "plays": [
                    {
                        "move": m.move,
                        "equity": m.equity,
                        "error": m.error,
                        "se": m.se,
                        "trials": m.trials,
                        "size": size_word(m.error),
                    }
                    for m in ro.moves
                ],
            }
            if self.play is not None:
                mine = _find_move(ro, self.play)
                if mine is not None:
                    v["your_play"] = {
                        "move": mine.move,
                        "equity": mine.equity,
                        "error": mine.error,
                        "size": size_word(mine.error),
                        "is_best": mine.rank == 1,
                    }
            return v
        if ro.kind == "cube":
            c = ro.cube
            assert c is not None
            v = {
                "action": c.best_cube_action,
                "take_decision": c.take_decision,
                "no_double": c.no_double,
                "double_take": c.double_take,
                "double_pass": c.double_pass,
                "se_no_double": c.se_no_double,
                "se_double_take": c.se_double_take,
                "trials": c.trials,
                "double_margin": round(min(c.double_take, c.double_pass) - c.no_double, 3),
                "take_margin": round(c.double_pass - c.double_take, 3),
            }
            if self.play is not None:
                v["your_action"] = self.play
            return v
        if ro.kind == "static":
            s = ro.static
            assert s is not None
            return {
                "note": "no cube decision for the player on roll; this is the position's value",
                "cubeful_equity": s.cubeful_equity,
                "cubeless_equity": s.cubeless_equity,
                "se": s.se,
                "trials": s.trials,
                "win": s.probs.win,
            }
        return {"status": f"unsupported rollout kind {ro.kind}"}

    def to_dict(self) -> dict[str, Any]:
        pos = self.position
        return {
            "schema": SCHEMA_VERSION,
            "bgcoach": __version__,
            "created": self.created.isoformat(timespec="seconds"),
            "position": {
                "xgid": pos.xgid(),
                "decision": self.decision,
                "on_roll": pos.turn,
                "pips": {"bottom": pos.pip_count(1), "top": pos.pip_count(-1)},
                "money_game": pos.is_money_game,
                "ascii": pos.ascii(),
            },
            "your_play": self.play,
            "your_reasoning": self.reasoning,
            "candidates": self.candidates.to_dict() if self.candidates else None,
            "rollout": self.rollout.to_dict() if self.rollout else None,
            "verdict": self.verdict(),
            "hypotheses": self.hypotheses,
            "variants": self.variants,
            "account": self.account,
        }

    # ------------------------------------------------------------------

    def markdown(self) -> str:
        """Render ``study.md`` from the same data as the JSON."""
        pos = self.position
        v = self.verdict()
        out: list[str] = []
        out.append(f"# Study: {pos.xgid()}")
        out.append("")
        out.append("```")
        out.append(pos.ascii())
        out.append("```")
        out.append("")
        if self.play:
            out.append(f"**Your play:** {self.play}")
            out.append("")
        if self.reasoning:
            out.append(f"**Your reasoning:** {self.reasoning}")
            out.append("")
        if self.account:
            out.append(self.account.rstrip())
            out.append("")
        else:
            out.append("_Account not written yet._")
            out.append("")
        out.append("<details>")
        out.append("<summary>How this was checked</summary>")
        out.append("")
        ro = self.rollout
        if ro is not None and ro.rollout is not None:
            info = ro.rollout
            trunc = (
                "no truncation"
                if info.truncation is None
                else f"truncated at {info.truncation} plies"
            )
            out.append(
                f"Rollout: {ro.engine} {info.engine_version or ''}, {info.trials} trials"
                f"{' (JSD early stop)' if info.jsd_stop else ''}, "
                f"{'cubeful' if info.cubeful else 'cubeless'}, "
                f"{'variance reduction' if info.variance_reduction else 'no variance reduction'}, "
                f"{trunc}, seed {info.seed}."
            )
            out.append("")
        if ro is not None and ro.kind == "checker":
            out.append("| Play | Equity | SE | Error | Games |")
            out.append("|---|---|---|---|---|")
            for p in v["plays"]:
                se = f"{p['se']:.3f}" if p["se"] is not None else ""
                out.append(
                    f"| {p['move']} | {p['equity']:+.3f} | {se} | {p['error']:+.3f} ({p['size']}) | {p['trials'] or ''} |"
                )
        elif ro is not None and ro.kind == "cube":

            def fmt_se(x: float | None) -> str:
                return f" (SE {x:.3f})" if x is not None else ""

            out.append(f"- No double: {v['no_double']:+.3f}{fmt_se(v['se_no_double'])}")
            out.append(f"- Double/take: {v['double_take']:+.3f}{fmt_se(v['se_double_take'])}")
            out.append(f"- Double/pass: {v['double_pass']:+.3f}")
            out.append(f"- Verdict: {v['action']}; taker should {v['take_decision']}.")
        elif ro is not None and ro.kind == "static":
            se = f" (SE {v['se']:.3f})" if v["se"] is not None else ""
            out.append(
                f"- Position value: {v['cubeful_equity']:+.3f} cubeful{se}, "
                f"{v['cubeless_equity']:+.3f} cubeless; wins {v['win']:.0%}."
            )
            out.append("- No cube decision for the player on roll.")
        if self.candidates is not None and self.candidates.kind == "checker":
            out.append("")
            out.append(f"Candidates at {self.candidates.level}:")
            out.append("")
            for m in self.candidates.moves:
                out.append(f"- {m.move}: {m.equity:+.3f} ({m.error:+.3f}) {m.ply}")
        if self.variants:
            out.append("")
            out.append(f"{len(self.variants)} variant(s) recorded in study.json.")
        out.append("")
        out.append("</details>")
        out.append("")
        return "\n".join(out)

    # ------------------------------------------------------------------

    folder: Path | None = None  # set by save(); later saves rewrite the same folder

    def save(self, root: Path | str = "studies", *, slug: str | None = None) -> Path:
        """Write ``study.json`` and ``study.md`` under ``root/<date>-<slug>/``.

        The first save picks a folder that does not exist yet (adding
        ``-2``, ``-3``, ... if needed); later saves of the same study
        rewrite that folder.
        """
        if self.folder is None:
            root = Path(root)
            base = f"{self.created.date().isoformat()}-{slugify(slug or self._default_slug())}"
            folder = root / base
            n = 2
            while folder.exists():
                folder = root / f"{base}-{n}"
                n += 1
            self.folder = folder
        self.folder.mkdir(parents=True, exist_ok=True)
        (self.folder / "study.json").write_text(json.dumps(self.to_dict(), indent=2) + "\n")
        (self.folder / "study.md").write_text(self.markdown())
        return self.folder

    def _default_slug(self) -> str:
        pos = self.position
        kind = self.decision
        dice = f"{pos.dice[0]}{pos.dice[1]}" if pos.dice else ""
        return f"{kind}-{dice}-{pos.xgid(prefix=False)[:8]}"


def _find_move(ev: Evaluation, text: str):
    from bgcoach.engines.gnubg import canonical_move

    key = canonical_move(text)
    for m in ev.moves:
        if canonical_move(m.move) == key:
            return m
    return None


def run_study(
    engine: Engine,
    position: Position,
    *,
    play: str | None = None,
    reasoning: str | None = None,
    plies: int = 2,
    top: int = 2,
    settings: object | None = None,
) -> Study:
    """Evaluate the decision at ``plies`` and roll out what matters.

    Checker play: the top ``top`` candidates by the shallow evaluation,
    plus your play if you gave one and it is not already among them.
    Cube: the cube decision itself. The study is returned unsaved.
    """
    study = Study(position=position, play=play, reasoning=reasoning)
    study.candidates = engine.evaluate(position, plies=plies)
    if study.candidates.kind == "checker":
        chosen = [m.move for m in study.candidates.moves[:top]]
        if play is not None:
            mine = _find_move(study.candidates, play)
            if mine is None:
                listed = ", ".join(m.move for m in study.candidates.moves)
                raise ValueError(
                    f"your play {play!r} is not a legal play here. Legal plays: {listed}"
                )
            if all(_find_move(study.candidates, c) is not mine for c in chosen):
                chosen.append(mine.move)
        study.rollout = engine.rollout(position, moves=chosen, settings=settings)
    else:
        # Cube decision, or the position's value when there is no decision.
        study.rollout = engine.rollout(position, settings=settings)
    return study
