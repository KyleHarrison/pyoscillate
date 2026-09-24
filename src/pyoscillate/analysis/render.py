"""Offline rendering of a single patch to raw samples.

Each render runs in its own subprocess: pyo keeps one native server per
process and does not reliably survive repeated boot/shutdown cycles, so a
fresh interpreter per render is what keeps renders isolated from each other.
"""

from __future__ import annotations

import importlib
import inspect
import json
import subprocess
import sys
import tempfile
import wave
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np

SAMPLE_RATE = 44100
# fixed seed so noise-based patches render the same samples every run
SEED = 1
DEFAULT_BPM = 120
DEFAULT_TICKS_PER_BAR = 32
# 32-bit int keeps quiet tails (-60 dB and below) well above quantisation
SAMPLE_TYPE_INT32 = 2
INT32_SCALE = 2**31


@dataclass(frozen=True)
class Render:
    """Mono samples (first output channel) in -1..1, plus the sample rate."""

    samples: np.ndarray
    sample_rate: int

    @property
    def duration(self) -> float:
        return len(self.samples) / self.sample_rate


def render(
    module: str,
    params: dict[str, Any] | None = None,
    *,
    seconds: float = 1.0,
    bpm: float = DEFAULT_BPM,
    clock_running: bool = True,
    volume: float | None = None,
) -> Render:
    """Build `module`'s patch with `params`, start it, and render `seconds`
    of its output offline in a fresh subprocess.

    With `clock_running=False` the patch is started but never receives a
    tick, so anything audible was not scheduled by its sequencer.

    `volume` defaults to the module's `VOLUME_DEFAULT` (the level its volume
    slider starts at), so the render passes through the output limiter the way the
    listener hears it.
    """
    with tempfile.TemporaryDirectory() as directory:
        path = Path(directory) / "render.wav"
        request = {
            "module": module,
            "params": params or {},
            "seconds": seconds,
            "bpm": bpm,
            "clock_running": clock_running,
            "volume": volume,
            "path": str(path),
        }
        result = subprocess.run(
            [sys.executable, "-m", "pyoscillate.analysis.render", json.dumps(request)],
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode != 0:
            raise RuntimeError(f"rendering {module} failed:\n{result.stderr}")
        return _read_wav(path)


def _read_wav(path: Path) -> Render:
    with wave.open(str(path), "rb") as file:
        channels = file.getnchannels()
        if file.getsampwidth() != 4:
            raise ValueError(
                f"expected 32-bit samples, got {file.getsampwidth() * 8}-bit"
            )
        frames = np.frombuffer(file.readframes(file.getnframes()), dtype="<i4")
        rate = file.getframerate()
    return Render(
        samples=frames[::channels].astype(np.float64) / INT32_SCALE,
        sample_rate=rate,
    )


def _render_in_process(request: dict[str, Any]) -> None:
    """Subprocess body: boot an offline server, run the patch, write a wav."""
    from pyo.lib.server import Server

    from pyoscillate.clock import Clock
    from pyoscillate.tempo import Tempo

    server = Server(sr=SAMPLE_RATE, nchnls=2, duplex=0, audio="offline")
    server.setGlobalSeed(SEED)
    server.boot()
    server.recordOptions(
        dur=request["seconds"],
        filename=request["path"],
        fileformat=0,
        sampletype=SAMPLE_TYPE_INT32,
    )

    module = importlib.import_module(request["module"])
    build = module.build
    tempo = Tempo(bpm=request["bpm"])
    clock = Clock(tempo, ticks_per_bar=DEFAULT_TICKS_PER_BAR)
    context = {"tempo": tempo, "clock": clock}
    accepted = inspect.signature(build).parameters
    kwargs = {name: value for name, value in context.items() if name in accepted}

    # keep the patch and clock referenced for the whole render so their
    # pyo graph (including `resources`) cannot be collected mid-render
    patch = build(**kwargs, **request["params"])
    volume = request["volume"]
    patch.volume = (
        volume if volume is not None else getattr(module, "VOLUME_DEFAULT", 1.0)
    )
    patch.start()
    if request["clock_running"]:
        clock.start()
    # offline start() blocks until `dur` seconds have been written
    server.start()
    patch.stop()
    clock.stop()
    server.shutdown()


if __name__ == "__main__":
    _render_in_process(json.loads(sys.argv[1]))
