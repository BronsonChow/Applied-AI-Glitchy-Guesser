"""Edge-case checker for Glitchy Guesser.

Runs the game's rules from logic_utils.py against edge cases and prints a
pass rate. It doesn't need Streamlit or a browser.

    python edge_cases.py                          # built-in edge cases
    python edge_cases.py --file tests/edge_cases.csv
    python edge_cases.py --interactive            # type cases one at a time
    python edge_cases.py --interactive --save my_cases.csv

Run `python edge_cases.py --help` for every option.

Guess cases use these expected results:
    reject  the game refuses the guess and no attempt is used
    accept  the game takes the guess (any hint)
    win     the guess matches the secret
    higher  the hint says "Go HIGHER!" (the guess is below the secret)
    lower   the hint says "Go LOWER!"  (the guess is above the secret)
win, higher and lower need a secret number.
"""

import argparse
import csv
import os
import sys
from dataclasses import dataclass
from typing import Callable

from logic_utils import (
    DEFAULT_DIFFICULTY,
    DIFFICULTY_SETTINGS,
    MAX_WIN_POINTS,
    MIN_WIN_POINTS,
    check_guess,
    closest_difficulty,
    get_attempts_for_difficulty,
    get_range_for_difficulty,
    parse_guess,
    score_multiplier,
    update_score,
    validate_guess,
)

GUESS_RESULTS = ("reject", "accept", "win", "higher", "lower")
HINT_RESULTS = {"Win": "win", "Too High": "lower", "Too Low": "higher"}
CSV_COLUMNS = ["input", "expected", "low", "high", "history", "secret", "note"]
LINE_WIDTH = 78


@dataclass
class Case:
    category: str
    name: str
    expected: object
    # Returns (actual result, short detail shown next to it).
    run: Callable[[], tuple]


@dataclass
class Result:
    case: Case
    passed: bool
    actual: object
    detail: str


# --------------------------------------------------------------------------
# Running one guess through the game's rules, the same way app.py does.
# --------------------------------------------------------------------------

def play_guess(raw, low, high, history=(), secret=None):
    """Return (result, message) for one guess, using a GUESS_RESULTS name."""
    ok, guess, err = parse_guess(raw)
    if ok:
        ok, err = validate_guess(guess, low, high, list(history))
    if not ok:
        return "reject", err
    if secret is None:
        return "accept", f"accepted as {guess}"
    outcome, message = check_guess(guess, secret)
    return HINT_RESULTS[outcome], message


def guess_case(category, name, raw, expected, low, high, history=(), secret=None):
    """Build a Case that plays one guess and compares it with `expected`."""
    if expected not in GUESS_RESULTS:
        raise ValueError(
            f"expected must be one of {', '.join(GUESS_RESULTS)}, not {expected!r}"
        )
    if expected in ("win", "higher", "lower") and secret is None:
        raise ValueError(f"expected '{expected}' needs a secret number")

    def run():
        actual, message = play_guess(raw, low, high, history, secret)
        # "accept" means any hint, so collapse the hint to "accept".
        if expected == "accept" and actual in ("win", "higher", "lower"):
            actual = "accept"
        return actual, message

    settings = f"{low}..{high}"
    if history:
        settings += f", guessed {' '.join(map(str, history))}"
    if secret is not None:
        settings += f", secret {secret}"
    label = f"{name}  [{raw!r} in {settings}]" if name else f"{raw!r} in {settings}"
    return Case(category, label, expected, run)


def value_case(category, name, func, *args, expected, **kwargs):
    """Build a Case that calls func(*args, **kwargs) and compares the return."""
    def run():
        return func(*args, **kwargs), ""
    return Case(category, name, expected, run)


# --------------------------------------------------------------------------
# Built-in edge cases.
# --------------------------------------------------------------------------

