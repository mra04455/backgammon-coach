# Study: XGID=-b----E-C---eE---c-e----B-:0:0:1:31:0:0:0:0:10

```
 +-13-14-15-16-17-18-+---+-19-20-21-22-23-24-+
 | X           O     |   | O              X  |
 | X           O     |   | O              X  |
 | X           O     |   | O                 |
 | X                 |   | O                 |
 | X                 |   | O                 |
 |                   |BAR|                   |
 | O                 |   | X                 |
 | O                 |   | X                 |
 | O           X     |   | X                 |
 | O           X     |   | X              O  |
 | O           X     |   | X              O  |
 +-12-11-10--9--8--7-+---+--6--5--4--3--2--1-+
 X (bottom) to play 31. Cube 1 (centered). money game.
 Pips: X 167, O 167. Off: X 0, O 0.
 XGID=-b----E-C---eE---c-e----B-:0:0:1:31:0:0:0:0:10
```

**Your play:** 13/9

**Your reasoning:** I wanted a builder aimed at the 5-point and did not want to break the 8-point.

_Account not written yet._

<details>
<summary>How this was checked</summary>

Rollout: gnubg 1.08.003, 1296 trials (JSD early stop), cubeful, variance reduction, no truncation, seed 20261029.

| Play | Equity | SE | Error | Games |
|---|---|---|---|---|
| 8/5 6/5 | +0.225 | 0.017 | +0.000 (level) | 327 |
| 24/23 13/10 | -0.003 | 0.021 | -0.228 (huge blunder) | 326 |
| 13/9 | -0.053 | 0.022 | -0.278 (huge blunder) | 325 |

Candidates at gnubg 2-ply:

- 8/5 6/5: +0.219 (+0.000) 2-ply
- 24/23 13/10: -0.010 (-0.229) 2-ply
- 13/9: -0.025 (-0.243) 2-ply
- 24/20: -0.025 (-0.244) 2-ply
- 13/10 6/5: -0.028 (-0.247) 2-ply
- 24/23 24/21: -0.040 (-0.259) 2-ply
- 24/21 6/5: -0.048 (-0.267) 2-ply
- 24/23 8/5: -0.099 (-0.318) 2-ply
- 24/23 6/3: -0.110 (-0.329) 0-ply
- 24/21 8/7: -0.111 (-0.330) 0-ply

</details>
