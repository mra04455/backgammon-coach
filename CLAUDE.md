# backgammon-coach

Hypothesis-driven backgammon analysis. Claude is the analyst; an engine is the oracle.
The loop: state why a play is right → build position variants that would come out
differently if that explanation were wrong → evaluate them → keep, refine, or discard.

Read `docs/DESIGN.md` for the agreed design (roles, oracle, analysis loop, output,
storage), `docs/PLAN.md` for what to build next and `docs/ARCHITECTURE.md` for how the
pieces fit. `docs/research/` holds the notes the design rests on. Keep this file short;
put detail in those.

## Layout

- `src/bgcoach/position.py` — `Position` model, XGID parse/encode, ASCII board.
- `src/bgcoach/perturb.py` — named edits (move/add/remove checker, cube, score, dice, mirror)
  and `apply(pos, [op dicts])`.
- `src/bgcoach/engines/` — `Engine` protocol + `gnubg.py` backend: `evaluate` (command file →
  `hint` → parsed) and `rollout` (two passes: rank at 2-ply, then `analyse rollout move`/`cube`).
- `src/bgcoach/moves.py` — legal plays for a roll (checked against gnubg's move list), gnubg-notation
  parse/format, and exact counts: shots at a blot, entering numbers, point-making numbers.
- `src/bgcoach/facts.py` — the counts an account relies on (home board, blots, spares, primes, shots
  after a play, cover numbers), so nothing is read off the diagram.
- `src/bgcoach/analysis.py` — sweeps (base + variants, evaluated, deltas summarised).
- `src/bgcoach/study.py` — a study: candidates at 2-ply, rollout verdict, `studies/<date>-<slug>/study.{json,md}`.
- `src/bgcoach/mcp_server.py` — MCP tools: `show_position`, `facts`, `perturb_position`, `evaluate`, `sweep`, `rollout`, `engines`.
- `src/bgcoach/cli.py` — `bgcoach show|facts|eval|sweep|rollout|study|write`; all but `show`/`eval` emit JSON.
  `study` rolls out the original (extending close decisions to 5184 trials); `write` records the
  analyst's hypotheses, variants and account and re-renders `study.md` from the JSON.
- `.claude/skills/study/` — the analyst skill: `/study <XGID> [play] [reasoning]` runs the loop in
  DESIGN.md (`SKILL.md` procedure, `knobs.md` feature edits, `style.md` voice and model paragraphs).
- `scripts/build-gnubg.sh` — builds the gnubg CLI binary from source into `.gnubg/` (gitignored).
- `tests/` — pytest; `tests/fixtures/` holds real gnubg 1.07 and 1.08 output the parser tests run against.

## Conventions

- Player `+1` = bottom (uppercase in XGID), `-1` = top. Points in perturbation ops are in the
  *acting player's own numbering* (1 = their ace point); `25` = bar, `0` = off.
- Equities are cubeful, normalised, from the on-roll player's view. `error` on a move is ≤ 0.
- Rollout results carry `se` (standard error of the cubeful equity) and `trials` (games actually
  played; fewer than requested when JSD stopping ended it). Evaluations leave both None.
- Any number that reaches a written account comes from a rollout, never from a 2-ply evaluation.
  Any count (points, blots, spares, shots, entering numbers) comes from `bgcoach facts`, never
  from reading the diagram. Home board means a player's own points 1 to 6.
- Positions move between functions as `Position` objects; as XGID strings at the MCP boundary.
- Engine-specific parsing stays inside `engines/<name>.py`. Nothing above that layer may know
  what gnubg output looks like.

## Running things

```bash
uv venv .venv && uv pip install -e ".[dev]" --python .venv/bin/python   # or python -m venv + pip
scripts/build-gnubg.sh                                   # once; ~1 min, needs the packages it lists
.venv/bin/pytest                                         # live gnubg tests are skipped if gnubg is absent
bgcoach show "XGID=-b----E-C---eE---c-e----B-:0:0:1:31:0:0:0:0:10"
bgcoach eval "XGID=-b----E-C---eE---c-e----B-:0:0:1:31:0:0:0:0:10" --plies 2
bgcoach rollout "XGID=-b----E-C---eE---c-e----B-:0:0:1:31:0:0:0:0:10" --top 2 --trials 36   # quick
bgcoach study "XGID=-b----E-C---eE---c-e----B-:0:0:1:31:0:0:0:0:10" --play "13/9" --reasoning "..."
```

gnubg: the engine looks for `$BGCOACH_GNUBG`, then the repo-local build at `.gnubg/bin/gnubg`,
then `gnubg` on PATH (`brew install gnubg`, `apt install gnubg` with `/usr/games/gnubg`, or the
Windows `gnubg-cli.exe`). Verified against 1.07.001 and 1.08.003. `.mcp.json` registers the MCP
server for Claude Code in this repo; approve it once when prompted and check `/mcp`.

Rollout cost (4 cores, gnubg 1.08, 1296 trials): about 100 s per candidate play, 200 s for a
two-play decision, 100 s for a cube decision. JSD early stopping (on by default) ends a settled
two-play rollout after 324 games. Use `--truncate` for ranking sweeps, full rollouts for numbers
that reach an account.

## gnubg gotchas (already handled, don't regress them)

- `set xgid` needs a game to exist: always `new match 0` first.
- A move filter with accept count `0` makes the CLI silently evaluate everything at 0-ply. Keep
  accept counts positive (`MoveFilter` enforces this; `test_build_commands_uses_positive_accept_counts`).
  Related: when only one move survives a filter stage gnubg skips the final-ply pass, so a
  "2-ply" hint can label its best move 1-ply. Positive accept counts avoid that too.
- `set lang C` so decimals are dots; `set output mwc off` so match equities print as equity.
- The on-roll player's moves are reported in *their* numbering; don't renumber them.
- The bare `rollout` command takes no arguments and prints results only on a tty. Checker plays
  are rolled out via `move`, `previous`, `analyse move`, `analyse rollout move <ranks>`; cube
  decisions via `double`, `previous`, `analyse move`, `analyse rollout cube`. Ranks come from the
  analysed list, so `set analysis ...` must mirror `set evaluation ...` (`MoveFilter.commands`).
  When the player on roll has no cube decision (opponent's cube, dead cube) the bare `rollout`
  runs under a pseudo-terminal (`_run_under_pty`) and its `Current Position:` block is parsed.
- gnubg starts with one calculation thread; the driver sets `set threads <cpu count>`.
- gnubg ships with JSD/STD early stopping off; `RolloutSettings` turns JSD stopping on.
- `set xgid` rejects a pending double (`:D:`); the driver rolls out the doubler's decision instead.
- Money-play XGID field 8 is honoured by `set xgid`: bit 1 sets the Jacoby rule, bit 2 allows
  beavers (checked with `show jacoby`/`show beavers`, gnubg 1.08). Jacoby moves the no-double
  equity; beavers change the advice wording ("No double, beaver"). Keep the flags constant within
  a study and matching the conditions you play under.

## Working style

- Small PRs, one PLAN step each. Add or extend a test for every behaviour change.
- When the engine disagrees with a stated hypothesis, that is a finding, not a bug.
- Don't add XG/UI-automation code until PLAN step 7; keep it behind the `Engine` protocol.
