// rx promo runtime: helpers for a motion-graphics page whose every frame is a pure function of time.
// The page defines window.renderFrame(t) (seconds) and may set window.promoAssets = [image urls] to preload.
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
  const P = {
    clamp, ease,
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
