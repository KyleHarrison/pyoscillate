# Theory refactor: TODO

Each phase is meant to run in its own Claude Code session. Finish a phase
(tests + `uv run ruff check src` green, ted) before starting the next.
Start each session with: "Do Phase N of docs/THEORY_REFACTOR_TODO.md".

Follow `src/pyoscillate/AGENTS.md`: no module-level variables or functions,
everything is a class attribute or method. Run Python with `uv run`.

## Decisions (already made)

- Saved presets are **deleted**, not migrated. Dropdown values become stable
  string ids, so no index-compat constraints ("only ever append") apply.
- Notes become a plain-float class (`Note.F3`), no enum, no 120 aliases.
- Pitch/phrase/chord definitions are dataclasses with named fields, never
  positional tuples.

## Problems being fixed

- `Harmony` is mutable runtime state (key/progression/scale) read by every
  patch, but lives in `theory/` and documents itself as rack-level.
- `notes.py`: 120 enum members + 120 duplicate float aliases.
- `intervals.py` (930 lines) mixes: dropdown base (`Choice`), scales, chord
  shapes (`ChordShape` semitones, `Voicing` degrees), `Progression`, and five
  phrase families.
- `Rhythm`, `Melody`, `ChordTones`, `ArpOrder`, `Walk` are one concept: steps
  whose offset means different things. Stored as positional tuples decoded
  with `len(entry) > 2`.
- Flat, huge dropdowns (Melody mixes bass/bell/fill; Voicing ~75 entries;
  patch "Style" selector flat).

## Target layout

```
src/pyoscillate/
  harmony.py            Harmony state (moved out of theory/, beside clock.py/tempo.py)
  theory/
    pitch.py            Note (plain float class attrs), midi_to_freq, freq_to_midi,
                        semitone_ratio, transpose, nearest_note, note_name, NOTE_NAMES
    interval.py         Interval IntEnum: UNISON=0 ... OCTAVE=12 (named semitones)
    scale.py            Scale (name, offsets) + voice/degree/snap
    chord.py            Chord(name, offsets, unit=SEMITONES|DEGREES, category)
    progression.py      Progression(name, roots, numerals)
    catalog.py          Catalog base (replaces Choice): id, label, category,
                        by_id, grouped options
    phrase/
      base.py           Step(at, offset=0, accent=1.0, length=1.0, open=False)
                        Phrase(division, cycle, steps, label, role, mode)
                        PhraseMode: NONE | SEMITONES | CHORD_TONE | POOL_INDEX
      rhythm.py bass.py lead.py arp.py fill.py ...   members grouped by role
```

---

## Phase 1: Foundations and migration

Goal: new theory modules exist, every patch/rack/UI import is migrated,
behaviour unchanged, old modules deleted.

- [x] Delete preset JSON: `src/flet/forest_psytrance/presets/forest.json` and
      any other `presets/*.json`; keep the dirs creatable (`PresetStore`
      does `mkdir`). Check `git ls-files | grep presets`.
- [x] `theory/pitch.py`: `Note` as plain float class attributes C0..B10
      (pyo rejects enum members), plus the math helpers from `notes.py`.
      Replace every `notes.X` / `from ...notes import ...` (grep
      `pyoscillate.theory`) with `Note.X`; update AGENTS.md rule that names
      `theory/notes.py`.
- [x] `theory/interval.py`: `Interval` IntEnum; use it inside phrase/chord
      definitions instead of bare ints where a musical interval is meant.
- [x] `theory/scale.py`, `theory/chord.py` (merge `ChordShape` + `Voicing`;
      `unit` says semitones vs scale degrees; carry `category` from the
      existing section comments: Basic, Open, Spread, House, Trance, Dark,
      Quartal, Cluster, Comping, ...), `theory/progression.py`.
- [x] `theory/catalog.py`: `Catalog` base with stable string `id` per member
      (replaces `Choice.by_index/index/labels`). `choice_param` in
      `patches/params.py` stores the id (Param value stays numeric for sliders
      today, so decide: either keep an index internally derived from the
      catalog's order and persist the id, or extend `Param`; check
      `patches/params.py` and `flet/base.py` preset save/load).
