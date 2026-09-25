# uv run flet run src/flet/patch/app.py -- pyoscillate.patches.tonal.drone.filter
from __future__ import annotations

from pyo.lib.controls import SigTo
from pyo.lib.effects import Delay, Freeverb
from pyo.lib.filters import MoogLP
from pyo.lib.generators import Lorenz
from pyo.lib.tableprocess import Osc
from pyo.lib.tables import HarmTable

from pyoscillate.patches.base import BuiltPatch
from pyoscillate.patches.common import ContinuousSequencer
from pyoscillate.patches.params import PyoParamRef, SliderSpec
from pyoscillate.patches.utility.notes import notes

ROOT_FREQ = notes.A3  # current default

PARAMETERS = (
    SliderSpec(
        "root_freq",
        notes.A1,
        notes.A4,
        1,
        ROOT_FREQ,
        "Register",
        "Sets the drone's fundamental pitch.",
        (PyoParamRef(Osc, "freq"),),
        scale="note",
    ),
    SliderSpec(
        "cutoff_speed",
        0.01,
        0.5,
        0.01,
        0.05,
        "Sweep speed",
        "How quickly the filter's cutoff wanders; slower feels like a slow-breathing wah, faster feels more agitated.",
        (PyoParamRef(Lorenz, "pitch"),),
    ),
    SliderSpec(
        "cutoff_chaos",
        0,
        1,
        0.05,
        0.6,
        "Sweep instability",
        "How unpredictable the cutoff sweep is; higher feels more restless and alive, lower stays closer to a steady, cyclical wah.",
        (PyoParamRef(Lorenz, "chaos"),),
    ),
    SliderSpec(
        "filter_res",
        0,
        1,
        0.05,
        0.6,
        "Resonance",
        "Adds emphasis around the cutoff as it sweeps; higher makes the motion more vocal and whistling, lower keeps it smoother.",
        (PyoParamRef(MoogLP, "res"),),
    ),
    SliderSpec(
        "filter_base",
        100,
        2000,
        10,
        700,
        "Brightness",
        "Sets the average brightness the filter sweeps around; higher opens the drone up, lower keeps it duller and more closed.",
        (PyoParamRef(Lorenz, "add"),),
    ),
    SliderSpec(
        "filter_range",
        0,
        1500,
        10,
        600,
        "Sweep depth",
        "Controls how far the filter sweeps each cycle; wider ranges create more dramatic movement, narrower keeps the tone closer to static.",
        (PyoParamRef(Lorenz, "mul"),),
    ),
    SliderSpec(
        "reverb_size",
        0,
        1,
        0.05,
        0.8,
        "Space",
        "Sets how large and distant the drone's room feels, from a tight presence to a huge, cavernous decay.",
        (PyoParamRef(Freeverb, "size"),),
    ),
    SliderSpec(
        "reverb_damp",
        0,
        1,
        0.05,
        0.5,
        "Tail darkness",
        "Darkens the reverb tail as it decays; higher settings sound warmer and more muffled, lower settings stay bright and shimmering.",
        (PyoParamRef(Freeverb, "damp"),),
    ),
    SliderSpec(
        "reverb_bal",
        0,
        1,
        0.05,
        0.75,
        "Distance",
        "Blends how much of the drone is heard through the reverb versus dry; higher dissolves it into the atmosphere, lower keeps it present.",
        (PyoParamRef(Freeverb, "bal"),),
    ),
    SliderSpec(
        "delay_time",
        0.05,
        2,
        0.05,
        0.45,
        "Echo spacing",
        "Sets the time between echo repeats, smearing the timbral drift across time.",
        (PyoParamRef(Delay, "delay"),),
    ),
    SliderSpec(
        "delay_feedback",
        0,
        0.9,
        0.05,
        0.3,
        "Echo density",
        "Sets how many times each echo repeats before fading; higher creates a denser, more layered wash.",
        (PyoParamRef(Delay, "feedback"),),
    ),
)

# harmonic-rich static tone for the filter to carve movement into - the pad's
# "color" comes entirely from the cutoff sweep below, not from this waveform changing
PAD_HARMONICS = [1, 0.6, 0.4, 0.25, 0.15, 0.08, 0.04]


