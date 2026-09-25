# Melody and Lead Lines — Motif-First Writing

The deeper theory lives in `../melody/motivic-development.md`,
`../melody/melodic-construction.md` and `../melody/phrase-structure.md`. This
file is the compact working method for loop-based electronic leads.

## Rule: build from a motif, never a long flat list

**Never write a melody as a flat sequence longer than 8 steps.** Write a short
motif, then develop it with a plan. That is the difference between a melody
that sounds composed and one that sounds random.

```text
bad:  0 2 4 - 2 4 5 - 3 4 2 0 - - - -       (no structure)
good: motif [0 2 4 -], plan: state, state, transpose +2, invert
```

## Motif — a transformable fragment

A motif is 2–6 notes plus rests. Each transformation produces a new motif:

| Operation | Result for `[0 2 4 -]` |
|---|---|
| transpose +2 | `[2 4 6 -]` |
| transpose −1 | `[-1 1 3 -]` |
| invert (mirror around first note) | `[0 -2 -4 -]` |
| retrograde | `[- 4 2 0]` |
| extend `[3 2]` | `[0 2 4 - 3 2]` |
| truncate to 3 | `[0 2 4]` |

Operations chain: transpose +2 then invert → `[2 0 -2 -]`.

## Phrase — a development plan over one motif

A phrase is a motif plus an ordered plan, looped:

- **state** — play the motif as-is
- **transpose n** — shift by n degrees
- **invert** — mirror around the first note
- **retrograde** — reverse
- **extend [degrees]** — append a tail

Typical plan: *state, state, transpose +2, invert* — state it, repeat so it
registers, vary it, vary it again.

A useful default ("auto-develop"): *state, state, transpose, resolve* (end with
an extension that lands on 0 or 2).

## Common structures

### Call and response
The call ends on tension (degree 3, 4 or 5); the response resolves (to 0 or 2).

```text
call:     [0 2 4 5 - -]
response: [4 3 2 0 - -]
```

## Contour shapes

Every motif has a shape. Choose one deliberately:

| Shape | Example | Character |
|---|---|---|
| Arch (up then down) | `[0 2 4 2 0 -]` | natural, singable |
| Descent | `[5 4 3 2 0 -]` | tension release |
| Wave | `[0 2 4 2 0 -1 0 -]` | hypnotic, good for arps |
| Plateau (repeated note) | `[0 0 0 2 0 -]` | the rhythm is the hook |

## Step vs leap

- **Mostly stepwise** (0→1, 3→2) is smooth — the default.
- **Leaps of 3+ degrees** grab attention. Resolve by step in the opposite direction.
- **Leaps larger than a 5th** are for climaxes. An octave jump is powerful — use it once.

## Phrasing

### Phrase length — check the arithmetic
Motifs are 2–6 notes. A whole phrase should total **1 or 2 bars**; 4 bars is
too long to register as a repeating hook.

```text
motif length × step (beats) × number of plan steps = bars × beats per bar
e.g. 4 × 0.25 × 4 = 4 beats = 1 bar of 4/4  ✓
```

Always verify this before playing; an off-by-one plan drifts against the bar.

### Leave gaps
End motifs with a rest. The silence is anticipation, not emptiness.

## Melody in electronic music

Electronic leads differ from pop/rock toplines. They should:

- **be sparse** — 3–5 notes per motif, plenty of rests
- **loop as a hook** — the phrase cycle *is* the melody
- **leave room** — delay and reverb fill space, not more notes
- **stay in register** — octaves 4–5; don't overlap bass or pads

## Worked example

```text
motif: [0 2 4 -]    mode: dorian, root D, octave 5
plan:  state, state, transpose +2, extend [3 2 -]
step:  0.25    note length: 0.15 beats    amp: 0.4
```

## Rhythmic displacement

Same motif shifted by a 16th — instant variation: prepend a single rest step
(`[- 0 2 4 -]`). See `../rhythm-groove/rhythmic-devices.md` ("Displacement").

