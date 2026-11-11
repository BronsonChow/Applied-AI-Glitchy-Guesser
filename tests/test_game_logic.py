from logic_utils import (
    check_guess,
    get_range_for_difficulty,
    is_float,
    parse_guess,
    update_score,
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


# update_score: wins earn points scaled by range size; misses cost nothing.

def test_first_try_win_on_normal_range():
    assert update_score(0, "Win", attempt_number=1, range_size=100) == 100

def test_later_win_earns_fewer_points():
    assert update_score(0, "Win", attempt_number=3, range_size=100) == 80

def test_win_points_never_drop_below_minimum():
    assert update_score(0, "Win", attempt_number=20, range_size=100) == 10

def test_wrong_guess_does_not_change_score():
    assert update_score(0, "Too High", attempt_number=1) == 0
    assert update_score(0, "Too Low", attempt_number=1) == 0

def test_late_win_beats_a_loss():
    # Losing scores 0, so any win must be worth more.
    assert update_score(0, "Win", attempt_number=20, range_size=2) > 0

def test_wider_range_is_worth_more():
    easy = update_score(0, "Win", attempt_number=1, range_size=20)
    hard = update_score(0, "Win", attempt_number=1, range_size=200)
    assert easy < 100 < hard
