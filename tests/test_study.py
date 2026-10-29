"""Study assembly and persistence, with a fake engine so no gnubg is needed."""

import json
from pathlib import Path

import pytest

from bgcoach.engines.base import CubeEval, Evaluation, MoveEval, Probs, RolloutInfo
from bgcoach.position import parse_xgid
from bgcoach.study import Study, run_study, size_word

OPENING_31 = "XGID=-b----E-C---eE---c-e----B-:0:0:1:31:0:0:0:0:10"
OPENING_CUBE = "XGID=-b----E-C---eE---c-e----B-:0:0:1:00:0:0:0:0:10"
P = Probs(0.55, 0.17, 0.01, 0.45, 0.11, 0.01)


class FakeEngine:
    name = "fake"

    def __init__(self):
        self.rollout_calls = []

    def evaluate(self, position, *, plies=2):
        if position.dice is not None:
            moves = [
                MoveEval(1, "8/5 6/5", 0.204, 0.0, P, "2-ply"),
                MoveEval(2, "24/23 13/10", -0.022, -0.226, P, "2-ply"),
                MoveEval(3, "24/20", -0.031, -0.235, P, "2-ply"),
                MoveEval(4, "13/9", -0.040, -0.244, P, "2-ply"),
            ]
            return Evaluation(position, "checker", self.name, "fake 2-ply", moves=moves)
        cube = CubeEval(0.131, -0.192, 1.0, "No double, take", P, 0.085, "2-ply")
        return Evaluation(position, "cube", self.name, "fake 2-ply", cube=cube)

    def rollout(self, position, *, moves=None, top=2, settings=None):
        self.rollout_calls.append(moves)
        info = RolloutInfo(1296, 1, True, True, None, True, 2.33, 0, 2, "fake")
        if position.dice is not None:
            eqs = {"8/5 6/5": 0.246, "24/23 13/10": 0.011, "24/20": -0.02, "13/9": -0.03}
            chosen = sorted(moves, key=lambda m: -eqs[m])
            best = eqs[chosen[0]]
            rolled = [
                MoveEval(
                    i + 1, m, eqs[m], round(eqs[m] - best, 3), P, "rollout", se=0.011, trials=1296
                )
                for i, m in enumerate(chosen)
            ]
            return Evaluation(
                position, "checker", self.name, "fake rollout", moves=rolled, rollout=info
            )
        cube = CubeEval(
            0.122,
            -0.2,
            1.0,
            "No double, take",
            P,
            0.079,
            "rollout",
            se_no_double=0.012,
            se_double_take=0.015,
            trials=1296,
        )
        return Evaluation(position, "cube", self.name, "fake rollout", cube=cube, rollout=info)


def test_size_words():
    assert size_word(0.0) == "level"
    assert size_word(-0.019) == "level"
    assert size_word(0.03) == "small error"
    assert size_word(-0.05) == "error"
    assert size_word(0.1) == "blunder"
    assert size_word(0.5) == "huge blunder"


def test_run_study_checker_adds_your_play(tmp_path: Path):
    eng = FakeEngine()
    study = run_study(eng, parse_xgid(OPENING_31), play="13/9", reasoning="builds a point", top=2)
    # Top two plus the user's play, which was outside the top two.
    assert eng.rollout_calls == [["8/5 6/5", "24/23 13/10", "13/9"]]
    v = study.verdict()
    assert v["best_play"] == "8/5 6/5"
    assert v["your_play"]["move"] == "13/9"
    assert v["your_play"]["is_best"] is False
    assert v["your_play"]["size"] == "huge blunder"
    folder = study.save(tmp_path)
    data = json.loads((folder / "study.json").read_text())
    assert data["schema"] == 1
    assert data["position"]["xgid"] == OPENING_31
    assert data["position"]["decision"] == "checker"
    assert data["your_reasoning"] == "builds a point"
    assert data["rollout"]["rollout"]["trials"] == 1296
    assert data["verdict"]["plays"][0]["move"] == "8/5 6/5"
    md = (folder / "study.md").read_text()
    assert "How this was checked" in md and "| 8/5 6/5 |" in md
    assert folder.name.startswith(study.created.date().isoformat())


def test_run_study_checker_play_already_in_top(tmp_path: Path):
    eng = FakeEngine()
    run_study(eng, parse_xgid(OPENING_31), play="6/5 8/5", top=2)
    assert eng.rollout_calls == [["8/5 6/5", "24/23 13/10"]]


def test_run_study_rejects_illegal_play():
    with pytest.raises(ValueError, match="not a legal play"):
        run_study(FakeEngine(), parse_xgid(OPENING_31), play="24/18 13/11")


def test_run_study_cube(tmp_path: Path):
    study = run_study(FakeEngine(), parse_xgid(OPENING_CUBE))
    v = study.verdict()
    assert v["action"] == "no double" and v["take_decision"] == "take"
    assert v["se_no_double"] == 0.012
    folder = study.save(tmp_path, slug="opening cube")
    assert folder.name.endswith("-opening-cube")
    assert "Double/take" in (folder / "study.md").read_text()
    # Saving a second study with the same slug does not overwrite the first.
    other = Study(position=parse_xgid(OPENING_CUBE)).save(tmp_path, slug="opening cube")
    assert other != folder and other.exists()


def test_run_study_static_position(tmp_path: Path):
    from bgcoach.engines.base import StaticEval

    class StaticEngine(FakeEngine):
        def evaluate(self, position, *, plies=2):
            st = StaticEval(P, 0.076, -0.086, "2-ply")
            return Evaluation(position, "static", self.name, "fake 2-ply", static=st)

        def rollout(self, position, *, moves=None, top=2, settings=None):
            info = RolloutInfo(1296, 1, True, True, None, True, 2.33, 0, 2, "fake")
            st = StaticEval(P, 0.064, -0.094, "rollout", se=0.012, trials=1296)
            return Evaluation(
                position, "static", self.name, "fake rollout", static=st, rollout=info
            )

    study = run_study(
        StaticEngine(), parse_xgid("XGID=-b----E-C---eE---c-e----B-:1:-1:1:00:0:0:0:0:10")
    )
    assert study.decision == "position"
    v = study.verdict()
    assert v["cubeful_equity"] == -0.094 and v["se"] == 0.012 and v["trials"] == 1296
    folder = study.save(tmp_path)
    assert "Position value" in (folder / "study.md").read_text()
    assert json.loads((folder / "study.json").read_text())["position"]["decision"] == "position"
