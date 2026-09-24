# Hi-hat

## Sonic function

A hi-hat is a short, bright rhythmic articulation. It can be closed and tight,
or open and sustained, but both forms occupy the upper spectrum and help define
the subdivision of the groove.

## Minimal architecture

trigger
→ complex metallic/noisy source
→ high-pass filter
→ amplitude envelope
→ output

The source may be several high-frequency oscillators with modulation or a
simple noise generator. The filter removes low energy so the hat stays out of
the kick and bass range.

## Closed and open hats

Closed hats use the shorter decay and leave space for the next subdivision.
Open hats use the longer decay and create a sustained top-end lift. If both are
scheduled in the same voice, a closed hit should choke the open tail rather
than allowing both envelopes to ring indefinitely.

## Envelope and filter

Use a sharp attack and a strongly exponential decay. A high-pass region around
the upper spectrum produces the familiar crisp articulation; lower settings
leave more body, while higher settings sound thinner and airier.

## Design alternatives

Closed electronic hat:
	metallic source + high-pass filter + short exponential decay

Open electronic hat:
	same source and filter + longer exponential decay

## What NOT to assume

There is no universal oscillator count, cutoff, or decay. The open/closed
relationship and the amount of space left for the kick are more important than
any fixed value.
