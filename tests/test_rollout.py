"""Rollout driver and parser tests.

Parser tests run against output captured from gnubg 1.08.003 (built by
scripts/build-gnubg.sh). The live tests use 36 trials so they finish in
seconds; they are skipped when gnubg is absent.
"""

from pathlib import Path

import pytest

from bgcoach.engines.gnubg import (
    GnubgEngine,
    MoveFilter,
    RolloutSettings,
    canonical_move,
    find_gnubg,
    move_for_command,
    parse_checker_hint,
    parse_cube_hint,
    parse_cube_rollout,
    parse_version,
)
from bgcoach.position import parse_xgid

FIX = Path(__file__).parent / "fixtures"
OPENING_31 = "XGID=-b----E-C---eE---c-e----B-:0:0:1:31:0:0:0:0:10"
OPENING_CUBE = "XGID=-b----E-C---eE---c-e----B-:0:0:1:00:0:0:0:0:10"


def test_parse_rollout_moves_full_1296():
    text = (FIX / "rollout_checker_money_1296.txt").read_text()
    moves = parse_checker_hint(text)
    rolled = [m for m in moves if m.ply == "rollout"]
    assert [m.move for m in rolled] == ["8/5 6/5", "24/23 13/10"]
    best, second = rolled
    assert best.equity == pytest.approx(0.246)
    assert best.se == pytest.approx(0.011)
    assert best.trials == 1296
    assert best.cubeless_equity == pytest.approx(0.163)
    assert best.probs is not None and best.probs.win == pytest.approx(0.553)
    assert second.error == pytest.approx(-0.234)
    assert second.se == pytest.approx(0.011)
    # The un-rolled moves in the same list keep their evaluation labels.
    others = [m for m in moves if m.ply != "rollout"]
    assert others and all(m.se is None and m.trials is None for m in others)
    assert parse_version(text) == "1.08.003"


def test_parse_rollout_moves_jsd_stopped_early():
    moves = parse_checker_hint((FIX / "rollout_checker_money_jsd.txt").read_text())
    rolled = [m for m in moves if m.ply == "rollout"]
    assert len(rolled) == 2
    # JSD stop ended the rollout well short of the 324-trial cap.
    assert rolled[0].trials == 39 and rolled[1].trials == 38
    assert rolled[0].se == pytest.approx(0.065)


def test_parse_cube_rollout():
    text = (FIX / "rollout_cube_money_jsd.txt").read_text()
    cube = parse_cube_rollout(text)
    assert cube is not None
    assert cube.ply == "rollout"
    assert cube.no_double == pytest.approx(0.067)
    assert cube.double_take == pytest.approx(-0.240)
    assert cube.double_pass == pytest.approx(1.0)
    assert cube.proper_action.startswith("No double, take")
    assert cube.best_cube_action == "no double"
    assert cube.take_decision == "take"
    assert cube.cubeless_equity == pytest.approx(0.068)
    assert cube.trials == 38
    assert cube.se_no_double is not None and cube.se_double_take is not None
    # Probabilities come from the no-double (centred cube) rollout.
    assert cube.probs is not None and 0.4 < cube.probs.win < 0.6


def test_parse_cube_rollout_beaver_wording():
    cube = parse_cube_rollout((FIX / "rollout_cube_money_beavers_36.txt").read_text())
    assert cube is not None
    assert cube.proper_action.startswith("No double, beaver")
    assert cube.best_cube_action == "no double"
    assert cube.se_no_double == pytest.approx(0.051)
    assert cube.se_double_take == pytest.approx(0.061)
    assert cube.trials == 36


def test_cube_rollout_parser_rejects_plain_hint():
    assert parse_cube_rollout((FIX / "cube_2ply_match.txt").read_text()) is None
    # And the plain parser still reads the rollout block (ply label aside).
    plain = parse_cube_hint((FIX / "rollout_cube_money_jsd.txt").read_text())
    assert plain is not None and plain.ply == "Rollout"


def test_hint_parser_unchanged_for_evaluations():
    moves = parse_checker_hint((FIX / "checker_2ply_money.txt").read_text())
    assert moves[0].ply == "2-ply" and moves[0].se is None and moves[0].trials is None


