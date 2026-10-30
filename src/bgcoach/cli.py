"""Tiny CLI for poking at positions without an MCP client.

    bgcoach show    XGID
    bgcoach eval    XGID [--plies N]
    bgcoach sweep   XGID --var "label: op json" ...   (see README)
    bgcoach rollout XGID [--move M ...] [--top N] [--trials N] [--truncate P] [--seed S]
    bgcoach study   XGID [--play M] [--reasoning TEXT] [--trials N] [--out DIR]
    bgcoach write   STUDY_DIR [--account FILE] [--hypotheses JSON] [--variants JSON]
    bgcoach facts   XGID [--after PLAY ...]

``rollout``, ``study``, ``write`` and ``facts`` print JSON; ``study`` writes
``studies/<date>-<slug>/study.{json,md}`` and ``write`` records the
analyst's hypotheses, variants and account in it, re-rendering the markdown.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from bgcoach import analysis, facts, perturb
from bgcoach.engines import EngineError, get_engine
from bgcoach.position import XGIDError, parse_xgid
from bgcoach.study import EXTENDED_TRIALS, run_study, update_study


def _rollout_settings(args):
    """Build gnubg RolloutSettings from CLI flags (None = engine defaults)."""
    from bgcoach.engines.gnubg import RolloutSettings

    kwargs = {}
    if args.trials is not None:
        kwargs["trials"] = args.trials
    if args.truncate is not None:
        kwargs["truncation"] = args.truncate
    if args.seed is not None:
        kwargs["seed"] = args.seed
    if args.no_jsd_stop:
        kwargs["jsd_stop"] = False
    return RolloutSettings(**kwargs) if kwargs else None


def _add_rollout_flags(parser) -> None:
    parser.add_argument("--trials", type=int, default=None, help="games per rollout (default 1296)")
    parser.add_argument(
        "--truncate",
        type=int,
        default=None,
        metavar="PLIES",
        help="truncate each game after PLIES plies (default: play to the end)",
    )
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument(
        "--no-jsd-stop",
        action="store_true",
        help="disable early stopping when the candidates are settled",
    )
    parser.add_argument("--engine", default="gnubg")


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="bgcoach")
    sub = ap.add_subparsers(dest="cmd", required=True)

    s = sub.add_parser("show", help="print the board for an XGID")
    s.add_argument("xgid")

    e = sub.add_parser("eval", help="evaluate a position")
    e.add_argument("xgid")
    e.add_argument("--plies", type=int, default=2)
    e.add_argument("--engine", default="gnubg")
    e.add_argument("--json", action="store_true")

    w = sub.add_parser("sweep", help="evaluate a base and variants")
    w.add_argument("xgid")
    w.add_argument(
        "--var",
        action="append",
        default=[],
        metavar="LABEL=OPS_JSON",
        help='e.g. --var "no anchor=[{\\"op\\":\\"move\\",\\"player\\":1,\\"src\\":20,\\"dst\\":13}]"',
    )
    w.add_argument("--plies", type=int, default=2)
    w.add_argument("--engine", default="gnubg")
    w.add_argument("--workers", type=int, default=2)

    r = sub.add_parser("rollout", help="roll out a checker play or cube decision (JSON)")
    r.add_argument("xgid")
    r.add_argument(
        "--move",
        action="append",
        default=[],
        metavar="MOVE",
        help="candidate play in gnubg notation, repeatable; default: the top plays",
    )
    r.add_argument("--top", type=int, default=2, help="how many top plays to roll out (default 2)")
    _add_rollout_flags(r)

    st = sub.add_parser("study", help="evaluate, roll out, and save a study (JSON)")
    st.add_argument("xgid")
    st.add_argument("--play", default=None, help="the play or cube action you made")
    st.add_argument("--reasoning", default=None, help="what you were thinking, in plain text")
    st.add_argument("--plies", type=int, default=2)
    st.add_argument("--top", type=int, default=2)
    st.add_argument("--out", default="studies", help="studies root directory (default: studies)")
    st.add_argument("--slug", default=None, help="folder name suffix (default: derived)")
    st.add_argument(
        "--extend-trials",
        type=int,
        default=EXTENDED_TRIALS,
        metavar="N",
        help=f"re-roll a close decision at N trials (default {EXTENDED_TRIALS}; 0 disables)",
    )
    _add_rollout_flags(st)

    wr = sub.add_parser("write", help="record hypotheses, variants and the account in a study")
    wr.add_argument("study_dir", help="the studies/<date>-<slug> folder (or its study.json)")
    wr.add_argument(
        "--account",
        default=None,
        metavar="FILE",
        help="markdown file with the written account ('-' for stdin)",
    )
    wr.add_argument(
        "--hypotheses",
        default=None,
        metavar="JSON",
        help="JSON list of hypothesis objects, or @file",
    )
    wr.add_argument(
        "--variants", default=None, metavar="JSON", help="JSON list of variant objects, or @file"
    )

    fa = sub.add_parser(
        "facts", help="exact counts: points, blots, spares, primes, shots, entering (JSON)"
    )
    fa.add_argument("xgid")
    fa.add_argument(
        "--after",
        action="append",
        default=[],
        metavar="PLAY",
        help="also report the position after this play by the player on roll, with the "
        "opponent's shots and the mover's covering numbers; repeatable",
    )

    args = ap.parse_args(argv)

    if args.cmd == "write":
        return _write(args)

    try:
        pos = parse_xgid(args.xgid)
    except XGIDError as err:
        print(f"error: {err}", file=sys.stderr)
        return 2

    if args.cmd == "show":
        print(pos.ascii())
        return 0

    if args.cmd == "facts":
        out = {"position": facts.facts(pos)}
        if args.after:
            if pos.dice is None:
                print("error: --after needs a position with dice", file=sys.stderr)
                return 2
            try:
                out["plays"] = [facts.play_facts(pos, play) for play in args.after]
            except ValueError as err:
                print(f"error: {err}", file=sys.stderr)
                return 2
        print(json.dumps(out, indent=2))
        return 0

    try:
        engine = get_engine(args.engine)
    except EngineError as err:
        print(f"error: {err}", file=sys.stderr)
        return 1

    if args.cmd == "eval":
        try:
            ev = engine.evaluate(pos, plies=args.plies)
        except EngineError as err:
            print(f"error: {err}", file=sys.stderr)
            return 1
        if args.json:
            print(json.dumps(ev.to_dict(), indent=2))
            return 0
        print(pos.ascii())
        print()
        print(f"[{ev.level}]")
        if ev.kind == "checker":
            for m in ev.moves:
                p = (
                    f"  {m.probs.win:.3f} {m.probs.win_g:.3f} {m.probs.win_bg:.3f} - {m.probs.lose:.3f} {m.probs.lose_g:.3f} {m.probs.lose_bg:.3f}"
                    if m.probs
                    else ""
                )
                print(f"{m.rank:>3}. {m.move:<22} {m.equity:+.3f} ({m.error:+.3f}) {m.ply}{p}")
        elif ev.kind == "cube":
            c = ev.cube
            assert c is not None
            print(f"  No double    {c.no_double:+.3f}")
            print(f"  Double/take  {c.double_take:+.3f}")
            print(f"  Double/pass  {c.double_pass:+.3f}")
            print(f"  Proper:      {c.proper_action}")
        else:
            s = ev.static
            assert s is not None
            p = s.probs
            print("  No cube decision here (cube dead or owned by opponent).")
            print(
                f"  {p.win:.3f} {p.win_g:.3f} {p.win_bg:.3f} - {p.lose:.3f} {p.lose_g:.3f} {p.lose_bg:.3f}"
            )
            print(
                f"  Cubeless {s.cubeless_equity:+.3f}   Cubeful {s.cubeful_equity:+.3f}   ({s.ply})"
            )
        return 0

    if args.cmd == "sweep":
        spec = []
        for item in args.var:
            label, _, ops_json = item.partition("=")
            try:
                ops = json.loads(ops_json)
            except json.JSONDecodeError as err:
                print(f"error: bad JSON for variant {label!r}: {err}", file=sys.stderr)
                return 2
            spec.append((label.strip(), ops))
        try:
            result = analysis.run_sweep(engine, pos, spec, plies=args.plies, workers=args.workers)
        except (EngineError, perturb.PerturbError) as err:
            print(f"error: {err}", file=sys.stderr)
            return 1
        print(json.dumps(result.to_dict()["summary"], indent=2))
        return 0

    if args.cmd == "rollout":
        try:
            ev = engine.rollout(
                pos, moves=args.move or None, top=args.top, settings=_rollout_settings(args)
            )
        except (EngineError, ValueError) as err:
            print(f"error: {err}", file=sys.stderr)
            return 1
        print(json.dumps(ev.to_dict(), indent=2))
        return 0

    if args.cmd == "study":
        try:
            study = run_study(
                engine,
                pos,
                play=args.play,
                reasoning=args.reasoning,
                plies=args.plies,
                top=args.top,
                settings=_rollout_settings(args),
                extend_trials=args.extend_trials or None,
            )
        except (EngineError, ValueError) as err:
            print(f"error: {err}", file=sys.stderr)
            return 1
        folder = study.save(args.out, slug=args.slug)
        data = study.to_dict()
        data["saved_to"] = str(folder)
        print(json.dumps(data, indent=2))
        return 0

    return 0


def _json_arg(text: str | None):
    if text is None:
        return None
    if text.startswith("@"):
        text = Path(text[1:]).read_text()
    value = json.loads(text)
    if not isinstance(value, list):
        raise ValueError("expected a JSON list")
    return value


def _write(args) -> int:
    try:
        account = None
        if args.account is not None:
            account = sys.stdin.read() if args.account == "-" else Path(args.account).read_text()
        data = update_study(
            args.study_dir,
            hypotheses=_json_arg(args.hypotheses),
            variants=_json_arg(args.variants),
            account=account,
        )
    except (OSError, ValueError) as err:
        print(f"error: {err}", file=sys.stderr)
        return 2
    print(
        json.dumps(
            {
                "study": args.study_dir,
                "hypotheses": len(data.get("hypotheses") or []),
                "variants": len(data.get("variants") or []),
                "account_chars": len(data.get("account") or ""),
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
