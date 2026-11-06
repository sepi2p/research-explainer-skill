// probe_motion.mjs [JOBS]: step through the whole video (15 samples a second) without drawing and write
// work/audio/motion_events.json, which work/audio.py turns into quiet sound effects where no hand-placed cue covers them:
//   appear  a paper component starts to show (the list is in work/probe_hooks.js), with its scene
//   pins    year-ribbon pins landing (E.PINS t0)
//   moves   camera moves, from the cam each scene returns: start, duration, peak speed (screen px per second)
//   shots   the rung climb into each new scene (the old shot slides down, the new one arrives)
// Anything already on screen when a scene's shot arrives belongs to that shot and gets no event of its own.
// Run after work/timeline.py, and again after every change of timing or scenes:  node work/probe_motion.mjs [4]
// JOBS browser pages share the video (default 4). Playwright comes from the skill (RX_SKILL, as in video/render_seg.mjs).
import os from 'node:os';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';
const SKILL = process.env.RX_SKILL || (os.homedir() + '/.claude/skills/research-explainer');
const { chromium } = await import(pathToFileURL(SKILL + '/promo/node_modules/playwright/index.mjs').href);
const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const V = path.join(ROOT, 'video');
let html = fs.readFileSync(path.join(V, 'index.html'), 'utf8');
const at = html.search(/<script src="scenes\//);
if (at < 0) throw new Error('video/index.html has no <script src="scenes/...">: the probe hooks go right before the first scene');
html = html.slice(0, at) + '<script src="../work/probe_hooks.js"></script>\n' + html.slice(at);
const PAGE = path.join(V, '.probe.html');
const TL = JSON.parse(fs.readFileSync(path.join(ROOT, 'timeline.json'), 'utf8'));
const JOBS = Math.max(1, +(process.argv[2] || 4)), FPS = 15, T = TL.total, PRE = 1.0;

const job = async (b, j) => {
  const a = T * j / JOBS, z = T * (j + 1) / JOBS;
  const p = await b.newPage({ viewport: { width: 854, height: 480 } });
  p.on('pageerror', e => console.log('page error:', e.message));
  await p.goto(pathToFileURL(PAGE).href);
  await p.waitForFunction(() => window.renderFrame && window.E && E.scenes && window.__probe);
  return p.evaluate(({ a, z, T, FPS, PRE }) => {
    const st = document.getElementById('stage');   // no drawing: the frame string is built and thrown away
    Object.defineProperty(st, 'innerHTML', { set() { }, get() { return ''; } });
    const P = window.__probe, cams = {};
    for (const id of Object.keys(E.scenes)) {
      const f = E.scenes[id];
      E.scenes[id] = t => { P.cur = id; P.rendered.add(id); const r = f(t); if (r && r.cam) cams[id] = r.cam; return r; };
    }
    const appear = [], moves = [], shots = [], last = new Map(), seen = new Set(), prev = {}, mv = {};
    const close = id => { const m = mv[id]; delete mv[id]; if (m.t >= a && m.t < z) moves.push({ t: +m.t.toFixed(3), dur: +(m.end - m.t).toFixed(2), peak: Math.round(m.peak), scene: id }); };
    const i0 = Math.max(0, Math.floor((a - PRE) * FPS)), i1 = Math.ceil(z * FPS), iMax = Math.min(Math.ceil(T * FPS), i1 + 8 * FPS);
    for (let i = i0; i < iMax; i++) {
      const inside = i < i1;                        // past z: only finish the camera moves that began before z
      if (!inside && !Object.keys(mv).length) break;
      const t = i / FPS; P.frame = new Map(); P.rendered = new Set();
      for (const k in cams) delete cams[k];
      try { window.renderFrame(t); } catch (e) { throw new Error(`renderFrame(${t.toFixed(3)}): ${e.message}`); }
      const emit = inside && t >= a;
      const arrived = new Set([...P.rendered].filter(id => !seen.has(id)));
      for (const id of arrived) { seen.add(id); if (emit && t > 0) shots.push({ t: +t.toFixed(3), scene: id }); }
      if (inside) for (const [k, t0] of P.frame) {
        const l = last.get(k);
        if ((l === undefined || t - l > 0.35) && emit && !arrived.has(k.split('|')[1])) {
          const te = t0 !== null && t0 <= t && t0 > t - 1.5 / FPS ? t0 : t;   // exact start when the component has one
          appear.push({ t: +te.toFixed(3), key: k });
        }
        last.set(k, t);
      }
      for (const id in mv) if (!cams[id]) close(id);   // the scene left the screen mid-move
      for (const id in cams) {
        const c = cams[id], q = prev[id];
        if (q && q.i === i - 1) {
          const sp = (Math.abs(c.x - q.c.x) + Math.abs(c.y - q.c.y)) * FPS * c.z + Math.abs(Math.log(c.z / q.c.z)) * FPS * 600;
          const m = mv[id];
          if (!m) { if (sp > 60 && inside) mv[id] = { t: (i - 1) / FPS, peak: sp, end: t }; }
          else { m.peak = Math.max(m.peak, sp); m.end = t; if (sp < 20) close(id); }
        }
        prev[id] = { c: { ...c }, i };
      }
    }
    for (const id in mv) close(id);
    const pins = (E.PINS || []).filter(q => q.t0 !== undefined && q.t0 >= a && q.t0 < z).map(q => ({ t: +(+q.t0).toFixed(3), label: q.label || String(q.year) }));
    return { appear, moves, pins, shots };
  }, { a, z, T, FPS, PRE });
};

const t0 = Date.now();
fs.writeFileSync(PAGE, html);
const b = await chromium.launch({ args: ['--allow-file-access-from-files'] });
let parts;
try { parts = await Promise.all([...Array(JOBS).keys()].map(j => job(b, j))); }
finally { await b.close(); fs.rmSync(PAGE, { force: true }); }
const by = k => (x, y) => x[k] - y[k];
const out = {
  fps: FPS, total: T,
  appear: parts.flatMap(r => r.appear).sort(by('t')), moves: parts.flatMap(r => r.moves).sort(by('t')),
  pins: parts.flatMap(r => r.pins).sort(by('t')), shots: parts.flatMap(r => r.shots).sort(by('t')),
};
fs.mkdirSync(path.join(ROOT, 'work/audio'), { recursive: true });
fs.writeFileSync(path.join(ROOT, 'work/audio/motion_events.json'), JSON.stringify(out, null, 0));
const kinds = {};
for (const e of out.appear) { const k = e.key.split('|')[0]; kinds[k] = (kinds[k] || 0) + 1; }
console.log(`work/audio/motion_events.json: ${out.appear.length} appearances (${Object.entries(kinds).map(([k, n]) => k + ' ' + n).join(', ') || 'none'}), ` +
  `${out.moves.length} camera moves, ${out.pins.length} pins, ${out.shots.length} shots in ${((Date.now() - t0) / 1000).toFixed(1)} s`);
