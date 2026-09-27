# uv run flet run src/flet/patch/app.py -- pyoscillate.patches.tonal.bass.hover
"""Dark, reverb-soaked bass that hovers on a fixed tonic rather than
following the rack's chord - see `profiles.HOVER` for the four-bar
E/F/G/A neighbour-tone phrase this reads. Unlike `groove.GrooveBass`
(16th-note, chord-following, dry), this style is built for a slowed,
"tape-warped" ambience: a near-sine tone, a steady 8th-note pulse, and its
own long reverb tail with a slow breathing swell, rather than a dry voice
left for the rack to treat externally - see `voice_output()`.
"""

from __future__ import annotations

from pyo import PyoObject
from pyo.lib.effects import Freeverb
from pyo.lib.generators import Sine

from pyoscillate.clock import Clock
from pyoscillate.patches.base import Patch
from pyoscillate.patches.params import Param, rate_param
from pyoscillate.patches.tonal.bass.base import BASE_DIVISION, Bass
from pyoscillate.patches.tonal.bass.profiles import HOVER
from pyoscillate.patches.utility.notes import notes
from pyoscillate.tempo import Tempo


class BassHover(Bass):
    """Dark, sine-like bass that hovers on a fixed tonic with slow stepwise
    neighbour motion, soaked in a long, slowly breathing reverb tail rather
    than articulated with a plucky envelope."""

    title = "Bass - Hover"
    summary = "Dark, sine-like bass hovering on the tonic under a slow, breathing reverb tail."
    # a continuous, densely-retriggered source through a long `Freeverb` tail
    # builds up more sustained energy than a single struck note - kept low
    # enough that the loudest corner (max Space/Breath/Brightness) still
    # clears the patch limiter, checked offline
    volume_default = 0.22

    reverb_voice: Freeverb
    breath_lfo: Sine
    breathed: PyoObject
    _tempo: Tempo

    # read live off `self.root_freq` by `Bass.note_root`'s trigger-time
    # callback - no control body needed, see `patches/AGENTS.md`'s note on a
    # parameter only read by a sequencer callback
    root_freq = Param(
        notes.E0,
        notes.E2,
        1,
        notes.E1,
        "Register",
        "Sets the tonic the bass hovers around.",
        scale="note",
    )

    @Param(
        120,
        900,
        10,
        280,
        "Brightness",
        "Opens or closes the bass's low-pass filter; kept dark and rounded by default so it stays "
        "clean and sine-like rather than buzzy.",
    )
    def cutoff(self, value: float) -> None:
        self.filtered.freq = value

    @Param(
        0,
        1,
        0.05,
        0.85,
        "Space",
        "Sets how large and distant the reverb tail feels, from a close presence to a huge, "
        "cavernous decay.",
    )
    def reverb_size(self, value: float) -> None:
        self.reverb_voice.size = value

    @Param(
        0,
        1,
        0.05,
        0.5,
        "Tail darkness",
        "Darkens the reverb tail as it decays; higher settings sound warmer and more muffled, lower "
        "settings stay brighter.",
    )
    def reverb_damp(self, value: float) -> None:
        self.reverb_voice.damp = value

    @Param(
        0,
        1,
        0.05,
        0.55,
        "Distance",
        "Blends how much of the bass is heard through the reverb versus dry; higher dissolves it "
        "into the wash, lower keeps the pulse present.",
    )
    def reverb_bal(self, value: float) -> None:
        self.reverb_voice.bal = value

    @Param(
        0,
        0.6,
        0.05,
        0.25,
        "Breath",
        "Depth of a slow, multi-bar amplitude swell; higher makes the bass visibly breathe in "
        "and out, lower keeps its level steadier.",
    )
    def breath(self, value: float) -> None:
        self.breath_lfo.mul = value * 0.5
        self.breath_lfo.add = 1 - value * 0.5

    rate = rate_param(
        BASE_DIVISION,
        "Halves or doubles the bass's pulse speed for each step away from its steady 8th-note grid.",
    )

    def voice_output(self) -> PyoObject:
        self.reverb_voice = Freeverb(self.filtered, size=self.reverb_size, damp=self.reverb_damp)
        # a single slow cycle every four bars - slow enough to read as
        # "breathing" (see the rack's README) rather than tremolo. `mul`/
        # `add` are neutral (no swell) here; `breath`'s control sets the
        # real depth once `finish()` runs every control below.
        self.breath_lfo = Sine(freq=1 / (self._tempo.bar * 4), mul=0, add=1)
        self.breathed = self.reverb_voice * self.breath_lfo
        return self.breathed

    def build(self, tempo: Tempo, clock: Clock) -> Patch:
        self._reset()
        self._tempo = tempo
        return self.build_voice(
            tempo,
            clock,
            HOVER,
            self.root_freq,
            self.cutoff,
            self.rate,
            harmony=None,
        )
