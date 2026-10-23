# uv run flet run src/flet/patch/app.py -- pyoscillate.patches.tonal.strings.bowed
"""Bowed solo strings: a continuously driven string, not a struck one.

The same tuned, damped delay line as the plucked strings (`pluck/string.py`),
but fed the whole time the bow is down instead of once. A bow drags the
string along and lets it snap back, which makes it move in a sawtooth, so the
bow is a band-limited sawtooth at the note's pitch plus a little noise for
the rosin's rasp, rolled off by Brightness (bow pressure) and shaped by an
attack/release envelope (the bow starting and leaving the string). The string
loop resonates around it: its low-pass keeps the highs from piling up, and
Resonance sets how much the string rings on its own and how fast the note
swells.

A resonant loop gains a steady tone by about its pitch times its ring time,
so the bow's level is scaled by the inverse, keeping every note and every
Resonance at one loudness.

A note is bowed for the rest of its step plus `Legato` of the way to the next
note: at 0 each note stops with its step, at 1 a note holds until the next one
and a change of pitch under a bow already down is a slur, not a new bow. A
vibrato (a slow sine on the pitch) and a glide between notes finish the
voice; what is left is the instrument's body (`Body`).
"""

from __future__ import annotations

from typing import ClassVar

from pyo import PyoObject
from pyo.lib._core import Sig
from pyo.lib.controls import Adsr, SigTo
from pyo.lib.effects import Waveguide
from pyo.lib.filters import ButLP
from pyo.lib.generators import LFO, Noise, Sine

from pyoscillate.clock import NoteDivision
from pyoscillate.harmony import Harmony
from pyoscillate.patches.base import BuildContext, Patch
from pyoscillate.patches.common import Body, ChordRoot, Gate, GatedVoice, Phrased
from pyoscillate.patches.params import Param, rate_param
from pyoscillate.theory.phrase import Hooks, PhraseRole
from pyoscillate.theory.pitch import Note


