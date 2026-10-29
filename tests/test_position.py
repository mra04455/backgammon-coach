import pytest

from bgcoach.position import (
    BOTTOM,
    TOP,
    Position,
    XGIDError,
    parse_xgid,
    starting_position,
)

# Real XGIDs: starting position, a 5-point match with an owned cube and the
# top player on roll, a bear-off, a pending double, and bar checkers in a
# money game with Jacoby + beavers.
KNOWN = [
    "XGID=-b----E-C---eE---c-e----B-:0:0:1:31:0:0:0:0:10",
    "XGID=---BBBBAAA---Ac-bbccbAA-A-:1:1:-1:63:4:3:0:5:8",
    "XGID=----BBCA-----A----B-B--eB-:0:0:1:51:0:3:0:5:10",
    "XGID=----BBCA-----A----B-B--eB-:0:0:-1:D:0:0:0:0:10",
    "XGID=aBBBB-------------------bA:0:0:1:00:0:0:3:0:10",
]


@pytest.mark.parametrize("xgid", KNOWN)
def test_roundtrip(xgid):
    assert parse_xgid(xgid).xgid() == xgid


def test_prefix_optional_and_default_max_cube():
    p = parse_xgid("-b----E-C---eE---c-e----B-:0:0:1:31:0:0:0:0")
    assert p.max_cube == 1024
    assert p.xgid() == KNOWN[0]
    assert p.xgid(prefix=False) == KNOWN[0][5:]


def test_starting_position_facts():
    p = starting_position()
    assert p.pip_count(BOTTOM) == 167
    assert p.pip_count(TOP) == 167
    assert p.off(BOTTOM) == p.off(TOP) == 0
    assert p.checkers_on(BOTTOM, 24) == 2
    assert p.checkers_on(BOTTOM, 13) == 5
    assert p.checkers_on(BOTTOM, 8) == 3
    assert p.checkers_on(BOTTOM, 6) == 5
    # Symmetric: the top player sees the same thing in their own numbering.
    for pt in (24, 13, 8, 6):
        assert p.checkers_on(TOP, pt) == p.checkers_on(BOTTOM, pt)
    assert p.dice is None and p.cube_action is None


def test_fields_decode():
    p = parse_xgid(KNOWN[1])
    assert p.cube_value == 2
    assert p.cube_owner == BOTTOM
    assert p.turn == TOP
    assert p.dice == (6, 3)
    assert p.score == (4, 3)
    assert p.match_length == 5
    assert p.away(BOTTOM) == 1 and p.away(TOP) == 2
    assert p.max_cube == 256
    assert not p.crawford

    q = parse_xgid(KNOWN[3])
    assert q.cube_action == "D" and q.dice is None

    r = parse_xgid(KNOWN[4])
    assert r.bar == (1, 1)
    assert r.jacoby and r.beaver and r.is_money_game
    assert r.off(BOTTOM) == 6 and r.off(TOP) == 12


def test_bear_off_counts():
    p = parse_xgid(KNOWN[2])
    assert p.off(TOP) == 10
    assert p.pip_count(TOP) == 10  # five checkers on their 2-point


def test_mirror_is_involution_and_swaps_sides():
    p = parse_xgid(KNOWN[1])
    m = p.mirror()
    assert m.mirror() == p
    assert m.turn == -p.turn
    assert m.cube_owner == -p.cube_owner
    assert m.score == (p.score[1], p.score[0])
    assert m.pip_count(BOTTOM) == p.pip_count(TOP)
    # Each player's own-numbered view is unchanged by mirroring.
    for pt in range(1, 25):
        assert m.checkers_on(BOTTOM, pt) == p.checkers_on(TOP, pt)


def test_crawford_flag_roundtrip():
    p = starting_position(match_length=5, score=(4, 2), crawford=True)
    assert p.xgid().split(":")[7] == "1"
    assert parse_xgid(p.xgid()).crawford


@pytest.mark.parametrize(
    "bad",
    [
        "XGID=-b----E-C---eE---c-e----B-:0:0:1:31:0:0:0",  # too few fields
        "XGID=-b----E-C---eE---c-e----B:0:0:1:31:0:0:0:0:10",  # 25 chars
        "XGID=-b----E-C---eE---c-e----Bb:0:0:1:31:0:0:0:0:10",  # bottom bar lowercase
        "XGID=-b----E-C---eE---c-e----B-:0:0:1:79:0:0:0:0:10",  # bad dice
        "XGID=-b----E-C---eE---c-e----B-:0:0:2:31:0:0:0:0:10",  # bad turn
        "XGID=OOOOOO--------------------:0:0:1:00:0:0:0:0:10",  # 90 checkers
    ],
)
def test_rejects_malformed(bad):
    with pytest.raises(XGIDError):
        parse_xgid(bad)


def test_position_validation():
    with pytest.raises(ValueError):
        Position(board=(0,) * 23)
    with pytest.raises(ValueError):
        Position(board=(0,) * 24, cube_value=3)
    with pytest.raises(ValueError):
        Position(board=(0,) * 24, dice=(3, 1), cube_action="D")


def test_ascii_contains_summary():
    s = parse_xgid(KNOWN[1]).ascii()
    assert "O (top) to play 63" in s
    assert "5-pt match" in s
    assert KNOWN[1] in s
    # Every board row has the same width.
    rows = [ln for ln in s.splitlines() if ln.startswith((" |", " +"))]
    assert len({len(r) for r in rows}) == 1
