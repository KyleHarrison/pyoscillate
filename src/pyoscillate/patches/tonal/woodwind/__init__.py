"""Woodwind patch family: held, blown pipes.

`wind` holds the shared base (`Wind`); the `flute` subpackage the jet-driven
flutes and their tunes."""

from pyoscillate.patches.tonal.woodwind import flute, wind

__all__ = ["flute", "wind"]
