# uv run flet run src/flet/patch/app.py -- pyoscillate.patches.tonal.woodwind.flute.flute
"""Woodwinds: the base every wind patch shares.

A wind is a pipe that a player's breath sets sounding. Whatever the family
(an air jet across an edge, a single reed, a double reed, buzzing lips), the
same things happen around the tone, and `Wind` owns them once, so a style
only builds its *source* (what the breath excites, `make_source()`) and keeps
the rest:

- **The pipe's low-pass** (`Brightness`): the bore and its tone holes let the
  low partials out and keep the high ones in. It is a filter on the whole
  sound, breath included, that *opens as each note swells* (`Opening`: the
  cookbook recipe's filter envelope, which follows the note's own attack, so a
  blown note starts dull and brightens as the air gets going) and that follows
  the pitch (`Pitch tracking`: high notes are brighter, low ones mellower, as
  on any pipe, since the cutoff rides with the note instead of staying put).
- **Breath** (inherited from `Breathed`): noise let in beside the tone, rung by
  the pipe at the note's own pitch (`Air focus` is how sharply), so the hiss is
  part of the note rather than a layer on top.
- **Tonguing** (`Tongue`, `Tongue length`): the consonant at the start of a
  note, a short burst of noise around the pitch each time the note is struck
  afresh. A slurred note has none, because the tongue never touched the reed
  or the air: the `Held` base tells a slur from a new note (`on_attack()`).
- **Breath pulse** (`Tremolo`, `Tremolo speed`): the level swells and fades with
  the player's air, growing in after the note starts with the vibrato.
- **The scoop** (`Bend`, from `PitchBend`): a note starts slightly off pitch
  and settles, as breath pressure does, on every note struck afresh.

A line voice: one note at a time from the rack's chord tones, held by `Held`
(attack, release, vibrato, glide, legato, phrase), with `Breathed`'s drift and
room. The pitch the source plays is `self.held_pitch`.
"""

from __future__ import annotations

from typing import ClassVar

from pyo import PyoObject
from pyo.lib._core import Mix, Pow
from pyo.lib.controls import Adsr, SigTo
from pyo.lib.dynamics import Clip
from pyo.lib.filters import ButLP, Reson
from pyo.lib.generators import Noise, Sine

from pyoscillate.patches.common import Breathed, PitchBend
from pyoscillate.patches.params import Param
from pyoscillate.theory.phrase import Leads, PhraseRole
from pyoscillate.theory.pitch import Note


