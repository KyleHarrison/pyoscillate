"""Keys patch family: keyboards.

`keys` is the FM electric piano and the `FmKeys` base it shares with `celeste`;
`string_keys` holds the keyboards with strings (piano, harpsichord, clavichord);
`sustained` is the base of the held keyboards `organ` and `accordion`."""

from pyoscillate.patches.tonal.keys import (
    accordion,
    celeste,
    keys,
    organ,
    string_keys,
    sustained,
)

__all__ = ["accordion", "celeste", "keys", "organ", "string_keys", "sustained"]
