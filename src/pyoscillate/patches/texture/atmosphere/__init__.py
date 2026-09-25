# uv run flet run src/flet/patch/app.py -- pyoscillate.patches.texture.atmosphere
from __future__ import annotations

from typing import Any, ClassVar

from pyo.lib.effects import Freeverb
from pyo.lib.generators import FM, Sine
from pyo.lib.tables import CosTable
from pyo.lib.triggers import Trig, TrigEnv

from pyoscillate.clock import Clock
from pyoscillate.patches.base import Patch
from pyoscillate.patches.params import SliderSpec
from pyoscillate.patches.utility.notes import notes
from pyoscillate.tempo import Tempo

# arpeggio shape: root, minor 3rd, 5th, minor 7th, octave, up and back down
ARP_INTERVALS = [0, 3, 7, 10, 12, 10, 7, 3]

ARP_ROOT = notes.Gs3  # current default

PARAMETERS = (
    SliderSpec(
        "arp_root",
        110,
        440,
        1,
        ARP_ROOT,
        "Register",
        "Shifts the arpeggio up or down in pitch; higher settles brighter and clear of the bass, lower pulls it toward a darker, more muddied register.",
    ),
    SliderSpec(
        "step_division",
        1,
        16,
        1,
        8,
        "Speed",
        "Sets how quickly the arpeggio steps; lower values race by breathlessly, higher values stretch it into a slower, more spacious pattern.",
    ),
    SliderSpec(
        "fm_ratio",
        0.1,
        4,
        0.1,
        0.4,
        "Tone character",
        "Detunes the pad's overtones; near a simple ratio sounds clean and bell-like, drifting away adds a warm, unstable, slightly dissonant shimmer.",
    ),
    SliderSpec(
        "fm_index",
        0,
        10,
        0.1,
        3,
        "Brightness",
        "Moves the pad from a plain, mellow tone to a brighter, buzzier, more harmonically complex one.",
    ),
    SliderSpec(
        "reverb_size",
        0,
        1,
        0.05,
        0.25,
        "Space",
        "Sets how large and distant the pad's room feels, from a tight close ambience to a huge, cavernous decay.",
    ),
    SliderSpec(
        "reverb_damp",
        0,
        1,
        0.05,
        0.15,
        "Tail darkness",
        "Darkens the reverb tail as it decays; higher settings sound warmer and more muffled, lower settings stay bright and shimmering.",
    ),
    SliderSpec(
        "reverb_bal",
        0,
        1,
        0.05,
        0.1,
        "Distance",
        "Blends how much of the pad is heard through the reverb versus dry; higher dissolves it into an atmospheric wash, lower keeps it present and up front.",
    ),
)


VOLUME_DEFAULT = 0.6


class Atmosphere(Patch):
    """FM pad voice arpeggiated on the clock, with a slow amplitude swell and reverb.

    `step_division` is a `rebuild_parameters` entry: the swell period and
    envelope `dur` are derived from it at build time, and the sequencer is
    subscribed at that raw tick count, so changing it live can't just
    update an existing control - the graph has to be rebuilt. `fm_index` is
    fixed (unlike the drone's LFO-modulated index), setting a constant
    brightness for the whole pad.
    """

    title = "Atmosphere (FM pad + arpeggiator)"
    summary = "Breathing melodic pad that arpeggiates and swells overhead."
    parameters = PARAMETERS
    volume_default = VOLUME_DEFAULT
    rebuild_parameters: ClassVar[tuple[str, ...]] = ("step_division",)
    needs_tempo: ClassVar[bool] = True
    needs_clock: ClassVar[bool] = True

    arp_root: float
    step_division: int
    fm_ratio: float
    fm_index: float
    reverb_size: float
    reverb_damp: float
    reverb_bal: float

    def build(self, tempo: Tempo, clock: Clock, **values: Any) -> Patch:
        self.configure(**values)
        arp_trig = Trig()
        step_time = tempo.sixteenth * self.step_division

        # slow swell over 32 steps so the pad breathes in and out across two bars
        arp_swell = Sine(freq=1 / (32 * step_time), mul=0.01, add=0.5)

        # dur is longer than the step time so envelopes overlap into a sustained pad
        envelope_table = CosTable([(0, 0), (2000, 1), (5000, 0.4), (8191, 0)])
        arp_env = TrigEnv(
            arp_trig, table=envelope_table, dur=step_time * 1.2, mul=arp_swell, add=-0.3
        )

        # slow, detuned ratio for a warm, slightly unstable atmospheric tone
        fm_voice = FM(
            carrier=self.arp_root, ratio=self.fm_ratio, index=self.fm_index, mul=arp_env, add=-0.3
        )
        voice = Freeverb(
            fm_voice, size=self.reverb_size, damp=self.reverb_damp, bal=self.reverb_bal
        )

        arp_root = self.arp_root
        step = {"i": 0}

        def next_step() -> None:
            i = step["i"] % len(ARP_INTERVALS)
            fm_voice.carrier = arp_root * pow(2, ARP_INTERVALS[i] / 12)
            arp_trig.play()
            step["i"] += 1

        self.sequencer = clock.subscribe(self.step_division, next_step)
        self.voice = voice
        self.controls = {
            "arp_root": lambda value: setattr(fm_voice, "carrier", value),
            "fm_ratio": lambda value: setattr(fm_voice, "ratio", value),
            "fm_index": lambda value: setattr(fm_voice, "index", value),
            "reverb_size": lambda value: setattr(voice, "size", value),
            "reverb_damp": lambda value: setattr(voice, "damp", value),
            "reverb_bal": lambda value: setattr(voice, "bal", value),
        }
        self.resources = [arp_trig, arp_swell, envelope_table, arp_env, fm_voice]
        return self
