# uv run flet run src/flet/patch/app.py -- pyoscillate.patches.tonal.bass.fm.fm style=bark
#   style: bark | grit
"""FM bass: every note barks bright, then settles to a rounder tone.

The index follows a break-point table (pyo example x10/01's index
`LinTable` 20 → 10 → 0, scaled to 1 → 0.5 → 0) read over Settle seconds, on
top of a steady Edge floor. Accented steps scale the bark as well as the
level, so the groove's accents hit harder and brighter. That is the FM
equivalent of velocity opening the index.

- `bark` (`FmBassBark`): two-operator FM (x03/03 `FM`) at integer ratio 1, so
  the spectrum stays harmonic and the note keeps a clear pitch at any index.
- `grit` (`FmBassGrit`): `CrossFM` (x03/03) at ratio 2. The carrier modulates
  the modulator back, which roughens the bark into a buzzier, less stable
  edge.

The note line is the `rolling` groove profile, on the shared clock. Both
styles share the `FmBass` base below; only the operator pair built in
`tone()` differs, since that is genuinely different behavior, not just
different profile data (`patches/CLAUDE.md`'s design rule 1).
"""

from __future__ import annotations

from typing import Any, ClassVar

from pyo import PyoObject
from pyo.lib.controls import SigTo
from pyo.lib.filters import ButHP
from pyo.lib.generators import FM, CrossFM
from pyo.lib.tables import CosTable, LinTable
from pyo.lib.triggers import TrigEnv

from pyoscillate.clock import Clock, NoteDivision
from pyoscillate.patches.base import Patch
from pyoscillate.patches.params import PyoParamRef, SliderSpec
from pyoscillate.patches.tonal.bass.base import Bass
from pyoscillate.patches.tonal.bass.profiles import GROOVE
from pyoscillate.patches.utility.notes import notes
from pyoscillate.tempo import Tempo

STYLES = ("bark", "grit")
BASE_DIVISION = NoteDivision.SIXTEENTH
PROFILE = GROOVE["rolling"]

PARAMETERS = (
    SliderSpec(
        "root_freq",
        notes.B0,
        notes.A2,
        1,
        notes.A1,
        "Register",
        "Moves the bassline up or down; low sits under the kick as weight, high brings the bark forward as a melodic line.",
        (PyoParamRef(FM, "carrier"), PyoParamRef(CrossFM, "carrier")),
        scale="note",
    ),
    SliderSpec(
        "growl",
        0,
        12,
        0.5,
        6,
        "Growl",
        "How hard each note barks: low is a soft, round thump, high a bright, buzzing snarl at the start of every note.",
        (PyoParamRef(TrigEnv, "mul"),),
    ),
    SliderSpec(
        "settle",
        0.02,
        0.4,
        0.01,
        0.12,
        "Settle",
        "How long the bark takes to die down, in seconds: short is a quick pluck on the front of the note, long a slow, wah-like close.",
        (PyoParamRef(TrigEnv, "dur"),),
    ),
    SliderSpec(
        "edge",
        0,
        3,
        0.1,
        0.5,
        "Edge",
        "The brightness left once the bark has settled: at 0 the note settles to a pure sub, higher keeps a buzzing edge under the whole note.",
        (PyoParamRef(SigTo, "value"),),
    ),
    SliderSpec(
        "length",
        0.3,
        1.5,
        0.05,
        0.9,
        "Length",
        "How long each note lasts, in 16ths: short is tight and staccato, long runs one note into the next.",
        (PyoParamRef(TrigEnv, "dur"),),
    ),
    SliderSpec(
        "rate",
        Clock.rate_limits(BASE_DIVISION)[0],
        Clock.rate_limits(BASE_DIVISION)[1],
        1,
        0,
        "Rate",
        "Halves or doubles the bassline speed for each step away from its 16th-note grid.",
    ),
)
# x10/01's index break-points, normalised: a fast drop to half, then a
# linear fall to nothing over the rest of Settle
INDEX_POINTS = [(0, 1.0), (512, 0.5), (8191, 0.0)]
# the bass core's amplitude shape: a quick rise, a held body, then the release
AMP_POINTS = [(0, 0.0), (80, 1.0), (2100, 0.5), (8191, 0.0)]
RATIOS = {"bark": 1, "grit": 2}
# `grit`: how strongly the carrier modulates the modulator back, relative to
# the main index
CROSS = 0.5
# FM keeps a constant amplitude whatever the index, so the peak is GAIN x
# accent x volume before the subsonic high-pass, whose phase shift adds up to
# ~25% to the crest at the lowest Register
GAIN = 0.3
# under the lowest Register (30 Hz), which loses under 1 dB to it
SUBSONIC = 20
VOLUME_DEFAULT = 0.42


