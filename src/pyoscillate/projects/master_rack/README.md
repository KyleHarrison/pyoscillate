# Master Rack

A catalogue rack rather than a song: every concrete patch under
`src/pyoscillate/patches/` is available, grouped by its category directory
(Drums, Tonal, Texture, ...). It is a sketchpad for auditioning and layering
any patch together without writing a project first.

## Musical brief

- Tempo/feel: 120 BPM, 4/4, default clock resolution - neutral, so any patch
  is audible at a sensible speed.
- Harmony: A minor, `Progressions.STATIC` (the default). Chord-following
  patches hold one chord until the user picks a progression in the page header.
- Form: none. The user adds patches and switches them on by hand.

Grounding: no genre brief, so no music-theory reference drove this; the rack
defers every musical choice to the patches' own defaults.

## Concept-to-patch mapping

| Concept | Patch family | Status |
| --- | --- | --- |
| "Every patch, by category" | each concrete `Patch` subclass found under a category directory of `patches/` | reused as-is, discovered at import time |
| "Pick which patches are in the rack" | a `GroupController(selectable=True)` per category | new group mode: tickbox menu adds/removes panels |
| "Adding does not play" | the panel's own enable switch stays off | unchanged |

## Behaviour

- One top-level group per category directory, in alphabetical order.
- Each group's tickbox menu lists every patch of that category. Ticking adds
  its panel to a two-column grid inside the group; unticking removes it and
  silences it. Adding never switches a patch on.
- Patches are discovered, not listed: a new patch module appears in the rack
  without editing it. Patch `name`s must be unique across the repo.
- A patch's panel only enters the page when it is added, and its sliders are
  only made when its tile first opens, so the page stays small however many
  patches the rack offers. A patch that was never added still keeps its
  settings: presets and group controls reach it, and its sliders show those
  values when it is added and opened.
- Presets save which patches are added alongside each patch's settings.

Run: `uv run flet run src/flet/master_rack/app.py`
