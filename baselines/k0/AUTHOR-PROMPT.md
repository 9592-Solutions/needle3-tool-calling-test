# K0 author prompt (published verbatim; DESIGN §4.3)

You are building a keyword-based command parser for two small apps. You are given ONLY each app's tool
schema (JSON, OpenAI function format) and, for the desk app, the fact line the app knows at run time:
`date: 2026-06-10 Wed 14:30; locale: en-US`. You have no example requests and must not look for any:
do not read any other file in the repository, and do not use the web.

Deliverables, in `production/needle3/baselines/k0/`:

1. `triggers_S0.json` and `triggers_S1.json`: for each tool in that schema, up to 15 trigger phrases
   (short phrases a user might say to invoke that tool), `{"<tool name>": ["phrase", ...], ...}`.
   Write them in one pass from the schema; do not iterate against any data.
2. `extractor.py`: a pure-Python (standard library only) rule-based argument extractor with
   `extract(schema_tool: dict, text: str, fact_line: str | None) -> dict | None` returning the
   arguments for that tool, or None when the tool cannot be filled (refuse). Rules it must follow:
   - enum values: gazetteer over the schema's enum values plus synonyms that appear in the schema's own
     descriptions (nothing else); if several match, the one nearest the tool's trigger word;
   - numbers: digits and English number words, with units from the schema; validate ranges from the
     schema; an out-of-range value returns None (refuse), never clamps;
   - on/off, start/stop and similar polar values from a verb lexicon, mapped to the schema's own values;
   - relative words ("up", "down", "brighter", "a bit") map to a value only when the schema has a
     matching enum; otherwise they give no value;
   - free text (item, text): the span after the trigger phrase up to a preposition that introduces
     another argument, or the end, minus tokens already used by other arguments;
   - times as 24-hour HH:MM and dates as YYYY-MM-DD when the schema asks for those formats, resolving
     relative dates and times against the fact line;
   - a required argument that cannot be filled returns None; an optional one with no evidence is omitted
     (never guessed), unless the schema declares a `default`, which may be left out.
   Also `split(text) -> list[str]`: split a request into clauses on a declared conjunction list
   (" and ", " then ", ", then", ";"), so two actions can become two calls.
3. `AUTHOR-NOTES.md`: 10-20 lines on what you did and every choice a reader should know about.

Test the extractor on a handful of utterances YOU make up (not from any dataset) and keep those tests in
`test_extractor.py`. Do not commit; reply with the file paths.
