"""Patch definitions for the dark, slowed-and-reverbed lofi rack."""

from __future__ import annotations

from pyoscillate.controller import GroupController
from pyoscillate.patches.texture.noise import noise
from pyoscillate.patches.tonal.bass import hover as bass
from pyoscillate.patches.tonal.drone import wash
from pyoscillate.patches.utility.notes import notes
from pyoscillate.projects.base import Rack

# the rack's E Phrygian centre - no `Harmony` object, because neither patch
# here follows a chord: the bass hovers on a fixed tonic (see `bass.hover`'s
# module docstring) and the pad holds a static register. See README.md's
# "Shared harmony and tempo".
ROOT_NOTE = notes.E1


class SlowedReverbRack(Rack):
    """Dark, slowed, bass-dominant lofi rack: a hovering sine-like bass
    under a long, breathing reverb tail, a dark reverberant pad wash, and a
    quiet, dusty texture bed - see README.md for the reference-track
    grounding behind this brief."""

    # felt tempo from the reference track's half-time drag (see README.md)
    bpm = 61
    needs_clock = True

    def build_groups(self) -> tuple[GroupController, ...]:
        return (
            # foreground: carries ~87% of the reference's RMS - see
            # `bass.hover.BassHover`'s own long reverb tail and breathing
            # swell, which is this rack's main "dark, reverberant" carrier
            GroupController(
                "bass",
                "Bass",
                (bass.BassHover(root_freq=ROOT_NOTE),),
            ),
            # a static, dark reverberant pad bed under the bass - reused
            # unmodified from `tonal/drone`'s existing wash style, just
            # re-tuned dark and distant (see README.md's mapping table)
            GroupController(
                "pad",
                "Pad",
                (
                    wash.SoundscapeWash(
                        root_freq=notes.E2,
                        detune=0.4,
                        detune_bal=0.55,
                        chorus_depth=1.0,
                        chorus_feedback=0.2,
                        chorus_bal=0.35,
                        reverb_size=0.92,
                        reverb_damp=0.65,
                        reverb_bal=0.85,
                        delay_time=1.2,
                        delay_feedback=0.2,
                        volume=0.3,
                    ),
                ),
            ),
            # quiet, dusty texture bed - reused unmodified from the
            # `boom_bap` sibling's own atmosphere layer, darkened further to
            # match this brief's ~850 Hz mix-wide rolloff
            GroupController(
                "texture",
                "Texture",
                (
                    noise.NoiseDust(
                        brightness=700,
                        colour=1.7,
                        motion=0.3,
                        depth=0.15,
                        level=0.12,
                    ),
                ),
            ),
        )