def builtin_cases():
    low, high = get_range_for_difficulty(DEFAULT_DIFFICULTY)
    g = "Guess input"
    v = "Range and repeats"
    h = "Hints"
    s = "Scoring"
    d = "Difficulty settings"

    def multiplier_of(name):
        lo, hi = DIFFICULTY_SETTINGS[name]["range"]
        return round(score_multiplier(hi - lo + 1, DIFFICULTY_SETTINGS[name]["attempts"]), 6)

    cases = [
        # What the player types.
        guess_case(g, "empty input", "", "reject", low, high),
        guess_case(g, "only spaces", "   ", "reject", low, high),
        guess_case(g, "tab and newline", "\t\n", "reject", low, high),
        guess_case(g, "spaces around a number", "  42  ", "accept", low, high),
        guess_case(g, "letters", "abc", "reject", low, high),
        guess_case(g, "number then letters", "42abc", "reject", low, high),
        guess_case(g, "decimal", "4.5", "reject", low, high),
        guess_case(g, "whole number written as decimal", "5.0", "reject", low, high),
        guess_case(g, "trailing dot", "5.", "reject", low, high),
        guess_case(g, "scientific notation", "1e2", "reject", low, high),
        guess_case(g, "hex", "0x10", "reject", low, high),
        guess_case(g, "plus sign", "+5", "accept", low, high),
        guess_case(g, "leading zeros", "007", "accept", low, high),
        guess_case(g, "digit separator", "1_0", "reject", low, high),
        guess_case(g, "two numbers", "4 5", "reject", low, high),
        guess_case(g, "comma thousands", "1,000", "reject", low, high),
        guess_case(g, "infinity", "inf", "reject", low, high),
        guess_case(g, "not a number", "nan", "reject", low, high),
        guess_case(g, "huge number", "9" * 50, "reject", low, high),

        # Range limits and repeated guesses.
        guess_case(v, "lowest allowed", str(low), "accept", low, high),
        guess_case(v, "highest allowed", str(high), "accept", low, high),
        guess_case(v, "one below range", str(low - 1), "reject", low, high),
        guess_case(v, "one above range", str(high + 1), "reject", low, high),
        guess_case(v, "negative", "-5", "reject", low, high),
        guess_case(v, "negative range", "-5", "accept", -10, -1),
        guess_case(v, "minus zero", "-0", "accept", 0, 10),
        guess_case(v, "two-number range", "2", "accept", 1, 2),
        guess_case(v, "repeat guess", "50", "reject", low, high, history=[50]),
        guess_case(v, "repeat with spaces", " 50 ", "reject", low, high, history=[50]),
        guess_case(v, "repeat written as 050", "050", "reject", low, high, history=[50]),
        guess_case(v, "new guess after others", "51", "accept", low, high, history=[50, 52]),

        # Higher/lower hints.
        guess_case(h, "exact match", "50", "win", low, high, secret=50),
        guess_case(h, "one below secret", "49", "higher", low, high, secret=50),
        guess_case(h, "one above secret", "51", "lower", low, high, secret=50),
        guess_case(h, "secret at the minimum", str(low), "win", low, high, secret=low),
        guess_case(h, "secret at the maximum", str(high), "win", low, high, secret=high),
        guess_case(h, "lowest guess, secret at max", str(low), "higher", low, high, secret=high),
        guess_case(h, "highest guess, secret at min", str(high), "lower", low, high, secret=low),

        # Scoring.
        value_case(s, "first-try win", update_score, 0, "Win", 1, expected=MAX_WIN_POINTS),
        value_case(s, "wrong guess scores nothing", update_score, 0, "Too High", 1, expected=0),
        value_case(s, "loss keeps the current score", update_score, 30, "Too Low", 8, expected=30),
        value_case(s, "very late win hits the minimum", update_score, 0, "Win", 50,
                   expected=MIN_WIN_POINTS),
        value_case(s, "win with 0x multiplier still earns 1", update_score, 0, "Win", 1,
                   multiplier=0.0, expected=1),
        value_case(s, "Hard first-try win", update_score, 0, "Win", 1,
                   multiplier=1.5, expected=150),
        value_case(s, "unknown outcome scores nothing", update_score, 10, "Draw", 1, expected=10),

        # Difficulty settings.
        value_case(d, "Easy multiplier", multiplier_of, "Easy", expected=0.5),
        value_case(d, "Normal multiplier", multiplier_of, "Normal", expected=1.0),
        value_case(d, "Hard multiplier", multiplier_of, "Hard", expected=1.5),
        Case(d, "smallest Custom game (1..2, 20 attempts) is worth under 0.1x", True,
             lambda: (score_multiplier(2, 20) < 0.1, f"{score_multiplier(2, 20):.3f}x")),
        Case(d, "hardest Custom game (1..1000, 1 attempt) beats Hard", True,
             lambda: (score_multiplier(1000, 1) > 1.5, f"{score_multiplier(1000, 1):.3f}x")),
        Case(d, "range of 1 number gives 0x, not an error", 0.0,
             lambda: (score_multiplier(1, 5), "")),
        value_case(d, "unknown difficulty uses Normal range", get_range_for_difficulty,
                   "Impossible", expected=get_range_for_difficulty("Normal")),
        value_case(d, "Custom uses Normal attempts", get_attempts_for_difficulty,
                   "Custom", expected=get_attempts_for_difficulty("Normal")),
        value_case(d, "closest preset to 1..1000, 1 attempt", closest_difficulty,
                   1000, 1, expected="Hard"),
        value_case(d, "closest preset to 1..2, 20 attempts", closest_difficulty,
                   2, 20, expected="Easy"),
    ]
    return cases


# --------------------------------------------------------------------------
# Cases from a CSV file.
# --------------------------------------------------------------------------

