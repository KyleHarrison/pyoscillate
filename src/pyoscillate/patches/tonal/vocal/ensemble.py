# uv run flet run src/flet/patch/app.py -- pyoscillate.patches.tonal.vocal.ensemble
"""Sung ensembles: a choir and a chorus of angels holding the rack's chord, a
voice on every chord tone and each sung by several detuned singers (`Ensemble`,
see `common.py`). Both are a `FormantSinger` (see `singer.py`); the styles
differ in the chord they voice, the register, the vowel and how soft, slow and
spacious the swell is."""

from __future__ import annotations

from typing import ClassVar

from pyoscillate.patches.common import Ensemble, Phrased
from pyoscillate.patches.tonal.vocal.singer import FormantSinger, VocalTract
from pyoscillate.theory.chord import Chords
from pyoscillate.theory.phrase import PhraseRole, Rhythms
from pyoscillate.theory.pitch import Note


class ChoralSinger(Ensemble, FormantSinger):
    """Shared shape of the ensembles: the chord's tones sung together on a
    chord rhythm (a bar-long pulse by default), each by `copies` singers."""

    copies: ClassVar[int] = 2
    phrase_roles = (PhraseRole.CHORD_HIT,)
    phrase = Phrased.phrase.replace(
        default=Rhythms.BAR_PULSE,
        help_text="Picks when in the bar the chord is sung, from one held chord a bar to a backbeat or a "
        "swung pulse; every voice draws on the same shared patterns.",
    )
    root_freq = FormantSinger.root_freq.replace(
        help_text="Moves the whole chord up or down; low is a dark, deep, male-weighted choir, high is a thin, bright, soprano-led one.",
    )
    legato = FormantSinger.legato.replace(default=0.95)


class Choir(ChoralSinger):
    """Mixed choir: a bass an octave below the root, then the triad and the
    octave above, each sung by two singers on an open 'ah', swelling in and
    out with a slow, light vibrato."""

    title = "Choir"
    summary = "Warm, swelling mixed choir holding the rack's chord."

    voice_type: ClassVar[tuple] = VocalTract.ALTO
    chord_shape = Chords.SPREAD_TRIAD

    root_freq = ChoralSinger.root_freq.replace(
        minimum=Note.A2, maximum=Note.A4, default=Note.A3
    )
    attack = ChoralSinger.attack.replace(default=0.35)
    release = ChoralSinger.release.replace(default=0.9)
    vibrato = ChoralSinger.vibrato.replace(default=18)
    vibrato_speed = ChoralSinger.vibrato_speed.replace(default=4.8)
    vibrato_bloom = ChoralSinger.vibrato_bloom.replace(default=0.6)
    brightness = ChoralSinger.brightness.replace(default=3200)
    breath = ChoralSinger.breath.replace(default=0.12)
    reverb_size = ChoralSinger.reverb_size.replace(default=0.7)
    reverb_bal = ChoralSinger.reverb_bal.replace(default=0.4)


class Angels(ChoralSinger):
    """Chorus of angels: a high, open triad sung by three singers a note on a
    rounded 'oo-ah', airy and resonant, swelling in very slowly with a slow,
    shimmering vibrato and a vast room."""

    title = "Angels"
    summary = "High, airy, shimmering angelic chorus holding the rack's chord."

    voice_type: ClassVar[tuple] = VocalTract.SOPRANO
    copies: ClassVar[int] = 3
    chord_shape = Chords.TRIAD

    root_freq = ChoralSinger.root_freq.replace(
        minimum=Note.A3, maximum=Note.A5, default=Note.A4
    )
    attack = ChoralSinger.attack.replace(default=0.8)
    release = ChoralSinger.release.replace(default=1.6)
    vibrato = ChoralSinger.vibrato.replace(default=20)
    vibrato_speed = ChoralSinger.vibrato_speed.replace(default=2.4)
    vibrato_bloom = ChoralSinger.vibrato_bloom.replace(default=0.9)
    spread = ChoralSinger.spread.replace(default=18)
    vowel = ChoralSinger.vowel.replace(default=1.5)
    focus = ChoralSinger.focus.replace(default=1.6)
    brightness = ChoralSinger.brightness.replace(default=5000)
    breath = ChoralSinger.breath.replace(default=0.3)
    unsteadiness = ChoralSinger.unsteadiness.replace(default=0.2)
    reverb_size = ChoralSinger.reverb_size.replace(default=0.9)
    reverb_bal = ChoralSinger.reverb_bal.replace(default=0.55)
