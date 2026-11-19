# Model Card: Glitchy Guesser

## Limitations

Glitchy Guesser is a rule-based Streamlit game with no AI model of its own. AI (Claude) was used to help fix and test it. The game rules in `logic_utils.py` are covered by 63 pytest tests and 55 built-in edge cases, but the Streamlit UI and session state in `app.py` were only tested by hand, so a UI regression could go unnoticed. Input checking relies on Python's `int()`, so some unusual input is still accepted: full-width digits such as `５` are read as 5. The debug panel hides the secret number unless `?debug=true` is in the address, but it doesn't protect it, since anyone can add that. Custom difficulty multipliers have no upper limit. The AI's suggestions also had limits: they sometimes changed more code than was asked for, so every edit had to be reviewed and tested.

## AI suggestions

**Accepted:** When I asked the AI to stop out-of-range guesses, it also suggested rejecting decimal guesses, because the secret number is always a whole number. I accepted this after reading the code and testing it in the app. A guess like `4.5` now shows "Decimals aren't allowed. Enter a whole number." and doesn't use up an attempt.

**Rejected:** I asked the AI to change the range slider into number input fields. It did, but it also changed the minimum back to 1, which undid an earlier change that allowed negative numbers. I rejected that version and kept negative ranges, which the edge cases now check (for example, `-5` is accepted in a range of -10 to -1).
