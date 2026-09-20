---
name: pyo-music
description: Use whenever the user wants music, sound design, or procedural/generative audio *built or edited in this project's Pyo patches* — e.g. "make a dark evolving drone," "make the filter wander more organically," "add a clock-like ticking texture," "make this pad breathe," "make something inspired by [a track/artist]'s sound," or any request to write, adjust, or reason about code under `src/pyoscillate/patches/`. Also use for pure music-theory/composition questions (harmony, melody, rhythm, form, genre) even without a synthesis component, and for scaffolding a whole new named project ("new project called {project_name}") that needs a Flet app module, a patch rack, and its own patches/README. Do not use for unrelated Python/project tooling questions that don't touch music or the patches.
---

# Pyo Music

This skill connects two knowledge layers that must stay separate:

- **`../music-theory/`** — the music-composition reference skill. Answers "what is the musical/sonic idea?" It knows nothing about Pyo. Load it for the theory/composition layer before choosing synthesis mechanisms.
- **`references/pyo-api/`** — the authoritative documentation of every Pyo object exposed by the installed `pyo` package, one reference file per real `pyo/lib/*.py` source module (organized into the category folders below by use). Answers "what implementation primitives exist?" It knows nothing about music theory. **Never invent Pyo behaviour or constructor arguments — if `pyo-api/` documents it, read the file; don't answer from general Pyo knowledge.**

Neither layer talks about the other. Routing between them is this file's only job — it deliberately does not restate either layer's content.

## Reference map

For musical reasoning, load the sibling
[`music-theory/SKILL.md`](../music-theory/SKILL.md), then its
[`references/00-navigation.md`](../music-theory/references/00-navigation.md).

If the theory layer produced pitch/harmonic content (a chord, scale, or
interval set) rather than just a mechanism idea, first read
[`references/pitch-and-harmony-implementation.md`](./references/pitch-and-harmony-implementation.md)
to turn it into frequencies and a voice-count strategy.

For synthesis mechanism reasoning, start with
[`references/pyo-api-navigation.md`](./references/pyo-api-navigation.md),
then open the specific linked API reference it selects:

- [`references/pyo-api/core/`](./references/pyo-api/core/) for generators, timing, modulation, envelopes, effects, dynamics, and output
- [`references/pyo-api/analysis/`](./references/pyo-api/analysis/) for signal analysis and DSP expressions
- [`references/pyo-api/control/`](./references/pyo-api/control/) for random sources and value mapping
- [`references/pyo-api/external_io/`](./references/pyo-api/external_io/) for MIDI and network control
- [`references/pyo-api/playback_routing/`](./references/pyo-api/playback_routing/) for players, routing, and matrices
- [`references/pyo-api/sequencing/`](./references/pyo-api/sequencing/) for event and pattern sequencing
- [`references/pyo-api/spectral/`](./references/pyo-api/spectral/) for FFT and phase-vocoder processing

## Concept bridges

Most theory concepts (orchestration density, groove feel, genre convention,
production-aware arrangement...) don't need a dedicated bridge file — step 2
below plus `pyo-api-navigation.md`'s mechanism table already handles them,
because there's no unit mismatch, only a mechanism choice.

A dedicated bridge is only worth writing where the theory layer's units
don't exist in Pyo natively and require real conversion. Before adding a new
one, check whether the codebase already solves that conversion — point to
the existing utility instead of re-deriving it in a doc:

| Concept | Unit gap | Bridge |
|---|---|---|
| Pitch / harmony (single pitch) | semitones, chord tones ↔ Hz | already solved in code: `root_freq * 2 ** (semitones / 12)`, as used in `atmosphere.py`'s `ARP_INTERVALS` and `mid_arp.py` — or `MToF`/`FToM` in [`pyo-api/analysis/utils.py`](./references/pyo-api/analysis/utils.py) for MIDI-derived pitch. Read those directly; don't re-derive |
| Pitch / harmony (multiple pitches at once) | no existing convention for sounding a chord — every patch so far arpeggiates one pitch at a time | [`references/pitch-and-harmony-implementation.md`](./references/pitch-and-harmony-implementation.md) — genuinely undocumented territory, not solved in code yet |
| Rhythm / tempo | BPM, bars, 16ths ↔ seconds | `src/pyoscillate/tempo.py`'s `Tempo` and `clock.py`'s `Clock`/`Division` — already solved in code; read those directly rather than re-deriving BPM math, and use `Clock.subscribe()` for anything tempo-locked instead of a raw `Metro` |

