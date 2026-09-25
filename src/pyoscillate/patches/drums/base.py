"""Drums-archetype name for the shared gated-voice base.

Every gated drum voice (kick, snare, clap, hat, ...) follows the same shape
`GatedVoice` (`pyoscillate.patches.common`) factors out: one `Trig()` fires
per hit, one or more `TrigEnv`s read a break-point table off it, and a
`Clock` `Division` schedules the hit with a live `rate` control. That shape
isn't drums-specific - `tonal.bass.base.Bass` builds on the same base - so
this module just gives the drums family its own name for it, matching
`patches/CLAUDE.md`'s directory-level-base convention.
"""

from __future__ import annotations

from pyoscillate.patches.common import GatedVoice, semitone_ratio

__all__ = ["DrumVoice", "semitone_ratio"]


class DrumVoice(GatedVoice):
    """Base for a gated drums-archetype voice. See `GatedVoice` for the
    shared `self.envelope(...)`/`self.schedule(...)`/`self.finish(...)`
    contract every concrete voice builds on."""
