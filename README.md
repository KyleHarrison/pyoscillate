brew update
brew reinstall flac
brew install ffmpeg
?

brew install liblo libsndfile portaudio portmidi

Here's the conceptual map — Pyo's classes fall into a handful of roles, and every patch is just wiring these roles together into a graph. Each role is documented in its own file under [`.claude/skills/pyo-music/references/pyo-api/`](.claude/skills/pyo-music/references/pyo-api/): a short module docstring explains the role, and every class it imports from `pyo` carries a simplified docstring of its constructor params right below the import.

**How they combine — the actual pattern in your notebook:**

```
Metro (timing) ──► TrigEnv (amplitude shape) ──┐
Metro (timing) ──► TrigXnoiseMidi (pitch)   ────┼──► Osc (generator) ──► Compress (dynamics) ──► .out()
```

The general template is always: **timing source → triggered control objects → parameters of a generator/effect → dynamics → output.** Continuous modulators (LFOs) plug into the same parameter slots as triggered ones — the difference is just whether the modulation is event-driven (one-shot, gated) or free-running (cyclical, ungated). Once you see every object as one of the roles below, reading any Pyo patch becomes: trace each wire backward from `.out()` and ask "what role is feeding this parameter, and is it one-shot or continuous?"

| # | Role | File |
|---|---|---|
| 1 | Server — the audio engine | [`core/01_server.py`](.claude/skills/pyo-music/references/pyo-api/core/01_server.py) |
| 2 | Signal generators (sources) | [`core/02_generators.py`](.claude/skills/pyo-music/references/pyo-api/core/02_generators.py) |
| 3 | Tables — shapes/data generators read from | [`core/03_tables.py`](.claude/skills/pyo-music/references/pyo-api/core/03_tables.py) |
| 4 | Triggers / event sources | [`core/04_triggers.py`](.claude/skills/pyo-music/references/pyo-api/core/04_triggers.py) |
| 5 | Trig-reactive objects | [`core/05_trig_reactive.py`](.claude/skills/pyo-music/references/pyo-api/core/05_trig_reactive.py) |
| 6 | Envelopes / control signals | [`core/06_envelopes.py`](.claude/skills/pyo-music/references/pyo-api/core/06_envelopes.py) |
| 7 | Modulators (continuous, non-triggered) | [`core/07_modulators.py`](.claude/skills/pyo-music/references/pyo-api/core/07_modulators.py) |
| 8 | Filters & effects | [`core/08_filters_effects.py`](.claude/skills/pyo-music/references/pyo-api/core/08_filters_effects.py) |
| 9 | Dynamics (gain management), e.g. `Compress` in [`base.py`](src/pyoscillate/patches/base.py) | [`core/09_dynamics.py`](.claude/skills/pyo-music/references/pyo-api/core/09_dynamics.py) |
| 10 | Output — `.out()` / `.play()` | [`core/10_output.py`](.claude/skills/pyo-music/references/pyo-api/core/10_output.py) |

**Everything else in Pyo** — the roles above (all in [`.claude/skills/pyo-music/references/pyo-api/core/`](.claude/skills/pyo-music/references/pyo-api/core/)) cover every category this project actually uses. Pyo's [full API](https://belangeo.github.io/pyo/api/index.html) groups its remaining classes into categories this project doesn't touch (yet), organized under [`.claude/skills/pyo-music/references/pyo-api/`](.claude/skills/pyo-music/references/pyo-api/) by similarity of use:

| Sub-dir | Groups | Files |
|---|---|---|
| [`analysis/`](.claude/skills/pyo-music/references/pyo-api/analysis/) | Measuring and converting signals/values | [`signal_analysis.py`](.claude/skills/pyo-music/references/pyo-api/analysis/signal_analysis.py), [`arithmetic.py`](.claude/skills/pyo-music/references/pyo-api/analysis/arithmetic.py), [`expression.py`](.claude/skills/pyo-music/references/pyo-api/analysis/expression.py), [`utils.py`](.claude/skills/pyo-music/references/pyo-api/analysis/utils.py) |
| [`spectral/`](.claude/skills/pyo-music/references/pyo-api/spectral/) | Frequency-domain processing | [`fourier.py`](.claude/skills/pyo-music/references/pyo-api/spectral/fourier.py), [`pvoc.py`](.claude/skills/pyo-music/references/pyo-api/spectral/pvoc.py) |
| [`sequencing/`](.claude/skills/pyo-music/references/pyo-api/sequencing/) | Python-level / declarative event sequencing | [`event_sequencing.py`](.claude/skills/pyo-music/references/pyo-api/sequencing/event_sequencing.py), [`events_framework.py`](.claude/skills/pyo-music/references/pyo-api/sequencing/events_framework.py), [`mml.py`](.claude/skills/pyo-music/references/pyo-api/sequencing/mml.py) |
| [`external_io/`](.claude/skills/pyo-music/references/pyo-api/external_io/) | External device & network I/O | [`midi.py`](.claude/skills/pyo-music/references/pyo-api/external_io/midi.py), [`opensndctrl.py`](.claude/skills/pyo-music/references/pyo-api/external_io/opensndctrl.py), [`listeners.py`](.claude/skills/pyo-music/references/pyo-api/external_io/listeners.py) |
| [`control/`](.claude/skills/pyo-music/references/pyo-api/control/) | Non-audio control-signal helpers | [`randoms.py`](.claude/skills/pyo-music/references/pyo-api/control/randoms.py), [`value_converters.py`](.claude/skills/pyo-music/references/pyo-api/control/value_converters.py) |
| [`playback_routing/`](.claude/skills/pyo-music/references/pyo-api/playback_routing/) | Soundfile playback, channel routing, 2D data | [`players.py`](.claude/skills/pyo-music/references/pyo-api/playback_routing/players.py), [`routing.py`](.claude/skills/pyo-music/references/pyo-api/playback_routing/routing.py), [`matrix.py`](.claude/skills/pyo-music/references/pyo-api/playback_routing/matrix.py) |

(`Internal objects` and the WxPython GUI widgets are implementation details / legacy GUI helpers and are omitted.)