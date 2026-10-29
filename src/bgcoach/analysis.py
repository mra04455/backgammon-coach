"""Higher-level helpers the analyst loop uses: variants, sweeps, comparisons.

These are plain functions so they can be called from the MCP server, the
CLI, or tests. They never talk to an engine directly; one is passed in.
"""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from typing import Any

from bgcoach import perturb
from bgcoach.engines.base import Engine, EngineError, Evaluation
from bgcoach.position import Position


@dataclass
class Variant:
    label: str
    operations: list[dict[str, Any]]
    position: Position
    evaluation: Evaluation | None = None
    error: str | None = None

    def to_dict(self) -> dict:
        d: dict = {
            "label": self.label,
            "operations": self.operations,
            "xgid": self.position.xgid(),
        }
        if self.evaluation is not None:
            d["evaluation"] = self.evaluation.to_dict()
        if self.error is not None:
            d["error"] = self.error
        return d


@dataclass
class Sweep:
    """A base position plus a set of perturbed variants, all evaluated."""

    base: Variant
    variants: list[Variant] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "base": self.base.to_dict(),
            "variants": [v.to_dict() for v in self.variants],
            "summary": summarize(self),
        }


def make_variant(base: Position, label: str, operations: list[dict[str, Any]]) -> Variant:
    return Variant(label=label, operations=operations, position=perturb.apply(base, operations))


def evaluate_variant(engine: Engine, v: Variant, *, plies: int) -> Variant:
    try:
        v.evaluation = engine.evaluate(v.position, plies=plies)
    except EngineError as e:
        v.error = str(e)
    return v


def run_sweep(
    engine: Engine,
    base: Position,
    variants: list[tuple[str, list[dict[str, Any]]]],
    *,
    plies: int = 2,
    workers: int = 1,
) -> Sweep:
    """Evaluate ``base`` and every ``(label, operations)`` variant.

    ``workers > 1`` evaluates variants in parallel; gnubg is a separate
    process per call so this scales roughly with cores.
    """
    sweep = Sweep(base=Variant("base", [], base))
    sweep.variants = [make_variant(base, label, ops) for label, ops in variants]
    todo = [sweep.base, *sweep.variants]
    if workers <= 1:
        for v in todo:
            evaluate_variant(engine, v, plies=plies)
    else:
        with ThreadPoolExecutor(max_workers=workers) as ex:
            list(ex.map(lambda v: evaluate_variant(engine, v, plies=plies), todo))
    return sweep


def headline(ev: Evaluation) -> dict:
    """The one number an analyst compares across variants, plus what decided it."""
    if ev.kind == "checker":
        best = ev.best_move
        runner = ev.moves[1] if len(ev.moves) > 1 else None
        return {
            "kind": "checker",
            "best_move": best.move if best else None,
            "best_equity": best.equity if best else None,
            "margin_over_second": (-runner.error) if runner else None,
            "second_move": runner.move if runner else None,
        }
    if ev.kind == "static":
        s = ev.static
        assert s is not None
        return {
            "kind": "static",
            "note": "no cube decision available (cube dead or owned by opponent)",
            "cubeful_equity": s.cubeful_equity,
            "cubeless_equity": s.cubeless_equity,
            "win": s.probs.win,
        }
    c = ev.cube
    assert c is not None
    return {
        "kind": "cube",
        "action": c.best_cube_action,
        "take_decision": c.take_decision,
        "no_double": c.no_double,
        "double_take": c.double_take,
        "double_pass": c.double_pass,
        # >0 means take is right (the doubler would rather you passed).
        "take_margin": round(c.double_pass - c.double_take, 3),
        # >0 means doubling beats holding.
        "double_margin": round(min(c.double_take, c.double_pass) - c.no_double, 3),
    }


def summarize(sweep: Sweep) -> list[dict]:
    """Per-variant deltas against the base, in a shape that's easy to eyeball."""
    rows: list[dict] = []
    base_ev = sweep.base.evaluation
    base_h = headline(base_ev) if base_ev else None
    for v in sweep.variants:
        row: dict = {"label": v.label, "xgid": v.position.xgid()}
        if v.error or v.evaluation is None:
            row["error"] = v.error or "not evaluated"
            rows.append(row)
            continue
        h = headline(v.evaluation)
        row.update(h)
        if base_h and base_h["kind"] == h["kind"]:
            if h["kind"] == "checker":
                row["best_equity_delta"] = round(h["best_equity"] - base_h["best_equity"], 3)
                row["best_move_changed"] = h["best_move"] != base_h["best_move"]
            elif h["kind"] == "cube":
                row["take_margin_delta"] = round(h["take_margin"] - base_h["take_margin"], 3)
                row["double_margin_delta"] = round(h["double_margin"] - base_h["double_margin"], 3)
                row["action_changed"] = h["action"] != base_h["action"]
            else:
                row["cubeful_equity_delta"] = round(h["cubeful_equity"] - base_h["cubeful_equity"], 3)
        elif base_h and {base_h["kind"], h["kind"]} == {"cube", "static"}:
            # A variant killed or revived the cube; compare position values instead.
            base_val = base_ev.best_equity if base_ev else None
            if base_val is not None and v.evaluation.best_equity is not None:
                row["equity_delta"] = round(v.evaluation.best_equity - base_val, 3)
            row["kind_changed"] = f"{base_h['kind']} -> {h['kind']}"
        rows.append(row)
    return rows
