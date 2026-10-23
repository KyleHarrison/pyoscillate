# uv run flet run src/flet/patch/app.py -- pyoscillate.patches.tonal.keys.string_keys
"""Keyboards with strings: a piano's hammered strings, a harpsichord's quilled
ones and a clavichord's tangent-struck ones. All three are a `PluckedString`
(see `pluck/string.py` for the string itself) through a soundboard (`Body`) and
a set of strings per note (`Courses`); what differs is what sets the string
going and what follows.

A key plays either one note of the chord (a figure of chord tones) or the whole
chord struck at once (a chord rhythm), so the same instrument arpeggiates or
comps. The strings are the pluck family's round-robin bank, with room for a
chord to ring over the next one.

- `Piano`: a soft felt hammer strikes three unison strings a little out of tune
  with each other, so a note beats and sings; the lifted dampers let the other
  strings ring in answer (`Sympathy`, which is the sustain pedal).
- `Harpsichord`: a quill plucks the string with the same force whatever the
  touch, so it has no dynamics; two unison ranks and a rank an octave above
  (`Courses`) are drawn together for the plenum.
- `Clavichord`: a brass tangent strikes the string and stays on it, damped by
  cloth, so it is quiet, the most touch-sensitive of the three, and the player
  can rock the tangent for a tiny vibrato (`Bebung`).
"""

from __future__ import annotations

from typing import ClassVar

from pyo import PyoObject

from pyoscillate.patches.common import Body, Phrased
from pyoscillate.patches.tonal.pluck.string import (
    Courses,
    PluckedString,
    Sympathy,
)
from pyoscillate.theory.chord import Chord, Chords
from pyoscillate.theory.interval import Interval
from pyoscillate.theory.phrase import Hooks, PhraseRole
from pyoscillate.theory.pitch import Note


class KeyedString(Courses, Body, PluckedString):
    """Shared shape of the string keyboards: a figure of chord tones or a
    chord struck on a rhythm, through a soundboard. A style gives every shared
    control its own starting value and the strings and body of its instrument."""

    # the chord a chord rhythm strikes, lowest note first
    chord_shape: ClassVar[Chord] = Chords.TRIAD
    # room for a chord of four to ring over the next one at a long Sustain
    strings_count: ClassVar[int] = 12

    phrase_roles = (PhraseRole.HOOK, PhraseRole.CHORD_HIT)
    phrase = Phrased.phrase.replace(
        default=Hooks.SPARSE_HOOK,
        help_text="Picks which keys are struck and when: a figure of chord tones, or the whole chord struck on a rhythm; "
        "every voice draws on the same shared patterns.",
    )
    position = PluckedString.position.replace(
        help_text="Where along the string it is struck; near the end (low) is thin, bright and nasal, toward the middle (high) is hollow and round.",
    )

    def voice_stage(self, string: PyoObject) -> PyoObject:
        return self.add_body(string)

    def next_step(self) -> None:
        step = self._step()
        if not step.hit:
            return
        bar = self._clock.bar_index
        accent = self.selected_phrase.accents.get(step.index, 1.0)
        for note in self.sounding(step.value, bar):
            self.strike(note, accent, bar)


