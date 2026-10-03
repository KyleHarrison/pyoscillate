# Lofi Beats

A slow, understated **lofi hip-hop / beats-to-study-and-relax-to** rack at
80 BPM: a small, intimate musical scene rather than a conventional beat. A
warm lead melody carries the listener's attention while a sparse, thumpy
bass, soft strings, a high-register call-and-response voice, soft boom-bap
drums, and a continuous vinyl-dust bed interact around it - **calm,
repetitive, slightly imperfect, and gently hypnotic**, with a clear
foreground/middle-ground/background rather than an equal-weighted "lofi
drums + Rhodes" texture.

## Musical brief

- **Tempo/feel:** 75-82 BPM, centred at 80; 4/4; primarily a 16th-note grid
  with substantial MPC-style swing; behind-the-beat, slightly lazy pocket.
  Ghost notes on hats/snare — see
  `.claude/skills/music-theory/references/rhythm-groove/groove-and-feel.md`
  and `genres/hip-hop-rnb.md` ("Cloud rap / lo-fi hip-hop").
- **Density:** sparse. Empty space is part of the groove; nothing should
  feel aggressively accented or pushed forward.
- **Harmony:** a static, jazz-influenced vamp rather than a developing song
  form — `Dm9–G13–Cmaj7–Am9`, one chord per bar, four-bar loop.
- **Form:** four- and eight-bar phrases that keep breathing, with small,
  probabilistic per-cycle variation (a missing hit, a slightly different
  note, one extra offbeat) rather than frequent fills or dramatic change —
  see `.claude/skills/music-theory/references/melody/phrase-structure.md`
  and `motivic-development.md`. The listener should always recognise it as
  the same musical idea.
- **Arrangement hierarchy:** lead melody (foreground) > bass and strings
  (musical body) > high-register response (intermittent conversational
  detail) > atmosphere (should almost disappear into the background).

## Concept-to-patch mapping

