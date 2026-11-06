import os from 'node:os';
const SKILL = process.env.RX_SKILL || (os.homedir() + '/.claude/skills/research-explainer');
import path from 'node:path'; import { pathToFileURL } from 'node:url';
const { chromium } = await import(pathToFileURL(SKILL + '/promo/node_modules/playwright/index.mjs').href);
const b = await chromium.launch({ args: ['--allow-file-access-from-files'] });
const p = await b.newPage({ viewport: { width: 854, height: 480 } });
p.on('pageerror', e => console.log('PAGEERROR', e.stack || e.message));
p.on('console', m => console.log('console', m.type(), m.text()));
await p.goto(pathToFileURL(path.resolve(process.env.PAGE || 'index.html')).href);
await p.waitForTimeout(800);
const ts = process.argv.slice(2).map(Number);
for (const t of ts) {
  const r = await p.evaluate(t => { try { window.renderFrame(t); return 'ok ' + document.getElementById('stage').innerHTML.length; } catch (e) { return 'ERR ' + e.stack; } }, t);
  console.log(t, r.slice(0, 1500));
}
await b.close();
