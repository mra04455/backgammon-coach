"""A study: one position, its candidates at 2-ply, and the rollout that
settles them, written to ``studies/<date>-<slug>/`` as JSON (the source of
truth) and markdown (rendered from the JSON).

This is the first end-to-end milestone from DESIGN.md: the oracle's
verdict on the original position, established before any explaining
starts. Hypotheses, variants and the written account are added to the
same JSON by the analyst (``bgcoach write``); the markdown is re-rendered
from it.
"""

from __future__ import annotations

import json
import math
import re
from dataclasses import dataclass, field, replace
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

# A decision is "close" when the margin that decides it is inside the
# larger of 0.02 equity (the research note's error line) and two joint
# standard errors. DESIGN.md: extend such rollouts to 5184 trials.
CLOSE_EQUITY = 0.02
CLOSE_JOINT_SE = 2.0
EXTENDED_TRIALS = 5184


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


def _joint_se(*ses: float | None) -> float | None:
    known = [s for s in ses if s is not None]
    if not known:
        return None
    return math.sqrt(sum(s * s for s in known))


def is_close(ev: Evaluation) -> bool:
    """Is the margin that decides this rollout inside its noise band?

    Checker play: best against second best. Cube: the smaller of the
    double margin (no double vs double/take) and the take margin
    (double/take vs double/pass). Position values have no decision.
    """
    if ev.kind == "checker":
        if len(ev.moves) < 2:
            return False
        a, b = ev.moves[0], ev.moves[1]
        return _inside_band(a.equity - b.equity, _joint_se(a.se, b.se))
    if ev.kind == "cube" and ev.cube is not None:
        c = ev.cube
        double_margin = min(c.double_take, c.double_pass) - c.no_double
        take_margin = c.double_pass - c.double_take
        return _inside_band(double_margin, _joint_se(c.se_no_double, c.se_double_take)) or (
            _inside_band(take_margin, c.se_double_take)
        )
    return False


def _inside_band(margin: float, se: float | None) -> bool:
    band = CLOSE_EQUITY if se is None else max(CLOSE_EQUITY, CLOSE_JOINT_SE * se)
    return abs(margin) < band


@dataclass
class Study:
    position: Position
    play: str | None = None
    reasoning: str | None = None
    candidates: Evaluation | None = None  # shallow evaluation of the decision
    rollout: Evaluation | None = None  # the oracle's verdict
    superseded_rollouts: list[Evaluation] = field(default_factory=list)  # extended away
    hypotheses: list[dict[str, Any]] = field(default_factory=list)
    variants: list[dict[str, Any]] = field(default_factory=list)
    account: str | None = None
    created: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    folder: Path | None = None  # set by save(); later saves rewrite the same folder

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
                "close": is_close(ro),
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
                "close": is_close(ro),
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
            "superseded_rollouts": [r.to_dict() for r in self.superseded_rollouts],
            "verdict": self.verdict(),
            "hypotheses": self.hypotheses,
            "variants": self.variants,
            "account": self.account,
        }

    def markdown(self) -> str:
        return render_markdown(self.to_dict())

    # ------------------------------------------------------------------

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
        write_study_files(self.folder, self.to_dict())
        return self.folder

    def _default_slug(self) -> str:
        pos = self.position
        kind = self.decision
        dice = f"{pos.dice[0]}{pos.dice[1]}" if pos.dice else ""
        return f"{kind}-{dice}-{pos.xgid(prefix=False)[:8]}"


# ----------------------------------------------------------------------
# JSON-level helpers: the files are the seam, so these work on dicts
# ----------------------------------------------------------------------


def write_study_files(folder: Path, data: dict[str, Any]) -> None:
    folder.mkdir(parents=True, exist_ok=True)
    (folder / "study.json").write_text(json.dumps(data, indent=2) + "\n")
    (folder / "study.md").write_text(render_markdown(data))


def load_study(folder: Path | str) -> dict[str, Any]:
    folder = Path(folder)
    path = folder / "study.json" if folder.is_dir() else folder
    return json.loads(Path(path).read_text())


def update_study(
    folder: Path | str,
    *,
    hypotheses: list[dict[str, Any]] | None = None,
    variants: list[dict[str, Any]] | None = None,
    account: str | None = None,
) -> dict[str, Any]:
    """Record analyst output in an existing study and re-render its markdown.

    ``hypotheses`` and ``variants`` replace the stored lists when given;
    ``account`` replaces the account. Nothing else changes.
    """
    folder = Path(folder)
    data = load_study(folder)
    if hypotheses is not None:
        data["hypotheses"] = hypotheses
    if variants is not None:
        data["variants"] = variants
    if account is not None:
        data["account"] = account
    write_study_files(folder if folder.is_dir() else folder.parent, data)
    return data


