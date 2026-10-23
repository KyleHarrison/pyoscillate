# uv run flet run src/flet/patch/app.py -- pyoscillate.patches.tonal.pluck.guitar
"""Karplus-Strong plucked string: the base every plucked instrument shares.

Each note is a short burst of low-passed noise sent into a `Waveguide`, a
delay line tuned to the note with a low-pass in its feedback loop. The loop
returns the burst to itself once per period, so it settles into a pitched
tone; and because the low-pass shaves a little off the highs on every trip,
the note starts bright and mellows as it rings, which is what a plucked string
does and a fixed-spectrum oscillator cannot. Sustain sets how long the string
takes to fade.

Before the string, a comb on the burst models *where* it was plucked: a delay
of a fraction of the period subtracted from the burst notches the harmonics
that have a node at that point (the middle of the string loses its even
harmonics and sounds hollow, near the bridge keeps them and sounds thin and
twangy).

The strings are a round-robin bank, so a note that is still ringing is not
retuned when the next one starts. An instrument with paired strings (a
mandolin's unison courses, a kora's octave pairs) lists them in `courses`:
each course is another bank tuned a ratio away, struck by the same pluck.
Notes are the rack's chord tones (a hook phrase) or semitones above its chord
root (a bass line). What happens after the string is the style's:
`voice_stage` (a body, an amplifier, a buzzing bridge).

Every instrument is more than constants on this base: it gives each shared
control its own starting value (Hardness, Mute, Dynamics, Looseness, Vibrato,
Pick noise, Bend) and adds the controls that are the instrument's own,
through the `Courses` and `Sympathy` mixins below or in its own module.
"""

from __future__ import annotations

import random
from typing import ClassVar

from pyo import PyoObject
from pyo.lib._core import Mix, Sig
from pyo.lib.controls import SigTo
from pyo.lib.effects import Delay, Disto, Waveguide
from pyo.lib.filters import ButHP, ButLP
from pyo.lib.generators import Noise, Sine
from pyo.lib.tables import LinTable
from pyo.lib.triggers import Trig, TrigEnv

from pyoscillate.clock import NoteDivision
from pyoscillate.harmony import Harmony
from pyoscillate.patches.base import BuildContext, Patch
from pyoscillate.patches.common import (
    ChordRoot,
    Gate,
    GatedVoice,
    Phrased,
    PitchBend,
)
from pyoscillate.patches.params import Param, rate_param
from pyoscillate.theory.interval import Interval
from pyoscillate.theory.phrase import Hooks, PhraseRole
from pyoscillate.theory.pitch import Note


