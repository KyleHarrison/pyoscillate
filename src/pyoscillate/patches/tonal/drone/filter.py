# uv run flet run src/flet/patch/app.py -- pyoscillate.patches.tonal.drone.filter
"""Filter-swept drone: a static harmonic-rich tone carved by a chaotically
wandering resonant lowpass filter, then smeared with reverb and delay.

This is the drone family's "filter" style - the source spectrum never
changes; all of the movement the listener tracks comes from the cutoff
itself wandering, a more angular, "breathing" character closer to a classic
60s/70s psychedelic filter sweep than a softly evolving tone.
"""

from __future__ import annotations

from pyo.lib.controls import SigTo
from pyo.lib.effects import Delay, Freeverb
from pyo.lib.filters import MoogLP
from pyo.lib.generators import Lorenz
from pyo.lib.tableprocess import Osc
from pyo.lib.tables import HarmTable

from pyoscillate.patches.base import BuildContext, Patch
from pyoscillate.patches.common import ContinuousVoice, Gate
from pyoscillate.patches.params import Param
from pyoscillate.patches.utility.notes import notes

# harmonic-rich static tone for the filter to carve movement into - the drone's
# "color" comes entirely from the cutoff sweep below, not from this waveform changing
PAD_HARMONICS = [1, 0.6, 0.4, 0.25, 0.15, 0.08, 0.04]


