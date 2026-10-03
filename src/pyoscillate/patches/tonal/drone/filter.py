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
from pyo.lib.filters import MoogLP
from pyo.lib.generators import Lorenz
from pyo.lib.tableprocess import Osc
from pyo.lib.tables import HarmTable

from pyoscillate.patches.base import BuildContext, Patch
from pyoscillate.patches.common import ContinuousVoice, Echo, Gate, Reverb, RootPitch
from pyoscillate.patches.params import Param
from pyoscillate.theory.pitch import Note

# harmonic-rich static tone for the filter to carve movement into - the drone's
# "color" comes entirely from the cutoff sweep below, not from this waveform changing
PAD_HARMONICS = [1, 0.6, 0.4, 0.25, 0.15, 0.08, 0.04]


class SoundscapeFilter(Gate, Reverb, Echo, RootPitch, ContinuousVoice):
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
    pad_table: HarmTable
    pad_osc: Osc
    cutoff_chaos_lfo: Lorenz
    filtered: MoogLP

    root_freq = RootPitch.root_freq.replace(
        minimum=Note.A1,
        help_text="Sets the drone's fundamental pitch.",
    )

    @Param(
        0.01,
        0.5,
        0.01,
        0.05,
        "Sweep speed",
        "How quickly the filter's cutoff wanders; slower feels like a slow-breathing wah, faster feels "
        "more agitated.",
        sweep=True,
        advanced=True,
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
        advanced=True,
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

    reverb_size = Reverb.reverb_size.replace(default=0.8)
    reverb_bal = Reverb.reverb_bal.replace(default=0.75)

    delay_time = Echo.delay_time.replace(default=0.45)
    delay_feedback = Echo.delay_feedback.replace(default=0.3)

    def build(self, context: BuildContext) -> Patch:
        """Wire the graph; `finish()` applies every parameter's control."""
        self._reset()
        self.root_freq_sig = self.live(type(self).root_freq)
        self.cutoff_speed_sig = self.live(type(self).cutoff_speed)
        self.cutoff_chaos_sig = self.live(type(self).cutoff_chaos)
        self.filter_res_sig = self.live(type(self).filter_res)
        self.filter_base_sig = self.live(type(self).filter_base)
        self.filter_range_sig = self.live(type(self).filter_range)

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

        self.reverb = self.add_reverb(self.filtered)
        self.output = self.add_echo(self.reverb)
        return self.finish(self.add_gate(self.output, context))
