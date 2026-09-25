# S0 first-draft contract: author notes

- Home lights are split into three functions (power, brightness, colour), one per action, rather than one `set_lights` with optional fields, so each call has one required value.
- Rooms are a closed snake_case enum. `whole_house` and `current_room` are enum values, and `room` is optional with `current_room` as the documented default. The app applies that default when the field is missing.
- The vacuum is one `control_vacuum` function with an `action` enum (start/stop/dock). `room` only applies to `start`, and leaving it out means the whole house, so `whole_house` is not in its enum.
- The plug gets its own `set_plug_power` with an on/off enum. It has no room because there is only one plug.
- Colour names with spaces became `warm_white` / `cool_white`, and "to-do" became `todo`, to keep enum values identifier-like.
- Desk times are 24-hour `HH:MM` strings, validated by a regex. Dates are ISO `YYYY-MM-DD` (`format: date`). The model has to resolve "tomorrow" and similar phrases itself; the app never receives relative dates.
- Defaults (next occurrence for date, 09:00 for reminder time) are described in text and applied by the app. The schema declares no `default` keyword.
- Alarms and list edits come as add/remove pairs of functions, not a single function with an operation field. Removal matches by time (plus optional date) or by item text.
- There are no query, list or undo functions, because the spec lists none.
