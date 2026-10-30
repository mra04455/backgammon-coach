# Study: XGID=bBABBBB-A-A-bB---bbcb-b---:1:-1:1:11:5:14:3:0:10

```
 +-13-14-15-16-17-18-+---+-19-20-21-22-23-24-+
 | X           O  O  | O | O  O     O        |
 | X           O  O  | O | O  O     O        |
 |                   |   | O                 |
 |                   |   |                   |
 |                   |   |                   |
 |                   |BAR|                   |
 |                   |   |                   |
 |                   |   |                   |
 |                   |   |                   |
 | O                 |   | X  X  X  X     X  |
 | O     X     X     |   | X  X  X  X  X  X  |
 +-12-11-10--9--8--7-+---+--6--5--4--3--2--1-+
 X (bottom) to play 11. Cube 2 (owned by O). money game, Jacoby, beavers.
 Pips: X 84, O 140. Off: X 0, O 0.
 XGID=bBABBBB-A-A-bB---bbcb-b---:1:-1:1:11:5:14:3:0:10
```

**Your play:** 10/6

**Your reasoning:** I'm ahead in the race and have great winning chances if I can bring checkers in efficiently; 10/6 wastes no pips. I don't think getting hit is a huge risk since I have a stronger board and lots of return shots. If I get hit and hit a return shot I have great gammon chances, so I think the risk of leaving a shot is worth the benefit of closing him out.

This position is about the blot on your 2-point. O has two checkers on the bar and you hold five points, so the only question the 1-1 has to answer is which point O gets to enter on, and whether there is anything to hit when O does. 10/6 leaves the 2-point open with your blot still on it, so every 2 enters and hits, eleven rolls of thirty-six. Being hit there does not cost you gammons, which stay at about seven games in ten whatever you play, because when the hit does not come you close O out either way. It costs you whole games: the hit checker loses twenty-three pips and O's checker gains a foothold in your board, and about one game in twenty-five that you would otherwise win turns into a loss. With O holding a 2-cube that is a blunder, costing about a tenth of a point.

The best play is 5/2 5/4: cover the 2-point and leave the 5-point open instead. Now O enters only with 5s, lands on an empty point with nothing to hit there (only 5-5 enters and runs on to your blot on the 10-point), and sits directly under your checkers on the 8- and 10-points, which cover the 5-point with 3s and 5s. Opening the 4-point instead, with 8/7 4/2 4/3, is almost as good, a small error of a few hundredths. The lesson is in the shape of these plays rather than the choice between them: every good play here covers the slot. Which high point you open is a detail; a blot in your board with two men on the bar is not.

Your reasoning rested on three premises, and the one that is true does not carry the decision. Your board is stronger than O's: five points against three, so a hit checker of yours enters three rolls in four. But that is not where the cost of the hit lies. We took away O's 7- and 8-points, the block in front of O's board, and 10/6 cost the same tenth of a point, because what the hit costs is the pips and the foothold, not the trouble getting back in. Only when O's block grows into a full six-point prime from the 3-point to the 8-point does the picture change, and the other way: then 10/6 would cost about half a point. Pips are not the issue: you lead the race by fifty-six, and no play with a 1-1 changes whether you win the race, only whether you keep a checker out of trouble while you close the board. The third premise, that return shots make the hit cheap, is half right. You do have many return shots, but a return hit only puts you back where you started, with O's second checker meanwhile entering, and the games you lose are the ones where that exchange goes wrong. When your opponent has men on the bar and you have a loose checker in your board, cover it first and economise pips later. The rule would bend only if covering cost you a point you cannot spare, or if the entering checker could not hit, and neither is true here: three different covers were available and all of them beat the slot.

<details>
<summary>How this was checked</summary>

Rollout: gnubg 1.08.003, 1296 trials (JSD early stop), cubeful, variance reduction, no truncation, seed 20261030.

