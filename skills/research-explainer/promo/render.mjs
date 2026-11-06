// Capture an rx promo page frame by frame and encode it (video only; rx.py promo adds the audio).
// node render.mjs page.html out.mp4 --duration 22 [--fps 30] [--width 1280] [--height 720] [--format landscape|vertical|square]
//   [--sub 4] [--beats beats.json] [--query ?lang=fa] [--stills 1.5,9,20 --stills-dir dir]
// --sub N renders N sub-frames per frame and blends them (motion blur on fast moves). --format sets the page size in CSS
// pixels: landscape 1920x1080, vertical 1080x1920, square 1080x1080; --width/--height are the output pixels.
import { chromium } from 'playwright';
import { spawn } from 'node:child_process';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';

const here = path.dirname(fileURLToPath(import.meta.url));
const args = process.argv.slice(2);
const opt = (k, d) => { const i = args.indexOf('--' + k); return i >= 0 ? args[i + 1] : d; };
const [page_, out] = args;
const fps = +opt('fps', 30), W = +opt('width', 1280), H = +opt('height', 720);
const duration = +opt('duration', 20);
const sub = Math.max(1, +opt('sub', 1));
const stills = opt('stills', '');
const query = opt('query', '');
const format = opt('format', 'landscape');
const CSS = { landscape: [1920, 1080], vertical: [1080, 1920], square: [1080, 1080] }[format];
if (!CSS) { console.error(`unknown --format ${format} (landscape, vertical, square)`); process.exit(2); }
const beatsFile = opt('beats', '');
const beats = beatsFile ? JSON.parse(fs.readFileSync(beatsFile, 'utf8')) : null;

const fonts = path.join(here, '..', 'assets', 'fonts');
const face = (fam, file, w) => `@font-face{font-family:'${fam}';src:url('${pathToFileURL(path.join(fonts, file))}');font-weight:${w};}`;
const fontCss = [face('Inter', 'Inter-Regular.otf', 400), face('Inter', 'Inter-Medium.otf', 500), face('Inter', 'Inter-SemiBold.otf', 600),
  face('Inter', 'Inter-Bold.otf', 700), face('Inter', 'Inter-Bold.otf', 800), face('Inter', 'Inter-Bold.otf', 900),
  face('Vazirmatn', 'Vazirmatn-Regular.ttf', 400), face('Vazirmatn', 'Vazirmatn-Bold.ttf', 700), face('Vazirmatn', 'Vazirmatn-Bold.ttf', 900)].join('\n');

const browser = await chromium.launch({ args: ['--allow-file-access-from-files', '--font-render-hinting=none'] });
const page = await browser.newPage({ viewport: { width: CSS[0], height: CSS[1] }, deviceScaleFactor: W / CSS[0] });
page.on('console', m => { if (m.type() === 'error') console.error('page:', m.text()); });
page.on('pageerror', e => { console.error('page error:', e.message); process.exitCode = 1; });
// determinism: Math.random is re-seeded from the frame time before every frame, so a frame looks the same in every
// render and as a still; the page gets its format and beat grid before its own scripts run
await page.addInitScript(({ format, beats }) => {
  window.promoFormat = format;
  if (beats) window.BEATS = beats;
  let s = 1;
  Math.random = () => { s |= 0; s = s + 0x6D2B79F5 | 0; let x = Math.imul(s ^ s >>> 15, 1 | s);
    x = x + Math.imul(x ^ x >>> 7, 61 | x) ^ x; return ((x ^ x >>> 14) >>> 0) / 4294967296; };
  window.__rxFrame = t => { s = Math.round(t * 1e4) + 1; window.renderFrame(t); };
}, { format, beats });
await page.addInitScript({ path: path.join(here, 'runtime.js') });
await page.addInitScript(css => {
  document.addEventListener('DOMContentLoaded', () => { const s = document.createElement('style'); s.textContent = css; document.head.prepend(s); });
}, fontCss);
const q = query + (query.includes('format=') ? '' : (query ? '&' : '?') + 'format=' + format);
await page.goto(pathToFileURL(path.resolve(page_)).href + q);
await page.evaluate(() => window.promoReady);

if (stills) {
  const dir = opt('stills-dir', 'stills');
  fs.mkdirSync(dir, { recursive: true });
  for (const t of stills.split(',').map(Number)) {
    await page.evaluate(t => window.__rxFrame(t), t);
    await page.screenshot({ path: path.join(dir, `t${t.toFixed(2).padStart(6, '0')}.png`) });
  }
} else {
  // with sub-frames: tmix averages each group of `sub` frames, select keeps one per group
  // exact even output size (the scaled screenshot can be a pixel off, and H.264 needs even sides)
  const W2 = W - (W % 2), H2 = H - (H % 2);
  const blur = sub > 1 ? `tmix=frames=${sub},select='eq(mod(n\\,${sub})\\,${sub - 1})',setpts=N/${fps}/TB,` : '';
  const vf = ['-vf', `${blur}scale=${W2}:${H2}:flags=lanczos`];
  const ff = spawn('ffmpeg', ['-v', 'error', '-y', '-f', 'image2pipe', '-framerate', String(fps * sub), '-i', '-', ...vf,
    '-c:v', 'libx264', '-preset', 'medium', '-crf', '18', '-pix_fmt', 'yuv420p', '-r', String(fps), out], { stdio: ['pipe', 'inherit', 'inherit'] });
  let ffDone = false;
  ff.on('exit', code => { ffDone = true; if (code) { console.error(`\nffmpeg stopped (exit ${code}); see the message above`); process.exit(1); } });
  const n = Math.round(duration * fps * sub);
  for (let k = 0; k < n; k++) {
    await page.evaluate(t => window.__rxFrame(t), k / (fps * sub));
    const buf = await page.screenshot({ type: 'jpeg', quality: 92 });
    if (ffDone) break;
    if (!ff.stdin.write(buf)) await new Promise(r => { ff.stdin.once('drain', r); ff.once('exit', r); });
    if (k % (fps * sub * 2) === 0) process.stdout.write(`\rframe ${Math.floor(k / sub)}/${n / sub}`);
  }
  ff.stdin.end();
  await new Promise(r => ff.on('close', r));
  process.stdout.write(`\rframes ${n / sub}${sub > 1 ? ` (x${sub} sub-frames)` : ''}, ${out}\n`);
}
await browser.close();
