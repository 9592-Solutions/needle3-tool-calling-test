# Needle 3: the two app contracts (ground truth for every gold label)

Written 2026-09-22 by the configuration lead (session 2537465c), DESIGN.md §2 and §10 step 2.
Written before any request was labelled, from the design and from MASSIVE en-US **train and dev**
only (to see which words people use for rooms, colours, devices and lists). No test material was
read. This file is binding on the gold labels; a change after the custodian starts labelling is
versioned here with a date and a reason, and the custodian is told.

**What this file fixes, and what it does not.** It fixes what each app CAN do, which values exist,
which arguments are required and what the defaults are, the permitted normalisations, and the
outcome for each kind of request. It does not fix how the tools are described to a model: that is
S0 and S1 (`S0/`, `S1/`), which both map onto the canonical actions below (`mapping.py`, total).
Gold is written in the canonical form; the scorer maps every schema's output into it.

## 0. Gold format (all apps, all variants)

```json
{"id": "...", "variant": "main", "gold": [[{"action": "light_power", "args": {"room": "kitchen", "state": "off"}}]]}
```
- `gold` is a list of ACCEPTABLE ANSWERS. Almost always one. Each answer is a call multiset (a list
  compared order-free, duplicates kept). The empty list `[]` is "do nothing".
- More than one acceptable answer only where §1 names the case (rule R7). No other alternatives.
- `"gold": "ambiguous"` when two annotators and the adjudicator cannot reach one answer from this
  contract. Ambiguous items leave the headline and are reported (DESIGN §3.5).
- An argument with a declared default is written with its default VALUE in gold (e.g.
  `"room": "here"`). The scorer treats an omitted argument as equal to its declared default, and
  only then.

## 1. Rules that apply to both apps

- **R1 Atomic rule.** A request the app can only partly serve gets no action: `[]`. This includes
  a supported action plus an unsupported one ("turn off the lights and make coffee"), a supported
  action with an unsupported qualifier (a schedule, a recurrence, a condition, a duration, a
  specific fixture the app cannot address, a relative amount the tool cannot express).
- **R2 Two supported actions** in one request: both calls, as a multiset. The same action applied
  to two targets is two calls ("turn off the kitchen and bedroom lights").
- **R3 Negation, quotation, reported speech, hypotheticals, conditionals, questions about state**
  ("don't turn on the lights", "she said turn on the lights", "what if I turned the lights on",
  "if it gets dark turn on the lights", "are the lights on?"): `[]`.
- **R4 Values must be evidenced or defaulted.** A required argument with no span in the request and
  no declared default: `[]`. A value the app does not have (a room, colour, list the app lacks):
  `[]`. A number outside the declared range: `[]` (never clamped).
- **R5 Permitted normalisations** (declared before dev; the scorer applies them to every arm):
  case and whitespace; number words to digits ("thirty" = 30); "percent" / "per cent" / "%";
  int/float equality (50 = 50.0); the synonym tables in §2 and §3; for free text (§3), lowercase,
  punctuation stripped, collapsed whitespace, a leading article or determiner removed
  (`a, an, the, some, my`) and, for reminder text, a leading `to ` or `about ` removed.
- **R6 Indirect wording is served when it names a state one tool controls** and exactly one
  call follows from it: "it's too dark in the kitchen" is about light, so `light_power(kitchen,
  on)`; "the floor is filthy" is about floors, so `vacuum(start)`. A statement about the user
  rather than a controlled quantity ("time to sleep", "I'm off to work", "I need a wee") does not
  name an action: `[]`.
