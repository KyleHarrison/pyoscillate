3. "Musical timeline" visualization
This is the one I'd consider more important for your project than a conventional synth UI.
Your UI already says:
"The phrase changes every 8 bars."

But there isn't currently a strong visual representation of that.
Imagine:
LEADS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

        phrase 1          phrase 2
    ┌────────────────┐ ┌────────────────┐
    │  ·     ·   ·   │ │ ·   ·     ·    │
    │     ·       ·  │ │    ·     ·     │
    └────────────────┘ └────────────────┘
     1   2   3 ... 8    9  10 ...    16

Or, much more musically:
BAR       1       2       3       4       5       6       7       8
          │       │       │       │       │       │       │       │
FM Wind   ●───●───────●──────●───────●────────●─────●─────────────
FM Swirl      ●────●──────●───────●──────●────────●──────●────────
          └────────────────────────────────────────────────────────┘
                              ↓
                         EVOLVE HERE

This would make your generative structure visible.
That's important because your synth isn't merely:
oscillator → filter → effects

It's more like:
musical intention → evolving behaviours → DSP

That's a much more interesting interface problem.