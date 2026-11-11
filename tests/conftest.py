"""Pytest configuration for this project.

Writes the outcome of the latest test run to test-results/test_results.txt,
replacing the previous contents. Commit the file alongside code changes to
record outcomes; git history keeps the earlier runs. No extra flags needed --
it happens on any `pytest` invocation.
"""

import os
import sys
from datetime import datetime

import pytest

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RESULTS_DIR = os.path.join(PROJECT_ROOT, "test-results")
RESULTS_FILE = os.path.join(RESULTS_DIR, "test_results.txt")

LINE_WIDTH = 78

# Collected (nodeid, outcome, duration, detail) tuples for the current session.
_records = []


def _first_error_line(report):
    """Pull the most useful one-line explanation out of a failure report."""
    text = report.longreprtext or ""

    # Assertion output marks the actual error lines with a leading "E".
    error_lines = [
        line[1:].strip()
        for line in text.splitlines()
        if line.startswith("E ") or line.strip() == "E"
    ]
    if error_lines:
        return next((line for line in error_lines if line), "")

    for line in reversed(text.splitlines()):
        if line.strip():
            return line.strip()
    return ""


def pytest_runtest_logreport(report):
    if report.when == "call":
        if report.passed:
            _records.append((report.nodeid, "PASSED", report.duration, ""))
        elif report.failed:
            _records.append(
                (report.nodeid, "FAILED", report.duration, _first_error_line(report))
            )
        elif report.skipped:
            _records.append((report.nodeid, "SKIPPED", report.duration, ""))
        return

    # Failures outside the test body itself (fixture errors, teardown errors).
    if report.failed:
        _records.append(
            (
                report.nodeid,
                "ERROR ({})".format(report.when),
                report.duration,
                _first_error_line(report),
            )
        )
    elif report.skipped and report.when == "setup":
        _records.append((report.nodeid, "SKIPPED", report.duration, ""))


def pytest_sessionfinish(session, exitstatus):
    os.makedirs(RESULTS_DIR, exist_ok=True)

    counts = {}
    for _, outcome, _, _ in _records:
        key = outcome.split(" ")[0]
        counts[key] = counts.get(key, 0) + 1

    summary = ", ".join(
        "{} {}".format(counts[key], key.lower())
        for key in ("PASSED", "FAILED", "ERROR", "SKIPPED")
        if key in counts
    ) or "no tests ran"

    invocation = " ".join(session.config.invocation_params.args) or "(all tests)"
    name_width = max((len(name) for name, _, _, _ in _records), default=0)
    outcome_width = max((len(outcome) for _, outcome, _, _ in _records), default=0)

    lines = [
        "=" * LINE_WIDTH,
        "Test run: {}".format(datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
        "Target:   pytest {}".format(invocation),
        "Versions: python {} | pytest {}".format(
            sys.version.split()[0], pytest.__version__
        ),
        "-" * LINE_WIDTH,
    ]

    if _records:
        for nodeid, outcome, duration, detail in _records:
            lines.append(
                "{:<{ow}}  {:<{nw}}  {:>7.3f}s".format(
                    outcome, nodeid, duration, ow=outcome_width, nw=name_width
                )
            )
            if detail:
                lines.append("{}-> {}".format(" " * (outcome_width + 2), detail))
    else:
        lines.append("No tests were collected or run.")

    lines.append("-" * LINE_WIDTH)
    lines.append("Result: {} (exit status {})".format(summary, int(exitstatus)))
    lines.append("")

    # Overwrite rather than append: the file holds only the latest run, so it
    # stays small. Earlier outcomes are kept in git history.
    with open(RESULTS_FILE, "w", encoding="utf-8") as handle:
        handle.write("\n".join(lines) + "\n")

    _records.clear()
