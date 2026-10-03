# uv run flet run src/flet/patch/app.py -- pyoscillate.patches.drums.tom.tom
"""Pitched tom voice.

A pitched drum hit: a sine body with a quick but audible downward sweep, a
faster-decaying membrane overtone, and a short transient. It plays a sparse
two-bar fill down a minor pentatonic built on the rack's current chord root,
adding pitched contour to the kit without the weight of the kick.
"""

from typing import ClassVar

from pyo import PyoObject
from pyo.lib._core import Sig
from pyo.lib.filters import Biquad
from pyo.lib.generators import Sine
from pyo.lib.triggers import TrigEnv

from pyoscillate.clock import NoteDivision
from pyoscillate.harmony import Harmony
from pyoscillate.patches.base import BuildContext, Patch
from pyoscillate.patches.common import Phrased
from pyoscillate.patches.drums.base import DROP, DrumVoice
from pyoscillate.patches.params import Param, rate_param
from pyoscillate.theory.phrase import Fills, PhraseRole
from pyoscillate.theory.pitch import Note


class Tom(Phrased, DrumVoice):
    """Pitched tom playing a sparse two-bar fill on the current chord.

    The fill follows the chord rather than only the key: the rack's chords
    are parallel minor sevenths, so a pentatonic fixed to the key would land
    on non-chord tones over some of them.
    """

    summary = "Sparse two-bar tom fill on the current chord's minor pentatonic."
    volume = Patch.volume.replace(default=0.3)
    base_division: ClassVar[NoteDivision] = NoteDivision.SIXTEENTH

    # settled body pitch (Hz); pitch-bend depth/time; body decay; membrane
    # overtone ratio/level/decay; transient level/tuning/resonance/duration;
    # amplitude and pitch-bend curve exponents
    body_freq: ClassVar[float] = Note.A2
    bend_depth: ClassVar[float] = 0.4
    bend_time: ClassVar[float] = 0.06
    decay: ClassVar[float] = 0.3
    # a circular membrane's first overtone sits at roughly 1.59x the fundamental
    overtone_ratio: ClassVar[float] = 1.59
    overtone_level: ClassVar[float] = 0.5
    overtone_decay: ClassVar[float] = 0.12
    click_level: ClassVar[float] = 0.6
    click_ratio: ClassVar[float] = 6.0
    click_resonance: ClassVar[float] = 2.0
    click_duration: ClassVar[float] = 0.01
    decay_curve: ClassVar[float] = 3
    bend_curve: ClassVar[float] = 4

    # the graph, assigned by build(); finish() retains every one of them
    tuning: Sig
    root_freq: PyoObject
    overtone_pitch: PyoObject
    overtone: Sine
    overtone_env: TrigEnv
    overtone_signal: PyoObject
    click_env: TrigEnv
    click_burst: PyoObject
    click_freq: PyoObject
    click_signal: Biquad
    partials: PyoObject
    voice_signal: PyoObject

    # this bar's chord source, frozen at build time - read by `next_step`
    harmony: Harmony

    @Param(
        0.02,
        0.6,
        0.01,
        0.2,
        "Presence",
        "Sets how loud and upfront the tom fill sits in the mix.",
    )
    def level(self, value: float) -> None:
        self.body_env.mul = value
        self.overtone_env.mul = value * self.tone * self.overtone_level
        self.click_env.mul = value * self.tone * self.click_level

    # the fill: semitones above the chord root, so the pattern's steps are
    # pitches rather than levels. It walks down the minor pentatonic (fifth,
    # fifth, minor third, root), all tones of the rack's minor-seventh chords
    # (E, E, C, A over Am7)
    phrase_roles = (PhraseRole.FILL,)
    phrase = Phrased.phrase.replace(
        default=Fills.TOM_FILL,
        help_text="Picks the line that is played, as pitches above the current chord; every pitched voice draws "
        "on the same shared lines.",
    )

    tune = Param(
        -12,
        12,
        1,
        0,
        "Pitch",
        "Retunes the whole fill in semitones; lower is a deeper floor tom, higher a tighter rack tom.",
    )

    @Param(
        0.0,
        2.0,
        0.05,
        1.0,
        "Sweep",
        "Depth of the downward pitch bend on each hit; more gives a bigger impact gesture, too much "
        "starts to sound like a zap, none leaves a static pitched ping.",
        sweep=True,
    )
    def sweep(self, value: float) -> None:
        self.bend.mul = self.bend_depth * value

    @Param(
        0.5,
        2.0,
        0.05,
        1.0,
        "Length",
        "Shortens the tom toward a dry, damped hit or lets it ring out with a longer resonant tail.",
        sweep=True,
    )
    def length(self, value: float) -> None:
        self.body_env.dur = self.decay * value
        self.overtone_env.dur = self.overtone_decay * value

    @Param(
        0.0,
        1.0,
        0.05,
        0.35,
        "Brightness",
        "Adds the upper membrane overtone and stick attack; low is a round, deep tom, high a brighter, "
        "more articulate one.",
        sweep=True,
    )
    def tone(self, value: float) -> None:
        self.overtone_env.mul = self.level * value * self.overtone_level
        self.click_env.mul = self.level * value * self.click_level

    rate = rate_param(
        base_division,
        "Halves or doubles the fill speed for each step away from its 16th-note grid.",
    )

    def build(self, context: BuildContext) -> Patch:
        self._reset()
        self.harmony = context.harmony

        self.tuning = Sig(Note.semitone_ratio(self.tune))
        self.root_freq = self.tuning * self.body_freq

        self.pitched_body(
            self.root_freq,
            bend_depth=1.0,
            bend_time=self.bend_time,
            bend_curve=self.bend_curve,
            decay=self.decay,
            decay_curve=self.decay_curve,
        )

        self.overtone_pitch = self.pitch * self.overtone_ratio
        self.overtone = Sine(freq=self.overtone_pitch)
        self.phased.append(self.overtone)
        self.overtone_env = self.envelope(
            DROP, dur=self.overtone_decay, exp=self.decay_curve
        )
        self.overtone_signal = self.overtone * self.overtone_env

        self.click_env, self.click_burst = self.noise_burst(
            dur=self.click_duration, exp=self.bend_curve
        )
        self.click_freq = self.root_freq * self.click_ratio
        self.click_signal = Biquad(
            self.click_burst, freq=self.click_freq, q=self.click_resonance, type=2
        )

        self.partials = self.body_signal + self.overtone_signal
        self.voice_signal = self.partials + self.click_signal

        self.schedule_pattern(context)
        return self.finish(self.voice_signal)

    def next_step(self) -> None:
        step = self._step()
        if step.hit:
            chord_ratio = (
                self.harmony.chord_freq(self.body_freq, self._clock.bar_index)
                / self.body_freq
            )
            self.tuning.value = chord_ratio * Note.semitone_ratio(self.tune + step.value)
            self.strike()
