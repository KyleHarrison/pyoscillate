from __future__ import annotations

from pyo.lib.effects import Freeverb
from pyo.lib.generators import FM, Sine
from pyo.lib.pattern import Pattern
from pyo.lib.tables import CosTable
from pyo.lib.triggers import Trig, TrigEnv

from pysynth.patches.base import Patch
from pysynth.tempo import Tempo

# arpeggio shape: root, minor 3rd, 5th, minor 7th, octave, up and back down
ARP_INTERVALS = [0, 3, 7, 10, 12, 10, 7, 3]

ARP_ROOT = 220  # A3, an octave+ above the bass root


def build(tempo: Tempo, arp_root: float = ARP_ROOT) -> Patch:
    """FM pad voice arpeggiated at 8th notes, with a slow amplitude swell and reverb."""
    arp_trig = Trig()

    # slow swell over 32 steps so the pad breathes in and out across two bars
    arp_swell = Sine(freq=1 / (32 * tempo.eighth), mul=0.01, add=0.5)

    # dur is longer than the step time so envelopes overlap into a sustained pad
    envelope_table = CosTable([(0, 0), (2000, 1), (5000, 0.4), (8191, 0)])
    arp_env = TrigEnv(arp_trig, table=envelope_table, dur=tempo.eighth * 1.2, mul=arp_swell, add=-0.3)

    # slow, detuned ratio for a warm, slightly unstable atmospheric tone
    fm_voice = FM(carrier=arp_root, ratio=0.5012, index=4, mul=arp_env, add=-0.3)
    voice = Freeverb(fm_voice, size=0.85, damp=0.6, bal=0.5)

    step = {"i": 0}

    def next_step() -> None:
        i = step["i"] % len(ARP_INTERVALS)
        fm_voice.carrier = arp_root * pow(2, ARP_INTERVALS[i] / 12)
        arp_trig.play()
        step["i"] += 1

    sequencer = Pattern(next_step, time=tempo.eighth)
    return Patch(sequencer=sequencer, voice=voice)
