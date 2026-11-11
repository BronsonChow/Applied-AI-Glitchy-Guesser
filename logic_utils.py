import math

# Scoring rules, used by update_score.
# A first-try win earns MAX_WIN_POINTS; each extra attempt costs
# POINTS_LOST_PER_ATTEMPT, but a win never earns less than MIN_WIN_POINTS.
MAX_WIN_POINTS = 100
POINTS_LOST_PER_ATTEMPT = 10
MIN_WIN_POINTS = 10
# Win points are scaled by log2(range size) relative to this range size,
# so a 1-100 game is worth 1x, wider ranges more, narrower ranges less.
BASELINE_RANGE_SIZE = 100


#FIX: hard difficulty is harder than normal
def get_range_for_difficulty(difficulty: str):
    """Return (low, high) inclusive range for a given difficulty."""
    if difficulty == "Easy":
        return 1, 20
    if difficulty == "Normal":
        return 1, 100
    if difficulty == "Hard":
        return 1, 200
    return 1, 100


def is_float(raw: str):
    try:
        float(raw)
    except ValueError:
        return False
    return True


def parse_guess(raw: str):
    """
    Parse user input into an int guess.

    Returns: (ok: bool, guess_int: int | None, error_message: str | None)
    """
    if raw is None:
        return False, None, "Enter a guess."

    #FIX: whitespace-only input counts as empty
    if raw.strip() == "":
        return False, None, "Enter a guess."

    try:
        value = int(raw)
    except ValueError:
        if "." in raw and is_float(raw):
            return False, None, "Decimals aren't allowed. Enter a whole number."
        return False, None, "That is not a number."

    return True, value, None


def validate_guess(guess: int, low: int, high: int, history):
    """
    Check a parsed guess against the game's range and previous guesses.

    Returns: (ok: bool, error_message: str | None)
    """
    if not low <= guess <= high:
        return False, f"Your guess must be between {low} and {high}."
    if guess in history:
        return False, f"You already guessed {guess}. Try a different number."
    return True, None


def check_guess(guess, secret):
    """
    Compare guess to secret and return (outcome, message).

    outcome examples: "Win", "Too High", "Too Low"
    """
    if guess == secret:
        return "Win", "🎉 Correct!"

    if guess > secret:
        return "Too High", "📉 Go LOWER!"
    return "Too Low", "📈 Go HIGHER!"


#FIX: winning always scores more than losing
#FIX: wider ranges are worth more points
def update_score(
    current_score: int,
    outcome: str,
    attempt_number: int,
    range_size: int = BASELINE_RANGE_SIZE,
):
    """Update score based on outcome, attempt number, and range size."""
    # Wrong guesses are already penalized by the shrinking win bonus,
    # so they don't also subtract points.
    if outcome == "Win":
        points = MAX_WIN_POINTS - POINTS_LOST_PER_ATTEMPT * (attempt_number - 1)
        points = max(points, MIN_WIN_POINTS)
        # Scaled by how many guesses the range needs.
        multiplier = math.log2(range_size) / math.log2(BASELINE_RANGE_SIZE)
        return current_score + round(points * multiplier)

    return current_score