Add a new row here only when a request exposes a real gap of this kind —
don't pre-build one per theory topic speculatively.

## Reasoning chain

Move through these steps in order. Don't skip from natural language straight to a Pyo class name.

```
user's musical/sonic description
        ↓  (1)
../music-theory/  → musical/sonic reference file(s)
        ↓  (2)
translate into a synthesis-level idea: what changes, how, at what timescale,
gated or free-running, periodic or stochastic, harmonic or noisy...
        ↓  (2b, only if step 1 produced more than one simultaneous pitch — a chord/voicing)
references/pitch-and-harmony-implementation.md  → how to sound them together
        ↓  (3)
references/pyo-api-navigation.md  → candidate pyo-api/ file(s)
        ↓  (4)
read the actual pyo-api/ docstrings for the real constructor signature
        ↓  (5)
wire it into a patch (see "Writing/editing a patch" below)
```

**Step 2 is the one that's easy to skip and shouldn't be.** "Dark," "organic," "metallic," "breathing" do not map to one Pyo object each — each has several valid synthesis interpretations (register, spectrum, envelope shape, modulation type, density...). Decide *which* interpretation fits this request before opening `pyo-api-navigation.md`. If more than one interpretation is plausible and the user hasn't disambiguated, say so and offer 2-3 concrete options rather than silently picking one.

## Step 1 in detail — musical/sonic reasoning

Always start by loading `../music-theory/SKILL.md`, then begin at its `references/00-navigation.md`. It routes theory/composition/genre/vague-feeling requests to specific files (harmony, rhythm, form, genre, production-aware, etc.) and explains its own loading discipline (1-3 files for most requests; 5+ means the question is too broad). Follow that discipline here too.

The music-theory skill's `references/music-composition-skill-notes.md` holds its own philosophy and conventions (how to frame techniques, notation conventions, genre framing) — read it once if you need the reasoning style, not per request.

This layer is genuinely sufficient on its own for pure composition questions (chord progressions, melodic advice, arrangement) that have no synthesis/patch component — answer from it directly and skip step 3 onward.

## Step 3 in detail — synthesis reasoning

`references/pyo-api-navigation.md` is the linking table: it takes a synthesis-level idea (a category of mechanism — continuous modulation, triggered events, filtering, dynamics, spectral processing, etc.) and points to the specific `pyo-api/` file(s) that document real candidates, with one-line hints on what distinguishes them. It also points to worked examples already in `src/pyoscillate/patches/` — reading a working patch is often the fastest way to see how categories combine into a real signal chain.

That file's candidates are deliberately not 1:1 (e.g. "continuous organic modulation" lists both `Rossler` and `Lorenz`, plus a plain slow LFO as the non-chaotic alternative). Read the actual docstrings in `pyo-api/` before choosing between them — the navigation file narrows the search, it doesn't make the final call.

## Reference-track requests

("Make something like the clock ticks in Pink Floyd's *Time*", "give me the vibe of [artist]'s intro".)

Never treat the reference as a recipe to reproduce and never hard-code a patch keyed to a specific track/artist. Instead: use the music-theory skill's reference-track guidance and relevant genre/production-aware file to extract sonic/musical *characteristics* → step 2/3 above to turn those characteristics into synthesis mechanisms → an original patch. `pyo-api-navigation.md` documents one worked instance of this (`clock_tick.py`, derived from "several unsynchronized periodic ticks, each a distinct resonant timbre" — not from looking up the track).

## Writing or editing a patch

