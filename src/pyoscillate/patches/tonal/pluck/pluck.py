# uv run flet run src/flet/patch/app.py -- pyoscillate.patches.tonal.pluck.pluck

from __future__ import annotations

from typing import ClassVar

from pyo import PyoObject
from pyo.lib.controls import SigTo
from pyo.lib.effects import Freeverb
from pyo.lib.generators import FM

from pyoscillate.clock import NoteDivision
from pyoscillate.harmony import Harmony
from pyoscillate.patches.base import BuildContext, Patch
from pyoscillate.patches.common import ChordRoot, Gate, GatedVoice, Phrased
from pyoscillate.patches.params import Param, rate_param
from pyoscillate.theory.phrase import Hooks, PhraseRole
from pyoscillate.theory.pitch import Note


class Pluck(Gate, ChordRoot, Phrased, GatedVoice):
    """Single-note FM pluck with a fast amplitude contour and a brighter,
    quickly-decaying modulation index. Style subclasses supply the pattern."""

    volume = Patch.volume.replace(default=0.4)
    phrase_roles = (PhraseRole.HOOK,)
    phrase = Phrased.phrase.replace(
        default=Hooks.SPARSE_HOOK,
        help_text="Picks which chord tones are played and when, from a sparse hook to one that fills every step.",
    )
    base_division: ClassVar[NoteDivision] = NoteDivision.EIGHTH
    gain: ClassVar[float] = 0.14
    modulator_ratio: ClassVar[float] = 2.0
    triads: ClassVar[dict[int, tuple[int, int, int]]] = {
        0: (0, 4, 7),
        2: (0, 3, 7),
        4: (0, 3, 7),
        5: (0, 4, 7),
        7: (0, 4, 7),
        9: (0, 3, 7),
        11: (0, 3, 6),
    }

    pitch: SigTo
    amp_env: PyoObject
    brightness_env: PyoObject
    fm_voice: FM
    space: Freeverb
    harmony: Harmony

    root_freq = ChordRoot.root_freq.replace(
        default=Note.E3,
        help_text="Sets the chord-root register; the plucked chord tones sound an octave above it.",
    )

    @Param(
        0,
        5,
        0.1,
        2.4,
        "Brightness",
        "Sets the initial harmonic bite; the modulation naturally fades on each pluck.",
        sweep=True,
    )
    def brightness(self, value: float) -> None:
        self.brightness_env.mul = value

    @Param(
        0.1,
        1.5,
        0.05,
        0.45,
        "Decay",
        "Sets how long each plucked note rings before it falls away.",
        sweep=True,
    )
    def decay(self, value: float) -> None:
        self.amp_env.dur = value

    @Param(
        0.03,
        0.7,
        0.01,
        0.2,
        "Brightness decay",
        "Shortens or lengthens the bright attack; a shorter value makes each note softer sooner.",
        sweep=True,
        advanced=True,
    )
    def brightness_decay(self, value: float) -> None:
        self.brightness_env.dur = value

    rate = rate_param(
        base_division,
        "Halves or doubles the hook's speed for each step away from its eighth-note grid.",
    )

    def _note_frequency(self, tone_index: int, bar_index: int) -> float:
        degree = self.chord_offset(self.harmony, bar_index) % 12
        root = self.root_at(bar_index)
        triad = self.triads.get(degree, (0, 4, 7))
        return Note.transpose(root, 12 + triad[tone_index])

    def build(self, context: BuildContext) -> Patch:
        self._reset()
        self.harmony = context.harmony

        initial_frequency = self._note_frequency(0, context.clock.bar_index)
        self.pitch = SigTo(value=initial_frequency, time=0.01)
        self.amp_env = self.envelope(
            [(0, 0), (80, 1), (8191, 0)], dur=self.decay, exp=3
        )
        self.brightness_env = self.envelope(
            [(0, 1), (8191, 0)], dur=self.brightness_decay, mul=0, exp=3
        )
        self.fm_voice = FM(
            carrier=self.pitch,
            ratio=self.modulator_ratio,
            index=self.brightness_env,
            mul=self.amp_env * self.gain,
        )
        self.space = Freeverb(self.fm_voice, size=0.35, damp=0.55, bal=0.22)

        self.schedule_pattern(context)
        return self.finish(self.add_gate(self.space, context))

    def next_step(self) -> None:
        step = self._step()
        if not step.hit:
            self.amp_env.stop()
            self.brightness_env.stop()
            return

        self.pitch.value = self._note_frequency(step.value, self._clock.bar_index)
        self.trigger.play()


class PluckHook(Pluck):
    """Soft, sparse-to-full chord-tone hook in the middle and upper register."""

    title = "Hook - Pluck"
    summary = "Soft FM pluck tracing the shared chord tones above the bass and pad."
