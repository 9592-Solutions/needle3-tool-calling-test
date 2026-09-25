# S1 = S0 + the vendor's tool-design checklist, and nothing else

S0 (`../S0/`, notes in `../S0/AUTHOR-NOTES.md`) was written 2026-09-22 by a blind author agent (Opus)
from a plain-language spec of the two apps, told nothing about Needle or its guide, and not allowed to
read anything. S1 is produced from it by `../build_schemas.py`, deterministically, applying only the
rules of Cactus's "How to Design Tools for Needle 3" (2026-09-18; copy at
`production/series/needle3/research/raw/blog-designing-tools-for-needle.txt`). Tool names, argument
names, tool count and argument types are unchanged, so S0 vs S1 isolates descriptions, enum wording,
defaults and formats. `diff <(python3 -m json.tool ../S0/home.json) home.json` shows every edit.

| guide rule | edit made to S0 |
|---|---|
| "Names users would say": enum options are matched against the request | room values `living_room`/`whole_house`/`current_room` → `living room`/`whole house`/`this room`; colours `warm_white`/`cool_white` → `warm white`/`cool white`; list `todo` → `to-do` |
| "never hide an enum value inside a common query word" | the "current room" value is `this room`, not `here` (`here` sits inside "there" and "where") |
| "If a value is not going to be in the request… give it a schema default" | `"default": "this room"` on the three light tools' `room`; `"default": "whole house"` on the vacuum's `room` (and `whole house` added to its enum so the default is representable); `"default": "09:00"` on the reminder's `time`. The date default (next occurrence) is not a constant and stays with the app. |
| "Describe a tool by the actions it covers, not by its category"; "Keep the synonyms in the description" | every tool description rewritten as the actions it covers, with user synonyms (lounge, hall, roomba, socket, wemo, grocery, tasks, remind me, wake me up) |
| "Formats in the description": the model copies what it sees | time: "24-hour HH:MM, e.g. 07:30 for 7:30 am or 19:30 for 7:30 pm"; date: "ISO date YYYY-MM-DD, e.g. 2026-06-12"; item/text: "in the user's words, e.g. …"; brightness: "a whole number from 1 to 100" |
| "Keep the description free of instructions to the model" | S0's "If no room is given, the room the user is currently in is used" became a default in the schema; descriptions state facts |
| "Constraints in the grammar" | already in S0 (1..100 bounds, HH:MM pattern, `format: date`, enums); kept |
| "Polar pairs… as separate tools or as one enum" | already in S0 (on/off enums, start/stop/dock enum); kept |
| "Keep the toolset small": five or fewer | already five per app; kept |
| "One tool per action" | S0's vacuum is one tool with a start/stop/dock enum, which the guide allows for a polar family ("or as one enum"); splitting it would give seven tools and cross the five-tool line, so it is kept |

Not applied, deliberately: triggers (own diagnostic arm, DESIGN §1), renaming tools (own diagnostic,
V-RENAME), anything learned from running a model (S1 is fixed before any run).

## Tool-name overlap with Needle 1/2's training tools (DESIGN §5.3)

The Needle 1/2 dataset card (in git history at `37c9e02^:dataset_readme.md`, repo
`cactus-compute/needle`) names 88 of its 232 tools. Exact overlap with S0/S1: **`set_alarm`,
`create_reminder`** (desk). Near names: `control_lights`, `set_brightness` (home lights),
`start_robot_vacuum` (vacuum), `create_list_item` (lists), `set_timer` (V-TIMER's `start_timer`).
The renamed variant (`../variants/home-renamed.json`, `desk-renamed.json`, table in
`../variants/rename-table.json`) uses names absent from those 88; the other 144 are not public, so
"absent from the training list" is checked against the published part only.
