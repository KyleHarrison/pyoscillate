# Bell

## Sonic function

A bell is a pitched but spectrally complex percussion voice. Its identity comes
from inharmonic partials, a clear onset, and an exponential decay that lets the
metallic resonance ring out.

## Minimal architecture

trigger
→ FM or detuned oscillator network
→ optional band-pass filter
→ exponential amplitude envelope
→ output

Optional:
→ transient generator
→ sample-rate reduction

## FM bells

FM is useful when the carrier and modulation relationship creates a noisy,
metallic spectrum. The modulation index and frequency ratio should be treated
as interacting controls: increasing index can make the sound brighter, more
metallic, or harsher depending on register and ratio.

## 808-style cowbell

A cowbell can be built from two detuned rectangle oscillators mixed together and
sent through a resonant band-pass filter. Detuning supplies the beating and
rectangular waves provide the dense, nasal spectrum.

## Envelope and filter

Use a sharp attack and a strongly exponential decay. A band-pass filter shapes
the resonance and keeps the result from spreading across the entire spectrum.

## Design alternatives

Realistic bell:
    FM network + band-pass filter + long exponential decay

808-style cowbell:
    two detuned rectangle oscillators + resonant band-pass

## What NOT to assume

Metallic complexity does not come from FM index alone. Carrier frequency, ratio,
filtering, decay, and output level all affect whether the result reads as a
bell, clang, zap, or noisy accent.