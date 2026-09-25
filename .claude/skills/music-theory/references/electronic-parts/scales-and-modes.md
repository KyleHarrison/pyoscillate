# Scales and Modes for Electronic Genres

Deeper theory: `../fundamentals/pitch-intervals-scales.md`,
`../harmony/modal-harmony.md`, `../../assets/modes-cheatsheet.md`.

## Common scales

| Scale | Character | Genres |
|---|---|---|
| Natural minor | Dark, standard | Most electronic, techno, DnB |
| Dorian | Groovy, hopeful minor | House, deep house, neo-soul |
| Phrygian | Dark, Spanish, tense | Techno, industrial, psytrance |
| Mixolydian | Bright, bluesy | Funk, disco, classic house |
| Harmonic minor | Dramatic, "Eastern" | Trance, psytrance, darkwave |
| Pentatonic minor | Safe, hooky | Everything — never sounds wrong |
| Blues | Gritty, expressive | Hip-hop, R&B, lo-fi |

## Write in degrees

Fix the scale and root once, then write parts as scale degrees. Dorian in D is
the classic deep-house sound:

```text
mode: dorian, root D, octave 4
degrees: 0    2    4     3     2    1    0    -
step:    .5   .5   .25   .25   .5   .5   .5   1
```

Switching scale on the last bar of a phrase adds colour (e.g. minor, minor,
minor, harmonic minor — the raised 7th pulls back to the top).

## Chord tones vs tension notes

| Degrees | Role |
|---|---|
| 0, 2, 4 (root, 3rd, 5th) | Chord tones — safe landing points; resolve here |
| 1, 3 (2nd, 4th) | Mild tension — passing tones and suspensions |
| 5, 6 (6th, 7th) | Colour tones — flavour, especially 7ths in jazz/R&B |

Rule of thumb: start and end phrases on chord tones; use tension notes mid-phrase.

## Chromatic approach notes

Approach a chord tone from a half step below for a jazz/R&B feel. Degrees
can't express chromatic notes, so switch to semitone offsets for those
passages:

```text
notes: 5 6 7    chromatic walk up to the 5th (7 semitones above the root)
```

## Mode selection guide

1. **Default safe choice:** natural minor or pentatonic minor
2. **Groovier?** Dorian (raised 6th)
3. **More tension?** Phrygian (flat 2nd) or harmonic minor
4. **Brighter?** Mixolydian
5. **No wrong notes?** Pentatonic minor — 5 notes, all consonant