class PluckedString(PitchBend, Gate, ChordRoot, Phrased, GatedVoice):
    """Plucked-string voice. A style gives every shared control its own
    starting value, sets the courses and body data, adds the controls only its
    instrument has, and shapes the sound after the string in `voice_stage`."""

    volume = Patch.volume.replace(default=0.6)
    phrase_roles = (PhraseRole.HOOK,)
    phrase = Phrased.phrase.replace(
        default=Hooks.SPARSE_HOOK,
        help_text="Picks which notes are plucked and when, from a sparse figure to one that fills every step.",
    )
    base_division: ClassVar[NoteDivision] = NoteDivision.EIGHTH
    # strings in the round-robin bank: enough that a note has faded well before
    # its string is struck again at the longest Sustain and fullest phrase
    strings_count: ClassVar[int] = 6
    # the string pairs sounded for every note, each as (frequency ratio to the
    # note, level): one entry is a single string
    courses: ClassVar[tuple[tuple[float, float], ...]] = ((1.0, 1.0),)
    # how long the pluck lasts (s) at the softest and hardest Hardness
    pluck_slowest: ClassVar[float] = 0.012
    pluck_fastest: ClassVar[float] = 0.0008
    # the share of Brightness the softest touch lets through, and the highest
    # cutoff the pluck is ever given (Hz)
    soft_tone: ClassVar[float] = 0.3
    tone_ceiling: ClassVar[float] = 18000
    # the string's peak lands near this level, which an amplifier stage
    # rescales against
    gain: ClassVar[float] = 0.2
    # below the lowest note the Register can reach: the delay line is sized for it
    lowest_freq: ClassVar[float] = 30
    # seconds a moved Pluck position takes to glide, so a sweep does not zip
    position_glide: ClassVar[float] = 0.05
    # longest delay the pick-position comb can need (s)
    comb_reach: ClassVar[float] = 0.1
    # Mute at 1 cuts the ring to this fraction of Sustain and rolls the pluck's
    # brightness off by this fraction (a palm resting on the strings)
    mute_ring: ClassVar[float] = 0.85
    mute_dulling: ClassVar[float] = 0.6
    # how far Looseness at 1 can drop a note's level (fraction) and detune it (cents)
    looseness_level: ClassVar[float] = 0.35
    looseness_cents: ClassVar[float] = 10.0
    looseness_seed: ClassVar[int] = 7
    # the pick's own click: a burst of noise above `click_freq`, `click_time`
    # long, at `click_gain` for Pick noise at 1
    click_freq: ClassVar[float] = 2500.0
    click_time: ClassVar[float] = 0.006
    click_gain: ClassVar[float] = 0.15
    # finger vibrato speed (Hz)
    vibrato_rate: ClassVar[float] = 5.0
    # seconds the vibrato takes to follow a new depth
    vibrato_glide: ClassVar[float] = 0.1
    # `Disto` divides by 1 - drive, so full drive would be infinite gain; and
    # the level a string sustains at, which a saturating stage keeps
    max_drive: ClassVar[float] = 0.95
    string_peak: ClassVar[float] = 0.05

    pluck_table: LinTable
    exciter_noise: Noise
    exciter: ButLP
    triggers: list[Trig]
    # one stream per string in the bank
    freq_sig: Sig
    period_sig: Sig
    level_sig: Sig
    vibrato_depth: SigTo
    vibrato_lfo: Sine
    vibrato_ratio: PyoObject
    bent_freqs: PyoObject
    string_freqs: PyoObject
    pluck_env: TrigEnv
    pluck: PyoObject
    position_sig: SigTo
    pick_delays: PyoObject
    pick_comb: Delay
    excitation: PyoObject
    click_noise: Noise
    click_tone: ButHP
    click_env: TrigEnv
    click_voices: PyoObject
    click: Mix
    course_ratio_sigs: list[Sig]
    course_freqs: list[PyoObject]
    course_strings: list[Waveguide]
    string_mix: Mix
    struck: PyoObject
    harmony: Harmony
    # round-robin cursor and what each string was last struck with: sequence
    # state, kept on self like any step counter
    _next_string: int
    _notes: list[float]
    _periods: list[float]
    _levels: list[float]
    _rng: random.Random

    root_freq = ChordRoot.root_freq.replace(
        minimum=Note.E2,
        maximum=Note.E4,
        default=Note.E3,
        help_text="Moves the whole line up or down; low is a thick, deep register, high is a thinner, lighter line.",
    )

    @Param(
        0.3,
        8.0,
        0.1,
        2.5,
        "Sustain",
        "How long each note rings before it fades; short is a muted, choppy pick, long lets notes sing and overlap the next ones.",
        sweep=True,
    )
    def sustain(self, value: float) -> None:
        self.apply_ring()

    @Param(
        400,
        12000,
        0.02,
        5000,
        "Brightness",
        "How bright the strike is; low is a dull, muffled start, high is a bright, snappy one. Every note still mellows as it rings.",
        scale="cutoff",
        sweep=True,
    )
    def brightness(self, value: float) -> None:
        self.apply_tone()

    @Param(
        0.05,
        0.5,
        0.01,
        0.18,
        "Pluck position",
        "Where along the string the pick lands; near the bridge (low) is thin, bright and twangy, toward the middle (high) is hollow and round.",
        sweep=True,
    )
    def position(self, value: float) -> None:
        self.position_sig.value = value

    @Param(
        0,
        1,
        0.05,
        0.5,
        "Hardness",
        "What strikes the string; low is a soft fingertip or felt hammer that rounds off the start and takes the edge off the highs, high is a hard pick or nail with a sharp, clicky snap.",
        sweep=True,
    )
    def hardness(self, value: float) -> None:
        self.pluck_env.dur = self.hardness_duration(value)
        self.apply_tone()

    @Param(
        0,
        1,
        0.05,
        0,
        "Mute",
        "How much a resting hand damps the strings; none rings free, half is a tight, chunky palm mute, full is a dead, thudding pluck.",
        sweep=True,
    )
    def mute(self, value: float) -> None:
        self.apply_ring()
        self.apply_tone()

    dynamics = Param(
        0,
        1,
        0.05,
        0.5,
        "Dynamics",
        "How much the player leans on the accents of the figure; none plays every note the same, high swells the accented notes and lets the others sit back.",
        sweep=True,
    )

    looseness = Param(
        0,
        1,
        0.05,
        0.2,
        "Looseness",
        "How loose the playing is; none is machine-exact, a little gives each note its own touch and tiny tuning drift, a lot is a sloppy, rambling hand.",
        sweep=True,
        advanced=True,
    )

    @Param(
        0,
        100,
        1,
        0,
        "Vibrato",
        "How far the fretting finger rocks the pitch, in cents; none is a steady string, a little is a singing, vocal ring, a lot is a wide wobble.",
        sweep=True,
    )
    def vibrato(self, value: float) -> None:
        self.vibrato_depth.value = Note.semitone_ratio(value / 100) - 1

    @Param(
        0,
        1,
        0.05,
        0.2,
        "Pick noise",
        "How much of the pick itself you hear; none is only the string, high adds the click of a plectrum, the thump of a fingertip or the clack of a hammer.",
        sweep=True,
    )
    def pick_noise(self, value: float) -> None:
        self.click.mul = value * self.click_gain

    rate = rate_param(
        base_division,
        "Halves or doubles the speed of the figure for each step away from its eighth-note grid.",
    )

    def hardness_duration(self, value: float) -> float:
        """The pluck's length (s) at Hardness `value`: an even step in feel is
        an even ratio in time."""
        return self.pluck_slowest * (self.pluck_fastest / self.pluck_slowest) ** value

    def apply_ring(self) -> None:
        """Sustain, shortened by Mute, onto every string."""
        ring = self.sustain * (1 - self.mute_ring * self.mute)
        for string in self.course_strings:
            string.dur = ring

    def hardness_tone(self, value: float) -> float:
        """How much of Brightness a strike at Hardness `value` lets through,
        relative to the instrument's own starting Hardness (a soft touch
        rolls the highs off, a hard one lets them all through)."""
        return (self.soft_tone + (1 - self.soft_tone) * value) / (
            self.soft_tone + (1 - self.soft_tone) * type(self).hardness.default
        )

    def apply_tone(self) -> None:
        """Brightness, shaped by Hardness and dulled by Mute, onto the pluck."""
        self.exciter.freq = min(
            self.brightness
            * self.hardness_tone(self.hardness)
            * (1 - self.mute_dulling * self.mute),
            self.tone_ceiling,
        )

    def saturate(self, shaper: Disto, amount: float) -> None:
        """Push `shaper` to `amount` (0 to 1) and rescale it so a sustaining
        note keeps its loudness: only the strike is squashed, and the tail
        blooms."""
        drive = amount * self.max_drive
        gain = 2 * drive / (1 - drive)
        shaper.drive = drive
        shaper.mul = (1 + gain * self.string_peak) / (1 + gain)

    def strike_level(self, accent: float) -> float:
        """How loud a strike is: the accent as far as Dynamics follows it, a
        touch of looseness, and a compensation so a harder or softer pluck
        keeps the instrument's loudness."""
        level = (1 - self.dynamics) + self.dynamics * accent
        level *= 1 - self.looseness * self.looseness_level * self._rng.random()
        reference = self.hardness_duration(type(self).hardness.default)
        compensation = (reference / self.hardness_duration(self.hardness)) ** 0.5
        return level * compensation

    def drift(self, note: float) -> float:
        """`note` off by Looseness's tiny, random tuning drift."""
        cents = self.looseness * self.looseness_cents * (2 * self._rng.random() - 1)
        return Note.transpose(note, cents / 100)

    def voice_stage(self, string: PyoObject) -> PyoObject:
        """What happens to the summed strings before they leave the voice (a
        body, an amplifier, a buzzing bridge). A style assigns the nodes it
        builds to `self` and returns the signal; the default leaves the
        string as it is."""
        return string

    def on_strike(self, string: int, note: float, bar_index: int) -> None:
        """A note was just handed to `string`: a style with something else to
        retune per note (sympathetic strings) does it here."""

    def build(self, context: BuildContext) -> Patch:
        self._reset()
        self.harmony = context.harmony
        self._next_string = 0
        self._rng = random.Random(self.looseness_seed)

        # one pluck, shaped like a very short falling ramp, read by every
        # string's own trigger at that string's own level
        count = self.strings_count
        note = self.note_frequency(0, context.clock.bar_index)
        self._notes = [note] * count
        self._periods = [1 / note] * count
        self._levels = [1.0] * count
        self.level_sig = Sig(self._levels)
        self.pluck_table = LinTable([(0, 0), (40, 1), (8191, 0)])
        self.exciter_noise = Noise()
        self.exciter = ButLP(self.exciter_noise, freq=self.brightness)
        self.triggers = [Trig().stop() for _ in range(count)]
        self.pluck_env = TrigEnv(
            self.triggers,
            self.pluck_table,
            dur=self.pluck_slowest,
            mul=self.level_sig,
        )
        self.pluck = self.exciter * self.pluck_env

        # the pick's own click, struck by the same triggers at the same levels
        self.click_noise = Noise()
        self.click_tone = ButHP(self.click_noise, freq=self.click_freq)
        self.click_env = TrigEnv(
            self.triggers, self.pluck_table, dur=self.click_time, mul=self.level_sig
        )
        self.click_voices = self.click_tone * self.click_env
        self.click = Mix(self.click_voices, voices=1)

        # each string's own pitch (scooped by Bend, rocked by Vibrato), and its
        # period for the pick-position comb
        self.freq_sig = Sig(self._notes)
        self.period_sig = Sig(self._periods)
        self.vibrato_depth = SigTo(value=0, time=self.vibrato_glide)
        self.vibrato_lfo = Sine(freq=self.vibrato_rate, mul=self.vibrato_depth)
        self.vibrato_ratio = self.vibrato_lfo + 1
        self.bent_freqs = self.freq_sig * self.add_bend(self.triggers)
        self.string_freqs = self.bent_freqs * self.vibrato_ratio
        # starts at the Pluck position, not 0: a comb of no delay cancels the
        # pluck, so the first note would be silent
        self.position_sig = SigTo(
            value=self.position, time=self.position_glide, init=self.position
        )
        self.pick_delays = self.position_sig * self.period_sig
        self.pick_comb = Delay(
            self.pluck, delay=self.pick_delays, maxdelay=self.comb_reach
        )
        self.excitation = self.pluck - self.pick_comb

        # one bank of strings per course, tuned a ratio from the note; the
        # courses share the voice's level in proportion to their own
        total = sum(level for _, level in self.courses)
        self.course_ratio_sigs = [Sig(ratio) for ratio, _ in self.courses]
        self.course_freqs = [
            self.string_freqs * ratio for ratio in self.course_ratio_sigs
        ]
        self.course_strings = [
            Waveguide(
                self.excitation,
                freq=freqs,
                dur=self.sustain,
                minfreq=self.lowest_freq,
                mul=self.gain * level / total,
            )
            for freqs, (_, level) in zip(self.course_freqs, self.courses, strict=True)
        ]
        self.string_mix = Mix(self.course_strings, voices=1)
        self.struck = self.string_mix + self.click
        staged = self.voice_stage(self.struck)

        self.schedule_pattern(context)
        return self.finish(
            self.add_gate(staged, context),
            resources=(*self.triggers, *self.course_ratio_sigs),
        )

    def strike(self, note: float, accent: float, bar_index: int) -> None:
        """Pluck the next string of the bank at `note`, as hard as `accent`
        and the Dynamics say."""
        string = self._next_string
        self._next_string = (string + 1) % self.strings_count
        note = self.drift(note)
        self._notes[string] = note
        self._periods[string] = 1 / note
        self._levels[string] = self.strike_level(accent)
        self.freq_sig.value = self._notes
        self.period_sig.value = self._periods
        self.level_sig.value = self._levels
        self.on_strike(string, note, bar_index)
        self.triggers[string].play()

    def next_step(self) -> None:
        step = self._step()
        if not step.hit:
            return
        bar = self._clock.bar_index
        accent = self.selected_phrase.accents.get(step.index, 1.0)
        self.strike(self.note_frequency(int(step.value), bar), accent, bar)


