"""Patch definitions for the clock-locked lofi hip-hop rack."""

from pyoscillate.harmony import C, Harmony
from pyoscillate.patches.base import Patch
from pyoscillate.patches.drums.hat import groove as hat
from pyoscillate.patches.drums.kick import kick
from pyoscillate.patches.drums.snare import snare
from pyoscillate.patches.texture.noise import noise
from pyoscillate.patches.tonal.bass import groove as bass
from pyoscillate.patches.tonal.keys import keys
from src.flet.base import PatchGroupDef

# this project's own tempo and clock timing resolution - other projects set
# their own values instead of sharing a static default from `pyoscillate.clock`
BPM = 80
# matches deep_house's convention: fine enough for the swung 32nd-note
# patterns (drums/kick, drums/snare, drums/hat's `lofi` styles) to land exactly
TICKS_PER_BAR = 512
# the rack's shared key and vamp: Dm9-G13-Cmaj7-Am9, one chord per bar, four
# bars per loop - a static, jazz-influenced ii9-V13-Imaj9-vi9 in the key of C
# major (D=ii, G=V, C=I, A=vi), rather than a developing song form. The keys
# and bass patches both re-root on this on the same bar from the shared
# clock, so they change chord together regardless of their own Rate sliders
HARMONY = Harmony(key=C, progression=(2, 7, 0, 9), bars_per_chord=1)

PATCHES: dict[str, tuple[Patch, ...]] = {
    "keys": (keys.Keys(),),
    "bass": (bass.BassMuted(),),
    "noise": (noise.NoiseDust(),),
    "kick": (kick.KickLofi(),),
    "snare": (snare.SnareLofi(),),
    "hat": (hat.GrooveLofi(),),
}

GROUP_TITLES: dict[str, str] = {
    "keys": "Keys",
    "bass": "Bass",
    "noise": "Vinyl Dust",
    "kick": "Kick",
    "snare": "Snare",
    "hat": "Hi-hat",
}

PATCH_GROUPS: list[PatchGroupDef] = [
    PatchGroupDef(key, GROUP_TITLES[key], patches) for key, patches in PATCHES.items()
]
