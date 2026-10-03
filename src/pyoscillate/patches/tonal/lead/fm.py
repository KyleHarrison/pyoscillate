# uv run flet run src/flet/patch/app.py -- pyoscillate.patches.tonal.lead.fm
#   style: wind | swirl
"""Windy, psychedelic FM leads.

Two-operator FM (x03/03 `FM`) whose index barks on every note and then
settles onto a steady edge, with a slow index LFO swirling the spectrum
between notes. Three things make it "windy" rather than a plain FM tone: a
band-passed noise layer that tracks the note pitch (breath), a slow
multiplicative pitch drift, and portamento between notes. A dotted-eighth
echo smears each phrase into the next.

- `wind` (`LeadFmWind`): integer ratio 2, so the sidebands fold onto the odd
  harmonics - a hollow, reed-like tone - playing a sparse, floating phrase
  of long notes.
- `swirl` (`LeadFmSwirl`): ratio 3.01. The sidebands land about 1% off the
  harmonics and beat against them, which phases and shimmers the tone
  instead of locking it. Plays a short, syncopated, sliding groove.

Both play a two-bar phrase in semitones above the rack's current chord root,
and `on_evolve` alternates between two phrase variants.
"""

from __future__ import annotations

from typing import ClassVar

from pyo import PyoObject
from pyo.lib.controls import SigTo
from pyo.lib.effects import Delay
from pyo.lib.filters import ButBP, ButHP
from pyo.lib.generators import FM, Noise, Sine
from pyo.lib.tables import CosTable, LinTable
from pyo.lib.triggers import TrigEnv

from pyoscillate.clock import NoteDivision
from pyoscillate.harmony import Harmony
from pyoscillate.patches.base import BuildContext, Patch
from pyoscillate.patches.common import Gate, GatedVoice, Phrased, RootPitch
from pyoscillate.patches.params import Param, rate_param
from pyoscillate.tempo import Tempo
from pyoscillate.theory.phrase import Leads, Phrase, PhraseRole
from pyoscillate.theory.pitch import Note


