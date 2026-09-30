# Testing patches

This file covers how to test what a patch *sounds like*. The patch
lifecycle/runtime contract itself lives in
[src/pyoscillate/patches/AGENTS.md](../src/pyoscillate/patches/AGENTS.md), and
the perceptual vocabulary (descriptor → measurable correlate) lives in
[timbre-descriptors.md](../.claude/skills/pyo-music/references/timbre-descriptors.md).
Don't duplicate either here.

## The core rule

**If you can say what counts as a pass before the brief exists, it is a
pytest. If it depends on the brief, it is agent judgement, not a test.**

An agent deciding "did the centroid go up when Brightness went up?" is a unit
test with extra steps: slower, not reproducible, and able to pass for the wrong
reason. Write it down as a test. Agentic evaluation only adds value where the
pass/fail rule can't be written in advance.

## Three layers

### 1. Measurement: deterministic, and it never decides anything

`pyoscillate.analysis` renders a patch offline and returns measured features.
It is the agent's ears, and tests use the same code.

```
uv run python -m pyoscillate.analysis pyoscillate.patches.drums.clap.clap \
    --set decay=0.3 --seconds 1.2 --ceiling 0.18
```

- `render(module, params, seconds=..., bpm=...)` builds the patch with a full
  `BuildContext`, starts it on a real `Clock`, and records the server output in a **fresh subprocess**.
  Pyo keeps one native server per process and does not survive repeated
  boot/shutdown reliably, so never boot a real server inside the pytest process.
- `render()` plays the patch at its `volume` Param's default (the level its
  volume slider starts at), so the output goes through the patch limiter the way the
  listener hears it. Put `volume` in `params` to override that. `params` maps
  `Param` names to values (written by matching `param.name`), plus an optional
  `style` that selects the subclass - both are CLI-string boundaries; tests
  themselves iterate `patch.params` and never look a parameter up by string.
- `render(..., clock_running=False)` starts the patch but never ticks the
  clock. A gated patch must be silent in that state.
- `features(render, ceiling=...)` returns level and clipping, plus onset,
  peak, decay time, RMS, spectral centroid and zero-crossing rate for each hit.
- The server's global seed is fixed, so noise-based patches render the same
  samples every run.
- numpy (a dev dependency) provides the FFT. Harmonicity and stereo
  correlation aren't measured yet. Add them to `features.py` when a test
  needs them, not in the test itself.

### 2. Contracts: pytest, and they stay valid whatever the brief

Test what a control's **label and help text promise**, not what its current
tuning happens to produce:

- **Direction:** raising Brightness raises the brightness correlate. Compare two
  renders from the same run. No magic numbers.
- **Tolerance band:** Tail 0.3 s ends within ±30% of the envelope length the
  patch asks for. Derive the expectation from the patch's own constants.
- **Invariance a docstring claims:** "Brightness keeps loudness steady" →
  RMS moves less than ~1.5 dB across the range.
- **Health, on every patch:** hits land where the pattern says, it is silent
  before the first one, the tail dies before the next hit, and no value in a
  slider's range hard-clips at the default volume (test the loudest corner of
  the range).

Never assert golden values or snapshot a render. Retuning a patch must not
break its tests unless it breaks a promise.

### 3. Judgement: agentic, specific to the brief, never in `tests/`

"Is this warm enough for this brief?" or "is the grit coming from the filter
or the drive?" The agent reads probe output against the descriptor reference
and decides what to change next, one change at a time. The result is a
revision, not a pass/fail. This belongs in the pyo-music skill workflow.

## Writing a patch test

- Mirror the source layout: `src/pyoscillate/patches/drums/clap/clap.py` →
  `tests/pyoscillate/patches/drums/clap/test_clap.py`. pytest runs in
  `importlib` mode, so no `__init__.py` files are needed and
  `tests/pyoscillate/` does not shadow the real package.
- Match the existing style: `unittest.TestCase` classes, run by pytest.
- Wrap renders in `functools.cache`. Several tests share a render, and each
  render costs a subprocess.
- Measure the hit you scheduled (select it by expected onset), not
  `hits[0]`. That keeps a stray hit from breaking every direction test.
- Take measurements at a level safely below `PATCH_OUTPUT_CEILING`. At the
  ceiling, the limiter flattens exactly what a Level or Drive control is supposed
  to change.
- When a measurement looks wrong, check the measurement layer before blaming
  the patch. Print the envelope. The clap test found a bug in
  `features.py`, not in the clap.
- Not every control has a correlate you can measure yet (for example, the clap's
  Width). Leave it untested rather than asserting a weak proxy, and leave it to
  layer 3.

## Defects: test first, then document, then fix

This is **required** whenever a test finds a defect in a patch, or leads
to a change in one.

1. **Write the test first**, asserting the correct behaviour, and watch it
   fail for the reason you expect. Don't loosen the assertion to make it pass,
   and don't mark it `expectedFailure` to hide it.
2. **Record the finding in the test module's docstring**, under a
   `Findings` heading, with one numbered entry per defect:

   ```
   Findings
   ========

   1. <short title>
   ----------------
   Error:
       What was observed, with the measured numbers (peaks, times, dB) and
       what should have been observed instead.
   Cause:
       Why it happens, down to the object or constant responsible.
   Change:
       What was changed and why that fixes it, including how the fix was
       checked (an offline experiment, a before/after measurement).
   Status:
       "fix pending - <test> fails until then", or "fixed", with the files
       changed.
   ```

   When a finding turns out to be wrong or incomplete, say so under a
   `Corrected along the way` heading rather than deleting it quietly. A wrong
   first diagnosis is useful to the next reader.
3. **Report to the user before changing patch code** when the fix touches
   musical behaviour: a slider range, a default, gain staging, or anything
   the listener hears differently.
4. **Apply the fix**, confirm the test passes and the rest of the suite still
   passes, and update `Status`.

The docstring stays after the fix. It explains why the test exists and why
the patch looks the way it does.

## Running

```
uv run pytest                      # everything
uv run pytest tests/pyoscillate    # perceptual patch tests only
```
