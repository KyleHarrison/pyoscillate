"""Clock-locked deep-house voices for the Deep House Rack application.

Each builder exposes three intentionally distinct styles: rounded/physical,
classic/organ-like, and brighter or more percussive alternatives. They share
the rack's tempo and clock, so their downbeats stay aligned when a patch is
rebuilt from the Flet controls.
"""

from __future__ import annotations

from collections.abc import Callable

from pyo.lib.effects import Chorus, Disto, Freeverb
from pyo.lib.filters import Biquad, ButHP, MoogLP
from pyo.lib.generators import Noise, Sine
from pyo.lib.tableprocess import Osc
from pyo.lib.tables import CosTable, HarmTable, SawTable
from pyo.lib.triggers import Trig, TrigEnv, TrigLinseg

from pyoscillate.clock import FOURTH, SIXTEENTH, Clock
from pyoscillate.patches.base import Patch
from pyoscillate.patches.widgets import SliderSpec
from pyoscillate.tempo import Tempo

KICK_PARAMETERS = (
    SliderSpec("level", 0.1, 1.0, 0.05, 0.62, "Level", "Kick body level."),
    SliderSpec("drive", 0.0, 0.8, 0.05, 0.12, "Drive", "Soft saturation amount."),
)
BASS_PARAMETERS = (
    SliderSpec("root_freq", 35, 82, 1, 55, "Root", "Bass root frequency in Hz."),
    SliderSpec("cutoff", 180, 2400, 20, 720, "Cutoff", "Bass low-pass cutoff."),
)
CHORD_PARAMETERS = (
    SliderSpec("root_freq", 90, 220, 1, 146, "Root", "Chord root frequency in Hz."),
    SliderSpec("brightness", 300, 5000, 50, 1500, "Brightness", "Chord low-pass cutoff."),
)
HAT_PARAMETERS = (
    SliderSpec("level", 0.02, 0.5, 0.01, 0.14, "Level", "Hat burst level."),
    SliderSpec("cutoff", 3500, 14000, 100, 9000, "Cutoff", "High-pass cutoff."),
)
PERC_PARAMETERS = (
    SliderSpec("level", 0.02, 0.6, 0.01, 0.18, "Level", "Percussion burst level."),
    SliderSpec("tone", 180, 4000, 20, 1100, "Tone", "Percussion resonant frequency."),
)

KICK_PROFILES = {
    "round": (118.0, 0.24, 0.16),
    "punch": (168.0, 0.18, 0.28),
    "soft": (92.0, 0.34, 0.07),
}
BASS_PATTERNS = {
    "rolling": [0, 0, 7, 0, 0, 12, 7, 0, 0, 0, 3, 7, 0, 10, 7, 0],
    "dub": [0, 0, 0, 7, 0, 0, 10, 0, 0, 7, 0, 0, 3, 0, 7, 0],
    "muted": [0, 0, 0, 0, 7, 0, 0, 0, 0, 0, 3, 0, 0, 7, 0, 10],
}
CHORD_ROOTS = [0, 5, 10, 7]
CHORD_INTERVALS = (0, 3, 7, 10)
HAT_PATTERNS = {
    "crisp": {2, 6, 10, 14},
    "open": {2, 6, 10, 14, 15},
    "shuffle": {2, 5, 6, 10, 13, 14},
}
PERC_PATTERNS = {
    "clap": {4, 12},
    "rim": {3, 7, 11, 15},
    "conga": {3, 6, 9, 11, 14},
}


def build_kick(
    tempo: Tempo, clock: Clock, style: str, level: float = 0.62, drive: float = 0.12
) -> Patch:
    """Build a four-on-the-floor kick in the requested deep-house style."""
    pitch_start, decay, click = KICK_PROFILES[style]
    trigger = Trig()
    pitch = TrigLinseg(trigger, [(0, pitch_start), (0.055, 52), (decay, 48)])
    body = Sine(freq=pitch)
    envelope = TrigEnv(trigger, CosTable([(0, 0), (45, 1), (8191, 0)]), dur=decay, mul=level)
    click_env = TrigEnv(trigger, CosTable([(0, 0), (8, 1), (420, 0)]), dur=0.035, mul=click)
    voice = Disto((body * envelope) + (Noise() * click_env), drive=drive, slope=0.85)
    return Patch(
        sequencer=clock.subscribe(FOURTH, trigger.play),
        voice=voice,
        controls={
            "level": lambda value: setattr(envelope, "mul", value),
            "drive": lambda value: setattr(voice, "drive", value),
        },
    )


