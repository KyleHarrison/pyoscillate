# uv run flet run src/flet/patch/app.py -- pyoscillate.patches.drums.snare.snare
"""Tone-and-rattle snare voice, plus a swung, softened lofi voice.

Two layers share one trigger: a short sine body a little above the kick's
register, with a modest downward pitch bend, and a louder high-passed noise
rattle whose exponential tail runs from a dry crack to a small-room wash. It
sits on the backbeat under the clap, with a ghost note that swings into the
next bar.

The default voice starts on the 16-step `Rhythms.BACKBEAT_GHOST`; `SnareLofi`
starts on the 32-step (32nd-note) `Rhythms.SNARE_LOFI`, so its backbeat can
swing behind the straight grid and its ghost notes can sit at positions a
plain 16-step pattern can't express. Either can play any rhythm from its
Pattern dropdown.
"""

from typing import ClassVar

from pyo import PyoObject
from pyo.lib._core import Sig
from pyo.lib.effects import Disto
from pyo.lib.filters import Biquad
from pyo.lib.triggers import TrigEnv

from pyoscillate.clock import NoteDivision
from pyoscillate.patches.base import BuildContext, Patch
from pyoscillate.patches.drums.base import RhythmDrum
from pyoscillate.patches.params import Param, rate_param
from pyoscillate.theory.phrase import Rhythms
from pyoscillate.theory.pitch import Note


class Snare(RhythmDrum):
    """Tone-plus-rattle snare on the backbeat with a ghost note."""

    summary = "Tone-and-rattle backbeat snare with a swung ghost note, layered under the clap."
    volume = Patch.volume.replace(default=0.3)
    base_division: ClassVar[NoteDivision] = NoteDivision.SIXTEENTH
    decay_curve: ClassVar[float] = 3
    bend_curve: ClassVar[float] = 6

    # the backbeat with a quiet final ghost note
    phrase = RhythmDrum.phrase.replace(default=Rhythms.BACKBEAT_GHOST)
    base_freq: ClassVar[float] = Note.Fs3
    # pitch bend at the strike, as a fraction above the body - kept well
    # below a kick's so the snare never turns into a zap or tom
    bend_depth: ClassVar[float] = 0.35
    bend_time: ClassVar[float] = 0.02
    body_decay: ClassVar[float] = 0.09
    # the rattle is the louder layer; the body gives it a centre
    body_level: ClassVar[float] = 0.6
    rattle_resonance: ClassVar[float] = 1.2

    # the graph, assigned by build(); finish() retains every one of them
    tuning: Sig
    body_freq: PyoObject
    rattle_env: TrigEnv
    rattle_burst: PyoObject
    rattle: Biquad
    source: PyoObject

    @Param(
        0.02,
        0.6,
        0.01,
        0.2,
        "Presence",
        "Sets how loud and upfront the snare sits in the mix.",
    )
    def level(self, value: float) -> None:
        self.apply_gains()

    @Param(
        -12,
        12,
        1,
        0,
        "Pitch",
        "Retunes the drum body in semitones; lower is fatter and heavier, higher is tighter and more ringing.",
    )
    def tune(self, value: float) -> None:
        self.tuning.value = Note.semitone_ratio(value)

    @Param(
        0.0,
        2.0,
        0.05,
        1.0,
        "Snap",
        "Amount of noisy wire rattle against the drum body; more is wider and crisper, less leaves a "
        "rounder, more tonal hit.",
        sweep=True,
    )
    def snap(self, value: float) -> None:
        self.apply_gains()

    @Param(
        800,
        6000,
        50,
        2000,
        "Brightness",
        "Moves the rattle from fuller and thicker (lower) to thinner and more sizzling (higher).",
        sweep=True,
    )
    def tone(self, value: float) -> None:
        self.rattle.freq = value

    @Param(
        0.05,
        0.5,
        0.01,
        0.16,
        "Tail",
        "Length of the rattle after the hit; short is a dry crack, long reads like a small room around the snare.",
        sweep=True,
    )
    def decay(self, value: float) -> None:
        self.rattle_env.dur = value

    rate = rate_param(
        base_division,
        "Halves or doubles the snare pattern speed for each step away from its 16th-note grid.",
    )

    def apply_gains(self) -> None:
        """Recombine the current level, snap, and this step's accent into
        the body/rattle envelope levels."""
        gain = self.level * self.accent
        self.body_env.mul = gain * self.body_level
        self.rattle_env.mul = gain * self.snap

    def voice_output(self) -> PyoObject:
        """Hook: the final output node after `self.source`. The default is a
        no-op; a style overrides this to add its own post-processing (e.g. a
        closed low-pass and light saturation for a softer voice), assigning
        any node it builds onto `self` too."""
        return self.source

    def build(self, context: BuildContext) -> Patch:
        self._reset()
        self.tuning = Sig(Note.semitone_ratio(self.tune))
        self.body_freq = self.tuning * self.base_freq

        self.pitched_body(
            self.body_freq,
            bend_depth=self.bend_depth,
            bend_time=self.bend_time,
            bend_curve=self.bend_curve,
            decay=self.body_decay,
            decay_curve=self.decay_curve,
        )

        self.rattle_env, self.rattle_burst = self.noise_burst(
            dur=1.0, exp=self.decay_curve
        )
        self.rattle = Biquad(self.rattle_burst, q=self.rattle_resonance, type=1)

        self.source = self.body_signal + self.rattle

        self.schedule_pattern(context)
        return self.finish(self.voice_output())


class SnareLofi(Snare):
    """Soft, closed-low-pass boom-bap snare: the backbeat sits behind the
    grid with ghost notes either side, filtered down and lightly saturated
    for an 80 BPM lofi pocket rather than a crisp modern crack."""

    summary = (
        "Soft, filtered boom-bap snare with a behind-the-beat backbeat and ghost notes."
    )
    base_division: ClassVar[NoteDivision] = NoteDivision.THIRTYSECOND
    phrase = Snare.phrase.replace(default=Rhythms.SNARE_LOFI)
    # closes the rattle's high-passed edge down into a duller, muffled crack
    lowpass_cutoff: ClassVar[float] = 2600.0
    # light saturation warms the body/rattle mix without turning it harsh
    drive: ClassVar[float] = 0.15
    rate = rate_param(
        NoteDivision.THIRTYSECOND,
        "Halves or doubles the boom-bap snare pattern speed for each step away from its swung 32nd-note "
        "grid.",
    )

    lowpassed: Biquad
    shaper: Disto

    def voice_output(self) -> PyoObject:
        self.lowpassed = Biquad(self.source, freq=self.lowpass_cutoff, q=0.7, type=0)
        self.shaper = Disto(self.lowpassed, drive=self.drive, slope=0.7)
        return self.shaper