def _int_or_default(text, default, column, line):
    text = (text or "").strip()
    if text == "":
        return default
    try:
        return int(text)
    except ValueError:
        raise ValueError(f"line {line}: {column} must be a whole number, not {text!r}")


def load_csv_cases(path, default_low, default_high):
    """Read guess cases from a CSV file with the columns in CSV_COLUMNS.

    Only `input` and `expected` are required. Blank low/high use the
    --difficulty range. history is space-separated numbers. Lines starting
    with # are comments.
    """
    with open(path, newline="", encoding="utf-8") as handle:
        lines = [
            (number, text)
            for number, text in enumerate(handle, start=1)
            if text.strip() and not text.lstrip().startswith("#")
        ]
    if not lines:
        return []

    reader = csv.DictReader(text for _, text in lines)
    missing = {"input", "expected"} - set(reader.fieldnames or [])
    if missing:
        raise ValueError(f"{path}: header needs the columns {', '.join(sorted(missing))}")

    category = f"File: {os.path.basename(path)}"
    cases = []
    # The header is lines[0], so row i comes from lines[i + 1].
    for (line, _), row in zip(lines[1:], reader):
        expected = (row.get("expected") or "").strip().lower()
        low = _int_or_default(row.get("low"), default_low, "low", line)
        high = _int_or_default(row.get("high"), default_high, "high", line)
        secret = _int_or_default(row.get("secret"), None, "secret", line)
        history_text = (row.get("history") or "").split()
        history = [_int_or_default(n, None, "history", line) for n in history_text]
        try:
            case = guess_case(category, (row.get("note") or "").strip(),
                              row.get("input") or "", expected,
                              low, high, history, secret)
        except ValueError as error:
            raise ValueError(f"{path} line {line}: {error}")
        cases.append(case)
    return cases


# --------------------------------------------------------------------------
# Running and reporting.
# --------------------------------------------------------------------------

def run_case(case):
    try:
        actual, detail = case.run()
    except Exception as error:  # A crash is a failed edge case, not a crash of this tool.
        return Result(case, False, f"crashed: {type(error).__name__}", str(error))
    return Result(case, actual == case.expected, actual, detail)


def print_result(result):
    status = "PASS" if result.passed else "FAIL"
    print(f"  {status}  {result.case.name}")
    if result.passed:
        if result.detail:
            print(f"        -> {result.actual}: {result.detail}")
    else:
        print(f"        expected {result.case.expected!r}, got {result.actual!r}")
        if result.detail:
            print(f"        game said: {result.detail}")


def percent(passed, total):
    return 100.0 * passed / total if total else 0.0


def print_summary(results):
    if not results:
        print("No cases were run.")
        return

    print()
    print("-" * LINE_WIDTH)
    print("Summary by category")
    categories = list(dict.fromkeys(r.case.category for r in results))
    width = max(len(c) for c in categories)
    for category in categories:
        group = [r for r in results if r.case.category == category]
        passed = sum(r.passed for r in group)
        print(f"  {category:<{width}}  {passed:>3}/{len(group):<3}  "
              f"{percent(passed, len(group)):6.1f}%")

    passed = sum(r.passed for r in results)
    failed = [r for r in results if not r.passed]
    print("-" * LINE_WIDTH)
    print(f"Result: {passed}/{len(results)} edge cases passed "
          f"({percent(passed, len(results)):.1f}%)")
    if failed:
        print("Failed:")
        for r in failed:
            print(f"  - [{r.case.category}] {r.case.name}")
    print("=" * LINE_WIDTH)


def run_cases(cases, failures_only=False):
    results = []
    current = None
    for case in cases:
        result = run_case(case)
        results.append(result)
        if failures_only and result.passed:
            continue
        if case.category != current:
            current = case.category
            print()
            print(current)
        print_result(result)
    return results


# --------------------------------------------------------------------------
# Interactive mode.
# --------------------------------------------------------------------------

INTERACTIVE_HELP = """\
Type a guess to test it, then what you expect the game to do.
Expected results: reject, accept, win, higher, lower (Enter = accept)

Commands:
  :range LOW HIGH     set the range (now {low}..{high})
  :secret N           set the secret, so win/higher/lower can be tested
  :secret off         clear the secret
  :history N N ...    numbers already guessed (empty to clear)
  :quote TEXT         test TEXT exactly, even if it starts with ':' or is 'q'
  :help               show this help
  q                   finish and show the pass rate
"""


