# hassil arm: what the upstream English templates can and cannot produce

Read from OHF-Voice/intents @ f8cdbb0b (PINS.md). This is coverage of the canonical actions only; it says
nothing about how often each case occurs in the evaluation data, which was not seen.

| canonical action | reachable? | via | notable gaps (all produce `[]`) |
|---|---|---|---|
| `light_power` | yes | HassTurnOn/Off (area_domain, domain_only with the here-context, domain_all, name_*) | "turn ON all the lights" has no turn-on `domain_all` combination and does not match; bare "turn off the bathroom" (no light word) does not match |
| `set_light_level` | yes, absolute only | HassLightSet brightness combinations; percentage range 0..100 with number words; max/maximum/highest = 100, min/minimum/lowest = 1 | **no relative brightness intent at all** (no brighter/dimmer/"by 20%"; the relative intent upstream is volume-only); no "dim" verb; word order limits: "set the lights to 50%" (no area, no "brightness" word), "set the living room lights to 30 percent" (area before "lights") and "turn the lights on to 50%" do not match, while "set the lights in the kitchen to 30%", "set the kitchen to 20%" and "set the brightness to 12 percent" do; "half"/"full" are not brightness values |
| `set_light_color` | partly | HassLightSet colour (white, red, orange, yellow, green, blue, purple, pink; black/brown/turquoise are upstream-only and map to `[]`); warm white / cool white only through the colour-TEMPERATURE templates by name ("set the color temperature to warm white", "…daylight") | no violet, no shade modifiers (light blue), no "warm"/"cooler" alone; "set the lights to warm white" does not match; word order limits: "turn the kitchen lights green" and "kitchen lights blue" do not match, "make the kitchen blue" and "set the bedroom color to blue" do |
| `vacuum` start | yes | HassVacuumCleanArea ("vacuum/clean [the] <area>", "vacuum in here", "start the vacuum in the kitchen") → room; HassVacuumStart ("start [the] <vacuum name>") → whole house | no surface wording ("vacuum the carpet"); no English `area_only` for HassVacuumStart |
| `vacuum` dock | narrowly | HassVacuumReturnToBase: only "return [the] <vacuum name> [to base]" | "send the vacuum home", "dock the roomba" do not match |
| `vacuum` stop | **never** | none: there is no stop or pause vacuum intent in English, and HassTurnOff's name domains exclude vacuum | every stop request |
| `smart_plug` | yes | HassTurnOn/Off name_only with the plug as a `switch` entity named by the contract's plug words | plugs named by what is plugged in ("the rice cooker socket") do not match |

Structural limits that hold across every action:
- **One intent per sentence**, so two-action requests (R2) are never produced.
- **Indirect wording (R6)** such as "it's too dark in here" or "the floor is filthy" has no templates, so
  it returns `[]`.
- **Negation, questions and conditionals** do not match the action templates, so the `[]` answer comes
  out right without any logic in the arm. State questions match HassGetState, which is unmapped.
- **Unknown rooms** are rejected, because the area slot list holds only our six rooms plus their aliases.
- Politeness is handled only by the shipped `skip_words` (please, can you, could you, would you, for me,
  i'd like [to], i want). A wake word such as "olly" breaks the match.

Probed with hand-written sentences only (`test_hassil_arm.py` and ad-hoc `hassil_arm.py` CLI calls).
