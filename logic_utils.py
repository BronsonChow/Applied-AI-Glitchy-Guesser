import math

# Scoring rules, used by update_score.
# A first-try win earns MAX_WIN_POINTS; each extra attempt costs
# POINTS_LOST_PER_ATTEMPT, but a win never earns less than MIN_WIN_POINTS.
MAX_WIN_POINTS = 100
POINTS_LOST_PER_ATTEMPT = 10
MIN_WIN_POINTS = 10

# Preset difficulties. Their range and attempts are fixed, and each one
# scales win points by its multiplier.
DIFFICULTY_SETTINGS = {
    "Easy": {"range": (1, 20), "attempts": 10, "multiplier": 0.5},
    "Normal": {"range": (1, 100), "attempts": 8, "multiplier": 1.0},
    "Hard": {"range": (1, 200), "attempts": 5, "multiplier": 1.5},
}
# The player picks the range and attempts; the multiplier is interpolated
# from the presets above (see score_multiplier).
CUSTOM_DIFFICULTY = "Custom"
DEFAULT_DIFFICULTY = "Normal"


#FIX: hard difficulty is harder than normal
def get_range_for_difficulty(difficulty: str):
    """Return (low, high) inclusive range for a given difficulty.

    Custom and unknown difficulties get the default (Normal) range.
    """
    settings = DIFFICULTY_SETTINGS.get(difficulty, DIFFICULTY_SETTINGS[DEFAULT_DIFFICULTY])
    return settings["range"]


def get_attempts_for_difficulty(difficulty: str):
    """Return the attempt limit for a difficulty (Normal's for Custom/unknown)."""
    settings = DIFFICULTY_SETTINGS.get(difficulty, DIFFICULTY_SETTINGS[DEFAULT_DIFFICULTY])
    return settings["attempts"]


def difficulty_rating(range_size: int, attempt_limit: int):
    """How hard a game is: guesses a perfect player needs per attempt allowed.

    A binary search needs about log2(range_size) guesses, so a higher rating
    means less room for mistakes.
    """
    return math.log2(range_size) / attempt_limit


def _preset_anchors():
    """(rating, multiplier) points for each preset, easiest first."""
    anchors = []
    for settings in DIFFICULTY_SETTINGS.values():
        low, high = settings["range"]
        rating = difficulty_rating(high - low + 1, settings["attempts"])
        anchors.append((rating, settings["multiplier"]))
    return sorted(anchors)


def score_multiplier(range_size: int, attempt_limit: int):
    """Score multiplier for any range and attempt limit.

    Presets get exactly their own multiplier. Any other settings get their
    own multiplier, never snapped to a preset's: it is placed on a line
    through the presets by difficulty_rating. Between two presets it is
    interpolated; harder than Hard it keeps rising along the Normal-to-Hard
    slope; easier than Easy it falls toward 0, so trivial custom games
    can't farm points.
    """
    rating = difficulty_rating(range_size, attempt_limit)
    anchors = [(0.0, 0.0)] + _preset_anchors()

    # Pick the segment containing the rating, or the last one to extrapolate.
    for (r0, m0), (r1, m1) in zip(anchors, anchors[1:]):
        if rating <= r1:
            break
    return m0 + (m1 - m0) * (rating - r0) / (r1 - r0)


def closest_difficulty(range_size: int, attempt_limit: int):
    """Name of the preset whose difficulty rating is nearest these settings."""
    rating = difficulty_rating(range_size, attempt_limit)

    def distance(name):
        low, high = DIFFICULTY_SETTINGS[name]["range"]
        preset = difficulty_rating(high - low + 1, DIFFICULTY_SETTINGS[name]["attempts"])
        return abs(rating - preset)

    return min(DIFFICULTY_SETTINGS, key=distance)


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
#FIX: harder settings are worth more points
def update_score(
    current_score: int,
    outcome: str,
    attempt_number: int,
    multiplier: float = 1.0,
):
    """Update score based on outcome, attempt number, and difficulty multiplier.

    Get the multiplier from score_multiplier(range_size, attempt_limit).
    """
    # Wrong guesses are already penalized by the shrinking win bonus,
    # so they don't also subtract points.
    if outcome == "Win":
        points = MAX_WIN_POINTS - POINTS_LOST_PER_ATTEMPT * (attempt_number - 1)
        points = max(points, MIN_WIN_POINTS)
        # Any win earns at least 1 point, so it always beats a loss.
        return current_score + max(round(points * multiplier), 1)

    return current_score
