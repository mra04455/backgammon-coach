# Study: XGID=a-BCB-B-B---bD---bbcbab---:0:0:-1:61:0:0:3:0:10

```
 +-13-14-15-16-17-18-+---+-19-20-21-22-23-24-+
 | X           O  O  | O | O  O  O  O        |
 | X           O  O  |   | O  O     O        |
 | X                 |   | O                 |
 | X                 |   |                   |
 |                   |   |                   |
 |                   |BAR|                   |
 |                   |   |                   |
 |                   |   |                   |
 |                   |   |          X        |
 | O           X     |   | X     X  X  X     |
 | O           X     |   | X     X  X  X     |
 +-12-11-10--9--8--7-+---+--6--5--4--3--2--1-+
 O (top) to play 61. Cube 1 (centered). money game, Jacoby, beavers.
 Pips: X 101, O 119. Off: X 0, O 0.
 XGID=a-BCB-B-B---bD---bbcbab---:0:0:-1:61:0:0:3:0:10
```

**Your play:** bar/18

**Your reasoning:** My opponent's strategic objective is to unstack his midpoint so he can break contact and race. This play controls my opponent's outfield, making it harder for him to safely unstack his midpoint, and as a secondary benefit is more efficient race-wise than bar/24 with 8/2 or 7/1.

This position is about one checker and twenty numbers. You are eighteen pips behind with a man on the bar, so the race is gone; your wins come from a shot later, when X has to bring four checkers off the midpoint and two off the 8-point past whatever you keep back. The checker that wins that game is the one entering now. bar/18 parks it on X's bar point, where any 6 from the midpoint, any 1 from the 8-point and three combination rolls hit it, two rolls in three, against a four-point board. Hit there, you are dancing against four points while X comes home freely, and your gammon losses nearly double, from about one game in sixteen to one in nine. bar/18 is a huge blunder, costing more than a quarter of a point. Against a four-point board a blot that gets hit two times in three is not an outpost; it is a gift.

The best play is bar/24 8/2. The ace point is as safe as a lone checker gets: X can hit it, but only by leaving a blot on X's own ace point, where your entering 1s hit it back, with your three home points and the block from your 5-point to your 8-point waiting behind; that is a gamble X does not need while winning the race. From there the checker covers X's 5-point and bar point directly and the outfield beyond them indirectly, which is where X's midpoint checkers have to land. The 6 then has to go somewhere, and 8/2 is the least damaging place. It keeps your 5, 6 and 7-points together as a block in front of your board and starts the 2-point, and next turn nearly any roll covers either the 2-point or the 4-point. bar/24 7/1 is an error, costing about a twelfth of a point: it breaks that block to start the ace point, the least useful point to own. bar/24 13/7 fails for a different reason: it breaks your midpoint and leaves a blot that X's own midpoint checkers hit with 1s.

Your reasoning had the right picture of X's plan and the wrong price for interfering with it. Controlling the outfield from the bar point is real, but small, and it costs the whole game when X rolls first. We checked your idea in its best case, with X's board weakened to three points and two midpoint checkers already down as targets in front of your checker: bar/18 is still an error there, about a tenth of a point. Only the weak board moves the number much; the targets hardly do. The race argument does not apply at all. Eighteen pips down, no play with a 6-1 makes you a racing favourite, and the checker you were hurrying is the one that has to stay back. When you are far behind in the race with one checker back, that checker's job is to be safe and patient, and the rest of your army's job is to keep a board for the day the shot comes. The bar point would be the place to be if X's board were two points and X had nowhere to land; then the exchange of hits favours you. It is not the place to be against four points and an 8-point, with two rolls in three hitting.

<details>
<summary>How this was checked</summary>

Rollout: gnubg 1.08.003, 1296 trials (JSD early stop), cubeful, variance reduction, no truncation, seed 20261030.

| Play | Equity | SE | Error | Games |
|---|---|---|---|---|
| bar/24 8/2 | -0.747 | 0.015 | +0.000 (level) | 327 |
| bar/24 7/1 | -0.821 | 0.016 | -0.074 (error) | 327 |
| bar/18 | -1.029 | 0.017 | -0.282 (huge blunder) | 325 |

Candidates at gnubg 2-ply:

- bar/24 8/2: -0.657 (+0.000) 2-ply
- bar/24 7/1: -0.750 (-0.093) 2-ply
- bar/24 13/7: -0.949 (-0.292) 2-ply
- bar/18: -0.959 (-0.302) 2-ply

2 hypothesis(es) and 12 variant(s) recorded in study.json.

</details>
