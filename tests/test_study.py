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


class CloseEngine(FakeEngine):
    """Checker rollouts come back close at the default trial count, settled at more."""

    def rollout(self, position, *, moves=None, top=2, settings=None):
        trials = getattr(settings, "trials", 1296)
        self.rollout_calls.append((list(moves or []), trials))
        info = RolloutInfo(trials, 1, True, True, None, True, 2.33, 0, 2, "fake")
        se = 0.011 if trials <= 1296 else 0.005
        gap = 0.012  # inside 2 * joint SE at 1296 trials, outside at 5184
        rolled = [
            MoveEval(1, moves[0], 0.100, 0.0, P, "rollout", se=se, trials=trials),
            MoveEval(2, moves[1], 0.100 - gap, -gap, P, "rollout", se=se, trials=trials),
        ]
        return Evaluation(
            position, "checker", self.name, "fake rollout", moves=rolled, rollout=info
        )


def test_is_close():
    from bgcoach.engines.base import CubeEval
    from bgcoach.study import is_close

    def checker(gap, se):
        return Evaluation(
            parse_xgid(OPENING_31),
            "checker",
            "f",
            "l",
            moves=[
                MoveEval(1, "a", 0.1, 0.0, None, "rollout", se=se, trials=10),
                MoveEval(2, "b", 0.1 - gap, -gap, None, "rollout", se=se, trials=10),
            ],
        )

    assert is_close(checker(0.012, 0.011))  # 2 * joint SE = 0.031 > 0.012
    assert not is_close(checker(0.05, 0.011))
    assert is_close(checker(0.015, None))  # no SE: fall back to the 0.02 line
    assert not is_close(checker(0.03, None))

    def cube(nd, dt, se=0.01):
        c = CubeEval(nd, dt, 1.0, "x", None, None, "rollout", se_no_double=se, se_double_take=se)
        return Evaluation(parse_xgid(OPENING_CUBE), "cube", "f", "l", cube=c)

    assert not is_close(cube(0.3, 0.5))  # clear double, clear take
    assert is_close(cube(0.49, 0.5))  # double margin inside the band
    assert is_close(cube(0.3, 0.99))  # take margin inside the band
    assert not is_close(Evaluation(parse_xgid(OPENING_CUBE), "static", "f", "l"))


def test_run_study_extends_close_decision():
    from bgcoach.engines.gnubg import RolloutSettings

    eng = CloseEngine()
    eng.rollout_settings = RolloutSettings()
    study = run_study(eng, parse_xgid(OPENING_31), top=2)
    assert [t for _, t in eng.rollout_calls] == [1296, 5184]
    assert study.rollout is not None and study.rollout.rollout.trials == 5184
    assert len(study.superseded_rollouts) == 1
    # A 0.012 gap stays inside the 0.02 line however many trials: it is level,
    # and the study says so rather than extending again.
    assert study.verdict()["close"] is True
    d = study.to_dict()
    assert d["superseded_rollouts"][0]["rollout"]["trials"] == 1296
    assert "extended" in study.markdown()


def test_run_study_extension_can_be_disabled_or_is_skipped_when_not_bigger():
    from bgcoach.engines.gnubg import RolloutSettings

    eng = CloseEngine()
    run_study(eng, parse_xgid(OPENING_31), extend_trials=None, settings=RolloutSettings())
    assert [t for _, t in eng.rollout_calls] == [1296]
    eng = CloseEngine()
    run_study(eng, parse_xgid(OPENING_31), settings=RolloutSettings(trials=10000))
    assert [t for _, t in eng.rollout_calls] == [10000]
    # An engine without settings support just keeps the close result.
    eng = CloseEngine()
    study = run_study(eng, parse_xgid(OPENING_31))
    assert [t for _, t in eng.rollout_calls] == [1296]
    assert study.verdict()["close"] is True


def test_update_study_rerenders_markdown(tmp_path: Path):
    from bgcoach.study import load_study, update_study

    study = run_study(FakeEngine(), parse_xgid(OPENING_31), play="13/9")
    folder = study.save(tmp_path)
    assert "_Account not written yet._" in (folder / "study.md").read_text()
    data = update_study(
        folder,
        hypotheses=[{"feature": "builder", "prediction": "no effect"}],
        variants=[{"label": "no 8-point", "operations": []}],
        account="Making the 5-point is worth a quarter of a point.",
    )
    assert data["hypotheses"][0]["feature"] == "builder"
    md = (folder / "study.md").read_text()
    assert "quarter of a point" in md and "_Account not written yet._" not in md
    assert "1 hypothesis(es) and 1 variant(s)" in md
    # Untouched fields survive, and the JSON on disk is what load_study returns.
    again = load_study(folder)
    assert again["your_play"] == "13/9" and again["rollout"]["kind"] == "checker"
    update_study(folder, account="Second draft.")
    assert load_study(folder)["hypotheses"][0]["feature"] == "builder"


def test_write_cli(tmp_path: Path, capsys):
    from bgcoach.cli import main

    study = run_study(FakeEngine(), parse_xgid(OPENING_31))
    folder = study.save(tmp_path)
    acct = tmp_path / "account.md"
    acct.write_text("The point is the point.\n")
    rc = main(["write", str(folder), "--account", str(acct), "--hypotheses", '[{"feature": "x"}]'])
    assert rc == 0
    out = json.loads(capsys.readouterr().out)
    assert out["hypotheses"] == 1 and out["account_chars"] > 0
    assert "The point is the point." in (folder / "study.md").read_text()
    assert main(["write", str(folder), "--hypotheses", '{"not": "a list"}']) == 2