class Courses(PluckedString):
    """Opt-in add-on for an instrument whose notes sound on several strings
    (`courses`: a mandolin's unison pairs, a 12-string's octaves, a kora's
    octave strings): Spread detunes the extra strings against the first and
    Doubling sets how loud they are, so one instrument can be a single string,
    a shimmering pair or a chorus of strings. Mix it in ahead of the voice
    base: `class Mandolin(Courses, Body)`. Each course after the first is
    detuned by its position times Spread, so a unison pair beats at Spread
    cents and a third string at twice that."""

    @Param(
        0,
        30,
        0.5,
        0,
        "Spread",
        "How far the paired strings sit out of tune with each other; none fuses them into one string, a little is a slow shimmer, a lot is a wide, chorused, honky-tonk sound.",
        sweep=True,
    )
    def spread(self, value: float) -> None:
        for index, sig in enumerate(self.course_ratio_sigs):
            ratio = self.courses[index][0]
            sig.value = ratio * Note.semitone_ratio(index * value / 100)

    @Param(
        0,
        1.5,
        0.05,
        1.0,
        "Doubling",
        "How loud the extra strings are next to the first; none is a single string, full is a rich, paired voice, and the voice's total level stays the same.",
        sweep=True,
    )
    def doubling(self, value: float) -> None:
        weights = [
            level * (value if index else 1.0)
            for index, (_, level) in enumerate(self.courses)
        ]
        total = sum(weights)
        for string, weight in zip(self.course_strings, weights, strict=True):
            string.mul = self.gain * weight / total


