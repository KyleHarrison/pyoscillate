# Patch Architecture

This directory contains notebook-first Pyo patches. Every patch module follows one public shape:

- `PARAMETERS`: an ordered tuple of `SliderSpec` values describing notebook controls.
- `build(...) -> Patch`: constructs the Pyo graph once and returns its runtime state.
- `widget(rack, ..., controller=None)`: delegates standard controls to `patch_widget(...)`.

## Module template

Use this shape for a normal patch module. Its project rack passes `build`
directly to `PatchDef`; the notebook calls `widget(...)` once.

```python
from __future__ import annotations

from ipywidgets import VBox

from pyoscillate.patches.base import Patch, PatchRack
from pyoscillate.patches.presets import PresetController
from pyoscillate.patches.widgets import SliderSpec, patch_widget

PARAMETERS = (
    SliderSpec("amount", 0.0, 1.0, 0.05, 0.5, "Amount", "Musical effect."),
)


def build(amount: float = 0.5) -> Patch:
    """Build one independently addressable patch."""
    # Create the Pyo graph and any live controls here.
    return Patch(sequencer=..., voice=..., controls={"amount": ...})


def widget(rack: PatchRack, controller: PresetController | None = None) -> VBox:
    """Create this patch's standard notebook controls."""
    return patch_widget(rack, "patch_name", build, PARAMETERS, controller=controller)
```

For a clocked patch, add `tempo: Tempo, clock: Clock` to both `build` and
`widget`, then pass them through `build_kwargs={"tempo": tempo, "clock": clock}`.
The project rack sets `needs_tempo=True` and `needs_clock=True`. Pass
`rebuild_parameters` to both `patch_widget` and `PatchDef` only for structural
parameters that cannot update the existing Pyo graph.

## Profile variants

Most patch modules expose `build` directly to a `PatchDef`. A module may also
expose `make_builder(profile)` when several independently selectable rack
patches share the same parameters, live controls, lifecycle, and signal-graph
shape, but differ in fixed construction data such as a rhythmic pattern,
envelope profile, wavetable, or effect balance. This avoids near-identical
modules while keeping every profile independently addressable in presets and
the rack.

```python
PROFILES = {"soft": (...), "bright": (...)}


def build(tempo: Tempo, clock: Clock, profile: str, amount: float = 0.5) -> Patch:
    """Build one profile of this patch family."""
    fixed_value = PROFILES[profile]
    return Patch(sequencer=..., voice=..., controls={"amount": ...})


def make_builder(profile: str) -> Callable[..., Patch]:
    """Fix a profile for one independent rack entry."""
    return lambda tempo, clock, **values: build(tempo, clock, profile, **values)


def widget(
    rack: PatchRack,
    tempo: Tempo,
    clock: Clock,
    controller: PresetController | None = None,
    profile: str = "soft",
) -> VBox:
    """Create controls for one profile."""
    return patch_widget(
        rack,
        f"patch_name_{profile}",
        make_builder(profile),
        PARAMETERS,
        controller=controller,
        build_kwargs={"tempo": tempo, "clock": clock},
    )
```

The project rack creates one `PatchDef` per profile:

```python
PatchDef(
    name="patch_name_soft",
    title="Patch Name - Soft",
    summary="...",
    build=patch_name.make_builder("soft"),
    parameters=patch_name.PARAMETERS,
    needs_tempo=True,
    needs_clock=True,
)
```

Use this pattern only when the common controls genuinely mean the same thing
for every profile. Split variants into separate modules when they require a
different control surface, rebuild behavior, or substantially different
sequencing or signal topology.

## Construction and runtime

Keep `build` as a function. Do not create a class for every patch. A function keeps the signal graph local and easy for an agent to inspect. Use a small private class only when a patch owns unusual persistent sequencing behavior, such as multiple Metros or callback keepalive references.

`Patch` owns start/stop, output fading, compression, live controls, and volume. A parameter that can change without changing graph topology must be represented by a live Pyo control such as `SigTo` and exposed through `Patch.controls`. Widget changes call `Patch.update(...)`; they must not rebuild or restart an active patch.

A graph rebuild is appropriate only for structural changes: changing the number of voices, routing topology, fixed tables, or a buffer limit. Structural rebuild behavior must be explicit rather than accidental.

### Pyo graph ownership

`build()` must return a `Patch` that strongly owns every Python-side Pyo object
needed by its running DSP graph. Pyo's native nodes can retain pointers to
upstream objects without keeping the corresponding Python wrappers alive.
Garbage collection can then produce a nondeterministic segmentation fault,
often only when multiple patches run or a widget callback changes a value.

Name graph nodes instead of creating them only inside another constructor or
arithmetic expression. Pass auxiliary nodes to `Patch(resources=(...))` when
they are not already guaranteed to remain alive through `voice`, `sequencer`,
or a control closure. Include tables, triggers, generators, envelopes, and
arithmetic intermediates conservatively. See `deep_house/kick.py` for the
known-good pattern.

Do not diagnose this failure from the last Python callback alone. A slider can
make the fault occur more often without being its cause. Minimize suspected
native crashes in a child process using `audio="manual"`, advance DSP with
repeated `server.process()` calls, and enable `-X faulthandler`.

Native-crash regressions must remain subprocess tests so a future segfault is
reported as a nonzero child exit instead of killing the test runner. Exercise
multiple simultaneous instances and live control updates. A test that only
constructs or starts a patch does not validate native graph lifetime. The
reference regression is `tests/test_deep_house_patches.py`.

## Parameter metadata

`SliderSpec` contains the project-level parameter name, UI range/default, musical description, and optional `PyoParamRef` values. `PyoParamRef` points to the actual imported Pyo class and constructor parameter so IDE hover/navigation reaches Pyo documentation:

```python
SliderSpec(
    "root_freq",
    55,
    220,
    1,
    110,
    "Carrier frequency",
    "Carrier frequency - the pad's held pitch.",
    (PyoParamRef(FM, "carrier"),),
)
```

Use multiple references when one project parameter controls several Pyo objects. Keep `help_text` local: it explains the musical effect and any mapping that Pyo's generic docstring cannot express.

## Timing and state

Continuous patches use `ContinuousSequencer` and ordinary live Pyo controls. Clocked or generative patches preserve their sequence index, random state, and callback objects. Synthesis parameters should still update live. Timing parameters require custom setters that update or resubscribe the existing sequencer; they are not ordinary `PyoParamRef` controls unless the runtime behavior is genuinely equivalent.

## Notebook contract

Notebook cells should need one call:

```python
soundscape_fm.widget(rack, preset_controller)
```

Do not duplicate checkbox, slider construction, preset registration, or `interactive_output` plumbing in individual modules. Keep patch-specific ranges, defaults, descriptions, Pyo references, and custom update behavior in the patch module.

## Migration checklist

When adding or migrating a patch:

1. Define `PARAMETERS` in build-parameter order.
2. Add real Pyo references where they accurately describe the control.
3. Create live Pyo controls in `build` for non-structural parameters.
4. Return `Patch(..., controls={...})` with setters that preserve runtime state.
5. Retain all auxiliary Pyo graph nodes with `Patch(resources=(...))`.
6. Use `patch_widget` for standard controls.
7. Keep custom timing/state setters explicit and test that slider changes preserve the active `Patch`.
8. Run manual-backend DSP processing for concurrent instances; isolate native-crash regressions in a subprocess.
9. Run targeted diagnostics and Ruff checks.
