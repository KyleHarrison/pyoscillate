# Breakbeats — Slicing and Rearrangement

A breakbeat is a recorded drum loop cut into equal slices and resequenced.
The musical decisions are how finely to slice, which slices to reorder,
repeat, reverse or re-pitch, and what tempo and genre frame to put it in.
For the style background see `../genres/electronic-edm.md`.

## Slice count

| Slices | Over | Resolution |
|---|---|---|
| 8 | 1 bar | 8th notes (most common) |
| 16 | 1 bar | 16th notes (fine chops) |
| 16 | 2 bars | 8th notes on a 2-bar loop |
| 4 | 1 bar | quarter notes (coarse, big swaps) |

Straight playback is the identity order: `0 1 2 3 4 5 6 7`.

## Rearrangement techniques

Slice orders below assume 8 slices over 1 bar. A negative index means "play
that slice reversed".

| Technique | Order | Effect |
|---|---|---|
| Swap halves | `4 5 6 7 0 1 2 3` | flips the bar |
| Stutter | `0 0 0 0 4 5 6 7` | tension, roll |
| Snare roll | `0 1 2 3 4 4 4 4` | repeat the snare slice |
| Drop and replace | `0 0 2 3 4 0 6 7` | weak slices replaced by the kick slice |
| Reverse slices | `0 1 -2 3 4 5 -6 7` | turntable-style reversals |
| Reverse second half | `0 1 2 3 -7 -6 -5 -4` | backwards tail |
| Jungle chop | `0 0 3 2 7 6 5 4` | new groove from old material |
| Halftime | 8 slices over 2 bars, `0 0 1 1 2 2 3 3` | stretched, heavy feel |

## Per-slice rate

Playback rate changes speed *and* pitch together (2 = octave up and double
speed, 0.5 = octave down and half speed).

- **Double-time the last two slices:** rates `1 1 1 1 1 1 2 2`.
- **Pitched-down intro, normal drop:** whole loop at 0.5, then at 1.
- **Random variation:** choose each slice's rate from `1 1 1 1 1.5 0.75` so
  most slices stay put.

## Genre applications

### Jungle / DnB (160–175 BPM)
Heavy rearrangement, fast tempo, snare on beat 3; the Amen break is the
canonical source. 16 slices, e.g.
`0 0 4 3 8 9 -10 7 0 1 12 3 8 8 14 15`.

### Hip-hop (85–95 BPM)
Slower; keep the original groove mostly intact with subtle swaps. 8 slices
over 2 bars, near-identity order.

### Breakcore (160–300 BPM)
Extreme slicing, stutters, reversals, rapid rate changes:

```text
order: 0 0 0 3 -4 -4 6 7 0 0 12 -3 8 8 8 8
rate:  1 2 2 1 1  1  1.5 .5 1 2 1 -1 2 2 4 4
```

## Layering breaks with programmed drums

- A programmed kick reinforces the break's low end (e.g. step lengths
  `1 1 .75 .25 1`, amp ≈ .5).
- The break, turned down (≈ .25), supplies texture and ghost notes.

## Processing breaks

Typical treatments: bit-crushing (≈ 8 bits, ≈ 8 kHz sample rate) for grit, a
resonant low-pass (≈ 2 kHz, high resonance) for filtered builds, distortion
for weight. These are choices about character; the pyo-music skill decides
the implementation.

---
Adapted from claude-collider (Jeremy Ruppel, MIT). See [`overview.md`](overview.md#attribution).
