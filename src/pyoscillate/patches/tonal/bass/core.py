"""Shared building blocks for clocked monophonic bass voices."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from pyo.lib.filters import MoogLP
from pyo.lib.generators import LFO
from pyo.lib.tableprocess import Osc
from pyo.lib.tables import CosTable, HarmTable
from pyo.lib.triggers import Trig, TrigEnv

from pyoscillate.clock import Clock, NoteDivision
from pyoscillate.patches.base import Patch
from pyoscillate.tempo import Tempo

BASE_DIVISION = NoteDivision.SIXTEENTH


@dataclass(frozen=True)
class BassProfile:
    """Musical and perceptual policy for one bass voice."""

    pattern: tuple[int, ...]
    accents: tuple[float, ...]
    envelope_decay: float
    resonance: float
    harmonics: tuple[float, ...] = (1.0, 0.32, 0.18, 0.1)


def build_bass(
    tempo: Tempo,
    clock: Clock,
    profile: BassProfile,
    root_freq: float,
    cutoff: float,
    rate: float = 0,
    *,
    filter_base: float | None = None,
    filter_range: float = 0,
    filter_res: float | None = None,
) -> Patch:
    """Build a triggered pitch voice from a musical profile.

    A fixed ``cutoff`` gives a compact, controlled bass. Supplying
    ``filter_base`` and ``filter_range`` adds a bar-long continuous sweep,
    which is useful for a more animated techno voice.
    """
    if len(profile.pattern) != len(profile.accents):
        raise ValueError("Bass pattern and accent pattern must have equal lengths")

    trigger = Trig()
    envelope_table = CosTable([(0, 0), (80, 1), (2100, 0.5), (8191, 0)])
    envelope = TrigEnv(
        trigger,
        table=envelope_table,
        dur=tempo.sixteenth * profile.envelope_decay,
    )
    oscillator_table = HarmTable(list(profile.harmonics))
    oscillator = Osc(
        oscillator_table,
        freq=root_freq,
        mul=envelope,
    )

    cutoff_lfo: Any | None = None
    if filter_base is None:
        cutoff_source: Any = cutoff
    else:
        cutoff_lfo = LFO(
            freq=1 / tempo.bar,
            type=0,
            mul=filter_range,
            add=filter_base,
        )
        cutoff_source = cutoff_lfo

    voice = MoogLP(
        oscillator,
        freq=cutoff_source,
        res=profile.resonance if filter_res is None else filter_res,
    )
    state = {"step": 0, "root": root_freq}

    def next_step() -> None:
        step = state["step"] % len(profile.pattern)
        oscillator.freq = state["root"] * 2 ** (profile.pattern[step] / 12)
        envelope.mul = profile.accents[step]
        trigger.play()
        state["step"] += 1

    controls = {
        "root_freq": lambda value: state.update(root=value),
        "cutoff": lambda value: setattr(voice, "freq", value),
    }
    if filter_base is not None and cutoff_lfo is not None:
        controls.update(
            {
                "filter_base": lambda value: setattr(cutoff_lfo, "add", value),
                "filter_range": lambda value: setattr(cutoff_lfo, "mul", value),
            }
        )
    if filter_res is not None:
        controls["filter_res"] = lambda value: setattr(voice, "res", value)

    division = clock.subscribe(clock.ticks_for_rate(BASE_DIVISION, rate), next_step)
    controls["rate"] = lambda value: setattr(
        division, "steps", clock.ticks_for_rate(BASE_DIVISION, value)
    )
    return Patch(
        sequencer=division,
        voice=voice,
        controls=controls,
        resources=(
            trigger,
            envelope_table,
            envelope,
            oscillator_table,
            oscillator,
            cutoff_lfo,
        ),
    )
