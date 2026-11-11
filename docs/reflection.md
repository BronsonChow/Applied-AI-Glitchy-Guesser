# 💭 Reflection: Game Glitch Investigator

Answer each question in 3 to 5 sentences. Be specific and honest about what actually happened while you worked. This is about your process, not trying to sound perfect.

## 1. What was broken when you started?

- What did the game look like the first time you ran it?

The game was visually fine, no issues at first. Then, upon further inspection and interactions, the bugs were clear and present.

- List at least two concrete bugs you noticed at the start  
  (for example: "the hints were backwards").

1. The hints did not work properly when given a very large or negative number.
2. The slider would glitch back to the previous stuck position after sliding.

**Bug Reproduction Log**

Document at least 3 bugs you found. Add rows as needed.

| Input | Expected Behavior | Actual Behavior | Console Output / Error |
|-------|-------------------|-----------------|------------------------|
|Guess of -22220|Hint displays "Go HIGHER!"|Hint displays "Go LOWER!"|none|
|Guess of 1.11e+46 expanded form|Hint displays "Go LOWER!"|Hint displays "Go HIGHER!"|none|
|New Game button pressed|Attempts and states reset|Nothing is reset|none|

---

## 2. How did you use AI as a teammate?

- Which AI tools did you use on this project (for example: ChatGPT, Gemini, Copilot)?

Claude Opus 5.5

- Give one example of an AI suggestion that was correct (including what the AI suggested and how you verified the result).

The AI suggested that guess attempts should not allow decimals when I prompted it to disallow numbers out of bounds. This was a correct deduction from the AI since the guessing game was only allowing integers as the secret value. I verified the result by checking over the code and also testing the application.

- Give one example of an AI suggestion you did not accept as written (including what the AI suggested, why you rejected or changed it, and how you verified your version). It does not have to be a suggestion that was wrong: over-engineered, out of scope, harder to read, or a poor fit for this codebase all count.

I prompted the AI to make the secret value range to be a slider and it properly did that. Then I asked it to allow negative numbers and it also properly did that. When I then asked it to make it an input field instead, it reverted the negative numbers as the minimum back to 1. I did not accept this, and rejected the change.

---

## 3. Debugging and testing your fixes

- How did you decide whether a bug was really fixed?

I decided a bug was fixed when I inspected the code and saw that it only changed the portion that I asked it to. Then I manually tested that specific function in the application and if it performed as I expected, then I considered it fixed.

- Describe at least one test you ran (manual or using pytest)
  and what it showed you about your code.

I ran tests using edge cases such as when I manually input extreme numbers such as 2222222 or -2222222 and it would display the correct hint that my guess was out of bounds.

- Did AI help you design or understand any tests? How?

The AI helped me with debugging logs essentially. It generated test cases and also errors if there was any. This way I can quickly check where the errors are occurring, whether it was a syntax/logic code error or an error with the directories not having required files.

---

## 4. What did you learn about Streamlit and state?

- How would you explain Streamlit "reruns" and session state to a friend who has never used Streamlit?

Streamlit is very smooth for the most part. There was a small niche bug that took the AI a bit to figure out which was the delay that would allow the slider to dynamically change the website. But the way that streamlit works, the solution was not recommended by the AI.

---

## 5. Looking ahead: your developer habits

- What is one habit or strategy from this project that you want to reuse in future labs or projects?
  - This could be a testing habit, a prompting strategy, or a way you used Git.
 
The strategy that I would reuse is to first manually test the application and fix any apparent bugs. Then, after all the bugs that I could manually find are found, I would ask the AI to list any logic errors there could be. This would sift through bugs that went past me.

- What is one thing you would do differently next time you work with AI on a coding task?

I would refrain from asking it too much in a single prompt. I would keep it simple when asking to fix bugs and be very specific in what is to be changed.

- In one or two sentences, describe how this project changed the way you think about AI generated code.

This project made me appreciate how quickly AI can detect and fix errors. It does need some fine tuning to achieve the desired result but it is still impressive in it's own right.
