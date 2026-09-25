# Annotator prompt (published verbatim; DESIGN §3.5)

You are labelling requests to a small app with the ONE call multiset the app should execute, or nothing.
The ground truth is the written contract, not your guess about what a model would do.

Read `production/needle3/contracts/CONTRACT.md` in full first (§0 gold format, §1 rules R1-R8, §2 the
home app, §3 the desk app). Label only against the MAIN contract (not the §4 variants). Read nothing else
in the repository besides the contract and your batch file; do not look at any model output or any other
annotator's work.

For every line of your batch file (`{"id", "app", "text"}`) write one JSON line:
`{"id": ..., "gold": <list of acceptable answers, or "ambiguous">, "stratum": "A1"|"A2"|"A3"|"N1"|"N2"|"N3", "rule": "<the contract rule or section that decides it, in a few words>"}`
- `gold` format exactly as CONTRACT §0: e.g. `[[{"action": "light_power", "args": {"room": "kitchen", "state": "off"}}]]`,
  `[[]]` for "do nothing", two answers only under R7. Canonical action and argument names and values only
  (e.g. room "here", colour "warm white", list "to-do", time "07:00", date "2026-06-11"). Write every
  argument that has a value, including declared defaults (room "here", reminder time "09:00", the
  next-occurrence date).
- `stratum`: A1 direct, fully specified request the app serves; A2 indirect, conversational or relative
  wording the app still serves; A3 a normalisation (units, number words, times, dates) or two actions,
  served; N1 a capability, entity or value the app does not have; N2 missing required information or
  genuinely ambiguous; N3 negation, quotation, reported speech, conditional, question about state.
- `"ambiguous"` only when the contract genuinely does not decide the item; say why in `rule`.
Work item by item; do not batch-guess. Write the output file named in your instructions, with exactly one
line per input line, same ids. Do not commit.
