# hassil arm: declared mapping (written before any evaluation data was seen)

This was declared on 2026-09-22 from CONTRACT.md §2 and `contracts/mapping.py` only. The machine-readable
form is `mapping_table.json`, and `hassil_arm.py` implements it. No sentence template was written, edited
or added. Everything this arm adds sits in the slot lists (the configuration a Home Assistant user gives
their instance) and in the intent-to-tool table.

## What hassil is given

- **Areas** are the six rooms. Each area's aliases are exactly CONTRACT §2's synonyms: living room ← lounge,
  sitting room; bedroom ← bed room, my bedroom; hallway ← hall, corridor. Each value_out is the canonical
  room name.
- **Floors**: none, because the contract has no floors. Every `{floor}` template is therefore unmatchable.
- **Entities** (the `{name}` list, each carrying its `domain` in the value context the way HA's own name
  list does):
  - one light per area, named `<room> light` (e.g. "kitchen light"), domain `light`, in that area;
  - `vacuum.robot`: names "vacuum", "robot vacuum", "roomba", "cleaner", "hoover" (the vacuum words in
    CONTRACT §2), no area;
  - `switch.smart_plug`: names "smart plug", "plug", "socket", "smart socket", "outlet", "wemo", "power
    socket" (the plug words in CONTRACT §2), no area.
- **Satellite context**: every request is recognized with `intent_context = {area: "here"}`. This stands
  for the voice satellite being in the speaker's room. Upstream's `context_area` combinations ("turn on the
  lights", "lights on in here", "vacuum in here", "make the lights red") copy it into the area slot, and it
  becomes the contract's `here` room. That matches the contract's default rule: no room named → `here`.
- **Recognizer**: `hassil.recognize_best(..., language="en", best_slot_name="name")`. These are the same
  call and priority HA's default agent uses. Upstream's `skip_words` (please, can you, …) apply as shipped.

## Intent → canonical call

| HA intent | slot condition | canonical call |
|---|---|---|
| HassTurnOn / HassTurnOff | domain light, area slot (spoken or context `here`) | `light_power(room=area, state=on/off)` |
| HassTurnOn / HassTurnOff | domain light, no area (only the `domain_all` combination: "all the lights", `<everywhere>`) | `light_power(room="whole house", …)` |
| HassTurnOn / HassTurnOff | name → a light entity (an area slot, if present, must equal the entity's area, else `[]`) | `light_power(room=entity area, …)` |
| HassTurnOn / HassTurnOff | name → smart plug, no area slot | `smart_plug(state=on/off)` |
| HassLightSet | brightness slot, integer 1..100 (0 or a non-integer → `[]`); target = area / context / named light's area | `set_light_level(room, level)` |
| HassLightSet | colour ∈ {white, red, orange, yellow, green, blue, purple, pink} | `set_light_color(room, color)` |
| HassLightSet | colour black, brown or turquoise (in upstream's list, not in COLORS) | `[]` |
| HassLightSet | temperature slot, decided by its SPOKEN text: "warm white" → warm white; "cool white" / "cold white" / "daylight" / "day light" → cool white | `set_light_color(room, …)` |
| HassLightSet | temperature "candle light" or any numeric kelvin | `[]` |
| HassVacuumStart | name → vacuum | `vacuum(start, room="whole house")` |
| HassVacuumCleanArea | area slot (spoken or context `here`); a name, if present, must be the vacuum | `vacuum(start, room=area)` |
| HassVacuumReturnToBase | name → vacuum | `vacuum(dock)` |

The kelvin rule exists because CONTRACT §2 has no kelvin value. A number could only be mapped to warm or
cool white by inventing a threshold, so numbers stay unmapped. The named values map through the
contract's own synonyms (daylight → cool white).

## Deliberately unmapped (a match returns `[]`)

- Every other intent in the shipped English grammar. That covers HassGetState, climate, fan speed, media,
  volume, timers, lists and shopping list, HassNevermind, HassRespond, HassBroadcast, HassSetPosition,
  lawn mower, weather, and date/time. A question such as "is the kitchen light on" matches HassGetState and
  correctly produces no action.
- HassTurnOn/Off on domain `fan`, on cover device classes, and on scenes and scripts.
- Anything hassil does not match: returns `[]`. A hassil exception on odd input is also treated as a
  non-match.

## Contract rules the arm does not implement itself

R1–R8 are not coded. The arm relies on whole-sentence matching. A negation, a conditional, a schedule
suffix or a second action ("… and make coffee") leaves the sentence unmatched, so the result is `[]`.
This is a property of the grammar, not a filter we added. The multiset rule for two actions (R2) can never
be satisfied, because hassil returns one intent per sentence.
