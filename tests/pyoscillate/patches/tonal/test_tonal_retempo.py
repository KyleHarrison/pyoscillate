import unittest

from pyoscillate.clock import Clock
from pyoscillate.patches.base import BuildContext, start_server
from pyoscillate.patches.texture.atmosphere import Atmosphere
from pyoscillate.patches.tonal.drone import Drone
from pyoscillate.patches.tonal.lead.fm import LeadFmWind
from pyoscillate.tempo import Tempo
from pyoscillate.theory.harmony import Harmony


class TonalRetempoTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.server = start_server(audio="manual")
        cls.tempo = Tempo(bpm=120)
        cls.clock = Clock(cls.tempo)
        cls.clock.start()

    @classmethod
    def tearDownClass(cls) -> None:
        cls.clock.stop()
        cls.server.stop()
        cls.server.shutdown()

    def setUp(self) -> None:
        self.addCleanup(self.tempo.set_bpm, 120)
        self.context = BuildContext(self.tempo, self.clock, Harmony())

    def test_lead_fm_follows_tempo(self) -> None:
        voice = LeadFmWind()
        built = voice.build(self.context)
        dur, delay, drift = voice.amp.dur, voice.echo.delay, voice.drift.freq

        self.tempo.set_bpm(240)
        built.retempo()

        self.assertAlmostEqual(voice.amp.dur, dur / 2, places=4)
        self.assertAlmostEqual(voice.echo.delay, delay / 2, places=4)
        self.assertAlmostEqual(voice.drift.freq, drift * 2, places=4)

    def test_drone_follows_tempo(self) -> None:
        voice = Drone()
        built = voice.build(self.context)
        glide, freq = voice.drone_freq_sig.time, voice.ratio_lfo.freq

        self.tempo.set_bpm(240)
        built.retempo()

        self.assertAlmostEqual(voice.drone_freq_sig.time, glide / 2, places=4)
        self.assertAlmostEqual(voice.ratio_lfo.freq, freq * 2, places=4)

    def test_atmosphere_follows_tempo(self) -> None:
        voice = Atmosphere()
        built = voice.build(self.context)
        dur, freq = voice.arp_env.dur, voice.arp_swell.freq

        self.tempo.set_bpm(240)
        built.retempo()

        self.assertAlmostEqual(voice.arp_env.dur, dur / 2, places=4)
        self.assertAlmostEqual(voice.arp_swell.freq, freq * 2, places=4)