def build(
    root_freq: float = ROOT_FREQ,
    cutoff_speed: float = 0.05,
    cutoff_chaos: float = 0.6,
    filter_res: float = 0.6,
    filter_base: float = 700,
    filter_range: float = 600,
    reverb_size: float = 0.8,
    reverb_damp: float = 0.5,
    reverb_bal: float = 0.75,
    delay_time: float = 0.45,
    delay_feedback: float = 0.3,
) -> BuiltPatch:
    """Static harmonic-rich drone carved by a chaotically-swept resonant lowpass filter.

    Unlike `soundscape_fm`'s smooth FM timbre drift, all the movement here
    comes from the filter cutoff wandering - a more angular, "breathing"
    character closer to a classic 60s/70s psychedelic filter sweep than a
    softly evolving tone.

    Args:
        root_freq: Fundamental frequency (Hz) of the static harmonic tone
            under the filter. The pitch never changes; only the filter
            cutoff moves.
        cutoff_speed: `pitch` parameter of the `Lorenz` attractor driving the
            filter cutoff - how fast it wanders. Lower values give a slow,
            spacious sweep; raising it makes the filter audibly restless.
        cutoff_chaos: `chaos` parameter of the same attractor, 0-1. Higher
            values make the sweep more unpredictable and angular; lower
            values pull it toward smoother, more periodic movement.
        filter_res: `MoogLP` resonance (0-1ish, self-oscillates as it
            approaches/exceeds 1). Higher values emphasize whatever
            frequency the sweep is currently sitting on, giving the pad a
            more pronounced, vocal-like "wah" as the cutoff wanders; lower
            values give a smoother, less colored response.
        filter_base: Center cutoff frequency (Hz) the wander rides on top
            of. Raising it lets more harmonics through on average, for a
            brighter pad; lowering it darkens and rounds it off.
        filter_range: How far (Hz) the attractor swings the cutoff above and
            below `filter_base`. Larger values make the sweep more dramatic
            - the pad audibly opens and closes; smaller values keep the
            cutoff nearly static for a more constant tone.
        reverb_size: Freeverb room size (0-1). Large by default so the pad
            reads as an enveloping space rather than a distinct voice.
        reverb_damp: Freeverb high-frequency damping (0-1). Higher values
            darken the tail; lower values keep it bright and ringing.
        reverb_bal: Freeverb dry/wet balance (0-1). Kept high so the pad is
            heard mostly through its reverb space.
        delay_time: Delay line time in seconds, thickening the sweep's
            drift by echoing each moment of it slightly later.
        delay_feedback: Delay feedback (0-1). Higher values repeat each
            echo more times before decaying, for a denser wash.
    """
    live = {
        name: SigTo(value=value, time=0.15)
        for name, value in {
            "root_freq": root_freq,
            "cutoff_speed": cutoff_speed,
            "cutoff_chaos": cutoff_chaos,
            "filter_res": filter_res,
            "filter_base": filter_base,
            "filter_range": filter_range,
            "reverb_size": reverb_size,
            "reverb_damp": reverb_damp,
            "reverb_bal": reverb_bal,
            "delay_time": delay_time,
            "delay_feedback": delay_feedback,
        }.items()
    }
    pad_table = HarmTable(PAD_HARMONICS)
    pad_osc = Osc(table=pad_table, freq=live["root_freq"], mul=0.25)

    cutoff_chaos_lfo = Lorenz(
        pitch=live["cutoff_speed"],
        chaos=live["cutoff_chaos"],
        mul=live["filter_range"],
        add=live["filter_base"],
    )
    filtered = MoogLP(pad_osc, freq=cutoff_chaos_lfo, res=live["filter_res"])

    reverb_voice = Freeverb(
        filtered,
        size=live["reverb_size"],
        damp=live["reverb_damp"],
        bal=live["reverb_bal"],
    )
    voice = Delay(
        reverb_voice,
        delay=live["delay_time"],
        feedback=live["delay_feedback"],
        maxdelay=2,
    )

    return BuiltPatch(
        sequencer=ContinuousSequencer(),
        voice=voice,
        controls={
            name: lambda value, control=control: setattr(control, "value", value)
            for name, control in live.items()
        },
        resources=(
            *live.values(),
            pad_table,
            pad_osc,
            cutoff_chaos_lfo,
            filtered,
            reverb_voice,
        ),
    )
