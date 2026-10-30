# Style guide for the account

The account is the conclusion and why it is right. It teaches; it does not show work. The
variants were quality control, like an editor's fact-check, and they do not appear. Exploration
history, abandoned hypotheses and the sweep never appear either. The engine record is appended
automatically in a collapsed section, so the account itself needs no numbers table.

## Rules

1. **Decisive feature first.** The first sentence names what drives the position. Not the
   verdict, not the equity: the reason.
2. **Error size in words.** "A blunder costing a quarter of a point", "a small error", "the
   plays are level". Never a decimal.
3. **Probabilities as rough round numbers only.** "About one shot in three", "a gammon one
   game in five". Never a percentage with a decimal.
4. **Rules of thumb come with the situation in which they fail.** "The leader should race;
   that stops being true once the trailer's board is strong enough to punish a hit."
5. **Silence about features that did not matter**, unless the silence would surprise a player,
   in which case one sentence: "the race turned out not to matter here."
6. **Any number that reaches the account comes from a rollout**, never from a 2-ply evaluation.
7. **No confidence statements, no process hedging.** Not "this only changed the race by one pip
   so we cannot be sure". Not "the engine suggests". Say what is true.
8. **No thresholds deciding the kind of response.** When plays are level, say they are level and
   explain what each plan accomplishes. Do not hunt for why one is a hair better.
9. **Length follows the idea, not the equity.** A huge blunder can be one sentence. A small
   error with an interesting cause can be a page.
10. **Explain the best play against the alternatives that matter:** the user's play when given,
    otherwise the plans a player would seriously consider. Each alternative gets what it
    accomplishes and why that is worth less here, and when it would be right.
11. **Answer the user's reasoning directly** when they gave it: which feature they weighted
    wrongly, when their reasoning would have been right, then the correct account.
12. **A reference position appears only when it teaches.** "This is the standard 20-point
    holding game take with a stronger board for the trailer" is fine; a reference for its own
    sake is not. Never required.
13. **Equities from the perspective of the player on roll in the original position**, even when
    the sentence is about a variant that flipped the turn or the cube.
14. **Never grade the engine.** No "blind spot", no "the bot may be wrong here", no "rollouts
    are only as good as the bot's play".

## Shape

- Opening paragraph: the decisive feature, the best play, the size of the error.
- One paragraph per alternative that matters: what it accomplishes, why that is worth less
  here, when it would be right.
- If the user gave reasoning: a paragraph that answers it.
- Optional closing line: the rule of thumb this position illustrates, with its failure case.

## Model paragraphs

These show the voice. The positions are generic; do not reuse the verdicts.

**A clear checker-play error:**

> This position is about O's board, not the race. O already holds four points, so a hit that
> leaves a return shot costs you a game you were otherwise winning about two times in three.
> Playing safe with 13/7 6/5 gives up nothing you cannot get next turn. Hitting is a blunder,
> costing about a sixth of a point. Hitting would be right if O's board had two points fewer:
> then being hit back is an inconvenience, not a disaster, and the tempo matters more.

**Level plays:**

> The two plays are level, and they are level because they are different plans, not because
> the position does not care. 24/20 commits to a holding game: you accept a race deficit and
> wait for a shot from the 20-point, which comes about one game in three. 13/9 6/5 plays for
> the prime and the gammon, at the cost of a blot O hits one roll in four. Pick the plan that
> matches the cube: with the cube centred both are fine, with O holding the cube the quiet
> plan is the one that does not hand O a cash.

**A take, answering the user's reasoning:**

> You passed because you counted the race and found yourself eleven pips behind. The race is
> the wrong feature here. Your 20-point anchor means the race only decides the game if O gets
> the whole army home without leaving a shot, and with three outfield checkers still to clear
> O leaves one about two games in five. When you hit, your four-point board wins the game
> outright often enough that the take is comfortable, worth a fifth of a point more than
> passing. The pass would be right without the anchor, or with your board down to two points;
> then a hit would only start a long race you are losing.

## Before the account leaves your hands

Check each of these against the `facts` output for the position and for every play named:

- Home board sizes for both sides (points 1 to 6 only), and whether a claimed "stronger board" is true.
- Every "spare", "builder" and "cover" named: the point holds three or more checkers, or the
  cover number appears in `my_next_turn`.
- Every shot count and hit chance: the number in `opponent_threats.shots`, written as a rough
  fraction of 36.
- Every entering number, pip count and race lead.
- Every point the account calls open, made, slotted or a prime.
- Every equity and error size: from the rollout, in words.

A claim that fails the check is removed or corrected; it is never softened into a hedge.

## Words for sizes

Use these consistently (cubeful equity, money play):

| Rollout difference | Word |
|---|---|
| under 0.02 | level |
| 0.02 to 0.04 | a small error |
| 0.04 to 0.08 | an error |
| 0.08 to 0.16 | a blunder |
| over 0.16 | a huge blunder |

Fractions of a point are allowed where they help: "almost a quarter of a point" for 0.23.
