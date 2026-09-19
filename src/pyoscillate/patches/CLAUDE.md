# Patch Architecture

This directory contains notebook-first Pyo patches. Every patch module follows one public shape:

- `PARAMETERS`: an ordered tuple of `SliderSpec` values describing notebook controls.
- `build(...) -> Patch`: constructs the Pyo graph once and returns its runtime state.
- `widget(rack, ..., controller=None)`: delegates standard controls to `patch_widget(...)`.

## Construction and runtime

Keep `build` as a function. Do not create a class for every patch. A function keeps the signal graph local and easy for an agent to inspect. Use a small private class only when a patch owns unusual persistent sequencing behavior, such as multiple Metros or callback keepalive references.

`Patch` owns start/stop, output fading, compression, live controls, and volume. A parameter that can change without changing graph topology must be represented by a live Pyo control such as `SigTo` and exposed through `Patch.controls`. Widget changes call `Patch.update(...)`; they must not rebuild or restart an active patch.

A graph rebuild is appropriate only for structural changes: changing the number of voices, routing topology, fixed tables, or a buffer limit. Structural rebuild behavior must be explicit rather than accidental.

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
5. Use `patch_widget` for standard controls.
6. Keep custom timing/state setters explicit and test that slider changes preserve the active `Patch`.
7. Run targeted diagnostics and Ruff checks.
