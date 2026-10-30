"""Legal-move generation and the exact counts built on it.

The generator is checked against gnubg's own full move list (live tests)
and against hand-verified counts from the first three studies.
"""

import pytest

from bgcoach import facts
from bgcoach.engines.gnubg import GnubgEngine, find_gnubg
from bgcoach.moves import (
    apply_play,
    entering_rolls,
    find_play,
    format_play,
    hitting_rolls,
    legal_plays,
    parse_play,
    point_making_rolls,
)
from bgcoach.position import parse_xgid

OPENING_31 = "XGID=-b----E-C---eE---c-e----B-:0:0:1:31:0:0:0:0:10"
BEARIN_51 = "XGID=-a-B-CCBA-AAb---bbbcBa-b--:0:0:1:51:0:0:3:0:10"
BAR_61 = "XGID=a-BCB-B-B---bD---bbcbab---:0:0:-1:61:0:0:3:0:10"
CLOSEOUT_11 = "XGID=bBABBBB-A-A-bB---bbcb-b---:1:-1:1:11:5:14:3:0:10"


def test_opening_31_plays():
    plays = {str(p) for p in legal_plays(parse_xgid(OPENING_31))}
    assert len(plays) == 16
    assert {"8/5 6/5", "24/23 13/10", "24/21/20", "13/10/9"} <= plays


def test_parse_and_format_round_trip():
    assert parse_play("bar/24 13/7*/5 8/4(2)") == [(25, 24), (13, 7), (7, 5), (8, 4), (8, 4)]
    pos = parse_xgid(OPENING_31)
    for p in legal_plays(pos):
        again = apply_play(pos, str(p))
        assert again.board == p.result.board and again.bar == p.result.bar


def test_entering_rules_from_the_bar():
    pos = parse_xgid(BAR_61)  # O on roll, one on the bar, X holds its 6-point
    plays = {str(p) for p in legal_plays(pos)}
    assert plays == {"bar/24 8/2", "bar/24 7/1", "bar/24 13/7", "bar/24/18"}
    # Two on the bar with 1-1: both must enter before anything else moves.
    pos2 = parse_xgid(CLOSEOUT_11).with_(turn=-1, dice=(1, 1))
    assert legal_plays(pos2) == []  # O enters on O's 24-point = X's ace point, which X holds
    pos3 = parse_xgid(CLOSEOUT_11).with_(turn=-1, dice=(2, 2))
    plays3 = legal_plays(pos3)
    assert plays3
    for p in plays3:
        assert p.steps[0].src == 25 and p.steps[1].src == 25  # both enter first
        assert p.steps[0].hit  # the first one hits X's blot on the 2-point
        assert str(p).startswith("bar/23* bar/23")


def test_find_play_matches_loose_notation():
    pos = parse_xgid(CLOSEOUT_11)
    assert find_play(pos, "10/6") is not None
    assert find_play(pos, "10/9/8/7/6") is not None
    assert find_play(pos, "5/2 5/4") is not None
    assert find_play(pos, "24/18") is None  # no checker there


def test_hand_verified_shot_counts():
    # Study 1: after 11/6 8/7 the blot on X's 10 is hit only by 6-3 (5-4 and 3-3 are blocked).
    pos = parse_xgid(BEARIN_51)
    after = apply_play(pos, "11/6 8/7").with_(turn=-1, dice=None)
    assert hitting_rolls(after, -1, 10)[0] == 2
    after2 = apply_play(pos, "10/5 8/7").with_(turn=-1, dice=None)
    assert hitting_rolls(after2, -1, 11)[0] == 0
    # Study 2: after bar/18 X hits the blot on X's 7 with any 6, any 1, 4-2, 3-3, 2-2.
    pos = parse_xgid(BAR_61)
    after = apply_play(pos, "bar/24/18").with_(turn=1, dice=None)
    n, rolls = hitting_rolls(after, 1, 18)  # O's 18-point is X's 7-point
    assert n == 24
    assert (2, 4) in rolls and (3, 3) in rolls and (2, 2) in rolls
    # Study 3: after 10/6 every entering 2 hits the blot on X's 2-point; nothing reaches the 8.
    pos = parse_xgid(CLOSEOUT_11)
    after = apply_play(pos, "10/6").with_(turn=-1, dice=None)
    assert hitting_rolls(after, -1, 2)[0] == 11
    assert hitting_rolls(after, -1, 8)[0] == 0
    assert entering_rolls(after, -1) == {
        "on_bar": 2,
        "entering_dice": [2],
        "rolls_entering_one": 11,
        "rolls_entering_all": 1,
    }


def test_point_making_counts_from_study_one():
    pos = parse_xgid(BEARIN_51)
    after_best = apply_play(pos, "11/6 8/7").with_(turn=1, dice=None)
    after_user = apply_play(pos, "10/5 8/7").with_(turn=1, dice=None)
    assert point_making_rolls(after_best, 1, 4)[0] == 15
    assert point_making_rolls(after_user, 1, 4)[0] == 9


def test_facts_home_board_excludes_blocking_points():
    f = facts.facts(parse_xgid(CLOSEOUT_11))
    assert f["O"]["home_board"]["made"] == [3, 5, 6] and f["O"]["home_board"]["count"] == 3
    assert f["O"]["made_points"] == [3, 5, 6, 7, 8, 13]
    assert f["O"]["prime"] == {"from": 5, "to": 8, "length": 4}
    assert f["X"]["home_board"]["made"] == [1, 3, 4, 5, 6]
    assert f["X"]["spares"] == {}  # two checkers on the 6-point is not a spare
    assert f["X"]["blots"] == [2, 8, 10]
    assert f["O"]["entering"]["rolls_entering_one"] == 11
    assert f["race"]["X_leads_by"] == 56
    pf = facts.play_facts(parse_xgid(CLOSEOUT_11), "5/2 5/4")
    assert pf["legal"] and pf["after"]["X"]["home_board"]["open"] == [5]
    # Entering on the 5-point hits nothing; only 5-5 enters and runs on to the blot on the 10.
    assert pf["opponent_threats"]["shots"] == [
        {"blot_on_defender_point": 10, "rolls": 1, "of": 36, "dice": [(5, 5)]}
    ]
    assert pf["my_next_turn"]["make_home_point"][5] == 8


@pytest.mark.skipif(find_gnubg() is None, reason="gnubg not installed")
@pytest.mark.parametrize("xgid", [OPENING_31, BEARIN_51, BAR_61, CLOSEOUT_11])
def test_live_generator_matches_gnubg_move_list(xgid):
    eng = GnubgEngine()
    eng.hint_moves = 500
    pos = parse_xgid(xgid)
    theirs = set()
    for m in eng.evaluate(pos, plies=0).moves:
        r = apply_play(pos, m.move)
        theirs.add((r.board, r.bar))
    ours = {(p.result.board, p.result.bar) for p in legal_plays(pos)}
    assert ours == theirs
    assert format_play(legal_plays(pos)[0].steps)  # notation never blank
