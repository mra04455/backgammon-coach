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

- [x] `.claude/skills/study/` encodes the DESIGN.md loop: roll out the original first, hypothesis
      with predictions before any sweep, 2-ply sweep with the 0.05 band and controls, refine,
      confirm with at most four rollouts, write. `knobs.md` maps each expert feature to concrete
      edits and lists where to start by position type; `style.md` carries the rules and model
      paragraphs. (DESIGN.md says no confidence statements, so none are reported.)
- [x] Stable report shape: `study.md` is rendered from `study.json` (`bgcoach write` records
      hypotheses, variants and the account; the engine record is the collapsed section).
- [ ] Run the skill on three positions the user knows well (Step 2) and fix what is awkward.

## Step 4 — Perturbation vocabulary

- [ ] Add ops that Step 2 showed were missing. Likely candidates: `slot` (place a blot from a
      stack), `break_point`, `advance_anchor`, `race_adjust` (shift N pips without changing
      structure), `swap_races` (give the other side the lead).
- [x] Legal move generator (`moves.py`), checked against gnubg's full move list on four positions,
      plus exact shot, entering and point-making counts, and `bgcoach facts` / the MCP `facts` tool
      (2026-10-30, after two published accounts misread the diagram).

## Step 5 — Rollouts

- [x] gnubg rollouts behind the same `Engine` interface: `rollout(position, moves=…, top=…,
      settings=RolloutSettings(...))` returning `Evaluation` with `ply="rollout"`, `se`, `trials`
      and a `RolloutInfo` provenance block. Checker plays and cube decisions; pending doubles are
      rolled out as the doubler's decision. Exposed as `bgcoach rollout` and the MCP `rollout` tool.
      (2026-10-29: built gnubg 1.08.003 from source with `scripts/build-gnubg.sh`; measured ~100 s
      per candidate at 1296 trials on 4 cores.)
- [x] First end-to-end study: `bgcoach study XGID [--play] [--reasoning]` evaluates at 2-ply, rolls
      out the top plays plus yours, and writes `studies/<date>-<slug>/study.{json,md}` with the
      DESIGN.md schema (hypotheses, variants and account left for the analyst to fill).
- [ ] Cache evaluations on disk keyed by (engine, settings, xgid) so re-runs are free.
- [x] Position-only rollouts for positions with no cube decision (opponent owns the cube, Crawford,
      DMP): the bare `rollout` under a pseudo-terminal, parsed into `static` with `se`/`trials`.
- [ ] Use the `gnubg` PyPI wheel for sweeps: verified importable on Python 3.13 here, 2-ply
      `evaluate` about 20 ms cold. Would replace one subprocess per 2-ply evaluation.

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