- Every patch is a `build(...) -> Patch` function plus a `widget(...)` for the notebook UI, living either directly under `src/pyoscillate/patches/` (e.g. `drone.py`, `clock_tick.py`) or under a concept subfolder `src/pyoscillate/patches/{concept}/{patch}.py` (`concept` = a logical layer like `bass/`, `mid/`, `drone/`, `soundscape/`, `percussion/` — `patches/psyambient/` is the existing precedent for this, via its `bass_*`/`mid_*`/`soundscape_*` filename prefixes). Look at an existing patch for the shape before adding a new one, and match whichever layout the patch's project already uses.
- **Extend before you fork.** Before adding a new patch, search `src/pyoscillate/patches/**` for one that's already conceptually close. If one exists, add new *optional* parameters to it (default = current behavior) instead of writing a new file — this keeps every project/rack that already imports it working unchanged. Only create a new patch file — under `patches/{concept}/{new_patch}.py` — when reuse would break backward compatibility or the sound is genuinely a new concept.
- `base.py`'s `Patch`/`PatchRack` handle start/stop, fade, and the shared `Compress` gain-stage tail — don't reimplement gain staging or click-free stop/start per patch.
- Prefer high-level, musically-named parameters (e.g. `reverb_size`, `wood_q`) with docstring explanations of what raising/lowering them does perceptually, matching the existing patches' style.
- After wiring a patch, trace it backward from `.out()`/the returned `voice` and check each stage against the `pyo-api/` file it came from — this is the fastest way to catch a misremembered parameter name before running it.

## New project workflow

When the user asks for a new project named `{project_name}` (a whole new Flet
app + patch rack, not a single patch edit), run this sequence in order:

1. **Ground the request.** Run the usual reasoning chain above (music-theory
   → sonic reasoning → synthesis strategy) for whatever musical/sonic brief
   defines this project, before creating any files.
2. **Flet app module.** Create `src/flet/{project_name}/` as a package
   (`__init__.py` + `app.py`). **No reusable starter template exists yet** —
   this is a known TODO. Until one is built, copy-adapt the closest existing
   example: `rack_demo_app.py` or `psyambient_app.py` for a multi-voice rack,
   `app.py` for a single-patch app. `app.py`'s `main()` must build a
   `PatchRackApp` (`src/flet/base.py`) from the `PATCH_DEFS` defined in step
   3's `rack.py`, with a `CATALOG_DIR` under `src/flet/presets/{project_name}/`.
3. **Project rack module.** Create `src/pyoscillate/projects/{project_name}/`
   with `__init__.py` and `rack.py`. `rack.py` owns `PATCH_DEFS:
   list[PatchDef]` — this replaces today's convention of defining that list
   inline in the `*_app.py` file; the app module should only import it.
4. **Reuse or add patches.** Follow "Writing or editing a patch" above for
   every patch this project needs: extend a conceptually close existing
   patch with new optional parameters where possible, and only create a
   genuinely new patch (under `patches/{concept}/{new_patch}.py`) when that
   isn't possible.
5. **Wire the rack.** Once every needed patch exists or has been extended,
   `rack.py`'s `PATCH_DEFS` lists a `PatchDef` per patch for this project,
   same shape as `PATCH_DEFS` in `psyambient_app.py`/`rack_demo_app.py`
   today.
6. **Project README.** Generate
   `src/pyoscillate/projects/{project_name}/README.md` documenting: the
   musical/theory brief from step 1, the concept→patch mapping decided in
   steps 4-5, and per-patch parameter docs explaining what each control does
   perceptually and how it serves the musical goal — matching the docstring
   voice already used in existing patch files.

This workflow (the `projects/{project_name}/rack.py` + `patches/{concept}/`
split) applies going forward only — existing projects (`rack_demo`,
`psyambient`, `deep_house`, `soundscape_fm`) keep their current inline
`PATCH_DEFS`/flat-patch layout unless a future task asks to migrate them.

## Known gaps

`pyo-api-navigation.md` ends with a short list of categories (`analysis/`, `spectral/`, `sequencing/`, `external_io/`, `playback_routing/`, `control/`) whose mapping is inferred from their docstrings rather than from an existing patch using them — treat a mismatch there as a cue to refine that file, not as ground truth.

No patch in this codebase currently sustains a chord (simultaneous pitches) — everything arpeggiates one note at a time. `pitch-and-harmony-implementation.md`'s multi-voice options are therefore reasoned from the Pyo API, not distilled from a working example here; treat a mismatch as a cue to refine that file once a real chord/pad patch exists.

The "new project workflow" section above is untested — no project has been
scaffolded through it yet. Treat the first real usage as the place to
sanity-check the `rack.py`/app-package split before treating it as settled
convention.
