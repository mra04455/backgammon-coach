# gnubg engine reliability: when to trust a shallow evaluation

Sources: gnubg manual source (`doc/gnubg/gnubg.texi`) and C source from the GitHub mirror, the pip `gnubg` 1.1.0a16 wheel (inspected statically), and analyst material via search summaries (bkgm.com, bgonline.org, extremegammon.com and gnu.org were blocked from direct fetch here, so those quotes are second-hand).

## 1. Error of 0/2/3-ply versus rollouts, and weak position types

Measurements (vendor or community, none peer reviewed):

- Backgammon Galaxy: mean absolute equity deviation from long rollouts, millipoints, XG target / gnubg target: gnubg 0-ply 84.8/80.3, 2-ply 52.2/46.7, 4-ply 43.0/36.8. So 0-ply is off by about 0.08 on average, 2-ply about 0.05, 4-ply about 0.04. https://www.backgammongalaxy.com/backgammon-galaxy-engine-analysis
- XG's Depreli-position comparison (decision errors, old gnubg 1.00): 2-ply total equity lost 20.951 (PR 0.58), 3-ply 16.775 (0.46), 4-ply 12.536 (0.35), XG Roller++ 4.097 (0.11). https://www.extremegammon.com/studies.aspx
- Manual: "if you really need better answers than 2 ply, rollouts are probably a lot better." https://www.gnu.org/software/gnubg/manual/html_node/The-depth-to-search-and-plies.html

Known weaknesses:

