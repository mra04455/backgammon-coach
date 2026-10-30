# Knobs: how to vary each feature

Every variant is a list of edit operations applied to the base XGID. The operations are
`move`, `move_point`, `add`, `remove`, `make_point`, `cube`, `dice`, `turn`, `mirror` (and the
match-score ones, unused in money play). Points are in the **acting player's own numbering**
(1 = their ace point, 24 = their opponent's ace point), `25` = bar, `0` = off. Player `1` is the
bottom side of the XGID, `-1` the top.

Recipes below name the feature, say which way the decision should move if the feature is what
matters, and give the edit. Choose sizes that are large enough to show (a one-pip race change
tells you nothing at 2-ply) but not so large the position changes character. Always inspect the
result and write down what else moved.

## Race lead

Shift pips without changing structure: advance a spare from one point to a point already held.
"+8 pips for X" = move two of X's spares forward four pips each, e.g. from the midpoint to the
9-point if X holds the 9-point. To hand the lead to the other side, do the same for O.

```json
[{"op": "move", "player": 1, "src": 13, "dst": 9}, {"op": "move", "player": 1, "src": 13, "dst": 9}]
```

Prediction shape: the leader's safe plays and doubles gain; the trailer's bold plays gain.
Watch: moving spares can also create or remove builders and blots. Record it.

## Board strength

Make or break a home-board point. Cover a blot with `make_point`; break a point by moving one
checker off it to a spare position; add a point by moving two spares onto it.

```json
[{"op": "make_point", "player": -1, "point": 4}]
[{"op": "move", "player": -1, "src": 4, "dst": 2}]
```

Prediction shape: a stronger board for the hitter makes hitting (and doubling) better; a
stronger board for the side being hit makes the bold play worse and the take better.
Watch: the checkers you use come from somewhere; keep the pip count roughly level unless the
race is the thing you are testing.

## Anchor height and presence

Move both anchor checkers together with `move_point`; remove the anchor by advancing both out.

```json
[{"op": "move_point", "player": 1, "src": 20, "dst": 21}]
[{"op": "move_point", "player": 1, "src": 20, "dst": 13}]
```

Prediction shape: a higher anchor (20, 21) makes the holding game a more comfortable take and
blunts a blitz; losing the anchor turns a take into a pass in many holding games.
Watch: removing an anchor changes the race by many pips. Pair it with a race control.

## Timing and spares

Give a side more time by pulling a spare back (e.g. from the 6-point to the midpoint) or less
by advancing one into the home board. Stacks and dead checkers are timing too: move a spare
from a stack onto a useful point to test whether distribution matters.

```json
[{"op": "move", "player": 1, "src": 6, "dst": 13}]
```

Prediction shape: the side that must hold a position gains from more time; the side that wants
to attack now gains from the opponent having less.

## Blots in the opponent's board / shots

Add a blot where it can be hit, or lift one to safety. Count the shots in both positions and
record the number.

```json
[{"op": "move", "player": 1, "src": 8, "dst": 22}]
```

Prediction shape: more shots for the opponent make the bold play worse and the double better
for the side with the board to punish a hit.

## Gammon potential

No single edit changes gammon chances alone; use two proxies and say which you used. Checkers
sent back (add a checker to the bar or to the opponent's home board) raise the gammon rate
against that side; closing points in the attacker's board raises it the other way. Compare
the win/gammon probabilities in the engine output, not only the equity.

```json
[{"op": "move", "player": -1, "src": 13, "dst": 25}]
```

## Cube ownership and level

```json
[{"op": "cube", "owner": -1, "value": 2}]
[{"op": "cube", "owner": 0, "value": 1}]
```

When the opponent owns the cube the player on roll has no cube decision; the variant returns
the position's value, and you compare values. When testing whether "the recube makes this a
take", compare the take with a centred cube against the same position with the taker owning a
2-cube (which is what taking produces).

## Who is on roll

`{"op": "turn", "player": -1}` plus a dice change if the base had dice. Use sparingly: it
changes the question, not a feature of the position. `mirror` swaps the sides (useful only to
check that a verdict does not depend on which side is which).

## Reading the result

Do not read a variant's pips, points or shots off the board. `bgcoach facts VARIANT_XGID` gives
them, and `--after PLAY` gives the shots and cover numbers after each candidate play in the
variant. Record `what_moved` from that output.

## Saturation

When one side is already a double/pass, cubeful equities pin at exactly +1.000 or -1.000 and
every play reads the same. If a variant does that, re-run it with the trailing side owning the
cube (`{"op": "cube", "owner": <trailer>, "value": 2}`) so no cash is possible, compare plays in
that frame, and say so in the record.

## Controls

Every sweep needs one or two variants your explanation says will not matter: a race change
when you claim it is about the board, a board change when you claim it is about the race.
Predict "no effect" explicitly. A control that moves more than 0.05 at 2-ply is a failed
prediction and sends you back to refine.

## By position type, where to start

- **Opening and early game:** builders versus safety; blots in the outfield; the 5-point and
  4-point; whether the back checkers are split. Race rarely matters yet.
- **Holding game (20- or 21-point anchor):** race lead first, then anchor height, then the
  trailer's board strength and timing. Classic take/pass territory.
- **Blitz:** attacker's board strength and spares in the zone; defender's anchor (none, 24, or
  advanced); checkers already on the bar. Gammon rate drives the cube.
- **Prime versus prime:** timing (who must break first), the number of checkers behind the
  prime, spare count on the prime. Small edits swing a lot here; record pips carefully.
- **Backgame:** timing above all; the forward position of the backgame player's other checkers;
  which two points are held.
- **Race and bearoff:** pip count, wastage (stacked low points, gaps), checkers off. Cube
  decisions turn on a few pips; use larger edits than you think.
- **Late game, one side closed out:** checkers on the bar, the closed-out side's board, pips.
