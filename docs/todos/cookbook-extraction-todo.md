Extraction only — no patches have been created yet. Each entry below is a subtractive-synth
recipe (2 oscillators, LFO, low-pass filter, amplifier) as printed in the book. `Osc 2 Track`/`Osc 2 Sync`
are oscillator-sync/keyboard-tracking flags; `Voices` refers to unison voice count; ADSR times are
seconds unless noted `max` (full range) or `-` (not used/no envelope).

Where a filter row lists two values (24db / 12db), both slopes are given as book alternates —
pick one filter type per implementation, not both.

## STRINGS (p.53–61)

- **Banjo** — Osc1: PW20%, 0db(100%). Osc2: PW10%, +5 semi, -7.6db(80%), track on, sync on. LFO: amp, triangle, 10hz(fast), depth 10%. Filter 24db: 2.9khz(72%) res 0% env75% A0 D0.19 S0 R0.19. Amp A0 D0.67 S0 R0.67.
- **Cello** — Osc1: PW10%, 0db(100%). Osc2: square, -7.6db(80%), track on, sync off. LFO: amp, sine, 7.5hz(moderate), depth5%. Filter 24db: 40hz(10%) res0% env90% A0 D3.29 S78% Rmax. Amp A0.06 Dmax S100% R0.30. Alternate: Osc1 sawtooth.
- **Double Bass** — Osc1: PW45%, -1oct, 0db(100%). Osc2: square, -17db(60%), track on, sync off. LFO: pitch, triangle, 5hz(moderate), depth 11cents(light). Filter 24db: 1.6khz(63%) res0% env0%, no ADSR. Amp A0.35 Dmax S100% R0.19.
- **Dulcimer** — Osc1: PW25%, -7.6db(80%). Osc2: PW5%, -7semi, 0db(100%), track on, sync off. LFO: amp, triangle, 1.5hz(very slow), depth22%. Filter 24db: 600hz(49%) res0% env50% A0 D1.69 S0 R1.78. Amp A0 D4.00 S0 R4.00.
- **Guitar Acoustic** — Osc1: PW25%, 0db(100%). Osc2: PW10%, +10semi, -4db(90%), track on, sync on. Filter 24db: 3.1khz(73%) res0% env70% A0 D0.35 S0 R0.29. Amp A0 D1.70 S0 R1.70. No LFO.
- **Guitar Electric** — Osc1: PW20%, -13.4db(65%). Osc2: PW15%, +10semi, 0db(100%), track on, sync on. Filter 24db: 20khz(100%) res0% env0%, no ADSR. Amp A0 D1.70 S0 R1.70. No LFO.
- **Harp** — Osc1: any waveform, -40db(0%). Osc2: square, +6semi, 0db(100%), track on, sync on. LFO: amp, triangle, 7.5hz(moderate), depth6%. Filter 24db: 40hz(10%) res5% env60% A0 D0.37 S78% R0.94. Amp A0 D1.30 S0 R3.30. Alternate: Osc1 sawtooth 0db(100%), Osc2 triangle tuned to osc1 pitch, sync off.
- **Hurdy Gurdy** — Osc1: PW15%, -4.1db(90%). Osc2: square, D3, 0db(100%), track off, sync off. Glide on, time0.04s(very short). Filter 24db: 40hz(10%) res0% env100% A0.04 Dmax S100% R0.23. Amp A0 Dmax S100% R0.85. Voices mono.
- **Kora** — Osc1: triangle, 0db(100%). Osc2: triangle, +1oct, 0db(100%), track on, sync off. LFO: pitch, triangle, 8hz(fast), depth8cents(light). Filter 24db: 20khz(100%) res0% env0%, no ADSR. Amp A0 D2.33 S0 R2.33.
- **Lute** — Osc1: sawtooth, +1oct, 0db(100%). Osc2: triangle, -7db(85%), track on, sync off. LFO: pitch, triangle, 5hz(moderate), depth47cents(medium) — "warbling" vibrato. Filter 24db: 20khz(100%) res0% env0%, no ADSR. Amp A0 D0.66 S0 R0.66.
- **Mandocello** — Osc1: PW25%, 0db(100%). Osc2: PW15%, +4cents, 0db(100%), track on, sync off. LFO: amp, triangle, 3hz(slow), depth20%. Filter 24db: 12khz(92%) res30% env35% A0 D1.78 S0 R0. Amp A0 D1.50 S0 R1.50.
- **Mandolin** — Osc1: PW25%, 0db(100%). Osc2: PW15%, +1oct, -9.6db(75%), track on, sync off. LFO: amp, triangle, 2hz(slow), depth9%. Filter 24db: 40hz(10%) res0% env100% A0 D2.07 S0 R2.13. Amp A0 D0.09 S20% R2.33.
- **Riti** — Osc1: square, 0db(100%). Osc2: PW40%, 0db(100%), track on, sync off. LFO: pitch, triangle, 6hz(moderate), depth10cents(shallow); glide on time0.02s. Filter 24db: 7.9khz(86%) res100% env85% A0 D1.19 S0 R0. Amp A0 D0.09 S0 R0.
- **Sitar** — Osc1: PW10%, 0db(100%). Osc2: PW35%, C3, 0db(100%), track off, sync off. LFO: pitch, triangle, 6.5hz(moderate), depth40cents(medium). Filter 24db: 20khz(100%) res0% env0%, no ADSR. Amp A0 D0.93 S0 R0.93.
- **Standup Bass** — Osc1: PW25%, -1oct, 0db(100%). Osc2: triangle, -1oct, 0db(100%), track on, sync off. LFO: amp, triangle, 15hz(fast), depth10%. Filter 24db: 40hz(10%) res0% env75% A0 D2.33 S60% R2.33. Amp A0 D1.28 S0 R1.38.
- **Viola** — Osc1: sawtooth, -11.6db(70%). Osc2: PW25%, +7semi, 0db(100%), track on, sync on. LFO: routing pitch-osc2, triangle, 4hz(moderate), depth80cents. Filter 24db: 4.9khz(80%) res0% env0%, no ADSR. Amp A0.81 Dmax S100% R0.73. Alternate: Osc2 triangle tuned to osc1 sync off; LFO amp 5hz(moderate) depth8%; filter 20khz(100%).
- **Violin** — Osc1: any waveform, -40db(0%). Osc2: sawtooth, +6semi, 0db(100%), track on, sync on. LFO: routing pitch-osc2, triangle, 5hz(moderate), depth88cents. Filter 24db: 3.2khz(73%) res0% env0%, no ADSR. Amp A0.03 Dmax S100% R0.35. Alternate: Osc1 PW25% 0db(100%), Osc2 square tuned to osc1 sync off, LFO amp 3.5hz(slow) depth10%, filter 9.8khz(90%). Note: osc2 is the only sound source but must sync to osc1.

