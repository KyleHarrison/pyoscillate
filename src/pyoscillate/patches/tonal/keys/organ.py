# uv run flet run src/flet/patch/app.py -- pyoscillate.patches.tonal.keys.organ
"""Drawbar organ: nine sine ranks on the harmonic series, a chime on the front
of each note, a key click, a rotating speaker and a tube preamp.

Each drawbar is one rank (`RankedKeys`, see `sustained.py`) at a harmonic of the
note: the 16' bar sounds an octave below, the 8' bar the note itself, and the
others the fifth, octave, twelfth and so on above, the way an organ's
footage names the pipe that would sound it. Their balance is the whole tone:
a few low bars is a round, sweet flute, all of them is a full, bright,
piercing chorus. Each bar is set in the organ's own steps, 0 (off) to 8, each
step 3 dB.

The percussion switch adds a second or third harmonic that dies away on every
key press, a pluck on the front of a steady tone; the key click is the tick
of the contacts. The Leslie speaker's rotors turn the sound: a delay swinging
back and forth bends the pitch (the Doppler effect of a spinning horn) and a
tremolo pulses the level, both at the rotor's speed, which takes a
second or so to speed up or slow down. A tube preamp saturates it all.
"""

from __future__ import annotations

from typing import ClassVar

from pyo import PyoObject
from pyo.lib._core import Mix
from pyo.lib.controls import Adsr, SigTo
from pyo.lib.effects import Delay, Disto
from pyo.lib.filters import ButHP
from pyo.lib.generators import Noise, Sine

from pyoscillate.patches.common import Reverb
from pyoscillate.patches.params import Param
from pyoscillate.patches.tonal.keys.sustained import RankedKeys


