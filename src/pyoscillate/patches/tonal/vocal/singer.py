# uv run flet run src/flet/patch/app.py -- pyoscillate.patches.tonal.vocal.solo
"""Sung voices: the bases every vocal patch shares.

`Singer` is a held voice (`common.Held`: notes, vibrato, glide, legato) with
what any voice has beside its pitch: breath, a little unsteadiness in the
pitch, and a room (`Reverb`). It leaves two things to the style: the `source`
(what is excited) and the `tract` (what shapes it).

`FormantSinger` is the speaking and singing voice. The source is a sawtooth at
the note's pitch, the vocal folds' buzz, rolled off by Brightness (how hard
the voice is pushed); the tract is five resonant band-pass filters, one per
formant, tuned to the frequencies a mouth of that shape favours. A vowel is
nothing but where those five peaks sit, so Vowel moves them (through a table
of measured vowels, interpolated, so it sweeps), Throat scales them all (a
smaller mouth for a childlike voice, a larger one for a giant) and Focus
sharpens or softens them. The pitch never changes: that is the point of a
formant filter, and what a plain low-pass cannot do.

Breath is noise let into the tract beside the buzz, so a breathy voice is
shaped by the same vowel. An ensemble (`Ensemble`) repeats every note in
several detuned copies, each with its own vibrato, which is what makes a
section sound like people.
"""

from __future__ import annotations

from typing import ClassVar

from pyo import PyoObject
from pyo.lib._core import Mix
from pyo.lib.controls import SigTo
from pyo.lib.filters import ButLP, Reson
from pyo.lib.generators import LFO, Noise
from pyo.lib.randoms import Randi

from pyoscillate.patches.common import Held, Reverb
from pyoscillate.patches.params import Param


class VocalTract:
    """Formant tables: for each voice type, the five vowels `oo oh ah eh ee`
    (the order a vowel triangle runs in, so neighbours morph smoothly), each as
    five formants of `(frequency Hz, level dB, bandwidth Hz)`. The classic
    singing-voice formant data (Dodge & Jerse, as tabulated in the Csound
    manual); a synthesis reference, not a measurement of any one singer."""

    SOPRANO: ClassVar[tuple[tuple[tuple[float, float, float], ...], ...]] = (
        (
            (325, 0, 50),
            (700, -16, 60),
            (2700, -35, 170),
            (3800, -40, 180),
            (4950, -60, 200),
        ),
        (
            (450, 0, 40),
            (800, -11, 80),
            (2830, -22, 100),
            (3800, -22, 120),
            (4950, -50, 120),
        ),
        (
            (800, 0, 80),
            (1150, -6, 90),
            (2900, -32, 120),
            (3900, -20, 130),
            (4950, -50, 140),
        ),
        (
            (350, 0, 60),
            (2000, -20, 100),
            (2800, -15, 120),
            (3600, -40, 150),
            (4950, -56, 200),
        ),
        (
            (270, 0, 60),
            (2140, -12, 90),
            (2950, -26, 100),
            (3900, -26, 120),
            (4950, -44, 120),
        ),
    )
    ALTO: ClassVar[tuple[tuple[tuple[float, float, float], ...], ...]] = (
        (
            (325, 0, 50),
            (700, -12, 60),
            (2530, -30, 170),
            (3500, -40, 180),
            (4950, -64, 200),
        ),
        (
            (450, 0, 70),
            (800, -9, 80),
            (2830, -16, 100),
            (3500, -28, 130),
            (4950, -55, 135),
        ),
        (
            (800, 0, 80),
            (1150, -4, 90),
            (2800, -20, 120),
            (3500, -36, 130),
            (4950, -60, 140),
        ),
        (
            (400, 0, 60),
            (1600, -24, 80),
            (2700, -30, 120),
            (3300, -35, 150),
            (4950, -60, 200),
        ),
        (
            (350, 0, 50),
            (1700, -20, 100),
            (2700, -30, 120),
            (3700, -36, 150),
            (4950, -60, 200),
        ),
    )
    TENOR: ClassVar[tuple[tuple[tuple[float, float, float], ...], ...]] = (
        (
            (350, 0, 40),
            (600, -20, 80),
            (2700, -17, 100),
            (2900, -14, 120),
            (3300, -26, 120),
        ),
        (
            (400, 0, 40),
            (800, -10, 80),
            (2600, -12, 100),
            (2800, -12, 120),
            (3000, -26, 120),
        ),
        (
            (650, 0, 80),
            (1080, -6, 90),
            (2650, -7, 120),
            (2900, -8, 130),
            (3250, -22, 140),
        ),
        (
            (400, 0, 70),
            (1700, -14, 80),
            (2600, -12, 100),
            (3200, -14, 120),
            (3580, -20, 120),
        ),
        (
            (290, 0, 40),
            (1870, -15, 90),
            (2800, -18, 100),
            (3250, -20, 120),
            (3540, -30, 120),
        ),
    )
    BASS: ClassVar[tuple[tuple[tuple[float, float, float], ...], ...]] = (
        (
            (350, 0, 40),
            (600, -20, 80),
            (2400, -32, 100),
            (2675, -28, 120),
            (2950, -36, 120),
        ),
        (
            (400, 0, 40),
            (750, -11, 80),
            (2400, -21, 100),
            (2600, -20, 120),
            (2900, -40, 120),
        ),
        (
            (600, 0, 60),
            (1040, -7, 70),
            (2250, -9, 110),
            (2450, -9, 120),
            (2750, -20, 130),
        ),
        (
            (400, 0, 40),
            (1620, -12, 80),
            (2400, -9, 100),
            (2800, -12, 120),
            (3100, -18, 120),
        ),
        (
            (250, 0, 60),
            (1750, -30, 90),
            (2600, -16, 100),
            (3050, -22, 120),
            (3340, -28, 120),
        ),
    )