class SoundscapeFilter(Gate, ContinuousVoice):
    """Static harmonic-rich drone carved by a chaotically-swept resonant lowpass filter.

    Unlike `SoundscapeFm`'s smooth FM timbre drift, all the movement here
    comes from the filter cutoff wandering - a more angular, "breathing"
    character closer to a classic 60s/70s psychedelic filter sweep than a
    softly evolving tone.
    """

    title = "Soundscape - filter-swept pad"
    summary = "Sustained drone whose brightness sweeps and breathes unpredictably."
    volume = Patch.volume.replace(default=0.6)

    # the graph, assigned by build(); finish() retains every one of them
    root_freq_sig: SigTo
    cutoff_speed_sig: SigTo
    cutoff_chaos_sig: SigTo
    filter_res_sig: SigTo
    filter_base_sig: SigTo
    filter_range_sig: SigTo
    reverb_size_sig: SigTo
    reverb_damp_sig: SigTo
    reverb_bal_sig: SigTo
    delay_time_sig: SigTo
    delay_feedback_sig: SigTo
    pad_table: HarmTable
    pad_osc: Osc
    cutoff_chaos_lfo: Lorenz
    filtered: MoogLP
    reverb_voice: Freeverb
    output: Delay

    @Param(
        notes.A1,
        notes.A4,
        1,
        notes.A3,
        "Register",
        "Sets the drone's fundamental pitch.",
        scale="note",
    )
    def root_freq(self, value: float) -> None:
        self.root_freq_sig.value = value

    @Param(
        0.01,
        0.5,
        0.01,
        0.05,
        "Sweep speed",
        "How quickly the filter's cutoff wanders; slower feels like a slow-breathing wah, faster feels "
        "more agitated.",
        sweep=True,
    )
    def cutoff_speed(self, value: float) -> None:
        self.cutoff_speed_sig.value = value

    @Param(
        0,
        1,
        0.05,
        0.6,
        "Sweep instability",
        "How unpredictable the cutoff sweep is; higher feels more restless and alive, lower stays closer "
        "to a steady, cyclical wah.",
        sweep=True,
    )
    def cutoff_chaos(self, value: float) -> None:
        self.cutoff_chaos_sig.value = value

    @Param(
        0,
        1,
        0.05,
        0.6,
        "Resonance",
        "Adds emphasis around the cutoff as it sweeps; higher makes the motion more vocal and whistling, "
        "lower keeps it smoother.",
        sweep=True,
    )
    def filter_res(self, value: float) -> None:
        self.filter_res_sig.value = value

    @Param(
        100,
        2000,
        10,
        700,
        "Brightness",
        "Sets the average brightness the filter sweeps around; higher opens the drone up, lower keeps it "
        "duller and more closed.",
        sweep=True,
    )
    def filter_base(self, value: float) -> None:
        self.filter_base_sig.value = value

    @Param(
        0,
        1500,
        10,
        600,
        "Sweep depth",
        "Controls how far the filter sweeps each cycle; wider ranges create more dramatic movement, "
        "narrower keeps the tone closer to static.",
        sweep=True,
    )
    def filter_range(self, value: float) -> None:
        self.filter_range_sig.value = value

    @Param(
        0,
        1,
        0.05,
        0.8,
        "Space",
        "Sets how large and distant the drone's room feels, from a tight presence to a huge, cavernous decay.",
        sweep=True,
    )
    def reverb_size(self, value: float) -> None:
        self.reverb_size_sig.value = value

    @Param(
        0,
        1,
        0.05,
        0.5,
        "Tail darkness",
        "Darkens the reverb tail as it decays; higher settings sound warmer and more muffled, lower "
        "settings stay bright and shimmering.",
        sweep=True,
    )
    def reverb_damp(self, value: float) -> None:
        self.reverb_damp_sig.value = value

    @Param(
        0,
        1,
        0.05,
        0.75,
        "Distance",
        "Blends how much of the drone is heard through the reverb versus dry; higher dissolves it into "
        "the atmosphere, lower keeps it present.",
        sweep=True,
    )
    def reverb_bal(self, value: float) -> None:
        self.reverb_bal_sig.value = value

    @Param(
        0.05,
        2,
        0.05,
        0.45,
        "Echo spacing",
        "Sets the time between echo repeats, smearing the timbral drift across time.",
        sweep=True,
    )
    def delay_time(self, value: float) -> None:
        self.delay_time_sig.value = value

    @Param(
        0,
        0.9,
        0.05,
        0.3,
        "Echo density",
        "Sets how many times each echo repeats before fading; higher creates a denser, more layered wash.",
        sweep=True,
    )
    def delay_feedback(self, value: float) -> None:
        self.delay_feedback_sig.value = value

    def build(self, context: BuildContext) -> Patch:
        """Wire the graph; `finish()` applies every parameter's control."""
        self._reset()
        self.root_freq_sig = self.live(type(self).root_freq)
        self.cutoff_speed_sig = self.live(type(self).cutoff_speed)
        self.cutoff_chaos_sig = self.live(type(self).cutoff_chaos)
        self.filter_res_sig = self.live(type(self).filter_res)
        self.filter_base_sig = self.live(type(self).filter_base)
        self.filter_range_sig = self.live(type(self).filter_range)
        self.reverb_size_sig = self.live(type(self).reverb_size)
        self.reverb_damp_sig = self.live(type(self).reverb_damp)
        self.reverb_bal_sig = self.live(type(self).reverb_bal)
        self.delay_time_sig = self.live(type(self).delay_time)
        self.delay_feedback_sig = self.live(type(self).delay_feedback)

        self.pad_table = HarmTable(PAD_HARMONICS)
        self.pad_osc = Osc(table=self.pad_table, freq=self.root_freq_sig, mul=0.25)

        self.cutoff_chaos_lfo = Lorenz(
            pitch=self.cutoff_speed_sig,
            chaos=self.cutoff_chaos_sig,
            mul=self.filter_range_sig,
            add=self.filter_base_sig,
        )
        self.filtered = MoogLP(
            self.pad_osc, freq=self.cutoff_chaos_lfo, res=self.filter_res_sig
        )

        self.reverb_voice = Freeverb(
            self.filtered,
            size=self.reverb_size_sig,
            damp=self.reverb_damp_sig,
            bal=self.reverb_bal_sig,
        )
        self.output = Delay(
            self.reverb_voice,
            delay=self.delay_time_sig,
            feedback=self.delay_feedback_sig,
            maxdelay=2,
        )
        return self.finish(self.add_gate(self.output, context))
