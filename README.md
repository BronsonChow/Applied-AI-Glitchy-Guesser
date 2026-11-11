# 🎮 Game Glitch Investigator: The Impossible Guesser

## 🚨 The Situation

You asked an AI to build a simple "Number Guessing Game" using Streamlit.
It wrote the code, ran away, and now the game is unplayable. 

- You can't win.
- The hints lie to you.
- The secret number seems to have commitment issues.

## 🛠️ Setup

1. Install dependencies: `pip install -r requirements.txt`
2. Run the broken app: `python -m streamlit run app.py`

## 🕵️‍♂️ Your Mission

1. **Play the game.** Add `?debug=true` to the address to see the secret number. Try to win.
2. **Find the State Bug.** Why does the secret number change every time you click "Submit"? Ask ChatGPT: *"How do I keep a variable from resetting in Streamlit when I click a button?"*
3. **Fix the Logic.** The hints ("Higher/Lower") are wrong. Fix them.
4. **Refactor & Test.** - Move the logic into `logic_utils.py`.
   - Run `pytest` in your terminal.
   - Keep fixing until all tests pass!

## 📝 Document Your Experience

My full write-up of the project is in [docs/reflection.md](docs/reflection.md).

- [ ] Describe the game's purpose.

The game is trying to guess a number using a limited number of guesses. If done correctly, it is near 100% to always guess the correct number.
- [ ] Detail which bugs you found.

1. Delay when submitting a guess
2. Could not press enter to submit a guess
3. Disallowing repeat/out of bounds/decimal values
4. Game logic lives in logic_utils.py
5. Test results differed from expected return value
6. Whitespaces in guesses
7. Debug panel shown immediately
8. Hint was hiding win message
9. Old guesses were not cleared when inputting a new range
- [ ] Explain what fixes you applied.

I applied all that I deemed were a necessary or valuable enough fix. This includes all the fixes that were listed above.

I also made these changes so the game logic is easier to test and change later:

- **Guess validation moved to `logic_utils.py`.** The range check and the repeat-guess check now live in `validate_guess()`, next to `parse_guess()` and `check_guess()`, so they can be tested without running the app.
- **Scoring rules have names.** The numbers used for scoring are constants at the top of `logic_utils.py`, so you can change the scoring in one place:

  | Constant | Value | Meaning |
  |---|---|---|
  | `MAX_WIN_POINTS` | 100 | Points for a first-try win |
  | `POINTS_LOST_PER_ATTEMPT` | 10 | Points lost for each extra guess |
  | `MIN_WIN_POINTS` | 10 | Fewest points a win can earn |

  Each difficulty's range, attempts and score multiplier are in `DIFFICULTY_SETTINGS` in the same file.

- **Locked difficulties and a Custom mode.** Easy, Normal and Hard now have a fixed range and number of attempts. The new **Custom** difficulty lets you choose your own, and scores according to how close your settings are to the three presets (see step 2 of the walkthrough).
- **More tests.** Every function in `logic_utils.py` now has tests (51 in total).
- **Test results file stays small.** `test-results/test_results.txt` now holds only the latest test run instead of every run. Earlier results are kept in git history.

## 🗺️ Architecture

![Architecture diagram](docs/assets/architecture.png)

`app.py` draws the page with Streamlit and keeps the game state in `st.session_state`. All game rules live in `logic_utils.py`, which `tests/test_game_logic.py` tests. `tests/conftest.py` writes each test run's results to `test-results/test_results.txt`.

