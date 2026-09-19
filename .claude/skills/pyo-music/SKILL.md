---
name: pyo-music
description: Use whenever the user wants music, sound design, or procedural/generative audio *built or edited in this project's Pyo patches* — e.g. "make a dark evolving drone," "make the filter wander more organically," "add a clock-like ticking texture," "make this pad breathe," "make something inspired by [a track/artist]'s sound," or any request to write, adjust, or reason about code under `src/pyoscillate/patches/`. Also use for pure music-theory/composition questions (harmony, melody, rhythm, form, genre) even without a synthesis component. Do not use for unrelated Python/project tooling questions that don't touch music or the patches.
---

# Pyo Music

This skill connects two knowledge layers that must stay separate:

- **`references/`** (everything except `pyo-api/`) — the music-composition reference library. Answers "what is the musical/sonic idea?" It knows nothing about Pyo.
- **`references/pyo-api/`** — the authoritative, hand-written documentation of every Pyo object this project uses or has evaluated. Answers "what implementation primitives exist?" It knows nothing about music theory. **Never invent Pyo behaviour or constructor arguments — if `pyo-api/` documents it, read the file; don't answer from general Pyo knowledge.**

Neither layer talks about the other. Routing between them is this file's only job — it deliberately does not restate either layer's content.

## Reasoning chain

Move through these steps in order. Don't skip from natural language straight to a Pyo class name.

```
user's musical/sonic description
        ↓  (1)
references/00-navigation.md  → musical/sonic reference file(s)
        ↓  (2)
translate into a synthesis-level idea: what changes, how, at what timescale,
gated or free-running, periodic or stochastic, harmonic or noisy...
        ↓  (3)
references/pyo-api-navigation.md  → candidate pyo-api/ file(s)
        ↓  (4)
read the actual pyo-api/ docstrings for the real constructor signature
        ↓  (5)
wire it into a patch (see "Writing/editing a patch" below)
```

**Step 2 is the one that's easy to skip and shouldn't be.** "Dark," "organic," "metallic," "breathing" do not map to one Pyo object each — each has several valid synthesis interpretations (register, spectrum, envelope shape, modulation type, density...). Decide *which* interpretation fits this request before opening `pyo-api-navigation.md`. If more than one interpretation is plausible and the user hasn't disambiguated, say so and offer 2-3 concrete options rather than silently picking one.

## Step 1 in detail — musical/sonic reasoning

Always start at `references/00-navigation.md`. It routes theory/composition/genre/vague-feeling requests to specific files (harmony, rhythm, form, genre, production-aware, etc.) and explains its own loading discipline (1-3 files for most requests; 5+ means the question is too broad). Follow that discipline here too.

`references/music-composition-skill-notes.md` holds that skill's own philosophy and conventions (how to frame techniques, notation conventions, genre framing) — read it once if you need the reasoning style, not per request.

This layer is genuinely sufficient on its own for pure composition questions (chord progressions, melodic advice, arrangement) that have no synthesis/patch component — answer from it directly and skip step 3 onward.

## Step 3 in detail — synthesis reasoning

`references/pyo-api-navigation.md` is the linking table: it takes a synthesis-level idea (a category of mechanism — continuous modulation, triggered events, filtering, dynamics, spectral processing, etc.) and points to the specific `pyo-api/` file(s) that document real candidates, with one-line hints on what distinguishes them. It also points to worked examples already in `src/pyoscillate/patches/` — reading a working patch is often the fastest way to see how categories combine into a real signal chain.

That file's candidates are deliberately not 1:1 (e.g. "continuous organic modulation" lists both `Rossler` and `Lorenz`, plus a plain slow LFO as the non-chaotic alternative). Read the actual docstrings in `pyo-api/` before choosing between them — the navigation file narrows the search, it doesn't make the final call.

## Reference-track requests

("Make something like the clock ticks in Pink Floyd's *Time*", "give me the vibe of [artist]'s intro".)

Never treat the reference as a recipe to reproduce and never hard-code a patch keyed to a specific track/artist. Instead: `references/research/reference-track-digging.md` (and the relevant genre/production-aware file) to extract sonic/musical *characteristics* → step 2/3 above to turn those characteristics into synthesis mechanisms → an original patch. `pyo-api-navigation.md` documents one worked instance of this (`clock_tick.py`, derived from "several unsynchronized periodic ticks, each a distinct resonant timbre" — not from looking up the track).

## Writing or editing a patch

- Every patch lives in `src/pyoscillate/patches/` as a `build(...) -> Patch` function plus a `widget(...)` for the notebook UI — look at an existing patch (e.g. `drone.py`, `clock_tick.py`) for the shape before adding a new one.
- `base.py`'s `Patch`/`PatchRack` handle start/stop, fade, and the shared `Compress` gain-stage tail — don't reimplement gain staging or click-free stop/start per patch.
- Prefer high-level, musically-named parameters (e.g. `reverb_size`, `wood_q`) with docstring explanations of what raising/lowering them does perceptually, matching the existing patches' style.
- After wiring a patch, trace it backward from `.out()`/the returned `voice` and check each stage against the `pyo-api/` file it came from — this is the fastest way to catch a misremembered parameter name before running it.

## Known gaps

`pyo-api-navigation.md` ends with a short list of categories (`analysis/`, `spectral/`, `sequencing/`, `external_io/`, `playback_routing/`, `control/`) whose mapping is inferred from their docstrings rather than from an existing patch using them — treat a mismatch there as a cue to refine that file, not as ground truth.