## WOODWINDS (p.63–68)

- **Bagpipes** — Osc1: sawtooth, 0db(100%). Osc2: square, C3, -11db(75%), track off, sync off. Glide on time0.04s. Filter 24db: 20khz(100%) res0% env0%, no ADSR. Amp A0.02 Dmax S100% R0.85.
- **Bass Clarinet** — Osc1: square, 0db(100%). Osc2: PW5%, 0db(100%), track on, sync off. LFO: pitch, triangle, 7.5hz(moderate), depth5cents(very light). Filter 24db: 40hz(10%) res0% env65% A0.09 Dmax S100% R0.23. Amp A0 Dmax S100% R0.23. Alternate: Osc1 -3.6db(85%), Osc2 sawtooth -1oct -14db(60%), filter env75%.
- **Bassoon** — Osc1: PW10%, 0db(100%). Osc2: square, +1oct, 0db(100%), track on, sync off. LFO: amp, triangle, 7.5hz(moderate), depth5%. Filter 24db: 40hz(10%) res0% env60% A0.16 D1.13 S83% R0.28. Amp A0 Dmax S100% Rmax. Alternate: Osc1 square, filter env75%.
- **Clarinet** — Osc1: PW45%, 0db(100%). Osc2: none. LFO: pitch, sine, 7.5hz(moderate), depth1cent(very light). Filter 24db: 40hz(10%) res0% env55% A0.15 Dmax S100% Rmax. Amp A0 Dmax S100% R0.32. Alternate: Osc1 square, Osc2 sawtooth -9.6db(70%), filter env100%.
- **Conch Shell** — Osc1: triangle, 0db(100%). Osc2: sawtooth, -14.1db(65%), track on, sync off. LFO: amp, triangle, 2hz(slow), depth5%; glide on time0.012s(fast). Voices mono. Filter 24db: 1khz(56%) res0% env55% A0.11 D0.07 S80% R0.13. Amp A0.11 Dmax S100% R0.13.
- **Contrabassoon** — Osc1: PW10%, -1oct, 0db(100%). Osc2: triangle, +1oct, 0db(100%), track on, sync off. LFO: amp, triangle, 7.5hz(moderate), depth5%. Filter 24db: 40hz(10%) res0% env60% A0.09 D1.13 S83% R0.28. Amp A0 Dmax S100% R0.29. Alternate: Osc1 square, Osc2 square, filter env75%.
- **Didgeridoo** — Osc1: square, -1oct, 0db(100%). Osc2: PW25%, +9semi, 0db(100%), track on, sync on. LFO: filter-cutoff, triangle, 1hz(slow), depth10%(shallow); glide on time moderate. Voices mono. Filter 24db: 1.5khz(62%) res80% env0%, no ADSR. Amp A0.03 Dmax S100% R0.50. Note: play in lower octaves; try unison 2-3 voices.
- **English Horn (Cor Anglais)** — Osc1: PW15%, 0db(100%). Osc2: triangle, +1oct, -28.6db(30%), track on, sync off. LFO: pitch, triangle, 7.5hz(moderate), depth3cents(shallow). Filter 24db: 40hz(10%) res0% env60% A0.07 Dmax S100% Rmax. Amp A0 Dmax S100% R0.37. Alternate: Osc1 triangle, Osc2 +2oct, filter env95%.
- **Flute** — Osc1: PW25%, 0db(100%). Osc2: none; glide on time0.015s. Filter 24db: 40hz(10%) res0% env60% A0.11 Dmax S100% R0.28. Amp A0.11 Dmax S100% R0.28. Alternate: Osc1 sawtooth.
- **Oboe** — Osc1: PW20%, 0db(100%). Osc2: PW5%, 0db(100%), track on, sync off. LFO: pitch, sine, 7.5hz(moderate), depth1cent(very light). Filter 24db: 40hz(10%) res25% env60% A0.15 Dmax S100% Rmax. Amp A0 Dmax S100% R0.14. Alternate: Osc1 sawtooth -3.6db(85%), Osc2 triangle +2oct -24.9db(40%), filter res20% env80%.
- **Piccolo** — Osc1: sawtooth, -9db(80%). Osc2: triangle, +1oct, 0db(100%), track on, sync off. LFO: amp, triangle, 5hz(moderate), depth5%; glide on time0.01s. Filter 24db: 40hz(10%) res50% env60% A0.11 Dmax S100% R0.28. Amp A0.11 Dmax S100% R0.28. Alternate: Osc1 square +1oct -25db(40%), Osc2 +1oct -18db(55%), filter env100%.

