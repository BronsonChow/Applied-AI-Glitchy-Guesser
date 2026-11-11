import pytest

from logic_utils import (
    DIFFICULTY_SETTINGS,
    check_guess,
    closest_difficulty,
    get_attempts_for_difficulty,
    get_range_for_difficulty,
    is_float,
    parse_guess,
    update_score,
    score_multiplier,
    validate_guess,
)


# get_range_for_difficulty returns the inclusive (low, high) default range.

def test_range_easy():
    assert get_range_for_difficulty("Easy") == (1, 20)

def test_range_normal():
    assert get_range_for_difficulty("Normal") == (1, 100)

def test_range_hard():
    assert get_range_for_difficulty("Hard") == (1, 200)

def test_range_unknown_difficulty_falls_back_to_normal():
    assert get_range_for_difficulty("Impossible") == get_range_for_difficulty("Normal")

def test_range_grows_with_difficulty():
    sizes = [
        high - low + 1
        for low, high in map(get_range_for_difficulty, ["Easy", "Normal", "Hard"])
    ]
    assert sizes == sorted(sizes) and len(set(sizes)) == 3

def test_every_range_is_valid():
    # The app's min/max inputs require low < high.
    for difficulty in ["Easy", "Normal", "Hard"]:
        low, high = get_range_for_difficulty(difficulty)
        assert low < high


# is_float decides whether parse_guess reports "Decimals" or "not a number".

def test_is_float_accepts_decimals_and_ints():
    assert is_float("4.5")
    assert is_float("-0.25")
    assert is_float("7")

def test_is_float_rejects_text():
    assert not is_float("abc")
    assert not is_float("4.5.6")
    assert not is_float("")

# check_guess returns (outcome, message); the app shows the message as a hint.

def test_winning_guess():
    # If the secret is 50 and guess is 50, it should be a win
    outcome, message = check_guess(50, 50)
    assert outcome == "Win"
    assert "Correct" in message

def test_guess_too_high():
    # If secret is 50 and guess is 60, hint should be "Too High"
    outcome, message = check_guess(60, 50)
    assert outcome == "Too High"
    assert "LOWER" in message

def test_guess_too_low():
    # If secret is 50 and guess is 40, hint should be "Too Low"
    outcome, message = check_guess(40, 50)
    assert outcome == "Too Low"
    assert "HIGHER" in message


# parse_guess returns (ok, guess_int, error_message).

def test_parse_valid_number():
    assert parse_guess("42") == (True, 42, None)

def test_parse_strips_surrounding_spaces():
    assert parse_guess(" 42 ") == (True, 42, None)

def test_parse_empty_input():
    assert parse_guess("") == (False, None, "Enter a guess.")

def test_parse_whitespace_only_counts_as_empty():
    assert parse_guess("   ") == (False, None, "Enter a guess.")

def test_parse_none():
    assert parse_guess(None) == (False, None, "Enter a guess.")

def test_parse_rejects_decimals():
    ok, value, err = parse_guess("4.5")
    assert not ok and value is None
    assert "Decimals" in err

def test_parse_rejects_text():
    assert parse_guess("abc") == (False, None, "That is not a number.")


# validate_guess returns (ok, error_message) for a parsed guess.

def test_validate_accepts_guess_in_range():
    assert validate_guess(50, 1, 100, []) == (True, None)

def test_validate_accepts_range_bounds():
    assert validate_guess(1, 1, 100, []) == (True, None)
    assert validate_guess(100, 1, 100, []) == (True, None)

def test_validate_rejects_below_range():
    assert validate_guess(0, 1, 100, []) == (
        False, "Your guess must be between 1 and 100."
    )

def test_validate_rejects_above_range():
    assert validate_guess(101, 1, 100, []) == (
        False, "Your guess must be between 1 and 100."
    )

def test_validate_rejects_duplicate_guess():
    assert validate_guess(42, 1, 100, [10, 42]) == (
        False, "You already guessed 42. Try a different number."
    )

def test_validate_respects_custom_range():
    # Users can set their own min/max, including ranges not starting at 1.
    assert validate_guess(-5, -10, 10, []) == (True, None)
    assert validate_guess(5, 50, 60, [])[0] is False

def test_validate_allows_new_guess_with_history():
    assert validate_guess(43, 1, 100, [10, 42]) == (True, None)