class Organ(Reverb, RankedKeys):
    """Drawbar organ: nine sine ranks, percussion, key click, a rotating
    speaker and a tube preamp, holding the rack's chord as long as the keys
    are down."""

    title = "Organ"
    summary = "Warm, sustained drawbar organ with a rotating speaker, holding the rack's chords."

    volume = RankedKeys.volume.replace(default=0.7)
    # 16', 5 1/3', 8', 4', 2 2/3', 2', 1 3/5', 1 1/3', 1': the harmonic of the
    # note each drawbar's pipe sounds
    ranks = (0.5, 1.5, 1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 8.0)
    # each step of a drawbar is this many dB, the organ's own
    drawbar_step: ClassVar[float] = 3.0
    drawbar_steps: ClassVar[int] = 8
    # the ratio the percussion chimes at: the second or the third harmonic
    percussion_ratios: ClassVar[tuple[float, float]] = (2.0, 3.0)
    # the ranks' level, which the percussion and the click are set against
    gain = 0.022
    # how fast the percussion's pluck starts, and its level at full Percussion
    # as a multiple of one rank's
    percussion_attack: ClassVar[float] = 0.002
    percussion_boost: ClassVar[float] = 1.5
    # the click's length and brightness, and its level at full Key click as a
    # multiple of one rank's
    click_decay: ClassVar[float] = 0.008
    click_freq: ClassVar[float] = 2500.0
    click_boost: ClassVar[float] = 5.0
    # the rotor: seconds it takes to speed up, the tremolo's depth and the
    # delay's swing (s) at full Leslie, and the delay it swings about
    rotor_ramp: ClassVar[float] = 1.2
    rotor_tremolo_max: ClassVar[float] = 0.35
    rotor_doppler_max: ClassVar[float] = 0.0004
    rotor_doppler_base: ClassVar[float] = 0.0006
    # the preamp's `Disto` slope, the most drive it takes (`Disto` divides by
    # 1 - drive, so full drive would be infinite gain), and the level a
    # held chord reaches it at, which the preamp's makeup keeps it to
    preamp_slope: ClassVar[float] = 0.6
    max_drive: ClassVar[float] = 0.9
    preamp_peak: ClassVar[float] = 0.05

    perc_ratio: SigTo
    perc_pitch: PyoObject
    perc_env: Adsr
    perc_level: SigTo
    perc_amp: PyoObject
    perc_gain: PyoObject
    perc_tone: Sine
    perc_bank: Mix
    click_noise: Noise
    click_tone: ButHP
    click_env: Adsr
    click_level: SigTo
    click_amp: PyoObject
    clicking: PyoObject
    clicked: PyoObject
    rotor_speed: SigTo
    rotor_depth: SigTo
    rotor_lfo: Sine
    rotor_tremolo_swing: PyoObject
    rotor_tremolo: PyoObject
    rotor_delay_swing: PyoObject
    rotor_delay_time: PyoObject
    rotor_doppler: Delay
    rotating: PyoObject
    preamp: Disto
    played: PyoObject

    attack = RankedKeys.attack.replace(default=0.01)
    release = RankedKeys.release.replace(default=0.12)
    legato = RankedKeys.legato.replace(default=0.9)
    vibrato = RankedKeys.vibrato.replace(
        help_text="How far the scanner vibrato rocks the pitch, in cents; none is a steady, tonewheel-pure note, a lot is the wide, swirling vibrato of a chorus-vibrato organ."
    )
    reverb_size = Reverb.reverb_size.replace(default=0.5)
    reverb_bal = Reverb.reverb_bal.replace(default=0.15)

    @Param(
        0,
        8,
        1,
        8,
        "Sub 16'",
        "The 16' drawbar, a note an octave below: adds a deep, hollow foundation and a weight like a big pipe organ.",
        sweep=True,
    )
    def sub(self, value: float) -> None:
        self.apply_ranks()

    @Param(
        0,
        8,
        1,
        0,
        "Sub-fifth 5⅓'",
        "The 5⅓' drawbar, a fifth above that sub-octave: adds a dark, reedy, slightly hollow body.",
        sweep=True,
    )
    def sub_fifth(self, value: float) -> None:
        self.apply_ranks()

    @Param(
        0,
        8,
        1,
        8,
        "Fundamental 8'",
        "The 8' drawbar, the note itself: the plain, round centre of the tone.",
        sweep=True,
    )
    def fundamental(self, value: float) -> None:
        self.apply_ranks()

    @Param(
        0,
        8,
        1,
        6,
        "Octave 4'",
        "The 4' drawbar, an octave above: adds clarity and a flute-like sweetness.",
        sweep=True,
    )
    def octave(self, value: float) -> None:
        self.apply_ranks()

    @Param(
        0,
        8,
        1,
        0,
        "Twelfth 2⅔'",
        "The 2⅔' drawbar, an octave and a fifth above: adds a nasal, reedy brightness like a clarinet.",
        sweep=True,
    )
    def twelfth(self, value: float) -> None:
        self.apply_ranks()

    @Param(
        0,
        8,
        1,
        4,
        "Fifteenth 2'",
        "The 2' drawbar, two octaves above: adds shimmer and a bright, pealing edge.",
        sweep=True,
    )
    def fifteenth(self, value: float) -> None:
        self.apply_ranks()

    @Param(
        0,
        8,
        1,
        0,
        "Tierce 1⅗'",
        "The 1⅗' drawbar, a major third three octaves above: adds a hard, hollow, woodwind bite.",
        sweep=True,
    )
    def tierce(self, value: float) -> None:
        self.apply_ranks()

    @Param(
        0,
        8,
        1,
        0,
        "Nazard 1⅓'",
        "The 1⅓' drawbar, a fifth above that: adds a thin, buzzing, reedy sparkle.",
        sweep=True,
    )
    def nazard(self, value: float) -> None:
        self.apply_ranks()

    @Param(
        0,
        8,
        1,
        0,
        "Fife 1'",
        "The 1' drawbar, three octaves above: adds a piercing, whistling top that makes a full chorus cut.",
        sweep=True,
    )
    def fife(self, value: float) -> None:
        self.apply_ranks()

    @Param(
        0,
        1,
        0.05,
        0.35,
        "Percussion",
        "A chime that dies away on the front of every note, like the organ's percussion switch; none is a smooth, steady organ, high is a bright, plucky, bell-like attack.",
        sweep=True,
    )
    def percussion(self, value: float) -> None:
        self.perc_level.value = value * self.gain * self.percussion_boost

    @Param(
        0,
        1,
        1,
        1,
        "Percussion pitch",
        "Which harmonic the percussion chimes on; 0 is the second harmonic, a round, mellow pluck, 1 is the third, a brighter, more bell-like one.",
        advanced=True,
    )
    def percussion_pitch(self, value: float) -> None:
        self.perc_ratio.value = self.percussion_ratios[round(value)]

    @Param(
        0.05,
        0.8,
        0.01,
        0.25,
        "Percussion decay",
        "How long the percussion's chime rings on each note, in seconds; short is a quick tick, long is a lingering, bell-like ping.",
        sweep=True,
        advanced=True,
    )
    def percussion_decay(self, value: float) -> None:
        self.perc_env.decay = value
        self.perc_env.dur = self.percussion_attack + value + self.perc_env.release

    @Param(
        0,
        1,
        0.05,
        0.3,
        "Key click",
        "The tick of the contacts as a key is pressed; none is a clean, silent entry, high is the clicking, throbbing attack of a vintage organ.",
        sweep=True,
    )
    def click(self, value: float) -> None:
        self.click_level.value = value * self.gain * self.click_boost

    @Param(
        0,
        1,
        0.05,
        0.5,
        "Leslie",
        "How much the rotating speaker turns the sound; none is the straight organ, a little is a slow, swirling shimmer, a lot is a dizzying, wobbling whirl.",
        sweep=True,
    )
    def leslie(self, value: float) -> None:
        self.rotor_depth.value = value

    @Param(
        0.4,
        7.5,
        0.1,
        0.8,
        "Rotor speed",
        "How fast the speaker's rotors turn, in cycles a second; slow is the lazy, rolling chorale, fast is the whirling tremolo, and the rotors take a moment to speed up or slow down.",
        sweep=True,
    )
    def rotor_rate(self, value: float) -> None:
        self.rotor_speed.value = value

    @Param(
        0,
        1,
        0.05,
        0.25,
        "Drive",
        "How hard the tube preamp is pushed; none is clean and glassy, a little is a warm, gritty edge, a lot is a roaring, overdriven blues organ.",
        sweep=True,
    )
    def drive(self, value: float) -> None:
        drive = value * self.max_drive
        gain = 2 * drive / (1 - drive)
        self.preamp.drive = drive
        self.preamp.mul = (1 + gain * self.preamp_peak) / (1 + gain)

    def rank_values(self) -> list[float]:
        return [
            self.drawbar_level(setting)
            for setting in (
                self.sub,
                self.sub_fifth,
                self.fundamental,
                self.octave,
                self.twelfth,
                self.fifteenth,
                self.tierce,
                self.nazard,
                self.fife,
            )
        ]

    def drawbar_level(self, setting: float) -> float:
        """A drawbar's level (0 to 1) at `setting` (0 off, 8 loudest): each step
        below the top is `drawbar_step` dB quieter."""
        if setting <= 0:
            return 0.0
        return 10 ** (-(self.drawbar_steps - setting) * self.drawbar_step / 20)

    def rank_tone(self, freq: PyoObject, level: PyoObject) -> PyoObject:
        return Sine(freq=freq, mul=level)

    def make_tone(self) -> PyoObject:
        drawbars = super().make_tone()
        # the percussion: a second or third harmonic that dies on every key press
        self.perc_ratio = SigTo(value=self.percussion_ratios[1], time=0.02)
        self.perc_pitch = self.held_pitch * self.perc_ratio
        self.perc_env = Adsr(
            attack=self.percussion_attack, decay=0.25, sustain=0, release=0.05, dur=0.3
        )
        self.perc_level = SigTo(value=0, time=0.05)
        self.perc_amp = self.perc_env * self.perc_level
        self.perc_gain = self.voice_gain * self.perc_amp
        self.perc_tone = Sine(freq=self.perc_pitch, mul=self.perc_gain)
        self.perc_bank = Mix(self.perc_tone, voices=1)
        return drawbars + self.perc_bank

    def voice_stage(self, signal: PyoObject) -> PyoObject:
        # the contacts' click, on the front of every key press
        self.click_noise = Noise()
        self.click_tone = ButHP(self.click_noise, freq=self.click_freq)
        self.click_env = Adsr(
            attack=0.0005,
            decay=self.click_decay,
            sustain=0,
            release=0.004,
            dur=0.0005 + self.click_decay + 0.004,
        )
        self.click_level = SigTo(value=0, time=0.05)
        self.click_amp = self.click_env * self.click_level
        self.clicking = self.click_tone * self.click_amp
        self.clicked = signal + self.clicking

        # the rotating speaker: a swinging delay (the Doppler bend) and a pulsing level
        self.rotor_speed = SigTo(value=0.8, time=self.rotor_ramp)
        self.rotor_depth = SigTo(value=0, time=0.05)
        self.rotor_lfo = Sine(freq=self.rotor_speed)
        self.rotor_tremolo_swing = self.rotor_depth * self.rotor_tremolo_max
        self.rotor_tremolo = self.rotor_lfo * self.rotor_tremolo_swing + 1
        self.rotor_delay_swing = self.rotor_depth * self.rotor_doppler_max
        self.rotor_delay_time = (
            self.rotor_lfo * self.rotor_delay_swing + self.rotor_doppler_base
        )
        self.rotor_doppler = Delay(
            self.clicked, delay=self.rotor_delay_time, maxdelay=0.01
        )
        self.rotating = self.rotor_doppler * self.rotor_tremolo

        self.preamp = Disto(self.rotating, drive=0, slope=self.preamp_slope)
        self.played = self.add_reverb(self.preamp)
        return self.played

    def on_note(self, notes: list[float], bar_index: int) -> None:
        self.perc_env.play()
        self.click_env.play()
