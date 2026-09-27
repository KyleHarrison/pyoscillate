# Drone

## Sonic function

A drone is an ungated, continuous pitched voice: it holds a stable pitch
centre and never articulates notes. It works as a bed — the keynote layer that
other voices are heard against — and its interest comes from slow change
underneath the held pitch rather than from events.

Any register belongs here. A sub drone and a mid-range drone share the same
role and construction; register is a parameter of the patch, not a separate
family.

## Minimal architecture

pitched source (held, amplitude open)
→ one or more slow modulation sources (LFO, random, chaotic attractor, swell)
→ applied to a chosen dimension of the sound
→ optional spatial treatment

There is no trigger-to-envelope path. If a patch needs one, it is not a drone.

## What moves

Drones in this family are best distinguished by which dimension the modulation
drives, because that decides what the listener tracks:

- **timbre** — spectral content changes under a held pitch (e.g. FM ratio or
  index, waveform, harmonic balance)
- **filter** — a fixed rich spectrum is carved by a moving cutoff or resonance
- **space** — the tone itself is fairly static; movement comes from chorus,
  delay, and reverb smear
- **level** — the drone breathes in amplitude
- **micro-pitch** — the centre wanders within a range narrow enough that it
  never reads as a note change
- **slow pitch steps** — the centre itself moves rarely (bars, not beats) and
  glides, so it still reads as held rather than melodic

A new drone should state which dimension it moves. Two drones moving the same
dimension with the same modulation character are one patch with different
settings.

## Distinguish from

- **pad** (`tonal/pad`): a pad carries harmony that changes on events and uses
  envelopes; a drone holds one centre.
- **bass** (`tonal/bass`): a bassline is gated and articulates notes against
  the kick; a sub drone is continuous weight.
- **texture** (`texture/`): texture has no stable pitch centre (noise, grains,
  chaos used as timbre); a drone always has one.
- **soundscape**: a rack-level arrangement of layers, not a patch. Drones are
  one of its building blocks.

## What NOT to assume

"Drone" does not mean static. A drone with nothing moving is a test tone; the
choice of what moves, how fast, and how predictably is the design. Equally,
movement that becomes fast or wide enough to be tracked as events — audible
pitch bends, rhythmic swells, obvious sweeps — has left the drone role.

## To be written from sources

The mechanism-level sections (detuned stacks and beating, chaotic modulation
character, FM timbre drift, filter sweeps, spatial smear) should be distilled
from the sources listed in `docs/todos/sources.md` rather than written from
memory.

## Musical references

These point to the music-theory layer for decisions *around* this voice
(pitch centre, tuning, role in the arrangement and mix). They do not
cover synthesis; the sections above stay authoritative for the DSP.

- `.claude/skills/music-theory/references/harmony/modal-harmony.md` — "How modal music establishes its tonal center (without a leading tone)", for choosing a centre that other voices can move against
- `.claude/skills/music-theory/references/techniques/microtonal.md` — "Cents" and "Just intonation", for tuning stacked or detuned drone layers and the beating between them
- `.claude/skills/music-theory/references/techniques/20th-century-techniques.md` — "Minimalism and process music" and "Spectralism", for sustained-tone and slow-process thinking
- `.claude/skills/music-theory/references/production-aware/arrangement-for-mix.md` — "Kick and bass — the perennial challenge" and "Stereo space", for sub drones under a kick and wide beds
- `.claude/skills/music-theory/references/production-aware/energy-and-dynamics.md` — "Reverb and delay — atmosphere", for the spatial dimension