class Singer(Reverb, Held):
    """A held voice with breath, unsteadiness and a room. A style builds its
    `source` and `tract` and gives every shared control its own starting
    value."""

    # the loudest breath noise gets next to the tone, and the widest the pitch
    # wanders (as a fraction of the pitch) at full Unsteadiness
    breath_max: ClassVar[float] = 0.5
    drift_max: ClassVar[float] = 0.012
    # how fast the pitch wanders (Hz): slow and irregular, a human's drift
    drift_rate: ClassVar[float] = 3.0
    # seconds the breath and drift take to follow a new setting
    level_glide: ClassVar[float] = 0.05

    breath_level: SigTo
    breath_gain: PyoObject
    breath_noise: Noise
    source: PyoObject
    drift_depth: SigTo
    drift_noise: Randi
    drift_ratio: PyoObject
    wandering_pitch: PyoObject

    @Param(
        0,
        1,
        0.05,
        0.15,
        "Breath",
        "How much air rides on the voice; none is a clean, pure tone, a little is a soft, intimate breath, a lot is a hushed, whispery voice.",
        sweep=True,
    )
    def breath(self, value: float) -> None:
        self.breath_level.value = value * self.breath_max

    @Param(
        0,
        1,
        0.05,
        0.3,
        "Unsteadiness",
        "How much the pitch wanders by itself; none is a rock-steady, machine-exact note, a little is a living, human voice, a lot is a wavering, unsure one.",
        sweep=True,
    )
    def unsteadiness(self, value: float) -> None:
        self.drift_depth.value = value * self.drift_max

    def modulation(self) -> PyoObject:
        """The vibrato and the pitch's slow random wander."""
        self.drift_depth = SigTo(value=0, time=self.level_glide)
        self.drift_noise = Randi(
            min=-1,
            max=1,
            freq=[
                self.drift_rate * (1 + self.vibrato_scatter * position)
                for _ in range(self.note_count())
                for position in self.copy_positions()
            ],
            mul=self.drift_depth,
        )
        self.drift_ratio = self.drift_noise + 1
        self.wandering_pitch = self.vibrato_ratio * self.drift_ratio
        return self.wandering_pitch

    @classmethod
    def section_trim(cls) -> float:
        """The level each voice is trimmed to: the voices of a section add in
        power, so a choir of ten is as loud as a soloist, not three times
        louder."""
        return 1 / cls.voice_count() ** 0.5

    def make_source(self) -> PyoObject:
        """What the voice is excited with, one stream per voice, silenced by
        `voice_gain`. Supplied by a style."""
        raise NotImplementedError

    def make_tract(self, source: PyoObject, breath: PyoObject) -> PyoObject:
        """The `source` and `breath` shaped into the voice, mixed to one
        stream. Supplied by a style."""
        raise NotImplementedError

    def make_tone(self) -> PyoObject:
        self.breath_level = SigTo(value=0, time=self.level_glide)
        self.breath_gain = self.breath_level * self.voice_gain * self.section_trim()
        self.breath_noise = Noise(mul=self.breath_gain)
        self.source = self.make_source()
        return self.make_tract(self.source, self.breath_noise)

    def voice_stage(self, signal: PyoObject) -> PyoObject:
        self.reverb = self.add_reverb(signal)
        return self.reverb


