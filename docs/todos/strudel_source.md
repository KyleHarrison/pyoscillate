Yes. The screenshot is **very clearly based on Strudel**, rather than being a proprietary synthesis framework built from scratch.

### What Switch Angel is using

The underlying system is **Strudel**, an open-source browser-based live-coding environment. Strudel is essentially a JavaScript implementation of the pattern language pioneered by TidalCycles. Its audio engine uses Web Audio. ([Strudel][1])

The giveaway in your screenshot is code like:

```js
n("<0 4 0 9 7>*16")
  .scale("g:minor")
  .trans(-12)
.o(3)
.s("sawtooth")
.acidenv(slider(0.763))
._pianoroll()
```

Those are **Strudel idioms**, including:

* `n(...)` for note patterns
* `.scale(...)`
* `.trans(...)`
* `.s("sawtooth")`
* `.o(...)` for audio orbits
* `slider(...)`
* `._pianoroll()`

### But there is an interesting second layer

Switch Angel has her **own open-source extension layer on top of Strudel**:

[Switch Angel's strudel-scripts repository](https://github.com/switchangel/strudel-scripts)

The repository describes itself as:

> "my custom strudel scripts that haven't made it in to strudel for whatever reason" ([GitHub][2])

And this is where things become particularly relevant to the synthesis framework you've been working on.

Her `prebake.strudel` contains custom functions such as:

```js
register('acidenv', ...)
register('o', ...)
register('rlpf', ...)
register('rhpf', ...)
register('trancegate', ...)
register('vstruct', ...)
```

It also contains custom synthesis abstractions such as:

```js
window.DX = (...)
register('acid', ...)
```

and even a **text-to-synthesis function**:

```js
window.stxt = register('stxt', (text, pat) => {
    ...
})
```

That function maps text bytes onto synthesis parameters such as:

```text
lpf
room
vib
vibmod
wt
note
wtrate
wtdepth
delay
delaytime
delayfeedback
decay
attack
lpenv
lpd
lpa
detune
s
```

with the available oscillator types including:

```text
sawtooth
supersaw
wt_digital
sine
triangle
pulse
```

([GitHub][3])

### So the architecture is roughly

```text
                TidalCycles
                    │
                    ▼
                 Strudel
          JavaScript live coding
                    │
          ┌─────────┴─────────┐
          ▼                   ▼
     Pattern system       Web Audio
          │                   │
          └─────────┬─────────┘
                    ▼
          Switch Angel's
          custom extensions
                    │
       ┌────────────┼─────────────┐
       ▼            ▼             ▼
    acidenv      trancegate      stxt
    rlpf         vstruct         acid
    rhpf         custom FX       DX
```

So **the synthesis primitives aren't hers**, but she has built a fairly substantial *musical abstraction layer* over Strudel.

### This is actually quite relevant to your pyo project

There is a significant conceptual similarity with what you've been trying to build.

Your project has been heading toward:

```text
musical description
       ↓
musical affordances
       ↓
DSP components
       ↓
parameter relationships
       ↓
patch
```

Switch Angel's `strudel-scripts` demonstrates a much simpler version of exactly this idea:

```text
musical concept
      ↓
custom Strudel abstraction
      ↓
Strudel DSP parameters
```

For example, instead of requiring the performer to construct a filter envelope manually, she creates:

```js
.acidenv(slider(...))
```

which hides:

```js
.lpf(100)
.lpenv(x * 9)
.lps(.2)
.lpd(.12)
.lpq(2)
```

That's a **musical affordance**. `acidenv` communicates something much closer to "acid-style filter envelope" than the underlying DSP API does.

And that's probably the most interesting thing in the screenshot from the perspective of your agentic synth work.

### One important distinction

Strudel itself is open source, currently under AGPL, and its source has moved from GitHub to Codeberg. ([Strudel][1])

Switch Angel's additional scripts are also public on GitHub. ([GitHub][2])

So you can actually inspect **both layers** rather than trying to reverse engineer the screenshot.

The Switch Angel repo is only about **30 commits and ~1,300 lines in its current `prebake.strudel`**, so it is surprisingly approachable as a case study. ([GitHub][3])

**The particularly interesting part for you is not the Strudel engine. It's her custom abstraction layer.** It is an example of how a relatively low-level synthesis API can be wrapped in semantically meaningful musical operations, which is very close to the "musical affordances" layer you identified as missing in your pyo agent system.

[1]: https://strudel.cc/ "Strudel REPL"
[2]: https://github.com/switchangel/strudel-scripts "GitHub - switchangel/strudel-scripts: my custom strudel scripts that haven't made it in to strudel for whatever reason · GitHub"
[3]: https://github.com/switchangel/strudel-scripts/blob/main/prebake.strudel "strudel-scripts/prebake.strudel at main · switchangel/strudel-scripts · GitHub"