The diagram source is in [docs/diagrams/architecture.mmd](docs/diagrams/architecture.mmd). You can paste it into [mermaid.live](https://mermaid.live) to edit it.

## 📸 Demo Walkthrough

Describe your fixed game in numbered steps so a reader can follow along without watching a video:

1. **Start the game.** Run `python -m streamlit run app.py`. The game opens in your browser at `http://localhost:8501`.
2. **Pick a difficulty** in the sidebar. Easy, Normal and Hard have a fixed range and number of attempts, which you can see but not change:

   | Difficulty | Range | Attempts | Score multiplier |
   |---|---|---|---|
   | Easy | 1–20 | 10 | 0.50x |
   | Normal | 1–100 | 8 | 1.00x |
   | Hard | 1–200 | 5 | 1.50x |
   | Custom | you choose | you choose | depends on your settings |

   **Custom** lets you type your own **Min**, **Max** (up to 1000) and **Attempts allowed** (1 to 20). It starts from Normal's settings. Custom gets its own multiplier, calculated from how hard your settings are compared with the three presets. It is never rounded to a preset's multiplier:
   - The game rates difficulty as *guesses a perfect player needs* (about log2 of the range size) divided by *attempts allowed*.
   - If your rating falls between two presets, your multiplier falls between theirs. For example, 1–150 with 6 attempts is between Normal and Hard and earns 1.27x.
   - Settings harder than Hard keep earning more, with no cap. For example, 1–1000 with 3 attempts earns 2.78x.
   - Settings easier than Easy earn less than 0.50x, so a 1–2 range with 20 attempts is worth almost nothing (0.06x).
   - The sidebar shows your multiplier and which preset your difficulty is most similar to, as a guide only.

   Changing difficulty or any Custom setting starts a new game, clears the guess box and shows "New game started."
3. **Make a guess.** Type a whole number and press **Enter** or click **Submit Guess 🚀**. These guesses are rejected with a message and *don't* use up an attempt:
   - an empty guess, or one with only spaces
   - text, like `abc`
   - decimals, like `4.5`
   - a number outside the range
   - a number you've already guessed
4. **Follow the hints.** After each wrong guess the game says **📉 Go LOWER!** or **📈 Go HIGHER!**, and the "Attempts left" counter goes down by one. Every guess so far is listed in the **Your guesses** box. Untick **Show hint** to play without hints.
5. **Win.** Guess the secret number to get balloons and a message like "🎉 Correct! You won! The secret was 57. Final score: 90". You still see this message with hints turned off.
   - A first-try win is worth 100 points. Each extra guess costs 10 points, down to a minimum of 10.
   - Those points are multiplied by the difficulty's multiplier: a first-try win scores 50 on Easy, 100 on Normal and 150 on Hard.
6. **Or lose.** If you run out of attempts, the game shows the secret number and you score 0. A win always scores more than a loss.
7. **Play again.** Click **New Game 🔁** for a new secret number. Your attempts and score reset and the guess box is cleared.
8. **(Optional) Peek at the secret.** Add `?debug=true` to the address, e.g. `http://localhost:8501/?debug=true`, to show the **Developer Debug Info** panel. It shows the secret number, attempts, score, difficulty, score multiplier and guess history.

**Screenshot** *(optional)*: <!-- Insert a screenshot of your fixed, winning game here -->

## 🧪 Test Results

```
$ python -m pytest tests/
============================= test session starts =============================
platform win32 -- Python 3.14.3, pytest-9.1.1, pluggy-1.6.0
collected 51 items

tests\test_game_logic.py ............................................... [ 92%]
....                                                                     [100%]

============================= 51 passed in 0.09s ==============================
```

| Function | Tests |
|---|---|
| `get_range_for_difficulty` | 6 |
| `is_float` | 2 |
| `parse_guess` | 7 |
| `validate_guess` | 8 |
| `check_guess` | 3 |
| `update_score` | 6 |
| `get_attempts_for_difficulty` (and Custom defaults) | 2 |
| `score_multiplier` | 13 |
| `closest_difficulty` | 4 |

Each run's full results, one line per test, are written to [test-results/test_results.txt](test-results/test_results.txt).

## 🚀 Stretch Features

The log of AI interactions for stretch features is in [docs/ai_interactions.md](docs/ai_interactions.md).

- [ ] [If you choose to complete Challenge 4, describe the Enhanced UI changes here — a screenshot is optional]