class Bowed(Body, Gate, ChordRoot, Phrased, GatedVoice):
    """Bowed string voice. Style subclasses set the register, the bow's attack,
    release, vibrato and rasp, and the body."""

    volume = Patch.volume.replace(default=0.6)
    phrase_roles = (PhraseRole.HOOK, PhraseRole.LEAD)
    phrase = Phrased.phrase.replace(
        default=Hooks.SPARSE_HOOK,
        help_text="Picks which notes are bowed and when, from a sparse figure to a flowing line; every voice draws on the same shared patterns.",
    )
    base_division: ClassVar[NoteDivision] = NoteDivision.EIGHTH
    # the sawtooth's sharpness (0 to 1): the full edge, which Brightness rolls off
    bow_sharpness: ClassVar[float] = 1.0
    # the string loop's gain for a steady tone, as a multiple of pitch x ring
    # time: measured on the pyo `Waveguide` with a sawtooth input
    loop_gain: ClassVar[float] = 0.12
    # the steady level the loop is scaled to (rms)
    bow_level: ClassVar[float] = 0.015
    # how much of the bow itself is heard beside the string: the loop's
    # low-pass rolls the highs off, and the bow carries them back
    bow_direct: ClassVar[float] = 0.08
    # seconds the bow's level takes to follow a new pitch or Resonance
    level_glide: ClassVar[float] = 0.02
    # seconds the vibrato takes to fade to a new depth, and its speed (Hz)
    vibrato_glide: ClassVar[float] = 0.1
    vibrato_rate: ClassVar[float] = 5.5
    # the loudest the rosin's noise gets against the sawtooth
    rosin_max: ClassVar[float] = 0.3
    # the envelope's decay and sustain: the bow settles straight to full
    bow_decay: ClassVar[float] = 0.05
    # below the lowest note the Register can reach: the delay line is sized for it
    lowest_freq: ClassVar[float] = 30

    pitch: SigTo
    vibrato_depth: SigTo
    vibrato_lfo: Sine
    vibrato_ratio: PyoObject
    bowed_pitch: PyoObject
    bow_saw: LFO
    rosin: SigTo
    bow_noise: Noise
    bow_mix: PyoObject
    bow_tone: ButLP
    bow_env: Adsr
    level: SigTo
    bow: PyoObject
    driven: PyoObject
    string: Waveguide
    bow_direct_signal: PyoObject
    bowed: PyoObject
    harmony: Harmony
    # sequence state, kept on self like any step counter: the pitch the bow is
    # on, and the clock tick after which it lifts (None while it is up)
    _note: float
    _release_tick: int | None

    root_freq = ChordRoot.root_freq.replace(
        help_text="Moves the whole line up or down; low is a deep, dark register, high is a thin, singing one.",
    )

    @Param(
        500,
        12000,
        0.02,
        5000,
        "Brightness",
        "How hard the bow presses; low is a soft, veiled, flautando tone, high is a pressed, edgy, rasping one.",
        scale="cutoff",
        sweep=True,
    )
    def brightness(self, value: float) -> None:
        self.bow_tone.freq = value

    @Param(
        0.01,
        1.5,
        0.01,
        0.08,
        "Attack",
        "How gradually the bow takes hold of the string; short is a crisp, accented start, long is a slow swell.",
        sweep=True,
    )
    def attack(self, value: float) -> None:
        self.bow_env.attack = value

    @Param(
        0.05,
        2.0,
        0.01,
        0.3,
        "Release",
        "How long the sound lingers once the bow lifts; short stops cleanly, long lets the note fade into the next.",
        sweep=True,
        advanced=True,
    )
    def release(self, value: float) -> None:
        self.bow_env.release = value

    @Param(
        0.1,
        1.5,
        0.05,
        0.3,
        "Resonance",
        "How much the string rings on its own; low is a dry, close, quickly-speaking tone, high is a singing, resonant string that swells in and lingers.",
        sweep=True,
    )
    def resonance(self, value: float) -> None:
        self.string.dur = value
        self.apply_level()

    @Param(
        0,
        100,
        1,
        25,
        "Vibrato",
        "How far the pitch rocks around the note, in cents; none is a steady, pure tone, a little is a warm, human voice, a lot is a wide, operatic wobble.",
        sweep=True,
    )
    def vibrato(self, value: float) -> None:
        self.vibrato_depth.value = Note.semitone_ratio(value / 100) - 1

    @Param(
        0,
        1,
        0.05,
        0.2,
        "Rosin",
        "How much bow noise rides on the tone; low is smooth and pure, high is a raspy, scratchy, gritty bow.",
        sweep=True,
    )
    def rosin_amount(self, value: float) -> None:
        self.rosin.value = value * self.rosin_max

    @Param(
        0,
        0.3,
        0.01,
        0,
        "Glide",
        "Slides each note into the next over this many seconds; none is stepped and exact, long is a smeared, sliding line.",
        sweep=True,
        advanced=True,
    )
    def glide(self, value: float) -> None:
        self.pitch.time = value

    legato = Param(
        0,
        1,
        0.05,
        0.8,
        "Legato",
        "How long each note is held toward the next; at 0 every note stops with its step, at 1 it holds right up to the next note and the change is a slur.",
        sweep=True,
    )

    rate = rate_param(
        base_division,
        "Halves or doubles the speed of the line for each step away from its eighth-note grid.",
    )

    def apply_level(self) -> None:
        """Scale the bow so the string sounds at `bow_level` whatever the pitch
        and Resonance (see the module docstring)."""
        loop = self.loop_gain * self._note * self.resonance
        self.level.value = self.bow_level / loop

    def voice_stage(self, string: PyoObject) -> PyoObject:
        """What follows the string: the body, by default. A style with more
        (a drone string) overrides it."""
        return self.add_body(string)

    def on_note(self, note: float, bar_index: int) -> None:
        """A note was just handed to the bow: a style with something else to
        retune per note does it here."""

    def build(self, context: BuildContext) -> Patch:
        self._reset()
        self.harmony = context.harmony
        self._note = self.note_frequency(0, context.clock.bar_index)
        self._release_tick = None

        self.pitch = SigTo(value=self._note, time=self.glide, init=self._note)
        self.vibrato_depth = SigTo(value=0, time=self.vibrato_glide)
        self.vibrato_lfo = Sine(freq=self.vibrato_rate, mul=self.vibrato_depth)
        self.vibrato_ratio = self.vibrato_lfo + 1
        self.bowed_pitch = self.pitch * self.vibrato_ratio

        # the bow: a sawtooth at the pitch plus noise, rolled off, then opened
        # and closed by the envelope
        self.bow_saw = LFO(freq=self.bowed_pitch, sharp=self.bow_sharpness, type=0)
        self.rosin = SigTo(value=0, time=self.level_glide)
        self.bow_noise = Noise(mul=self.rosin)
        self.bow_mix = self.bow_saw + self.bow_noise
        self.bow_tone = ButLP(self.bow_mix, freq=self.brightness)
        self.bow_env = Adsr(
            attack=self.attack,
            decay=self.bow_decay,
            sustain=1.0,
            release=self.release,
        )
        self.level = SigTo(value=1.0, time=self.level_glide)
        self.bow = self.bow_tone * self.bow_env
        self.driven = self.bow * self.level

        self.string = Waveguide(
            self.driven,
            freq=self.bowed_pitch,
            dur=self.resonance,
            minfreq=self.lowest_freq,
        )
        self.bow_direct_signal = self.bow * self.bow_direct
        self.bowed = self.string + self.bow_direct_signal
        staged = self.voice_stage(self.bowed)

        self.schedule_pattern(context)
        return self.finish(self.add_gate(staged, context))

    def steps_to_next_hit(self, index: int) -> int:
        """Steps from step `index` to the phrase's next note, wrapping the cycle."""
        phrase = self.selected_phrase
        hits = sorted(step.at for step in phrase.steps)
        later = [at - index for at in hits if at > index]
        return later[0] if later else hits[0] + phrase.cycle - index

    def next_step(self) -> None:
        step = self._step()
        tick = self._clock.tick
        slurred = step.hit and self.legato >= 1
        lifting = self._release_tick is not None and tick >= self._release_tick
        if lifting and not slurred:
            self.bow_env.stop()
            self._release_tick = None
        if not step.hit:
            return
        bar = self._clock.bar_index
        self._note = self.note_frequency(int(step.value), bar)
        self.pitch.value = self._note
        self.apply_level()
        self.on_note(self._note, bar)
        # held for its own step, and `legato` of the way on to the next note
        gap = self.steps_to_next_hit(step.index)
        held = 1 + self.legato * (gap - 1)
        if self._release_tick is None:
            self.bow_env.play()
        self._release_tick = tick + round(self._division.steps * held)


