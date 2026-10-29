# Architecture

## The idea in one paragraph

A study tool where Claude acts as the analyst and an engine acts as the oracle. Given a
position, Claude proposes an explanation for why the best play is best ("this is a take
because of the 20-point anchor, not the race"), designs small variations of the position that
would be true-if-the-explanation-is-right and false-otherwise, runs them through the engine,
and reads how the equities shift. The output is a tested, plain-language account of what
drives the position, which is the thing a human needs in order to generalise.

## Layers

```
 Claude Code (analyst)  ──MCP──▶  mcp_server.py
                                      │
                       ┌──────────────┼───────────────┐
                       ▼              ▼               ▼
                 position.py     perturb.py      analysis.py
                 (XGID codec)    (named edits)   (sweeps, deltas)
                                                      │
                                                      ▼
                                              engines/base.py  ◀── Engine protocol
                                                 │          │
                                            engines/gnubg.py   engines/xg.py (later)
                                                 │
                                          gnubg -t -q -c <file>
```

- **position.py** is the only place that knows the XGID format. Everything else works with
  `Position`. The 26-char board is stored as 24 signed ints plus two bar counts; checkers off are
  derived (15 minus on-board minus bar).
- **perturb.py** gives edits stable names so the analyst can describe an experiment as data
  (`[{"op": "move", "player": 1, "src": 20, "dst": 13}]`). Edits are not legal-move checked: an
  experiment often needs a position that could not arise from the base by a legal play.
- **engines/** returns one `Evaluation` type regardless of backend. Move lists, cube tables and
  probabilities are normalised there; raw engine text is kept on the object for debugging.
- **analysis.py** runs a base plus N variants (optionally in parallel; gnubg is one process per
  call) and computes the deltas an analyst actually looks at: best-move equity change, whether the
  best move changed, take margin, double margin, whether the cube action changed.
- **mcp_server.py** is thin: it parses, calls, and serialises. Tool docstrings are written for the
  model that will call them, so they carry the operation vocabulary and the numbering conventions.

## Engine choice

GNU Backgammon first: headless, fast (2-ply ≈ 0.1 s, 3-ply ≈ 0.7 s on a laptop-class CPU),
accepts XGIDs directly, cross-platform. eXtreme Gammon has no API; the only route is Windows UI
automation (see AnkiGammon's pywinauto approach), which is slow and brittle. The plan is gnubg for
the exploratory sweep where speed matters and small errors wash out, XG later as a confirmer for
the one or two conclusions that survive. Because both sit behind `Engine`, swapping or adding a
backend doesn't touch the analyst layer.

## Known limits / open questions

- XGID field 8 in money play (Jacoby bit 0, beaver bit 1) is implemented from the spec but not
  yet confirmed against an XGID exported by XG with beavers on.
- When the dice field is `D` (double offered), which player `turn` refers to has not been
  confirmed against XG. gnubg accepts the string and prints the doubler-side cube table either way,
  so `CubeEval.take_decision` is derived from that table rather than from `turn`.
- gnubg's `hint` in match play prints normalised equity (we force `set output mwc off`). If a
  future gnubg prints MWC the move regex accepts `MWC:` and a `%` suffix, but the numbers would
  then be MWC, not equity; a test should catch this.
- No rollouts yet. gnubg can do them (`rollout` after `hint`, with `set rollout ...` settings);
  that's PLAN step 5.