class Wind(PitchBend, Breathed):
    """A blown pipe. A style builds the `source` (`make_source()`) and gives
    every shared control its own starting value; the pipe, breath, tongue and
    breath pulse are built here."""

    # the source's level (peak), which a style sets so its note sits at one
    # loudness whatever its overtones
    tone_level: ClassVar[float] = 0.08
    # where the breath rings, as a multiple of the note's pitch, and the level
    # of the resonated breath against the tone at full Breath; the resonator
    # loses level as it sharpens, so the trim is held at `air_reference`'s Q
    # and scaled by Air focus to the power `air_makeup`
    air_ratio: ClassVar[float] = 1.0
    air_trim: ClassVar[float] = 1.8
    air_reference: ClassVar[float] = 20.0
    air_makeup: ClassVar[float] = 0.4
    # the tongue's burst: where it rings (a multiple of the pitch), how sharply,
    # its level at full Tongue against the tone, and the attack and release (s)
    # around the Tongue length's decay
    tongue_ratio: ClassVar[float] = 2.0
    tongue_q: ClassVar[float] = 1.5
    tongue_boost: ClassVar[float] = 6.0
    tongue_attack: ClassVar[float] = 0.004
    tongue_release: ClassVar[float] = 0.02
    # the pitch at which Pitch tracking leaves the cutoff where Brightness put
    # it, and the range the pipe's cutoff is held inside (Hz)
    track_reference: ClassVar[float] = Note.A4
    bore_floor: ClassVar[float] = 80.0
    bore_ceiling: ClassVar[float] = 18000.0

    air_pitch: PyoObject
    air: Reson
    air_voiced: PyoObject
    tract_sum: PyoObject
    tract_bank: Mix
    bright: SigTo
    opening_amount: SigTo
    tracking_amount: SigTo
    closed_gap: PyoObject
    opening_depth: PyoObject
    opening_factor: PyoObject
    track_base: PyoObject
    track_factor: Pow
    bore_raw: PyoObject
    bore_freq: Clip
    bore: ButLP
    tongue_noise: Noise
    tongue_pitch: PyoObject
    tongue_band: Reson
    tongue_env: Adsr
    tongue_level: SigTo
    tongue_swell: PyoObject
    tongue_amp: PyoObject
    tongue_hit: PyoObject
    tongue_mix: Mix
    tremolo_depth: SigTo
    tremolo_rate: SigTo
    tremolo_lfo: Sine
    tremolo_swing: PyoObject
    tremolo_gain: PyoObject
    articulated: PyoObject
    breathed: PyoObject
    bent_pitch: PyoObject

    phrase_roles = (PhraseRole.HOOK, PhraseRole.LEAD)
    phrase = Breathed.phrase.replace(
        default=Leads.WIND_DRIFT,
        help_text="Picks which notes are blown and when, from long, floating notes to a flowing line; "
        "every voice draws on the same shared patterns.",
    )
    root_freq = Breathed.root_freq.replace(
        help_text="Moves the whole line up or down; low is a dark, hollow register, high is a bright, piping one.",
    )
    breath = Breathed.breath.replace(
        default=0.25,
        help_text="How much air hisses around the note; none is a clean, pure tone, a little is a soft, breathy one, a lot is a windy, effortful blow.",
    )
    unsteadiness = Breathed.unsteadiness.replace(
        default=0.15,
        help_text="How much the pitch wanders by itself; none is a machine-exact note, a little is a living player, a lot is a tired, unsure one.",
    )
    bend = PitchBend.bend.replace(
        minimum=-3,
        maximum=3,
        step=0.05,
        default=0,
        help_text="Scoops each note into its pitch from this many semitones away; negative swells up from below, positive falls from above, zero is a clean, centred start.",
    )
    reverb_size = Breathed.reverb_size.replace(default=0.5)
    reverb_bal = Breathed.reverb_bal.replace(default=0.25)

    brightness = Param(
        500,
        12000,
        0.02,
        4500,
        "Brightness",
        "How much of the top end gets out of the pipe; low is a soft, covered, hooty tone, high is a bright, open, reedy one.",
        scale="cutoff",
        sweep=True,
    )
    opening = Param(
        0,
        0.95,
        0.05,
        0.5,
        "Opening",
        "How much the tone opens up as each note swells in; none is the same colour from the first instant, a lot starts dull and muffled and brightens into the note.",
        sweep=True,
    )
    tracking = Param(
        0,
        1,
        0.05,
        0.5,
        "Pitch tracking",
        "How much the tone brightens as the note goes up; none keeps one colour at every pitch, a lot makes low notes mellow and high notes shine.",
        sweep=True,
    )
    tongue = Param(
        0,
        1,
        0.05,
        0.3,
        "Tongue",
        "The consonant at the start of each note; none is a smooth, slurred entry, a lot is a clear, tongued 'tu' on every new note. A note slurred into the last has none.",
        sweep=True,
    )
    tremolo = Param(
        0,
        0.6,
        0.02,
        0.1,
        "Tremolo",
        "How much the level pulses with the player's breath; none is a steady stream of air, a little is a living, breathing note, a lot is a throbbing, shaky one.",
        sweep=True,
    )
    tremolo_speed = Param(
        2,
        10,
        0.1,
        5.5,
        "Tremolo speed",
        "How fast the breath pulses, in cycles a second; slow is a heaving swell, fast is a nervous flutter.",
        sweep=True,
        advanced=True,
    )

    @Param(
        3,
        80,
        1,
        20,
        "Air focus",
        "How sharply the breath rings at the pitch; low is a diffuse, airy hiss around the note, high is a tight, whistling ring in the pipe.",
        sweep=True,
        advanced=True,
    )
    def air_focus(self, value: float) -> None:
        self.air.q = value
        self.air.mul = self.air_trim * (value / self.air_reference) ** self.air_makeup

    @Param(
        0.005,
        0.15,
        0.005,
        0.03,
        "Tongue length",
        "How long the tongued consonant lasts; short is a crisp, clipped 'tu', long is a soft, breathy 'hu'.",
        sweep=True,
        advanced=True,
    )
    def tongue_length(self, value: float) -> None:
        self.tongue_env.decay = value
        self.tongue_env.dur = self.tongue_attack + value + self.tongue_release

    def modulation(self) -> PyoObject:
        """The vibrato and drift, with the scoop into each note multiplied in."""
        self.bent_pitch = super().modulation() * self.add_bend(self.trigger)
        return self.bent_pitch

    def make_tract(self, source: PyoObject, breath: PyoObject) -> PyoObject:
        """The source plus the breath, rung by the pipe at the note's pitch."""
        self.air_pitch = self.held_pitch * self.air_ratio
        self.air = Reson(
            breath, freq=self.air_pitch, q=self.air_reference, mul=self.air_trim
        )
        self.tract_sum = source + self.air
        self.tract_bank = Mix(self.tract_sum, voices=1)
        return self.tract_bank

    def voice_stage(self, signal: PyoObject) -> PyoObject:
        cls = type(self)
        # the pipe: a low-pass that opens through the note's swell and follows
        # its pitch
        self.bright = self.live(cls.brightness)
        self.opening_amount = self.live(cls.opening)
        self.tracking_amount = self.live(cls.tracking)
        self.closed_gap = 1 - self.note_env
        self.opening_depth = self.opening_amount * self.closed_gap
        self.opening_factor = 1 - self.opening_depth
        self.track_base = self.pitch * (1 / self.track_reference)
        self.track_factor = Pow(self.track_base, self.tracking_amount)
        self.bore_raw = self.bright * self.opening_factor * self.track_factor
        self.bore_freq = Clip(self.bore_raw, min=self.bore_floor, max=self.bore_ceiling)
        self.bore = ButLP(signal, freq=self.bore_freq)

        # the tongue: noise around the pitch, once per freshly struck note,
        # past the pipe so the opening cannot muffle it
        self.tongue_noise = Noise()
        self.tongue_pitch = self.held_pitch * self.tongue_ratio
        self.tongue_band = Reson(
            self.tongue_noise,
            freq=self.tongue_pitch,
            q=self.tongue_q,
            mul=self.tone_level * self.tongue_boost,
        )
        self.tongue_env = Adsr(
            attack=self.tongue_attack,
            decay=0.03,
            sustain=0,
            release=self.tongue_release,
            dur=self.tongue_attack + 0.03 + self.tongue_release,
        )
        self.tongue_level = self.live(cls.tongue)
        self.tongue_swell = self.tongue_env * self.tongue_level
        self.tongue_amp = self.tongue_swell * self.voice_gain
        self.tongue_hit = self.tongue_band * self.tongue_amp
        self.tongue_mix = Mix(self.tongue_hit, voices=1)
        self.articulated = self.bore + self.tongue_mix

        # the breath pulse, grown in with the vibrato
        self.tremolo_depth = self.live(cls.tremolo)
        self.tremolo_rate = self.live(cls.tremolo_speed)
        self.tremolo_lfo = Sine(freq=self.tremolo_rate, mul=self.tremolo_depth)
        self.tremolo_swing = self.tremolo_lfo * self.vibrato_swell
        self.tremolo_gain = self.tremolo_swing + 1
        self.breathed = self.articulated * self.tremolo_gain
        return super().voice_stage(self.breathed)

    def on_attack(self) -> None:
        self.tongue_env.play()
        self.trigger.play()
