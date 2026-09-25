# uv run flet run src/flet/patch/app.py -- pyoscillate.patches.drums.tom.tom
"""Pitched tom voice.

A pitched drum hit: a sine body with a quick but audible downward sweep, a
faster-decaying membrane overtone, and a short transient. It plays a sparse
two-bar fill down a minor pentatonic built on the rack's current chord root,
adding pitched contour to the kit without the weight of the kick.
"""

from pyo.lib._core import Sig
from pyo.lib.filters import Biquad
from pyo.lib.generators import Noise, Sine
from pyo.lib.tables import ExpTable
from pyo.lib.triggers import Trig, TrigEnv

from pyoscillate.clock import Clock, NoteDivision
from pyoscillate.harmony import Harmony
from pyoscillate.patches.base import Patch
from pyoscillate.patches.params import SliderSpec
from pyoscillate.patches.utility.notes import notes
from pyoscillate.tempo import Tempo

BASE_DIVISION = NoteDivision.SIXTEENTH

PARAMETERS = (
    SliderSpec(
        "level",
        0.02,
        0.6,
        0.01,
        0.2,
        "Presence",
        "Sets how loud and upfront the tom fill sits in the mix.",
    ),
    SliderSpec(
        "tune",
        -12,
        12,
        1,
        0,
        "Pitch",
        "Retunes the whole fill in semitones; lower is a deeper floor tom, higher a tighter rack tom.",
    ),
    SliderSpec(
        "sweep",
        0.0,
        2.0,
        0.05,
        1.0,
        "Sweep",
        "Depth of the downward pitch bend on each hit; more gives a bigger impact gesture, too much "
        "starts to sound like a zap, none leaves a static pitched ping.",
    ),
    SliderSpec(
        "length",
        0.5,
        2.0,
        0.05,
        1.0,
        "Length",
        "Shortens the tom toward a dry, damped hit or lets it ring out with a longer resonant tail.",
    ),
    SliderSpec(
        "tone",
        0.0,
        1.0,
        0.05,
        0.35,
        "Brightness",
        "Adds the upper membrane overtone and stick attack; low is a round, deep tom, high a brighter, "
        "more articulate one.",
    ),
    SliderSpec(
        "rate",
        Clock.rate_limits(BASE_DIVISION)[0],
        Clock.rate_limits(BASE_DIVISION)[1],
        1,
        0,
        "Rate",
        "Halves or doubles the fill speed for each step away from its 16th-note grid.",
    ),
)
# step in the two-bar (32-step) cycle -> semitones above the chord root;
# fifth, fifth, minor third, root walks down the minor pentatonic, and all
# four are tones of the rack's minor-seventh chords (E, E, C, A over Am7)
PATTERN = {10: 7, 26: 7, 29: 3, 31: 0}
CYCLE = 32
# A2 - low-mid register, well above a kick; each chord root snaps to the
# octave nearest this before Pitch retunes it
BODY_FREQ = notes.A2
BEND_DEPTH = 0.4
BEND_TIME = 0.06
DECAY = 0.3
# a circular membrane's first overtone sits at roughly 1.59x the fundamental
OVERTONE_RATIO = 1.59
OVERTONE_LEVEL = 0.5
OVERTONE_DECAY = 0.12
CLICK_LEVEL = 0.6
CLICK_RATIO = 6.0
CLICK_RESONANCE = 2.0
CLICK_DURATION = 0.01
DECAY_CURVE = 3
BEND_CURVE = 4
VOLUME_DEFAULT = 0.3
# a static key of A - used only outside a rack that shares its own `Harmony`
FALLBACK_HARMONY = Harmony()


def _ratio(semitones: float) -> float:
    return 2 ** (semitones / 12)