## BRASS (p.69–72)

- **French Horn** — Osc1: PW10%, 0db(100%). Osc2: none. Filter 24db: 40hz(10%) res20% env45% A0.05 D5.76 S94% R0.39. Amp A0 D3.9 S96% R0.93. Alternate: Osc1 sawtooth, Osc2 triangle +2oct, filter env55%.
- **Harmonica** — Osc1: PW2%, -11db(75%). Osc2: PW15%, +8semi+7cents, 0db(100%), track on, sync on. LFO: PW-osc1, triangle, 1.6hz(slow), depth85%(deep). Filter 24db: 1.9khz(66%) res0% env65% A0.16 Dmax S100% R0.16. Amp A0.13 D0.33 S50% R0.14.
- **Penny Whistle** — Osc1: square, 0db(100%). Osc2: triangle, +2oct, -7db(85%), track on, sync off. LFO: amp, triangle, 90hz(extreme), depth5%(shallow); glide on time0.04s. Filter 24db: 1.1khz(58%) res80% env77% A0.11 Dmax S100% Rmax. Amp A0.11 Dmax S100% R0.57.
- **Saxophone** — Osc1: PW30%, 0db(100%). Osc2: PW45%, +8semi, -9.6db(75%), track on, sync on. LFO: pitch-osc1&osc2, sine, 7.5hz(moderate), depth10cents(shallow). Filter 24db: 40hz(10%) res0% env90% A0.14 D0.37 S78% Rmax. Amp A0 Dmax S100% R0.30. Alternate: Osc1 sawtooth -3.6db(85%), Osc2 sawtooth +1oct sync off, LFO amp depth6%.
- **Trombone** — Osc1: sawtooth, 0db(100%). Osc2: triangle, +1oct, 0db(100%), track on, sync off. LFO: amp, triangle, 5hz(moderate), depth5%. Filter 24db: 900hz(55%) res0% env30% A0.11 Dmax S100% R0.18. Amp A0.06 Dmax S100% R0.50.
- **Trumpet** — Osc1: sawtooth, 0db(100%). Osc2: sawtooth, +1oct, -14.4db(65%), track on, sync off. LFO: amp, triangle, 7.5hz(moderate), depth5%. Filter 24db: 50hz(13%) res15% env75% A0.08 Dmax S100% R0.19. Amp A0 Dmax S100% R0.19.
- **Tuba** — Osc1: sawtooth, -6db(85%). Osc2: sawtooth, -1oct, 0db(100%), track on, sync off. LFO: amp, triangle, 2.4hz(slow), depth5%. Filter 24db: 40hz(10%) env60% A0.7 Dmax S100% R0.11. Amp A0.03 Dmax S100% R0.11.

## KEYBOARDS (p.73–76)

