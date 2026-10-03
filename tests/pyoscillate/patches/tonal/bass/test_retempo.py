"""A BPM change reaches a built bass voice's tempo-derived values."""

import unittest

from pyoscillate.clock import Clock
from pyoscillate.harmony import Harmony
from pyoscillate.patches.base import BuildContext, start_server
from pyoscillate.patches.tonal.bass import TechnoBass
from pyoscillate.patches.tonal.bass.fm.fm import FmBassBark
from pyoscillate.patches.tonal.bass.hover import BassHover
from pyoscillate.tempo import Tempo


class BassRetempoTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.server = start_server(audio="manual")

    @classmethod
    def tearDownClass(cls) -> None:
        cls.server.stop()
        cls.server.shutdown()

    def build(self, patch_type: type, bpm: float = 120):
        tempo = Tempo(bpm=bpm)
        clock = Clock(tempo)
        return tempo, patch_type().build(BuildContext(tempo, clock, Harmony()))

    def test_envelope_and_filter_lfo_follow_bpm(self) -> None:
        tempo, patch = self.build(TechnoBass)
        before = (patch.envelope.dur, patch.cutoff_lfo.freq)
        tempo.set_bpm(60)
        patch.retempo()
        self.assertAlmostEqual(patch.envelope.dur, before[0] * 2)
        self.assertAlmostEqual(patch.cutoff_lfo.freq, before[1] / 2)

    def test_fm_length_follows_bpm(self) -> None:
        tempo, patch = self.build(FmBassBark)
        before = patch.amp.dur
        tempo.set_bpm(60)
        patch.retempo()
        self.assertAlmostEqual(patch.amp.dur, before * 2)

    def test_hover_breath_follows_bpm(self) -> None:
        tempo, patch = self.build(BassHover)
        before = patch.breath_lfo.freq
        tempo.set_bpm(60)
        patch.retempo()
        self.assertAlmostEqual(patch.breath_lfo.freq, before / 2)


if __name__ == "__main__":
    unittest.main()
