# uv run flet run src/flet/patch/app.py -- pyoscillate.patches.drums.snare.snare
"""Tone-and-rattle snare voice, plus a swung, softened lofi voice.

Two layers share one trigger: a short sine body a little above the kick's
register, with a modest downward pitch bend, and a louder high-passed noise
rattle whose exponential tail runs from a dry crack to a small-room wash. It
sits on the backbeat under the clap, with a ghost note that swings into the
next bar.

The default voice's `pattern` reads its accents off a 16-step bar
(`pattern_cycle` = 16); `SnareLofi` instead reads a 32-step bar (32nd-note
resolution) so its backbeat can swing behind the straight grid and its ghost
notes can sit at 32nd-note positions a plain 16-step pattern can't express -
`step_pattern()` already supports any cycle length, so this is the same
mechanism at a finer grid, not a new one.
"""

from collections.abc import Callable
from typing import ClassVar

from pyo import PyoObject
from pyo.lib._core import Sig
from pyo.lib.effects import Disto
from pyo.lib.filters import Biquad
from pyo.lib.generators import Noise, Sine
from pyo.lib.triggers import TrigEnv

from pyoscillate.clock import NoteDivision
from pyoscillate.patches.base import BuildContext, Patch
from pyoscillate.patches.common import Step
from pyoscillate.patches.drums.base import DrumVoice, semitone_ratio
from pyoscillate.patches.params import Param, rate_param
from pyoscillate.theory import notes

# full-to-zero break-points shared by every envelope; `exp` sets the curve
DROP = [(0, 1), (8191, 0)]


class Snare(DrumVoice):
    """Tone-plus-rattle snare on the backbeat with a ghost note."""

    summary = "Tone-and-rattle backbeat snare with a swung ghost note, layered under the clap."
    volume = Patch.volume.replace(default=0.3)
    base_division: ClassVar[NoteDivision] = NoteDivision.SIXTEENTH
    decay_curve: ClassVar[float] = 3
    bend_curve: ClassVar[float] = 6

    # step in a `pattern_cycle`-step bar -> accent; the quiet final hit is a
    # ghost note
    pattern: ClassVar[dict[int, float]] = {4: 1.0, 12: 1.0, 15: 0.3}
    pattern_cycle: ClassVar[int] = 16
    base_freq: ClassVar[float] = notes.Fs3
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
    bend: TrigEnv
    pitch: PyoObject
    body: Sine
    body_env: TrigEnv
    body_signal: PyoObject
    noise: Noise
    rattle_env: TrigEnv
    rattle_burst: PyoObject
    rattle: Biquad
    source: PyoObject

    # per-hit accent from the step pattern, not a parameter: kept on self so
    # a live level/snap change doesn't lose the current step's accent
    accent: float
    # the step pattern's callable, frozen at build time - fed to
    # `next_step`, which build() can no longer close over now that it's a
    # real method
    _step: Callable[[], Step]

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
        self.tuning.value = semitone_ratio(value)

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
        self.accent = 1.0
        self.tuning = Sig(semitone_ratio(self.tune))
        self.body_freq = self.tuning * self.base_freq

        self.bend = self.envelope(
            DROP, dur=self.bend_time, mul=self.bend_depth, add=1, exp=self.bend_curve
        )
        self.pitch = self.body_freq * self.bend
        self.body = Sine(freq=self.pitch)
        self.body_env = self.envelope(DROP, dur=self.body_decay, exp=self.decay_curve)
        self.body_signal = self.body * self.body_env

        self.noise = Noise()
        self.rattle_env = self.envelope(DROP, dur=1.0, exp=self.decay_curve)
        self.rattle_burst = self.noise * self.rattle_env
        self.rattle = Biquad(self.rattle_burst, q=self.rattle_resonance, type=1)

        self.source = self.body_signal + self.rattle

        self._step = self.step_pattern(self.pattern_cycle, self.pattern)

        self.schedule(self.base_division, self.rate, context.clock)
        return self.finish(self.voice_output())

    def next_step(self) -> None:
        step = self._step()
        if step.hit:
            self.accent = step.value
            self.apply_gains()
            # restart the body on a zero crossing so the immediate
            # attack doesn't click wherever the oscillator last stopped
            self.body.reset()
            self.trigger.play()


# 32nd-note steps (`pattern_cycle` = 32, 8 per beat) -> accent. The backbeat
# on beats 2 and 4 (straight would be 8 and 24) lands one 32nd late, at 9 and
# 25, for a laid-back, behind-the-beat pocket; a soft pickup ghost sits
# before beat 2 (6) and a quieter one swings into the loop before beat 1 (30)
# - see groove-and-feel.md's "Ghost notes" and "Behind the beat" sections.
SNARE_LOFI_PATTERN = {9: 1.0, 25: 1.0, 6: 0.25, 30: 0.3}


class SnareLofi(Snare):
    """Soft, closed-low-pass boom-bap snare: the backbeat sits behind the
    grid with ghost notes either side, filtered down and lightly saturated
    for an 80 BPM lofi pocket rather than a crisp modern crack."""

    summary = (
        "Soft, filtered boom-bap snare with a behind-the-beat backbeat and ghost notes."
    )
    base_division: ClassVar[NoteDivision] = NoteDivision.THIRTYSECOND
    pattern: ClassVar[dict[int, float]] = SNARE_LOFI_PATTERN
    pattern_cycle: ClassVar[int] = 32
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