- [x] `theory/phrase/base.py`: `Step`, `Phrase`, `PhraseMode`. Port every
      `Rhythm`/`Melody`/`ChordTones`/`ArpOrder`/`Walk` member to
      `Phrase(...)` with `Step(...)` fields, grouped into role modules.
      Walk members become POOL_INDEX/SEMITONES phrases of consecutive steps.
      Remove tuple decoding (`entry[2] if len(entry) > 2 ...`).
- [x] `harmony.py`: move `Harmony` here; `Harmony.progression` takes only
      `Progression | tuple[int, ...]` as today. Fix its docstring: it is
      per-rack state *passed to* patches via `BuildContext`; verify
      `patches/base.py` and each patch's `harmony` handling and say what is
      actually true. Move key constants `C`, `F`, `A` onto `Note`/`Harmony`
      as class attributes.
- [x] Collapse `Rhythmic`/`Melodic`/`Figured` in `patches/common.py` into one
      `Phrased` mixin (`phrase` param, `selected_phrase`, `use_phrase`) that
      branches on `Phrase.mode` where pitch is resolved.
- [x] Update call sites (~95 refs + `flet/base.py` Progression/NOTE_NAMES,
      `analysis/render.py`, `projects/*/rack.py`, tests).
- [x] Delete `theory/intervals.py`, `theory/notes.py`; `theory/__init__.py`
      docstring updated.
- [x] `uv run pytest` and `uv run ruff check src` pass; .

## Phase 2: Role/category filtering of pattern dropdowns

Goal: a patch only offers phrases/chords relevant to it.

- [ ] Define `role` values (e.g. KICK, SNARE, HAT, PERC, BASS, LEAD, BELL,
      FILL, CHORD_HIT, ARP, DRONE) as a `PhraseRole` enum in
      `theory/phrase/base.py`.
- [ ] `Phrased` mixin gets `phrase_roles: ClassVar[tuple[PhraseRole, ...]]`;
      `choice_param` offers only catalog members whose role is accepted.
      Set it on every gated patch (drums, bass, lead, keys, stab, bell, tom).
- [ ] `Catalog.options` returns grouped data (`category -> members`); extend
      `SliderSpec.options` or add `grouped_options` for large catalogs.
- [ ] Flet `choice` control (`flet/base.py` ~line 284): when a catalog has
      more than one category and more than ~12 members, render a Category
      dropdown plus an Item dropdown filtered to it. Small catalogs stay one
      dropdown. Use the flet MCP (`get_api`) to check Dropdown API.
- [ ] Apply to Chord/Voicing params (stab, lead) and Progression.
- [ ] Tests for filtering; ruff; .

## Phase 3: Categorised patch selector

Goal: the group "Style" dropdown (`PatchGroup` in `flet/base.py`, ~line 611)
is no longer one flat list.

- [ ] Add `category` (and optional `subcategory`) to `Patch` (class attr);
      fill it for every patch under `src/pyoscillate/patches/**`
      (drums/tonal/musical/texture/transition/pitched_percussion/utility).
- [ ] `GroupController` alternatives expose their panels' categories.
- [ ] `PatchGroup`: Category dropdown + Style dropdown filtered by it; hide the
      category dropdown when all alternatives share one category.
- [ ] Same treatment for the standalone patch app picker
      (`src/flet/patch/app.py`) if it lists patches flat.
- [ ] Update `tests/test_flet_patch_groups.py`; update patch/project
      AGENTS.md docs describing the selector; ruff; .

## Phase 4 (optional cleanup)

- [ ] Update `SKILL.md`, `.claude/skills/*`, `README.md`, and the patches/
      projects `AGENTS.md` files for the new module names.
- [ ] Grep for stale names: `Choice`, `Rhythm.`, `Melody.`, `ChordTones`,
      `ArpOrder`, `Walk`, `Voicing`, `intervals`, `theory.notes`.
