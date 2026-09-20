# Patch architecture

This directory is not a place to dump boilerplate examples. Use the real implementation modules as the source of truth and keep this file as a concise operating guide.

## Read these first

- `.claude/skills/pyo-music/SKILL.md` — musical intent, synthesis strategy, and choice of Pyo objects
- `src/pyoscillate/patches/base.py` — `Patch`, `PatchRack`, start/stop behavior, resource retention
- `src/pyoscillate/patches/widgets.py` — `SliderSpec`, `patch_widget`, shared notebook UI
- `src/pyoscillate/patches/deep_house/kick.py` — canonical profile-based patch family
- Another conceptually close patch in the same family before adding new code

The goal is simple: musical reasoning is handled by the skill, while implementation and runtime discipline are handled here.

## Patch contract

Every patch module should expose the same public interface:

- `PARAMETERS`: ordered `SliderSpec` values for the notebook controls
- `build(...) -> Patch`: creates the DSP graph and returns the live patch
- `widget(...)`: creates the standard control surface through `patch_widget(...)`

Do not duplicate boilerplate in this file. Copy the structure from the actual modules that already work.

## Design rules

### 1. Extend existing families before creating new files

Before adding a new module, look for a neighboring patch with the same musical role.

Prefer:

- extending an existing patch family
- adding optional parameters to an existing builder
- using `make_builder(profile)` when the signal graph and control intent are the same but fixed profile data differs

Create a new patch module only when the patch genuinely needs a new control surface, topology, or lifecycle.

### 2. Keep parameters musical, not technical

A slider should describe what the listener hears:

- `Brightness`, `Body`, `Punch`, `Warmth`, `Movement`, `Depth`, `Drive`, `Decay`, `Rate`

Avoid exposing low-level implementation names such as filter cutoff, oscillator gain, wet/dry amount, or coefficient values when a perceptual label is clearer.

The `help_text` should answer: “What will I hear if I move this slider?”

### 3. Parameter changes should usually be live

If a parameter can change without changing the graph topology, it should be exposed as a live Pyo control and updated through `Patch.controls`.

- `Patch.update(...)` is the standard runtime update path.
- Rebuilds are for structural choices only: new voice count, new routing, different tables, changed buffer limits, or a genuine sequencing rewrite.
- Do not rebuild a patch just to tweak a value that could remain live.

### 4. Retain the full DSP graph

`build()` must return a patch that strongly owns the Python objects needed by the running DSP chain.

- name tables, triggers, envelopes, generators, and arithmetic intermediates
- include graph-critical objects in `Patch(resources=(...))` when needed
- do not rely on anonymous constructor expressions to keep the graph alive

This is important because Pyo native nodes can outlive their Python wrappers and cause nondeterministic crashes when patches are updated or multiple instances are active.

### 5. Keep timing/state explicit

Clocked and generative patches must preserve their sequence index, callback state, and random state when the same patch is updated.

- synthesis parameters usually remain live
- timing parameters often require custom setters or resubscription logic
- do not treat timing as a normal live parameter unless the runtime is genuinely equivalent

### 6. Keep the notebook contract small

Patch modules should not manually reconstruct the same UI plumbing each time.

- use `patch_widget(...)` for the standard controls
- keep patch-specific ranges, labels, and descriptions in the patch module
- do not duplicate preset registration or `interactive_output` wiring

## Canonical examples

Use these as the real templates for any new patch work:

- `src/pyoscillate/patches/base.py` — shared runtime contract and safety rules
- `src/pyoscillate/patches/widgets.py` — UI and slider metadata conventions
- `src/pyoscillate/patches/deep_house/kick.py` — profile family pattern and live-update behavior
- `src/pyoscillate/patches/psyambient/*.py` — other families with different sonic roles and control shapes

Treat code samples in this file as obsolete. The code under `src/pyoscillate/patches/` is the authoritative example set.

## Quality bar

A patch is ready when it does all of the following:

- fits the nearest existing family or clearly justifies a new one
- exposes user-facing musical controls instead of raw DSP names
- updates live when the underlying topology is unchanged
- preserves the full graph lifetime with explicit ownership
- keeps timing behavior and state transitions deliberate
- follows the standard `patch_widget` contract

If a concept belongs to the music skill rather than patch runtime discipline, move it there and keep this file focused on architecture and implementation rules.
