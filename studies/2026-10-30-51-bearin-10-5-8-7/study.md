# Study: XGID=-a-B-CCBA-AAb---bbbcBa-b--:0:0:1:51:0:0:3:0:10

```
 +-13-14-15-16-17-18-+---+-19-20-21-22-23-24-+
 |          O  O  O  |   | O  X  O     O     |
 |          O  O  O  |   | O  X        O     |
 |                   |   | O                 |
 |                   |   |                   |
 |                   |   |                   |
 |                   |BAR|                   |
 |                   |   |                   |
 |                   |   |                   |
 |                   |   | X  X              |
 | O              X  |   | X  X     X        |
 | O  X  X     X  X  |   | X  X     X     O  |
 +-12-11-10--9--8--7-+---+--6--5--4--3--2--1-+
 X (bottom) to play 51. Cube 1 (centered). money game, Jacoby, beavers.
 Pips: X 122, O 124. Off: X 0, O 0.
 XGID=-a-B-CCBA-AAb---bbbcBa-b--:0:0:1:51:0:0:3:0:10
```

**Your play:** 10/5 8/7

**Your reasoning:** I wanted to bring a checker home efficiently and minimize shots

This position is about the 4-point. O's last checker sits on your ace point, and you already hold the 3, 5, 6 and 7-points. Make the 4-point and you have a five-point block that all but traps that checker: the only way out is a 1 followed by a 6, and meanwhile you are closing out, winning gammons and cashing the cube. Everything about this 5-1 should serve that goal, and the checker that serves it best is the one on your 10-point, which makes the 4-point with any 6. 10/5 8/7 spends that checker on a fourth man on the 5-point, where it only makes the 4-point with 1s. It is a blunder, costing about an eighth of a point. The right plays keep the 10-point checker in the fight.

The best play is 11/6 8/7. The spare it adds to the 6-point makes the 4-point with 2s, the spare already on the 7-point makes it with 3s, and the 10-point checker makes it with 6s, so about two rolls in five make the 4-point next turn, against one in four after your play. The price is a blot on the 10-point that O hits with 6-3, about one roll in twenty, and with a weak two-point board facing your 20-point anchor the hit costs you little even when it lands.

11/10 8/3 is just as good, and it is the play your instinct was reaching for. It makes the 10-point, leaves no blot anywhere, keeps two checkers aimed at the 4-point with 6s, and the point itself blocks the escaping checker's 9s. It makes the 4-point about as often as 11/6 8/7 does, though more of its ways to do so give up another point, and it takes no risk at all and gets a useful outfield point for free. The two plays are level; pick by temperament.

Your reasoning weighted the wrong feature. Minimising shots was not a bad instinct, but it was already free: your blot on the 11-point cannot be hit, and 11/10 8/3 is safer still. What your play gave up was not safety but purpose. A fourth checker on the 5-point is the least useful checker on the board, and the 10-point checker it came from was your best builder. Efficiency in a bear-in means bringing checkers to where they do work, not to where they are safe. The lesson travels: when the opponent has one checker left behind a four-point block, the next point matters more than a shot or two, as long as the hit is cheap. That rule stops working when the opponent's board is strong, because then a hit turns into a lost game rather than a delay, and when you have no anchor to fall back on.

<details>
<summary>How this was checked</summary>

Rollout: gnubg 1.08.003, 5184 trials (JSD early stop), cubeful, variance reduction, no truncation, seed 20261030.

| Play | Equity | SE | Error | Games |
|---|---|---|---|---|
| 11/6 8/7 | +0.604 | 0.005 | +0.000 (level) | 5184 |
| 11/10 8/3 | +0.594 | 0.005 | -0.010 (level) | 5184 |
| 10/5 8/7 | +0.480 | 0.019 | -0.124 (blunder) | 325 |

The top two plays are inside the rollout's noise band.

1 earlier rollout(s) were extended because the decision was close; they are kept in study.json.

Candidates at gnubg 2-ply:

- 11/6 8/7: +0.598 (+0.000) 2-ply
- 11/10 8/3: +0.571 (-0.027) 2-ply
- 11/5: +0.565 (-0.033) 2-ply
- 11/6 10/9: +0.556 (-0.042) 2-ply
- 10/4: +0.491 (-0.107) 2-ply
- 11/6 5/4: +0.466 (-0.132) 2-ply
- 10/5 8/7: +0.458 (-0.140) 2-ply
- 10/9 8/3: +0.441 (-0.157) 2-ply
- 11/10 6/1*: +0.410 (-0.188) 2-ply
- 8/3 6/5: +0.320 (-0.278) 2-ply

2 hypothesis(es) and 7 variant(s) recorded in study.json.

</details>
