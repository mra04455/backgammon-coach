"""Tiny CLI for poking at positions without an MCP client.

    bgcoach show  XGID
    bgcoach eval  XGID [--plies N]
    bgcoach sweep XGID --var "label: op json" ...   (see README)
"""

from __future__ import annotations

import argparse
import json
import sys

from bgcoach import analysis, perturb
from bgcoach.engines import EngineError, get_engine
from bgcoach.position import XGIDError, parse_xgid


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
    w.add_argument("--var", action="append", default=[], metavar="LABEL=OPS_JSON",
                   help='e.g. --var "no anchor=[{\\"op\\":\\"move\\",\\"player\\":1,\\"src\\":20,\\"dst\\":13}]"')
    w.add_argument("--plies", type=int, default=2)
    w.add_argument("--engine", default="gnubg")
    w.add_argument("--workers", type=int, default=2)

    args = ap.parse_args(argv)
    try:
        pos = parse_xgid(args.xgid)
    except XGIDError as err:
        print(f"error: {err}", file=sys.stderr)
        return 2

    if args.cmd == "show":
        print(pos.ascii())
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
                p = f"  {m.probs.win:.3f} {m.probs.win_g:.3f} {m.probs.win_bg:.3f} - {m.probs.lose:.3f} {m.probs.lose_g:.3f} {m.probs.lose_bg:.3f}" if m.probs else ""
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
            print(f"  {p.win:.3f} {p.win_g:.3f} {p.win_bg:.3f} - {p.lose:.3f} {p.lose_g:.3f} {p.lose_bg:.3f}")
            print(f"  Cubeless {s.cubeless_equity:+.3f}   Cubeful {s.cubeful_equity:+.3f}   ({s.ply})")
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

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
