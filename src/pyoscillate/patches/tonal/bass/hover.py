# uv run flet run src/flet/patch/app.py -- pyoscillate.patches.tonal.bass.hover
"""Dark, reverb-soaked bass that hovers on a fixed tonic rather than
following the rack's chord - see `Melody.BASS_HOVER` for the four-bar
E/F/G/A neighbour-tone phrase it starts on. Unlike `groove.GrooveBass`
(16th-note, chord-following, dry), this style is built for a slowed,
"tape-warped" ambience: a near-sine tone, a steady 8th-note pulse, and its
own long reverb tail with a slow breathing swell, rather than a dry voice
left for the rack to treat externally - see `voice_output()`.
"""

from __future__ import annotations

from pyo import PyoObject
from pyo.lib.generators import Sine

from pyoscillate.patches.base import Patch
from pyoscillate.patches.common import Reverb, RootPitch
from pyoscillate.patches.params import Param, rate_param
from pyoscillate.patches.tonal.bass.base import BASE_DIVISION, AccentBass
from pyoscillate.patches.tonal.bass.profiles import HOVER
from pyoscillate.theory import notes
from pyoscillate.theory.intervals import Melody


class BassHover(Reverb, RootPitch, AccentBass):
    """Dark, sine-like bass that hovers on a fixed tonic with slow stepwise
    neighbour motion, soaked in a long, slowly breathing reverb tail rather
    than articulated with a plucky envelope."""

    title = "Bass - Hover"
    summary = "Dark, sine-like bass hovering on the tonic under a slow, breathing reverb tail."
    # a continuous, densely-retriggered source through a long `Freeverb` tail
    # builds up more sustained energy than a single struck note - kept low
    # enough that the loudest corner (max Space/Breath/Brightness) still
    # clears the patch limiter, checked offline
    volume = Patch.volume.replace(default=0.22)
    profile = HOVER
    melody = AccentBass.melody.replace(default=Melody.BASS_HOVER.index)

    breath_lfo: Sine
    breathed: PyoObject

    # read live off `self.root_freq` by `current_root`'s trigger-time
    # callback - no control body needed, see `patches/AGENTS.md`'s note on a
    # parameter only read by a sequencer callback
    root_freq = RootPitch.root_freq.replace(
        minimum=notes.E0,
        maximum=notes.E2,
        default=notes.E1,
        help_text="Sets the tonic the bass hovers around.",
    )

    @Param(
        120,
        900,
        10,
        280,
        "Brightness",
        "Opens or closes the bass's low-pass filter; kept dark and rounded by default so it stays "
        "clean and sine-like rather than buzzy.",
        sweep=True,
    )
    def cutoff(self, value: float) -> None:
        self.filtered.freq = value

    reverb_size = Reverb.reverb_size.replace(default=0.85)
    reverb_bal = Reverb.reverb_bal.replace(default=0.55)

    @Param(
        0,
        0.6,
        0.05,
        0.25,
        "Breath",
        "Depth of a slow, multi-bar amplitude swell; higher makes the bass visibly breathe in "
        "and out, lower keeps its level steadier.",
        sweep=True,
    )
    def breath(self, value: float) -> None:
        self.breath_lfo.mul = value * 0.5
        self.breath_lfo.add = 1 - value * 0.5

    rate = rate_param(
        BASE_DIVISION,
        "Halves or doubles the bass's pulse speed for each step away from its steady 8th-note grid.",
    )

    def voice_output(self) -> PyoObject:
        self.reverb = self.add_reverb(self.filtered)
        # a single slow cycle every four bars - slow enough to read as
        # "breathing" (see the rack's README) rather than tremolo. `mul`/
        # `add` are neutral (no swell) here; `breath`'s control sets the
        # real depth once `finish()` runs every control below.
        self.breath_lfo = self.tempo_sine(
            self._tempo, lambda t: t.bar * 4, mul=0, add=1
        )
        self.breathed = self.reverb * self.breath_lfo
        return self.breathed

    def current_root(self) -> float:
        return self.root_freq
