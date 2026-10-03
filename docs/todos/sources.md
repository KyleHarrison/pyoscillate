## Latest

| Repository                                                                                       | What it gives you                                                          | Fit to your architecture                  |
| ------------------------------------------------------------------------------------------------ | -------------------------------------------------------------------------- | ----------------------------------------- |
| [belangeo/zyne](https://github.com/belangeo/zyne)                         | Modular synth built *on top of pyo*, with module classes and connections   | **Very high**                             |
| [belangeo/pyo-tools](https://github.com/belangeo/pyo-tools)               | Reusable higher-level DSP classes composed from pyo objects                | **High**                                  |
| [belangeo/pyo](https://github.com/belangeo/pyo)                           | The underlying `PyoObject` object graph itself                             | **Very high, but lower-level**            |
| [alexandrepoirier/PyoSynth](https://github.com/alexandrepoirier/PyoSynth) | Runtime manipulation of pyo scripts, MIDI-controlled parameters and voices | **Medium-high**                           |
| [tiagovaz/pyo-collection](https://github.com/tiagovaz/pyo-collection)     | Extensive examples showing composition of pyo graphs                       | **Useful reference, less framework-like** |


## Sources that cover several patches

| Source | Access | Why it fits |
|---|---|---|
| [Synth Secrets, Gordon Reid (Sound On Sound)](https://www.soundonsound.com/series/synth-secrets-sound-sound): 63 parts, 1999–2004 | Free | The closest match to your drum source. Each part explains how a real sound works acoustically and then how to patch it. Still used as course reading. |
| [The Theory and Technique of Electronic Music, Miller Puckette](https://msp.ucsd.edu/techniques/latest/book.pdf) | Free, from the author | DSP theory with over 100 worked examples: modulation, waveshaping, delay, filters. Good for the mechanism layer. |
| [Pyo docs and examples](http://ajaxsoundstudio.com/pyodoc/), e.g. [complex oscillators](http://ajaxsoundstudio.com/pyodoc/examples/03-generators/01-complex-oscs.html), [FM](http://ajaxsoundstudio.com/pyodoc/examples/03-generators/03-fm-generators.html), [granulation](http://ajaxsoundstudio.com/pyodoc/examples/10-tables/04-granulation.html) | Free | Official, and specific to pyo. Explains objects like `SuperSaw`, `SineLoop` and `Granulator` that your patches already use. |
| [Welsh's Synthesizer Cookbook](https://synthesizer-cookbook.com/) | Paid | Recipes grounded in harmonic analysis for leads, bass, pads, percussion and effects. |

## By patch

**texture/soundscape** (which of these you want depends on the definition question from earlier)
- *If it means an evolving harmonic bed with chaotic modulation* (fits the current `filter`, `fm` and `wash` patches):
  - [Adam Szabo, *How to Emulate the Super Saw*](https://www.adamszabo.com/internet/adam_szabo_how_to_emulate_the_super_saw.pdf) (free BSc thesis on the author's site): a measured analysis of the JP-8000 supersaw, including its non-linear detune curve and mix balance. It maps directly onto `wash.py`'s `detune` and `detune_bal`.
  - [musicdsp.org: Rössler and Lorenz oscillators](https://www.musicdsp.org/en/latest/Synthesis/184-rossler-and-lorenz-oscillators.html) (free): describes how each attractor sounds. Lorenz is unpitched and pink-noise-like; Rössler has spectral peaks over a noisy background. That is directly relevant to `fm.py` and `filter.py`, which use chaotic modulators.
  - [Valhalla DSP blog](https://valhalladsp.com/blog/) and [The Halls of Valhalla (reverb category)](https://valhalladsp.wordpress.com/category/reverb/) (free): a reverb designer writing about diffusion, modulation and metallic colouration. Useful for the wash's reverb and delay stage.
  - Synth Secrets parts 60–62: digital effects and "Creative Synthesis With Delays".
- *If it means an environmental scene*:
  - [Andy Farnell, *Designing Sound*](https://mitpress.mit.edu/9780262014410/designing-sound/) (MIT Press, paid; a [free Pd intro excerpt](https://aspress.co.uk/ds/pdf/pd_intro.pdf) is on the publisher's site). Procedural wind, rain, water and fire. Each practical goes physics → model → implementation, which is the same structure as your drum docs. Farnell's older free tutorials were on obiwannabe.co.uk.
  - [R. Murray Schafer's soundscape model](https://en.wikipedia.org/wiki/Soundscape) (keynote / signal / soundmark, hi-fi vs lo-fi) and [Bernie Krause](https://en.wikipedia.org/wiki/Bernie_Krause) (geophony / biophony / anthrophony). These give the scene's perceptual layers. Wikipedia is fine as a pointer, but cite Schafer's *The Tuning of the World* for the doc itself.

**texture/atmosphere and the texture parent**
- Curtis Roads, *Microsound* ([SOS review](https://www.soundonsound.com/reviews/curtis-roads-microsound); paid book): the standard reference on granular density, grain duration, and the change from rhythmic to pitched to cloud.
- [Barry Truax, Granular Synthesis (SFU)](https://www.sfu.ca/~truax/gran.html) (free, from a pioneer of real-time granular synthesis).

**tonal/drone**
- [Perfect Circuit: Drone Music Explained](https://www.perfectcircuit.com/signal/drone-music-explained) and [Thom Holmes: Electronic Drone Music](https://www.thomholmes.com/post/electronic-drone-music): beating between close tunings, just intonation, and Radigue's work on the ARP 2500. These are secondary sources, lighter on DSP. Pair them with Puckette for the mechanism.

**tonal/bass** (no `AGENTS.md` yet)
- [Devil Fish TB-303 manual, Robin Whittle](https://www.firstpr.com.au/rwi/dfish/Devil-Fish-Manual.pdf) (free, by the designer): real technical detail on the accent sweep, slide, filter envelope decay ranges and overdrive. It's a hardware manual, the same kind of source as your drum doc.
- [Olney, *Computational Thinking through Modular Sound Synthesis*: TB-303 chapter](https://olney.ai/ct-modular-book/tb-303.html) (free).
- For sub and Reese bass, what I found was mostly vendor blogs ([Noise Engineering: Reese](https://noiseengineering.us/blogs/loquelic-literitas-the-blog/quick-patch-how-to-make-a-reese-with-just-about-anything/) is the best of them). They're weaker, so use them only for style variants.

**tonal/pluck**
- Synth Secrets 28–30 (plucked strings, the theoretical guitar patch).
- [Julius O. Smith, Karplus-Strong in *Physical Audio Signal Processing* (CCRMA)](https://ccrma.stanford.edu/~jos/pasp/Karplus_Strong_Algorithm.html) (free, authoritative).
- [Välimäki et al., *Plucked String Models*](http://users.spa.aalto.fi/vpv/publications/cmj98.pdf) (free paper).

**tonal/pad**
- Synth Secrets 46–47 (string machines, PWM and ensemble). This is where the classic pad sound comes from.
- [SOS: Creating & Using Synth Pad Sounds](https://www.soundonsound.com/techniques/creating-using-synth-pad-sounds).
- [Yamaha: Manny's Modulation Manifesto, Synth Pads](https://yamahasynth.com/learn/synth%20-programming/basics-of-fm-synthesis-lesson-4-new/) (written by a synth vendor's sound designer).

**tonal/lead**
- Synth Secrets 24–27 (wind and brass: articulation, vibrato, filter contour, which is the source of most lead design).
- Synth Secrets 51 (articulation) and 18–19 (note priority and triggers, relevant to mono lead behaviour).

**Drums (to extend your existing docs)**
- Synth Secrets 31–39 cover kick, snare, metallic percussion and cymbals in depth. They're worth cross-checking against your current drum docs.

When writing each doc, fetch the specific sources, turn them into principles in the kick-doc format, and add a short "Sources" line at the bottom of the doc.
