---
name: run-master-rack
description: Use to launch a Pyoscillate Flet rack (master rack or any project rack) in a browser, drive it (start the engine, add and enable patches, expand patches, Evolve patterns/progressions) and take a screenshot, including a full-page one. Use for README screenshots or to confirm a GUI change works in the real app.
---

# Run and screenshot a rack

Verified on macOS with the master rack (`src/flet/master_rack/app.py`). Any rack works the same: swap the app path.

## 1. Launch the app (web mode)

```bash
lsof -iTCP:8561 -sTCP:LISTEN          # pick a free port first; never kill a process you did not start
nohup uv run flet run --web --port 8561 src/flet/master_rack/app.py > "$SCRATCH/flet.log" 2>&1 &
sleep 10; curl -s -m 5 -o /dev/null -w "%{http_code}\n" http://127.0.0.1:8561   # expect 200
```

- The README's `8551` is often already held by a stale `deep_house` app. Flet then crashes with `address already in use` and `curl` to that port still answers from the old app, so use a different port.
- The audio engine runs server-side in Python (pyo), so it works with a headless browser.
- Each page load is a new session and starts with the engine stopped and no patches added.

## 2. Headless Chrome with a CDP port, and the driver

```bash
npm i --prefix "$SCRATCH" playwright-core        # once; not a repo dependency
nohup "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" --headless=new \
  --remote-debugging-port=9333 --user-data-dir="$SCRATCH/chrome-profile" \
  --window-size=1280,1000 http://127.0.0.1:8561 > "$SCRATCH/chrome.log" 2>&1 &
sleep 7
PW_DIR="$SCRATCH" H=1700 node .claude/skills/run-master-rack/drive.mjs out.png "click 618 40" "wait 3500"
```

Chrome stays open between driver calls, so page state (the Flet session) persists across calls. `drive.mjs` documents its steps (`click X Y`, `key Escape`, `wait MS`, `wheel DY`, `size W H`). Look at each screenshot after every action; a blank frame means launch failed.

## 3. Flet gotchas

- The UI is a canvas: no selectors. Click by pixel and verify with a screenshot.
- The viewport resets to the window height on every new connection. Pass `H=<height>` on every call that clicks or captures below the fold, or the click lands off-screen and does nothing.
- **Full-page screenshot:** the app scrolls internally, so a normal screenshot is only a section. Set `H` to the content height (about 1700 for a few patches, 2700 with Evolve sections open), check the capture has no large blank band at the bottom, then re-capture with `H` trimmed to the content.
- Resizing closes open popup menus. Open a menu and act on it within the same call, after `H` has applied.
- Menus (add-patches, pattern, progression) are checkbox lists that stay open while you tick items. Close them with `key Escape`. Clicking elsewhere to dismiss can hit a slider (it moved Master to 0.23 once) or a group toggle.
- Menu positions shift with viewport height, so open the menu, screenshot, then click the items.

## 4. Layout cheat sheet (1280 px wide, master rack)

- Header: Start engine `(618, 40)`; Pause `(750, 40)`; Master slider thumb at 0.80 is `(778, 144)`.
- Group cards start at y=180, about 100 px apart when collapsed. Chevron at `x=1203`; the group switch at `x=87` switches the whole group.
- Expanded group: "Add patches" button at `(90, group_y + 60)`. Menu items are 40 px apart. A newly added patch row appears about 70 px below the button, with its enable switch at `x=1197` and its expand chevron at `x=61`.
- Expanded patch: waveform and spectrum graphs, then a Pattern row (dropdown, plus a Hold/Evolve segment with Evolve at `x≈1195`). In Evolve, the dropdown ticks which patterns cycle ("2 of 4"), and a timeline and a "Changes every N bars" slider appear. Chord-following patches (Musical, for example "Chord Stab - Velvet") also get a Progression row with its own Hold/Evolve and tick list.
- Header Key/Progression dropdowns are single-select and only enabled when a chord-following patch exists. Evolving several progressions is done per patch, not in the header.
- Waveform/spectrum graphs of one-shot drums are flat between hits. For a README shot, expand a sustained patch (for example "Noise - Air") or capture several frames and keep one where the kick is firing.

## 5. Clean up

```bash
pkill -f "remote-debugging-port=9333"; pkill -f "flet run --web --port 8561"
```

Work in the session scratchpad; only commit the final image (README screenshot lives in `docs/images/master-rack.png`).