- **Accordion** — Osc1: PW10%, 0db(100%). Osc2: PW10%, +15cents, 0db(100%), track on, sync off. LFO: amp, triangle, 13hz(fast), depth5%. Filter 24db: 8.2khz(87%) res0% env0%, no ADSR. Amp A0.18 Dmax S100% R0.18.
- **Celeste** — Osc1: triangle, 0db(100%). Osc2: none. No LFO. Voices all. Filter 24db: 1.2khz(59%) res0% env100% A0 D0.07 S45% R2.10. Amp A0 D2.10 S0 R2.10. Note: if using square wave for osc1, halve filter frequency.
- **Clavichord** — Osc1: sawtooth, 0db(100%). Osc2: sawtooth, +1oct+4semi, 0db(100%), track on, sync on. LFO: pitch, triangle, 1hz(very slow), depth15cents(shallow vibrato). Filter 24db: 1.8khz(65%) res0% env70% A0 D0.10 S65% Rmax. Amp A0 D1.9 S0 R0.35.
- **Electric Piano** — Osc1: sawtooth, 0db(100%). Osc2: PW5%, +2oct+9semi, 0db(100%), track on, sync on. No LFO. Filter 24db: 630hz(50%) res0% env50% A0 D0.33 S50% Rmax. Amp A0 D5.14 S0 R0.66.
- **Harpsichord** — Osc1: PW25%, -3db(95%). Osc2: PW5%, +9semi, 0db(100%), track on, sync on. No LFO. Filter 24db: 2.4khz(69%) res0% env100% A0 D0.23 S65% Rmax. Amp A0 D2 S0 R0.35.
- **Organ** — Osc1: triangle, 0db(100%). Osc2: triangle, -2oct, 0db(100%), track on, sync off. No LFO. Filter 24db: 20khz(100%) res0% env0%, no ADSR. Amp A0.6 Dmax S100% R0.40.
- **Piano** — Osc1: sawtooth, -10.4db(75%). Osc2: PW15%, +1oct+2semi, 0db(100%), track on, sync on. No LFO. Filter 24db: 40hz(10%) res0% env75% A0 D5.22 S0 Rmax. Amp A0 D0.67 S25% R0.50. Alternate: Osc1 0db(100%), Osc2 sawtooth +1oct 0db(100%) sync off.

## VOCALS (p.77–79)

- **Angels** — Osc1: sawtooth, 0db(100%). Osc2: none. LFO: pitch, triangle, 2.4hz(slow), depth20cents(shallow). Filter 24db: 900hz(55%) res70% env0%, no ADSR. Amp A0.32 Dmax S100% R0.93. Note: C4-C6, 24db filter works best.
- **Choir** — Osc1: PW15%, -2oct, 0db(100%). Osc2: PW25%, 0db(100%), track on, sync off. LFO: pitch, triangle, 2.4hz(slow), depth20cents(shallow). Filter 24db: 1.7khz(64%) res0% env0%, no ADSR. Amp A0.32 Dmax S100% R0.93.
- **Vocal Female** — Osc1: PW5%, 0db(100%). Osc2: PW25%, -13.9db(65%), track on, sync off. LFO: pitch, triangle, 2.4hz(slow), depth20cents(shallow). Filter 24db: 1.2khz(59%) res50% env0%, no ADSR. Amp A0.32 Dmax S100% R0.93. Notes: C4-C6; 24db filter is best.
- **Vocal Male** — Osc1: PW15%, -1oct, 0db(100%). Osc2: PW25%, -4.3db(90%), track on, sync off. LFO: pitch, triangle, 2.4hz(slow), depth20cents(shallow). Filter 24db: 2.0khz(67%) res0% env0%, no ADSR. Amp A0.32 Dmax S100% R0.93. Alternate: Osc1 sawtooth 0db(100%), Osc2 sawtooth 0db(100%), filter 24db900hz(55%)/12db600hz(49%) res70%. Note: 12db filter works best.
- **Whistling** — Osc1: triangle, +2oct, 0db(100%). Osc2: none. Voices 2. LFO: pitch, triangle, 7hz(moderate), depth12cents(shallow). Filter 24db: 500hz(46%) res0% env40% A0.04 Dmax S100% Rmax. Amp A0.03 Dmax S100% R0.35. Notes: lower cutoff for lower pitches; if using square wave for osc1, lower filter to 24db 0.3khz / 12db 0.1khz.

## TUNED PERCUSSION (p.81–84)