class Violin(Bowed):
    """Solo violin: a quick, bright bow with a warm vibrato over a small,
    high body."""

    title = "Violin"
    summary = "Bright, singing solo violin line over the rack's chord tones."

    body_modes = (Note.D4, Note.A4, Note.D5)
    body_q = (6, 8, 8)

    root_freq = Bowed.root_freq.replace(
        minimum=Note.G3, maximum=Note.A5, default=Note.A4
    )
    attack = Bowed.attack.replace(default=0.03)
    release = Bowed.release.replace(default=0.35)
    vibrato = Bowed.vibrato.replace(default=35)
    brightness = Bowed.brightness.replace(default=6000)
    resonance = Bowed.resonance.replace(default=0.3)


class Viola(Bowed):
    """Solo viola: a slower, darker bow than a violin, a little reedy, with a
    wide, slow vibrato."""

    title = "Viola"
    summary = "Dark, reedy solo viola line over the rack's chord tones."

    vibrato_rate = 4.5
    body_modes = (Note.G3, Note.D4, Note.A4)
    body_q = (6, 7, 8)

    root_freq = Bowed.root_freq.replace(
        minimum=Note.C3, maximum=Note.A4, default=Note.A3
    )
    # the recipe's 0.8 s swell is a held pad; a phrased line needs a quicker one
    attack = Bowed.attack.replace(default=0.12)
    release = Bowed.release.replace(default=0.5)
    vibrato = Bowed.vibrato.replace(default=30)
    brightness = Bowed.brightness.replace(default=4000)
    resonance = Bowed.resonance.replace(default=0.35)
    rosin_amount = Bowed.rosin_amount.replace(default=0.25)


class Cello(Bowed):
    """Solo cello: a deep, warm bow with a steady vibrato over a large body."""

    title = "Cello"
    summary = "Deep, warm solo cello line under the rack's chord tones."

    body_modes = (Note.G2, Note.D3, Note.A3)
    body_q = (6, 7, 8)

    root_freq = Bowed.root_freq.replace(
        minimum=Note.C2, maximum=Note.E4, default=Note.A2
    )
    attack = Bowed.attack.replace(default=0.06)
    release = Bowed.release.replace(default=0.3)
    vibrato = Bowed.vibrato.replace(default=25)
    brightness = Bowed.brightness.replace(default=3500)
    resonance = Bowed.resonance.replace(default=0.45)
    rate = Bowed.rate.replace(default=-1)


