# Compact patch waveform and spectrum: feasibility and implementation scope

## Assessment

This is a small-to-medium feature with moderate integration difficulty, not an
audio-engine redesign. A basic drawing prototype is straightforward; safe graph
ownership, callback handoff, rebuilds, and engine restarts are the substantive work.

The current architecture already has the required attachment points:

- `src/pyoscillate/patches/base.py`: `Patch.start()` constructs `_output` after
  sidechain processing, volume, compression, clipping, fade, and stereo routing.
  It is separate from the raw `voice` and precedes the server's master gain.
- `src/flet/base.py`: `PatchPanel._apply()` builds and starts the patch; panel
  stop and rebuild paths can attach/detach its analyser.
- `src/flet/base.py`: `PatchRackApp._animate_sweeps()` already schedules UI
  refreshes approximately ten times per second.
- `src/flet/patch/app.py`: the single-patch entry point uses the same rack and
  panel architecture as larger projects. No pluck-specific UI or DSP is needed.

## Confirmed scope

- Two simple embedded views: time-domain waveform and basic frequency spectrum.
- Final patch output, before rack master gain; not raw oscillator or `voice`.
- One trace per view, using the left output channel.
- Enable only in the single-patch app initially; multi-patch rack UIs retain
  their current appearance and do not allocate analysers.
- First acceptance case:
  `pyoscillate.patches.tonal.pluck.pluck`, selecting `PluckHook` through the
  existing module-resolution mechanism.
- Shared reusable implementation, not changes to the pluck synthesis graph.

## Evidence collected

The installed Pyo 1.0.5 implementation provides:

- `Scope(input, length=..., function=...)` for waveform display data.
- `Spectrum(input, size=..., function=...)` for FFT display data.
- Supplying a callback prevents the automatic native wx display window.
- Both callbacks actually deliver lists of `(x, y)` display coordinates,
  grouped by channel, rather than raw PCM samples or calibrated FFT bins.
- `setWidth()` / `setHeight()` bound the drawing data size.
- Spectrum supports logarithmic frequency and magnitude scaling and
  `polltime()`. Scope's polling mechanism is different; do not assume it has
  Spectrum's adjustable polling timer.

A device-free manual-server experiment built and started the actual PluckHook:

- With a 256-by-100 analysis viewport, Scope returned 256 points per channel;
  Spectrum returned 258, including boundary points.
- Processing approximately one second of audio yielded 21 waveform callbacks
  and 10 spectrum callbacks when Spectrum polling was set to 0.1 seconds.
- Native analyser windows remained absent.
- Over two processed seconds, the spectrum had visible non-flat frames;
  quiet frames between plucks were expected.
- Explicitly calling `Scope.setGain(5)` produced an 8-pixel maximum waveform
  span for the pluck. A 0.1-amplitude reference sine produced a 49-pixel span.
  Passing gain only to the constructor did not produce the same visible
  scaling in this experiment: configure and test display gain explicitly.
- Shutdown completed after stopping analysers and processing the patch fade.

Flet's available Canvas/Path APIs support rendering these points directly.
An embedded Flet animation, real-time responsiveness, CPU cost, and repeated
native resource retirement have not yet been verified. Manual processing is
functional evidence, not a real-time performance benchmark.

## Proposed minimal UX

Two short dark plots below the patch header, matching existing colours:

- Waveform: one accent-colour line and a subtle zero baseline.
- Spectrum: one line with sparse frequency labels; logarithmic frequency and
  relative logarithmic magnitude, not an unverified calibrated dBFS meter.
- Responsive stacking on narrow windows; no complex grid or analyser knobs.
- Approximately 10 UI redraws per second, with bounded drawing payloads.
- Initial waveform window: 50 ms; initial FFT: 2048 samples.
- Fixed, documented waveform display gain, validated against a reference
  signal. No automatic normalization that hides actual volume changes.
- An explicit idle state when the patch is disabled or the engine is stopped;
  no stale trace from a previously playing graph.

This is a short moving waveform, not the amplitude envelope of an entire
pluck note. Sparse plucks will naturally alternate signal and near-silence.
Trigger stabilization, peak hold, and a longer envelope/history view are
separate enhancements if the basic prototype proves hard to read.

## Implementation todos

### 1. Exposing the final patch signal

Update `src/pyoscillate/patches/base.py` with a typed read-only output accessor.
Keep graph construction and audible routing unchanged. Define availability
explicitly: no native signal before a successful start, and no supported use
of a retired/stopped output. Avoid UI reads of `_output`.

### 2. Building the bounded analysis bridge

Add `src/pyoscillate/analysis/live.py`:

