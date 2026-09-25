# Bass Lines

A bass line that only plays the root of each chord is a placeholder, not a
part. For the broader idiom (walking bass, electric bass role) see
`../instrument-idiom/bass.md`.

## Beyond root notes

### Root–5th alternation
The simplest upgrade.

```text
degrees: 0 4 0 4    octave: 3    step: 0.5
```

### Octave jumps for energy
Drop to the low octave, jump up for emphasis.

```text
degrees: 0 0 0 0    octave: 2 3 2 2
```

### Approach notes
A chromatic half-step into the next chord's root creates forward motion.

```text
notes: 0 0 0 -1 | 0 0 0 4    step: 0.5    (-1 = half step below the root)
```

### Passing tones
Connect chord tones with scale steps.

```text
degrees: 0 1 2 4 3 2 1 0    step: 0.25    (walk up to the 5th and back)
```

## Rhythmic patterns by genre

### Four-on-the-floor (house)
Not just steady quarters — add ghost notes and velocity variation.

```text
degrees: 0   0   -   0   0   -   0   0
amp:     .6  .3  0   .5  .3  0   .6  .2
step: 0.25    octave: 3    mode: dorian
```

### Syncopated (R&B, hip-hop)
Off-beat emphasis, rests on the downbeat.

```text
degrees: -   0   -   4   0   -   2   -
amp:     0   .5  0   .6  .4  0   .5  0
step: 0.25
```

### Broken (DnB, garage)
Unpredictable hits with mixed durations.

```text
degrees: 0     -    0     4     -    2     -     0
step:    .25   .5   .25   .25   .5   .25   .75   .25
```

### Driving (techno)
Steady 16ths; the filter movement is the expression (acid-style voice).

```text
degrees:  0    0    0    0     3     3     0    0
brightness: 400  600  800  1200  2000  1200  800  600   (cutoff, Hz)
step: 0.25    octave: 3    mode: phrygian
```

## Interaction with the kick

- **Kick is steady →** the bass syncopates. The kick anchors; the bass dances around it.
- **Kick is syncopated →** the bass locks to the root on downbeats. One part must be the anchor.
- **Sidechain ducking** creates pumping space when both parts are active. See
  `../production-aware/energy-and-dynamics.md` ("Sidechaining").

## Register

Stay in octaves 2–3. A bass above C4 (MIDI 60) is a mid-range part, not a
bass. For more bass energy, stay low and use filter movement for expression
rather than climbing in pitch.

## Filter as expression

Vary brightness per note for movement instead of only changing pitch:

```text
cutoff:    300  500  800  1500  800  500  300  300
resonance: .3   .3   .2   .1    .2   .3   .3   .4
```

This keeps the line rooted but gives it timbral motion — darker on weak
beats, brighter on accents.
