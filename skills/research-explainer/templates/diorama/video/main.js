// Frame composer. Each scene module registers E.scenes[id] = t => ({cam, world, screen, frame, hud}).
//   cam   {x, y, z}: world point at the screen centre and zoom (world units are logical px at z = 1)
//   world SVG in world coordinates (under the camera); screen: SVG in screen coordinates (over the camera)
//   frame {k, chip, label}: the saffron frame border (frame shots only)
//   hud   {ladder: 0..1, ribbon: 0..1, caption: 0..1}: HUD visibility for this moment (defaults: ladder 1, ribbon auto,
//         caption 1)
(() => {
  const { C } = E;
  // ---------------- the video's configuration (edit this block for your own video) ----------------
  // scene order: one file per scene in scenes/, registered in index.html too
  const ORDER = ['s1_reading', 's2_average', 's3_shared', 's4_takeaway'];
  // chapter label shown for ~2.2 s when a scene starts: [number, label, small second label (optional)]
  const CHAPTER = {
    s1_reading: ['1', 'One reading', ''], s2_average: ['2', 'Average', ''], s3_shared: ['3', 'Shared wobble', ''],
    s4_takeaway: ['', 'Takeaway', ''],
  };
  // ladder rungs, bottom to top (screen right). locked: grey with a padlock (pulses at the end); hiddenUntil: '?' before
  E.RUNGS = [{ label: 'One reading' }, { label: 'Average' }, { label: 'Shared' }, { label: 'Next', locked: true }];
  const RUNG_OF = { s1_reading: 0, s2_average: 1, s3_shared: 2, s4_takeaway: 2 };
  // a rung cracks when the next question breaks it: {rung index: () => time}
  const CRACKS = { 1: () => E.cue('C2', 'stalls') };
  const PULSE_TOP = () => E.B('E1').start + 1.0;   // the locked top rung starts to pulse here
  // captions: drawn when the timeline says so (text-only renders: work/timeline.py writes captions: true)
  const CAPTIONS = !!(E.TL && E.TL.captions);
  // -----------------------------------------------------------------------------------------------

  const GAP = 1.0;   // seconds between the last word of one scene and the first of the next (the rung climb)
  const bound = i => i === 0 ? 0 : E.TL.scenes[ORDER[i]].start - GAP;    // scene i becomes active here
  E.ORDER = ORDER;
  E.sceneStart = id => bound(ORDER.indexOf(id));
  E.sceneEnd = id => { const i = ORDER.indexOf(id); return i + 1 < ORDER.length ? bound(i + 1) : E.TL.total; };

  // HUD state that depends on the whole video's progress
  E.hudState = t => {
    let cur = 0;
    for (const id of ORDER) if (t >= E.sceneStart(id) + 0.4) cur = RUNG_OF[id] ?? cur;
    const cracked = [];
    for (const k in CRACKS) { try { if (t >= CRACKS[k]()) cracked.push(+k); } catch (e) { } }
    let pulseTop = 0; try { const a = PULSE_TOP(); if (t > a) pulseTop = 0.5 + 0.5 * Math.sin((t - a) * 6); } catch (e) { }
    return { current: cur, cracked, pulseTop };
  };

  const ribbonK = t => {          // the ribbon slides up for ~3 s after each pin lands
    let k = 0;
    for (const p of E.PINS) if (p.t0 !== undefined) k = Math.max(k, E.win(t, p.t0 - 0.35, p.t0 + 2.8, 0.35));
    return k;
  };

  const defs = () => `<defs>
    <pattern id="gridp" width="10" height="10" patternUnits="userSpaceOnUse"><path d="M10,0 L0,0 0,10" fill="none" stroke="${C.grid}" stroke-width="0.7"/></pattern>
    <linearGradient id="shaftg" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#FFF8E6" stop-opacity="0.9"/><stop offset="1" stop-color="#FFF8E6" stop-opacity="0"/></linearGradient>
    <radialGradient id="lampg"><stop offset="0" stop-color="#FFE3A8" stop-opacity="0.95"/><stop offset="1" stop-color="#FFE3A8" stop-opacity="0"/></radialGradient>
    <radialGradient id="vign" cx="0.5" cy="0.5" r="0.75"><stop offset="0.6" stop-color="#000" stop-opacity="0"/><stop offset="1" stop-color="#2A1A0A" stop-opacity="0.28"/></radialGradient>
    <filter id="flat"><feOffset dx="0" dy="0"/></filter>
    <clipPath id="vp"><rect x="0" y="0" width="854" height="480"/></clipPath>
    ${E.GRAIN ? `<pattern id="grain" width="256" height="256" patternUnits="userSpaceOnUse"><image href="${E.GRAIN}" width="256" height="256"/></pattern>` : ''}
  </defs>`;

  const camTf = cam => `translate(${(E.W / 2).toFixed(2)},${(E.H / 2).toFixed(2)}) scale(${cam.z.toFixed(4)}) translate(${(-cam.x).toFixed(2)},${(-cam.y).toFixed(2)})`;
  // camera micro-drift (always alive)
  const drift = (t, cam) => ({ x: cam.x + E.noise1(t * 0.05, 'cx') * 4 / cam.z, y: cam.y + E.noise1(t * 0.05, 'cy') * 3 / cam.z, z: cam.z });

  const renderScene = (id, t) => {
    const f = E.scenes[id];
    if (!f) return { svg: E.rect(0, 0, E.W, E.H, { fill: '#333' }) + E.text(E.W / 2, E.H / 2, 'missing scene ' + id, { dir: 'ltr', fill: '#fff' }), hud: {} };
    const r = f(t);
    const cam = drift(t, r.cam || { x: 900, y: 240, z: 1 });
    let s = '';
    if (r.bg) s += r.bg;
    if (r.world) s += `<g transform="${camTf(cam)}">${r.world}</g>`;
    if (r.screen) s += r.screen;
    if (r.frame) s += E.comp.FrameBorder(t, r.frame);
    return { svg: `<g clip-path="url(#vp)">${s}</g>`, hud: r.hud || {}, fk: r.frame ? (r.frame.k || 0) : 0 };
  };

  const chapterLabel = (t, id) => {
    const c = CHAPTER[id]; if (!c) return '';
    const t0 = E.sceneStart(id) + 0.45, k = E.win(t, t0, t0 + 2.2, 0.35);
    if (k <= 0) return '';
    const main = (c[0] ? E.num(c[0]) + ' · ' : '') + c[1], sub = c[2] || '';
    const rtl = /[؀-ۿ]/.test(main);
    const w1 = main.length * (rtl ? 10.5 : 10.8), w2 = sub ? 22 + sub.length * 8.2 : 0, bw = 34 + w1 + w2;
    const x = E.W - 20 + (1 - E.ease.out(k)) * 260;
    let s = E.rect(-bw, -22, bw, 44, { fill: C.ink, r: 8, opacity: 0.92 });
    if (rtl) {
      s += E.text(-14, 0, main, { size: 20, weight: 700, fill: C.paper, anchor: 'start', dir: 'rtl' });
      if (sub) s += E.text(-bw + 14, 1, sub, { size: 14, weight: 600, dir: 'ltr', font: E.FONT.en, anchor: 'start', fill: C.saffron });
    } else {
      s += E.text(-bw + 16, 0, main, { size: 20, weight: 700, fill: C.paper, anchor: 'start', dir: 'ltr' });
      if (sub) s += E.text(-14, 1, sub, { size: 14, weight: 600, dir: 'ltr', font: E.FONT.en, anchor: 'end', fill: C.saffron });
    }
    return E.g(E.tf(x - 30, 42), s);
  };

  // the narration on screen: the beat being spoken (fades between beats; hidden in pauses longer than 0.6 s)
  const caption = t => {
    if (!CAPTIONS) return '';
    for (const b of E.TL.beats) {
      if (t >= b.start - 0.15 && t <= b.end + 0.35) return E.comp.Caption(t, { text: (b.text ?? '').replace(/⏸/g, ' ').replace(/\s+/g, ' ').trim(), k: E.win(t, b.start - 0.1, b.end + 0.3, 0.18) });
    }
    return '';
  };

  window.renderFrame = t => {
    let i = 0;
    for (let k = 0; k < ORDER.length; k++) if (t >= bound(k)) i = k;
    const id = ORDER[i];
    let body;
    // rung climb: around each boundary the old shot slides down while the new one arrives from above
    const tb = bound(i), tn = i + 1 < ORDER.length ? bound(i + 1) : Infinity, TR = 0.45;
    let hud;
    if (i > 0 && t < tb + TR) {
      const p = E.ease.inOut(E.clamp((t - (tb - TR)) / (2 * TR)));
      const old = renderScene(ORDER[i - 1], t), nw = renderScene(id, t);
      body = E.g(`translate(0,${(p * E.H).toFixed(2)})`, old.svg) + E.g(`translate(0,${((p - 1) * E.H).toFixed(2)})`, nw.svg);
      hud = { ...nw.hud, fk: nw.fk };
    } else if (t > tn - TR) {
      const p = E.ease.inOut(E.clamp((t - (tn - TR)) / (2 * TR)));
      const cur = renderScene(id, t), nx = renderScene(ORDER[i + 1], t);
      body = E.g(`translate(0,${(p * E.H).toFixed(2)})`, cur.svg) + E.g(`translate(0,${((p - 1) * E.H).toFixed(2)})`, nx.svg);
      hud = { ...cur.hud, fk: cur.fk };
    } else {
      const r = renderScene(id, t); body = r.svg; hud = { ...r.hud, fk: r.fk };
    }
    const hs = E.hudState(t);
    let over = '';
    const inFrame = E.clamp((hud.fk - 0.3) / 0.3);       // inside a frame shot there is only what the frame holds: no HUD
    const lk = (hud.ladder ?? 1) * (1 - inFrame);
    over += E.comp.Ladder(t, { ...hs, k: lk });
    if (hud.ribbon !== 0 && inFrame < 1 && E.PINS.length) over += E.g('', E.comp.Ribbon(t, { k: hud.ribbon ?? ribbonK(t), pins: E.PINS }), { opacity: 1 - inFrame });
    over += chapterLabel(t, id);
    if (E.overlay) over += E.overlay(t);
    if (hud.caption !== 0) over += caption(t);
    const grain = E.GRAIN ? `<rect width="${E.W}" height="${E.H}" fill="url(#grain)" opacity="0.07" style="mix-blend-mode:multiply"/>` : '';
    document.getElementById('stage').innerHTML = defs() + `<rect width="${E.W}" height="${E.H}" fill="${C.paper}"/>` + body +
      `<rect width="${E.W}" height="${E.H}" fill="url(#vign)"/>` + over + grain;
  };

  // paper grain: one static noise tile, made once; fonts loaded before the first frame
  window.setupPromo = async () => {
    const c = document.createElement('canvas'); c.width = c.height = 256;
    const x = c.getContext('2d'), im = x.createImageData(256, 256), r = E.rng(1234);
    for (let i = 0; i < im.data.length; i += 4) { const v = 150 + r() * 105; im.data[i] = v; im.data[i + 1] = v * 0.97; im.data[i + 2] = v * 0.9; im.data[i + 3] = 255; }
    x.putImageData(im, 0, 0); E.GRAIN = c.toDataURL('image/png');
    await document.fonts.load('700 20px Vazirmatn'); await document.fonts.load('400 20px Vazirmatn');
    await document.fonts.load('400 16px Inter'); await document.fonts.load('500 16px Inter'); await document.fonts.load('600 16px Inter'); await document.fonts.load('700 16px Inter');
    await document.fonts.load('400 14px "JetBrains Mono"');
  };
})();