class Piano(Sympathy, KeyedString):
    """Grand piano: a felt hammer strikes three unison strings that beat
    gently against each other, singing through a large soundboard, with the
    sustain pedal letting the other strings ring in answer."""

    title = "Piano"
    summary = "Warm, ringing grand piano figure over the rack's chord tones."
    volume = KeyedString.volume.replace(default=0.5)

    # three strings to a note, each a little further out of tune than the last
    courses = ((1.0, 1.0), (1.0, 1.0), (1.0, 1.0))
    # the soundboard's broad, low resonances
    body_modes = (Note.A1, Note.E2, Note.B2, Note.G3)
    body_q = (3, 3, 4, 4)
    click_freq = 1200
    click_time = 0.012
    # the strings the pedal lets ring: the chord's root, fifth and octave
    sympathy_intervals = (Interval.UNISON, Interval.PERFECT_FIFTH, Interval.OCTAVE)

    root_freq = KeyedString.root_freq.replace(
        minimum=Note.A2, maximum=Note.A4, default=Note.A3
    )
    sustain = KeyedString.sustain.replace(default=4.0)
    brightness = KeyedString.brightness.replace(default=4500)
    position = KeyedString.position.replace(default=0.12)
    # a felt hammer, a player who leans into the accents, a little thump
    hardness = KeyedString.hardness.replace(
        default=0.35,
        help_text="How hard the hammer is; low is a soft, mellow, felted piano, high is a hard, bright, honky-tonk hammer with a sharp attack.",
    )
    dynamics = KeyedString.dynamics.replace(default=0.7)
    looseness = KeyedString.looseness.replace(default=0.15)
    pick_noise = KeyedString.pick_noise.replace(
        default=0.12,
        label="Hammer noise",
        help_text="How much of the hammer's thump you hear; none is only the strings, high is a percussive, knocking attack.",
    )
    mute = KeyedString.mute.replace(
        label="Mute pedal",
        help_text="How far a felt strip is lowered between the hammers and the strings; none is a full, ringing piano, full is a dull, short, intimate practice piano.",
    )
    body = KeyedString.body.replace(
        default=0.5,
        help_text="How much the soundboard rings with the strings; low is thin and dry, like a pickup, high is a full, warm, resonant piano.",
    )
    spread = KeyedString.spread.replace(
        default=3,
        help_text="How far the three strings of a note are out of tune with each other; none fuses them into one hard string, a little is the slow beating of a well-kept piano, a lot is a honky-tonk, detuned upright.",
    )
    doubling = KeyedString.doubling.replace(
        label="Strings struck",
        help_text="How many of each note's strings sound; none is one thin, clear string, full is the rich, beating three-string unison of the middle of the keyboard.",
    )
    sympathy_level = Sympathy.sympathy_level.replace(
        default=0.25,
        label="Pedal",
        help_text="How much the other strings ring in answer, as when the sustain pedal lifts every damper; none is dry, damped notes, full is a washy, blurred halo around the chord.",
    )
    sympathy_ring = Sympathy.sympathy_ring.replace(
        default=3.0,
        label="Pedal ring",
        help_text="How long the freed strings keep singing; short is a quick blur that clears, long is a halo that hangs over the notes that follow.",
    )

    def voice_stage(self, string: PyoObject) -> PyoObject:
        return self.add_body(self.add_sympathy(string))


class Harpsichord(KeyedString):
    """Harpsichord: a quill plucks the string, bright and dry and always at
    the same strength, over two unison ranks and a rank an octave above, with
    the click of the jack."""

    title = "Harpsichord"
    summary = "Bright, dry harpsichord figure over the rack's chord tones."
    volume = KeyedString.volume.replace(default=0.45)

    # two 8' ranks and the 4' rank an octave above, each quieter than the last
    courses = ((1.0, 1.0), (1.0, 0.8), (2.0, 0.55))
    body_modes = (Note.D3, Note.A3, Note.E4)
    body_q = (4, 5, 6)
    click_freq = 3500
    click_time = 0.004

    phrase = KeyedString.phrase.replace(default=Hooks.FULL_HOOK)
    root_freq = KeyedString.root_freq.replace(
        minimum=Note.A2, maximum=Note.A4, default=Note.A3
    )
    sustain = KeyedString.sustain.replace(default=1.4)
    brightness = KeyedString.brightness.replace(default=7000)
    position = KeyedString.position.replace(default=0.1)
    # a quill, and a player who cannot change its force
    hardness = KeyedString.hardness.replace(
        default=0.9,
        help_text="How the quill plucks; low is a soft, lute-like pluck, high is a hard, sharp, snapping quill.",
    )
    dynamics = KeyedString.dynamics.replace(
        default=0,
        help_text="How much the player leans on the accents; a harpsichord's quill plucks with the same force whatever the touch, so none is authentic, and more adds the swell of a modern, touch-sensitive instrument.",
    )
    looseness = KeyedString.looseness.replace(default=0.05)
    pick_noise = KeyedString.pick_noise.replace(
        default=0.5,
        label="Jack click",
        help_text="How much of the jack's click and the thump of its return you hear; none is only the strings, high is a clattering, mechanical harpsichord.",
    )
    mute = KeyedString.mute.replace(
        label="Buff stop",
        help_text="How far a strip of leather presses on the strings; none rings free, full is the dry, plucked, lute-like sound of the buff stop.",
    )
    body = KeyedString.body.replace(
        default=0.6,
        help_text="How much the soundboard and the case ring with the strings; low is thin and dry, high is a full, woody harpsichord.",
    )
    spread = KeyedString.spread.replace(
        default=3,
        help_text="How far the ranks sit out of tune with each other; none is a clean, locked plenum, a little is the shimmer of two ranks, a lot is a wide, wobbling, out-of-tune instrument.",
    )
    doubling = KeyedString.doubling.replace(
        label="Registers",
        help_text="How many ranks of strings are drawn; none is a single, thin 8' rank, full adds the second rank and the bright rank an octave above for the full plenum.",
    )


