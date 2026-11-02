// Capture an rx promo page frame by frame and encode it (video only; rx.py promo adds the audio).
// node render.mjs page.html out.mp4 --duration 22 [--fps 30] [--width 1280] [--height 720] [--query ?lang=fa] [--stills 1.5,9,20 --stills-dir dir]
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
const stills = opt('stills', '');
const query = opt('query', '');

const fonts = path.join(here, '..', 'assets', 'fonts');
const face = (fam, file, w) => `@font-face{font-family:'${fam}';src:url('${pathToFileURL(path.join(fonts, file))}');font-weight:${w};}`;
const fontCss = [face('Inter', 'Inter-Regular.otf', 400), face('Inter', 'Inter-Medium.otf', 500), face('Inter', 'Inter-SemiBold.otf', 600),
  face('Inter', 'Inter-Bold.otf', 700), face('Inter', 'Inter-Bold.otf', 800), face('Inter', 'Inter-Bold.otf', 900),
  face('Vazirmatn', 'Vazirmatn-Regular.ttf', 400), face('Vazirmatn', 'Vazirmatn-Bold.ttf', 700), face('Vazirmatn', 'Vazirmatn-Bold.ttf', 900)].join('\n');

const browser = await chromium.launch({ args: ['--allow-file-access-from-files', '--font-render-hinting=none'] });
const page = await browser.newPage({ viewport: { width: 1920, height: 1080 }, deviceScaleFactor: W / 1920 });
page.on('console', m => { if (m.type() === 'error') console.error('page:', m.text()); });
page.on('pageerror', e => { console.error('page error:', e.message); process.exitCode = 1; });
await page.addInitScript({ path: path.join(here, 'runtime.js') });
await page.addInitScript(css => {
  document.addEventListener('DOMContentLoaded', () => { const s = document.createElement('style'); s.textContent = css; document.head.prepend(s); });
}, fontCss);
await page.goto(pathToFileURL(path.resolve(page_)).href + query);
await page.evaluate(() => window.promoReady);

if (stills) {
  const dir = opt('stills-dir', 'stills');
  fs.mkdirSync(dir, { recursive: true });
  for (const t of stills.split(',').map(Number)) {
    await page.evaluate(t => window.renderFrame(t), t);
    await page.screenshot({ path: path.join(dir, `t${t.toFixed(2).padStart(6, '0')}.png`) });
  }
} else {
  const ff = spawn('ffmpeg', ['-v', 'error', '-y', '-f', 'image2pipe', '-framerate', String(fps), '-i', '-',
    '-c:v', 'libx264', '-preset', 'medium', '-crf', '18', '-pix_fmt', 'yuv420p', '-r', String(fps), out], { stdio: ['pipe', 'inherit', 'inherit'] });
  const n = Math.round(duration * fps);
  for (let k = 0; k < n; k++) {
    await page.evaluate(t => window.renderFrame(t), k / fps);
    const buf = await page.screenshot({ type: 'jpeg', quality: 92 });
    if (!ff.stdin.write(buf)) await new Promise(r => ff.stdin.once('drain', r));
    if (k % (fps * 2) === 0) process.stdout.write(`\rframe ${k}/${n}`);
  }
  ff.stdin.end();
  await new Promise(r => ff.on('close', r));
  process.stdout.write(`\rframes ${n}, ${out}\n`);
}
await browser.close();
