// rx promo runtime: helpers for a motion-graphics page whose every frame is a pure function of time.
// The page defines window.renderFrame(t) (seconds) and must not keep state between frames (no timers, no CSS
// transitions, no requestAnimationFrame while rendering); and may set window.promoAssets = [image urls] to preload.
// render.mjs injects this file before the page's own scripts and waits for window.promoReady.
(() => {
  const clamp = (x, a = 0, b = 1) => Math.min(b, Math.max(a, x));
  const ease = {
    linear: x => x,
    out: x => 1 - Math.pow(1 - x, 3),
    in: x => x * x * x,
    inOut: x => (x < 0.5 ? 4 * x * x * x : 1 - Math.pow(-2 * x + 2, 3) / 2),
    outExpo: x => (x >= 1 ? 1 : 1 - Math.pow(2, -10 * x)),
    inExpo: x => (x <= 0 ? 0 : Math.pow(2, 10 * x - 10)),
    outBack: x => { const c1 = 1.70158, c3 = c1 + 1; return 1 + c3 * Math.pow(x - 1, 3) + c1 * Math.pow(x - 1, 2); },
  };
  // Closed-form damped spring, 0 -> 1, a pure function of time (no simulation, so any frame renders on its own).
  // k = stiffness, d = damping. Underdamped springs overshoot a hair and settle: motion with mass.
  function spring(t, k = 170, d = 26) {
    if (t <= 0) return 0;
    const w0 = Math.sqrt(k), z = d / (2 * w0);
    if (z < 1) {
      const wd = w0 * Math.sqrt(1 - z * z);
      return 1 - Math.exp(-z * w0 * t) * (Math.cos(wd * t) + (z * w0 / wd) * Math.sin(wd * t));
    }
    return 1 - Math.exp(-w0 * t) * (1 + w0 * t);   // critical (and over-damped treated as critical)
  }
  // Seeded noise (mulberry32). The renderer also seeds Math.random per frame, but prefer an explicit rng(seed).
  const rng = seed => () => { seed |= 0; seed = seed + 0x6D2B79F5 | 0;
    let x = Math.imul(seed ^ seed >>> 15, 1 | seed); x = x + Math.imul(x ^ x >>> 7, 61 | x) ^ x;
    return ((x ^ x >>> 14) >>> 0) / 4294967296; };
  const P = {
    clamp, ease, spring, rng,
    // presets [k, d]: snappy for buttons and leading edges, base for cards and camera, heavy for big type and
    // logo lockups (no overshoot), playful for stickers and mascots (visible overshoot)
    springs: { snappy: [400, 34], base: [170, 22], heavy: [120, 24], playful: [200, 12] },
    // spring progress of a move that starts at `start`; preset name or [k, d]
    sp: (t, start, preset = 'base') => { const [k, d] = Array.isArray(preset) ? preset : P.springs[preset]; return spring(t - start, k, d); },
    // a value that changes target several times: keys = [[time, value], ...]. One spring per change, summed, so the
    // motion stays continuous and frame 812 needs no frames before it.
    track(t, keys, preset = 'base') {
      const [k, d] = Array.isArray(preset) ? preset : P.springs[preset];
      let v = keys[0][1];
      for (let i = 1; i < keys.length; i++) v += (keys[i][1] - keys[i - 1][1]) * spring(t - keys[i][0], k, d);
      return v;
    },
    // opacity of text inside a morphing container: in after the morph starts, out before the next one
    swapAlpha: (t, tIn, tOut) => Math.min(clamp((t - tIn - 0.08) / 0.12), clamp((tOut - 0.1 - t) / 0.1)),
    // beat grid (window.BEATS, from promo.json "beats" or synthesized music): time of beat n, of downbeat (bar) n
    beat: n => (window.BEATS && window.BEATS.beats[n] !== undefined) ? window.BEATS.beats[n] : n * 0.5,
    bar: n => (window.BEATS && window.BEATS.downbeats[n] !== undefined) ? window.BEATS.downbeats[n] : n * 2,
    // layout format: 'landscape' | 'vertical' | 'square' (rx.py promo --format); reframe per format, never crop
    format: (new URLSearchParams(location.search).get('format')) || window.promoFormat || 'landscape',
    lerp: (a, b, p) => a + (b - a) * p,
    // eased progress of an animation that starts at `start` and lasts `dur`
    at: (t, start, dur = 0.5, e = ease.out) => e(clamp((t - start) / dur)),
    // 1 inside [a, b), with soft edges of `fade` seconds; for showing a layer during a scene
    live: (t, a, b, fade = 0.15) => clamp(Math.min((t - a) / fade + 1, (b - t) / fade)),
    $: sel => document.querySelector(sel),
    el(tag, cls, parent, html) {
      const e = document.createElement(tag);
      if (cls) e.className = cls;
      if (html !== undefined) e.innerHTML = html;
      (parent || document.getElementById('stage')).appendChild(e);
      return e;
    },
    css(e, s) { Object.assign(e.style, s); return e; },
    // typewriter: shows the first n characters of `text`, n growing at `cps` from `start`
    typed(e, text, t, start, cps = 40, caret = true) {
      const n = Math.max(0, Math.min(text.length, Math.floor((t - start) * cps)));
      const blink = caret && t >= start && (n < text.length || Math.floor(t * 2.2) % 2 === 0);
      e.textContent = text.slice(0, n) + (blink ? '▌' : '');
      return n;
    },
    // decaying shake offset (px) for an impact at `at`
    shake(t, at, amp = 12, dur = 0.4, f = 22) {
      const d = t - at;
      if (d < 0 || d > dur) return 0;
      return amp * Math.exp(-6 * d / dur) * Math.sin(2 * Math.PI * f * d);
    },
    images: {},
    // draw frame k of a preloaded image sequence into a canvas
    seq(canvas, urls, t, start, fps = 30, loop = false) {
      let k = Math.floor((t - start) * fps);
      k = loop ? ((k % urls.length) + urls.length) % urls.length : clamp(k, 0, urls.length - 1);
      const img = P.images[urls[k]];
      const ctx = canvas.getContext('2d');
      if (img) ctx.drawImage(img, 0, 0, canvas.width, canvas.height);
    },
  };
  window.P = P;
  window.promoReady = new Promise(resolve => {
    const go = async () => {
      const urls = window.promoAssets || [];
      await Promise.all(urls.map(u => new Promise(r => {
        const i = new Image();
        i.onload = () => { P.images[u] = i; r(); };
        i.onerror = () => { console.error('missing asset ' + u); r(); };
        i.src = u;
      })));
      await document.fonts.ready;
      if (window.setupPromo) await window.setupPromo();
      resolve(true);
    };
    if (document.readyState === 'complete') go(); else window.addEventListener('load', go);
  });
})();