class FormantSinger(Singer):
    """A voice shaped by five formants: a sawtooth buzz through a bank of
    band-pass filters tuned by Vowel, Throat and Focus. A style names its
    `voice_type` (a `VocalTract` table)."""

    voice_type: ClassVar[tuple[tuple[tuple[float, float, float], ...], ...]] = (
        VocalTract.ALTO
    )
    # the sawtooth's level, which brings the filter bank to the loudness of the
    # other held voices
    gain: ClassVar[float] = 0.25
    # how much of the unfiltered buzz is let past the formants: a mouth
    # passes a little of everything, so a note falling between two formants
    # is quieter, not gone
    direct_mix: ClassVar[float] = 0.1
    # seconds the formants take to follow a new Vowel, Throat or Focus, so a
    # sweep glides through the vowels instead of stepping
    formant_glide: ClassVar[float] = 0.04
    # the vowel table's last index: Vowel runs 0 to this
    last_vowel: ClassVar[int] = 4
    # a sharper formant passes less of the buzz, so each is brought back up by
    # Focus to this power, which holds the voice at one loudness (measured)
    focus_makeup: ClassVar[float] = 0.85

    glottal_level: PyoObject
    glottis: LFO
    glottal_tone: ButLP
    formant_freqs: list[SigTo]
    formant_qs: list[SigTo]
    formant_gains: list[SigTo]
    resonators: list[Reson]
    excited: PyoObject
    direct: PyoObject
    vowel_bank: Mix

    @Param(
        0,
        4,
        0.05,
        2.0,
        "Vowel",
        "Shapes the mouth: 0 is a closed 'oo', 1 'oh', 2 an open 'ah', 3 'eh' and 4 a bright 'ee', morphing smoothly between them; sweep it for 'wah' and 'yeah'.",
        sweep=True,
    )
    def vowel(self, value: float) -> None:
        self.apply_tract()

    @Param(
        0.7,
        1.4,
        0.01,
        1.0,
        "Throat",
        "How big the singer is; small is a thin, childlike or cartoon voice, large is a deep, hollow, giant one, changing the colour of the voice without moving its pitch.",
        sweep=True,
    )
    def throat(self, value: float) -> None:
        self.apply_tract()

    @Param(
        0.4,
        3.0,
        0.05,
        1.0,
        "Focus",
        "How sharply the mouth rings on its vowel; low is a soft, open, blurred 'aah', high is a ringing, nasal voice where the vowel stands out.",
        sweep=True,
    )
    def focus(self, value: float) -> None:
        self.apply_tract()

    @Param(
        500,
        9000,
        0.02,
        3500,
        "Brightness",
        "How hard the voice is pushed; low is a soft, covered, muffled tone, high is a pressed, bright, edgy one with more top end.",
        scale="cutoff",
        sweep=True,
    )
    def brightness(self, value: float) -> None:
        self.glottal_tone.freq = value

    def apply_tract(self) -> None:
        """Move every formant to where Vowel, Throat and Focus put it: the
        two neighbouring vowels of the table blended, their frequencies scaled
        by Throat and their sharpness by Focus."""
        lower = min(int(self.vowel), self.last_vowel - 1)
        blend = self.vowel - lower
        for index, (near, far) in enumerate(
            zip(self.voice_type[lower], self.voice_type[lower + 1], strict=True)
        ):
            freq = (near[0] + (far[0] - near[0]) * blend) / self.throat
            level = near[1] + (far[1] - near[1]) * blend
            width = near[2] + (far[2] - near[2]) * blend
            self.formant_freqs[index].value = freq
            self.formant_qs[index].value = self.focus * freq / width
            self.formant_gains[index].value = 10 ** (level / 20) * (
                self.focus**self.focus_makeup
            )

    def make_source(self) -> PyoObject:
        # the voices add in power, so each is trimmed by the section's size
        self.glottal_level = self.voice_gain * (self.gain * self.section_trim())
        self.glottis = LFO(
            freq=self.held_pitch, sharp=1.0, type=0, mul=self.glottal_level
        )
        self.glottal_tone = ButLP(self.glottis, freq=self.brightness)
        return self.glottal_tone

    def make_tract(self, source: PyoObject, breath: PyoObject) -> PyoObject:
        count = len(self.voice_type[0])
        self.formant_freqs = [
            SigTo(value=800, time=self.formant_glide) for _ in range(count)
        ]
        self.formant_qs = [
            SigTo(value=8, time=self.formant_glide) for _ in range(count)
        ]
        self.formant_gains = [
            SigTo(value=1, time=self.formant_glide) for _ in range(count)
        ]
        self.excited = source + breath
        self.resonators = [
            Reson(self.excited, freq=freq, q=q, mul=level)
            for freq, q, level in zip(
                self.formant_freqs, self.formant_qs, self.formant_gains, strict=True
            )
        ]
        self.retain(
            *self.formant_freqs, *self.formant_qs, *self.formant_gains, *self.resonators
        )
        self.direct = self.excited * self.direct_mix
        self.retain(self.direct)
        self.vowel_bank = Mix([*self.resonators, self.direct], voices=1)
        return self.vowel_bank