class FmBass(Bass):
    """FM bass base: every note barks bright, then settles to a rounder
    tone. Style variants subclass this and override `tone()` for FM vs.
    CrossFM; the rest of the graph is identical. See the module docstring
    for the sonic detail."""

    parameters = PARAMETERS
    volume_default = VOLUME_DEFAULT

    root_freq: float
    growl: float
    settle: float
    edge: float
    length: float
    rate: float

    ratio: ClassVar[int]

    def tone(self, index: PyoObject, level: PyoObject) -> tuple[PyoObject, tuple[Any, ...]]:
        """This style's FM operator pair, unfiltered, plus any extra Pyo
        objects it built for `build()` to retain. Overridden per style."""
        raise NotImplementedError

    def build(self, tempo: Tempo, clock: Clock, **values: Any) -> Patch:
        """Build an FM bassline whose index barks on each note."""
        self.configure(**values)
        self._reset()
        # matches the free `Trig()` this voice used before it was migrated
        # onto `Bass`'s trigger: silent until the clock ticks (see
        # tests/pyoscillate/patches/test_gated_patches.py)
        self.trigger.stop()
        state = {"step": 0, "root": self.root_freq, "growl": self.growl, "accent": 1.0}

        index_table = LinTable(INDEX_POINTS)
        amp_table = CosTable(AMP_POINTS)
        bark = TrigEnv(self.trigger, index_table, dur=self.settle, mul=self.growl)
        floor = SigTo(value=self.edge, time=0.05, init=self.edge)
        index = bark + floor
        amp = TrigEnv(self.trigger, amp_table, dur=tempo.sixteenth * self.length)
        level = amp * GAIN
        self.retain(index_table, amp_table, bark, floor, index, amp, level)

        tone, tone_resources = self.tone(index, level)
        self.retain(*tone_resources, tone)
        # at ratio 1 the first lower sideband lands on 0 Hz, so the bark carries a
        # DC offset that follows the index envelope: a subsonic thump that eats
        # headroom. CrossFM's feedback does the same at high index. A 2nd-order
        # high-pass below the lowest Register clears it; pyo's one-pole DCBlock
        # is too slow for an offset that moves within a few milliseconds.
        voice = ButHP(tone, freq=SUBSONIC)

        def next_step() -> None:
            step = state["step"] % len(PROFILE.pattern)
            state["accent"] = PROFILE.accents[step]
            tone.carrier = state["root"] * 2 ** (PROFILE.pattern[step] / 12)
            bark.mul = state["growl"] * state["accent"]
            amp.mul = state["accent"]
            self.trigger.play()
            state["step"] += 1

        def set_growl(value: float) -> None:
            state["growl"] = value
            bark.mul = value * state["accent"]

        self.schedule(BASE_DIVISION, self.rate, clock, next_step)
        return self.finish(
            voice,
            {
                "root_freq": lambda value: state.update(root=value),
                "growl": set_growl,
                "settle": lambda value: setattr(bark, "dur", value),
                "edge": lambda value: setattr(floor, "value", value),
                "length": lambda value: setattr(amp, "dur", tempo.sixteenth * value),
            },
        )


class FmBassBark(FmBass):
    """Clean, harmonic bark: two-operator FM at ratio 1."""

    ratio = RATIOS["bark"]

    def tone(self, index: PyoObject, level: PyoObject) -> tuple[PyoObject, tuple[Any, ...]]:
        tone = FM(carrier=self.root_freq, ratio=self.ratio, index=index, mul=level)
        return tone, ()


class FmBassGrit(FmBass):
    """Grittier, less stable bark: carrier and modulator cross-modulate at ratio 2."""

    ratio = RATIOS["grit"]

    def tone(self, index: PyoObject, level: PyoObject) -> tuple[PyoObject, tuple[Any, ...]]:
        cross = index * CROSS
        tone = CrossFM(carrier=self.root_freq, ratio=self.ratio, ind1=cross, ind2=index, mul=level)
        return tone, (cross,)
