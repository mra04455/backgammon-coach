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

Start with where the game stands. You are eight pips behind with two back checkers split deep in O's board, facing a block from O's 6-point to the 8-point with three spares on the 6-point waiting to extend it. O has two back checkers split in your board and a home board of one point. So the plans are set: O wants to anchor or escape and then prime you; you want to attack those two loose checkers while you build a board, because your race is lost and your winning chances come from the attack and the gammons it brings. A 5-5 serves that plan handsomely either way. Both plays make your 5-point and your 3-point with a hit, and they differ only in the last 5: XG plays 13/8, bringing a midpoint checker down and keeping the 8-point; you played 6/1*, hitting a second checker loose on your ace point and leaving the 8-point as a single checker. Your play is a blunder, costing about an eighth of a point.

This is a trade, and it is worth seeing both sides of it. The second hit buys real things: O has two men on the bar instead of one and gets both in with only one roll in four; your gammons rise from one game in four to nearly three in ten. It costs real things too: any 1 enters and hits your checker on the ace point, eleven rolls of thirty-six, sending a third checker back; the checker on the ace point is out of play even when it survives; and the 8-point, your best asset for the priming game you asked about, is broken and left as a blot. The engine's verdict is that the structure is worth more than the tempo here, by an eighth of a point, with your wins falling from about five in eight to a little under six in ten while the gammons rise.

What makes the trade go against you is the 8-point rather than the loose hit itself. Give yourself a fourth checker on the 8-point, so that hitting twice no longer breaks it, and the double hit becomes as good as XG's play. Give yourself the 4-point as well as the 6, so that your board is strong enough to make two men on the bar dance, and the two plays are level again. Those are the conditions under which your instinct is right: a blitz wants a board behind it and spares to hit with, and here you have neither yet, so the fourth 5 is better spent building than hitting. O's side of the board turns out not to be the issue. Breaking O's block in front of your back checkers makes the quiet play better still, and strengthening O's home board changes nothing, so the danger of a third checker back is not what decides this; your own structure is.

Your two guesses were both half right. Keeping the 8-point does keep a priming plan alive, but the deeper point is that it keeps the attack alive too: with the 3, 5, 6 and 8-points held and the 4 and 7 to fill, every hit you make later lands against a board that can hold the checker. And the midpoint checker XG brings down is not just a fourth man on the 6-point; it is a builder for the 4-point and a spare that lets you hit next time without breaking anything. The rule this position teaches is that a double hit is a blitz, and a blitz with a two-point board is a loan against structure you have not built. It becomes the right play once the board is there, or once the hit costs no point.

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
