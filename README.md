# backgammon-coach

A backgammon study tool built around one loop: **Claude forms a hypothesis about a position,
perturbs the position to test it, and asks an engine.**

```
 position ──▶ "why is this a take?" ──▶ 3 variants that would say otherwise ──▶ engine ──▶ verdict
```

The point isn't the equity number; it's a tested explanation of what drives the position.

## Status

Scaffold. The engine layer (GNU Backgammon), the XGID codec, the perturbation vocabulary, and an
MCP server for Claude Code are implemented and tested. The analyst procedure and the eXtreme
Gammon backend are next; see [docs/PLAN.md](docs/PLAN.md).

## Quick start

```bash
git clone https://github.com/mra04455/backgammon-coach && cd backgammon-coach
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"

# install GNU Backgammon
brew install gnubg            # macOS
sudo apt install gnubg        # Debian/Ubuntu (binary at /usr/games/gnubg)
# Windows: https://www.gnu.org/software/gnubg/ — use gnubg-cli.exe, set BGCOACH_GNUBG to its path

pytest
bgcoach show "XGID=-b----E-C---eE---c-e----B-:0:0:1:31:0:0:0:0:10"
bgcoach eval "XGID=-b----E-C---eE---c-e----B-:0:0:1:31:0:0:0:0:10" --plies 3
```

Then open Claude Code in the repo. `.mcp.json` registers the `bg-engine` MCP server; approve it
when asked and try:

> Show me XGID=-b----E-C---eE---c-e----B-:0:0:1:00:0:0:0:0:10, then tell me whether moving the
> back checkers up to the 20-point changes the cube action, and why.

## Tools exposed to Claude

| Tool | What it does |
| --- | --- |
| `show_position` | ASCII board + pips, off, bar, cube, score |
| `perturb_position` | Apply named edits (`move`, `add`, `remove`, `cube`, `away`, `dmp`, …) and return the new XGID |
| `evaluate` | Checker-play move list or cube table, cubeful equities, 0–4 ply |
| `sweep` | Base + labelled variants, evaluated in parallel, with deltas |
| `engines` | Which backends are available |

Conventions: player `+1` is the bottom side of the XGID (uppercase), `-1` the top. Points in
operations use the acting player's own numbering; `25` is the bar, `0` is off.

## Why gnubg first

It's headless, fast, free, cross-platform, and reads XGIDs. eXtreme Gammon has no API, so it can
only be driven by Windows UI automation; it's planned as a second, confirming backend behind the
same `Engine` interface. See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md).

## License

MIT
