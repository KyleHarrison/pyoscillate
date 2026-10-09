# uv run flet run src/flet/patch/app.py -- pyoscillate.patches.tonal.bass.standup
"""Standup bass: a heavy gut or steel string plucked with the flesh of the
finger, over a large hollow body that carries the low end.

It is a `PluckedString` (see `pluck/string.py` for the string itself), not a
`Bass` oscillator voice: a bass line from the shared catalog sets the pitches,
and the string, its soft finger strike and its body make the note. The finger
is slow and fleshy, so the strike is soft; the string rings briefly and
mellows quickly, which is what makes a walking line thump rather than sustain.
"""

from __future__ import annotations

from pyo import PyoObject

from pyoscillate.clock import NoteDivision
from pyoscillate.patches.base import Patch
from pyoscillate.patches.common import Body
from pyoscillate.patches.params import rate_param
from pyoscillate.patches.tonal.pluck.string import PluckedString
from pyoscillate.theory.phrase import BassLines, PhraseRole, Phrases
from pyoscillate.theory.pitch import Note


class StandupBass(Body, PluckedString):
    """Plucked upright bass: a soft finger on a heavy string, thumping under
    the rack's chord changes."""

    title = "Standup Bass"
    summary = "Round, woody standup-bass line thumping under the rack's chords."

    volume = Patch.volume.replace(default=0.9)
    base_division = NoteDivision.SIXTEENTH
    # the flesh of a finger: a slow, soft strike
    pluck_time = 0.008
    # a low string moves little air for its energy: heard at the same level as
    # the others it needs a much hotter pluck
    gain = 0.7
    # the body's loudest resonances: the air inside and its upper modes
    body_modes = (Note.A1, Note.E2, Note.B2)
    body_q = (6, 6, 7)

    phrase_roles = (PhraseRole.BASS,)
    phrase = PluckedString.phrase.replace(
        default=BassLines.BASS_CONVERSATION,
        catalog=Phrases.for_roles(PhraseRole.BASS),
        help_text="Picks the bass line that is played, as pitches above the current chord; every pitched voice draws on the same shared lines.",
    )
    root_freq = PluckedString.root_freq.replace(
        minimum=Note.E1,
        maximum=Note.E3,
        default=Note.A1,
        help_text="Moves the bass line up or down; low sits deep under the kick, high comes up toward the chords.",
    )
    sustain = PluckedString.sustain.replace(default=1.4)
    brightness = PluckedString.brightness.replace(default=700)
    position = PluckedString.position.replace(default=0.3)
    body = Body.body.replace(default=0.6)
    rate = rate_param(
        base_division,
        "Halves or doubles the speed of the line for each step away from its sixteenth-note grid.",
    )

    def voice_stage(self, string: PyoObject) -> PyoObject:
        return self.add_body(string)
