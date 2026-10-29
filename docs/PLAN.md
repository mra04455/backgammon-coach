# Plan

Ordered. Each step is sized for one Claude Code session and one PR. Tick the box and add a
one-line note when done so the next session (or the chat side) can see where things stand.

## Done in the scaffold

- [x] XGID codec + `Position` model with pip counts, off counts, mirror, ASCII board. Round-trip
      tests on real XGIDs including bar checkers, owned cube, pending double, Jacoby/beaver bits.
- [x] Perturbation library with a dict-based `apply()` and human `describe()`.
- [x] gnubg backend: command-file driver, checker and cube `hint` parsers, fixtures captured from
      gnubg 1.07.001. Verified live: 2-ply and 3-ply checker play, cube decisions, match play,
      top player on roll.
- [x] Sweep: base + variants, parallel evaluation, delta summary.
- [x] MCP server (`show_position`, `perturb_position`, `evaluate`, `sweep`, `engines`) and `.mcp.json`.
      Exercised end to end through an MCP client.
- [x] `bgcoach` CLI for quick manual checks.

## Step 1 — Run it on your machine

- [ ] Clone, create a venv, `pip install -e ".[dev]"`, install gnubg, run `pytest`. All tests
      including `test_live_gnubg_round_trip` should pass. If gnubg isn't found, set `BGCOACH_GNUBG`.
- [ ] Start Claude Code in the repo, approve the `bg-engine` server when prompted, run `/mcp`, and
      ask it to `show_position` the starting XGID. Confirm the tools appear.
- [ ] Note the macOS/Windows gnubg path that worked in CLAUDE.md if it differed from the defaults.

## Step 2 — First real analysis session (no code)

- [ ] Pick 3 positions you already understand well (one checker play, one take/pass, one
      double/no-double). For each, ask Claude Code to: show the position, evaluate it, state a
      hypothesis about *why*, design 2–4 variants, run `sweep`, and write a short conclusion.
- [ ] Save the transcripts under `sessions/` (even as pasted markdown). These are the eval set
      for everything that follows: when a later change makes the analysis better or worse, these
      are how you'll know.
- [ ] Write down what was awkward: missing perturbation ops, confusing output fields, places where
      Claude misread the board. Those become Steps 3–4.

## Step 3 — Analyst skill

- [ ] Add `.claude/skills/analyze-position/SKILL.md` encoding the loop as a procedure: how to read
      the board, the hypothesis → variants → sweep → conclusion structure, the convention of
      stating a prediction *before* running the sweep, and how to report confidence. Keep it
      engine-agnostic.
- [ ] Add a `report` helper (markdown) in `analysis.py` so the conclusion of a sweep has a stable
      shape: position, hypothesis, variants with predicted vs observed deltas, verdict.

## Step 4 — Perturbation vocabulary

- [ ] Add ops that Step 2 showed were missing. Likely candidates: `slot` (place a blot from a
      stack), `break_point`, `advance_anchor`, `race_adjust` (shift N pips without changing
      structure), `swap_races` (give the other side the lead).
- [ ] Add a "legal move" generator (`moves.py`) so the analyst can also ask "what are the legal
      plays here" and compare the engine's list to its own.

## Step 5 — Rollouts

- [ ] gnubg rollouts behind the same `Engine` interface: `rollout(position, trials=…, truncation=…)`
      returning `Evaluation` with `ply="rollout"` plus confidence intervals. Used sparingly, as the
      confirmer at the end of a sweep.
- [ ] Cache evaluations on disk keyed by (engine, settings, xgid) so re-runs are free.

## Step 6 — Hosting (only if local becomes the bottleneck)

- [ ] Dockerfile that builds gnubg and runs the MCP server over HTTP with a bearer token, so the
      engine can be reached from claude.ai connectors and cloud Claude Code sessions.

## Step 7 — eXtreme Gammon as a second backend (Windows)

- [ ] `engines/xg.py` using pywinauto + clipboard, modelled on AnkiGammon's XG automation. Same
      `Evaluation` shape. Used for confirmation and rollouts only; gnubg stays the sweep engine.
- [ ] Compare gnubg vs XG on the `sessions/` set; log disagreements as findings.

## Parking lot

- GammonView / bgsage as a third backend if it proves strong enough.
- Import a match file (.mat/.sgf/.xg) and extract the positions where you erred, to feed the loop.
- Watch for an XG API after the ownership change; it would replace Step 7's UI automation.