def test_validate_out_of_range_takes_priority_over_duplicate():
    # Matches the app's original order: range check first.
    ok, err = validate_guess(500, 1, 100, [500])
    assert not ok and "between" in err


# update_score: wins earn points scaled by the multiplier; misses cost nothing.

def test_first_try_win_on_normal():
    assert update_score(0, "Win", attempt_number=1, multiplier=1.0) == 100

def test_later_win_earns_fewer_points():
    assert update_score(0, "Win", attempt_number=3, multiplier=1.0) == 80

def test_win_points_never_drop_below_minimum():
    assert update_score(0, "Win", attempt_number=20, multiplier=1.0) == 10

def test_wrong_guess_does_not_change_score():
    assert update_score(0, "Too High", attempt_number=1) == 0
    assert update_score(0, "Too Low", attempt_number=1) == 0

def test_late_win_beats_a_loss():
    # Losing scores 0, so any win must be worth more, even at a tiny multiplier.
    assert update_score(0, "Win", attempt_number=20, multiplier=0.01) > 0

def test_multiplier_scales_win_points():
    assert update_score(0, "Win", attempt_number=1, multiplier=0.5) == 50
    assert update_score(0, "Win", attempt_number=1, multiplier=1.5) == 150


# Preset difficulties lock their attempts; Custom/unknown fall back to Normal.

def test_attempts_per_difficulty():
    assert get_attempts_for_difficulty("Easy") == 10
    assert get_attempts_for_difficulty("Normal") == 8
    assert get_attempts_for_difficulty("Hard") == 5

def test_custom_defaults_to_normal_settings():
    assert get_range_for_difficulty("Custom") == get_range_for_difficulty("Normal")
    assert get_attempts_for_difficulty("Custom") == get_attempts_for_difficulty("Normal")


# score_multiplier: presets get their own multiplier; Custom is interpolated.

def _preset(name):
    low, high = DIFFICULTY_SETTINGS[name]["range"]
    return high - low + 1, DIFFICULTY_SETTINGS[name]["attempts"]

@pytest.mark.parametrize("name", ["Easy", "Normal", "Hard"])
def test_preset_gets_its_own_multiplier(name):
    expected = DIFFICULTY_SETTINGS[name]["multiplier"]
    assert score_multiplier(*_preset(name)) == pytest.approx(expected)

def test_harder_presets_are_worth_more():
    easy, normal, hard = (score_multiplier(*_preset(n)) for n in ["Easy", "Normal", "Hard"])
    assert easy < normal < hard

def test_custom_between_normal_and_hard():
    # 1-150 with 6 attempts is harder than Normal but easier than Hard.
    assert 1.0 < score_multiplier(150, 6) < 1.5

def test_custom_harder_than_hard_keeps_rising():
    # Not capped at Hard's multiplier: harder custom games earn more.
    hard = DIFFICULTY_SETTINGS["Hard"]["multiplier"]
    assert hard < score_multiplier(200, 4) < score_multiplier(1000, 1)

@pytest.mark.parametrize("range_size, attempts", [(150, 6), (20, 7), (2, 20), (1000, 1)])
def test_custom_never_snaps_to_a_preset_multiplier(range_size, attempts):
    preset_multipliers = [s["multiplier"] for s in DIFFICULTY_SETTINGS.values()]
    multiplier = score_multiplier(range_size, attempts)
    assert all(multiplier != pytest.approx(m) for m in preset_multipliers)

def test_trivial_custom_is_worth_less_than_easy():
    # A 1-2 range with 20 attempts can't be used to farm points.
    assert score_multiplier(2, 20) < DIFFICULTY_SETTINGS["Easy"]["multiplier"]

def test_fewer_attempts_never_lowers_multiplier():
    multipliers = [score_multiplier(100, attempts) for attempts in range(20, 0, -1)]
    assert multipliers == sorted(multipliers)

def test_wider_range_never_lowers_multiplier():
    multipliers = [score_multiplier(size, 8) for size in range(2, 1001)]
    assert multipliers == sorted(multipliers)


# closest_difficulty names the preset a Custom game most resembles.

@pytest.mark.parametrize("name", ["Easy", "Normal", "Hard"])
def test_preset_settings_are_closest_to_themselves(name):
    assert closest_difficulty(*_preset(name)) == name

def test_closest_difficulty_for_custom_settings():
    assert closest_difficulty(2, 20) == "Easy"
    assert closest_difficulty(100, 10) == "Normal"
    assert closest_difficulty(1000, 1) == "Hard"