- **Bell** — Osc1: triangle, 0db(100%). Osc2: square, +5semi, -14db(65%), track on, sync off. LFO: amp, triangle, 7.5hz(moderate), depth5%. Filter 24db: 20khz(100%) res0% env0%, no ADSR. Amp A0 D1.30 S0 R3.30.
- **Bongos** — Osc1: triangle, 0db(100%). Osc2: square, -13.9db(65%), track on, sync off. Voices 2. No LFO. Filter 24db: 600hz(49%) res0% env60% A0 D0.11 S0 R0.11. Amp A0 D0.22 S0 R0.22. Notes: G2-G4.
- **Conga** — Osc1: square, 0db(100%). Osc2: square, +1oct+2semi, -6.5db(85%), track on, sync off. Voices mono. No LFO. Filter 24db: 300hz(39%) res40% env50% A0 D0.02 S80% Rmax. Amp A0 D0.15 S0 R0.15.
- **Glockenspiel** — Osc1: triangle, 0db(100%). Osc2: triangle, +2oct+6semi, 0db(100%), track on, sync off. Voices all. No LFO. Filter 24db: 3.8khz(76%) res- env75% A0 D0.10 S25% R0.10. Amp A0 D1.20 S0 R1.20. Note: play above G5.
- **Marimba** — Osc1: triangle, 0db(100%). Osc2: triangle, +2oct, -9.6db(75%), track on, sync off. LFO: amp, triangle, 8hz(fast), depth11%. Filter 24db: 2.9khz(72%) res0% env0%, no ADSR. Amp A0 D1.66 S20% R1.66.
- **Timpani** — Osc1: square, -1oct, 0db(100%). Osc2: square, -1oct-10semi, -15.3db(60%), track on, sync off. No LFO. Filter 24db: 800hz(53%) res45% env35% A0 D0.35 S0 R0.38. Amp A0 D2.89 S0 R1.90.
- **Xylophone** — Osc1: triangle, +1oct+10semi, 0db(100%). Osc2: triangle, 0db(100%), track on, sync off. LFO: amp, triangle, 7.5hz(moderate), depth5%. Filter 24db: 300hz(39%) res- env60% A0 D0.53 S45% R0.50. Amp A0 D1.88 S0 R1.78.

## UNTUNED PERCUSSION (p.85–90)

- **Bass Drum** — Osc1: triangle, -2oct, 0db(100%). Osc2: triangle, -2oct, 0db(100%), track on, sync off. No LFO/noise. Filter 24db: 20khz(100%) res0% env0%, no ADSR. Amp A0 D0.12 S0 R0.12.
- **Castanets** — No oscillators; noise on, 0db(100%). Voices 1. No LFO. Filter 24db: 7.6khz(86%) res100%, no ADSR. Amp A0 D0.04 S0 R0.04.
- **Clap** — No oscillators; noise on, 0db(100%). LFO: amp, square, 32hz(very fast), depth45%. Filter 24db: 1.6khz(63%) res30% env50% A0 D0.15 S0 R0.15. Amp A0 D0.11 S0 R0.11. Notes: 12db filter works best; set LFO to retrigger, else each hit has different amplitude.
- **Claves** — No oscillators; noise on, 0db(100%). Voices mono. No LFO. Filter 24db: 2.1khz(67%) res100% env0%, no ADSR. Amp A0 D0.14 S0 R0.14. Notes: change filter cutoff to alter pitch; 12db filter allows full resonance without losing highs.
- **Cowbell** — Osc1: square, 0db(100%). Osc2: PW35%, +1oct+2semi, 0db(100%), track on, sync off. Voices mono. No LFO. Filter 24db: 8.8khz(88%) res55% env65% A0 D0.02 S65% Rmax. Amp A0 D0.15 S0 R0.15. Note: play around 5th octave.
- **Cowbell (analog drum machine)** — Osc1: PW10%, 0db(100%). Osc2: PW35%, +5semi, 0db(100%), track on, sync off. Voices mono. No LFO. Filter 24db: 8.1khz(87%) res0% env65% A0 D0.02 S65% Rmax. Amp A0 D0.15 S0 R0.15. Note: play around 5th octave.
- **Cymbal** — No oscillators; noise on, 0db(100%). Voices mono. No LFO. Filter 24db: 9.4khz(89%) res50% env70% A0 D0.14 S0 R1.80. Amp A0 D1.10 S0 R1.00. Note: use EQ/high-pass to remove low end + distortion; hardest patch in the book (~4hrs), still least realistic; included for completeness.
- **Side Stick** — No oscillators; noise on, 0db(100%). Voices mono. No LFO. Filter 24db: 2.7khz(71%) res100% env85% A0 D1.19 S0 R0. Amp A0 D0.09 S0 R0.
- **Snare Drum** — Osc1: triangle, -1oct, 0db(100%). Osc2: none; noise mix -31.4db(20%). Voices multi. No LFO. Filter 24db: 20khz(100%) res-, no ADSR. Amp A0 D0.27 S0 R0.27.
- **Tambourine** — No oscillators; noise on, 0db(100%). Voices mono. No LFO. Filter 24db: 5.3khz(81%) res100% env0%, no ADSR. Amp A0 D0.34 S0 R0.34. Note: turn off keyboard tracking if available.
- **Wheels of Steel** — No oscillators; noise on, 0db(100%). Voices mono. No LFO. Filter 24db: 40hz(10%) res40% env100% A0.02 D0.09 S0 R0.09. Amp A0 D1.65 S0 R0.05.

## LEADS (p.91–94)

