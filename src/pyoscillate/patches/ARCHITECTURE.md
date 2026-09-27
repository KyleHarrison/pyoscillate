# Patch framework architecture

This describes the shared framework every patch is built on top of —
`base.py`, `common.py`, `params.py`, and their relationship to `Clock`. It is
not a class-by-class reference; read those modules for that. This is the
concept the code implements: **one inherited definition of what a patch is
and how it behaves, held in a single place, so a change to that definition
updates every patch family at once instead of being copy-pasted into each
one.**

Every family-specific detail (a kick's envelope shape, a bass's oscillator
choice) lives in that family's own module. Everything a patch has *in
common with every other patch* — how it's constructed, how its graph comes
to life, how it hears about tempo, how a slider reaches the running audio —
lives here, once, on `Patch` and its two archetype subclasses. A family
module never reimplements any of this; it only fills in the parts that
make it a kick instead of a bass.

## Why one shared base instead of per-family code

Without a shared base, each patch family would need its own answer to: how
do I stay inert until the audio server exists, how do I not leak a Pyo
object into a dangling native segfault, how do I let a slider move the
running graph, how do I share a clock with every other patch in the rack.
Those are not musical questions — they're the same answer for a kick, a
bass, and a drone. Centralizing that answer in `Patch` (plus the
`GatedVoice`/`ContinuousVoice` archetypes) means:

- the resource-retention discipline that prevents a segfault is enforced
  once, in `_bind()`, not audited per family
- the parameter/control contract (`Param`) is one descriptor every family
  gets for free, not a hand-rolled `controls` dict per module
- a shared timing source (`Clock`) is subscribed to the same way by every
  clocked voice, so "every 2nd tick" means the same tick for the whole rack
- fixing or improving any of the above is a change to one file, inherited
  everywhere, instead of a sweep across every patch module

A family module's job is narrowed to exactly what makes it musically
distinct: its graph, its parameters, its sound.

## Construction vs. `build()`: two separate lifecycle stages

A `Patch` instance exists in two different states, and the framework keeps
them deliberately separate rather than collapsing them into one step.

**Construction** (`Patch()`) happens at rack-definition time, before any
audio server exists. It only seeds this instance's current parameter values
from class defaults and sets up bookkeeping — no Pyo object is created, so
an entire rack of patches (most of which a user never switches on) can be
listed and inspected for free.

**`build()`** is what actually materializes the Pyo graph: the point where
oscillators, envelopes, and filters are constructed and wired together on
`self`. It only runs once a real audio server (and the shared `Tempo`/
`Clock`, and `Harmony` if the patch needs it) exists, and it is
**repeatable on the same instance** — a rebuild reruns `build()` when a
structural parameter changes or a patch is switched back on, replacing the
graph in place rather than constructing a new `Patch` object. Every
concrete family's `build()` follows the same shape: reset, construct the
graph, hand off to `finish()`. `finish()` is the one place that closes the
loop — it retains everything the graph needs to stay alive, and runs every
parameter's control once so the graph starts in the state its current
values describe. That shape lives once on the archetype base classes
(`GatedVoice`/`ContinuousVoice`); a family's `build()` only ever adds the
graph and calls it.

Because construction and `build()` are separate, a patch can be freely
reconfigured — new values, new presets — without ever touching audio, and
audio is only ever (re)built when something actually needs to play.

## Connecting to shared state: `Clock` and `Tempo`

Patches don't own their own timer. A single `Clock`, driven by one shared
`Tempo`, ticks once per project and every clocked patch subscribes a
division of that master pulse rather than running an independent `Pattern`.
This is the same "one shared source of truth" idea as the base class: if
each patch ran its own timer, two patches could drift out of phase with
each other the moment one of them rebuilt. Subscribing to the same clock
instead means every patch's "every Nth tick" always refers to the same
tick, and a patch that rebuilds mid-session resubscribes into the clock's
current position rather than resetting its own phase to zero.

`Tempo`/`Clock`/`Harmony` are handed into `build()` as arguments (not stored
on the class, not looked up globally) precisely because they're
rack-level, project-scoped state that doesn't exist until the audio engine
does — a patch's musical behavior is a function of the clock and harmony it
was built against, not something it manufactures itself.

## Parameters: one declaration, three roles at once

A slider is declared exactly once, as a `Param`-decorated method on the
family class, and that single declaration plays three roles that would
otherwise be three separate, driftable pieces of state:

1. The **slider contract** — its range, default, and label — is data on the
   class, shared by every instance and every style.
2. The **current value** is per-instance state the same descriptor stores;
   reading `self.<name>` always returns this instance's live setting.
3. The **control** — the decorated method body — is how a new value reaches
   the already-running Pyo graph, called automatically whenever the value
   changes after the patch is built.

The point of merging these is that a parameter's meaning is asserted once.
There is no second dict mapping names to setter functions, no shadow copy of
current values kept anywhere else (in the UI layer, in a preset loader);
`self.<name>` is the only place a value lives, and assigning it — directly,
through `set()`, or through `configure()` for several at once — is
sufficient to update both the stored value and the running graph. A style
subclass that needs a different range or default overrides just that one
declaration and keeps the same control; it never needs to touch how the
control reaches the graph.

Parameters that would change the graph's topology rather than a running
value are declared the same way but without a control — the framework
treats them as staged state a caller rebuilds against, not something it can
push live.

## What this buys a new patch author

Writing a new patch family means writing the graph and the `Param`
declarations that make it musically distinct. Everything else — staying
inert before the server boots, surviving a rebuild without leaking or
crashing, staying in sync with the rack's shared clock, and getting a
working slider-to-graph connection for free — comes from inheriting
`Patch` and the right archetype base. See
[AGENTS.md](AGENTS.md) for the concrete contract that shape has to satisfy.