def test_canonical_move():
    assert canonical_move("8/5 6/5") == canonical_move("6/5 8/5")
    assert canonical_move("8/5(2)") == canonical_move("8/5 8/5")
    assert canonical_move("13/7* 7/5") == canonical_move("13/7 7/5")
    assert canonical_move("Bar/20") == canonical_move("bar/20")
    assert canonical_move("24/23 13/10") != canonical_move("24/21 13/11")
    assert move_for_command("13/7* 8/5(2)") == "13/7 8/5 8/5"


def test_rollout_settings_commands():
    rs = RolloutSettings(trials=36, seed=7, truncation=None, jsd_stop=True)
    cmds = rs.commands()
    assert "set rollout trials 36" in cmds
    assert "set rollout jsd stop on" in cmds
    # Minimum games never exceed the trial count.
    assert "set rollout jsd minimumgames 36" in cmds
    assert "set rollout truncation enable off" in cmds
    assert "set rollout seed 7" in cmds
    assert "set rollout limit enable off" in cmds
    trunc = RolloutSettings(truncation=7, jsd_stop=False).commands()
    assert "set rollout truncation enable on" in trunc
    assert "set rollout truncation plies 7" in trunc
    assert "set rollout jsd stop off" in trunc
    assert not any(c.startswith("set rollout jsd limit") for c in trunc)
    with pytest.raises(ValueError):
        RolloutSettings(trials=0)
    info = rs.info("1.08.003")
    assert info.trials == 36 and info.engine_version == "1.08.003" and info.jsd_limit == 2.33


def _engine_without_binary() -> GnubgEngine:
    eng = GnubgEngine.__new__(GnubgEngine)
    eng.binary = "gnubg"
    eng.move_filter = MoveFilter(accept=6, extra=2, threshold=0.1)
    eng.timeout = 1
    eng.threads = 4
    return eng


def test_build_rollout_commands_checker():
    eng = _engine_without_binary()
    cmds = eng.build_rollout_commands(
        parse_xgid(OPENING_31),
        settings=RolloutSettings(trials=36),
        play="13/7* 8/5(2)",
        ranks=[3, 1],
    )
    lines = cmds.splitlines()
    assert "set threads 4" in lines
    # Analysis settings mirror the evaluation settings so ranks line up.
    assert "set analysis chequerplay evaluation plies 2" in lines
    assert "set analysis movefilter 2 0 6 2 0.1" in lines
    assert lines.index("set xgid " + OPENING_31) < lines.index("move 13/7 8/5 8/5")
    assert lines[-3:] == ["previous", "analyse move", "analyse rollout move 1 3"]
    assert "set rollout trials 36" in lines


def test_build_rollout_commands_cube():
    eng = _engine_without_binary()
    cmds = eng.build_rollout_commands(
        parse_xgid(OPENING_CUBE), settings=RolloutSettings(trials=36), play=None, ranks=None
    )
    assert cmds.splitlines()[-4:] == ["double", "previous", "analyse move", "analyse rollout cube"]


def test_evaluation_commands_unchanged_shape():
    eng = _engine_without_binary()
    cmds = eng.build_commands(parse_xgid(OPENING_31), plies=2)
    assert "set evaluation movefilter 2 0 6 2 0.1" in cmds
    assert cmds.strip().endswith("hint")


@pytest.mark.skipif(find_gnubg() is None, reason="gnubg not installed")
def test_live_checker_rollout_top_two():
    eng = GnubgEngine()
    ev = eng.rollout(
        parse_xgid(OPENING_31), top=2, settings=RolloutSettings(trials=36, seed=1, jsd_stop=False)
    )
    assert ev.kind == "checker"
    assert ev.rollout is not None and ev.rollout.trials == 36
    assert ev.rollout.engine_version is not None
    assert [m.rank for m in ev.moves] == [1, 2]
    assert ev.moves[0].move == "8/5 6/5"
    assert ev.moves[0].error == 0.0 and ev.moves[1].error < 0
    assert all(m.ply == "rollout" and m.trials == 36 and m.se is not None for m in ev.moves)