- **Brass Section** — Osc1: square, -10cents, 0db(100%). Osc2: PW20%, +1oct+10cents, 0db(100%), track on, sync off. LFO: PW-osc1&osc2, triangle/sine, 5.5hz, depth45%. Filter 24db: 40hz(10%) res0% env100% A0.03 Dmax S100% R0.60. Amp A0 Dmax S100% R0.35.
- **Mellow 70's Lead** — Osc1: square, -10cents, 0db(100%). Osc2: square, +10cents, 0db(100%), track on, sync off; glide on time0.02s, voices mono. No LFO. Filter 24db: 20khz(100%) res0% env0%, no ADSR. Amp A0 Dmax S100% R0.35.
- **Mono Solo** — Osc1: PW30%, 0db(100%). Osc2: PW20%, +4cents, 0db(100%), track on, sync off. LFO: pitch-osc1&osc2, triangle/sine, 4.5hz(moderate), depth22cents(moderate); glide on time0.04s(very fast). Filter 24db: 40hz(10%) res45% env80%, ADSR partially illegible (image clipped). Amp similarly clipped — re-check book scan.
- **New Age Lead** — Osc1: square, +5cents, 0db(100%). Osc2: square, -5cents, 0db(100%), track on, sync off. LFO: PW-osc1&osc2, triangle/sine, 5.5hz, depth45%. Filter 24db: 1.4khz(61%) res65% env75% A0 D1.20 S20% R0.60. Amp A0.05 Dmax S100% R0.35.
- **R&B Slide** — Osc1: triangle, +1oct, 0db(100%). Osc2: triangle, +3oct, -6db(85%), track on, sync off; glide on time0.02s, voices mono. No LFO. Filter 24db: 1.9khz(66%) res45% env65% A1.20 Dmax S100% R6.30. Amp A0.02 Dmax S100% R0.60. Note: play in higher octaves; try light unison.
- **Screaming Sync** — Osc1: any waveform, -1oct, -40db(0%). Osc2: square, 0db(100%), track on, sync on; glide on time0.02s, unison on, voices mono. LFO: pitch-osc2, triangle/sine, 0.66hz, depth4.5cents(medium). Filter 24db: 20khz(100%) res0% env0%, no ADSR. Amp A0 Dmax S100% R0.60. Note: osc1 on but volume all the way down.
- **Strings Pulse-Width Modulation** — Osc1: square, -10cents, 0db(100%). Osc2: square, +10cents, 0db(100%), track on, sync off. LFO: PW-osc1&osc2, sine, 2hz(slow), depth47%. Filter 24db: 2khz(67%) res0% env100% A0.09 Dmax S100% Rmax. Amp A0.11 Dmax S100% R0.35. Note: use thick chorus and delay.
- **Trance 5th** — Osc1: square, 0db(100%). Osc2: square, +7semi, 0db(100%), track on, sync off; unison on, voices mono. LFO: PW-osc1&osc2, triangle/sine, 6hz(moderate), depth80%. Filter 24db: 20khz(100%) res0% env0%, no ADSR. Amp A0 Dmax S100% R0s.

## BASS (p.95–98)

- **Acid Bass** — Osc1: PW25%, +10cents, -12db(70%). Osc2: square, -2oct-10cents, 0db(100%), track on, sync off; voices mono. No LFO. Filter 24db: 450hz(45%) res60% env0%, no ADSR. Amp A0 D0.45 S15% R0.26. Note: turn filter cutoff knob during play for acid effect.
- **Bass of the Time Lords** — Osc1: PW30%, -2oct, 0db(100%). Osc2: PW30%, -1oct, 0db(100%), track on, sync off; voices mono. No LFO. Filter 24db: 40hz(10%) res0% env85% A0 D0.25 S25% R0.25. Amp A0 D0.65 S0 R0.70.
- **Detroit Bass** — Osc1: square, -1oct, 0db(100%). Osc2: sawtooth, -2oct, 0db(100%), track on, sync off; glide on time0.01s, voices mono. No LFO. Filter 24db: 20khz(100%) res0% env0%, no ADSR. Amp A0 Dmax S100% R0.
- **Deutsche Bass** — Osc1: PW25%, -2oct, 0db(100%). Osc2: sawtooth, -1oct-3semi, 0db(100%), track on, sync on; voices mono. No LFO. Filter 24db: 800hz(53%) res35% env50% A0 D0.15 S0 R0.15. Amp A0 Dmax S100% R0.15.
- **Digital Bass** — Osc1: square, -1oct, -6db(85%). Osc2: sawtooth, -2oct, 0db(100%), track on, sync off; voices mono. No LFO. Filter 24db: 122hz(26%) res0% env100% A0 D0.15 S0 R0. Amp A0 Dmax S100% R1.00.
- **Funk Bass** — Osc1: sawtooth, -2oct, 0db(100%). Osc2: PW30%, -1oct, 0db(100%), track on, sync off; glide on time0.02s, voices mono. No LFO. Filter 24db: 40hz(10%) res50% env85% A0.15 D0.10 S45% R0.08. Amp A0 D0.29 S30% R0.40.
- **Growling Bass** — Osc1: square, -2oct, 0db(100%). Osc2: sawtooth, -9semi, 0db(100%), track on, sync off; voices mono. No LFO. Filter 24db: 122hz(26%) res0% env100% A0 D0.50 S20% R0.60. Amp A0 Dmax S100% R0.60.
- **Rez Bass** — Osc1: square, -2oct, 0db(100%). Osc2: square, -2oct, 0db(100%), track on, sync on; glide off time0.08s, voices mono. LFO: pitch-osc2, triangle/sine, 10hz(fast), depth30cents(shallow). Filter 24db: 6.5khz(84%) res50% env0%, no ADSR. Amp A0 Dmax S100% R0.10.

