"""Pluck patch family: clocked, articulated pitched voices.

`pluck` is the FM pluck; `string` is the Karplus-Strong base the plucked
instruments share (`guitar`, `folk`, `harp`, `sitar`)."""

from pyoscillate.patches.tonal.pluck import folk, guitar, harp, pluck, sitar, string

__all__ = ["folk", "guitar", "harp", "pluck", "sitar", "string"]
