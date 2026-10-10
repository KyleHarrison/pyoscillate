# uv run flet run src/flet/patch/app.py -- pyoscillate.patches.tonal.vocal.solo
"""Solo voices: one singer on a line of the rack's chord tones, a female
(soprano) and a male (tenor) voice. Both are a `FormantSinger` (see
`singer.py`); the styles differ in the formant table, the register and how the
voice is carried: its brightness, breath, vibrato and room."""

from __future__ import annotations

from typing import ClassVar

from pyoscillate.patches.tonal.vocal.singer import FormantSinger, VocalTract
from pyoscillate.theory.pitch import Note


class SoloSinger(FormantSinger):
    """Shared shape of the solo voices: one note at a time, sung over the
    chord tones, in a register set by the style."""

    root_freq = FormantSinger.root_freq.replace(
        help_text="Moves the whole line up or down; low is a dark, chesty register, high is a thin, bright, head-voice one.",
    )
    legato = FormantSinger.legato.replace(default=0.9)


class VocalFemale(SoloSinger):
    """Female solo voice: a soprano singing an open 'ah', warm and breathy,
    with a vibrato that blooms in after each note."""

    title = "Vocal - Female"
    summary = "Warm, breathy soprano line over the rack's chord tones."

    voice_type: ClassVar[tuple] = VocalTract.SOPRANO

    root_freq = SoloSinger.root_freq.replace(
        minimum=Note.C4, maximum=Note.C6, default=Note.A4
    )
    attack = SoloSinger.attack.replace(default=0.12)
    release = SoloSinger.release.replace(default=0.4)
    vibrato = SoloSinger.vibrato.replace(default=28)
    vibrato_speed = SoloSinger.vibrato_speed.replace(default=5.4)
    vibrato_bloom = SoloSinger.vibrato_bloom.replace(default=0.45)
    brightness = SoloSinger.brightness.replace(default=4000)
    breath = SoloSinger.breath.replace(default=0.15)
    unsteadiness = SoloSinger.unsteadiness.replace(default=0.3)
    reverb_size = SoloSinger.reverb_size.replace(default=0.5)
    reverb_bal = SoloSinger.reverb_bal.replace(default=0.25)


class VocalMale(SoloSinger):
    """Male solo voice: a tenor singing an open 'ah', lower and rounder than
    the soprano, with a slower, narrower vibrato."""

    title = "Vocal - Male"
    summary = "Round, low tenor line over the rack's chord tones."

    voice_type: ClassVar[tuple] = VocalTract.TENOR

    root_freq = SoloSinger.root_freq.replace(
        minimum=Note.E2, maximum=Note.E4, default=Note.A2
    )
    attack = SoloSinger.attack.replace(default=0.1)
    release = SoloSinger.release.replace(default=0.35)
    vibrato = SoloSinger.vibrato.replace(default=22)
    vibrato_speed = SoloSinger.vibrato_speed.replace(default=5.0)
    vibrato_bloom = SoloSinger.vibrato_bloom.replace(default=0.4)
    brightness = SoloSinger.brightness.replace(default=3000)
    breath = SoloSinger.breath.replace(default=0.12)
    unsteadiness = SoloSinger.unsteadiness.replace(default=0.25)
    reverb_size = SoloSinger.reverb_size.replace(default=0.45)
    reverb_bal = SoloSinger.reverb_bal.replace(default=0.2)
