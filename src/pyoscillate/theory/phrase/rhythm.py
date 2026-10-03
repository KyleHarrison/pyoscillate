"""Hit patterns for drums and chord-striking patches."""

from __future__ import annotations

from pyoscillate.clock import NoteDivision
from pyoscillate.theory.catalog import Catalog
from pyoscillate.theory.phrase.base import Phrase, PhraseMode, PhraseRole, Step


class Rhythms(Catalog):
    """Hit patterns for any percussive or chord-striking patch: a `PhraseMode.NONE` phrase says when to hit and how hard. Where a voice maps velocity to brightness (see `Keys`), the accents shape the timbre as well as the level; a step marked `open` is a hat that rings open rather than closed."""

    # beat one, then the "and" of two
    CHARLESTON = Phrase(
        division=NoteDivision.SIXTEENTH,
        cycle=16,
        label="Charleston: beat 1 and the 'and' of 2",
        mode=PhraseMode.NONE,
        category="Comping",
        roles=(PhraseRole.CHORD_HIT,),
        steps=(
            Step(0),
            Step(6, accent=0.55),
        ),
    )
    # a stab on every beat, the downbeats strongest
    FOUR_ON_THE_FLOOR = Phrase(
        division=NoteDivision.SIXTEENTH,
        cycle=16,
        label="Four on the floor: every beat",
        mode=PhraseMode.NONE,
        category="Pulse",
        roles=(PhraseRole.CHORD_HIT, PhraseRole.KICK),
        steps=(
            Step(0),
            Step(4, accent=0.7),
            Step(8, accent=0.85),
            Step(12, accent=0.7),
        ),
    )
    # the "and" of every beat, the house offbeat
    OFFBEAT_HOUSE = Phrase(
        division=NoteDivision.SIXTEENTH,
        cycle=16,
        label="Offbeat house: every 'and'",
        mode=PhraseMode.NONE,
        category="Comping",
        roles=(PhraseRole.CHORD_HIT, PhraseRole.HAT, PhraseRole.PERC),
        steps=(
            Step(2, accent=0.9),
            Step(6, accent=0.8),
            Step(10, accent=0.9),
            Step(14, accent=0.8),
        ),
    )
    # one chord a bar, left to ring
    WHOLE_BAR = Phrase(
        division=NoteDivision.SIXTEENTH,
        cycle=16,
        label="Whole bar: one hit a bar",
        mode=PhraseMode.NONE,
        category="Pulse",
        roles=(PhraseRole.CHORD_HIT,),
        steps=(Step(0),),
    )
    # pushes ahead of beats two and four
    SYNCOPATED_PUSH = Phrase(
        division=NoteDivision.SIXTEENTH,
        cycle=16,
        label="Syncopated push: ahead of the beat",
        mode=PhraseMode.NONE,
        category="Comping",
        roles=(PhraseRole.CHORD_HIT,),
        steps=(
            Step(0),
            Step(5, accent=0.6),
            Step(8, accent=0.8),
            Step(11, accent=0.55),
        ),
    )
    # one full-level hit per beat: the classic kick pulse
    QUARTER_PULSE = Phrase(
        division=NoteDivision.QUARTER,
        cycle=1,
        label="Quarter pulse: a hit on every beat",
        mode=PhraseMode.NONE,
        category="Pulse",
        roles=(PhraseRole.KICK, PhraseRole.HAT, PhraseRole.PERC, PhraseRole.CHORD_HIT),
        steps=(Step(0),),
    )
    # one hit per half-beat: a steady ticking hat
    EIGHTH_PULSE = Phrase(
        division=NoteDivision.EIGHTH,
        cycle=1,
        label="Eighth pulse: a hit on every half-beat",
        mode=PhraseMode.NONE,
        category="Pulse",
        roles=(PhraseRole.HAT, PhraseRole.PERC, PhraseRole.CHORD_HIT),
        steps=(Step(0),),
    )
    # beats two and four, the backbeat a clap or snare accents
    BACKBEAT = Phrase(
        division=NoteDivision.SIXTEENTH,
        cycle=16,
        label="Backbeat: beats 2 and 4",
        mode=PhraseMode.NONE,
        category="Backbeat",
        roles=(PhraseRole.SNARE, PhraseRole.PERC),
        steps=(
            Step(4),
            Step(12),
        ),
    )
    # the backbeat with a quiet ghost note on the last 16th of the bar
    BACKBEAT_GHOST = Phrase(
        division=NoteDivision.SIXTEENTH,
        cycle=16,
        label="Backbeat with a ghost: beats 2 and 4, a soft pickup",
        mode=PhraseMode.NONE,
        category="Backbeat",
        roles=(PhraseRole.SNARE,),
        steps=(
            Step(4),
            Step(12),
            Step(15, accent=0.3),
        ),
    )
    # the last 16th of every beat, a tight woody rim-click figure
    RIM_OFFBEATS = Phrase(
        division=NoteDivision.SIXTEENTH,
        cycle=16,
        label="Rim offbeats: the last 16th of every beat",
        mode=PhraseMode.NONE,
        category="Percussion",
        roles=(PhraseRole.PERC,),
        steps=(
            Step(3),
            Step(7),
            Step(11),
            Step(15),
        ),
    )
    # a loose, syncopated conga figure
    CONGA_SYNCOPATED = Phrase(
        division=NoteDivision.SIXTEENTH,
        cycle=16,
        label="Conga syncopation: five loose hits a bar",
        mode=PhraseMode.NONE,
        category="Percussion",
        roles=(PhraseRole.PERC,),
        steps=(
            Step(3),
            Step(6),
            Step(9),
            Step(11),
            Step(14),
        ),
    )
    # a quarter-note ride, the downbeat and beat three strongest
    RIDE_QUARTERS = Phrase(
        division=NoteDivision.SIXTEENTH,
        cycle=16,
        label="Ride quarters: a hit on every beat",
        mode=PhraseMode.NONE,
        category="Cymbal",
        roles=(PhraseRole.CYMBAL, PhraseRole.HAT),
        steps=(
            Step(0),
            Step(4, accent=0.8),
            Step(8, accent=0.9),
            Step(12, accent=0.8),
        ),
    )
    # one crash at the start of an eight-bar phrase
    CRASH_PHRASE = Phrase(
        division=NoteDivision.SIXTEENTH,
        cycle=128,
        label="Crash phrase: one hit every eight bars",
        mode=PhraseMode.NONE,
        category="Cymbal",
        roles=(PhraseRole.CYMBAL,),
        steps=(Step(0),),
    )
    # hats: closed 16ths on the "and" of every beat
    HAT_CRISP = Phrase(
        division=NoteDivision.SIXTEENTH,
        cycle=16,
        label="Crisp hats: closed on every 'and'",
        mode=PhraseMode.NONE,
        category="Hats",
        roles=(PhraseRole.HAT,),
        steps=(
            Step(2),
            Step(6),
            Step(10),
            Step(14),
        ),
    )
    # open offbeats choked by a closed ghost on the last 16th
    HAT_OPEN = Phrase(
        division=NoteDivision.SIXTEENTH,
        cycle=16,
        label="Open hats: ringing offbeats choked on the last 16th",
        mode=PhraseMode.NONE,
        category="Hats",
        roles=(PhraseRole.HAT,),
        steps=(
            Step(2, open=True),
            Step(6, open=True),
            Step(10, open=True),
            Step(14, open=True),
            Step(15, accent=0.66),
        ),
    )
    # loosely shuffled, syncopated hats ending on an open hit
    HAT_SHUFFLE = Phrase(
        division=NoteDivision.SIXTEENTH,
        cycle=16,
        label="Shuffle hats: syncopated, ending open",
        mode=PhraseMode.NONE,
        category="Hats",
        roles=(PhraseRole.HAT,),
        steps=(
            Step(2),
            Step(5, accent=0.66),
            Step(6),
            Step(10),
            Step(13, accent=0.66),
            Step(14, open=True),
        ),
    )
    # quiet open offbeats choked by softer closed ghosts, a background shimmer
    HAT_FOREST = Phrase(
        division=NoteDivision.SIXTEENTH,
        cycle=16,
        label="Forest hats: quiet open offbeats choked by ghosts",
        mode=PhraseMode.NONE,
        category="Hats",
        roles=(PhraseRole.HAT,),
        steps=(
            Step(2, accent=0.6, open=True),
            Step(3, accent=0.25),
            Step(6, accent=0.6, open=True),
            Step(7, accent=0.25),
            Step(10, accent=0.6, open=True),
            Step(11, accent=0.25),
            Step(14, accent=0.7, open=True),
            Step(15, accent=0.3),
        ),
    )
    # 32nd-note steps (8 per beat). Each beat keeps its downbeat and "and"
    # on the grid but delays the weak "e"/"a" 16ths by one 32nd (to 3 and 7)
    # for an MPC-style swing, each a quiet ghost hit; the bar's last "a"
    # opens to breathe before the loop restarts
    HAT_LOFI = Phrase(
        division=NoteDivision.THIRTYSECOND,
        cycle=32,
        label="Lofi hats: swung 16ths with ghost notes",
        mode=PhraseMode.NONE,
        category="Hats",
        roles=(PhraseRole.HAT,),
        steps=(
            Step(0),
            Step(3, accent=0.4),
            Step(4, accent=0.75),
            Step(7, accent=0.4),
            Step(8, accent=0.85),
            Step(11, accent=0.4),
            Step(12, accent=0.75),
            Step(15, accent=0.4),
            Step(16),
            Step(19, accent=0.4),
            Step(20, accent=0.75),
            Step(23, accent=0.4),
            Step(24, accent=0.85),
            Step(27, accent=0.4),
            Step(28, accent=0.55, open=True),
        ),
    )
    # the lofi hats with the straight 16ths filled in as faint ghosts
    HAT_LOFI_FULL = Phrase(
        division=NoteDivision.THIRTYSECOND,
        cycle=32,
        label="Lofi hats, full: swung 16ths with every ghost filled in",
        mode=PhraseMode.NONE,
        category="Hats",
        roles=(PhraseRole.HAT,),
        steps=(
            Step(0),
            Step(2, accent=0.25),
            Step(3, accent=0.4),
            Step(4, accent=0.75),
            Step(6, accent=0.3),
            Step(7, accent=0.4),
            Step(8, accent=0.85),
            Step(10, accent=0.25),
            Step(11, accent=0.4),
            Step(12, accent=0.75),
            Step(14, accent=0.3),
            Step(15, accent=0.4),
            Step(16),
            Step(18, accent=0.25),
            Step(19, accent=0.4),
            Step(20, accent=0.75),
            Step(22, accent=0.3),
            Step(23, accent=0.4),
            Step(24, accent=0.85),
            Step(26, accent=0.25),
            Step(27, accent=0.4),
            Step(28, accent=0.55, open=True),
        ),
    )
    # 32nd-note steps. Beat one's downbeat is full; the syncopated "and" of
    # beat two lands on step 13 instead of the straight 12, one 32nd late (a
    # 5:3 swing ratio), and a quiet ghost flicks in a 32nd behind beat 4's
    # "a" - both just behind the grid for a laid-back boom-bap pocket
    KICK_LOFI = Phrase(
        division=NoteDivision.THIRTYSECOND,
        cycle=32,
        label="Lofi kick: boom-bap with a swung 'and' and a ghost",
        mode=PhraseMode.NONE,
        category="Lofi",
        roles=(PhraseRole.KICK,),
        steps=(
            Step(0),
            Step(13, accent=0.85),
            Step(31, accent=0.3),
        ),
    )
    # the lofi kick with two softer fills
    KICK_LOFI_FULL = Phrase(
        division=NoteDivision.THIRTYSECOND,
        cycle=32,
        label="Lofi kick, full: boom-bap with extra soft hits",
        mode=PhraseMode.NONE,
        category="Lofi",
        roles=(PhraseRole.KICK,),
        steps=(
            Step(0),
            Step(8, accent=0.45),
            Step(13, accent=0.85),
            Step(24, accent=0.55),
            Step(31, accent=0.3),
        ),
    )
    # 32nd-note steps. The backbeat on beats 2 and 4 (straight would be 8 and
    # 24) lands one 32nd late, at 9 and 25, for a behind-the-beat pocket; a
    # soft pickup ghost sits before beat 2 and a quieter one swings into the
    # loop before beat 1
    SNARE_LOFI = Phrase(
        division=NoteDivision.THIRTYSECOND,
        cycle=32,
        label="Lofi snare: a late backbeat with ghost notes",
        mode=PhraseMode.NONE,
        category="Lofi",
        roles=(PhraseRole.SNARE,),
        steps=(
            Step(6, accent=0.25),
            Step(9),
            Step(25),
            Step(30, accent=0.3),
        ),
    )
    # one hit at the top of every bar: a whole-bar re-articulation
    BAR_PULSE = Phrase(
        division=NoteDivision.WHOLE,
        cycle=1,
        label="Bar pulse: a hit at the top of every bar",
        mode=PhraseMode.NONE,
        category="Pulse",
        roles=(PhraseRole.CHORD_HIT, PhraseRole.CYMBAL),
        steps=(Step(0),),
    )