def render_markdown(data: dict[str, Any]) -> str:
    """Render ``study.md`` from the study JSON.

    The account is the document; the engine record is the collapsed
    "how this was checked" section, as DESIGN.md specifies.
    """
    pos = data["position"]
    v = data.get("verdict") or {}
    ro = data.get("rollout")
    out: list[str] = []
    out.append(f"# Study: {pos['xgid']}")
    out.append("")
    out.append("```")
    out.append(pos["ascii"])
    out.append("```")
    out.append("")
    if data.get("your_play"):
        out.append(f"**Your play:** {data['your_play']}")
        out.append("")
    if data.get("your_reasoning"):
        out.append(f"**Your reasoning:** {data['your_reasoning']}")
        out.append("")
    if data.get("account"):
        out.append(str(data["account"]).rstrip())
    else:
        out.append("_Account not written yet._")
    out.append("")
    out.append("<details>")
    out.append("<summary>How this was checked</summary>")
    out.append("")
    if ro and ro.get("rollout"):
        info = ro["rollout"]
        trunc = (
            "no truncation"
            if info.get("truncation") is None
            else f"truncated at {info['truncation']} plies"
        )
        out.append(
            f"Rollout: {ro.get('engine', '')} {info.get('engine_version') or ''}, "
            f"{info['trials']} trials{' (JSD early stop)' if info.get('jsd_stop') else ''}, "
            f"{'cubeful' if info.get('cubeful') else 'cubeless'}, "
            f"{'variance reduction' if info.get('variance_reduction') else 'no variance reduction'}, "
            f"{trunc}, seed {info.get('seed')}."
        )
        out.append("")
    if ro and ro.get("kind") == "checker":
        out.append("| Play | Equity | SE | Error | Games |")
        out.append("|---|---|---|---|---|")
        for p in v.get("plays", []):
            se = f"{p['se']:.3f}" if p.get("se") is not None else ""
            out.append(
                f"| {p['move']} | {p['equity']:+.3f} | {se} | "
                f"{p['error']:+.3f} ({p['size']}) | {p.get('trials') or ''} |"
            )
        if v.get("close"):
            out.append("")
            out.append("The top two plays are inside the rollout's noise band.")
    elif ro and ro.get("kind") == "cube":

        def fmt_se(x: float | None) -> str:
            return f" (SE {x:.3f})" if x is not None else ""

        out.append(f"- No double: {v['no_double']:+.3f}{fmt_se(v.get('se_no_double'))}")
        out.append(f"- Double/take: {v['double_take']:+.3f}{fmt_se(v.get('se_double_take'))}")
        out.append(f"- Double/pass: {v['double_pass']:+.3f}")
        out.append(f"- Verdict: {v['action']}; taker should {v['take_decision']}.")
        if v.get("close"):
            out.append("- The deciding margin is inside the rollout's noise band.")
    elif ro and ro.get("kind") == "static":
        se = f" (SE {v['se']:.3f})" if v.get("se") is not None else ""
        out.append(
            f"- Position value: {v['cubeful_equity']:+.3f} cubeful{se}, "
            f"{v['cubeless_equity']:+.3f} cubeless; wins {v['win']:.0%}."
        )
        out.append("- No cube decision for the player on roll.")
    sup = data.get("superseded_rollouts") or []
    if sup:
        out.append("")
        out.append(
            f"{len(sup)} earlier rollout(s) were extended because the decision was close; "
            "they are kept in study.json."
        )
    cands = data.get("candidates")
    if cands and cands.get("kind") == "checker":
        out.append("")
        out.append(f"Candidates at {cands.get('level', '')}:")
        out.append("")
        for m in cands.get("moves", []):
            out.append(f"- {m['move']}: {m['equity']:+.3f} ({m['error']:+.3f}) {m['ply']}")
    hyps = data.get("hypotheses") or []
    variants = data.get("variants") or []
    if hyps or variants:
        out.append("")
        out.append(
            f"{len(hyps)} hypothesis(es) and {len(variants)} variant(s) recorded in study.json."
        )
    out.append("")
    out.append("</details>")
    out.append("")
    return "\n".join(out)


# ----------------------------------------------------------------------


def _find_move(ev: Evaluation, text: str):
    from bgcoach.engines.gnubg import canonical_move

    key = canonical_move(text)
    for m in ev.moves:
        if canonical_move(m.move) == key:
            return m
    return None


def _with_trials(settings: object | None, engine: Engine, trials: int) -> object | None:
    """``settings`` (or the engine's defaults) with a new trial count, if the
    settings object supports it (a dataclass with a ``trials`` field)."""
    base = settings if settings is not None else getattr(engine, "rollout_settings", None)
    if base is None or not hasattr(base, "trials"):
        return None
    try:
        return replace(base, trials=trials)  # type: ignore[type-var]
    except TypeError:
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
    extend_trials: int | None = EXTENDED_TRIALS,
) -> Study:
    """Evaluate the decision at ``plies`` and roll out what matters.

    Checker play: the top ``top`` candidates by the shallow evaluation,
    plus your play if you gave one and it is not already among them.
    Cube: the cube decision itself. If the rollout leaves the decision
    inside its noise band (:func:`is_close`) and ``extend_trials`` is set,
    it is rolled out again at that many trials and the first result kept
    under ``superseded_rollouts``. The study is returned unsaved.
    """
    study = Study(position=position, play=play, reasoning=reasoning)
    study.candidates = engine.evaluate(position, plies=plies)
    moves: list[str] | None = None
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
        moves = chosen
    study.rollout = engine.rollout(position, moves=moves, settings=settings)
    if extend_trials and is_close(study.rollout):
        current = study.rollout.rollout.trials if study.rollout.rollout else None
        bigger = _with_trials(settings, engine, extend_trials)
        if bigger is not None and (current is None or extend_trials > current):
            study.superseded_rollouts.append(study.rollout)
            study.rollout = engine.rollout(position, moves=moves, settings=bigger)
    return study