class DoubleBass(Bowed):
    """Bowed double bass: a heavy string that speaks slowly and swells into a
    deep, dark, near-pure note."""

    title = "Double Bass"
    summary = "Deep, slow-speaking bowed double bass under the rack's chords."

    vibrato_rate = 5.0
    body_modes = (Note.B1, Note.Fs2, Note.B2)
    body_q = (6, 6, 7)

    root_freq = Bowed.root_freq.replace(
        minimum=Note.E1, maximum=Note.E3, default=Note.A1
    )
    attack = Bowed.attack.replace(default=0.35)
    release = Bowed.release.replace(default=0.2)
    vibrato = Bowed.vibrato.replace(default=10)
    brightness = Bowed.brightness.replace(default=2500)
    resonance = Bowed.resonance.replace(default=0.5)
    rosin_amount = Bowed.rosin_amount.replace(default=0.3)
    rate = Bowed.rate.replace(default=-1)


class HurdyGurdy(Bowed):
    """Hurdy-gurdy: a rosined wheel bows the strings, so the note starts at
    once, never stops and leaves slowly, with a drone string sounding the
    key's tonic underneath."""

    title = "Hurdy Gurdy"
    summary = "Droning, wheel-bowed hurdy-gurdy line over the rack's chord tones."

    # seconds the drone string takes to fade, and the register it sits in
    drone_sustain: ClassVar[float] = 1.0
    drone_register: ClassVar[float] = Note.D3
    vibrato_rate = 0.5
    body_modes = (Note.G2, Note.D3, Note.A3)
    body_q = (5, 6, 6)

    drone_saw: LFO
    drone_pitch: Sig
    drone_driven: PyoObject
    drone: Waveguide
    _drone_freq: float

    root_freq = Bowed.root_freq.replace(
        minimum=Note.D3, maximum=Note.A4, default=Note.A3
    )
    # a wheel bows with no ramp, and the glide of a gurdy's keys is short
    attack = Bowed.attack.replace(default=0.01)
    release = Bowed.release.replace(default=0.85)
    vibrato = Bowed.vibrato.replace(default=0)
    glide = Bowed.glide.replace(default=0.04)
    legato = Bowed.legato.replace(default=1.0)
    brightness = Bowed.brightness.replace(default=4500)
    rosin_amount = Bowed.rosin_amount.replace(default=0.35)

    @Param(
        0,
        1,
        0.05,
        0.6,
        "Drone",
        "How loud the drone string is under the melody; none is a bare melody, high is a thick, bagpipe-like bed on the key's tonic.",
        sweep=True,
    )
    def drone_level(self, value: float) -> None:
        self.apply_drone()

    def apply_drone(self) -> None:
        """Scale the drone's wheel to the Drone level, as `apply_level` does
        for the melody string."""
        loop = self.loop_gain * self._drone_freq * self.drone_sustain
        self.drone_saw.mul = self.drone_level * self.bow_level / loop

    def voice_stage(self, string: PyoObject) -> PyoObject:
        self._drone_freq = self.harmony.key_freq(self.drone_register)
        self.drone_pitch = Sig(self._drone_freq)
        self.drone_saw = LFO(freq=self.drone_pitch, sharp=self.bow_sharpness, type=0)
        # the same wheel bows the drone, so it opens and closes with the notes
        self.drone_driven = self.drone_saw * self.bow_env
        self.drone = Waveguide(
            self.drone_driven,
            freq=self.drone_pitch,
            dur=self.drone_sustain,
            minfreq=self.lowest_freq,
        )
        return self.add_body(string + self.drone)

    def on_note(self, note: float, bar_index: int) -> None:
        # the tonic follows the rack's key
        self._drone_freq = self.harmony.key_freq(self.drone_register)
        self.drone_pitch.value = self._drone_freq
        self.apply_drone()


class Riti(Bowed):
    """Riti: a one-string fiddle bowed with a rough horsehair bow over a small
    skin-covered gourd, nasal and rasping, with a quick vibrato and sliding
    between notes."""

    title = "Riti"
    summary = "Nasal, rasping one-string riti fiddle over the rack's chord tones."

    vibrato_rate = 6.0
    # a small skin-covered gourd: a few tight, high resonances (the nasal edge)
    body_modes = (Note.D5, Note.A5)
    body_q = (3, 4)

    root_freq = Bowed.root_freq.replace(
        minimum=Note.E3, maximum=Note.E4, default=Note.A3
    )
    attack = Bowed.attack.replace(default=0.02)
    release = Bowed.release.replace(default=0.15)
    vibrato = Bowed.vibrato.replace(default=12)
    glide = Bowed.glide.replace(default=0.02)
    brightness = Bowed.brightness.replace(default=7000)
    rosin_amount = Bowed.rosin_amount.replace(default=0.7)
    resonance = Bowed.resonance.replace(default=0.25)
