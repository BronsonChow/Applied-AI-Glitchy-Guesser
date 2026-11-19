import pytest

from edge_cases import (
    builtin_cases,
    guess_case,
    load_csv_cases,
    main,
    play_guess,
    run_case,
)


def test_play_guess_reports_hint_direction():
    assert play_guess("10", 1, 100, secret=50)[0] == "higher"
    assert play_guess("90", 1, 100, secret=50)[0] == "lower"
    assert play_guess("50", 1, 100, secret=50)[0] == "win"

def test_play_guess_rejects_without_using_secret():
    assert play_guess("abc", 1, 100, secret=50)[0] == "reject"

def test_accept_matches_any_hint():
    assert run_case(guess_case("t", "", "10", "accept", 1, 100, secret=50)).passed

def test_wrong_expectation_fails():
    result = run_case(guess_case("t", "", "10", "lower", 1, 100, secret=50))
    assert not result.passed and result.actual == "higher"

def test_hint_expectation_needs_secret():
    with pytest.raises(ValueError):
        guess_case("t", "", "10", "win", 1, 100)

def test_unknown_expectation_is_refused():
    with pytest.raises(ValueError):
        guess_case("t", "", "10", "maybe", 1, 100)

def test_builtin_cases_never_crash():
    for case in builtin_cases():
        assert not str(run_case(case).actual).startswith("crashed"), case.name

def test_csv_cases_load_and_use_defaults(tmp_path):
    path = tmp_path / "cases.csv"
    path.write_text(
        "# comment\n"
        "input,expected,low,high,history,secret,note\n"
        "5,accept,,,,,\n"
        "5,reject,,,5,,repeat\n"
        "\"#7\",reject,,,,,\n",
        encoding="utf-8",
    )
    cases = load_csv_cases(str(path), 1, 100)
    assert len(cases) == 3
    assert all(run_case(case).passed for case in cases)

def test_csv_bad_number_names_the_line(tmp_path):
    path = tmp_path / "cases.csv"
    path.write_text("input,expected,low\n5,accept,one\n", encoding="utf-8")
    with pytest.raises(ValueError, match="line 2"):
        load_csv_cases(str(path), 1, 100)

def test_sample_csv_passes():
    assert main(["--file", "tests/edge_cases.csv"]) == 0

def test_fail_under_sets_exit_status(tmp_path):
    path = tmp_path / "cases.csv"
    path.write_text("input,expected\n5,accept\n5,reject\n", encoding="utf-8")
    assert main(["--file", str(path)]) == 1
    assert main(["--file", str(path), "--fail-under", "50"]) == 0