## PADS (p.99–103)

- **Android Dreams** — Osc1: square, -2oct, 0db(100%). Osc2: sawtooth, -1semi, 0db(100%), track on, sync on; noise on -6db(90%). LFO: *see note (multiple routings) — PW osc1&2 depth45%, filter cutoff depth10%, pitch osc2 depth 3 semitones; triangle/sine, 0.25hz(very slow). Filter 24db: 2.4khz(69%) res30% env0%, no ADSR. Amp A0.45 Dmax S100% R2.25.
- **Celestial Wash** — No oscillators; noise on, 0db(100%). LFO: resonance, square, 5.5hz(moderate), depth100%. Filter 24db: 1khz(57%) res100% env0%, no ADSR. Amp A1.65 D5.85 S0 R4.40. Note: turn filter's keyboard tracking on if available.
- **Dark City** — Osc1: square, -2oct, 0db(100%). Osc2: sawtooth, -11semi-92cents, 0db(100%), track on, sync off. LFO: PW-osc1&osc2, triangle/sine, 4hz(moderate), depth45%. Filter 24db: 300hz(39%) res0% env75% A5.15 D6.35 S50% R5.20. Amp A0 D3.90 S70% R6.35.
- **Aurora** — Osc1: square, +10cents, 0db(100%). Osc2: square, -10cents, 0db(100%), track on, sync off. LFO: PW-osc1&osc2, triangle/sine, 4hz(moderate), depth40%. Filter 24db: 40hz(10%) res65% env50% A1.50 Dmax S100% R0.60. Amp A0.60 Dmax S100% R0.60.
- **Galactic Cathedral** — Osc1: square, -11cents, 0db(100%). Osc2: square, +2oct+11cents, -6db(85%), track on, sync off. LFO: filter cutoff, triangle/sine, 0.3hz(very slow), depth10%. Filter 24db: 1.2khz(59%) res60% env0%, no ADSR. Amp A0.40 Dmax S100% R2.25.
- **Galactic Chapel** — Osc1: triangle, 0db(100%). Osc2: triangle, +1oct, -6db(85%), track on, sync off. LFO: cutoff+amp, triangle/sine, 0.3hz(very slow), depth cutoff10% amp17%. Filter 24db: 1.4khz(61%) res65% env0%, no ADSR. Amp A0.35 Dmax S100% R2.25.
- **Portus** — Osc1: triangle, 0db(100%). Osc2: triangle, +1oct, 0db(100%), track on, sync off; glide on time1.5s. No LFO. Filter 24db: 75hz(19%) res70% env70% A1.80 Dmax S100% R2.90. Amp A1.50 Dmax S100% R3.30.
- **Post-Apocalyptic Sync Sweep** — Osc1: square, -2oct, 0db(100%). Osc2: square, -1oct, -6db(85%), track on, sync on. LFO: pitch-osc2, triangle/sine, 0.7hz(very slow), depth4.5semi(moderate). Filter 24db: 40hz(10%) res65% env50% A2.10 D5.20 S0 R3.00. Amp A0 Dmax S100% R0.60.
- **Terra Enceladus** — Osc1: sawtooth, 0db(100%). Osc2: square, -1oct, -3db(90%), track on, sync off. LFO: PW-osc2, triangle/sine, 1.75hz(slow), depth45%. Filter 24db: 1.3khz(60%) res0% env0%, no ADSR. Amp A0.40 Dmax S100% R2.25.

## SOUND EFFECTS (p.105–110)