class Sympathy(PluckedString):
    """Opt-in add-on for strings that are never played but ring in answer: a
    sitar's sympathetic strings, a harp's open strings, a lute's bass courses.
    They are waveguides tuned `sympathy_intervals` (semitones) above the
    chord's root, retuned on every strike and fed by the played string, so
    they ring only where the note shares a partial with them. Sympathy sets how
    much they add and Sympathy ring how long they sing. Mix it in ahead of the
    voice base and pass the played string through `add_sympathy` in
    `voice_stage`."""

    # the unplayed strings, as semitones above the chord's root
    sympathy_intervals: ClassVar[tuple[float, ...]] = (
        Interval.UNISON,
        Interval.PERFECT_FIFTH,
    )
    # trims the sympathetic strings (a resonator gains a steady tone heavily)
    # so Sympathy at 1 adds about as much as the played string
    sympathy_trim: ClassVar[float] = 0.01

    sympathy_freqs: Sig
    sympathy: Waveguide
    sympathy_sum: PyoObject
    sympathy_voiced: PyoObject

    @Param(
        0,
        1,
        0.05,
        0.4,
        "Sympathy",
        "How much the unplayed strings ring in answer to the note; low is a dry, single string, high is a shimmering halo around the chord.",
        sweep=True,
    )
    def sympathy_level(self, value: float) -> None:
        self.sympathy.mul = value * self.sympathy_trim

    @Param(
        0.5,
        6.0,
        0.1,
        2.0,
        "Sympathy ring",
        "How long the unplayed strings keep singing; short is a quick shimmer that clears, long is a halo that hangs over the next notes.",
        sweep=True,
        advanced=True,
    )
    def sympathy_ring(self, value: float) -> None:
        self.sympathy.dur = value

    def sympathy_tuning(self, bar_index: int) -> list[float]:
        """The unplayed strings' pitches under `bar_index`'s chord."""
        root = self.root_at(bar_index)
        return [Note.transpose(root, interval) for interval in self.sympathy_intervals]

    def add_sympathy(self, source: PyoObject) -> PyoObject:
        """`source` plus the strings it sets ringing; call from `voice_stage`."""
        self.sympathy_freqs = Sig(self.sympathy_tuning(0))
        self.sympathy = Waveguide(
            source,
            freq=self.sympathy_freqs,
            dur=self.sympathy_ring,
            minfreq=self.lowest_freq,
        )
        self.sympathy_sum = self.sympathy.mix(1)
        self.sympathy_voiced = source + self.sympathy_sum
        return self.sympathy_voiced

    def on_strike(self, string: int, note: float, bar_index: int) -> None:
        super().on_strike(string, note, bar_index)
        self.sympathy_freqs.value = self.sympathy_tuning(bar_index)
