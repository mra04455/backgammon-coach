# Study: XGID=-a-a-AD-C-A-cD---cbe--A-A-:0:0:1:55:9:23:3:0:10

```
 +-13-14-15-16-17-18-+---+-19-20-21-22-23-24-+
 | X           O  O  |   | O        X     X  |
 | X           O  O  |   | O                 |
 | X           O     |   | O                 |
 | X                 |   | O                 |
 |                   |   | O                 |
 |                   |BAR|                   |
 |                   |   |                   |
 |                   |   | X                 |
 | O           X     |   | X                 |
 | O           X     |   | X                 |
 | O     X     X     |   | X  X     O     O  |
 +-12-11-10--9--8--7-+---+--6--5--4--3--2--1-+
 X (bottom) to play 55. Cube 1 (centered). money game, Jacoby, beavers.
 Pips: X 161, O 153. Off: X 0, O 0.
 XGID=-a-a-AD-C-A-cD---cbe--A-A-:0:0:1:55:9:23:3:0:10
```

**Your play:** 10/5 8/3*(2) 6/1*

**Your reasoning:** I really have no idea why this was wrong. XG's play keeps the 8-point and doesn't leave a shot at the cost of hitting only once. Maybe the idea is to keep a priming game plan available? Or bring an extra builder into the zone, even though it's just a fourth checker on the six-point?

The race is close to even: you trail by eight before this roll and lead by twelve after it, with O to roll. What is not even is the position. O has two loose checkers in your board and a one-point home board; you have two back checkers split behind O's block from the 6-point to the 8-point, with three spares on O's 6-point ready to extend it. Both sides are in a fight for position, and the 5-5 is a fine roll for it: either way you make your 5-point and your 3-point with a hit, and the only question is the last 5. XG plays 13/8; you played 6/1*. The difference costs about an eighth of a point, a blunder.

The second hit is tempting, and it is not nothing: two men on the bar instead of one, both in with only one roll in four, and your gammons up from a quarter of the games to nearly three in ten. But look at what you have left to follow it up with. Your board is three points. Any 1 enters and hits the checker you left on the ace point, eleven rolls of thirty-six, and then you have a third checker back behind a block that O is about to extend. The 8-point is gone, left as a single checker, and your last spare on the 6-point went with it. You have hit twice and have nothing to hit with next.

That is the idea to take away. A double hit is a blitz, and a blitz needs two things behind it: a board that makes the men you hit dance, and spares to keep hitting and to cover with. With the 3, 5, 6 and 8-points held and the 4-point and bar point still to fill, 13/8 keeps both: the next hit lands against a board that can hold it, and the checker you bring down is a builder for the 4-point and a spare you can hit with later without breaking anything. If your 8-point were already safe, or your board one point stronger, the second hit would be right; here the structure is worth more than the tempo, by an eighth of a point, with your wins at roughly five in eight against a little under six in ten.

Your two guesses were both on the right track. Keeping the 8-point does keep a priming plan alive, but the deeper point is that it keeps the attack alive too, because it is the hits you make later that win this game, and they need something to land against. The checker XG brings down is not just a fourth man heading for the 6-point; it is the ammunition for the next turn. The rule is that hitting a second checker is only worth a point of your own when your board can already hold two, and here it cannot yet.

<details>
<summary>How this was checked</summary>

Rollout: gnubg 1.08.003, 1296 trials (JSD early stop), cubeful, variance reduction, no truncation, seed 20261104.

| Play | Equity | SE | Error | Games |
|---|---|---|---|---|
| 13/3* 10/5 8/3 | +0.611 | 0.025 | +0.000 (level) | 327 |
| 10/5 8/3*(2) 6/1* | +0.494 | 0.025 | -0.117 (blunder) | 324 |

Candidates at gnubg 2-ply:

- 13/3* 10/5 8/3: +0.619 (+0.000) 2-ply
- 10/5 8/3*(2) 6/1*: +0.518 (-0.101) 2-ply
- 10/5 8/3* 6/1*(2): +0.387 (-0.232) 2-ply
- 10/5 8/3*(3): +0.363 (-0.256) 2-ply
- 8/3*(2) 6/1*(2): +0.357 (-0.261) 2-ply
- 13/8 10/5 6/1*(2): +0.250 (-0.369) 2-ply
- 13/3* 10/5 6/1*: +0.170 (-0.449) 2-ply
- 13/3* 13/8 10/5: +0.167 (-0.451) 2-ply
- 13/3* 8/3 6/1*: +0.082 (-0.537) 0-ply
- 13/8(2) 10/5 6/1*: +0.053 (-0.565) 0-ply
- 13/3*(2): +0.011 (-0.607) 0-ply
- 13/3* 6/1*(2): -0.047 (-0.666) 0-ply
- 13/8(3) 10/5: -0.141 (-0.760) 0-ply
- 8/3*(3) 6/1*: -0.155 (-0.774) 0-ply
- 13/3* 8/3(2): -0.222 (-0.841) 0-ply
- 13/8(2) 6/1*(2): -0.229 (-0.848) 0-ply
- 13/3* 13/8 6/1*: -0.269 (-0.887) 0-ply
- 13/3* 13/8(2): -0.508 (-1.127) 0-ply
- 10/5 6/1*(3): -0.567 (-1.185) 0-ply
- 13/8(4): -0.612 (-1.231) 0-ply
- 13/8(3) 6/1*: -0.631 (-1.250) 0-ply
- 13/8 6/1*(3): -1.000 (-1.619) 0-ply
- 8/3* 6/1*(3): -1.000 (-1.619) 0-ply
- 6/1*(4): -1.000 (-1.619) 0-ply

1 hypothesis(es) and 6 variant(s) recorded in study.json.

</details>
