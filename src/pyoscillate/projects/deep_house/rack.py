"""Patch definitions for the clock-locked deep-house rack."""

from pyoscillate.patches import deep_house
from src.flet.base import PatchDef

ROLE_SPECS = (
    ("kick", "Kick", "Four-on-the-floor foundation.", deep_house.KICK_PARAMETERS, 0.8),
    ("bass", "Bass", "16th-note low-end movement.", deep_house.BASS_PARAMETERS, 0.62),
    ("chord", "Chord Stab", "Offbeat minor-seventh harmony.", deep_house.CHORD_PARAMETERS, 0.4),
    ("hat", "Hat", "Offbeat and shuffled top texture.", deep_house.HAT_PARAMETERS, 0.25),
    (
        "percussion",
        "Percussion",
        "Clap, rim, or conga rhythmic color.",
        deep_house.PERC_PARAMETERS,
        0.28,
    ),
)

STYLE_LABELS = {
    "kick": (("round", "Round"), ("punch", "Punch"), ("soft", "Soft")),
    "bass": (("rolling", "Rolling"), ("dub", "Dub"), ("muted", "Muted")),
    "chord": (("velvet", "Velvet"), ("organ", "Organ"), ("shimmer", "Shimmer")),
    "hat": (("crisp", "Crisp"), ("open", "Open"), ("shuffle", "Shuffle")),
    "percussion": (("clap", "Clap"), ("rim", "Rim"), ("conga", "Conga")),
}


def _build_patch_defs() -> list[PatchDef]:
    definitions: list[PatchDef] = []
    for role, title, summary, parameters, volume in ROLE_SPECS:
        for style, label in STYLE_LABELS[role]:
            definitions.append(
                PatchDef(
                    name=f"{role}_{style}",
                    title=f"{title} - {label}",
                    summary=summary,
                    build=deep_house.make_builder(role, style),
                    parameters=parameters,
                    volume_default=volume,
                    needs_tempo=True,
                    needs_clock=True,
                )
            )
    return definitions


PATCH_DEFS: list[PatchDef] = _build_patch_defs()
