import math
from enum import Enum

# pitch-class names, spelled as the rack's key picker spells them
NOTE_NAMES = ("C", "C#", "D", "Eb", "E", "F", "F#", "G", "Ab", "A", "Bb", "B")


class Note(float, Enum):
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


def midi_to_freq(note: float) -> float:
    """Equal-tempered frequency (Hz) of MIDI note `note`, with A4 = 69 = 440 Hz."""
    return 440 * 2 ** ((note - 69) / 12)


def freq_to_midi(freq: float) -> float:
    """MIDI note number of `freq` Hz; fractional when `freq` is between notes."""
    return 69 + 12 * math.log2(freq / 440)


def semitone_ratio(semitones: float) -> float:
    """Frequency ratio of a pitch shift of `semitones`."""
    return 2 ** (semitones / 12)


def transpose(freq: float, semitones: float) -> float:
    """`freq` Hz shifted by `semitones`."""
    return freq * semitone_ratio(semitones)


def nearest_note(freq: float) -> float:
    """The equal-tempered note frequency closest to `freq` Hz."""
    return midi_to_freq(round(freq_to_midi(freq)))


def note_name(freq: float) -> str:
    """Scientific pitch name of the note nearest `freq` Hz, e.g. 55 -> "A1",
    spelled as the rack's key picker spells it."""
    note = round(freq_to_midi(freq))
    return f"{NOTE_NAMES[note % 12]}{note // 12 - 1}"


# Short aliases as plain floats, so importing individual notes remains clean;
# pyo type-checks arguments exactly and rejects the `Note` members themselves.
C0 = Note.C0.value
Cs0 = Note.Cs0.value
D0 = Note.D0.value
Ds0 = Note.Ds0.value
E0 = Note.E0.value
F0 = Note.F0.value
Fs0 = Note.Fs0.value
G0 = Note.G0.value
Gs0 = Note.Gs0.value
A0 = Note.A0.value
As0 = Note.As0.value
B0 = Note.B0.value

C1 = Note.C1.value
Cs1 = Note.Cs1.value
D1 = Note.D1.value
Ds1 = Note.Ds1.value
E1 = Note.E1.value
F1 = Note.F1.value
Fs1 = Note.Fs1.value
G1 = Note.G1.value
Gs1 = Note.Gs1.value
A1 = Note.A1.value
As1 = Note.As1.value
B1 = Note.B1.value

C2 = Note.C2.value
Cs2 = Note.Cs2.value
D2 = Note.D2.value
Ds2 = Note.Ds2.value
E2 = Note.E2.value
F2 = Note.F2.value
Fs2 = Note.Fs2.value
G2 = Note.G2.value
Gs2 = Note.Gs2.value
A2 = Note.A2.value
As2 = Note.As2.value
B2 = Note.B2.value

C3 = Note.C3.value
Cs3 = Note.Cs3.value
D3 = Note.D3.value
Ds3 = Note.Ds3.value
E3 = Note.E3.value
F3 = Note.F3.value
Fs3 = Note.Fs3.value
G3 = Note.G3.value
Gs3 = Note.Gs3.value
A3 = Note.A3.value
As3 = Note.As3.value
B3 = Note.B3.value

C4 = Note.C4.value
Cs4 = Note.Cs4.value
D4 = Note.D4.value
Ds4 = Note.Ds4.value
E4 = Note.E4.value
F4 = Note.F4.value
Fs4 = Note.Fs4.value
G4 = Note.G4.value
Gs4 = Note.Gs4.value
A4 = Note.A4.value
As4 = Note.As4.value
B4 = Note.B4.value

C5 = Note.C5.value
Cs5 = Note.Cs5.value
D5 = Note.D5.value
Ds5 = Note.Ds5.value
E5 = Note.E5.value
F5 = Note.F5.value
Fs5 = Note.Fs5.value
G5 = Note.G5.value
Gs5 = Note.Gs5.value
A5 = Note.A5.value
As5 = Note.As5.value
B5 = Note.B5.value

C6 = Note.C6.value
Cs6 = Note.Cs6.value
D6 = Note.D6.value
Ds6 = Note.Ds6.value
E6 = Note.E6.value
F6 = Note.F6.value
Fs6 = Note.Fs6.value
G6 = Note.G6.value
Gs6 = Note.Gs6.value
A6 = Note.A6.value
As6 = Note.As6.value
B6 = Note.B6.value

C7 = Note.C7.value
Cs7 = Note.Cs7.value
D7 = Note.D7.value
Ds7 = Note.Ds7.value
E7 = Note.E7.value
F7 = Note.F7.value
Fs7 = Note.Fs7.value
G7 = Note.G7.value
Gs7 = Note.Gs7.value
A7 = Note.A7.value
As7 = Note.As7.value
B7 = Note.B7.value

C8 = Note.C8.value
Cs8 = Note.Cs8.value
D8 = Note.D8.value
Ds8 = Note.Ds8.value
E8 = Note.E8.value
F8 = Note.F8.value
Fs8 = Note.Fs8.value
G8 = Note.G8.value
Gs8 = Note.Gs8.value
A8 = Note.A8.value
As8 = Note.As8.value
B8 = Note.B8.value

C9 = Note.C9.value
Cs9 = Note.Cs9.value
D9 = Note.D9.value
Ds9 = Note.Ds9.value
E9 = Note.E9.value
F9 = Note.F9.value
Fs9 = Note.Fs9.value
G9 = Note.G9.value
Gs9 = Note.Gs9.value
A9 = Note.A9.value
As9 = Note.As9.value
B9 = Note.B9.value

C10 = Note.C10.value
Cs10 = Note.Cs10.value
D10 = Note.D10.value
Ds10 = Note.Ds10.value
E10 = Note.E10.value
F10 = Note.F10.value
Fs10 = Note.Fs10.value
G10 = Note.G10.value
Gs10 = Note.Gs10.value
A10 = Note.A10.value
As10 = Note.As10.value
B10 = Note.B10.value
