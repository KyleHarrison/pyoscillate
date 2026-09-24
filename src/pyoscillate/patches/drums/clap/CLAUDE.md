# Clap

## Sonic function

A clap is a short, noisy rhythmic accent. Its characteristic identity comes
from several nearby noise bursts rather than from a stable pitch: the small
timing differences create a fuzzy, human-like attack.

## Minimal architecture

trigger
→ repeated short amplitude bursts
→ white-noise source
→ band-pass filtering
→ output

Optional:
→ transient layer
→ saturation

## Burst structure

The repeat count and spacing shape the impression of several hands arriving at
nearly the same time.

More repeats or longer spacing:
- wider
- fuzzier
- more animated

Fewer repeats or shorter spacing:
- tighter
- more direct
- closer to a single noise hit

## Noise spectrum

White noise provides the broadband material. A band-pass filter concentrates it
into the bright, papery region that makes the clap articulate in a mix.

Increasing the filter frequency generally makes the clap thinner and sharper;
lowering it makes the accent fuller and less brittle. Resonance can add a
focused snap, but too much becomes ringing rather than a clap.

## Amplitude envelope

The attack should be short. A strongly exponential decay produces a crisp hit
with a diminishing noisy tail; a less exponential decay sounds more direct and
dry.

## Design alternatives

Dry electronic clap:
    white noise + band-pass filter + short decay

Classic layered clap:
    repeated noise bursts + short final tail

Processed clap:
    repeated noise bursts + filter + mild saturation

## What NOT to assume

There is no universal repeat count, burst spacing, filter frequency, resonance,
or decay. These depend on tempo, register, and the amount of space left by the
other percussion voices.

## Musical references

These point to the music-theory layer for decisions *around* this voice
(pattern, pitch material, role in the arrangement and mix). They do not
cover synthesis; the sections above stay authoritative for the DSP.

- `.claude/skills/music-theory/references/instrument-idiom/drums-percussion.md` — "Backbeat" and "Percussion layers" (claps as backbeat/community feel, layering with snare)
- `.claude/skills/music-theory/references/rhythm-groove/groove-and-feel.md` — "Microtiming", for laid-back or pushed placement relative to the grid (separate from the burst spacing inside the clap)
- `.claude/skills/music-theory/references/genres/electronic-edm.md` — house and UK garage sections, for clap conventions by style
