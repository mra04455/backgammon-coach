# backgammon-coach: design

Agreed design for version one. Written after a structured design interview;
the research that informed it is in `docs/research/`.

## Purpose

The greatest backgammon learning tool: unlimited, world-class explanations of
your own errors. You give it a position (and, ideally, the play you made and
what you were thinking). It returns a plain-language account of what actually
drives the position, written so that you get it right next time.

Version one is a personal tool run from Claude Code. A public app later wraps
the same core; the core is designed so that only the driver changes.

## Roles

- **Claude is the analyst.** It forms the explanation, designs the tests, and
  writes the account. In version one it runs inside a Claude Code session via
  a skill. Later, an agent loop calling the Claude API drives the same tools.
- **GNU Backgammon is the oracle.** Its highest level (rollouts) is treated as
  the truth. The tool illuminates the engine's verdict; it never grades the
  engine, flags "blind spots", or hedges about engine reliability.

## Oracle

- Two builds of the same engine behind one interface:
  - the `gnubg` Python wheel for fast in-process evaluation (2-ply in ~30 ms)
    and legal-move ranking;
  - the real `gnubg` command-line binary, built from source, driven as a
    subprocess, for rollouts. (The wheel's rollout command is a no-op and its
    `hint` hangs on checker plays; verified.)
  - Fallback if the build fails: a rollout loop on top of the wheel's move
    finder (slower, no variance reduction).
- Rollout settings: gnubg defaults (1296 trials, cubeful, variance reduction,
  no truncation, early stop when settled), extended to 5184 trials when the
  decision being confirmed is close. Note that the gnubg binary ships with
  early stopping switched off; the driver switches JSD stopping on (limit
  2.33, minimum 324 games). Measured on a 4-core machine with gnubg
  1.08.003: about 100 s per candidate at 1296 trials, so a two-play
  decision is about 3.5 minutes and a cube decision about 1.7 minutes.
- Money play only in version one. Match context is carried in the position
  format so match play is additive later.
- Cube verdicts (take/pass, double/no double) are derived from cubeful
  equities in our code, since the wheel does not expose them.

## Input

`/study <XGID> [your play] [your reasoning in plain text]`

- Position as XGID (GNUbg IDs also accepted). No hand-typed board format.
- Your play or cube action: optional.
- Your reasoning: optional free text. When given, the account answers it
  directly: which feature you weighted wrongly, when your reasoning would have
  been right, then the correct account.
- One position per run. Importing a game file and studying its blunders is a
  later feature that feeds this same entry point.

## Analysis loop

1. **Roll out the original position first.** Its verdict is the thing being
   explained and must be established before any explaining starts.
2. **Explain in the expert vocabulary.** Claude proposes an explanation of the
   form "feature F drives this; change F and the decision should move this
   way by roughly this much". The vocabulary is drawn from Magriel, Robertie,
   Woolsey and modern annotators: race lead, board strength, anchor height,
   timing/spares, blots in the opponent's board, gammon potential, cube
   ownership, score.
3. **Sweep.** Claude predicts, for every plausibly relevant feature, whether
   and how the decision moves. The tool exposes feature *knobs* (e.g. "race
   +8 pips for the leader", "remove the 20-point anchor"); Claude picks knobs
   and sizes, the tool turns each into a concrete, validated position edit and
   records exactly what moved (something else always changes; the record is
   precise rather than claiming nothing else did). Raw edits are available as
   an escape hatch. All sweep variants are evaluated at 2-ply.
   - A prediction *holds* when the observed shift agrees in direction and
     exceeds the 2-ply noise band (~0.05 equity). Inside the band counts as
     "no effect". This rule is internal; it never appears in the account.
   - Controls (knobs the explanation predicts will *not* matter) are part of
     the sweep.
4. **Refine.** Where predictions failed, revise the explanation and design
   variants that distinguish the revised account from the old one. Repeat
   until predictions hold.
5. **Confirm.** Roll out the variants the final explanation rests on (cap:
   four beyond the original). A contradicting rollout sends the explanation
   back to step 4. If an explanation needs more than four load-bearing
   variants, it is too complicated and the skill says so.
6. **Write.** See Output.

Validation: structural legality only (both sides on one point, more than 15
checkers, negative counts); reachability is not attempted. For checker-play
studies, every candidate play discussed must remain legal in any variant it is
claimed about.

Checker play is the first end-to-end milestone; cube decisions are second, on
a decision-agnostic core.

## Output

A markdown explanation written to teach, not to show work.

- The account is the conclusion and why it is right. The variants are quality
  control (like an editor's fact-check), not the explanation. Exploration
  history, abandoned hypotheses and the sweep never appear in the account.
- Decisive feature first. Error size in words, not decimals. Probabilities
  only as rough round numbers. Rules of thumb stated with the situations in
  which they fail. Silence about features that turned out not to matter,
  unless that silence would itself surprise a player.
- Any number that does reach the account comes from a rollout, never from a
  2-ply evaluation.
- No confidence statements. No process hedging ("this only changed the race
  by one pip so we cannot be sure..."). No thresholds deciding the *kind* of
  response: when plays are level, say they are level and explain what each
  plan accomplishes; do not hunt for why one is a hair better. The length of
  an explanation follows the idea, not the equity: a huge blunder can be one
  sentence, a small one a page.
- Explains the best play against the alternatives that matter: your play when
  you gave one, otherwise the plans a player would seriously consider.
- A supporting position, or a famous reference position with a known
  solution, appears only when it teaches ("this well-known holding game shows
  that even if X were true, it is still a take"). Never required.
- Equities are always from the perspective of the player on roll in the
  original position, even in variants that flip the turn or cube.
- The skill carries a short style guide, derived from the research, with
  model paragraphs, so the voice is consistent.
- The markdown ends with a collapsed "how this was checked" section for the
  curious. The full test record is in the JSON.

## Storage

- `studies/<date>-<slug>/study.json`: source of truth. Position, your play
  and reasoning, hypotheses, variants (knob, concrete edit, pip deltas,
  predictions), engine results tagged with depth/trials/engine version,
  verdicts, and the final account.
- `studies/<date>-<slug>/study.md`: rendered from the JSON.
- The JSON is the seam the future app reads.

## Reference positions

Minimal in version one: the data structure, a handful of seeds from public
sources, and "nearest reference: none yet" when there is none. Growing it well
is its own project and depends on access to the expert literature.

## Repository

- Python 3.13, `uv`, `pytest`, `ruff`.
- `bgcoach` CLI; every subcommand emits JSON. Subcommands mirror the skill's
  steps so a later agent loop can drive them one for one.
- Engine build script for the gnubg binary, run once at setup.
- `.claude/skills/study/`: the analyst procedure, knob checklist by position
  type, and style guide.
- `docs/DESIGN.md` (this file), `docs/research/`.

## Deferred

- Adaptive evaluation depth (go deeper when the conclusion is not safe under
  the engine's error band). Version one uses the fixed policy above.
- Match play.
- Game-file import and blunder selection.
- Growing the reference-position library.
- A corpus of expert writing (bkgm.com, bgonline.org, etc.) for the analyst
  to draw on. Both sites were reachable from the cloud environment on
  2026-10-29 (the research notes were written while they were blocked), so
  this is deferred on priority, not access.
- The public app: web front end plus an API-driven agent loop over the same
  core.