- **R7 Level implies power.** Where a request asks for a light level AND says "on" ("turn the
  lights on to 50%"), both `[set_light_level]` and `[light_power on, set_light_level]` are accepted.
  This is the only place alternative answers exist.
- **R8 Descriptive words that change nothing** are ignored and do not make a request partial:
  politeness, fillers and wake words ("olly", "please", "can you"), a reason ("so I can read"), an
  alarm's purpose ("for my meeting"; alarms carry no label in this app).

## 2. Home app

The home has these rooms and nothing else: living room, kitchen, bedroom, bathroom, hallway,
study. It has lights in every room (addressed per room, never per fixture), one robot vacuum and
one smart plug. It has no thermostat, blinds, locks, speakers, TV, fan, coffee maker or oven.

| canonical action | arguments | required | default |
|---|---|---|---|
| `light_power` | `room` ∈ ROOMS, `state` ∈ {on, off} | state | room = `here` |
| `set_light_level` | `room` ∈ ROOMS, `level` integer 1..100 (percent) | level | room = `here` |
| `set_light_color` | `room` ∈ ROOMS, `color` ∈ COLORS | color | room = `here` |
| `vacuum` | `command` ∈ {start, stop, dock}, `room` ∈ ROOMS | command | room = `whole house` (start only) |
| `smart_plug` | `state` ∈ {on, off} | state | none |

**ROOMS** = `living room, kitchen, bedroom, bathroom, hallway, study, whole house, here`.
Synonyms (the only ones): living room ← lounge, sitting room; bedroom ← bed room, my bedroom;
hallway ← hall, corridor; whole house ← house, home, the flat, apartment, everywhere, all rooms,
"all the lights" / "every light" when no room is named; here ← in here, this room, the room,
my room. A room word outside ROOMS and its synonyms (garage, porch, garden, balcony, den, office,
dining room, guest room, kids bedroom, basement, patio, game room, media room): `[]` under R4.
Why `here` exists and is the default: 79 of 130 light requests in MASSIVE `iot` test name no room
(DESIGN §2); a real home app acts on the room the speaker is in. This is the frozen
required-argument policy; the room-required alternative is variant V-ROOMREQ (§4).

**Light words**: light, lights, lamp, lamps, lighting, bulbs mean the room's lights. A request that
picks one fixture out of several ("the left light", "the desk lamp", "the lamp next to the sofa",
"the porch light") cannot be addressed by this app: `[]` under R1.

**Levels**: integer 1..100, meaning percent. "full", "max", "maximum", "full brightness", "full
power", "all the way" = 100; "half", "halfway" = 50. A bare number is a percent ("dim to seven" =
7). 0 or "zero" is out of range: `[]`. A relative amount ("by twenty percent", "a bit", "a little
more", "brighter", "dim the lights", "turn the lights down", "too bright") has no absolute value, so
under the main contract it is `[]` (R4). Under V-REL it becomes `adjust_light_level`.

**COLORS** = `red, orange, yellow, green, blue, purple, pink, white, warm white, cool white`.
Synonyms: purple ← violet; warm white ← warm, warmer, warm light, soft white; cool white ← cool,
cooler, cold white, daylight. A named colour with a shade modifier maps to the base colour
("light blue", "dark blue", "bright red", "pale green", "yellowish" → blue, blue, red, green,
yellow). Anything else is not a colour this app has: `[]` (lavender, turquoise, romantic, random,
party mode, reading, dark, softer, vibrant, "something nice").

**Vacuum**: vacuum, robot vacuum, roomba, cleaner, hoover, "clean/vacuum/hoover the <room>".
`start` takes an optional room; `stop` and `dock` ("send it home", "back to its base") take none,
and the scorer ignores a room argument on stop and dock. A surface instead of a room ("the
carpet", "the floor", "the rug") is `start` with the default room. A schedule, time, date or
recurrence ("at one pm", "daily", "tomorrow"): `[]` under R1.

**Smart plug**: plug, smart plug, socket, smart socket, outlet, wemo, power socket, including a
plug named by what is plugged in ("the rice cooker socket"). A request naming only an appliance
("turn on the fan", "turn off the TV", "switch on the charger") does not say it is on the plug:
`[]` under R4.

**Indirect wording** (R6), declared cases: too dark / can't see / dark in here → `light_power(on)`;
too bright → `[]` under main (no level), `adjust_light_level(down)` under V-REL; floor or carpet
dirty, dusty, crumbs → `vacuum(start)` (room if named); cold, warm, hot, stuffy → `[]` (no
thermostat); sleep, bed, leaving, arriving → `[]`.

"turn out the lights" = off. "lights on full" is `set_light_level(100)` with R7.

## 3. Desk app

Fixed facts, sent to every arm as the system fact line
`date: 2026-06-10 Wed 14:30; locale: en-US` (Needle's documented fact format). All relative dates
and times resolve against 2026-06-10 (a Wednesday), 14:30.

| canonical action | arguments | required | default |
|---|---|---|---|
| `set_alarm` | `time` "HH:MM" 24-hour, `date` "YYYY-MM-DD" | time | date = next occurrence of `time` after 2026-06-10 14:30 |
| `remove_alarm` | `time` "HH:MM", `date` "YYYY-MM-DD" | time | date = next occurrence of `time` after now |
| `add_to_list` | `item` free text (one item), `list` ∈ LISTS | item, list | none |
| `remove_from_list` | `item` free text (one item), `list` ∈ LISTS | item, list | none |
| `create_reminder` | `text` free text, `time` "HH:MM", `date` "YYYY-MM-DD" | text | time = 09:00; date = next occurrence of `time` after now |

"Next occurrence after now": today (2026-06-10) if the time is later than 14:30, else tomorrow
(2026-06-11). Gold writes the computed date; an omitted date is equal to it (§0).

**Times.** "seven am" = 07:00, "7:30 pm" = 19:30, "noon" = 12:00, "midnight" = 00:00, "half past
six in the morning" = 06:30, "quarter to eight pm" = 19:45. Time-of-day words fix am/pm: morning =
am; afternoon, evening, tonight = pm; "night" = pm for 7-11 and am for 12-4. A 24-hour form
("19:00", "0700") is exact. **A bare 1-12 hour with no am/pm and no time-of-day word ("at seven",
"five o'clock") is ambiguous: `[]` under R4.** A time-of-day word without a clock time ("in the
morning", "this evening") is not a time: `[]` for alarms (time required); for reminders it is a
vague time, `[]` (R1, a qualifier the tool cannot express).
**Relative times** resolve against 14:30 on 2026-06-10: "in 25 minutes" = 14:55, "in half an hour"
= 15:00, "in two hours" = 16:30, date today. "thirty minutes before my 3 pm meeting tomorrow" =
14:30 on 2026-06-11 (both values stated, so computable).
**Dates.** today = 2026-06-10; tomorrow = 2026-06-11; a weekday name, with or without "next" or
"this", is its first occurrence strictly after today (friday = 2026-06-12, wednesday =
2026-06-17); a month and day, or "the 25th", is its next occurrence on or after today (the 25th =
2026-06-25, "september four" = 2026-09-04). Vague dates ("this weekend", "next week", "later",
"soon", "some time"): `[]` (R1).
**Recurrence** ("every day", "weekdays", "daily"): the app has none: `[]` (R1).

**Alarms** carry no label (R8). "remove my wake up alarm", "turn off my alarms", "delete all
alarms": no time, `[]`. "cancel tomorrow's 7 am alarm" = `remove_alarm(07:00, 2026-06-11)`.
Snooze, alarm sound, alarm volume: `[]`.

**LISTS** = `shopping, to-do, packing`. Synonyms: shopping ← grocery, groceries, shopping list,
grocery list; to-do ← to do, todo, to-do list, things to do, task list, tasks; packing ← packing
list, trip list, travel list. Any other named list (workout, wish list, christmas gift list):
`[]`. **No list named: `[]`** (list is required and has no default; "add butter to the list" is
N2). One item per call: "add milk and eggs to the shopping list" is two `add_to_list` calls (R2).
The item is the request's own words for the thing (R5 normalisation), including quantities ("two
bottles of milk"). Creating, deleting, renaming, reading or clearing a whole list, "the last one",
"everything": `[]`.

**Reminders**: "remind me to", "don't let me forget", "alert me", "set a reminder". `text` is the
span naming what to be reminded of, excluding the reminder phrase and the date/time words ("remind
me to take the bins out on thursday" → text "take the bins out", date 2026-06-11, time 09:00).
Scheduling a calendar EVENT ("schedule a meeting with John at 3", "add dinner with mom to my
calendar", "book time for the dentist") is not a reminder: `[]` under R4, as a capability the app
lacks. A reminder about a named event ("remind me about the dentist tomorrow at 10") is a reminder
(text "the dentist" → normalised "dentist").

**Out of scope** (querying alarms, lists or reminders, timers, weather, messages, music): `[]`.

## 4. Variants (for the diagnostics; same gold format, same rules)

Each variant changes one thing. Gold is written per variant only where the variant changes the
outcome; otherwise the main gold stands.

- **V-REL** (home, DESIGN §5.2): the main home contract, `smart_plug` removed, plus
  `adjust_light_level(room ∈ ROOMS default here, direction ∈ {up, down})` with an app-defined step.
  up ← brighter, brighten, turn up, raise, increase, more light, lights up; down ← dim, dimmer,
  darker, lower, turn down, less bright, too bright. A relative request with an amount ("by twenty
  percent", "by half") is `[]` (the step is the app's, not the user's: R1). Absolute requests stay
  `set_light_level`. **Five tools, not six**: DESIGN §5.2 said "S1 plus" the relative tool, which
  would be six tools and cross the five-tool line where retrieval may engage (facts §3), so the
  contrast would confound the relative tool with the tool count. The plug tool is the one removed
  because it shares no vocabulary with light requests; V-REL is scored only on light items (the A2
  families and matched controls), so its absence changes no gold there. Recorded in DESIGN §5.2.
- **V-ROOMREQ** (home): `room` required with no default in `light_power`, `set_light_level`,
  `set_light_color`; `here` counts only when the request says it (in here, this room). No room
  words: `[]`. Vacuum unchanged.
- **V-TIMER-S / V-TIMER-U** (desk, argument representation, DESIGN §5.3): the main desk contract
  with `remove_alarm` replaced by a timer. Canonical action `start_timer(duration_seconds` integer
  1..86400, required). Gold is always in seconds ("25 minute timer" = 1500, "an hour and a half" =
  5400). V-TIMER-S exposes `duration_seconds`; V-TIMER-U exposes `amount` (integer) + `unit` ∈
  {seconds, minutes, hours}, mapped to seconds as amount × unit (so "90 minutes" and "1.5 hours"
  are not both expressible: any amount/unit whose product equals the gold is correct). Pausing,
  cancelling, querying timers: `[]`.
- **V-DISPATCH** (both): each app exposed as ONE tool whose `action` enum names the canonical
  actions and whose other arguments are the union of theirs. The mapping turns a dispatcher call
  into the canonical call; an argument that does not belong to the chosen action is an extra
  argument and makes the call wrong.
- **V-RENAME** (both): S1 with every tool name replaced by a name absent from Needle 1/2's
  232-tool list (`variants/home-renamed.json`, `variants/desk-renamed.json`, table in `variants/rename-table.json`). Gold unchanged.
- **V-COUNT-6 / 10 / 20** (both): S1 plus distractor tools (`variants/{home,desk}-count{6,10,20}.json`, built by `build_distractors.py`). Gold is
  in canonical names plus the distractors' own names. A request a distractor serves (e.g. "set the
  thermostat to 20" when `set_thermostat` is present) has that call as gold under that variant;
  anchors for this diagnostic should be chosen so that no distractor serves them, or labelled per
  variant.
- **V-VENDOR** (home): Cactus's own `smart_home` environment (5 tools, vendor-written, repo
  `cactus-compute/needle` at the pinned commit, `needle/environments/smart_home.py`). Gold uses
  that environment's tool names and argument names directly, under R1-R8 read against ITS
  tools and values. Labelled "vendor home turf" everywhere.
- **V-TRIGGERS, V-FORCED, V-CONTRACT-IN-PROMPT, the depth curve**: gold identical to main.

## 5. What is deliberately not in the contract

- No confidence rule. What an app does with the confidence score is the policy of DESIGN §7.3, set
  on calibration data, not part of ground truth.
- No preference between S0 and S1. Both are descriptions of these actions; the contract is
  what they describe.
- No statement about what Needle should find easy. Gold says what the app should do.

## 6. Changelog

### v1.1, 2026-09-22 (configuration lead, session 2537465c): clarifications from config-side adjudication

Written after 1,179 config items (dev, selection, calibration, lexical bank; never test) were labelled by
two blind annotators and 101 disagreements adjudicated (`partitions/annotation/adjudicated.jsonl`). None of
these changes an action, value or default above; they settle what the text left open. The custodian was told
the same day.

**Strata (DESIGN §3.3), defined here and applied in this order; the first that fits wins.**
- Act items (gold has a call): **A2** if the wording is indirect, conversational or relative and the call still
  follows (R6); else **A3** if two actions, or a value that needs normalising or resolving (a unit, a number
  word, a clock time, a date, a relative time); else **A1**. A room or device synonym alone is not A3.
- No-act items (gold is `[]`): **N3** if the request is negated, quoted, reported, conditional, or a question
  about the state of something the app DOES control; else **N1** if it asks for a capability, entity or value
  the app does not have, including a relative light change under the main contract, a question about
  something the app does not control, a schedule or recurrence, and a vague time; else **N2** (missing
  required information, genuinely ambiguous wording, a statement about the user that names no action, a
  fragment that is not a request).

**Silent cases, decided:**
1. Contradictory actions on one target in one request ("turn all lights on and turn off all the lights"):
   R2 applies literally, both calls.
2. An indirect cue beside an explicit relative request ("I can't see, let's make it brighter"): the explicit
   request decides; the cue is a reason (R8). Under the main contract `[]`.
3. "give me dark" and similar: more than one call could follow (off, dimmer): `[]`, N2.
4. A time-of-day word that describes the EVENT a reminder is about ("tomorrow's afternoon meeting") is still a
   vague time for the reminder: `[]` (R1).
5. A negated clause beside a served action ("remind me … and don't play the old list"): the negated clause asks
   for nothing, so it does not make the request partial; the served action stands.
6. A date inside a reason clause ("because it will be hot today") is not the reminder's date.
7. "to my to-do list for today" / "list of things to do today": "today" is a schedule qualifier the list cannot
   hold: `[]` (R1).
8. The LIST synonym table is closed, like the room table: "the things I need to travel with" is `[]`.
9. There is no minimum level word: "minimize the light", "lowest" is `[]`, N2.
10. "reminder alarm" names both an alarm and a reminder: `"ambiguous"`.