- **Cat** — Osc1: PW10%, +1oct+5semi, 0db(100%). Osc2: PW5%, 0db(100%), track on, sync off. LFO: pitch, sine, 1.7hz(slow), depth11cents. Filter 24db: 270hz(37%) res65% env65% A0.57 D1.90 S55% R0.29. Amp A0.51 D1.05 S55% R0.93.
- **Digital Alarm Clock** — Osc1: PW5%, 0db(100%). Osc2: sawtooth, 0db(100%), track on, sync off. LFO: amp, square, 2hz(slow), depth100%. Filter 24db: 9.5khz(89%) res0% env40%, no ADSR. Amp A0 Dmax S100% R0.
- **Journey to the Core** — Osc1: sawtooth, -2oct, 0db(100%). Osc2: square, -1oct, 0db(100%), track on, sync off. LFO: *see note — pitch osc1&osc2 depth 7 semitones, PW-osc2 depth100%; sawtooth, 7.5hz(moderate). Filter 24db: 120hz(26%) res45% env100% A3.30 D3.20 S0 R3.20. Amp A0 Dmax S100% R0.80.
- **Kazoo** — Osc1: PW15%, 0db(100%). Osc2: PW2%, 0db(100%), track on, sync off; voices mono. LFO: pitch, noise/saw, 32hz(very fast), depth70cents(deep). Filter 24db: 1.2khz(59%) res30% env50% A0.06 D1.20 S0 R0.63. Amp A0.03 D3.9 S0 R0.33. Note: use noise for LFO source if available, else sawtooth.
- **Laser** — No oscillators; noise on, 0db(100%). Voices mono. No LFO. Filter 24db: 40hz(10%) res100% env100% A0 D0.38 S0 R0.25. Amp A0 D0.45 S0 R0.30.
- **Motor** — Osc1: PW25%, -2oct, 0db(100%). Osc2: PW25%, -1oct, -14.3db(65%), track on, sync off; glide on time1.3s(long), voices mono. LFO: amp, square, 32hz(very fast), depth40%. Filter 24db: 20khz(100%) res0% env0%, no ADSR. Amp A0 Dmax S100% R0.60. Note: glide on is essential for this patch to sound right.
- **Nerd-O-Tron 2000** — Osc1: sawtooth, 0db(100%). Osc2: square, +2oct, 0db(100%), track on, sync off. LFO: filter cutoff, noise, 0.9hz(very slow), depth25%. Filter 24db: 680hz(51%) res85% env0%, no ADSR. Amp A0 Dmax S100% R2.00.
- **Ocean Waves (with foghorn)** — No oscillators; noise on, 0db(100%). LFO: amp osc1&noise, triangle, 0.2hz(very slow), depth75%. Filter 24db: 4.3khz(78%) res30% env0%, no ADSR. Amp A0.40 Dmax S100% R1.00. Note: for foghorn, set osc1 to sawtooth, -1oct, 0db(100%).
- **[Title obscured — likely "Positronic Rhythm"]** (p.109, scan defect obscures the left column) — Osc1: sawtooth, -2oct, 0db(100%). Osc2: square, -1oct, 0db(100%), track on, sync off. LFO: *see note — pitch osc1&osc2 depth 7 semitones, PW-osc2 depth100%; square, 4hz(moderate). Filter 24db: 165hz(30%) res45% env100% A3.30 D4.00 S0 R2.90. Amp A0 Dmax S100% R0.80. **Needs re-check against original book/higher-quality scan for the correct title.**
- **Space Attack!** — Osc1: square, -1oct, 0db(100%). Osc2: sawtooth, -1oct, 0db(100%), track on, sync off; voices mono. LFO: pitch-osc1&osc2, sawtooth, 2.5hz(moderate), depth1oct(deep). Filter 24db: 20khz(100%) res0% env0%, no ADSR. Amp A0 Dmax S100% R2.00. Note: if a 2nd LFO available, set routing amp-osc1&osc2, sawtooth, 15hz(fast), depth100%.
- **Toad** — Osc1: triangle, +1oct, 0db(100%). Osc2: square, -2oct, 0db(100%), track on, sync off; glide on time1.3s(long). LFO: amp, triangle, 32hz(very fast), depth100%. Filter 24db: 40hz(10%) res0% env0%, no ADSR. Amp A0.09 D0.23 S0 R0.23.
- **Wind** — No oscillators; noise on, 0db(100%). LFO: noise amplitude, noise, 0.7hz(very slow), depth40%. Filter 24db: 780hz(53%) res75% env0%, no ADSR. Amp A0.40 Dmax S100% R2.70.

## Notes / follow-ups

- No patches created yet — this file is extraction-only, per instruction.
- One patch title on printed p.109 is visually clipped in the scan; title guessed as "Positronic Rhythm" from context (electronic/rhythmic SFX section) but should be verified against a cleaner scan before use.
- "Mono Solo" (p.92) ADSR values for filter/amp envelopes were partly obscured by a scan artifact (dark smudge over the R column) — re-verify against the source before implementing.
- Several patches reference book-specific LFO routing combinations (e.g. "PW osc1, osc2" as a single routing, dual-parameter LFOs) that don't map 1:1 onto a single Pyo LFO object — worth discussing during pyo-music/implementation translation.
