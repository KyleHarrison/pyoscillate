# TODO: incorporate ideas from the "Generating Synth Patches with AI" gist

Source: [0xdevalias, *Generating Synth Patches with AI*](https://gist.github.com/0xdevalias/5a06349b376d01b2a76ad27a86b08c1b)
(reviewed 2026-09-24). It is a curated link dump on ML-driven synth patch
generation: research papers, VST hosting tools, Serum/Vital preset formats,
datasets, and brainstorming. Most of it does not apply to a Pyo-native project.
This file records the few ideas worth keeping and the order to add them in.

## How to use this file (for future sessions)

1. Work through the tasks in order. Tasks 1 and 2 come first because later tasks build on them.
2. Before editing, re-read the files a task touches. They may have changed since this was written.
3. Respect the existing layering. Don't duplicate contracts between layers:
   - [.claude/skills/pyo-music/SKILL.md](../../.claude/skills/pyo-music/SKILL.md) holds the sonic/perceptual reasoning.
   - [src/pyoscillate/patches/AGENTS.md](../../src/pyoscillate/patches/AGENTS.md) holds the runtime/patch contract.
   - The nested `AGENTS.md` files in each patch-type directory hold that family's sonic concept.
   - [AGENTS.md](../../AGENTS.md) holds project scaffolding.
4. Keep the foundational principle: **never map a word directly to a Pyo
   object.** Every descriptor or reference must go through perception → measurable
   correlate → several candidate mechanisms.
5. When a task is done, tick it here, note the commit or files, and add anything learned.
6. Use `uv run` for any Python (for example `uv run python -c "..."`, `uv run ruff check src`).

## Why these ideas matter here

The papers in the gist (CTAG, SerumRNN, InverSynth, Syntheon, preset-gen-vae)
share one lesson: patch generation only works with **audio feedback**. Render
the patch, measure the audio, compare it with the target, and adjust. Our
agent writes patches it has never heard. Pyo already has everything needed to
fix that without new dependencies:

- `Server(audio="offline")` for offline rendering
- `Centroid` for brightness
- `Follower` / `PeakAmp` for the envelope and punch
- `Yin` for pitch and stability
- `AttackDetector` for transients
- `Spectrum` for spectral shape

References: [pyo-api/analysis/analysis.py](../../.claude/skills/pyo-music/references/pyo-api/analysis/analysis.py)
and [pyo-api/core/server.py](../../.claude/skills/pyo-music/references/pyo-api/core/server.py).

## Tasks

### 1. Timbre-descriptor reference — [x] done (2026-09-24)

**Why:** pyo-music says not to map "metallic" → `Resonx`, but gives nothing to
use instead. The gist points to two sources: the NSynth quality labels and the
Arturia/"Make That Sound More Metallic" work on perceptually relevant timbre
control.

**Do:**
- Create `.claude/skills/pyo-music/references/timbre-descriptors.md`.
- For each descriptor, give:
  - a perceptual definition
  - a measurable correlate (centroid, envelope slope, inharmonicity, noise ratio, pitch stability, and so on)
  - 2–4 *different* candidate mechanisms
  - context caveats, in the "do not overclaim" style already in pyo-music
- Include these descriptors:
  - the NSynth set: bright, dark, distortion, fast_decay, long_release, multiphonic, nonlinear_env, percussive, reverb, tempo-synced
  - common extras: metallic, warm, hollow, airy, punchy, gritty, glassy, wide
- Example row: *metallic* → inharmonic partials / partial ratios off the harmonic series → FM with a non-integer ratio, a resonator bank, ring modulation, or comb/Karplus feedback.
- Link it from the "Parameter reasoning standard" section of pyo-music SKILL.md.

**Done when:** the reference exists, it is linked, and no descriptor maps to a single Pyo object.

### 2. Render-and-verify step — [ ] not started (depends on 1)

**Why:** this closes the loop between the brief and the audio (see "Why these ideas matter here").

**Do:**
- In pyo-music SKILL.md, add step 8 to the "Minimal working pattern": render
  offline and check the measurable correlates from task 1 against the brief.
  Example: "raising Brightness raises the centroid"; "Decay 0.3 s reaches −40 dB in about 0.3 s".
- In patches/AGENTS.md, add an optional item to the quality bar: key controls
  move their correlate in the direction the label promises. Keep the
  implementation detail out of that file and point to a helper instead.
- Build a small helper, possibly `src/pyoscillate/analysis/` or a test
  utility next to [tests/](../../tests/). It should:
  - boot an offline `Server`
  - build a patch
  - render N seconds with `recordOptions` / `recstart`
  - run the analysis objects
  - return a small feature dict
- Check how the existing tests boot a server, and follow that.
- Add one example test on an existing patch, such as a kick (Decay) or a pad (Brightness).

**Done when:** the helper runs through `uv run pytest`, one patch has a perceptual-direction test, and both docs reference the step.

**Watch out:** graph-ownership rules still apply inside the offline render.
Retain everything in `resources`. Shut the server down cleanly between renders.

### 3. Divergent strategies before implementing — [ ] not started

**Why:** the QDax/quality-diversity note says "multiple and very different
solutions can exist". Synplant (genetic) and Vinetics (merging presets) take
the same view. This is our foundational principle stated as a search method.

**Do:**
- In pyo-music SKILL.md, add a step between SONIC INTENT and DSP MECHANISM:
  for open briefs, propose 2–3 genuinely different synthesis strategies with
  their tradeoffs (character, CPU, how controllable it is, which family it
  fits). Then choose one, or ask.
- Link to [revision-and-feedback-loops.md](../../.claude/skills/music-theory/references/creative-workflows/revision-and-feedback-loops.md).
- Say when to skip this: tightly specified requests, or an edit to an existing patch.

### 4. References to commercial synths and presets — [ ] not started

**Why:** the Serum→Vital thread shows that conversion between synths isn't 1:1.
Different engines have different defaults ("Vital warm, Serum crisp").

**Do:**
- Extend the "inspired by a recording/artist/scene" section in
  [pyo-api-navigation.md](../../.claude/skills/pyo-music/references/pyo-api-navigation.md)
  (around line 86) to cover references like "a Serum supersaw" or "a DX7 E-piano".
- Treat a reference as a *perceptual target*. Run it through the normal chain
  and the task 1 descriptors. Never copy knob or parameter values.
- Add a short by-ear reverse-engineering checklist: oscillator/source →
  filter → envelopes → modulation → FX/space → register/playing. It is based
  on the Unison guide: https://unison.audio/reverse-engineer-presets-in-serum/

### 5. Continuous vs categorical parameters; presets that blend — [ ] not started

**Why:** preset-gen-vae models parameters as a mix of numerical and categorical
variables. The latent-morph work (Neural Wavetable, the VAE papers) shows the
value of interpolating between presets.

**Do:**
- In patches/AGENTS.md, add to design rule 3 ("Parameter changes should usually be live"):
  - Continuous controls must be interpolable, so any blend between two presets sounds musical.
  - Categorical choices (waveform, topology, table) belong in profiles or rebuilds, never inside a slider's range.
- Note this as the groundwork for a future preset-morph feature using `SigTo`
  in the Flet app. Don't build that feature as part of this task.

### 6. Slider ranges as the space you can explore safely — [ ] not started

**Why:** random patch generators (RenderMan's `PatchGenerator`, the VST Preset
Generator, the random-preset GANs) only work when the parameter ranges are
musically bounded.

**Do:**
- In patches/AGENTS.md, add to design rule 2: choose each `SliderSpec`
  min/max so that every value in the range is usable. That makes a future
  randomise/mutate action safe to build.
- Optionally, audit a few existing patches for ranges that go past the useful
  zone, and list what you find here instead of fixing them all at once.

### 7. Change one thing at a time, and say what it did — [ ] not started

**Why:** SerumRNN gives step-by-step instructions, one effect change at a
time, and finds that the order of effects matters.

**Do:**
- In pyo-music SKILL.md, add to the "Parameter reasoning standard": when
  revising toward a target, change one parameter or stage per step, describe
  the perceptual result, and re-verify with task 2 when possible.

### 8. Mechanism notes for patch families — [ ] fold in as each family is filled

These are not standalone tasks. Apply each one when its family's placeholder
`AGENTS.md` is filled in:

- **tonal/bass/acid**
  ([AGENTS.md](../../src/pyoscillate/patches/tonal/bass/acid/AGENTS.md)):
  - The DiffAPF paper (https://arxiv.org/abs/2404.07970,
    https://github.com/DiffAPF/TB-303) models the 303 as a mono oscillator →
    biquad whose cutoff sweeps fast with a per-note envelope ("squelch") →
    waveshaper *after* the filter. This confirms the draft architecture. Cite it
    alongside the Devil Fish manual already in [sources.md](sources.md).
  - The Abstract 303 pack
    (https://www.samplescience.info/2022/05/abstract-303.html) is a
    royalty-free, dry reference for A/B listening.
- **Layer A modulation/effects** (patches/AGENTS.md mechanism list, or a
  future effects/modulation family doc), from the mod_extraction paper
  (https://arxiv.org/abs/2305.13262):
  - A phaser is cascaded all-pass filters plus a dry path plus optional
    feedback (the EHX Small Stone uses 4 stages).
  - Chorus and flanger are delays whose time is modulated by an LFO.
  - The LFO shape can be quasi-periodic, combined, or distorted, not only a sine.

### 9. Sources to add to [sources.md](sources.md) — [ ] not started

Add these to the "Sources that cover several patches" table:

- [instatetragrammaton/Patches](https://github.com/instatetragrammaton/Patches): clean-room remakes of well-known sounds, with the theory explained. The best find in the gist for writing family docs.
- [Syntorial](https://www.syntorial.com/): paid. Its lesson progression is a model for the order in which to write family docs.
- [Unison: reverse-engineer any preset](https://unison.audio/reverse-engineer-presets-in-serum/): the by-ear procedure (also used in task 4).
- [CTAG](https://ctag.media.mit.edu/): sounds made from a small, interpretable parameter set (78 parameters) capture the "essence" of a prompt, like a sketch. This supports keeping each patch's control surface small and musical.

## Deliberately out of scope

- **Serum `.fxp` / `.SerumPreset` / Vital formats and VST hosting**
  (DawDreamer, Pedalboard, RenderMan): not relevant to Pyo. The only reason
  to revisit them would be A/B comparison against a real VST.
- **Training datasets and ML architectures** (VAE/GAN/RNN, data bucketing):
  we reason about patches; we don't train models.
- **Metadata tagging** (NSynth-style source/family/qualities on `PatchDef` for
  searching by vibe): maybe later, once the library is big enough to need search.
  If picked up, reuse the task 1 descriptor vocabulary.

## Log

- 2026-09-24: gist reviewed; this plan written.
- 2026-09-24: task 1 done.
  - Added `.claude/skills/pyo-music/references/timbre-descriptors.md` with 19 descriptors in 5 groups.
  - Linked it from pyo-music SKILL.md: the routing list, the reasoning model, and step 2 of the parameter reasoning standard.
  - Every cited Pyo object and parameter was checked against `pyo-api/`.
  - Findings for task 2:
    - Native Pyo can measure centroid, envelope, attack, decay and pitch (`Centroid`, `Follower`, `PeakAmp`, `AttackDetector`, `Yin`, `AToDB`).
    - Harmonicity, even/odd balance and stereo correlation have no native object. They need an offline FFT, and **numpy is not currently a dependency**. Decide whether to add it (probably as a dev/test dependency) or to limit verification to the native correlates.
