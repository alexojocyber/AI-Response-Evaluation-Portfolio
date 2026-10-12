# NNN: Short title of the task

| | |
|---|---|
| **Domain** | e.g. Linux security, Networking, Python code review |
| **Task type** | Pairwise comparison / Single response rating / Code review |
| **Response A** | Model and version, e.g. ChatGPT (GPT-x), default settings |
| **Response B** | Model and version, e.g. Gemini (x.x), default settings |
| **Tools enabled** | e.g. none / web search / code execution |
| **Date** | YYYY-MM-DD |

Both models received the identical prompt, and outputs are pasted verbatim.

## Prompt

> Paste the exact prompt given to both models.

## Response A

> Paste Response A exactly as written. Don't fix anything.

## Response B

> Paste Response B exactly as written.

## Scores

| Dimension | A | B |
|---|---|---|
| Correctness | | |
| Completeness | | |
| Safety | | |
| Instruction following | | |
| Clarity | | |
| Code quality *(if code)* | | |

## Issues found

| Response | Severity | Quote | Problem | Evidence |
|---|---|---|---|---|
| A | Major | "exact words" | What's wrong and what it does to the user | **Documented:** link / **Executed:** command and output / **Reasoned:** why |

## Verdict

**Preferred: A / B**, by a small / clear / wide margin.

One short paragraph a non-expert could follow: which one is better and the deciding reason. Say what evidence would change the verdict, if anything.

## Suggested ideal response

What a 5/5 answer would have done differently. Keep it short.

## Verification

How you checked the claims: which docs, which commands you ran, or which script in `scripts/`.

For code, list the test cases:

| Case | Expected | A | B |
|---|---|---|---|
| Happy path | | | |
| Edge case | | | |
| Invalid input | | | |

---

**Before publishing, check:** same rubric applied to both; scores not swayed by length, formatting or model brand; verdict follows from the issues table; every issue has an evidence label.
