from __future__ import annotations

from dataclasses import dataclass


@dataclass(eq=False)
class ContinuousSequencer:
    """No-op `Sequencer` for psyambient's purely continuous, non-triggered patches.

    These pads are wired entirely from free-running modulators (chaotic
    attractors, LFOs) feeding a generator's parameters directly - once the
    pyo objects exist they process every buffer on their own, with nothing
    that needs a `Pattern`/`Metro` to start or stop ticking. `Patch` still
    requires a `Sequencer` to call `play()`/`stop()` on, so this just
    satisfies that protocol with nothing to actually do.
    """

    def play(self) -> None:
        pass

    def stop(self) -> None:
        pass
