# uv run flet run src/flet/patch/app.py -- pyoscillate.patches.drums.kick.kick style=round
#   style: round | punch | soft | lofi
"""Four-on-the-floor kick voices, plus a swung, softened lofi voice.

Each hit restarts a sine body at a zero crossing, so the impact starts at full
amplitude without a phase click. An exponential pitch drop gives the attack
its gesture, an exponential amplitude decay sets the body length, a short
noise burst clarifies the transient, and gentle saturation adds density.

`round`/`punch`/`soft` fire on every `base_division` tick (the classic
four-on-the-floor pulse); `lofi` instead reads a per-step accent pattern off
`step_pattern()` at 32nd-note resolution, so it can place hits off the
straight 16th grid for an MPC-style swing pocket and quiet ghost hits,
without inventing a new timing mechanism.
"""

from typing import ClassVar

from pyo import PyoObject
from pyo.lib.effects import Disto
from pyo.lib.filters import Biquad
from pyo.lib.generators import Noise, Sine
from pyo.lib.triggers import TrigEnv

from pyoscillate.clock import Clock, NoteDivision
from pyoscillate.patches.base import Patch
from pyoscillate.patches.drums.base import DrumVoice
from pyoscillate.patches.params import Param, rate_param
from pyoscillate.tempo import Tempo

# full-to-zero break-points shared by every envelope; `exp` sets the curve
DROP = [(0, 1), (8191, 0)]


class Kick(DrumVoice):
    """Four-on-the-floor kick: pitch-enveloped sine body, noise-click
    transient, soft saturation. Style variants subclass this and override
    the profile attributes below with fixed data; the graph itself is
    identical across styles."""

    volume_default = 0.8
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

    # step in a `pattern_cycle`-step bar -> accent; `None` (the default) skips
    # the pattern entirely and fires every base_division tick instead (plain
    # four-on-the-floor) - a style sets both to place hits off the straight
    # grid (swing) and/or vary their level (ghost notes)
    pattern: ClassVar[dict[int, float] | None] = None
    pattern_cycle: ClassVar[int] = 1

    # the graph, assigned by build(); finish() retains every one of them
    pitch_env: TrigEnv
    body: Sine
    body_env: TrigEnv
    body_signal: PyoObject
    noise: Noise
    click_env: TrigEnv
    click_signal: PyoObject
    source: PyoObject
    shaper: Disto

    # per-hit accent from `pattern`, not a parameter: stays 1.0 (a no-op) for
    # every style that doesn't set `pattern`, and lets a live Body/Click
    # change coexist with a swung style's per-step ghost accents
    accent: float

    @Param(0.1, 1.0, 0.05, 0.62, "Body", "Controls the fullness and weight of the kick's low end.")
    def level(self, value: float) -> None:
        self.apply_gains()

    @Param(
        0.0,
        0.8,
        0.05,
        0.12,
        "Grit",
        "Adds soft saturation warmth and edge; higher pushes the kick toward a grittier, more aggressive thump.",
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

    def build(self, tempo: Tempo, clock: Clock) -> Patch:
        """Wire the graph; `finish()` applies every parameter's control."""
        self._reset()
        self.accent = 1.0

        self.pitch_env = self.envelope(
            DROP, dur=self.sweep_time, add=self.body_freq, exp=self.pitch_curve
        )
        self.body = Sine(freq=self.pitch_env)
        self.body_env = self.envelope(DROP, dur=self.decay, exp=self.body_curve)
        self.body_signal = self.body * self.body_env

        self.noise = Noise()
        self.click_env = self.envelope(DROP, dur=self.click_duration, exp=self.pitch_curve)
        self.click_signal = self.noise * self.click_env

        self.source = self.body_signal + self.click_signal
        self.shaper = Disto(self.source, slope=0.85)

        step = self.step_pattern(self.pattern_cycle, self.pattern) if self.pattern is not None else None

        def strike() -> None:
            if step is not None:
                _, accent = step()
                if accent is None:
                    return
                self.accent = accent
                self.apply_gains()
            # restart the sine at phase zero so the full-level attack starts
            # on a zero crossing instead of wherever the oscillator last
            # stopped
            self.body.reset()
            self.trigger.play()

        self.schedule(self.base_division, self.rate, clock, strike)
        return self.finish(self.voice_output())


class KickRound(Kick):
    """Deep, rounded low-end thump."""

    summary = "Deep, rounded low-end thump anchoring the groove."
    body_freq, sweep_depth, sweep_time, decay, click_level = 50.0, 80.0, 0.05, 0.27, 0.12


class KickPunch(Kick):
    """Tighter, punchier kick with more transient snap."""

    body_freq, sweep_depth, sweep_time, decay, click_level = 54.0, 140.0, 0.035, 0.2, 0.28


class KickSoft(Kick):
    """Soft, cushioned kick that sits back in the mix."""

    body_freq, sweep_depth, sweep_time, decay, click_level = 46.0, 50.0, 0.07, 0.37, 0.05


# 32nd-note steps (`pattern_cycle` = 32, 8 per beat) -> accent. Beat 1's
# downbeat is full; the syncopated "and" of beat 2 lands on step 13 instead
# of the straight 12 - one 32nd late, a 5:3 (~62:38) swing ratio (see
# `.claude/skills/music-theory/references/rhythm-groove/groove-and-feel.md`,
# "Swing ratio") - and a quiet ghost flicks in one 32nd behind beat 4's
# straight "a" (30) at 31, both sitting just behind the grid for the laid-back
# boom-bap pocket.
KICK_LOFI_PATTERN = {0: 1.0, 13: 0.85, 31: 0.3}


class KickLofi(Kick):
    """Soft, closed-low-pass boom-bap kick with an MPC-style swing pocket and
    a ghost hit, sitting behind an 80 BPM beat rather than on a
    four-on-the-floor grid."""

    summary = "Soft, filtered boom-bap kick with an MPC swing pocket and a ghost hit."
    body_freq, sweep_depth, sweep_time, decay, click_level = 48.0, 55.0, 0.06, 0.32, 0.04
    base_division: ClassVar[NoteDivision] = NoteDivision.THIRTYSECOND
    pattern_cycle: ClassVar[int] = 32
    pattern: ClassVar[dict[int, float]] = KICK_LOFI_PATTERN
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