def interactive(low, high, save_path=None):
    state = {"low": low, "high": high, "secret": None, "history": []}
    results = []
    saved_rows = []

    def settings_text():
        text = f"range {state['low']}..{state['high']}"
        if state["history"]:
            text += f", guessed {' '.join(map(str, state['history']))}"
        text += f", secret {state['secret']}" if state["secret"] is not None else ", no secret"
        return text

    print(INTERACTIVE_HELP.format(**state))
    while True:
        try:
            raw = input(f"guess ({settings_text()})> ")
        except EOFError:
            print()
            break
        if raw.strip().lower() in ("q", "quit", "exit"):
            break

        if raw.startswith(":") and not raw.startswith(":quote "):
            command, *args = raw[1:].split() or [""]
            try:
                if command == "range" and len(args) == 2:
                    new_low, new_high = int(args[0]), int(args[1])
                    if new_low >= new_high:
                        print("  LOW must be below HIGH.")
                        continue
                    state["low"], state["high"] = new_low, new_high
                elif command == "secret" and args == ["off"]:
                    state["secret"] = None
                elif command == "secret" and len(args) == 1:
                    state["secret"] = int(args[0])
                elif command == "history":
                    state["history"] = [int(n) for n in args]
                elif command == "help":
                    print(INTERACTIVE_HELP.format(**state))
                else:
                    print("  Unknown command. Type :help for the list.")
            except ValueError:
                print("  Numbers must be whole numbers.")
            continue
        if raw.startswith(":quote "):
            raw = raw[len(":quote "):]

        try:
            expected = input("  expected [accept]> ").strip().lower() or "accept"
        except EOFError:
            print()
            break
        try:
            case = guess_case("Interactive", "", raw, expected, state["low"],
                              state["high"], state["history"], state["secret"])
        except ValueError as error:
            print(f"  {error}. Not counted.")
            continue

        result = run_case(case)
        results.append(result)
        print_result(result)
        passed = sum(r.passed for r in results)
        print(f"  running total: {passed}/{len(results)} "
              f"({percent(passed, len(results)):.1f}%)")
        saved_rows.append({
            "input": raw, "expected": expected,
            "low": state["low"], "high": state["high"],
            "history": " ".join(map(str, state["history"])),
            "secret": "" if state["secret"] is None else state["secret"],
            "note": "",
        })

    if save_path and saved_rows:
        new_file = not os.path.exists(save_path) or os.path.getsize(save_path) == 0
        with open(save_path, "a", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=CSV_COLUMNS)
            if new_file:
                writer.writeheader()
            writer.writerows(saved_rows)
        print(f"Saved {len(saved_rows)} case(s) to {save_path}. "
              f"Run them again with: python edge_cases.py --file {save_path}")
    return results


# --------------------------------------------------------------------------
# Command line.
# --------------------------------------------------------------------------

def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Check Glitchy Guesser's game rules against edge cases "
                    "and print a pass rate.",
        epilog="Expected results for guess cases: " + ", ".join(GUESS_RESULTS),
    )
    parser.add_argument("--file", action="append", default=[], metavar="CSV",
                        help="run guess cases from a CSV file (can be repeated)")
    parser.add_argument("--interactive", "-i", action="store_true",
                        help="type guess cases one at a time")
    parser.add_argument("--save", metavar="CSV",
                        help="with --interactive, append your cases to this CSV file")
    parser.add_argument("--builtin", action="store_true",
                        help="also run the built-in cases when using --file or --interactive")
    parser.add_argument("--difficulty", default=DEFAULT_DIFFICULTY,
                        choices=list(DIFFICULTY_SETTINGS),
                        help="range used when a case doesn't give one "
                             f"(default {DEFAULT_DIFFICULTY})")
    parser.add_argument("--failures-only", "-f", action="store_true",
                        help="only list failed cases (the summary still counts all)")
    parser.add_argument("--fail-under", type=float, default=100.0, metavar="PERCENT",
                        help="exit with status 1 if the pass rate is below this "
                             "(default 100)")
    args = parser.parse_args(argv)
    # Hint messages contain emoji, which some Windows consoles can't print.
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(errors="replace")
    if args.save and not args.interactive:
        parser.error("--save only works with --interactive")

    low, high = get_range_for_difficulty(args.difficulty)
    run_builtin = args.builtin or not (args.file or args.interactive)

    cases = builtin_cases() if run_builtin else []
    for path in args.file:
        try:
            cases += load_csv_cases(path, low, high)
        except (OSError, ValueError) as error:
            print(f"Can't read cases: {error}", file=sys.stderr)
            return 2

    print("=" * LINE_WIDTH)
    print("Glitchy Guesser edge cases")
    print("=" * LINE_WIDTH)

    results = run_cases(cases, args.failures_only)
    if args.interactive:
        print()
        results += interactive(low, high, args.save)

    print_summary(results)
    passed = sum(r.passed for r in results)
    return 0 if results and percent(passed, len(results)) >= args.fail_under else 1


if __name__ == "__main__":
    sys.exit(main())
