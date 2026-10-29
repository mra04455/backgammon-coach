"""Parser tests run against captured gnubg 1.07 output (no gnubg needed).

The last test runs the real engine and is skipped when gnubg isn't installed.
"""

from pathlib import Path

import pytest

from bgcoach.engines.gnubg import (
    GnubgEngine,
    MoveFilter,
    find_gnubg,
    parse_checker_hint,
    parse_cube_hint,
)
from bgcoach.position import parse_xgid

FIX = Path(__file__).parent / "fixtures"


def test_parse_checker_2ply_money():
    moves = parse_checker_hint((FIX / "checker_2ply_money.txt").read_text())
    assert len(moves) == 10
    best = moves[0]
    assert best.rank == 1 and best.move == "8/5 6/5"
    assert best.equity == pytest.approx(0.218)
    assert best.error == 0.0
    assert best.ply == "2-ply"
    assert best.probs is not None and best.probs.win == pytest.approx(0.551)
    second = moves[1]
    assert second.move == "24/23 13/10"
    assert second.error == pytest.approx(-0.229)
    # Ranks are contiguous and errors are non-positive.
    assert [m.rank for m in moves] == list(range(1, 11))
    assert all(m.error <= 0 for m in moves)


def test_parse_checker_3ply_match_top_on_roll():
    moves = parse_checker_hint((FIX / "checker_3ply_match_top_on_roll.txt").read_text())
    assert moves[0].move == "11/8 11/5"
    assert moves[0].ply == "3-ply"
    # Filtered-out moves are reported at 0-ply; the parser keeps the label.
    assert any(m.ply == "0-ply" for m in moves)
    assert "*" in moves[1].move  # hitting moves keep their asterisk


def test_parse_cube_match():
    cube = parse_cube_hint((FIX / "cube_2ply_match.txt").read_text())
    assert cube is not None
    assert cube.no_double == pytest.approx(-2.058)
    assert cube.double_pass == pytest.approx(1.0)
    assert cube.double_take == pytest.approx(-2.43)
    assert cube.proper_action == "No double, take"
    assert cube.best_cube_action == "no double"
    assert cube.take_decision == "take"
    assert cube.cubeless_equity == pytest.approx(-2.238)
    assert cube.ply == "2-ply"
    assert cube.probs is not None and cube.probs.lose_bg == pytest.approx(0.44)


def test_parse_cube_too_good():
    cube = parse_cube_hint((FIX / "cube_2ply_money_double_offered.txt").read_text())
    assert cube is not None
    assert cube.proper_action.startswith("Too good to double")
    assert cube.best_cube_action == "too good"
    assert cube.take_decision == "pass"


def test_checker_parser_ignores_cube_block_and_vice_versa():
    assert parse_checker_hint((FIX / "cube_2ply_match.txt").read_text()) == []
    assert parse_cube_hint((FIX / "checker_2ply_money.txt").read_text()) is None


def test_build_commands_uses_positive_accept_counts():
    eng = GnubgEngine.__new__(GnubgEngine)
    eng.binary = "gnubg"
    eng.move_filter = MoveFilter(accept=6, extra=2, threshold=0.1)
    eng.timeout = 1
    cmds = eng.build_commands(
        parse_xgid("XGID=-b----E-C---eE---c-e----B-:0:0:1:31:0:0:0:0:10"), plies=2
    )
    assert "set evaluation chequerplay evaluation plies 2" in cmds
    assert "set evaluation movefilter 2 0 6 2 0.1" in cmds
    assert "set evaluation movefilter 2 1 -1 0 0" in cmds
    assert "set xgid XGID=-b----E-C---eE---c-e----B-:0:0:1:31:0:0:0:0:10" in cmds
    assert cmds.strip().endswith("hint")
    # Never emit an accept count of 0: the CLI treats it as "skip this ply".
    for line in cmds.splitlines():
        if line.startswith("set evaluation movefilter"):
            accept = int(line.split()[5])
            assert accept != 0


@pytest.mark.skipif(find_gnubg() is None, reason="gnubg not installed")
def test_live_gnubg_round_trip():
    eng = GnubgEngine()
    ev = eng.evaluate(parse_xgid("XGID=-b----E-C---eE---c-e----B-:0:0:1:31:0:0:0:0:10"), plies=2)
    assert ev.kind == "checker"
    assert ev.best_move is not None and ev.best_move.move == "8/5 6/5"
    assert ev.best_move.ply == "2-ply"
    cube = eng.evaluate(parse_xgid("XGID=----BBCA-----A----B-B--eB-:0:0:1:00:0:3:0:5:10"), plies=2)
    assert cube.kind == "cube" and cube.cube is not None


def test_parse_eval_table_dead_cube():
    from bgcoach.engines.gnubg import cube_is_dead_message, parse_eval_table

    text = (FIX / "static_dmp_cannot_double.txt").read_text()
    assert cube_is_dead_message(text)
    assert parse_cube_hint(text) is None
    st = parse_eval_table(text, prefer_ply=2)
    assert st is not None
    assert st.ply == "2-ply"
    assert st.probs.win == pytest.approx(0.525)
    assert st.probs.lose == pytest.approx(0.475)
    assert st.cubeless_equity == pytest.approx(0.050)
    assert st.cubeful_equity == pytest.approx(0.050)
    # Asking for a shallower ply returns that row.
    assert parse_eval_table(text, prefer_ply=1).ply == "1-ply"
    assert parse_eval_table(text, prefer_ply=0).ply == "0-ply"


@pytest.mark.skipif(find_gnubg() is None, reason="gnubg not installed")
def test_live_dead_cube_returns_static():
    eng = GnubgEngine()
    ev = eng.evaluate(parse_xgid("XGID=-b----E-C---eE---c-e----B-:0:0:1:00:0:0:0:1:10"), plies=2)
    assert ev.kind == "static" and ev.static is not None
    assert ev.best_equity == pytest.approx(ev.static.cubeful_equity)
