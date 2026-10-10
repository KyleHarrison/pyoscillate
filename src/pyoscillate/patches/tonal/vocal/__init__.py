"""Vocal patch family: held, sung voices.

`singer` holds the shared bases (`Singer`, `FormantSinger`); `solo` the solo
voices, `ensemble` the choirs and `whistling` the whistle."""

from pyoscillate.patches.tonal.vocal import ensemble, singer, solo, whistling

__all__ = ["ensemble", "singer", "solo", "whistling"]