class Clavichord(KeyedString):
    """Clavichord: a brass tangent strikes the string and stays on it, a
    quiet, intimate, touch-sensitive voice, damped by cloth, that the player
    can rock for a tiny vibrato."""

    title = "Clavichord"
    summary = "Quiet, intimate clavichord figure over the rack's chord tones."
    volume = KeyedString.volume.replace(default=0.65)

    # the strings are paired in unison
    courses = ((1.0, 1.0), (1.0, 1.0))
    body_modes = (Note.F3, Note.C4, Note.G4)
    body_q = (5, 6, 7)
    click_freq = 2000
    click_time = 0.005
    vibrato_rate = 6.0

    root_freq = KeyedString.root_freq.replace(
        minimum=Note.A2, maximum=Note.A4, default=Note.A3
    )
    sustain = KeyedString.sustain.replace(default=1.3)
    brightness = KeyedString.brightness.replace(default=3500)
    position = KeyedString.position.replace(default=0.2)
    # a tangent is hard but struck gently, and the cloth listing damps it
    hardness = KeyedString.hardness.replace(
        default=0.55,
        help_text="How the tangent strikes; low is a soft, rounded touch, high is a sharp, metallic tick.",
    )
    dynamics = KeyedString.dynamics.replace(
        default=0.9,
        help_text="How much the player leans on the accents; a clavichord answers every shade of touch, so high swells the accented notes and lets the others sit far back.",
    )
    looseness = KeyedString.looseness.replace(default=0.1)
    pick_noise = KeyedString.pick_noise.replace(
        default=0.2,
        label="Tangent tap",
        help_text="How much of the tangent's tap you hear; none is only the string, high is a clicking, mechanical touch.",
    )
    mute = KeyedString.mute.replace(
        default=0.35,
        label="Cloth damping",
        help_text="How much the strip of cloth damps the strings; none is a free, ringing clavichord, full is a very dry, soft, muted one.",
    )
    body = KeyedString.body.replace(
        default=0.5,
        help_text="How much the small wooden case rings with the strings; low is thin and dry, high is a warm, boxy resonance.",
    )
    spread = KeyedString.spread.replace(
        default=3,
        help_text="How far the paired strings are out of tune with each other; none fuses them, a little is a soft shimmer, a lot is a wide, wavering chorus.",
    )
    doubling = KeyedString.doubling.replace(
        label="Second string",
        default=0.8,
        help_text="How loud the second string of each pair is; none is a single string, full is a rich, equal pair.",
    )
    vibrato = KeyedString.vibrato.replace(
        default=10,
        label="Bebung",
        help_text="How far the player rocks the tangent against the string, in cents; none is a steady string, a little is the tiny, singing tremble only a clavichord can make, a lot is a wide wobble.",
    )