def build_bass(
    tempo: Tempo, clock: Clock, style: str, root_freq: float = 55, cutoff: float = 720
) -> Patch:
    """Build a 16th-note bassline with a style-specific motion pattern."""
    styles = {"rolling": (0.88, 0.55), "dub": (0.95, 0.78), "muted": (0.55, 0.3)}
    decay, resonance = styles[style]
    trigger = Trig()
    envelope = TrigEnv(
        trigger, CosTable([(0, 0), (80, 1), (2100, 0.5), (8191, 0)]), dur=tempo.sixteenth * decay
    )
    oscillator = Osc(HarmTable([1, 0.32, 0.18, 0.1]), freq=root_freq, mul=envelope)
    voice = MoogLP(oscillator, freq=cutoff, res=resonance)
    state = {"step": 0, "root": root_freq}

    def next_step() -> None:
        step = state["step"] % 16
        oscillator.freq = state["root"] * 2 ** (BASS_PATTERNS[style][step] / 12)
        envelope.mul = 1.0 if step % 4 == 0 else 0.72
        trigger.play()
        state["step"] += 1

    return Patch(
        sequencer=clock.subscribe(SIXTEENTH, next_step),
        voice=voice,
        controls={
            "root_freq": lambda value: state.update(root=value),
            "cutoff": lambda value: setattr(voice, "freq", value),
        },
    )


def build_chord(
    tempo: Tempo, clock: Clock, style: str, root_freq: float = 146, brightness: float = 1500
) -> Patch:
    """Build an offbeat minor-seventh chord stab from four explicit voices."""
    profiles = {
        "velvet": (HarmTable([1, 0.25, 0.12]), 0.34, 0.42),
        "organ": (HarmTable([1, 0.7, 0.4, 0.2]), 0.22, 0.2),
        "shimmer": (SawTable(order=12), 0.42, 0.58),
    }
    table, duration, wet = profiles[style]
    trigger = Trig()
    envelope = TrigEnv(trigger, CosTable([(0, 0), (200, 1), (2500, 0.55), (8191, 0)]), dur=duration)
    voices = [
        Osc(table, freq=root_freq * 2 ** (interval / 12), mul=envelope * 0.19)
        for interval in CHORD_INTERVALS
    ]
    filter_voice = Biquad(sum(voices), freq=brightness, q=1.2, type=0)
    voice = filter_voice
    if style == "shimmer":
        voice = Chorus(voice, depth=1.2, feedback=0.15, bal=0.28)
    voice = Freeverb(voice, size=0.72, damp=0.45, bal=wet)
    state = {"step": 0, "root": root_freq}

    def next_step() -> None:
        step = state["step"] % 16
        if step % 4 == 2:
            chord_root = state["root"] * 2 ** (CHORD_ROOTS[(step // 4) % 4] / 12)
            for oscillator, interval in zip(voices, CHORD_INTERVALS, strict=True):
                oscillator.freq = chord_root * 2 ** (interval / 12)
            trigger.play()
        state["step"] += 1

    return Patch(
        sequencer=clock.subscribe(SIXTEENTH, next_step),
        voice=voice,
        controls={
            "root_freq": lambda value: state.update(root=value),
            "brightness": lambda value: setattr(filter_voice, "freq", value),
        },
    )


def build_hat(
    tempo: Tempo, clock: Clock, style: str, level: float = 0.14, cutoff: float = 9000
) -> Patch:
    """Build a style-specific, grid-locked hat pattern."""
    duration = {"crisp": 0.07, "open": 0.22, "shuffle": 0.11}[style]
    trigger = Trig()
    envelope = TrigEnv(trigger, CosTable([(0, 0), (35, 1), (8191, 0)]), dur=duration, mul=level)
    voice = ButHP(Noise() * envelope, freq=cutoff)
    state = {"step": 0}

    def next_step() -> None:
        step = state["step"] % 16
        if step in HAT_PATTERNS[style]:
            envelope.mul = level if step % 4 == 2 else level * 0.66
            trigger.play()
        state["step"] += 1

    return Patch(
        sequencer=clock.subscribe(SIXTEENTH, next_step),
        voice=voice,
        controls={
            "level": lambda value: setattr(envelope, "mul", value),
            "cutoff": lambda value: setattr(voice, "freq", value),
        },
    )


def build_percussion(
    tempo: Tempo, clock: Clock, style: str, level: float = 0.18, tone: float = 1100
) -> Patch:
    """Build claps, rims, or conga-like resonance from the same rhythmic layer."""
    duration = {"clap": 0.16, "rim": 0.07, "conga": 0.19}[style]
    trigger = Trig()
    envelope = TrigEnv(trigger, CosTable([(0, 0), (30, 1), (8191, 0)]), dur=duration, mul=level)
    source = Noise() if style == "clap" else Sine(freq=tone)
    voice = Biquad(
        source * envelope,
        freq=tone,
        q=5 if style != "clap" else 1.1,
        type=2 if style != "clap" else 1,
    )
    state = {"step": 0}

    def next_step() -> None:
        step = state["step"] % 16
        if step in PERC_PATTERNS[style]:
            trigger.play()
        state["step"] += 1

    return Patch(
        sequencer=clock.subscribe(SIXTEENTH, next_step),
        voice=voice,
        controls={
            "level": lambda value: setattr(envelope, "mul", value),
            "tone": lambda value: setattr(voice, "freq", value),
        },
    )


def make_builder(role: str, style: str) -> Callable[..., Patch]:
    """Return one concrete builder for the selected rack role and style."""
    builders = {
        "kick": build_kick,
        "bass": build_bass,
        "chord": build_chord,
        "hat": build_hat,
        "percussion": build_percussion,
    }
    return lambda tempo, clock, **values: builders[role](tempo, clock, style, **values)
