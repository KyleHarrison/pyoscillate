"""Woodwind patch family: held, blown pipes.

`wind` holds the shared base (`Wind`); `flute` the jet-driven flutes and their
tunes, `reed` the single and double reeds and `lip` the buzzed pipes and
shells."""

from pyoscillate.patches.tonal.woodwind import flute, lip, reed, wind

__all__ = ["flute", "lip", "reed", "wind"]
