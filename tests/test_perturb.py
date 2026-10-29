import pytest

from bgcoach import perturb as P
from bgcoach.position import BOTTOM, TOP, parse_xgid, starting_position

START = starting_position(dice=(3, 1))


def test_move_checker_own_numbering_both_sides():
    p = P.move_checker(START, BOTTOM, 13, 11)
    assert p.checkers_on(BOTTOM, 13) == 4
    assert p.checkers_on(BOTTOM, 11) == 1
    q = P.move_checker(START, TOP, 13, 11)
    assert q.checkers_on(TOP, 13) == 4
    assert q.checkers_on(TOP, 11) == 1
    # Top player's 11-point is the bottom player's 14-point.
    assert q.board[14 - 1] == -1


def test_move_to_bar_and_off_adjusts_counts():
    p = P.move_checker(START, BOTTOM, 24, P.BAR)
    assert p.bar == (1, 0)
    assert p.checkers_on(BOTTOM, 24) == 1
    assert p.pip_count(BOTTOM) == 167 - 24 + 25
    q = P.move_checker(START, TOP, 6, P.OFF)
    assert q.off(TOP) == 1
    assert q.on_board(TOP) == 14


def test_blocked_destination_raises():
    with pytest.raises(P.PerturbError):
        P.move_checker(START, BOTTOM, 13, 12)  # bottom's 12 = top's 13-point stack


def test_empty_source_raises():
    with pytest.raises(P.PerturbError):
        P.move_checker(START, BOTTOM, 10, 9)
    with pytest.raises(P.PerturbError):
        P.move_checker(START, BOTTOM, P.BAR, 20)


def test_add_requires_off_checker():
    with pytest.raises(P.PerturbError):
        P.add_checker(START, BOTTOM, 20)
    p = P.remove_checker(START, BOTTOM, 6)
    assert p.off(BOTTOM) == 1
    p = P.add_checker(p, BOTTOM, 20)
    assert p.off(BOTTOM) == 0 and p.checkers_on(BOTTOM, 20) == 1


def test_move_point_moves_everything():
    p = P.move_point(START, BOTTOM, 8, 7)
    assert p.checkers_on(BOTTOM, 8) == 0 and p.checkers_on(BOTTOM, 7) == 3


def test_make_point():
    p = P.remove_checker(START, BOTTOM, 6)
    p = P.move_checker(p, BOTTOM, 13, 11)
    p = P.swap_blot_for_point(p, BOTTOM, 11)
    assert p.checkers_on(BOTTOM, 11) == 2
    with pytest.raises(P.PerturbError):
        P.swap_blot_for_point(p, BOTTOM, 11)


def test_cube_and_score_helpers():
    p = P.set_cube(START, value=2, owner=TOP)
    assert p.cube_value == 2 and p.cube_owner == TOP
    q = P.at_away(START, 3, 5)
    assert q.match_length == 5 and q.score == (2, 0)
    assert q.away(BOTTOM) == 3 and q.away(TOP) == 5
    d = P.to_dmp(START)
    assert d.match_length == 1 and d.score == (0, 0) and d.cube_value == 1
    g = P.gammon_go(START, BOTTOM)
    assert g.away(BOTTOM) == 2 and g.away(TOP) == 1
    s = P.gammon_save(START, BOTTOM)
    assert s.away(BOTTOM) == 1 and s.away(TOP) == 2
    m = P.to_money(q, jacoby=True)
    assert m.is_money_game and m.jacoby and not m.beaver


def test_dice_and_cube_action_are_exclusive():
    p = P.set_cube_action(START, "D")
    assert p.dice is None and p.cube_action == "D"
    q = P.set_dice(p, (6, 6))
    assert q.dice == (6, 6) and q.cube_action is None


def test_apply_sequence_and_describe():
    ops = [
        {"op": "move", "player": 1, "src": 13, "dst": 11},
        {"op": "cube", "value": 2, "owner": -1},
        {"op": "away", "bottom_away": 3, "top_away": 5},
        {"op": "dice", "dice": None},
    ]
    p = P.apply(START, ops)
    assert p.checkers_on(BOTTOM, 11) == 1
    assert p.cube_value == 2 and p.cube_owner == TOP
    assert p.match_length == 5 and p.dice is None
    assert P.describe(ops[0]) == "X: 13-pt → 11-pt"
    assert "O owns" in P.describe(ops[1])
    with pytest.raises(P.PerturbError):
        P.apply(START, [{"op": "teleport"}])
    with pytest.raises(P.PerturbError):
        P.apply(START, [{"op": "move", "player": 1}])


def test_mirror_op_keeps_decision_identical():
    p = parse_xgid("XGID=---BBBBAAA---Ac-bbccbAA-A-:1:1:-1:63:4:3:0:5:8")
    m = P.apply(p, [{"op": "mirror"}])
    assert m.turn == BOTTOM and m.away(BOTTOM) == 2