- Cube efficiency x is a constant per class (contact and crashed 0.68, one-sided bearoff 0.6, race 0.6–0.7 by pips). The manual concedes holding games and backgames "should have a lower cube efficiency" and blitzes higher, so cubeful equities in those types carry systematic bias that no ply depth removes. https://www.gnu.org/software/gnubg/manual/html_node/The-cube-efficiency.html
- Holding games: Ian Shaw found 2-ply "too optimistic for the holding player" in high-anchor holding games; 3-ply closer to rollouts. https://lists.nongnu.org/archive/html/bug-gnubg/2008-02/msg00030.html
- Odd/even ply cube bias: odd-ply cube equities run high, even-ply are closer to rollouts (https://lists.libreplanet.org/archive/html/bug-gnubg/2008-02/msg00037.html); one user saw a pass scored -0.090 to -0.363 across 0–4 ply before a rollout reversed it (take was the -0.069 error). https://www.bgonline.org/forums/webbbs_config.pl?noframes%3Bread=141906
- Backgames/containment: large ply-to-ply swings and net problems reported (https://lists.libreplanet.org/archive/html/bug-gnubg/2004-01/msg00068.html, https://lists.libreplanet.org/archive/html/bug-gnubg/2004-10/msg00010.html); analysts want a full untruncated rollout and a larger move filter there. https://www.bgonline.org/forums/webbbs_config.pl?noframes=&read=191066
- Race-to-bearoff hand-off can distort odd stacks. https://mail.gnu.org/archive/html/bug-gnubg/2020-09/msg00005.html

Classifier (`ClassifyPosition`, eval.c): OVER if a side has no checkers; CONTACT when rear checkers overlap (`nBack + nOppBack > 22`), downgraded to CRASHED when a side has at most 6 checkers not stacked on its ace/deuce points; else RACE, becoming BEAROFF1/BEAROFF2 when the databases apply (two-sided values are exact, cubeful money equity included). https://github.com/mormegil-cz/gnubg/blob/master/eval.c

## 2. Rollout error reporting and settled settings

- gnubg reports each output with a standard error (95% CI = 1.96 SE) and, for multiple candidates, a JSD: the SD of the equity difference between a play and the best play. The pip binding's `hint()` returns `probs-std`, `trials`, `stopped-on-jsd`.
- Defaults (gnubg.c `rcRollout`): 1296 trials, cubeful, variance reduction, rotated first rolls, truncation off (10 plies if on), cube decisions 2-ply, chequer play 0-ply, min 324 games, stop-on-STD when |STD/value| < 0.01, stop-on-JSD at 2.33 JSD (99%); JSD stop overrides STD stop. https://github.com/mormegil-cz/gnubg/blob/master/gnubg.c, https://github.com/mormegil-cz/gnubg/blob/master/rollout.c
- Manual: truncated rollouts "are better for estimating relative equity ... than absolute equity"; VR is automatic with lookahead. https://www.gnu.org/software/gnubg/manual/html_node/Rollouts-in-GNU-Backgammon.html. Reaching STD 0.020 can take 400 trials in one position, 1400 in another. https://www.gnu.org/software/gnubg/manual/allabout.pdf. Common rule: JSD limit 3, never below 2. http://www.backgammonmasters.com/backgammon-rollout-settings-in-gnu-backgammon.shtml
- Analyst practice: XG default 1296 trials, VR, 3-ply checker, XG Roller cube; XG studies run "until 95% CI < 0.005, min 1296". XG Roller++ cube: truncate 7, stop at 0.010 confidence, min 180 games; checker 360 games, truncate 5. https://lists.gnu.org/archive/html/bug-gnubg/2012-08/msg00000.html. "For anything close ... 1296 is not enough. I usually begin at 5184"; overlapping intervals mean more trials. https://www.bgonline.org/forums/webbbs_config.pl?noframes%3Bread=187302. "1296 trials gives SE 0.01" fails for non-simple positions. https://forumserver.twoplustwo.com/138/backgammon-forum-hosted-bill-robertie/rollout-parameters-874817/. Full XG cube rollouts typically show ±0.004. https://timothychow.net/cg/www.bgonline.org/forums/174334.html. Opening rollouts at 46656 trials reach SE < 0.001. https://bkgm.com/openings/rollouts.html
- Cube settledness: a redouble is confirmed when the cost of not doubling exceeds the CI radius. https://lists.gnu.org/archive/html/bug-gnubg/2003-07/msg00093.html. Zare: rollouts can say more about the bot than the position. https://bkgm.com/articles/Zare/Rollouts/

## 3. Cube outputs and the Python API

- gnubg computes three cubeful equities: no double (ND), double/take (DT), double/pass (DP = +1.000 normalised to the current cube). "The cube decision is simply made by comparing equities": Double/Take when ND < DT < 1; Double/Pass when DT >= 1 and ND < 1; Too good when ND >= 1; No double when ND >= DT. Deltas shown are differences from the best action; the bluff % is the pass rate that would justify a wrong double. https://www.gnu.org/software/gnubg/manual/html_node/Cube-decisions.html, https://www.gnu.org/software/gnubg/manual/html_node/Getting-cube-decision-hints-while-playing.html
- Janowski arithmetic: E(cubeful) = E(dead)(1-x) + E(live)x; take point TP = (L-0.5)/(W+L+0.5x), W and L the average cubeless value of won and lost games including gammons; x=0 gives the dead-cube 25% gammonless TP, x=1 the live 20%; cash point = 1 - opponent's TP. Match play recurses TP(live,n) = TP(dead,n)(1 - TP(live,2n)). https://www.bkgm.com/articles/Janowski/cubeformulae.pdf, https://www.gnu.org/software/gnubg/manual/html_node/Live-cube-equities.html
- pip `gnubg` 1.1.0a16: `evaluate([board],[cubeinfo],[evalcontext])` returns (win, wg, wbg, lg, lbg, equity), cubeful iff the evalcontext is; `evalcontext([cubeful, plies, deterministic, prune, noise])`; `cubeinfo([cube, owner, player, matchlen, score, crawford, bgv])`; `findbestmoves` returns `[{"move","score"}]`; `setgnubgid` accepts GNUbgID or XGID; `rolloutcontext` builds a dict; `classify`. No `rollout()` and no cube helper (upstream `cfevaluate` was not ported): cube decisions mean calling `evaluate` under the relevant cubeinfos, and rollouts run only via `command("set rollout ...")`/`command("rollout")` on the current position, read back with `hint()` (type "rollout" entries) or `match(analysis=1)`. The separate `gnubg-nn` package has `rollout()`/`cubeful_rollout()` but wraps the older engine. https://github.com/StonesAndDice/gnubg-pypi/blob/main/src/gnubgmodule/gnubgmodule.cpp, https://pypi.org/project/gnubg/, https://gnubg.readthedocs.io/en/latest/api.html

## 4. Meaningful differences

- gnubg `arSkillLevel` defaults: doubtful 0.04, bad 0.08, very bad 0.16; a 2019 proposal would lower to 0.03/0.06/0.12. https://lists.libreplanet.org/archive/html/bug-gnubg/2019-01/msg00000.html
- XG: error > 0.020 (0.015 at DMP), blunder > 0.080 (0.053). https://www.extremegammon.com/Exported%20Games/Match2/legend.htm
- Woolsey tolerates .01–.02 and targets .10 "whoppers". https://bkgm.com/articles/GOL/Sep03/burger.htm. Pals treats ±0.01 as too close to call and rolled out anything within 0.03. https://nebackgammon.org/wp-content/uploads/2025/08/RandyPalsRollouts_ModernBG.pdf
- Inside noise: at SE .002, gaps over .002 are "probably ordered correctly" (https://bkgm.com/openings/replyrollouts.html); a .006 gap at SD .003 after 12,960 trials was still borderline (https://bkgm.com/articles/GOL/Mar00/jakevar.htm).

## Recommendations: escalate when the conclusion is not safe under the error band

1. Give each depth an absolute band and never report a shift narrower than it: 0-ply ±0.08, 2-ply ±0.05, 3/4-ply ±0.04 (Galaxy MADs). Shallow plies rank and screen; a variation's equity shift is reportable only above the band or after rollout.
2. Checker play: top two within 0.02 at 2-ply (XG error line, Woolsey's tolerance) triggers 3-ply; still within 0.02 triggers a rollout with gnubg defaults (1296, cubeful, VR, JSD stop 2.33). Call "too close to call" under 0.01 or under 2 JSD; label a lesson only above 0.04 (gnubg doubtful) after rollout.
3. Cube: evaluate at even ply only (2-ply cubeful); if |ND - DT| < 0.05 or |DT - 1| < 0.05, roll out cubeful. Settled when both margins exceed 2 SE (about 0.004–0.01 at 1296–5184 trials); otherwise extend to 5184 or run until 95% CI < 0.005.
4. By class: trust 2-ply for RACE/BEAROFF (exact databases); for CONTACT/CRASHED with holding, backgame, containment or blitz features skip 3-ply and go straight to a full untruncated rollout with a larger move filter, because the fixed x = 0.68 and holding-game optimism are systematic.
5. For sibling variations, compare under identical settings and seed so systematic bias cancels (the manual's relative-vs-absolute point); truncated rollouts suffice for ranking, but escalate to full rollouts when a variation changes class or crosses an ND/DT or DT/DP boundary.
6. Store depth, trials, SE/JSD and class with every equity and show the band: below band is noise, 0.02–0.08 an error-size shift, above 0.08 blunder-size.
