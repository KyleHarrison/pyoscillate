# Lofi

An 80 BPM lofi hip-hop rack built around a dusty electric-piano chord loop, a
muted sub bass, soft boom-bap-adjacent drums, and a continuous vinyl-dust /
tape-wobble texture bed. Everything sits behind the beat with an MPC-style
swing rather than a quantized grid — the goal is a hazy, "beats to study to"
loop rather than an energetic dance groove.

## Musical brief

- **Tempo/feel:** 80 BPM, swung 16ths, behind-the-beat pocket, ghost notes on
  hats/snare — see `.claude/skills/music-theory/references/rhythm-groove/groove-and-feel.md`
  and `genres/hip-hop-rnb.md` ("Cloud rap / lo-fi hip-hop").
- **Harmony:** a static, jazz-influenced vamp rather than a developing song
  form — `Dm9–G13–Cmaj7–Am9`, one chord per bar, four-bar loop.
- **Form:** a single repeating loop with subtle per-cycle variation, not a
  verse/hook structure — this is an instrument rack, not a fixed track.

## Concept-to-patch mapping

| Concept | Patch | Notes |
|---|---|---|
| Dusty Rhodes/keys chord loop | `tonal/keys` | Existing FM electric-piano voice; comps the vamp in close rootless voicings. Adds a slow pitch-drift ("Wobble") param — separate from its existing tremolo throb — as the tape wow-and-flutter mechanism. |
| Muted sub bass | `tonal/bass` | Reuses an existing muted/dub style, re-rooting on the same chord as the keys. |
| Vinyl dust / crackle | `texture/noise` | New style layering the existing colored-noise bed (pink/brown blend) with sparse randomized click/pop transients, so the dust reads as discrete grain rather than steady hiss. |
| Soft boom-bap drums | `drums/kick`, `drums/snare`, `drums/hat` | New softened style per family: closed low-pass, light saturation, MPC-style swing with ghost notes — the 80 BPM boom-bap-adjacent pocket rather than deep_house's four-on-the-floor feel. |

## Shared harmony

`HARMONY` in `rack.py` holds one key and one vamp — `Dm9–G13–Cmaj7–Am9`, one
chord per bar, four bars per loop. The keys and bass patches re-root on the
same bar from the shared clock, so both change chord together regardless of
their own Rate sliders.

## Status

This README documents the grounded musical/sonic brief agreed before
implementation (see `src/pyoscillate/projects/CLAUDE.md`). `rack.py` and the
patch changes above are not yet implemented.
