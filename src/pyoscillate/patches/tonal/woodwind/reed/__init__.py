"""Reed winds: a reed driving a cylindrical or conical bore.

`reed` holds the shared base (`ReedWind`); `single` the clarinets, `double` the
oboes and bassoons and `bagpipes` the chanter with a drone."""

from pyoscillate.patches.tonal.woodwind.reed import bagpipes, double, reed, single

__all__ = ["bagpipes", "double", "reed", "single"]
