// Core of the paper-diorama page. Every frame is a pure function of time: renderFrame(t) builds one SVG string.
// Logical canvas: 854 x 480 (viewBox). Components return SVG strings. Nothing keeps state between frames except
// pure memo caches (same input -> same output), so any frame renders on its own and in any process.
(() => {
  const E = window.E = {};
  E.W = 854; E.H = 480;
  E.C = {
    paper: '#F3E9D2', paperShade: '#E6D7B8', ink: '#1F2A44', brick: '#B5533C', saffron: '#E9A23B', teal: '#2A9D8F',
    steel: '#4F6FA8', pistachio: '#7FA650', pomegranate: '#C8372D', night: '#16213A', graph: '#FBFAF6', grid: '#C9D6E3',
    sticky: '#F6D365', schematic: '#8A8F98', wood: '#A87C52', woodDark: '#7A5434', cream: '#FBF3E2', white: '#FFFFFF',
    sky: '#D7E8E6', skin: '#EFC3A0',
  };
  E.FONT = { fa: "Vazirmatn, sans-serif", en: "Inter, sans-serif", mono: "'JetBrains Mono', monospace", hand: "Caveat, Vazirmatn, sans-serif" };
  // narration language of this render (from the timeline: work/timeline.py --lang). 'fa' turns on right-to-left text,
  // Vazirmatn and Persian digits as the defaults; 'en' (or any left-to-right language) uses Inter and Latin digits.
  E.LANG = (window.TL && window.TL.lang) || 'en';
  E.RTL = ['fa', 'ar', 'ur', 'he'].includes(E.LANG);
  E.DIR = E.RTL ? 'rtl' : 'ltr';
  // fixed labels the shared components draw, per language (add a language here)
  E.LABELS = {
    en: { real: 'measured', named: 'NAMED', common: 'COMMON NAME', made: 'made-up world · real numbers', graph: 'graph paper = measured data', torn: 'torn paper = illustration' },
    fa: { real: 'اجرای واقعی', named: 'نام‌گذاری شد', common: 'نام رایج', made: 'دنیای ساختگی · عددهای واقعی', graph: 'کاغذ شطرنجی = داده‌ی واقعی', torn: 'کاغذ پاره = تصویر توضیحی' },
  };
  E.L = E.LABELS[E.LANG] || E.LABELS.en;

  // ---------- maths ----------
  const clamp = E.clamp = (x, a = 0, b = 1) => Math.min(b, Math.max(a, x));
  E.lerp = (a, b, p) => a + (b - a) * p;
  E.ease = {
    lin: x => x, out: x => 1 - Math.pow(1 - x, 3), in: x => x * x * x,
    inOut: x => (x < 0.5 ? 4 * x * x * x : 1 - Math.pow(-2 * x + 2, 3) / 2),
    outBack: x => { const c1 = 1.70158, c3 = c1 + 1; return 1 + c3 * Math.pow(x - 1, 3) + c1 * Math.pow(x - 1, 2); },
  };
  // eased progress 0..1 of an animation from `start` lasting `dur`
  E.at = (t, start, dur = 0.5, e = E.ease.out) => e(clamp((t - start) / dur));
  // window: 1 inside [a,b] with soft edges
  E.win = (t, a, b, f = 0.25) => clamp(Math.min((t - a) / f + 1, (b - t) / f + 1));
  E.fadeIn = (t, a, f = 0.3) => clamp((t - a) / f);
  E.fadeOut = (t, b, f = 0.3) => clamp((b - t) / f);
  // closed-form damped spring 0 -> 1 (k stiffness, d damping)
  E.spring = (t, k = 170, d = 18) => {
    if (t <= 0) return 0;
    const w0 = Math.sqrt(k), z = d / (2 * w0);
    if (z < 1) { const wd = w0 * Math.sqrt(1 - z * z); return 1 - Math.exp(-z * w0 * t) * (Math.cos(wd * t) + (z * w0 / wd) * Math.sin(wd * t)); }
    return 1 - Math.exp(-w0 * t) * (1 + w0 * t);
  };
  E.SPR = { obj: [170, 18], snap: [400, 34], heavy: [120, 24], play: [200, 12], cam: [60, 15.5] };
  E.sp = (t, start, p = 'obj') => { const [k, d] = Array.isArray(p) ? p : E.SPR[p]; return E.spring(t - start, k, d); };
  // value with several targets: keys [[time, value], ...]
  E.track = (t, keys, p = 'obj') => { let v = keys[0][1]; for (let i = 1; i < keys.length; i++) v += (keys[i][1] - keys[i - 1][1]) * E.sp(t, keys[i][0], p); return v; };
  // eased (non-spring) track, good for the camera: keys [[time, value, dur?]]
  E.etrack = (t, keys, dur = 1.0, e = E.ease.inOut) => { let v = keys[0][1]; for (let i = 1; i < keys.length; i++) v += (keys[i][1] - keys[i - 1][1]) * E.at(t, keys[i][0], keys[i][2] || dur, e); return v; };
  E.hash = s => { let h = 2166136261 >>> 0; s = String(s); for (let i = 0; i < s.length; i++) { h ^= s.charCodeAt(i); h = Math.imul(h, 16777619) >>> 0; } return h >>> 0; };
  E.rng = seed => () => { seed |= 0; seed = seed + 0x6D2B79F5 | 0; let x = Math.imul(seed ^ seed >>> 15, 1 | seed); x = x + Math.imul(x ^ x >>> 7, 61 | x) ^ x; return ((x ^ x >>> 14) >>> 0) / 4294967296; };
  E.noise1 = (x, seed = 0) => { // smooth 1D value noise in [-1,1]
    const i = Math.floor(x), f = x - i, a = E.rng(E.hash(seed + ':' + i))() * 2 - 1, b = E.rng(E.hash(seed + ':' + (i + 1)))() * 2 - 1;
    const u = f * f * (3 - 2 * f); return a + (b - a) * u;
  };
  // characters animate on twos (12 fps) like stop motion; data and camera at full frame rate
  E.twos = t => Math.floor(t * 12) / 12;
  E.boilFrame = t => Math.floor(t * 8);

  // ---------- text ----------
  const FA_DIG = '۰۱۲۳۴۵۶۷۸۹';
  E.fa = v => String(v).replace(/[0-9]/g, d => FA_DIG[+d]).replace(/\./g, '٫').replace(/,/g, '٬');
  E.faNum = (v, dec = 0) => E.fa(Number(v).toLocaleString('en-US', { minimumFractionDigits: dec, maximumFractionDigits: dec }));
  // a number in the render's language: Persian digits for 'fa', Latin otherwise (E.num(0.0625, 3) -> '0.063' / '۰٫۰۶۳')
  E.num = (v, dec = 0) => { const s = Number(v).toLocaleString('en-US', { minimumFractionDigits: dec, maximumFractionDigits: dec }); return E.RTL ? E.fa(s) : s; };
  E.esc = s => String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
  E.ltr = s => '⁦' + s + '⁩';   // isolate a Latin run inside Persian text
  // single-line SVG text. dir defaults to the language's ('rtl' for Persian). anchor: 'start' | 'middle' | 'end'
  // (for rtl, start = right edge). font defaults to Inter for ltr, Vazirmatn for rtl.
  E.text = (x, y, s, o = {}) => {
    const dir = o.dir || E.DIR;
    const size = o.size || 20, fam = o.font || (dir === 'ltr' ? E.FONT.en : E.FONT.fa);
    const extra = (o.opacity !== undefined ? ` opacity="${o.opacity.toFixed(3)}"` : '') + (o.stroke ? ` stroke="${o.stroke}" stroke-width="${o.sw || 3}" paint-order="stroke" stroke-linejoin="round"` : '');
    return `<text x="${x.toFixed(2)}" y="${y.toFixed(2)}" font-family="${fam}" font-size="${size}" font-weight="${o.weight || 400}" fill="${o.fill || E.C.ink}" direction="${dir}" text-anchor="${o.anchor || 'middle'}" dominant-baseline="${o.baseline || 'middle'}"${o.ls ? ` letter-spacing="${o.ls}"` : ''}${extra}>${E.esc(s)}</text>`;
  };
  // wrapped HTML text in a box (best bidi + line breaking). align: 'right' | 'center' | 'left'
  E.html = (x, y, w, h, inner, o = {}) => {
    const dir = o.dir || E.DIR;
    const st = `width:${w}px;height:${h}px;display:flex;flex-direction:column;justify-content:${o.valign || 'center'};` +
      `direction:${dir};text-align:${o.align || (dir === 'rtl' ? 'right' : 'left')};font-family:${o.font || (dir === 'rtl' ? E.FONT.fa : E.FONT.en)};` +
      `font-size:${o.size || 18}px;line-height:${o.lh || 1.45};font-weight:${o.weight || 400};color:${o.color || E.C.ink};` +
      `overflow:hidden;${o.style || ''}`;
    return `<foreignObject x="${x.toFixed(2)}" y="${y.toFixed(2)}" width="${w}" height="${h}"${o.opacity !== undefined ? ` opacity="${o.opacity.toFixed(3)}"` : ''}><div xmlns="http://www.w3.org/1999/xhtml" style="${st}"><div>${inner}</div></div></foreignObject>`;
  };
  E.span = (s, st = '') => `<span style="${st}">${E.esc(s)}</span>`;
  E.lat = (s, st = '') => `<bdi dir="ltr" style="font-family:${E.FONT.en};${st}">${E.esc(s)}</bdi>`;   // Latin term inside Persian HTML
  E.rtlSpan = (s, st = '') => `<bdi dir="rtl" style="font-family:${E.FONT.fa};${st}">${E.esc(s)}</bdi>`;  // Persian inside English HTML
  E.mono = (s, st = '') => `<bdi dir="ltr" style="font-family:${E.FONT.mono};font-variant-ligatures:none;${st}">${E.esc(s)}</bdi>`;

  // ---------- svg helpers ----------
  E.g = (tf, inner, o = {}) => `<g${tf ? ` transform="${tf}"` : ''}${o.opacity !== undefined ? ` opacity="${clamp(o.opacity).toFixed(3)}"` : ''}${o.clip ? ` clip-path="url(#${o.clip})"` : ''}${o.filter ? ` filter="url(#${o.filter})"` : ''}>${inner}</g>`;
  E.tf = (x = 0, y = 0, s = 1, r = 0, sx, sy) => {
    let out = `translate(${x.toFixed(2)},${y.toFixed(2)})`;
    if (r) out += ` rotate(${r.toFixed(2)})`;
    if (sx !== undefined || sy !== undefined) out += ` scale(${(sx ?? s).toFixed(4)},${(sy ?? s).toFixed(4)})`;
    else if (s !== 1) out += ` scale(${s.toFixed(4)})`;
    return out;
  };
  E.rect = (x, y, w, h, o = {}) => `<rect x="${x.toFixed(2)}" y="${y.toFixed(2)}" width="${Math.max(0, w).toFixed(2)}" height="${Math.max(0, h).toFixed(2)}"${o.r ? ` rx="${o.r}"` : ''} fill="${o.fill || 'none'}"${o.stroke ? ` stroke="${o.stroke}" stroke-width="${o.sw || 1.5}"` : ''}${o.opacity !== undefined ? ` opacity="${o.opacity.toFixed(3)}"` : ''}${o.dash ? ` stroke-dasharray="${o.dash}"` : ''}/>`;
  E.circle = (x, y, r, o = {}) => `<circle cx="${x.toFixed(2)}" cy="${y.toFixed(2)}" r="${Math.max(0, r).toFixed(2)}" fill="${o.fill || 'none'}"${o.stroke ? ` stroke="${o.stroke}" stroke-width="${o.sw || 1.5}"` : ''}${o.opacity !== undefined ? ` opacity="${o.opacity.toFixed(3)}"` : ''}/>`;
  E.path = (d, o = {}) => `<path d="${d}" fill="${o.fill || 'none'}"${o.stroke ? ` stroke="${o.stroke}" stroke-width="${o.sw || 1.5}" stroke-linecap="round" stroke-linejoin="round"` : ''}${o.opacity !== undefined ? ` opacity="${o.opacity.toFixed(3)}"` : ''}${o.dash ? ` stroke-dasharray="${o.dash}"` : ''}/>`;
  E.line = (x1, y1, x2, y2, o = {}) => E.path(`M${x1.toFixed(2)},${y1.toFixed(2)} L${x2.toFixed(2)},${y2.toFixed(2)}`, { stroke: o.stroke || E.C.ink, sw: o.sw || 1.5, ...o });

  // ---------- rough (hand-drawn) shapes, memoized ----------
  const gen = rough.generator();
  const cache = new Map();
  // E.R(type, args, opts, id, t): hand-drawn shape as SVG paths. Boils at 8 fps (seed changes) unless opts.still.
  // Shapes are cached by (type, args, opts, seed); draw in local coordinates and move with E.g/E.tf so the cache hits.
  E.R = (type, args, o = {}, id = '', t = 0) => {
    const bf = o.still ? 0 : E.boilFrame(t);
    const seed = (E.hash(id + type + args.join(',')) ^ (bf * 2654435761)) % 2147483646 + 1;
    const key = type + '|' + args.map(a => typeof a === 'number' ? a.toFixed(1) : JSON.stringify(a)).join(',') + '|' + JSON.stringify(o) + '|' + seed;
    let s = cache.get(key);
    if (s === undefined) {
      const opt = {
        roughness: o.roughness ?? 1.1, bowing: o.bowing ?? 0.8, stroke: o.stroke || E.C.ink, strokeWidth: o.sw ?? 2,
        fill: o.fill, fillStyle: o.fillStyle || 'solid', fillWeight: o.fillWeight ?? 1.2, hachureGap: o.hachureGap ?? 5,
        seed, disableMultiStroke: o.single ?? false, disableMultiStrokeFill: true, preserveVertices: false,
        curveFitting: 0.95,
      };
      if (o.noStroke) opt.stroke = 'none';
      const dr = gen[type](...args, opt);
      s = gen.toPaths(dr).map(p => `<path d="${p.d}" stroke="${p.stroke}" stroke-width="${p.strokeWidth}" fill="${p.fill || 'none'}" stroke-linecap="round" stroke-linejoin="round"/>`).join('');
      if (cache.size > 40000) cache.clear();
      cache.set(key, s);
    }
    return o.opacity !== undefined ? `<g opacity="${clamp(o.opacity).toFixed(3)}">${s}</g>` : s;
  };
  // flat offset shadow for a cut-paper object
  E.shadow = (inner, dx = 3, dy = 3) => `<g transform="translate(${dx},${dy})" opacity="0.22" filter="url(#flat)">${inner}</g>`;

  // ---------- timeline ----------
  const BEAT = {};
  for (const b of (window.TL ? TL.beats : [])) BEAT[b.id] = b;
  E.TL = window.TL;
  E.B = id => { const b = BEAT[id]; if (!b) throw new Error('unknown beat ' + id); return b; };
  // b.text is the narration as spoken in this render's language (work/timeline.py writes it)
  const said = b => b.text ?? b[E.LANG] ?? '';
  // where `sub` falls in beat b, as a fraction of the beat, or (with word times) in seconds from the beat start.
  // sub: a string in the render language, or {en: '...', fa: '...'}. A string that is not in this language's text but
  // is in the English source ("en") maps by its relative position there (about ±0.5 s): scenes written against the
  // English script still run in a translated render; give {en, fa} cues where the timing must be exact.
  const locate = (id, b, sub, atEnd) => {
    const tx = said(b), s = typeof sub === 'object' ? (sub[E.LANG] ?? sub.en) : sub;
    let i = tx.indexOf(s);
    if (i >= 0) {
      const j = atEnd ? Math.min(tx.length - 1, i + s.length) : i;
      if (b.ct && b.ct.length === tx.length) return { sec: b.ct[j] };   // real spoken time (word-aligned transcript)
      return { frac: (atEnd ? i + s.length : i) / Math.max(1, tx.length) };
    }
    const en = typeof sub === 'object' ? sub.en : sub;
    if (b.en && en && E.LANG !== 'en' && (i = b.en.indexOf(en)) >= 0) return { frac: (atEnd ? i + en.length : i) / Math.max(1, b.en.length) };
    throw new Error(`cue: "${s}" not in beat ${id}`);
  };
  // time at which the narration reaches `sub` in beat `id` (word-timed, or estimated by character position), + offset
  E.cue = (id, sub, off = 0) => {
    const b = E.B(id); if (!sub) return b.start + off;
    const r = locate(id, b, sub, false); return b.start + (r.sec ?? b.dur * r.frac) + off;
  };
  E.cueEnd = (id, sub, off = 0) => { const b = E.B(id), r = locate(id, b, sub, true); return b.start + (r.sec ?? b.dur * r.frac) + off; };
  E.scene = id => E.TL.scenes[id];

  // ---------- data (real measured or recorded results only; window.DATA from work/make_data.py) ----------
  E.D = path => {
    const parts = path.split('.'); let v = window.DATA;
    for (const p of parts) { if (v === undefined || v === null || !(p in Object(v))) throw new Error('missing data key ' + path); v = v[p]; }
    return v;
  };

  // registry
  E.comp = {}; E.scenes = {}; E.props = {};
  E.PINS = [];   // ribbon pins registered by scenes: {year, label, hollow, t0, row} (optional; see base.js Ribbon)
})();
