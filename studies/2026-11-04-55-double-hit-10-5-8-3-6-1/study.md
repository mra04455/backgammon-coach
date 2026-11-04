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

_Account not written yet._

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

</details>