class LeadFm(Gate, RootPitch, Phrased, GatedVoice):
    """FM lead base: every note barks bright and settles, with breath noise,
    pitch drift, portamento and an echo. Style subclasses supply the
    operator ratio, the swirl and drift speeds and the phrases; the graph is
    identical across styles."""

    volume = Patch.volume.replace(default=0.2)
    base_division: ClassVar[NoteDivision] = NoteDivision.SIXTEENTH

    # the brightness left under the whole note once the bark has settled
    edge: ClassVar[float]
    # the index LFO's period and the pitch drift's period, in bars
    swirl_bars: ClassVar[float]
    drift_bars: ClassVar[float]
    # pitch drift excursion as a fraction of the note's frequency (0.006 is
    # about 10 cents)
    drift_depth: ClassVar[float] = 0.006
    # the breath noise band's centre as a multiple of the note, and its Q
    air_ratio: ClassVar[float] = 2.0
    air_q: ClassVar[float] = 5.0
    air_gain: ClassVar[float] = 2.0
    # fed back into the echo, and the echo delay in 16ths (3 = dotted eighth)
    echo_feedback: ClassVar[float] = 0.45
    echo_sixteenths: ClassVar[float] = 3.0
    # level ceiling for the FM voice (FM keeps a constant amplitude whatever
    # the index, so this and the accent are all the level depends on)
    gain: ClassVar[float] = 0.3
    # under the lowest Register; clears the DC an FM voice carries
    subsonic: ClassVar[float] = 60.0
    # the level of a note that lands on a beat; every other note is full, so
    # the syncopations carry the groove
    beat_accent: ClassVar[float] = 0.75
    # amplitude and index shapes: a quick rise then a held body, and a fast
    # drop to half then a linear fall to nothing
    amp_points: ClassVar[list[tuple[int, float]]] = [
        (0, 0.0),
        (300, 1.0),
        (2400, 0.6),
        (8191, 0.0),
    ]
    index_points: ClassVar[list[tuple[int, float]]] = [
        (0, 1.0),
        (512, 0.5),
        (8191, 0.0),
    ]

    phrase_roles = (PhraseRole.LEAD,)
    phrase = Phrased.phrase.replace(
        default=Leads.LEAD_ARCH,
        help_text="Picks the line that is played, as pitches above the current chord; every pitched voice draws "
        "on the same shared lines.",
    )

    # the lines `on_evolve` rotates through, the first playing
    # first; each style supplies its own
    variants: ClassVar[tuple[Phrase, ...]]

    # the graph, assigned by build(); finish() retains every one of them
    pitch: SigTo
    drift: Sine
    carrier: PyoObject
    index_table: LinTable
    amp_table: CosTable
    bark: TrigEnv
    swirl_lfo: Sine
    index: PyoObject
    amp: TrigEnv
    level: PyoObject
    tone: FM
    noise: Noise
    air_level: SigTo
    air_band: ButBP
    air_gate: PyoObject
    air_mix: PyoObject
    body: PyoObject
    echo: Delay
    mixed: PyoObject
    cleaned: ButHP

    # the rack's harmony, the live tempo and the current note's
    # accent, read by `next_step` and the controls
    harmony: Harmony
    _tempo: Tempo
    _accent: float

    root_freq = RootPitch.root_freq.replace(
        minimum=Note.F3,
        maximum=Note.F5,
        default=Note.F4,
        help_text="Moves the lead up or down; low is a warm, reedy mid voice, high is a thin, whistling line above the mix. Notes always follow the rack's key and chord.",
    )

    @Param(
        1,
        4,
        0.01,
        2,
        "Colour",
        "Which overtones the tone has: a whole number is a locked, hollow reed-like tone, a hair "
        "off one (3.01) phases and shimmers against itself, in between is bell-like and unpitched.",
        sweep=True,
    )
    def ratio(self, value: float) -> None:
        self.tone.ratio = value

    @Param(
        0,
        8,
        0.25,
        3,
        "Bite",
        "How hard each note barks: low is a soft, pure tone, high a bright, buzzing snarl at the "
        "start of every note.",
        sweep=True,
    )
    def bite(self, value: float) -> None:
        self.bark.mul = value * self._accent

    @Param(
        0.02,
        0.5,
        0.01,
        0.15,
        "Settle",
        "How long the bark takes to die down, in seconds: short is a quick pluck on the front of "
        "the note, long a slow, vowel-like close.",
        sweep=True,
    )
    def settle(self, value: float) -> None:
        self.bark.dur = value

    @Param(
        0,
        3,
        0.1,
        0.8,
        "Swirl",
        "Depth of a slow, bar-scale swell in the tone between notes; low holds the colour steady, "
        "high keeps the spectrum phasing and shimmering.",
        sweep=True,
    )
    def swirl(self, value: float) -> None:
        self.swirl_lfo.mul = value
        self.swirl_lfo.add = value

    # follows `self.air_level`, a `live` signal, so no control body: setting
    # `.mul` on the gated product would replace the note envelope with a constant
    breath = Param(
        0,
        1,
        0.05,
        0.3,
        "Breath",
        "Mixes in airy, pitched noise under each note; low is a clean synth tone, high a windy, "
        "whistling breath.",
        sweep=True,
    )

    @Param(
        0,
        0.25,
        0.01,
        0.05,
        "Glide",
        "Slides each note into the next over this many seconds; none is stepped and exact, long "
        "is a smeared, wandering line.",
        sweep=True,
    )
    def glide(self, value: float) -> None:
        self.pitch.time = value

    @Param(
        0.3,
        4,
        0.1,
        1.5,
        "Length",
        "How long each note lasts, in 16ths: short is tight and staccato, long runs one note into "
        "the next.",
        sweep=True,
    )
    def length(self, value: float) -> None:
        self.amp.dur = self._tempo.sixteenth * value

    @Param(
        0,
        0.7,
        0.05,
        0.35,
        "Echo",
        "Level of a dotted-eighth echo that repeats each phrase behind itself; low is dry, high "
        "fills the gaps with a trailing, psychedelic wash.",
        sweep=True,
    )
    def echo_level(self, value: float) -> None:
        self.echo.mul = value

    rate = rate_param(
        base_division,
        "Halves or doubles the phrase speed for each step away from its 16th-note grid.",
    )

    def note_root(self) -> float:
        """The current bar's chord root in the octave nearest `root_freq`."""
        return self.root_at(self._clock.bar_index)

    def build(self, context: BuildContext) -> Patch:
        self._reset()
        self.harmony = context.harmony
        self._tempo = tempo = context.tempo
        self._accent = 1.0

        self.pitch = SigTo(value=self.root_freq, time=self.glide, init=self.root_freq)
        self.drift = self.tempo_sine(
            tempo, lambda t: t.bar * self.drift_bars, mul=self.drift_depth, add=1.0
        )
        self.carrier = self.pitch * self.drift

        self.index_table = LinTable(self.index_points)
        self.amp_table = CosTable(self.amp_points)
        self.bark = TrigEnv(
            self.trigger,
            self.index_table,
            dur=self.settle,
            mul=self.bite,
            add=self.edge,
        )
        self.swirl_lfo = self.tempo_sine(
            tempo, lambda t: t.bar * self.swirl_bars, mul=0, add=0
        )
        self.index = self.bark + self.swirl_lfo
        self.amp = TrigEnv(self.trigger, self.amp_table, dur=1.0)
        self.sync(tempo, lambda t: setattr(self.amp, "dur", t.sixteenth * self.length))
        self.level = self.amp * self.gain
        self.tone = FM(carrier=self.carrier, index=self.index, mul=self.level)

        self.noise = Noise()
        self.air_level = self.live(type(self).breath, time=0.05)
        self.air_band = ButBP(
            self.noise,
            freq=self.carrier * self.air_ratio,
            q=self.air_q,
            mul=self.air_gain,
        )
        self.air_gate = self.air_band * self.amp
        self.air_mix = self.air_gate * self.air_level
        self.body = self.tone + self.air_mix

        self.echo = Delay(
            self.body,
            delay=0.1,
            feedback=self.echo_feedback,
            maxdelay=2.0,
        )
        self.sync(
            tempo,
            lambda t: setattr(self.echo, "delay", t.sixteenth * self.echo_sixteenths),
        )
        self.mixed = self.body + self.echo
        self.cleaned = ButHP(self.mixed, freq=self.subsonic)

        self.schedule_pattern(context)
        return self.finish(self.add_gate(self.cleaned, context))

    def next_step(self) -> None:
        step = self._step()
        if step.hit:
            self._accent = self.beat_accent if step.index % 4 == 0 else 1.0
            self.pitch.value = Note.transpose(self.note_root(), step.value)
            self.bark.mul = self.bite * self._accent
            self.amp.mul = self._accent
            self.trigger.play()

    def on_evolve(self, index: int) -> None:
        """Rotate which of `variants` is playing; called rarely (tens of
        bars) by the rack's `EvolvingGroup`, never by the clock."""
        self.phrase = self.variants[index % len(self.variants)]