- Attach Scope and Spectrum to the current output's left stream without
  calling another audible `.out()`.
- Explicitly configure dimensions, gain, FFT size, and scaling.
- Retain analyser instances and callback owners, including objects reached
  through analyser input wrappers and timers.
- Callbacks publish only the newest bounded frame; do not update Flet,
  enqueue unlimited history, or perform expensive work in the audio callback.
- Use a small synchronized snapshot handoff and an attachment generation so
  obsolete callbacks cannot repopulate the display.
- Stop polling and native processing before graph retirement/server shutdown.
  Keep retired analyser/input references alive for the necessary native
  lifetime; verify this with the existing stop-fade discipline.
- Distinguish analyser failure from audio failure. Surface expected errors,
  disable the failed display, and preserve audio where safe.

### 3. Rendering the compact component

Add `src/flet/analysis.py` with Canvas/Path views. Render one path per plot,
not hundreds of independent controls. Reuse the current visual palette and
respond to actual plot dimensions. Copy/snapshot drawing frames outside the
audio callback. Label the monitored signal clearly as pre-master, left output.

### 4. Wiring opt-in UI and lifecycle

Update `src/flet/base.py` and `src/flet/patch/app.py`:

- Add an opt-in constructor option, off by default for existing rack apps.
- Enable it in the single-patch harness.
- Attach only after a patch successfully starts; detach before stop/rebuild.
- Cover parameter rebuild, patch/group enable, pause/resume, preset changes,
  style/rack replacement, engine stop/restart, and page close.
- Extend the existing refresh scheduling rather than adding a competing
  unmanaged loop. Retain/cancel the task or use a generation guard so a quick
  stop/start cannot leave two refresh loops active.
- Update only the analyser controls when appropriate; avoid whole-page
  redraws solely for analysis.
- Preserve parameter and preset schemas. Visualisation is not a synthesis
  `Param` and does not belong in saved audio presets.

### 5. Validating behavior and updating related docs

Add focused native-analysis and Flet wiring tests. Extend
`src/pyoscillate/patches/ARCHITECTURE.md` for the output contract and `README.md`
for the single-patch display.

Validation:

- Deterministic sine: waveform amplitude mapping and spectrum peak position
  agree with the configured viewport/frequency range.
- Real PluckHook: non-flat attack frames, quiet gaps, parameter response,
  pre-master semantics, and left-channel selection.
- Confirm callbacks supply bounded points and do not create wx windows.
- Compare rendered audio with analysis enabled/disabled; no change to output.
- Mocked UI tests: analysis is opt-in, idles when stopped, reattaches on rebuild,
  and ignores obsolete frames.
- Native lifecycle scenarios in isolated subprocesses, following the existing
  Pyo test isolation pattern: repeated enable/rebuild/stop and shutdown without
  stale callbacks or crashes.
- Run focused new tests plus existing pluck and Flet group tests and lint the
  changed modules.
- Manually run the single-patch app through start, enable, slider changes,
  pause/resume, stop/restart and close. Measure redraw rate/payload size and
  check responsiveness without audio dropouts on the intended backend.

Acceptance targets:

- At most one active UI refresh task.
- At most one live analyser pair per monitored patch graph.
- Roughly 10 redraw opportunities per second, never an unbounded queue.
- Analysis coordinates bounded by the chosen viewport, including Spectrum's
  extra boundary points; no full audio-rate sample stream sent to Flet.
- No analyser resources for default multi-patch rack panels.
- No audible routing, parameter, or preset behavior changes.

## Dependencies between todos

- Analysis bridge depends on the output accessor.
- Canvas rendering can be developed independently of the native bridge using
  synthetic coordinate frames.
- UI/lifecycle integration depends on both the bridge and renderer.
- End-to-end validation/documentation depends on integration.

## Risks and boundaries

The main risk is native lifecycle/thread safety, not FFT mathematics. Pyo keeps
native streams alive and the project explicitly preserves retired graphs
through fade-out. An analyser is another graph consumer and must participate
in that discipline.

The callback coordinates are useful for a compact visual display but should
not be presented as a general raw-sample API. A calibrated measurement tool
would need additional verification or a separate raw analysis path.

Out of scope: FFT implementation, audio-input capture, waveform recording,
export, triggering controls, zoom/gain knobs, freeze/history, 3D/wavetable
visuals, spectrum peak readouts, master-bus analysis, and enabling every rack
patch simultaneously.

The repository currently has substantial uncommitted changes, including the
shared UI and pluck. Planning has not changed any repository files. Future
implementation must integrate those changes rather than overwrite them.
