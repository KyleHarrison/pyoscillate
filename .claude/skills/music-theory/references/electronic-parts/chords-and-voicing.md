# Chord Voicing and Progressions for Electronic Parts

For full voicing theory see `../orchestration/voicing-and-texture.md` and
`../harmony/voice-leading.md`; for jazz shapes see `../../assets/jazz-voicings.md`.

## Voicing rules

### No 3rds below C3 (MIDI 48)
Low intervals are muddy. Below C3 use only roots, 5ths, and octaves; the 3rd
can live in the mid register.

### Pads — open and spread
Spread notes across octaves rather than clustering in one.

```text
bad  (block, one octave): midi 60 64 67 71    C4 E4 G4 B4 — dense, muddy
good (open, spread):      midi 48 67 71 76    C3 G4 B4 E5 — open, clear
```

### Keys and stabs — close voicing is fine
Short sounds in the mid register can cluster; stabs benefit from tight voicing.

```text
midi 64 67 72    E4 G4 C5    step: 0.25, note length: 0.1 beats
```

### Drop-2
Take the second-from-top note of a close voicing and drop it an octave.

```text
close:  midi 60 64 67 71   C E G B
drop-2: midi 55 60 64 71   G3 C4 E4 B4
```

## Voice leading

### Common tones stay, other voices move by step

```text
Dm7:   midi 50 60 65 72   D3 C4 F4 C5
G7:    midi 50 59 65 71   D3 B3 F4 B4   (D stays, others step)
Cmaj7: midi 48 60 64 71   C3 C4 E4 B4   (B stays, others step)
step: 4 beats per chord
```

### Contrary motion
When the bass moves up, upper voices move down (and vice versa). This creates
width and independence.

## Extensions by genre

| Genre | Typical harmony |
|---|---|
| House / techno | Triads and 7ths — keep it simple |
| R&B / neo-soul | 9ths, 11ths, 13ths, altered dominants |
| Ambient | Sus chords, add9, quartal voicings (stacked 4ths) |
| DnB | Minor triads, sometimes 7ths |
| Lo-fi | Maj7, min7, colour notes from the key |

Quartal voicing (ambient) — no clear major/minor, ethereal:

```text
midi 48 53 58 63   C F Bb Eb — all perfect 4ths
```

## Progressions by genre

Avoid the axis progression and its rotations unless asked (see
[`overview.md`](overview.md#6-avoid-the-axis-progression-by-default)).

### House
Minimal harmony — two-chord loops with 7ths.

```text
chords (degrees): [0 2 4 6] → [3 5 0 2]    i7 → iv7    mode: dorian, octave 4, 4 beats each
```

### R&B / neo-soul
Rich chromatic movement — ii9 → V13 → Imaj9.

```text
Dm9:   midi 50 57 62 65 69   (4 beats)
G13:   midi 43 59 62 65 69   (4 beats)
Cmaj9: midi 48 55 64 67 71   (8 beats)
```

### Techno
One chord or a modal centre — let rhythm and timbre do the work.

```text
chord (degrees): [0 2 4]    mode: minor    8 beats, held
```

### DnB
Minor-key movement with tension.

```text
[0 2 4] → [4 6 1] → [3 5 0] → [5 0 2]    i → v → iv → VI    mode: minor, 4 beats each
```

### Ambient / downtempo
Suspended and add9 chords, slow movement.

```text
Csus2 spread: midi 48 55 60 67
Fsus2 spread: midi 53 58 65 72
Dsus2 spread: midi 50 57 62 69
8 beats each
```
