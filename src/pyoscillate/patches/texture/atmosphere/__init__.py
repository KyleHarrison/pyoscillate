# uv run flet run src/flet/patch/app.py -- pyoscillate.patches.texture.atmosphere
"""FM pad voice arpeggiated on the clock, with a slow amplitude swell and reverb.

Each arpeggio step is a real event - a trigger opens an envelope through
`GatedVoice`'s trigger/envelope primitives - so despite living in the
ungated `texture/` family, this patch's shape is a gated voice's, not a
continuous one. It subscribes to the clock at a raw tick count
(`step_division`) instead of through `self.schedule()`'s rate machinery:
that count is a `rebuild_parameters` entry, a structural step count rather
than a live rate offset from a base division, so `self._division` is set
directly the way `schedule()` would set it, which is all `finish()` needs
to have happened.
"""

from __future__ import annotations

from typing import ClassVar

from pyo.lib.effects import Freeverb
from pyo.lib.generators import FM, Sine
from pyo.lib.tables import CosTable
from pyo.lib.triggers import TrigEnv

from pyoscillate.clock import Clock
from pyoscillate.patches.base import Patch
from pyoscillate.patches.common import GatedVoice
from pyoscillate.patches.params import Param
from pyoscillate.patches.utility.notes import notes
from pyoscillate.tempo import Tempo

# arpeggio shape: root, minor 3rd, 5th, minor 7th, octave, up and back down
ARP_INTERVALS = [0, 3, 7, 10, 12, 10, 7, 3]

ARP_ROOT = notes.Gs3  # current default
# dur is longer than the step time so envelopes overlap into a sustained pad
ENVELOPE_POINTS = [(0, 0), (2000, 1), (5000, 0.4), (8191, 0)]


class Atmosphere(GatedVoice):
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
    volume_default = 0.6
    rebuild_parameters: ClassVar[tuple[str, ...]] = ("step_division",)

    arp_swell: Sine
    envelope_table: CosTable
    arp_env: TrigEnv
    fm_voice: FM
    reverb: Freeverb

    @Param(
        110,
        440,
        1,
        ARP_ROOT,
        "Register",
        "Shifts the arpeggio up or down in pitch; higher settles brighter and clear of the bass, lower "
        "pulls it toward a darker, more muddied register.",
    )
    def arp_root(self, value: float) -> None:
        self.fm_voice.carrier = value

    step_division = Param(
        1,
        16,
        1,
        8,
        "Speed",
        "Sets how quickly the arpeggio steps; lower values race by breathlessly, higher values stretch "
        "it into a slower, more spacious pattern.",
    )

    @Param(
        0.1,
        4,
        0.1,
        0.4,
        "Tone character",
        "Detunes the pad's overtones; near a simple ratio sounds clean and bell-like, drifting away adds "
        "a warm, unstable, slightly dissonant shimmer.",
    )
    def fm_ratio(self, value: float) -> None:
        self.fm_voice.ratio = value

    @Param(
        0,
        10,
        0.1,
        3,
        "Brightness",
        "Moves the pad from a plain, mellow tone to a brighter, buzzier, more harmonically complex one.",
    )
    def fm_index(self, value: float) -> None:
        self.fm_voice.index = value

    @Param(
        0,
        1,
        0.05,
        0.25,
        "Space",
        "Sets how large and distant the pad's room feels, from a tight close ambience to a huge, "
        "cavernous decay.",
    )
    def reverb_size(self, value: float) -> None:
        self.reverb.size = value

    @Param(
        0,
        1,
        0.05,
        0.15,
        "Tail darkness",
        "Darkens the reverb tail as it decays; higher settings sound warmer and more muffled, lower "
        "settings stay bright and shimmering.",
    )
    def reverb_damp(self, value: float) -> None:
        self.reverb.damp = value

    @Param(
        0,
        1,
        0.05,
        0.1,
        "Distance",
        "Blends how much of the pad is heard through the reverb versus dry; higher dissolves it into an "
        "atmospheric wash, lower keeps it present and up front.",
    )
    def reverb_bal(self, value: float) -> None:
        self.reverb.bal = value

    def build(self, tempo: Tempo, clock: Clock) -> Patch:
        self._reset()

        step_time = tempo.sixteenth * self.step_division

        # slow swell over 32 steps so the pad breathes in and out across two bars
        self.arp_swell = Sine(freq=1 / (32 * step_time), mul=0.01, add=0.5)

        self.envelope_table = CosTable(ENVELOPE_POINTS)
        self.arp_env = TrigEnv(
            self.trigger, self.envelope_table, dur=step_time * 1.2, mul=self.arp_swell, add=-0.3
        )

        # slow, detuned ratio for a warm, slightly unstable atmospheric tone;
        # carrier/ratio/index start neutral here - each one's @Param control
        # sets the real value once finish() binds every control below
        self.fm_voice = FM(mul=self.arp_env, add=-0.3)
        self.reverb = Freeverb(self.fm_voice)

        # step_division is a rebuild-only raw tick count, not a live rate
        # offset from a base division, so self.schedule()'s rate machinery
        # doesn't apply here; self._division/self._clock are set directly,
        # the way schedule() would, which is all finish()/next_step need to
        # have happened.
        self._clock = clock
        self._division = clock.subscribe(self.step_division, self.next_step)
        return self.finish(self.reverb)

    def next_step(self) -> None:
        # derived from the shared clock's own tick, not a local counter
        # that starts at 0 whenever this patch is built or restarted -
        # see `Clock.tick`'s docstring
        i = (self._clock.tick // self.step_division) % len(ARP_INTERVALS)
        self.fm_voice.carrier = self.arp_root * pow(2, ARP_INTERVALS[i] / 12)
        self.trigger.play()
