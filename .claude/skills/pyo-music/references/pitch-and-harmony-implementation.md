# Pitch & Harmony Implementation

Covers the one piece of turning a chord/scale into sound that has **no
existing convention to point to**: sounding more than one pitch at once. For
converting a single pitch/interval to Hz, don't read this file — that's
already solved in code (see the "Concept bridges" table in
[`../SKILL.md`](../SKILL.md)): `root_freq * 2 ** (semitones / 12)`, as used
in `atmosphere.py`'s `ARP_INTERVALS` and `mid_arp.py`, or `MToF`/`FToM`
(documented in [`pyo-api/analysis/utils.py`](./pyo-api/analysis/utils.py))
if the pitch material is MIDI-derived. This file starts from *after* that
conversion, once you have N frequencies and need to decide how they sound
together.

## Sounding more than one pitch at once (chords)

**No patch in this codebase currently sustains a chord** (`atmosphere.py`'s
`ARP_INTERVALS` and `mid_arp.py`/`mid_canon.py` all arpeggiate — one pitch at
a time over the clock, never stacked). Building an actual chord/pad voice is
new territory here, not an existing pattern to imitate. Options, in
increasing order of how much of the API they touch:

- **Multiple generator instances, one per chord tone**, each fed its own
  Hz value from the conversion above, then summed. Summing is either plain
  Python `+` between `PyoObject`s, or explicit `Mix` (documented in
  [`pyo-api/core/signal_utils.py`](./pyo-api/core/signal_utils.py)) if you
  need channel-count control over the sum. This is the most explicit and
  easiest to reason about — each voice can have independent envelope/detune.
- **Passing a Python list as a generator's `freq=` argument.** Pyo objects
  expand a list argument into multiple parallel streams automatically (this
  is a general Pyo behaviour, not specific to one class — verify against the
  constructor you're using in `pyo-api/`, since not every parameter supports
  it the same way). This is more compact than separate instances but harder
  to give each tone an independent envelope or pan.
- **`OscBank`** (in
  [`pyo-api/core/tableprocess.py`](./pyo-api/core/tableprocess.py)) if the
  chord is being used more like a fixed harmonic stack driving one
  timbre (partials) rather than independently articulated voices — read its
  docstring closely, since it's built for a different use case (spectral/
  additive stacks) than a played chord and may not be the right fit.

Whichever mechanism is chosen, go to `pyo-api-navigation.md` next to decide
what generator/filter/envelope each individual voice actually uses — this
file only gets you from "a chord" to "N frequencies wired to N or one
signal path," not the timbre itself.


**No patch in this codebase currently sustains a chord** (`atmosphere.py`'s
`ARP_INTERVALS` and `mid_arp.py`/`mid_canon.py` all arpeggiate — one pitch at
a time over the clock, never stacked). Building an actual chord/pad voice is
new territory here, not an existing pattern to imitate. Options, in
increasing order of how much of the API they touch:

- **Multiple generator instances, one per chord tone**, each fed its own
  Hz value from the conversion above, then summed. Summing is either plain
  Python `+` between `PyoObject`s, or explicit `Mix` (documented in
  [`pyo-api/core/signal_utils.py`](./pyo-api/core/signal_utils.py)) if you
  need channel-count control over the sum. This is the most explicit and
  easiest to reason about — each voice can have independent envelope/detune.
- **Passing a Python list as a generator's `freq=` argument.** Pyo objects
  expand a list argument into multiple parallel streams automatically (this
  is a general Pyo behaviour, not specific to one class — verify against the
  constructor you're using in `pyo-api/`, since not every parameter supports
  it the same way). This is more compact than separate instances but harder
  to give each tone an independent envelope or pan.
- **`OscBank`** (in
  [`pyo-api/core/tableprocess.py`](./pyo-api/core/tableprocess.py)) if the
  chord is being used more like a fixed harmonic stack driving one
  timbre (partials) rather than independently articulated voices — read its
  docstring closely, since it's built for a different use case (spectral/
  additive stacks) than a played chord and may not be the right fit.

Whichever mechanism is chosen, go to `pyo-api-navigation.md` next to decide
what generator/filter/envelope each individual voice actually uses — this
file only gets you from "a chord" to "N frequencies wired to N or one
signal path," not the timbre itself.
