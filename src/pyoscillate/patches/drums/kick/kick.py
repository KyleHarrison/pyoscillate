# uv run flet run src/flet/patch/app.py -- pyoscillate.patches.drums.kick.kick
#   style: round | punch | soft | lofi
"""Four-on-the-floor kick voices, plus a swung, softened lofi voice.

Each hit restarts a sine body at a zero crossing, so the impact starts at full
amplitude without a phase click. An exponential pitch drop gives the attack
its gesture, an exponential amplitude decay sets the body length, a short
noise burst clarifies the transient, and gentle saturation adds density.

`round`/`punch`/`soft` play the quarter-note pulse (the classic
four-on-the-floor); `lofi` starts on a swung 32nd-note rhythm instead, so it
can place hits off the straight 16th grid for an MPC-style swing pocket and
quiet ghost hits. Every kick can play any rhythm from its Pattern dropdown.
"""

from typing import ClassVar

from pyo import PyoObject
from pyo.lib.effects import Disto
from pyo.lib.filters import Biquad
from pyo.lib.generators import Sine
from pyo.lib.triggers import TrigEnv

from pyoscillate.clock import NoteDivision
from pyoscillate.patches.base import BuildContext, Patch
from pyoscillate.patches.drums.base import DROP, RhythmDrum
from pyoscillate.patches.params import Param, rate_param
from pyoscillate.theory.phrase import PhraseRole, Rhythms


class Kick(RhythmDrum):
    """Four-on-the-floor kick: pitch-enveloped sine body, noise-click
    transient, soft saturation. Style variants subclass this and override
    the profile attributes below with fixed data; the graph itself is
    identical across styles."""

    volume = Patch.volume.replace(default=0.8)
    base_division: ClassVar[NoteDivision] = NoteDivision.QUARTER
    # exponent of the amplitude and pitch decay curves - higher values give the
    # fast-drop, long-tail shape of an analogue drum envelope; the body stays
    # moderate so the kick keeps its weight
    body_curve: ClassVar[float] = 2.5
    pitch_curve: ClassVar[float] = 6
    click_duration: ClassVar[float] = 0.012

    # settled body pitch (Hz), pitch-drop depth (Hz above body), pitch-drop
    # time (s), body decay (s), transient level - overridden per style
    body_freq: ClassVar[float]
    sweep_depth: ClassVar[float]
    sweep_time: ClassVar[float]
    decay: ClassVar[float]
    click_level: ClassVar[float]

    # the kick plays a full-level hit on every beat unless a style picks
    # another rhythm to place hits off the straight grid (swing) and/or vary
    # their level (ghost notes)
    phrase_roles = (PhraseRole.KICK,)
    phrase = RhythmDrum.phrase.replace(default=Rhythms.QUARTER_PULSE)

    # the graph, assigned by build(); finish() retains every one of them
    pitch_env: TrigEnv
    body: Sine
    body_env: TrigEnv
    body_signal: PyoObject
    click_env: TrigEnv
    click_signal: PyoObject
    source: PyoObject
    shaper: Disto

    @Param(
        0.1,
        1.0,
        0.05,
        0.62,
        "Body",
        "Controls the fullness and weight of the kick's low end.",
    )
    def level(self, value: float) -> None:
        self.apply_gains()

    @Param(
        0.0,
        0.8,
        0.05,
        0.12,
        "Grit",
        "Adds soft saturation warmth and edge; higher pushes the kick toward a grittier, more aggressive thump.",
        sweep=True,
    )
    def drive(self, value: float) -> None:
        self.shaper.drive = value

    @Param(
        0.0,
        2.0,
        0.05,
        1.0,
        "Punch",
        "Depth of the downward pitch drop at the start of each hit; more gives a sharper, more pronounced "
        "attack, too much starts to sound like a tom or zap, none leaves a pure low thud.",
        sweep=True,
    )
    def punch(self, value: float) -> None:
        self.pitch_env.mul = self.sweep_depth * value

    @Param(
        0.5,
        2.0,
        0.05,
        1.0,
        "Length",
        "Stretches or shortens the body; shorter is tight and dry and leaves room for the bass, longer is "
        "boomier and more 808-like but can mask the bassline.",
        sweep=True,
    )
    def length(self, value: float) -> None:
        self.body_env.dur = self.decay * value

    @Param(
        0.0,
        2.0,
        0.05,
        1.0,
        "Click",
        "Level of the short noise transient on the attack; more adds snap and definition, less sounds "
        "rounder and softer.",
        sweep=True,
    )
    def click(self, value: float) -> None:
        self.apply_gains()

    rate = rate_param(
        base_division,
        "Halves or doubles the kick pattern speed for each step away from the four-on-the-floor default.",
    )

    def voice_output(self) -> PyoObject:
        """Hook: the final output node after `self.shaper`. The default is a
        no-op; a style overrides this to add its own post-processing (e.g. a
        closed low-pass for a softer voice), assigning any node it builds
        onto `self` too."""
        return self.shaper

    def apply_gains(self) -> None:
        """Recombine the current Body/Click levels with this hit's step
        accent (1.0, a no-op, unless `pattern` sets it to something else)."""
        self.body_env.mul = self.level * self.accent
        self.click_env.mul = self.click_level * self.click * self.accent

    def build(self, context: BuildContext) -> Patch:
        """Wire the graph; `finish()` applies every parameter's control."""
        self._reset()

        self.pitch_env = self.envelope(
            DROP, dur=self.sweep_time, add=self.body_freq, exp=self.pitch_curve
        )
        self.body = Sine(freq=self.pitch_env)
        self.phased.append(self.body)
        self.body_env = self.envelope(DROP, dur=self.decay, exp=self.body_curve)
        self.body_signal = self.body * self.body_env

        self.click_env, self.click_signal = self.noise_burst(
            dur=self.click_duration, exp=self.pitch_curve
        )

        self.source = self.body_signal + self.click_signal
        self.shaper = Disto(self.source, slope=0.85)

        self.schedule_pattern(context)
        return self.finish(self.voice_output())


