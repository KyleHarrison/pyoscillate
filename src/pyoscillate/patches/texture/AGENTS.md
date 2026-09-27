# Texture

## Sonic function

A texture is an ungated, continuous layer with no stable pitch centre: noise, many small events, grains, or chaos used as timbre. It emphasizes the material itself. Unpitched low-end rumble belongs here, not in `tonal/bass`.

If the layer holds a pitch centre, it is a drone (`tonal/drone`). A soundscape is not a texture either: it is a rack-level arrangement of layers (textures, drones, and foreground events) and belongs in a project rack, not a patch family. Environmental sources such as wind, rain, or water are textures that a soundscape rack can arrange.

## Minimal architecture

many small sources or noisy elements
→ spectral shaping
→ modulation or randomness
→ density control
→ optional filtering or spatial treatment

## Core design idea

Texture asks:

- how dense is the layer?
- how much motion occurs in the spectrum?
- is it grainy, noisy, airy, or metallic?
- is the variation periodic or stochastic?

This family is useful for backgrounds, movement layers, and evolving tone mass rather than for single-note identity.

## Parameter logic

Common parameters include:

- density: how crowded or full the texture feels
- brightness: how much high-end energy is exposed
- motion: slow drift vs. faster shimmer
- grain: the coarse or smooth quality of the events
- space: how much the material dissolves into the room

## Design alternatives

Airy texture:
    high-pass or filtered noise + slow modulation + moderate reverb

Dense texture:
    layered harmonics/noise + more motion + little separation

Metallic texture:
    partial-rich source + brighter contour + short irregular events

## What NOT to assume

Texture is not a synonym for ambience. It is broader and more direct: a material that evolves, drifts, or shimmers, whether or not it is meant to suggest a physical place.

## Musical references

These point to the music-theory layer for decisions *around* this voice
(pattern, pitch material, role in the arrangement and mix). They do not
cover synthesis; the sections above stay authoritative for the DSP.

- `.claude/skills/music-theory/references/orchestration/arrangement-density.md` — density as an arrangement arc (the musical counterpart to this family's `density` control)
- `.claude/skills/music-theory/references/production-aware/energy-and-dynamics.md` — "Reverb and delay — atmosphere", for the `space` dimension
- `.claude/skills/music-theory/references/techniques/20th-century-techniques.md` — "Spectralism", "Aleatoric / chance music" and "Minimalism and process music", for stochastic vs. periodic variation and evolving tone mass
- `.claude/skills/music-theory/references/genres/game-music.md` — "Looping" / "Avoiding loop fatigue" and "Vertical layering", for long-running background layers
- `.claude/skills/music-theory/references/genres/film-tv-scoring.md` — "Underscoring", for textures that support without taking focus

Note: "texture" in `orchestration/voicing-and-texture.md` means monophony/homophony/polyphony, which is a different concept from this family.
