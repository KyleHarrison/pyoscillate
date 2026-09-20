# Percussion

## Sonic function

This family is for pitched or resonant rhythmic accents that do not fit the
dedicated kick, snare, clap, hat, cymbal, or bell roles. It is a useful home for
rim clicks, conga-like tones, wood blocks, and other supporting voices.

## Minimal architecture

trigger
→ tonal or transient source
→ short amplitude envelope
→ optional resonant filter
→ output

## Accent roles

Rim-like voices are short and focused, with a woody or click-like center.
Conga-like voices use a longer envelope and a lower resonant tone, giving the
groove a warmer answer to the kick without becoming a bass voice.

## Design rule

Use this family for genuinely miscellaneous accents. A clap belongs in `clap/`
because its repeated noise-burst construction is a distinct synthesis concept;
a snare belongs in `snare/` because its tonal body and filtered-noise tail have
a different balance and control vocabulary.

## What NOT to assume

"Percussion" is not a substitute for a sonic family. When a patch develops a
stable architecture and user-facing controls of its own, give it a dedicated
directory and instruction file.