| Concept | Patch | Reuse / extend / new |
|---|---|---|
| Lead melody — warm, hummable, rest-heavy pentatonic motif ("muted pluck") | `tonal/lead`, new style `LeadMutedKeys` | **Extend.** `Lead` already plays a monophonic motif that follows the rack's chord and rests between phrases (the shared `Melody` catalog's `LEAD_ARCH`); its motif is now chosen from the lead's Pattern dropdown, so a style can phrase differently, not just sound different. `LeadMutedKeys` is a near-unison, no-PWM, dark-filtered, undriven dual-pulse voice (a soft, covered pluck) playing a sparse, rest-heavy minor-pentatonic phrase — see `Melody.MUTED_KEYS`. |
| Lead melody, alternate voice — dusty electric-piano comping | `tonal/keys` (`Keys`) | **Reuse, extended.** Offered as a second voice in the same rack group as an alternative to the strict monophonic line: close-voiced chord comping in a Charleston rhythm still reads as a hummable top line, and the existing FM electric-piano character (see `tonal/keys/AGENTS.md`) already matches "warm electric piano". `Keys`'s hand-written `CHORDS` originally played its own independent vi9-ii9-IVmaj9-iii7 cycle (Am9-Dm9-Fmaj9-Em7), which shares this rack's key but not its actual chord-by-chord identity — every bar it clashed against the bass/strings' `Dm9-G13-Cmaj9-Am9` vamp. `CHORDS` was rewritten to the same rootless-voicing style but matching the rack's progression bar-for-bar. |
| Strings / harmonic accompaniment — soft, sustained, occasional colour tones | `tonal/strings`, new `Strings` (first patch in this family) | **New.** `tonal/strings` was a placeholder; `strings.py` is a `SuperSaw`-ensemble pad that re-opens once per bar on the rack's chord (root/fifth/octave, always consonant) with a separate, blendable major-9th colour voice, low-pass, and `Chorus` for ensemble shimmer — no struck attack. See `tonal/strings/AGENTS.md` (now filled in from placeholder). |
| Bass — sparse, thumpy, occasional offbeat re-entry over a four-bar phrase | `tonal/bass`, new profile/style `BassConversation` | **Extend.** A `Melody` leaves a step out to rest, so a bass voice can actually leave space instead of retriggering every step. `Melody.BASS_CONVERSATION` is a 64-step (four-bar) phrase of mostly rests, matching the brief's bar-by-bar ascii diagram one-for-one, with a longer envelope decay so held notes actually ring into the gaps. The original `BassMuted` stays available in the same rack group. |
| High-register call-and-response — a soft "ting" answering the bass | `pitched_percussion/bell` (`BellFm`) | **Reuse, unmodified — approximated.** The rack has no cross-patch event bus (patches only share `Harmony`/`Clock`, never each other's live triggers — see `patches/AGENTS.md`), so a bell that literally listens for a bass hit and answers it isn't buildable without new rack-level architecture. `BellFm` is tuned instead (`root_freq=A5`, soft `strike`, short `ring`, and one `rate` step slower than its default) to sit high, soft, and sparse on the shared clock, which reads as an intermittent answer without genuinely reacting to the bass. Noted here as a deliberate approximation, not an oversight. |
| Atmosphere — vinyl dust / tape crackle, felt more than heard | `texture/noise` (`NoiseDust`) | **Reuse, unmodified.** Already the rack's continuous background bed; its sparse, randomly-timed click/pop transients over a pink/brown noise floor are exactly "vinyl dust and stylus crackle" rather than steady hiss. |
| Soft boom-bap groove | `drums/kick` (`KickLofi`), `drums/snare` (`SnareLofi`), `drums/hat` (`GrooveLofi`) | **Reuse, unmodified.** Already closed-low-pass, lightly saturated, swung-32nd (MPC-style) patterns with ghost notes, built for this exact 80 BPM lofi pocket. |
| Shared harmony/tempo | `rack.py` | `HARMONY`/`BPM`/`TICKS_PER_BAR`, unchanged from the previous rack. |

## Shared harmony and tempo

`HARMONY` in `rack.py` holds one key and vamp — `Dm9–G13–Cmaj9–Am9`, one
chord per bar, four bars per loop. `BassConversation`, `Strings`, and
`LeadMutedKeys` (via `Lead`'s existing harmony support) all re-root
on `clock.bar_index`'s current chord, so they change together regardless of
their own Rate sliders. `keys.Keys` reads the same `Harmony` and stacks a
rootless ninth on each bar's root (see `keys.py`), so changing the rack's key
or progression - including from the Progression dropdown, whose presets are
`Progression`'s `.roots` - changes what it plays with no hand-syncing.

The `Keys` slot (in `rack.py`, `Evolve(32)`) rotates which voicing set it is
comping (voicing set 1, then back to set 0, ...) via `on_evolve` — the
harmony itself never changes, only which inversion voices it. The patch's own
UI panel (see `flet/base.py`'s `EvolveRow`) exposes its interval as a live
slider with a countdown to the next change, so the rotation speed is
adjustable instead of fixed.

## What this rack does not attempt

- **True bass/high-register conversation.** The brief's "bass speaks → space
  → high register answers" is a cross-patch behaviour (one voice reacting to
  another's live trigger) that the current patch/runtime architecture
  doesn't support — every patch only shares `Clock`/`Harmony`, not each
  other's events. The high-response bell approximates this by being sparse
  and clock-phase-offset instead, per the mapping table above. A literal
  version would need a rack-level event bus, which is future work beyond
  this rack.
- **Per-cycle probabilistic humanization** (velocity drift, an occasional
  missing kick, a slightly different melody note each loop) is not wired up
  as a rack-level mechanism; each patch's own fixed pattern/profile supplies
  the "performed rather than mechanical" feel the brief asks for, but true
  cycle-to-cycle randomization is a natural next step rather than something
  this rack's patches do today.