def build(
    tempo: Tempo,
    clock: Clock,
    level: float = 0.2,
    tune: float = 0,
    sweep: float = 1.0,
    length: float = 1.0,
    tone: float = 0.35,
    rate: float = 0,
    harmony: Harmony | None = None,
) -> Patch:
    """Build a pitched tom playing a sparse two-bar fill on the current chord.

    The fill follows the chord rather than only the key: the rack's chords
    are parallel minor sevenths, so a pentatonic fixed to the key would land
    on non-chord tones over some of them."""
    harmony = harmony or FALLBACK_HARMONY
    trigger = Trig()
    tuning = Sig(_ratio(tune))
    body_freq = tuning * BODY_FREQ

    bend_table = ExpTable([(0, 1), (8191, 0)], exp=BEND_CURVE)
    bend = TrigEnv(trigger, bend_table, dur=BEND_TIME, mul=BEND_DEPTH * sweep, add=1)
    pitch = body_freq * bend
    body = Sine(freq=pitch)
    body_table = ExpTable([(0, 1), (8191, 0)], exp=DECAY_CURVE)
    body_env = TrigEnv(trigger, body_table, dur=DECAY * length, mul=level)
    body_signal = body * body_env

    overtone_pitch = pitch * OVERTONE_RATIO
    overtone = Sine(freq=overtone_pitch)
    overtone_table = ExpTable([(0, 1), (8191, 0)], exp=DECAY_CURVE)
    overtone_env = TrigEnv(
        trigger,
        overtone_table,
        dur=OVERTONE_DECAY * length,
        mul=level * tone * OVERTONE_LEVEL,
    )
    overtone_signal = overtone * overtone_env

    noise = Noise()
    click_table = ExpTable([(0, 1), (8191, 0)], exp=BEND_CURVE)
    click_env = TrigEnv(trigger, click_table, dur=CLICK_DURATION, mul=level * tone * CLICK_LEVEL)
    click_burst = noise * click_env
    click_freq = body_freq * CLICK_RATIO
    click_signal = Biquad(click_burst, freq=click_freq, q=CLICK_RESONANCE, type=2)

    partials = body_signal + overtone_signal
    voice = partials + click_signal
    state = {"step": 0, "level": level, "tune": tune, "tone": tone}

    def apply_gains() -> None:
        overtone_env.mul = state["level"] * state["tone"] * OVERTONE_LEVEL
        click_env.mul = state["level"] * state["tone"] * CLICK_LEVEL
        body_env.mul = state["level"]

    def next_step() -> None:
        offset = PATTERN.get(state["step"] % CYCLE)
        if offset is not None:
            chord_ratio = harmony.chord_freq(BODY_FREQ, clock.bar_index) / BODY_FREQ
            tuning.value = chord_ratio * _ratio(state["tune"] + offset)
            # restart both partials on a zero crossing so the immediate
            # attack doesn't click wherever the oscillators last stopped
            body.reset()
            overtone.reset()
            trigger.play()
        state["step"] += 1

    def set_state(name: str, value: float) -> None:
        state[name] = value
        apply_gains()

    def set_length(value: float) -> None:
        body_env.dur = DECAY * value
        overtone_env.dur = OVERTONE_DECAY * value

    division = clock.subscribe(clock.ticks_for_rate(BASE_DIVISION, rate), next_step)
    return Patch(
        sequencer=division,
        voice=voice,
        controls={
            "level": lambda value: set_state("level", value),
            # takes effect from the next hit, which sets the fill note too
            "tune": lambda value: state.__setitem__("tune", value),
            "sweep": lambda value: setattr(bend, "mul", BEND_DEPTH * value),
            "length": set_length,
            "tone": lambda value: set_state("tone", value),
            "rate": lambda value: setattr(
                division, "steps", clock.ticks_for_rate(BASE_DIVISION, value)
            ),
        },
        resources=(
            trigger,
            tuning,
            body_freq,
            bend_table,
            bend,
            pitch,
            body,
            body_table,
            body_env,
            body_signal,
            overtone_pitch,
            overtone,
            overtone_table,
            overtone_env,
            overtone_signal,
            noise,
            click_table,
            click_env,
            click_burst,
            click_freq,
            click_signal,
            partials,
        ),
    )
