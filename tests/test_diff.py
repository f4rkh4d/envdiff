from envdiff.diff import check_against_example, diff_envs


def test_diff_only_in_a():
    r = diff_envs({"A": "1", "B": "2"}, {"B": "2"})
    assert r.only_in_a == ["A"]
    assert r.only_in_b == []
    assert r.different == []
    assert r.same == ["B"]
    assert r.has_differences


def test_diff_only_in_b():
    r = diff_envs({"B": "2"}, {"A": "1", "B": "2"})
    assert r.only_in_b == ["A"]


def test_diff_different_values():
    r = diff_envs({"A": "1"}, {"A": "2"})
    assert r.different == ["A"]


def test_diff_identical():
    r = diff_envs({"A": "1"}, {"A": "1"})
    assert not r.has_differences
    assert r.same == ["A"]


def test_check_missing_and_extra():
    target = {"FOO": "1", "EXTRA": "x"}
    example = {"FOO": "", "BAR": ""}
    r = check_against_example(target, example)
    assert r.missing == ["BAR"]
    assert r.extra == ["EXTRA"]
    assert r.ok is False


def test_check_empty_values():
    target = {"FOO": "", "BAR": "set"}
    example = {"FOO": "", "BAR": ""}
    r = check_against_example(target, example)
    assert r.empty == ["FOO"]
    assert r.ok is True  # empty doesn't fail, only missing does


def test_check_ok():
    r = check_against_example({"A": "1"}, {"A": ""})
    assert r.ok