class KickRound(Kick):
    """Deep, rounded low-end thump."""

    summary = "Deep, rounded low-end thump anchoring the groove."
    body_freq, sweep_depth, sweep_time, decay, click_level = (
        50.0,
        80.0,
        0.05,
        0.27,
        0.12,
    )


class KickPunch(Kick):
    """Tighter, punchier kick with more transient snap."""

    body_freq, sweep_depth, sweep_time, decay, click_level = (
        54.0,
        140.0,
        0.035,
        0.2,
        0.28,
    )


class KickSoft(Kick):
    """Soft, cushioned kick that sits back in the mix."""

    body_freq, sweep_depth, sweep_time, decay, click_level = (
        46.0,
        50.0,
        0.07,
        0.37,
        0.05,
    )


class KickLofi(Kick):
    """Soft, closed-low-pass boom-bap kick with an MPC-style swing pocket and
    a ghost hit, sitting behind an 80 BPM beat rather than on a
    four-on-the-floor grid."""

    summary = "Soft, filtered boom-bap kick with an MPC swing pocket and a ghost hit."
    body_freq, sweep_depth, sweep_time, decay, click_level = (
        48.0,
        55.0,
        0.06,
        0.32,
        0.04,
    )
    base_division: ClassVar[NoteDivision] = NoteDivision.THIRTYSECOND
    phrase = Kick.phrase.replace(default=Rhythms.KICK_LOFI)
    # closes the kick down from the shaper's grittier top end into a muffled,
    # cushioned thump
    lowpass_cutoff: ClassVar[float] = 1100.0
    drive = Kick.drive.replace(
        default=0.2,
        help_text="Adds soft saturation warmth; kept light here so the closed low-pass, not the grit, "
        "defines this kick's soft character.",
    )
    rate = rate_param(
        NoteDivision.THIRTYSECOND,
        "Halves or doubles the boom-bap kick pattern speed for each step away from its swung 32nd-note grid.",
    )

    lowpassed: Biquad

    def voice_output(self) -> PyoObject:
        self.lowpassed = Biquad(self.shaper, freq=self.lowpass_cutoff, q=0.7, type=0)
        return self.lowpassed
