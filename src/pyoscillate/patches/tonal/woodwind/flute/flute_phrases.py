"""Tunes for the flute: long, fixed melodies written out note by note.

The shared phrase catalogs (`theory/phrase/`) hold short figures every voice
can play. A tune is the opposite: one instrument's piece, many bars long, with
no use anywhere else, so it lives beside the instrument and is injected into
that instrument's dropdown (`FlutePhrases`: the tunes first, then everything a
wind line can already play). `Flute` takes the catalog with
`phrase = JetWind.phrase.replace(catalog=FlutePhrases)`.

A tune is a `Phrase` like any other: `SEMITONES` above the sounding chord's
root, on a sixteenth-note grid, so it follows the rack's progression and the
Register slider. Every step is `Step(at, offset)`: the sixteenth in the cycle
a note starts on, and its distance in semitones above the chord root (negative
is below). A note lasts until the next one starts, shortened by Legato.
"""

from __future__ import annotations

from pyoscillate.clock import NoteDivision
from pyoscillate.theory.catalog import Catalog
from pyoscillate.theory.phrase import Phrase, PhraseMode, PhraseRole, Phrases, Step


class FluteTunes(Catalog):
    """Fixed melodies for the flute."""

    category = "Flute tune"

    HILLSIDE_TUNE = Phrase(
        division=NoteDivision.SIXTEENTH,
        cycle=640,
        label="Hillside tune: a thirty-four-bar pastoral melody",
        mode=PhraseMode.SEMITONES,
        roles=(PhraseRole.LEAD,),
        steps=(
            # Measure 27: short ascending figure, then chordal response
            Step(0, 7, length=1),
            Step(2, 9, length=1),
            Step(4, 11, length=1),
            Step(6, 14, length=2),
            Step(12, 11, length=1),
            Step(14, 9, length=1),
            Step(16, 7, length=2),
            Step(20, 9, length=1),
            Step(22, 7, length=1),
            Step(24, 4, length=2),
            Step(28, 7, length=2),
            # Measures 28-30: sustained harmony
            Step(32, 4, length=16),
            Step(48, 2, length=16),
            # Measures 31-33: sustained harmony, then short response
            Step(64, 0, length=16),
            Step(80, 2, length=16),
            Step(96, 4, length=2),
            Step(100, 7, length=1),
            Step(102, 9, length=1),
            Step(104, 7, length=1),
            Step(108, 9, length=1),
            # Measure 34: repeated lower-register figure
            Step(112, 0, length=1),
            Step(114, -5, length=1),
            Step(116, -2, length=1),
            Step(118, -5, length=1),
            Step(120, 0, length=1),
            Step(122, -5, length=1),
            Step(124, -2, length=1),
            Step(126, -5, length=1),
            # Measures 35-38: recurring arpeggiated figure
            Step(128, 2, length=1),
            Step(130, -3, length=1),
            Step(132, 0, length=1),
            Step(134, -3, length=1),
            Step(136, 2, length=1),
            Step(138, -3, length=1),
            Step(140, 0, length=1),
            Step(142, -3, length=1),
            Step(144, 0, length=1),
            Step(146, -5, length=1),
            Step(148, -2, length=1),
            Step(150, -5, length=1),
            Step(152, 0, length=1),
            Step(154, -5, length=1),
            Step(156, -2, length=1),
            Step(158, -5, length=1),
            Step(160, 2, length=1),
            Step(162, -3, length=1),
            Step(164, 0, length=1),
            Step(166, -3, length=1),
            Step(168, 2, length=1),
            Step(170, -3, length=1),
            Step(172, 0, length=1),
            Step(174, -3, length=1),
            # Measures 39-42: repeated pattern with harmonic variation
            Step(176, 0, length=1),
            Step(178, -5, length=1),
            Step(180, -2, length=1),
            Step(182, -5, length=1),
            Step(184, 0, length=1),
            Step(186, -5, length=1),
            Step(188, -2, length=1),
            Step(190, -5, length=1),
            Step(192, 2, length=1),
            Step(194, -3, length=1),
            Step(196, 0, length=1),
            Step(198, -3, length=1),
            Step(200, 2, length=1),
            Step(202, -3, length=1),
            Step(204, 0, length=1),
            Step(206, -3, length=1),
            Step(208, 0, length=1),
            Step(210, -5, length=1),
            Step(212, -2, length=1),
            Step(214, -5, length=1),
            Step(216, 0, length=1),
            Step(218, -5, length=1),
            Step(220, -2, length=1),
            Step(222, -5, length=1),
            Step(224, 2, length=1),
            Step(226, -3, length=1),
            Step(228, 0, length=1),
            Step(230, -3, length=1),
            Step(232, 2, length=1),
            Step(234, -3, length=1),
            Step(236, 0, length=1),
            Step(238, -3, length=1),
            # Measures 43-46: melody returns over moving accompaniment
            Step(240, 4, accent=1.2, length=1),
            Step(242, 7, length=1),
            Step(244, 9, accent=1.2, length=1),
            Step(248, 7, length=1),
            Step(250, 4, length=1),
            Step(252, 2, accent=1.2, length=1),
            Step(256, 12, accent=1.3, length=2),
            Step(260, 7, length=1),
            Step(264, 4, length=1),
            Step(266, 5, length=1),
            Step(268, 7, length=2),
            Step(272, 4, length=2),
            Step(276, 7, length=1),
            Step(278, 9, length=1),
            Step(280, 7, length=2),
            Step(284, 4, length=2),
            Step(288, 7, length=1),
            Step(290, 9, length=1),
            Step(292, 11, length=2),
            Step(296, 9, length=2),
            Step(300, 7, length=2),
            # Measures 47-50: melodic phrase and sustained notes
            Step(304, 7, length=1),
            Step(306, 9, length=1),
            Step(308, 11, length=2),
            Step(312, 7, length=4),
            Step(320, 4, length=2),
            Step(324, 7, length=2),
            Step(328, 9, length=2),
            Step(332, 7, length=2),
            Step(336, 4, length=2),
            Step(340, 7, length=2),
            Step(344, 9, length=2),
            Step(348, 7, length=2),
            Step(352, 2, length=2),
            Step(356, 4, length=2),
            Step(360, 7, length=2),
            Step(364, 4, length=2),
            # Measures 51-52: phrase continuation
            Step(368, 7, length=2),
            Step(372, 9, length=2),
            Step(376, 11, length=2),
            Step(380, 9, length=2),
            Step(384, 7, length=2),
            Step(388, 4, length=2),
            Step(392, 2, length=2),
            Step(396, 4, length=2),
            Step(400, 7, length=2),
            Step(404, 4, length=2),
            Step(408, 2, length=2),
            Step(412, 0, length=4),
            # Page 3: measures 53-57 (rough draft, not verified note-by-note)
            Step(416, 7, length=1),
            Step(418, 9, length=1),
            Step(420, 7, length=1),
            Step(422, 4, length=2),
            Step(426, 2, length=1),
            Step(428, 4, length=1),
            Step(430, 7, length=2),
            Step(432, 4, length=1),
            Step(434, 7, length=1),
            Step(436, 9, length=1),
            Step(438, 7, length=1),
            Step(440, 4, length=2),
            Step(444, 2, length=2),
            Step(448, 0, length=1),
            Step(450, 2, length=1),
            Step(452, 4, length=1),
            Step(456, 7, length=2),
            Step(460, 4, length=1),
            Step(462, 2, length=1),
            Step(464, 0, length=2),
            Step(468, -5, length=1),
            Step(470, 0, length=1),
            Step(472, 4, length=1),
            Step(476, 7, length=2),
            Step(480, 7, length=4),
            Step(484, 7, length=1),
            Step(486, 9, length=1),
            Step(488, 11, length=1),
            Step(492, 9, length=1),
            # Measure 58 onward: score indicates a tempo change to 85 BPM
            Step(496, 7, length=1),
            Step(498, 4, length=1),
            Step(500, 2, length=1),
            Step(504, 4, length=1),
            Step(506, 2, length=1),
            # Measures 59-62
            Step(512, 0, length=2),
            Step(516, 4, length=1),
            Step(518, 2, length=1),
            Step(520, 0, length=2),
            Step(528, 7, length=1),
            Step(530, 9, length=1),
            Step(532, 7, length=2),
            Step(536, 4, length=2),
            Step(540, 2, length=2),
            Step(544, 7, length=1),
            Step(546, 9, length=1),
            Step(548, 11, length=2),
            Step(552, 9, length=2),
            Step(556, 7, length=2),
            Step(560, 4, length=2),
            Step(564, 7, length=2),
            Step(568, 9, length=2),
            Step(572, 7, length=2),
            # Measures 63-65: approximate closing phrase
            Step(576, 7, length=2),
            Step(580, 9, length=1),
            Step(582, 7, length=1),
            Step(584, 4, length=2),
            Step(588, 2, length=2),
            Step(592, 0, length=4),
            Step(600, 4, length=2),
            Step(604, 2, length=2),
            # Approximate final cadence. Score ends with ritardando and fermata.
            Step(608, 0, length=4),
            Step(616, 7, length=4),
            Step(624, 0, length=8),
        ),
    )


class FlutePhrases(Catalog):
    """What the flute's Pattern dropdown offers: its tunes, then every hook and
    lead a wind line already plays."""

    sources = (FluteTunes, Phrases.for_roles(PhraseRole.HOOK, PhraseRole.LEAD))