class LeadFmWind(LeadFm):
    """Hollow, reed-like FM lead playing a sparse, floating phrase of long
    notes."""

    title = "Lead - FM Wind"
    summary = "Hollow, breathy FM reed drifting through a sparse, floating phrase."
    ratio = LeadFm.ratio.replace(default=2.0)
    edge = 0.6
    swirl_bars = 2.0
    drift_bars = 3.0
    length = LeadFm.length.replace(default=3.0)
    glide = LeadFm.glide.replace(default=0.09)
    breath = LeadFm.breath.replace(default=0.45)
    variants = (Leads.WIND_DRIFT, Leads.WIND_DRIFT_B)
    phrase = LeadFm.phrase.replace(default=Leads.WIND_DRIFT)


class LeadFmSwirl(LeadFm):
    """Phasing, shimmering FM lead playing a short, syncopated, sliding
    groove."""

    title = "Lead - FM Swirl"
    summary = "Phasing FM lead sliding through a syncopated 16th-note groove."
    ratio = LeadFm.ratio.replace(default=3.01)
    edge = 1.0
    swirl_bars = 1.0
    drift_bars = 2.0
    length = LeadFm.length.replace(default=0.9)
    variants = (Leads.SWIRL_GROOVE, Leads.SWIRL_GROOVE_B)
    phrase = LeadFm.phrase.replace(default=Leads.SWIRL_GROOVE)
