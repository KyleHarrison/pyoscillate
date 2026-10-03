"""Pitch: the note table and the frequency math every pitched patch shares."""

from __future__ import annotations

import math


class Note:
    """Equal-tempered note frequencies in Hz, A4 = 440, as plain float class
    attributes (`Note.F3`, sharps spelled `Fs3`). Plain floats, not an enum:
    pyo type-checks arguments exactly and rejects enum members. Pitch-class
    constants (`Note.KEY_C`) are semitones above C for a rack's key."""

    # pitch-class names, spelled as the rack's key picker spells them
    NAMES = ("C", "C#", "D", "Eb", "E", "F", "F#", "G", "Ab", "A", "Bb", "B")

    # pitch class of C, for a rack whose vamp is easiest to name off a major-key
    # centre (e.g. roman-numeral chords built from scale degrees)
    KEY_C = 0
    # pitch class of F, for the dark psytrance racks
    KEY_F = 5
    # pitch class of A, the default key for racks that don't choose one
    KEY_A = 9

    C0 = 16.352

    Cs0 = 17.324
    D0 = 18.354
    Ds0 = 19.445
    E0 = 20.602
    F0 = 21.827
    Fs0 = 23.125
    G0 = 24.500
    Gs0 = 25.957
    A0 = 27.500
    As0 = 29.135
    B0 = 30.868

    C1 = 32.703

    Cs1 = 34.648
    D1 = 36.708
    Ds1 = 38.891
    E1 = 41.203
    F1 = 43.654
    Fs1 = 46.249
    G1 = 48.999
    Gs1 = 51.913
    A1 = 55.000
    As1 = 58.270
    B1 = 61.735

    C2 = 65.406

    Cs2 = 69.296
    D2 = 73.416
    Ds2 = 77.782
    E2 = 82.407
    F2 = 87.307
    Fs2 = 92.499
    G2 = 97.999
    Gs2 = 103.826
    A2 = 110.000
    As2 = 116.541
    B2 = 123.471

    C3 = 130.813

    Cs3 = 138.591
    D3 = 146.832
    Ds3 = 155.563
    E3 = 164.814
    F3 = 174.614
    Fs3 = 184.997
    G3 = 195.998
    Gs3 = 207.652
    A3 = 220.000
    As3 = 233.082
    B3 = 246.942

    C4 = 261.626

    Cs4 = 277.183
    D4 = 293.665
    Ds4 = 311.127
    E4 = 329.628
    F4 = 349.228
    Fs4 = 369.994
    G4 = 391.995
    Gs4 = 415.305
    A4 = 440.000
    As4 = 466.164
    B4 = 493.883

    C5 = 523.251

    Cs5 = 554.365
    D5 = 587.330
    Ds5 = 622.254
    E5 = 659.255
    F5 = 698.456
    Fs5 = 739.989
    G5 = 783.991
    Gs5 = 830.609
    A5 = 880.000
    As5 = 932.328
    B5 = 987.767

    C6 = 1046.502

    Cs6 = 1108.731
    D6 = 1174.659
    Ds6 = 1244.508
    E6 = 1318.510
    F6 = 1396.913
    Fs6 = 1479.978
    G6 = 1567.982
    Gs6 = 1661.219
    A6 = 1760.000
    As6 = 1864.655
    B6 = 1975.533

    C7 = 2093.005

    Cs7 = 2217.461
    D7 = 2349.318
    Ds7 = 2489.016
    E7 = 2637.020
    F7 = 2793.826
    Fs7 = 2959.955
    G7 = 3135.963
    Gs7 = 3322.438
    A7 = 3520.000
    As7 = 3729.310
    B7 = 3951.066

    C8 = 4186.009

    Cs8 = 4434.922
    D8 = 4698.636
    Ds8 = 4978.032
    E8 = 5274.041
    F8 = 5587.652
    Fs8 = 5919.911
    G8 = 6271.927
    Gs8 = 6644.875
    A8 = 7040.000
    As8 = 7458.620
    B8 = 7902.133

    C9 = 8372.018

    Cs9 = 8869.844
    D9 = 9397.273
    Ds9 = 9956.063
    E9 = 10548.082
    F9 = 11175.303
    Fs9 = 11839.822
    G9 = 12543.854
    Gs9 = 13289.750
    A9 = 14080.000
    As9 = 14917.240
    B9 = 15804.266

    C10 = 16744.036

    Cs10 = 17739.688
    D10 = 18794.545
    Ds10 = 19912.127
    E10 = 21096.164
    F10 = 22350.607
    Fs10 = 23679.643
    G10 = 25087.708
    Gs10 = 26579.501
    A10 = 28160.000
    As10 = 29834.481
    B10 = 31608.531

    @staticmethod
    def midi_to_freq(note: float) -> float:
        """Equal-tempered frequency (Hz) of MIDI note `note`, with A4 = 69 = 440 Hz."""
        return 440 * 2 ** ((note - 69) / 12)

    @staticmethod
    def freq_to_midi(freq: float) -> float:
        """MIDI note number of `freq` Hz; fractional when `freq` is between notes."""
        return 69 + 12 * math.log2(freq / 440)

    @staticmethod
    def semitone_ratio(semitones: float) -> float:
        """Frequency ratio of a pitch shift of `semitones`."""
        return 2 ** (semitones / 12)

    @staticmethod
    def transpose(freq: float, semitones: float) -> float:
        """`freq` Hz shifted by `semitones`."""
        return freq * Note.semitone_ratio(semitones)

    @staticmethod
    def nearest(freq: float) -> float:
        """The equal-tempered note frequency closest to `freq` Hz."""
        return Note.midi_to_freq(round(Note.freq_to_midi(freq)))

    @staticmethod
    def name(freq: float) -> str:
        """Scientific pitch name of the note nearest `freq` Hz, e.g. 55 -> "A1",
        spelled as the rack's key picker spells it."""
        note = round(Note.freq_to_midi(freq))
        return f"{Note.NAMES[note % 12]}{note // 12 - 1}"
