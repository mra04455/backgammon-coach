---
name: study
description: Study one backgammon position end to end. Roll out the decision, explain what drives it in expert vocabulary, test the explanation with position variants against gnubg, confirm with rollouts, and write a plain-language account into studies/. Use for /study <XGID> [your play] [your reasoning], or whenever the user wants to understand why a play or cube action is right.
---

# Study a position

You are the analyst. GNU Backgammon is the oracle: its rollouts are the truth and you
illuminate them. You never grade the engine, flag "blind spots", or hedge about its
reliability. The product is a plain-language account of what drives the position, written
so the reader gets it right next time. Read `docs/DESIGN.md` once if any of this is new.

Companion files: `knobs.md` (how to vary each feature) and `style.md` (how the account reads,
with model paragraphs). Read both before writing.

## Input

`/study <XGID> [your play or cube action] [your reasoning in plain text]`

Money play only for now. If the XGID is a match position, say so and stop. Positions are XGID
strings everywhere. Player `+1` is the bottom side (uppercase letters), `-1` the top. Points in
edits are in the acting player's own numbering (1 = their ace point), `25` = bar, `0` = off.

## Tools

Prefer the `bg-engine` MCP tools when connected: `show_position`, `evaluate`, `perturb_position`,
`sweep`, `rollout`. Otherwise the CLI does the same work from Bash:

```bash
.venv/bin/bgcoach show   XGID
.venv/bin/bgcoach facts  XGID --after "PLAY" --after "PLAY"   # exact counts; see "Counting"
.venv/bin/bgcoach eval   XGID --json
.venv/bin/bgcoach sweep  XGID --var "label=[ops json]" ...
.venv/bin/bgcoach rollout XGID [--move M ...] [--truncate P]
.venv/bin/bgcoach study  XGID [--play M] [--reasoning TEXT]   # step 1
.venv/bin/bgcoach write  STUDY_DIR --account FILE --hypotheses JSON --variants JSON   # step 6
```

Budget: a 2-ply evaluation is well under a second; a full rollout is about 100 s per candidate
play (4 cores). Sweep at 2-ply. Roll out only what the account rests on.

## Counting: never by eye

Every count in an account comes from `facts` (MCP tool or `bgcoach facts`) or from a rollout.
That includes: points made, the home board (own points 1 to 6 only; a point in front of it is a
block or prime, not board strength), open points, blots, spares (a point needs three checkers to
have a spare), the longest prime, anchors, checkers on the bar, pips and the race lead, shots at
each blot after each candidate play (rolls of 36, from full legal-move generation, so combination
shots and blocked intermediate points are handled), entering numbers, and the rolls that make a
point or cover a blot next turn. Run `facts` on the base and with `--after` for every play the
account discusses. If a sentence names a number or a count that is not in a `facts` output or a
rollout, remove the sentence or get the number.

The diagram is for orientation only. Two published accounts went wrong by reading it: one called
a point with two checkers a spare, one counted an opponent's outfield block as home-board points.

## Procedure

Work through the six steps in order. Do not write any explanatory prose for the user until
step 6; progress notes are fine.

### 1. Roll out the original position first

```bash
.venv/bin/bgcoach study XGID --play "..." --reasoning "..."
```

This evaluates the decision at 2-ply, rolls out the top candidates plus the user's play,
extends the rollout if the decision is close, and writes `studies/<date>-<slug>/study.json`
and `study.md`. Note the folder path from `saved_to`. Read the `verdict`: it is the thing you
are explaining and nothing you write may contradict it.

Run `facts` on the base and with `--after` for the rolled-out plays. Show the user the board
(`show_position` or the `ascii` field) and state the verdict in one line: best play, the user's
play, the size of the error in words. No explanation yet.

### 2. Explain in the expert vocabulary

Form an explanation of the form: *feature F drives this decision; change F and the decision
should move this way by roughly this much.* Use the vocabulary of Magriel, Robertie and
Woolsey: race lead, board strength, anchor height, timing and spares, blots in the opponent's
board, gammon potential, cube ownership. One decisive feature, perhaps a supporting one.

If the user gave reasoning, answer it: which feature did they weight wrongly, and under what
conditions would their reasoning have been right? That counterfactual becomes a variant.

Write each hypothesis down **before** touching the engine, with its predictions:

```json
{"id": "H1", "feature": "board strength", "claim": "hitting is right because O's board is weak",
 "predictions": [
   {"variant": "O makes 4-pt", "direction": "hitting loses ground", "size": "flips to safe play"},
   {"variant": "race +8 for X", "direction": "none", "size": "control"}
 ]}
```

### 3. Sweep

For every feature that could plausibly matter, build a variant that changes it (see
`knobs.md`), including one or two **controls**: features your explanation says will *not*
matter. Three to six variants per round. Check each variant with `perturb_position` or
`bgcoach show` and record exactly what moved (pips, points, blots), because something else
always changes too; the record is precise rather than claiming nothing else did.

Run them together with `sweep` (or `bgcoach sweep`) at 2-ply. Read the summary deltas against
the base.

Rules for reading a 2-ply sweep (internal; they never appear in the account):

- A prediction **holds** when the observed shift agrees in direction and exceeds 0.05 equity.
  A shift inside 0.05 counts as **no effect**, whichever way it points.
- A control that moves more than 0.05 is a failed prediction too.
- For checker-play studies every candidate play you discuss must remain legal in every variant
  you make a claim about. Check the variant's move list; if a play vanished, change the edit.
- Equities are always from the perspective of the player on roll in the **original** position.
  If a variant flips the turn or the cube, negate before comparing.

### 4. Refine

Where predictions failed, revise the explanation and design variants that distinguish the
revised account from the old one. Repeat steps 2 to 3 until every prediction holds. When the
engine disagrees with you, that is a finding about the position, not a bug. Keep every
hypothesis you tried, with its status (`held`, `failed`, `revised to H2`), in the list you will
store; only the final one shapes the account.

### 5. Confirm with rollouts

Roll out the variants the final explanation rests on, at most **four** beyond the original.
Use `rollout` with the specific plays you compare (`moves=[...]`), not a blanket top-N. For a
cube variant roll out the position; for a variant with no cube decision you get its value.

- A rollout contradicts a 2-ply sweep result when the direction differs or the difference is
  inside two joint standard errors (`sqrt(se1² + se2²)`). A contradiction sends you back to
  step 4.
- If the explanation needs more than four load-bearing variants, it is too complicated. Say so
  to the user and write the account around the one or two features the rollouts do support.

### 6. Write and record

Write the account following `style.md`. Before storing it, check every count in it against the
`facts` outputs (a checklist is in `style.md`). Then store everything:

```bash
.venv/bin/bgcoach write studies/<folder> --account account.md \
  --hypotheses @hypotheses.json --variants @variants.json
```

`study.md` is re-rendered from the JSON with the account on top and the engine record in a
collapsed section; you do not write that section. Each stored variant should carry: `label`,
`operations`, `xgid`, `what_moved`, `prediction`, `observed_2ply` (delta), `holds`, and
`rollout` for the confirmed ones (equities, standard errors, trials). Store numbers as the
engine gave them; the account is where they become words.

Finish by showing the user the account itself, not a summary of your process.
