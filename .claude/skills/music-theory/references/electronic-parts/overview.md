# Electronic Part Writing — Overview

Practical rules for writing the individual parts of a loop-based electronic
track: bass, chords/pads, leads, drums, and chopped breaks. These files are
compact and opinionated on purpose. For the deeper theory behind any rule,
follow the links to the general references (harmony, melody, rhythm-groove).

Load the file for the part being written:

| Part | File |
|---|---|
| Bassline movement, kick interaction, filter as expression | [`bass-lines.md`](bass-lines.md) |
| Chord voicing by register, voice leading, genre harmony | [`chords-and-voicing.md`](chords-and-voicing.md) |
| Motifs, development plans, phrase-length arithmetic | [`melody-and-motifs.md`](melody-and-motifs.md) |
| Drum velocity, swing, ghost notes, genre grooves | [`drums-and-rhythm.md`](drums-and-rhythm.md) |
| Scale/mode choice for electronic genres | [`scales-and-modes.md`](scales-and-modes.md) |
| Slicing and rearranging breakbeats | [`breakbeats.md`](breakbeats.md) |

## Pattern notation used in these files

Patterns are written library-neutrally so they can be implemented in any
sequencer:

- **degrees** — scale degrees, 0-based (0 = root, 2 = 3rd, 4 = 5th). `-` is a rest.
- **notes** — semitone offsets from the root, for chromatic passages.
- **midi** — absolute MIDI note numbers (60 = C4).
- **octave** — register the degrees sound in (3 = the octave starting at C3).
- **step** — the length of each step in beats (0.25 = a 16th note at 4/4).
- **amp** — relative velocity per step, 0–1.

## Universal principles

These apply to every part, every genre.

### 1. Repetition with variation
Repeat a phrase, then change one thing — a note, a rhythm, an octave, a rest.
Listeners need patterns to latch onto and surprises to stay engaged. See
`../melody/motivic-development.md` for the full transformation toolkit.

### 2. Space is musical
Use rests liberally. Don't fill every subdivision. The silence between notes
defines the groove as much as the notes do.

### 3. Register separation
Keep parts in their own range so they don't fight:

| Part | Octave |
|---|---|
| Bass | 2–3 |
| Chords / pads | 3–4 |
| Melody / leads | 4–5 |

See `../production-aware/arrangement-for-mix.md` for the frequency-side view.

### 4. Complementary rhythms
If one part is on the beat, another should syncopate. If the kick is steady,
the bass moves around it. Parts that always hit together collapse into mush.

### 5. Contrast
Dense section → sparse next section. Staccato part → pair it with something
sustained. Contrast creates structure.

### 6. Avoid the axis progression by default
Unless the user asks for it, don't reach for I–V–vi–IV (e.g. C–G–Am–F) or any
rotation of it (vi–IV–I–V, etc.). Prefer modal interchange, chromatic
mediants, suspended chords, or minor progressions with colour. See
`../harmony/modal-harmony.md` and `../harmony/chromatic-harmony.md`.