| Play | Equity | SE | Error | Games |
|---|---|---|---|---|
| 5/2 5/4 | +1.429 | 0.009 | +0.000 (level) | 327 |
| 8/7 4/2 4/3 | +1.398 | 0.010 | -0.031 (small error) | 327 |
| 10/6 | +1.326 | 0.011 | -0.103 (blunder) | 326 |

Candidates at gnubg 2-ply:

- 5/2 5/4: +1.450 (+0.000) 2-ply
- 8/7 4/2 4/3: +1.429 (-0.021) 2-ply
- 10/9 4/2 4/3: +1.403 (-0.047) 2-ply
- 10/9 8/7 3/2(2): +1.394 (-0.056) 2-ply
- 4/2(2): +1.381 (-0.069) 2-ply
- 8/6 3/2(2): +1.377 (-0.073) 2-ply
- 10/8 3/2(2): +1.367 (-0.084) 2-ply
- 10/9 3/1 3/2: +1.355 (-0.095) 2-ply
- 10/7 2/1: +1.346 (-0.104) 2-ply
- 10/9 8/6 2/1: +1.340 (-0.110) 2-ply
- 8/5 2/1: +1.335 (-0.115) 2-ply
- 8/7 3/1 3/2: +1.328 (-0.122) 2-ply
- 10/6: +1.288 (-0.162) 0-ply
- 6/2: +1.282 (-0.169) 0-ply
- 10/9 8/6 3/2: +1.273 (-0.177) 0-ply
- 10/7 3/2: +1.271 (-0.179) 0-ply
- 10/7 8/7: +1.271 (-0.179) 0-ply
- 10/9 5/2: +1.264 (-0.187) 0-ply
- 8/7 5/2: +1.262 (-0.188) 0-ply
- 8/6 4/2: +1.254 (-0.196) 0-ply
- 10/9 8/5: +1.252 (-0.198) 0-ply
- 10/9 8/7 4/2: +1.239 (-0.211) 0-ply
- 8/4: +1.228 (-0.222) 0-ply
- 8/5 3/2: +1.219 (-0.231) 0-ply
- 10/8 4/2: +1.215 (-0.235) 0-ply
- 6/4 6/5 2/1: +1.070 (-0.380) 0-ply
- 10/9 6/5(2) 2/1: +1.050 (-0.400) 0-ply
- 6/5(2) 3/2(2): +1.045 (-0.406) 0-ply
- 8/7 6/5(2) 2/1: +1.037 (-0.414) 0-ply
- 5/3 5/4 2/1: +1.008 (-0.442) 0-ply
- 10/9 5/4(2) 2/1: +0.992 (-0.458) 0-ply
- 8/7 5/4(2) 2/1: +0.991 (-0.460) 0-ply
- 5/4(2) 3/2(2): +0.966 (-0.484) 0-ply
- 10/8 6/5(2): +0.901 (-0.549) 0-ply
- 10/9 6/4 6/5: +0.888 (-0.562) 0-ply
- 8/7 6/4 6/5: +0.879 (-0.571) 0-ply
- 6/4 6/5 3/2: +0.873 (-0.577) 0-ply
- 10/9 4/3(2) 2/1: +0.869 (-0.581) 0-ply
- 8/7 4/3(2) 2/1: +0.867 (-0.583) 0-ply
- 6/3 6/5: +0.851 (-0.599) 0-ply
- 10/9 8/7 6/5(2): +0.849 (-0.601) 0-ply
- 10/8 5/4(2): +0.842 (-0.608) 0-ply
- 10/9 6/5(2) 3/2: +0.841 (-0.609) 0-ply
- 10/9 6/5 3/2(2): +0.836 (-0.614) 0-ply
- 6/5 4/2 4/3: +0.823 (-0.627) 0-ply
- 8/7 6/5(2) 3/2: +0.823 (-0.628) 0-ply
- 10/8 6/5 2/1: +0.818 (-0.632) 0-ply
- 8/7 6/5 3/2(2): +0.812 (-0.638) 0-ply
- 10/9 5/3 5/4: +0.809 (-0.641) 0-ply
- 8/6 5/4(2): +0.809 (-0.641) 0-ply
- 8/7 5/3 5/4: +0.806 (-0.644) 0-ply
- 10/9 8/7 6/5 2/1: +0.806 (-0.644) 0-ply
- 10/9 8/7 5/4(2): +0.780 (-0.670) 0-ply
- 6/5(2) 4/2: +0.777 (-0.673) 0-ply
- 6/4 3/2(2): +0.776 (-0.674) 0-ply
- 6/4(2): +0.771 (-0.679) 0-ply
- 10/9 6/4 2/1: +0.770 (-0.680) 0-ply
- 10/9 5/4(2) 3/2: +0.770 (-0.680) 0-ply
- 8/6 5/4 2/1: +0.766 (-0.684) 0-ply
- 10/8 5/4 2/1: +0.759 (-0.691) 0-ply
- 8/7 6/4 2/1: +0.758 (-0.692) 0-ply
- 10/9 5/4 3/2(2): +0.757 (-0.693) 0-ply
- 10/8 4/3(2): +0.757 (-0.693) 0-ply
- 8/7 5/4(2) 3/2: +0.756 (-0.694) 0-ply
- 6/5 3/1 3/2: +0.750 (-0.700) 0-ply
- 10/9 8/7 5/4 2/1: +0.746 (-0.704) 0-ply
- 8/7 5/4 3/2(2): +0.735 (-0.715) 0-ply
- 6/3 2/1: +0.725 (-0.725) 0-ply
- 10/8 4/3 2/1: +0.724 (-0.726) 0-ply
- 8/6 4/3(2): +0.723 (-0.727) 0-ply
- 10/9 5/3 2/1: +0.716 (-0.735) 0-ply
- 8/6 4/3 2/1: +0.708 (-0.742) 0-ply
- 8/7 5/3 2/1: +0.703 (-0.748) 0-ply
- 5/4 3/1 3/2: +0.684 (-0.767) 0-ply
- 10/9 8/7 4/3 2/1: +0.678 (-0.772) 0-ply
- 10/9 8/7 4/3(2): +0.677 (-0.773) 0-ply
- 5/3(2): +0.676 (-0.774) 0-ply
- 10/8 6/5 3/2: +0.661 (-0.789) 0-ply
- 4/1 4/3: +0.637 (-0.813) 0-ply
- 10/9 8/7 6/5 3/2: +0.627 (-0.823) 0-ply
- 10/7 6/5: +0.625 (-0.825) 0-ply
- 10/8 6/4: +0.617 (-0.833) 0-ply
- 10/9 8/6 5/4: +0.609 (-0.841) 0-ply
- 10/8 5/3: +0.606 (-0.844) 0-ply
- 8/6 5/4 3/2: +0.585 (-0.865) 0-ply
- 10/8 5/4 3/2: +0.585 (-0.865) 0-ply
- 10/9 8/6 4/3: +0.583 (-0.867) 0-ply
- 10/9 6/4 3/2: +0.580 (-0.870) 0-ply
- 8/6 5/3: +0.572 (-0.878) 0-ply
- 10/9 6/5 4/2: +0.569 (-0.881) 0-ply
- 10/7 5/4: +0.562 (-0.888) 0-ply
- 10/9 8/7 6/4: +0.559 (-0.891) 0-ply
- 8/7 6/5 4/2: +0.557 (-0.893) 0-ply
- 8/7 6/4 3/2: +0.557 (-0.893) 0-ply
- 8/5 4/3: +0.554 (-0.896) 0-ply
- 10/9 8/7 5/4 3/2: +0.551 (-0.899) 0-ply
- 10/7 4/3: +0.545 (-0.905) 0-ply
- 10/9 6/3: +0.539 (-0.911) 0-ply
- 4/2 3/2(2): +0.539 (-0.912) 0-ply
- 10/9 8/7 5/3: +0.526 (-0.924) 0-ply
- 10/8 3/1: +0.520 (-0.930) 0-ply
- 8/7 6/3: +0.519 (-0.931) 0-ply
- 8/5 6/5: +0.499 (-0.952) 0-ply
- 10/9 3/1 2/1: +0.487 (-0.963) 0-ply
- 4/1 2/1: +0.470 (-0.980) 0-ply
- 8/7 3/1 2/1: +0.460 (-0.990) 0-ply
- 10/9 4/2 3/2: +0.456 (-0.994) 0-ply
- 8/6 3/1: +0.447 (-1.003) 0-ply
- 3/1(2): +0.431 (-1.020) 0-ply
- 5/2 4/3: +0.426 (-1.024) 0-ply
- 10/9 8/7 3/1: +0.423 (-1.027) 0-ply
- 8/7 4/2 3/2: +0.417 (-1.033) 0-ply
- 5/2 3/2: +0.413 (-1.037) 0-ply
- 10/9 4/1: +0.377 (-1.073) 0-ply
- 5/1: +0.372 (-1.078) 0-ply
- 4/1 3/2: +0.370 (-1.080) 0-ply
- 8/7 4/1: +0.360 (-1.090) 0-ply
- 6/5(2) 4/3(2): +0.257 (-1.193) 0-ply
- 6/5 4/3(2) 2/1: +0.243 (-1.207) 0-ply
- 6/5(2) 4/3 2/1: +0.240 (-1.210) 0-ply
- 10/9 6/5(2) 4/3: -0.003 (-1.453) 0-ply
- 8/7 6/5(2) 4/3: -0.022 (-1.472) 0-ply
- 10/9 6/5 4/3(2): -0.023 (-1.473) 0-ply
- 10/9 6/5 4/3 2/1: -0.024 (-1.474) 0-ply
- 8/7 6/5 4/3(2): -0.037 (-1.487) 0-ply
- 8/7 6/5 4/3 2/1: -0.041 (-1.491) 0-ply
- 6/5(2) 3/1: -0.106 (-1.556) 0-ply
- 5/4(2) 3/1: -0.146 (-1.596) 0-ply
- 6/4 5/4 2/1: -0.172 (-1.622) 0-ply
- 10/8 6/5 4/3: -0.190 (-1.640) 0-ply
- 6/5 3/1 2/1: -0.206 (-1.657) 0-ply
- 6/4 5/4(2): -0.215 (-1.665) 0-ply
- 5/4 3/1 2/1: -0.222 (-1.672) 0-ply
- 5/3 4/3 2/1: -0.242 (-1.692) 0-ply
- 5/3 4/3(2): -0.285 (-1.735) 0-ply
- 10/9 8/7 6/5 4/3: -0.321 (-1.772) 0-ply
- 10/9 6/5 3/1: -0.415 (-1.865) 0-ply
- 6/5 4/2 3/2: -0.425 (-1.875) 0-ply
- 10/9 5/4 3/1: -0.428 (-1.878) 0-ply
- 6/5 4/1: -0.452 (-1.902) 0-ply
- 8/7 6/5 3/1: -0.463 (-1.913) 0-ply
- 6/3 5/4: -0.470 (-1.920) 0-ply
- 8/7 5/4 3/1: -0.477 (-1.928) 0-ply
- 10/9 6/4 5/4: -0.486 (-1.936) 0-ply
- 6/4 3/1: -0.487 (-1.937) 0-ply
- 6/4 5/4 3/2: -0.500 (-1.950) 0-ply
- 8/7 6/4 5/4: -0.509 (-1.959) 0-ply
- 6/3 4/3: -0.511 (-1.961) 0-ply
- 10/9 5/3 4/3: -0.520 (-1.970) 0-ply
- 8/7 5/3 4/3: -0.546 (-1.997) 0-ply

2 hypothesis(es) and 3 variant(s) recorded in study.json.

</details>