@pytest.mark.skipif(find_gnubg() is None, reason="gnubg not installed")
def test_live_checker_rollout_named_moves_and_pending_double():
    eng = GnubgEngine()
    ev = eng.rollout(
        parse_xgid(OPENING_31),
        moves=["13/10 24/23", "24/20"],  # out of order on purpose
        settings=RolloutSettings(trials=36, seed=1, jsd_stop=False),
    )
    assert {m.move for m in ev.moves} == {"24/23 13/10", "24/20"}
    with pytest.raises(Exception, match="not in gnubg's move list"):
        eng.rollout(
            parse_xgid(OPENING_31), moves=["24/18 13/11"], settings=RolloutSettings(trials=36)
        )


@pytest.mark.skipif(find_gnubg() is None, reason="gnubg not installed")
def test_live_cube_rollout():
    eng = GnubgEngine()
    ev = eng.rollout(
        parse_xgid(OPENING_CUBE), settings=RolloutSettings(trials=36, seed=1, jsd_stop=False)
    )
    assert ev.kind == "cube" and ev.cube is not None
    assert ev.cube.ply == "rollout"
    assert ev.cube.trials == 36
    assert ev.cube.se_no_double is not None and ev.cube.se_double_take is not None
    assert ev.cube.best_cube_action == "no double"
    # A pending double is rolled out as the doubler's decision.
    pending = parse_xgid("XGID=-b----E-C---eE---c-e----B-:0:0:1:D:0:0:0:0:10")
    ev2 = eng.rollout(pending, settings=RolloutSettings(trials=36, seed=1, jsd_stop=False))
    assert ev2.kind == "cube" and ev2.position.cube_action is None


OPP_OWNS_CUBE_NO_DICE = "XGID=-b----E-C---eE---c-e----B-:1:-1:1:00:0:0:0:0:10"
OPP_OWNS_CUBE_31 = "XGID=-b----E-C---eE---c-e----B-:1:-1:1:31:0:0:0:0:10"


def test_parse_static_rollout():
    from bgcoach.engines.gnubg import parse_static_rollout

    text = (FIX / "rollout_static_opp_cube_36.txt").read_text()
    st = parse_static_rollout(text)
    assert st is not None
    assert st.ply == "rollout"
    assert st.trials == 36
    assert st.se is not None and 0 < st.se < 0.2
    # Opponent owns a 2-cube: cubeful value is below the cubeless one.
    assert st.cubeful_equity < st.cubeless_equity
    assert st.probs.win + st.probs.lose == pytest.approx(1.0, abs=0.002)
    # The last block wins over the intermediate progress tables.
    assert text.count("Current Position:") >= 1
    assert parse_static_rollout((FIX / "checker_2ply_money.txt").read_text()) is None


def test_build_rollout_commands_static():
    eng = _engine_without_binary()
    cmds = eng.build_rollout_commands(
        parse_xgid(OPP_OWNS_CUBE_NO_DICE),
        settings=RolloutSettings(trials=36),
        play=None,
        ranks=None,
        static=True,
    )
    assert cmds.splitlines()[-1] == "rollout"
    with pytest.raises(ValueError):
        eng.build_rollout_commands(
            parse_xgid(OPP_OWNS_CUBE_NO_DICE),
            settings=RolloutSettings(),
            play="8/5 6/5",
            ranks=[1],
            static=True,
        )


@pytest.mark.skipif(find_gnubg() is None, reason="gnubg not installed")
def test_live_rollouts_with_opponent_owning_the_cube():
    eng = GnubgEngine()
    rs = RolloutSettings(trials=36, seed=1, jsd_stop=False)
    # Checker play: the ordinary path, cube ownership makes no difference.
    ev = eng.rollout(parse_xgid(OPP_OWNS_CUBE_31), top=2, settings=rs)
    assert ev.kind == "checker" and all(m.trials == 36 for m in ev.moves)
    # No dice: no cube decision for the player on roll, so the position's value.
    st = eng.rollout(parse_xgid(OPP_OWNS_CUBE_NO_DICE), settings=rs)
    assert st.kind == "static" and st.static is not None
    assert st.static.ply == "rollout" and st.static.trials == 36 and st.static.se is not None
    assert st.rollout is not None and st.rollout.engine_version is not None
    assert st.static.cubeful_equity < st.static.cubeless_equity
