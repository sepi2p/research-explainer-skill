// Shared recurring objects: slips and plots (graph paper = real data), torn paper, sticky notes, stamps, term cards,
// chips, bubbles, the frame border, marks, the ladder HUD, the ribbon, the reveal, the two-paper legend and the caption
// bar. Every function returns an SVG string. Coordinates are logical px (854 x 480 screen, or world units).
// Text direction and fonts follow the render language (E.LANG, E.DIR); fixed labels come from E.L (core.js).
(() => {
  const { C, FONT } = E;
  const stampTag = (x, y, label) => {
    const w = Math.max(60, label.length * 7.4 + 16);
    return E.g(E.tf(x, y, 1, -4), E.rect(0, 0, w, 18, { fill: C.graph, stroke: C.teal, sw: 1.4, r: 3 }) +
      E.text(w / 2, 9.5, label, { size: 12, weight: 700, fill: C.teal }));
  };

  // ---- graph-paper slip: REAL data only. key = data path (E.D), fmt(value) -> inner HTML ----
  // o: {x, y, w, h, key, fmt, footer, stamp=true, rot, s, opacity, size, align, dir, pad, id, weight, valign, lh}
  E.comp.Slip = (t, o) => {
    const w = o.w || 220, h = o.h || 70, pad = o.pad ?? 10;
    const val = E.D(o.key);                       // throws if the key is missing: no literal data on graph paper
    const inner = o.fmt ? o.fmt(val) : E.esc(val);
    let s = '';
    s += E.rect(3, 4, w, h, { fill: C.ink, opacity: 0.18, r: 2 });
    s += E.rect(0, 0, w, h, { fill: C.graph, r: 2 });
    s += E.rect(0, 0, w, h, { fill: 'url(#gridp)', r: 2 });
    s += E.rect(0, 0, w, h, { stroke: C.ink, sw: 1.2, r: 2, opacity: 0.85 });
    if (o.stamp !== false) s += stampTag(pad + 2, -8, E.L.real);
    const fh = o.footer ? 17 : 0;
    s += E.html(pad, pad + (o.stamp !== false ? 4 : 0), w - 2 * pad, h - 2 * pad - fh - (o.stamp !== false ? 4 : 0), inner,
      { size: o.size || 15, align: o.align, dir: o.dir, lh: o.lh || 1.4, valign: o.valign || 'center', weight: o.weight });
    if (o.footer && o.footer.trim()) s += E.text(w - pad, h - 9, o.footer, { size: 12, dir: 'ltr', font: FONT.mono, anchor: 'end', fill: C.schematic });
    return E.g(E.tf(o.x || 0, o.y || 0, o.s ?? 1, o.rot || 0), s, { opacity: o.opacity });
  };

  // ---- graph-paper plot: REAL data only. Every value comes from a data key. ----
  // o: {x, y, w, h, s, opacity, xs (key of the x values), xlog (bool), ymax, yticks [numbers], ydec, title, xlabel,
  //     traces: [{key, color, appear: [t per point] | t0, fmt(v, i) -> string, labelDx, labelDy (number or array per point), dim (0..1)}],
  //     hlines: [{key, color, label, labelDy, t0}]  (a value from the data drawn as a dashed level, e.g. a floor),
  //     guides: [{key, color, t0, label, labelDy}]  (a computed curve from the data, e.g. the theory, drawn dashed),
  //     footer, stamp=true, size (tick label px, default 14), id}
  E.comp.Plot = (t, o) => {
    const w = o.w || 420, h = o.h || 260, size = o.size || 14;
    const L = o.ml ?? 58, R = o.mr ?? 22, T = o.mt ?? 44, B = o.mb ?? (o.footer ? 62 : 46);
    const xs = E.D(o.xs), ymax = o.ymax ?? 1;
    const ux = v => o.xlog ? Math.log(v / xs[0]) / Math.log(xs[xs.length - 1] / xs[0]) : (v - xs[0]) / (xs[xs.length - 1] - xs[0]);
    const X = v => L + ux(v) * (w - L - R), Y = v => h - B - (v / ymax) * (h - T - B);
    let s = E.rect(3, 4, w, h, { fill: C.ink, opacity: 0.18, r: 2 });
    s += E.rect(0, 0, w, h, { fill: C.graph, r: 2 }) + E.rect(0, 0, w, h, { fill: 'url(#gridp)', r: 2 }) + E.rect(0, 0, w, h, { stroke: C.ink, sw: 1.2, r: 2, opacity: 0.85 });
    if (o.stamp !== false) s += stampTag(12, -8, E.L.real);
    if (o.title) s += E.text(E.RTL ? w - 16 : 16, 24, o.title, { size: size + 2, weight: 700, anchor: 'start' });
    // axes and ticks (crisp: data is never boiled)
    s += E.line(L, T - 6, L, h - B, { stroke: C.ink, sw: 1.4 }) + E.line(L, h - B, w - R + 6, h - B, { stroke: C.ink, sw: 1.4 });
    for (const v of (o.yticks || [])) {
      s += E.line(L - 5, Y(v), L, Y(v), { stroke: C.ink, sw: 1.2 }) + E.line(L, Y(v), w - R, Y(v), { stroke: C.grid, sw: 1 });
      s += E.text(L - 9, Y(v) + 1, E.num(v, o.ydec ?? 1), { size, anchor: 'end', dir: 'ltr', fill: C.ink, font: E.RTL ? FONT.fa : FONT.en });
    }
    for (const v of xs) s += E.line(X(v), h - B, X(v), h - B + 5, { stroke: C.ink, sw: 1.2 }) + E.text(X(v), h - B + 16, E.num(v), { size, dir: 'ltr', font: E.RTL ? FONT.fa : FONT.en });
    if (o.xlabel) s += E.text((L + w - R) / 2, h - B + 34, o.xlabel, { size: size - 1, fill: '#3C4660' });
    const at = (sr, i) => Array.isArray(sr.appear) ? sr.appear[i] : sr.appear;
    // dashed levels and guide curves first, points over them
    for (const hl of (o.hlines || [])) {
      const k = hl.t0 !== undefined ? E.at(t, hl.t0, 0.6) : 1; if (k <= 0) continue;
      const v = E.D(hl.key), x1 = E.lerp(L, w - R, k);
      s += E.line(L, Y(v), x1, Y(v), { stroke: hl.color || C.schematic, sw: 2, dash: '7 6' });
      if (hl.label && k >= 1) s += E.text(w - R - 2, Y(v) + (hl.labelDy ?? -11), hl.label, { size: size - 1, anchor: E.RTL ? 'start' : 'end', fill: hl.color || C.schematic, weight: 700, stroke: C.graph, sw: 3 });
    }
    for (const g of (o.guides || [])) {
      const k = g.t0 !== undefined ? E.at(t, g.t0, 0.8) : 1; if (k <= 0) continue;
      const ys = E.D(g.key), n = 40; let d = '';
      for (let j = 0; j <= n; j++) {   // log-interpolated between the computed values
        const f = j / n * (xs.length - 1) * k, i = Math.min(xs.length - 2, Math.floor(f)), u = f - i;
        const xv = Math.exp(E.lerp(Math.log(xs[i]), Math.log(xs[i + 1]), u)), yv = Math.exp(E.lerp(Math.log(ys[i]), Math.log(ys[i + 1]), u));
        d += (j ? 'L' : 'M') + X(xv).toFixed(1) + ',' + Y(yv).toFixed(1);
      }
      s += E.path(d, { stroke: g.color || C.schematic, sw: 1.8, dash: '3 5', opacity: 0.9 });
      // label below the curve, between the 2nd and 3rd x values (the empty side of a falling curve)
      if (g.label && k >= 1) s += E.text((X(xs[1]) + X(xs[2])) / 2 - 18, (Y(ys[1]) + Y(ys[2])) / 2 + (g.labelDy ?? 30), g.label, { size: size, fill: g.color || C.schematic, weight: 700, stroke: C.graph, sw: 3 });
    }
    for (const sr of (o.traces || [])) {
      const ys = E.D(sr.key), col = sr.color || C.teal, dim = sr.dim ?? 1;
      let line = '', pts = '';
      ys.forEach((v, i) => {
        const t0 = at(sr, i); if (t0 !== undefined && t < t0) return;
        const a = t0 !== undefined ? E.sp(t, t0, 'play') : 1;
        if (i > 0) {
          const t1 = at(sr, i - 1), k = t0 !== undefined ? E.at(t, t0 - 0.05, 0.3) : 1;
          if (t1 === undefined || t >= t1) line += E.line(X(xs[i - 1]), Y(ys[i - 1]), E.lerp(X(xs[i - 1]), X(xs[i]), k), E.lerp(Y(ys[i - 1]), Y(v), k), { stroke: col, sw: 2.6, opacity: dim });
        }
        pts += E.circle(X(xs[i]), Y(v), 6.5 * Math.max(0, a), { fill: col, stroke: C.ink, sw: 1.2, opacity: dim });
        const ldx = Array.isArray(sr.labelDx) ? sr.labelDx[i] : (sr.labelDx ?? 0), ldy = Array.isArray(sr.labelDy) ? sr.labelDy[i] : (sr.labelDy ?? -17);
        if (sr.fmt) pts += E.text(X(xs[i]) + ldx, Y(v) + ldy, sr.fmt(v, i), { size: size + 1, weight: 700, fill: col, dir: 'ltr', opacity: E.clamp(a) * dim, stroke: C.graph, sw: 3.5, font: E.RTL ? FONT.fa : FONT.en });
      });
      s += line + pts;
    }
    if (o.footer) s += E.text(w - 10, h - 10, o.footer, { size: 12, dir: 'ltr', font: FONT.mono, anchor: 'end', fill: C.schematic });
    return E.g(E.tf(o.x || 0, o.y || 0, o.s ?? 1, o.rot || 0), s, { opacity: o.opacity });
  };

  // ---- torn cream paper: metaphor / schematic content (boils) ----
  // o: {x,y,w,h, id, inner (svg string, local coords), html (wrapped text), rot, s, opacity, fill, size, align, dir}
  E.comp.Torn = (t, o) => {
    const w = o.w || 200, h = o.h || 120, id = o.id || 'torn';
    const r = E.rng(E.hash(id));
    const pts = [];
    const n = Math.max(8, Math.round((w + h) / 18));
    for (let i = 0; i <= n; i++) pts.push([w * i / n, (r() - 0.5) * 6]);
    for (let i = 1; i <= Math.round(n * h / (w + h)) + 2; i++) pts.push([w + (r() - 0.5) * 6, h * i / (Math.round(n * h / (w + h)) + 2)]);
    for (let i = n; i >= 0; i--) pts.push([w * i / n, h + (r() - 0.5) * 7]);
    for (let i = Math.round(n * h / (w + h)) + 1; i >= 1; i--) pts.push([(r() - 0.5) * 6, h * i / (Math.round(n * h / (w + h)) + 2)]);
    let s = E.g('translate(3,4)', E.R('polygon', [pts], { fill: C.ink, noStroke: true, roughness: 0.6, still: true }, id + 'sh', t), { opacity: 0.16 });
    s += E.R('polygon', [pts], { fill: o.fill || C.cream, stroke: C.ink, sw: 1.3, roughness: 0.9 }, id, t);
    if (o.inner) s += o.inner;
    if (o.html) s += E.html(12, 10, w - 24, h - 20, o.html, { size: o.size || 16, align: o.align || 'center', dir: o.dir, valign: 'center' });
    return E.g(E.tf(o.x || 0, o.y || 0, o.s ?? 1, o.rot || 0), s, { opacity: o.opacity });
  };

  // ---- sticky note: the viewer's idea in plain words (<= 6 words) ----
  E.comp.Sticky = (t, o) => {
    const w = o.w || 132, h = o.h || 96;
    let s = E.rect(3, 5, w, h, { fill: C.ink, opacity: 0.18 });
    s += E.R('rectangle', [0, 0, w, h], { fill: C.sticky, stroke: '#C9A43A', sw: 1, roughness: 0.6 }, (o.id || 'st') + 'b', t);
    s += E.R('rectangle', [w / 2 - 26, -9, 52, 18], { fill: 'rgba(255,255,255,0.55)', noStroke: true, roughness: 0.5 }, (o.id || 'st') + 'tape', t);
    s += E.html(8, 6, w - 16, h - 12, E.esc(o.text), { size: o.size || 17, weight: 700, align: 'center', lh: 1.3 });
    return E.g(E.tf(o.x, o.y, o.s ?? 1, o.rot ?? -3), s, { opacity: o.opacity });
  };

  // ---- the naming stamp (E.L.named, or E.L.common for a commonly used name) ----
  E.comp.Stamp = (t, o) => {
    const label = o.label || E.L.named, w = o.w || Math.max(120, label.length * 15 + 34), h = 46;
    const k = o.t0 !== undefined ? E.clamp((t - o.t0) / 0.15) : 1;
    const sc = o.t0 !== undefined ? E.lerp(1.35, 1, E.ease.out(k)) : 1;
    let s = E.rect(-w / 2, -h / 2, w, h, { fill: 'rgba(251,243,226,0.82)', stroke: C.brick, sw: 3, r: 6 }) + E.rect(-w / 2 + 5, -h / 2 + 5, w - 10, h - 10, { stroke: C.brick, sw: 1.2, r: 4 });
    s += E.text(0, 2, label, { size: 22, weight: 900, fill: C.brick, ls: E.RTL ? undefined : 1.5 });
    return E.g(E.tf(o.x, o.y, sc * (o.s ?? 1), o.rot ?? -8), s, { opacity: (o.opacity ?? 1) * (o.t0 !== undefined ? E.clamp((t - o.t0) / 0.05) : 1) * 0.92 });
  };

  // ---- term card (the reward): the real name of the idea ----
  // o: {x,y,s,rot, title (the name, render language), sub (second line, e.g. a formula or the English term; LTR),
  //     cite (one line: a citation or a definition), year (number, optional), titleSize, subSize, opacity}
  E.comp.TermCard = (t, o) => {
    const w = 300, h = 170, rtl = E.RTL;
    let s = E.rect(4, 5, w, h, { fill: C.ink, opacity: 0.2, r: 4 });
    s += E.rect(0, 0, w, h, { fill: '#FFFDF6', stroke: C.ink, sw: 1.4, r: 4 });
    s += E.line(14, 100, w - 14, 100, { stroke: '#E07B6A', sw: 1 });
    s += E.text(rtl ? w - 16 : 16, 36, o.title, { size: o.titleSize || 25, weight: 700, anchor: 'start' });
    if (o.sub) s += E.text(rtl ? w - 16 : 16, 72, o.sub, { size: o.subSize || 19, weight: 600, dir: 'ltr', font: FONT.en, anchor: rtl ? 'end' : 'start', fill: C.steel });
    if (o.year) s += E.text(rtl ? 18 : w - 18, 34, E.num(o.year), { size: 32, weight: 900, fill: C.brick, anchor: 'end', dir: rtl ? 'rtl' : 'ltr' });
    if (o.cite) s += E.html(14, 106, w - 28, 58, E.esc(o.cite), { dir: o.citeDir || 'ltr', font: FONT.en, size: 13, lh: 1.3, color: '#3C4660', align: o.citeDir === 'rtl' ? 'right' : 'left', valign: 'flex-start' });
    return E.g(E.tf(o.x, o.y, o.s ?? 1, o.rot || 0), s, { opacity: o.opacity });
  };

  // ---- chip: a quick name or setting, no stamp ----
  E.comp.Chip = (t, o) => {
    const w = o.w || 170, h = o.h || 28;
    let s = E.rect(2, 3, w, h, { fill: C.ink, opacity: 0.15, r: h / 2 });
    s += E.rect(0, 0, w, h, { fill: o.fill || '#FFFDF6', stroke: o.stroke || C.ink, sw: 1.2, r: h / 2 });
    s += E.text(w / 2, h / 2 + 1, o.text, { size: o.size || 13, dir: o.dir || 'ltr', font: o.dir === 'rtl' ? FONT.fa : (o.font || FONT.en), weight: 600, fill: o.color || C.ink });
    if (o.lock) s += lockGlyph(w - 16, h / 2);
    return E.g(E.tf(o.x, o.y, o.s ?? 1, o.rot || 0), s, { opacity: o.opacity });
  };
  const lockGlyph = (x, y, col = C.schematic) => E.rect(x - 5, y - 2, 10, 8, { fill: col, r: 1.5 }) + E.path(`M${x - 3},${y - 2} v-3 a3,3 0 0 1 6,0 v3`, { stroke: col, sw: 1.6 });
  E.lockGlyph = lockGlyph;

  // ---- speech bubble ----
  // o: {x,y,w,h,text|html, s, opacity, tail 'left'|'right', fill, size, initial (a letter in a small avatar disc), id}
  E.comp.Bubble = (t, o) => {
    const w = o.w || 260, h = o.h || 52;
    let s = E.rect(3, 4, w, h, { fill: C.ink, opacity: 0.16, r: 16 });
    s += E.rect(0, 0, w, h, { fill: o.fill || C.white, stroke: C.ink, sw: 1.4, r: 16 });
    const tx = o.tail === 'left' ? 18 : w - 18;
    s += E.path(`M${tx - 7},${h - 1} L${tx + (o.tail === 'left' ? -8 : 8)},${h + 11} L${tx + 7},${h - 1}`, { fill: o.fill || C.white, stroke: C.ink, sw: 1.4 });
    s += E.rect(tx - 7.5, h - 3, 15, 4, { fill: o.fill || C.white });
    let pad = 12, x0 = 12;
    if (o.initial) {
      const ax = E.RTL ? w - 22 : 22;
      s += E.circle(ax, h / 2, 13, { fill: C.skin, stroke: C.ink, sw: 1.2 }) + E.text(ax, h / 2 + 1, o.initial, { size: 12, weight: 700 });
      pad = 40; if (!E.RTL) x0 = 40;
    }
    s += E.html(E.RTL ? 10 : x0, 4, w - pad - 10, h - 8, o.html || E.esc(o.text), { size: o.size || 16, weight: 500, valign: 'center' });
    return E.g(E.tf(o.x, o.y, o.s ?? 1, o.rot || 0), s, { opacity: o.opacity });
  };

  // ---- frame border: shown when the camera has zoomed through a frame until it is the screen (frame shots only) ----
  // o: {k (0..1 visibility), chip (short text in a saffron pill, e.g. a count), label (text at the top right)}
  E.comp.FrameBorder = (t, o) => {
    const k = E.clamp(o.k ?? 1); if (k <= 0) return '';
    const W = E.W, H = E.H, m = 6;
    let s = '';
    for (let i = 0; i < 4; i++) s += E.rect(m + i * 3, m + i * 3, W - 2 * (m + i * 3), H - 2 * (m + i * 3), { stroke: C.saffron, sw: 3, opacity: 0.18 - i * 0.04, r: 6 });
    s += E.rect(m / 2, m / 2, W - m, H - m, { stroke: C.saffron, sw: 6, r: 8 });
    const br = (x, y, sx, sy) => E.path(`M${x},${y + sy * 26} L${x},${y} L${x + sx * 26},${y}`, { stroke: '#FFF4D6', sw: 3 });
    s += br(14, 14, 1, 1) + br(W - 14, 14, -1, 1) + br(14, H - 14, 1, -1) + br(W - 14, H - 14, -1, -1);
    if (o.chip) {
      const cw = Math.max(80, String(o.chip).length * 8 + 28);
      s += E.g(E.tf(E.RTL ? W - 22 - cw : 22, 20), E.rect(0, 0, cw, 26, { fill: C.saffron, r: 13 }) + E.text(cw / 2, 14, o.chip, { size: 14, weight: 700, fill: C.ink }));
    }
    if (o.label) s += E.text(E.RTL ? 26 : W - 26, 33, o.label, { size: 14, weight: 700, fill: C.saffron, anchor: 'end' });
    return E.g('', s, { opacity: k });
  };

  // ---- marks ----
  E.comp.Check = (t, o) => E.g(E.tf(o.x, o.y, (o.s ?? 1) * E.spring(t - (o.t0 ?? -9), 300, 14)),
    E.circle(0, 0, 15, { fill: C.pistachio }) + E.path('M-7,0 L-2,6 L8,-6', { stroke: C.white, sw: 3.4 }), { opacity: o.opacity });
  E.comp.Cross = (t, o) => E.g(E.tf(o.x, o.y, (o.s ?? 1) * E.spring(t - (o.t0 ?? -9), 300, 14)),
    E.circle(0, 0, 15, { fill: o.grey ? C.schematic : C.pomegranate }) + E.path('M-6,-6 L6,6 M6,-6 L-6,6', { stroke: C.white, sw: 3.4 }), { opacity: o.opacity });

  // ---- ladder HUD (screen right). Rungs come from E.RUNGS (set in main.js): [{label, locked, hiddenUntil}] ----
  // st: {current: index, cracked: [idx...], k: visibility, pulseTop: 0..1, t}
  E.RUNGS = E.RUNGS || [];
  E.comp.Ladder = (t, st) => {
    const k = st.k ?? 1, R = E.RUNGS, n = R.length; if (k <= 0 || !n) return '';
    const x0 = 826, x1 = 846, bottom = 356, gap = n > 1 ? Math.min(60, 270 / (n - 1)) : 0;
    const yOf = i => bottom - i * gap, top = yOf(n - 1);
    let s = '';
    s += E.line(x0, top - 26, x0, bottom + 20, { stroke: C.paper, sw: 5, opacity: 0.7 }) + E.line(x1, top - 26, x1, bottom + 20, { stroke: C.paper, sw: 5, opacity: 0.7 });
    s += E.R('line', [x0, top - 26, x0, bottom + 20], { sw: 2, roughness: 0.7 }, 'ladL', t);
    s += E.R('line', [x1, top - 26, x1, bottom + 20], { sw: 2, roughness: 0.7 }, 'ladR', t);
    R.forEach((r, i) => {
      const y = yOf(i), cur = st.current === i, done = st.current > i, locked = r.locked;
      let col = locked ? C.schematic : cur ? C.saffron : done ? C.ink : '#B8AF9C';
      if (locked && st.pulseTop) col = st.pulseTop > 0.5 ? C.saffron : C.schematic;
      s += E.line(x0, y, x1, y, { stroke: C.paper, sw: cur ? 7 : 5.5, opacity: 0.7 });
      s += E.R('line', [x0, y, x1, y], { sw: cur ? 4 : 2.5, stroke: col, roughness: 0.6 }, 'rung' + i, t);
      if (st.cracked && st.cracked.includes(i)) s += E.path(`M${x0 + 4},${y - 4} l4,5 l3,-4 l4,6 l3,-3`, { stroke: C.pomegranate, sw: 1.8 });
      let hidden = false; if (r.hiddenUntil) { try { hidden = t < r.hiddenUntil(); } catch (e) { hidden = true; } }
      const label = hidden ? '?' : r.label;
      const rtl = /[؀-ۿ]/.test(label);
      s += E.text(x0 - 8, y + 1, label, { size: cur ? 13 : 11, weight: cur ? 700 : 500, dir: rtl ? 'rtl' : 'ltr', font: rtl ? FONT.fa : FONT.en, anchor: rtl ? 'start' : 'end', fill: col, opacity: cur ? 1 : 0.9, stroke: C.paper, sw: 3.5 });
      if (locked) s += lockGlyph(x0 + 10, y - 12, col);
    });
    return E.g('', s, { opacity: k });
  };

  // ---- ribbon (bottom): an optional timeline axis with pins, e.g. the year each named idea was published ----
  // E.YR sets the range; scenes register pins with E.PINS.push({year, label, hollow, t0, row}) at load time.
  E.YR = E.YR || { y0: 1966, y1: 2027, x0: 40, x1: 800, step: 10 };
  E.yearX = y => E.lerp(E.YR.x0, E.YR.x1, (y - E.YR.y0) / (E.YR.y1 - E.YR.y0));
  E.comp.Ribbon = (t, o) => {
    const k = E.clamp(o.k ?? 1); if (k <= 0) return '';
    const y = E.H - 34 + (1 - k) * 40, step = E.YR.step || 10;
    let s = E.rect(0, y, E.W, 34, { fill: '#EADBBE', opacity: 0.96 }) + E.line(0, y, E.W, y, { stroke: C.ink, sw: 1, opacity: 0.4 });
    for (let yr = Math.ceil(E.YR.y0 / (step / 2)) * (step / 2); yr <= E.YR.y1; yr += step / 2) {
      const x = E.yearX(yr);
      s += E.line(x, y + 4, x, y + 9, { stroke: C.ink, sw: 1, opacity: 0.5 });
      if (yr % step === 0) s += E.text(x, y + 24, E.num(yr), { size: 12, fill: C.schematic });
    }
    (o.pins || []).forEach(p => {
      if (p.t0 !== undefined && t < p.t0) return;
      const a = p.t0 !== undefined ? E.sp(t, p.t0, 'play') : 1;
      const x = E.yearX(p.year), py = y + 6 - 10 * (1 - a);
      s += E.g(E.tf(x, py), E.path('M0,0 L-5,-9 L5,-9 Z', { fill: p.hollow ? '#FFFDF6' : C.brick, stroke: C.brick, sw: 1.4 }) +
        (p.label && p.t0 !== undefined && t < p.t0 + 3.2 ? E.g('', E.text(0, -16 - (p.row || 0) * 14, p.label, { size: 13, dir: 'ltr', font: FONT.en, weight: 700, fill: C.brick, stroke: '#EADBBE', sw: 3 }), { opacity: E.win(t, p.t0, p.t0 + 3.2, 0.3) }) : ''), { opacity: E.clamp(a * 1.5) });
    });
    return s;
  };

  // ---- the reveal: sticky note -> stamp on the name word -> flips into a term card -> flies to its rung ----
  // o: {t0 (sticky in), tStamp (cue of the spoken name word), sticky:{x,y,text,w,h}, card:{title,sub,cite,year},
  //     stampLabel, cardXY [x,y], cardS, flyTo [x,y] (e.g. [836, rungY]), tFly}
  E.comp.Reveal = (t, o) => {
    if (t < o.t0) return '';
    const sx = o.sticky.x, sy = o.sticky.y, sw = o.sticky.w || 132, sh = o.sticky.h || 96;
    const cx = o.cardXY ? o.cardXY[0] : sx - 80, cy = o.cardXY ? o.cardXY[1] : sy - 30;
    const tFlip = o.tStamp + 0.45, tFly = o.tFly ?? (o.tStamp + 2.6);
    let s = '';
    if (t < tFlip + 0.18) {
      const sc = E.spring(t - o.t0, 260, 14) * (t > tFlip ? 1 - E.clamp((t - tFlip) / 0.18) : 1);
      s += E.comp.Sticky(t, { x: sx, y: sy, text: o.sticky.text, s: 0.0001 + sc, id: 'rv' + o.card.title, w: sw, h: sh });
    }
    if (t >= o.tStamp && t < tFlip + 0.3) s += E.comp.Stamp(t, { x: sx + sw / 2, y: sy + sh * 0.86, t0: o.tStamp, label: o.stampLabel, opacity: 1 - E.clamp((t - tFlip) / 0.3) });
    if (t >= tFlip) {
      const f = E.clamp((t - tFlip) / 0.18);
      const fly = E.at(t, tFly, 0.6, E.ease.inOut);
      const tx = o.flyTo ? E.lerp(cx, o.flyTo[0], fly) : cx, ty = o.flyTo ? E.lerp(cy, o.flyTo[1], fly) : cy;
      const sc = (o.cardS || 1) * E.lerp(1, o.flyTo ? 0.08 : 1, fly);
      if (!(o.flyTo && fly >= 1)) s += E.g(E.tf(tx, ty, 1, 0, sc * f, sc), E.comp.TermCard(t, { x: 0, y: 0, ...o.card }), { opacity: o.flyTo ? 1 - E.clamp((fly - 0.85) / 0.15) : 1 });
    }
    return s;
  };

  // ---- two-paper legend: what graph paper and torn paper mean (pin it on a wall of the set) ----
  E.comp.Legend = (t, o = {}) => {
    let s = E.R('rectangle', [-104, -66, 208, 132], { fill: '#F7EEDB', sw: 1.6, roughness: 0.6 }, 'leg', t);
    s += E.circle(0, -62, 3, { fill: C.brick });
    const tx = E.RTL ? 22 : -42, an = E.RTL ? 'start' : 'start';
    const sw = E.RTL ? [30, 80] : [-92, -50];
    s += E.rect(sw[0], -50, 42, 30, { fill: C.graph }) + E.rect(sw[0], -50, 42, 30, { fill: 'url(#gridp)' }) + E.rect(sw[0], -50, 42, 30, { stroke: C.ink, sw: 1 });
    s += E.html(E.RTL ? -96 : tx, -52, 136, 34, E.esc(E.L.graph), { size: 11, weight: 700, lh: 1.2 });
    s += E.R('polygon', [[[sw[0], -4], [sw[0] + 42, -6], [sw[0] + 44, 24], [sw[0] - 2, 28]]], { fill: C.cream, sw: 1, roughness: 1.3 }, 'legt', t);
    s += E.html(E.RTL ? -96 : tx, -6, 136, 34, E.esc(E.L.torn), { size: 11, weight: 700, lh: 1.2 });
    s += E.g(E.tf(0, 48, 1, -3), E.rect(-94, -11, 188, 22, { stroke: C.brick, sw: 1.4, r: 3 }) + E.text(0, 0.5, E.L.made, { size: 11, weight: 700, fill: C.brick }));
    return E.g(E.tf(o.x ?? 0, o.y ?? 0, o.s ?? 1, o.rot || 0), s, { opacity: o.opacity });
  };

  // ---- caption bar: the narration on screen (text-only renders, or burned subtitles) ----
  // o: {text, k (0..1), size}
  E.comp.Caption = (t, o) => {
    const k = E.clamp(o.k ?? 1); if (k <= 0 || !o.text) return '';
    const size = o.size || 17, w = Math.min(740, 60 + o.text.length * size * 0.5), h = o.text.length * size * 0.5 > 680 ? 58 : 36;
    const x = (E.W - w) / 2, y = E.H - h - 12 + (1 - k) * 8;
    let s = E.rect(x + 2, y + 3, w, h, { fill: C.ink, opacity: 0.15 * k, r: 8 });
    s += E.rect(x, y, w, h, { fill: '#FFFBF0', stroke: C.ink, sw: 1, r: 8, opacity: 0.95 * k });
    s += E.html(x + 14, y + 3, w - 28, h - 6, E.esc(o.text), { size, align: 'center', lh: 1.3, weight: 500, opacity: k });
    return s;
  };
})();
