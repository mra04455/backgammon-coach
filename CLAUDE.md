# backgammon-coach

Hypothesis-driven backgammon analysis. Claude is the analyst; an engine is the oracle.
The loop: state why a play is right → build position variants that would come out
differently if that explanation were wrong → evaluate them → keep, refine, or discard.

Read `docs/PLAN.md` for what to build next and `docs/ARCHITECTURE.md` for how the
pieces fit. Keep this file short; put detail in those two.

## Layout

- `src/bgcoach/position.py` — `Position` model, XGID parse/encode, ASCII board.
- `src/bgcoach/perturb.py` — named edits (move/add/remove checker, cube, score, dice, mirror)
  and `apply(pos, [op dicts])`.
- `src/bgcoach/engines/` — `Engine` protocol + `gnubg.py` backend (command file → `hint` → parsed).
- `src/bgcoach/analysis.py` — sweeps (base + variants, evaluated, deltas summarised).
- `src/bgcoach/mcp_server.py` — MCP tools: `show_position`, `perturb_position`, `evaluate`, `sweep`, `engines`.
- `src/bgcoach/cli.py` — `bgcoach show|eval|sweep` for quick checks.
- `tests/` — pytest; `tests/fixtures/` holds real gnubg 1.07 output the parser tests run against.

## Conventions

- Player `+1` = bottom (uppercase in XGID), `-1` = top. Points in perturbation ops are in the
  *acting player's own numbering* (1 = their ace point); `25` = bar, `0` = off.
- Equities are cubeful, normalised, from the on-roll player's view. `error` on a move is ≤ 0.
- Positions move between functions as `Position` objects; as XGID strings at the MCP boundary.
- Engine-specific parsing stays inside `engines/<name>.py`. Nothing above that layer may know
  what gnubg output looks like.

## Running things

```bash
python -m venv .venv && source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -e ".[dev]"
pytest                                                   # live gnubg test is skipped if gnubg is absent
bgcoach show "XGID=-b----E-C---eE---c-e----B-:0:0:1:31:0:0:0:0:10"
bgcoach eval "XGID=-b----E-C---eE---c-e----B-:0:0:1:31:0:0:0:0:10" --plies 2
```

gnubg: `brew install gnubg` (macOS), `apt install gnubg` (Debian/Ubuntu; binary is `/usr/games/gnubg`),
or the Windows installer (CLI is `gnubg-cli.exe`, not on PATH by default). If it isn't found,
set `BGCOACH_GNUBG=/path/to/gnubg`. `.mcp.json` registers the MCP server for Claude Code in
this repo; approve it once when prompted and check `/mcp`.

## gnubg gotchas (already handled, don't regress them)

- `set xgid` needs a game to exist: always `new match 0` first.
- A move filter with accept count `0` makes the CLI silently evaluate everything at 0-ply. Keep
  accept counts positive (`MoveFilter` enforces this; `test_build_commands_uses_positive_accept_counts`).
- `set lang C` so decimals are dots; `set output mwc off` so match equities print as equity.
- The on-roll player's moves are reported in *their* numbering; don't renumber them.

## Working style

- Small PRs, one PLAN step each. Add or extend a test for every behaviour change.
- When the engine disagrees with a stated hypothesis, that is a finding, not a bug.
- Don't add XG/UI-automation code until PLAN step 7; keep it behind the `Engine` protocol.
