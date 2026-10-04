// Drive the Flet web app in headless Chrome over CDP and screenshot it.
// Flet renders to a canvas, so there is no DOM to query: everything is a
// coordinate click. See SKILL.md for the layout cheat sheet.
//
//   PW_DIR=<dir with node_modules/playwright-core> H=<viewport height> \
//   CDP_PORT=9333 node drive.mjs out.png "click 618 40" "wait 3000" ...
//
// Steps: click X Y | key NAME | wait MS | wheel DY | size W H
// H (optional) sets a 1280-wide viewport before any step; it resets to the
// window size on every new connection, so pass it on every call that clicks
// or screenshots below the fold. Resizing closes open popup menus.
import { createRequire } from 'node:module';
import path from 'node:path';

const require = createRequire(path.join(process.env.PW_DIR ?? process.cwd(), 'x.js'));
const { chromium } = require('playwright-core');

const b = await chromium.connectOverCDP(`http://127.0.0.1:${process.env.CDP_PORT ?? 9333}`);
const p = b.contexts()[0].pages()[0];
const [out, ...steps] = process.argv.slice(2);

if (process.env.H) {
  await p.setViewportSize({ width: 1280, height: +process.env.H });
  await p.waitForTimeout(1500);
}
for (const s of steps) {
  const [cmd, ...a] = s.split(' ');
  if (cmd === 'click') {
    await p.mouse.move(+a[0], +a[1]);
    await p.waitForTimeout(150);
    await p.mouse.down();
    await p.waitForTimeout(80);
    await p.mouse.up();
  } else if (cmd === 'key') await p.keyboard.press(a[0]);
  else if (cmd === 'wait') await p.waitForTimeout(+a[0]);
  else if (cmd === 'wheel') {
    await p.mouse.move(640, 450);
    await p.mouse.wheel(0, +a[0]);
  } else if (cmd === 'size') await p.setViewportSize({ width: +a[0], height: +a[1] });
}
await p.screenshot({ path: out });
process.exit(0);
