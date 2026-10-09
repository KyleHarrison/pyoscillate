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
"""

from __future__ import annotations

from typing import ClassVar

from pyo import PyoObject
from pyo.lib._core import Mix, Sig
from pyo.lib.controls import SigTo
from pyo.lib.effects import Delay, Waveguide
from pyo.lib.filters import ButLP
from pyo.lib.generators import Noise
from pyo.lib.tables import LinTable
from pyo.lib.triggers import Trig, TrigEnv

from pyoscillate.clock import NoteDivision
from pyoscillate.harmony import Harmony
from pyoscillate.patches.base import BuildContext, Patch
from pyoscillate.patches.common import ChordRoot, Gate, GatedVoice, Phrased
from pyoscillate.patches.params import Param, rate_param
from pyoscillate.theory.chord import Chords
from pyoscillate.theory.phrase import Hooks, PhraseMode, PhraseRole
from pyoscillate.theory.pitch import Note


class PluckedString(Gate, ChordRoot, Phrased, GatedVoice):
    """Plucked-string voice. Style subclasses set the pluck, the courses and
    the starting Sustain, Brightness and Pluck position, and shape the sound
    after the string in `voice_stage`."""

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
    # how long the pluck lasts (s): short is a hard, clicky pick
    pluck_time: ClassVar[float] = 0.003
    # the string's peak lands near this level, which an amplifier stage
    # rescales against
    gain: ClassVar[float] = 0.2
    # below the lowest note the Register can reach: the delay line is sized for it
    lowest_freq: ClassVar[float] = 30
    # seconds a moved Pluck position takes to glide, so a sweep does not zip
    position_glide: ClassVar[float] = 0.05
    # longest delay the pick-position comb can need (s)
    comb_reach: ClassVar[float] = 0.1

    pluck_table: LinTable
    exciter_noise: Noise
    exciter: ButLP
    triggers: list[Trig]
    freq_sigs: list[Sig]
    period_sigs: list[Sig]
    pluck_env: TrigEnv
    pluck: PyoObject
    position_sig: SigTo
    pick_delays: list[PyoObject]
    pick_comb: Delay
    excitation: PyoObject
    course_freqs: list[list[PyoObject]]
    course_strings: list[Waveguide]
    string_mix: Mix
    harmony: Harmony
    # round-robin cursor: sequence state, kept on self like any step counter
    _next_string: int

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
        for string in self.course_strings:
            string.dur = value

    @Param(
        400,
        12000,
        0.02,
        5000,
        "Brightness",
        "How hard or soft the pick is; low is a soft finger touch with a dull, muffled start, high is a bright, snappy pick attack. Every note still mellows as it rings.",
        scale="cutoff",
        sweep=True,
    )
    def brightness(self, value: float) -> None:
        self.exciter.freq = value

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

    rate = rate_param(
        base_division,
        "Halves or doubles the speed of the figure for each step away from its eighth-note grid.",
    )

    def note_frequency(self, value: int, bar_index: int) -> float:
        """The pitch a phrase step asks for in `bar_index`'s chord: for a
        chord-tone phrase `value` indexes the chord's triad, for a bass line
        it is semitones above the chord root. Either way it is the octave of
        the chord root nearest the Register."""
        root = self.root_at(bar_index)
        if self.selected_phrase.mode is PhraseMode.CHORD_TONE:
            tones = self.chord_tones(self.harmony, bar_index, Chords.TRIAD)
            return Note.transpose(root, tones[value] - tones[0])
        return Note.transpose(root, value)

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

        # one pluck, shaped like a very short falling ramp, read by every
        # string's own trigger
        self.pluck_table = LinTable([(0, 0), (40, 1), (8191, 0)])
        self.exciter_noise = Noise()
        self.exciter = ButLP(self.exciter_noise, freq=self.brightness)
        self.triggers = [Trig().stop() for _ in range(self.strings_count)]
        self.pluck_env = TrigEnv(self.triggers, self.pluck_table, dur=self.pluck_time)
        self.pluck = self.exciter * self.pluck_env

        # each string's own pitch, and its period for the pick-position comb
        note = self.note_frequency(0, context.clock.bar_index)
        self.freq_sigs = [Sig(note) for _ in self.triggers]
        self.period_sigs = [Sig(1 / note) for _ in self.triggers]
        # starts at the Pluck position, not 0: a comb of no delay cancels the
        # pluck, so the first note would be silent
        self.position_sig = SigTo(
            value=self.position, time=self.position_glide, init=self.position
        )
        self.pick_delays = [self.position_sig * period for period in self.period_sigs]
        self.pick_comb = Delay(
            self.pluck, delay=self.pick_delays, maxdelay=self.comb_reach
        )
        self.excitation = self.pluck - self.pick_comb

        # one bank of strings per course, tuned a ratio from the note; the
        # courses share the voice's level in proportion to their own
        total = sum(level for _, level in self.courses)
        self.course_freqs = [
            [sig * ratio for sig in self.freq_sigs] for ratio, _ in self.courses
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
        staged = self.voice_stage(self.string_mix)

        self.schedule_pattern(context)
        return self.finish(
            self.add_gate(staged, context),
            resources=(
                *self.triggers,
                *self.freq_sigs,
                *self.period_sigs,
                *self.pick_delays,
                *(freq for freqs in self.course_freqs for freq in freqs),
            ),
        )

    def next_step(self) -> None:
        step = self._step()
        if not step.hit:
            return
        string = self._next_string
        self._next_string = (string + 1) % self.strings_count
        bar = self._clock.bar_index
        note = self.note_frequency(int(step.value), bar)
        self.freq_sigs[string].value = note
        self.period_sigs[string].value = 1 / note
        self.on_strike(string, note, bar)
        self.triggers[string].play()
