// The demo's set: a baker's bench as a cut-paper diorama (world coordinates, x 0..1700, y 0..480 at rest; the wall and
// floor run past the edges so wide shots never show a gap). Layers: L0 wall texture (parallax 0.3), L1 shelf and jars
// (0.6), L2 bench, wall props, scale and puppet (1.0), L3 foreground clutter (1.3). Replace this file for your world;
// keep the pattern: fixed world positions in E.POS, props as functions of (t, options), one E.comp.<World>(t, cam, o).
(() => {
  const { C } = E;
  E.POS = {
    benchTop: 330,
    scale: { x: 760, y: 330 },                     // bottom centre of the scale, standing on the bench
    pip: { x: 575, y: 342 },                       // bottom of Pip's torso (hidden by the bench front)
    rail: { x0: 830, x1: 1090, y: 196 },           // the string the printed tickets hang on
    window: { x: 1250, y: 160, w: 196, h: 146 },
    clock: { x: 960, y: 74 },
    board: { x: 1480, y: 205, w: 192, h: 108 },    // the chart board: 16:9, so a frame shot fills the screen exactly
    legend: { x: 330, y: 214 },
  };
  const P = E.POS;
  E.POS.frame = P.board;                           // default frame-shot target

  // ---------- L0: the wall ----------
  const wall = (t) => {
    let s = E.rect(-600, -500, 3000, 900, { fill: '#EADBBB' });
    const r = E.rng(31);
    for (let i = 0; i < 90; i++) s += E.circle(-400 + r() * 2600, -300 + r() * 600, 6 + r() * 22, { fill: '#E1CFA9', opacity: 0.35 + r() * 0.3 });
    // tiled splashback above the bench
    for (let x = -400; x < 2200; x += 34) for (let y = 262; y < 330; y += 34) s += E.rect(x + 1.5, y + 1.5, 31, 31, { fill: '#E4E6D6', stroke: '#C9C3A6', sw: 1, r: 2 });
    return s;
  };
  // light from the window: a shaft with dust motes (always moving)
  const shaft = (t) => {
    const w = P.window, x = w.x, y = w.y + w.h / 2;
    let s = `<polygon points="${x - w.w / 2 + 10},${y - w.h + 10} ${x + w.w / 2 - 10},${y - w.h + 10} ${x - 10},${P.benchTop} ${x - 330},${P.benchTop}" fill="url(#shaftg)" opacity="0.35"/>`;
    for (let i = 0; i < 24; i++) {
      const r = E.rng(E.hash('dust' + i)), u = r(), sp = 5 + r() * 9;
      const yy = (r() * 260 + t * sp) % 250 + y - 120, k = (yy - (y - 120)) / 250;
      const xx = E.lerp(x - 40, x - 250, k) + (r() - 0.5) * 120 * (0.4 + k) + Math.sin(t * 0.6 + i) * 6;
      s += E.circle(xx, yy, 1 + u * 1.3, { fill: '#FFF6DE', opacity: 0.45 + 0.4 * Math.sin(t * 1.3 + i) });
    }
    return s;
  };

  // ---------- L1: shelf with jars ----------
  const shelf = (t, x0, x1, y, id) => E.R('rectangle', [x0, y, x1 - x0, 8], { fill: C.wood, sw: 1.5, roughness: 0.6 }, id, t) +
    E.R('line', [x0 + 12, y + 8, x0 + 12, y + 26], { stroke: C.woodDark, sw: 2 }, id + 'b1', t) + E.R('line', [x1 - 12, y + 8, x1 - 12, y + 26], { stroke: C.woodDark, sw: 2 }, id + 'b2', t);
  const jars = (t, x0, x1, y, seed) => {
    let s = '', x = x0; const r = E.rng(seed);
    const fills = ['#E9D9A6', '#C98A4B', '#F3EBDD', '#B7C79A', '#D9A35E'];
    while (x < x1 - 30) {
      const w = 26 + r() * 18, h = 30 + r() * 26, id = 'jar' + seed + '_' + Math.round(x), f = fills[Math.floor(r() * fills.length)];
      s += E.R('rectangle', [x, y - h, w, h], { fill: '#F6F1E4', sw: 1.4, roughness: 0.7 }, id, t);
      s += E.rect(x + 3, y - h * 0.72, w - 6, h * 0.72 - 3, { fill: f, opacity: 0.85 });
      s += E.R('rectangle', [x - 2, y - h - 7, w + 4, 8], { fill: r() < 0.5 ? C.brick : C.teal, sw: 1.2, roughness: 0.6 }, id + 'lid', t);
      x += w + 10 + r() * 14;
    }
    return s;
  };

  // ---------- L2 props ----------
  E.props.clock = (t, o = {}) => {
    const { x, y } = P.clock;
    let s = E.R('circle', [0, 0, 64], { fill: '#FFFDF6', sw: 2.2, roughness: 0.6 }, 'clk', t);
    for (let i = 0; i < 12; i++) { const a = i * 30 * Math.PI / 180; s += E.line(Math.sin(a) * 24, -Math.cos(a) * 24, Math.sin(a) * 28, -Math.cos(a) * 28, { stroke: C.ink, sw: i % 3 ? 1.2 : 2.2 }); }
    const sec = Math.floor(t) * 6 * Math.PI / 180, mn = (t / 60 * 6 + 60) * Math.PI / 180;
    s += E.line(0, 0, Math.sin(mn) * 20, -Math.cos(mn) * 20, { stroke: C.ink, sw: 2.6 }) + E.line(0, 0, Math.sin(2.1) * 13, -Math.cos(2.1) * 13, { stroke: C.ink, sw: 3 });
    s += E.line(0, 0, Math.sin(sec) * 25, -Math.cos(sec) * 25, { stroke: C.brick, sw: 1.3 }) + E.circle(0, 0, 2.6, { fill: C.ink });
    return E.g(E.tf(x, y), s, { opacity: o.opacity });
  };

  // the window: sky and distant roofs (their own parallax), a sash that swings open (o.open 0..1), a curtain that
  // flutters while o.wind > 0
  E.props.window = (t, cam, o = {}) => {
    const w = P.window, x0 = w.x - w.w / 2, y0 = w.y - w.h / 2, open = E.clamp(o.open || 0), wind = o.wind || 0;
    let s = `<clipPath id="winclip"><rect x="${x0}" y="${y0}" width="${w.w}" height="${w.h}"/></clipPath>`;
    let out = E.rect(x0, y0, w.w, w.h, { fill: C.sky });
    const dx = (cam.x - 900) * 0.25;
    for (let i = 0; i < 6; i++) { const rx = x0 - 40 + i * 52 + dx, rh = 30 + (i * 37 % 26); out += E.rect(rx, y0 + w.h - rh, 46, rh, { fill: '#B9CFCB' }) + E.path(`M${rx - 4},${y0 + w.h - rh} L${rx + 23},${y0 + w.h - rh - 16} L${rx + 50},${y0 + w.h - rh} Z`, { fill: '#A9C2BE' }); }
    out += E.circle(x0 + 40 + dx * 0.3, y0 + 34, 14, { fill: '#FFF4D6', opacity: 0.9 });
    s += E.g('', out, { clip: 'winclip' });
    // frame and sash: the right pane swings inward (drawn narrower as it turns)
    s += E.R('rectangle', [x0 - 8, y0 - 8, w.w + 16, w.h + 16], { stroke: C.woodDark, sw: 6, roughness: 0.5 }, 'winF', t);
    s += E.R('line', [w.x, y0, w.x, y0 + w.h], { stroke: C.woodDark, sw: 4, roughness: 0.4 }, 'winM', t);
    s += E.R('line', [x0, w.y, w.x, w.y], { stroke: C.woodDark, sw: 3, roughness: 0.4 }, 'winH', t);
    const pw = (w.w / 2) * (1 - 0.82 * open), skew = 14 * open;
    s += E.R('polygon', [[[w.x + w.w / 2, y0], [w.x + w.w / 2 - pw, y0 - skew], [w.x + w.w / 2 - pw, y0 + w.h + skew], [w.x + w.w / 2, y0 + w.h]]], { fill: open > 0.02 ? 'rgba(215,232,230,0.55)' : 'none', stroke: C.woodDark, sw: 3.5, roughness: 0.5 }, 'winS' + Math.round(open * 20), t);
    if (open < 0.02) s += E.R('line', [w.x, w.y, w.x + w.w / 2, w.y], { stroke: C.woodDark, sw: 3, roughness: 0.4 }, 'winH2', t);
    s += E.rect(x0 - 16, y0 + w.h + 6, w.w + 32, 9, { fill: C.wood, stroke: C.ink, sw: 1.2 });
    // curtain on the left: a torn-paper strip that billows with the wind (boils)
    const n = 7, pts = [];
    for (let i = 0; i <= n; i++) { const k = i / n; pts.push([x0 - 30 + Math.sin(t * 5 + k * 4) * 9 * wind * k - 30 * wind * k * k, y0 - 12 + k * (w.h + 30)]); }
    const back = pts.slice().reverse().map(([px, py]) => [px + 36 - 8 * wind * (py - y0) / w.h, py]);
    s += E.R('polygon', [pts.concat(back)], { fill: '#E9B8A6', sw: 1.6, roughness: 1.0 }, 'curt' + Math.round(wind * 4), t);
    s += E.R('line', [x0 - 40, y0 - 14, x0 + w.w + 30, y0 - 14], { stroke: C.woodDark, sw: 3 }, 'rod', t);
    return s;
  };

  // the ticket rail: a string with pegs; tickets (graph paper, real readings) are drawn by the scenes
  E.props.rail = (t, o = {}) => {
    const r = P.rail, sag = 7;
    let s = E.R('curve', [[[r.x0 - 20, r.y - 4], [(r.x0 + r.x1) / 2, r.y + sag], [r.x1 + 20, r.y - 4]]], { stroke: C.ink, sw: 1.4, roughness: 0.6 }, 'rail', t);
    s += E.circle(r.x0 - 20, r.y - 4, 3.5, { fill: C.woodDark }) + E.circle(r.x1 + 20, r.y - 4, 3.5, { fill: C.woodDark });
    return s;
  };
  E.railXY = i => { const r = P.rail, x = r.x0 + 26 + i * 52; const u = (x - r.x0 + 20) / (r.x1 - r.x0 + 40); return [x, r.y - 4 + 4 * 7 * u * (1 - u) + 3]; };
  // a printed ticket: graph paper with reading i of the example session (real data), hung from its top centre (x, y)
  E.props.ticket = (t, i, x, y, rot = 0) => E.g(E.tf(x, y, 1, rot),
    E.comp.Slip(t, { x: -23, y: 0, w: 46, h: 26, key: `readings.session.readings.${i}`, fmt: v => E.num(v, 2), size: 14, weight: 700, stamp: false, align: 'center', pad: 2, id: 'tk' + i }));
  E.props.peg = (x, y) => E.rect(x - 3, y - 9, 6, 16, { fill: C.wood, stroke: C.ink, sw: 1, r: 1.5 });

  // the chart board: a wooden frame around a graph-paper sheet; `inner` is drawn in 854 x 480 screen units and scaled
  // into the board, so a frame shot can cross-fade to the same drawing in screen space without a jump
  E.props.board = (t, o = {}) => {
    const b = P.board, x0 = b.x - b.w / 2, y0 = b.y - b.h / 2, k = b.w / E.W;
    let s = E.rect(x0 - 3, y0 + 4, b.w + 10, b.h + 10, { fill: C.ink, opacity: 0.18 });
    s += E.rect(x0, y0, b.w, b.h, { fill: '#FBF4E4' });
    if (o.inner) s += E.g(E.tf(x0, y0, k), o.inner);
    s += E.R('rectangle', [x0 - 6, y0 - 6, b.w + 12, b.h + 12], { stroke: C.woodDark, sw: 6, roughness: 0.5 }, 'brdF', t);
    s += E.R('line', [b.x - 30, y0 - 9, b.x, y0 - 34], { stroke: C.ink, sw: 1.2 }, 'brdS1', t) + E.R('line', [b.x + 30, y0 - 9, b.x, y0 - 34], { stroke: C.ink, sw: 1.2 }, 'brdS2', t);
    s += E.circle(b.x, y0 - 34, 3, { fill: C.brick });
    return s;
  };

  // the wobbly kitchen scale. o: {value (kg, where the needle points), avg (kg, a saffron pointer), avgK (0..1),
  //   bag (0..1 visible), bagY (drop offset), slotGlow (0..1), lean (deg, extra needle lean), trueMark (0..1)}
  const ANG = v => (-120 + 60 * v) * Math.PI / 180;   // 0..4 kg over 240 degrees, 2 kg straight up
  E.scaleAngle = ANG;
  E.props.scale = (t, o = {}) => {
    const id = 'scl';
    let s = '';
    s += E.R('rectangle', [-50, -4, 18, 6], { fill: C.ink, sw: 1 }, id + 'f1', t) + E.R('rectangle', [32, -4, 18, 6], { fill: C.ink, sw: 1 }, id + 'f2', t);
    s += E.R('path', ['M-58,-4 L-52,-100 Q-50,-106 -44,-106 L44,-106 Q50,-106 52,-100 L58,-4 Z'], { fill: '#E7D9BC', sw: 2.2, roughness: 0.7 }, id + 'body', t);
    s += E.R('rectangle', [-44, -14, 88, 6], { fill: C.woodDark, sw: 1, roughness: 0.4 }, id + 'trim', t);
    // plate on its stem
    s += E.R('rectangle', [-7, -118, 14, 13], { fill: C.schematic, sw: 1.4, roughness: 0.4 }, id + 'stem', t);
    s += E.R('ellipse', [0, -120, 150, 14], { fill: '#C9CED6', sw: 1.8, roughness: 0.5 }, id + 'plate', t);
    // dial (crisp: it carries the reading)
    const cy = -56, R = 38;
    s += E.circle(0, cy, R + 4, { fill: C.woodDark }) + E.circle(0, cy, R, { fill: '#FFFDF6', stroke: C.ink, sw: 1.4 });
    for (let v = 0; v <= 4.001; v += 0.25) {
      const a = ANG(v), maj = Math.abs(v - Math.round(v)) < 1e-6;
      s += E.line(Math.sin(a) * (R - (maj ? 8 : 5)), cy - Math.cos(a) * (R - (maj ? 8 : 5)), Math.sin(a) * (R - 2), cy - Math.cos(a) * (R - 2), { stroke: C.ink, sw: maj ? 1.6 : 0.9 });
      if (maj) s += E.text(Math.sin(a) * (R - 16), cy - Math.cos(a) * (R - 16) + 1, E.num(v), { size: 10, weight: 700, dir: 'ltr', font: E.RTL ? E.FONT.fa : E.FONT.en });
    }
    s += E.text(0, cy + 17, 'kg', { size: 9, dir: 'ltr', font: E.FONT.en, fill: C.schematic });
    if (o.trueMark) { const a = ANG(E.D('readings.true')); s += E.g(E.tf(Math.sin(a) * (R + 9), cy - Math.cos(a) * (R + 9), 1, a * 180 / Math.PI), E.path('M0,-1 L-5,-9 L5,-9 Z', { fill: C.pistachio, stroke: C.ink, sw: 1 }), { opacity: o.trueMark }); }
    if (o.avg !== undefined && (o.avgK ?? 1) > 0) {
      const a = ANG(o.avg);
      s += E.g(E.tf(0, cy, 1, a * 180 / Math.PI), E.path(`M0,${-R + 3} L-6,${-R + 15} L6,${-R + 15} Z`, { fill: C.saffron, stroke: C.ink, sw: 1.2 }), { opacity: o.avgK ?? 1 });
    }
    const a = ANG(o.value ?? 0) + (o.lean || 0) * Math.PI / 180;
    s += E.line(0, cy, Math.sin(a) * (R - 6), cy - Math.cos(a) * (R - 6), { stroke: C.ink, sw: 2.2 }) + E.circle(0, cy, 3.6, { fill: C.ink });
    // ticket slot on the right face
    if (o.slotGlow) s += E.rect(50, -64, 14, 40, { fill: C.saffron, opacity: 0.5 * o.slotGlow, r: 5 });
    s += E.R('line', [56, -60, 57, -28], { stroke: '#3A2A1C', sw: 4, roughness: 0.3 }, id + 'slot', t);
    // the bag of flour on the plate (drops in with o.bagY)
    if (o.bag) {
      let b = E.R('path', ['M-32,0 L-28,-62 L-20,-70 L-8,-64 L4,-72 L16,-64 L28,-70 L32,0 Z'], { fill: '#F2E8D5', sw: 1.8, roughness: 0.9 }, id + 'bag', t);
      b += E.R('rectangle', [-20, -46, 40, 30], { fill: C.cream, stroke: C.brick, sw: 1.2, roughness: 0.5 }, id + 'lab', t);
      b += E.text(0, -37, 'FLOUR', { size: 8.5, weight: 700, dir: 'ltr', font: E.FONT.en, fill: C.brick });
      b += E.text(0, -24, `${E.num(E.D('readings.true'))} kg`, { size: 10, weight: 700, dir: 'ltr', font: E.FONT.en, fill: C.ink });
      s += E.g(E.tf(0, -126 + (o.bagY || 0)), b, { opacity: o.bag });
    }
    return E.g(E.tf(P.scale.x, P.scale.y), s);
  };
  E.SLOT = () => [P.scale.x + 58, P.scale.y - 44];      // where a printed ticket leaves the scale (world)

  // draught streaks: schematic wind lines from the window towards the scale (o.k 0..1)
  E.props.draught = (t, o = {}) => {
    const k = E.clamp(o.k || 0); if (k <= 0) return '';
    const w = P.window; let s = '';
    for (let i = 0; i < 7; i++) {
      const r = E.rng(E.hash('wind' + i)), y = w.y - 50 + r() * 140, ph = (t * (0.55 + r() * 0.25) + r()) % 1;
      const xa = E.lerp(w.x - 70, P.scale.x + 40, ph), len = 70 + r() * 50, wob = Math.sin(t * 3 + i) * 6;
      s += E.path(`M${xa},${y} q${-len / 2},${-12 + wob} ${-len},0`, { stroke: C.schematic, sw: 2, opacity: k * Math.sin(ph * Math.PI) });
      s += E.path(`M${xa - len + 8},${y - 6} L${xa - len},${y} L${xa - len + 8},${y + 5}`, { stroke: C.schematic, sw: 2, opacity: k * Math.sin(ph * Math.PI) });
    }
    return s;
  };

  // ---------- L3: foreground clutter ----------
  const fore = (t) => {
    let s = E.R('rectangle', [120, 470, 240, 26], { fill: C.wood, sw: 1.8, roughness: 0.7 }, 'pin', t) + E.R('rectangle', [92, 476, 30, 14], { fill: C.woodDark, sw: 1.4 }, 'pinA', t) + E.R('rectangle', [358, 476, 30, 14], { fill: C.woodDark, sw: 1.4 }, 'pinB', t);
    s += E.R('path', ['M1560,520 L1570,440 L1650,440 L1660,520 Z'], { fill: '#C98A4B', sw: 1.8, roughness: 0.8 }, 'pot', t);
    for (let i = 0; i < 5; i++) s += E.R('path', [`M1610,442 q${-40 + i * 20},-50 ${-30 + i * 15},-${70 + (i % 2) * 20}`], { stroke: C.pistachio, sw: 4, roughness: 1 }, 'leaf' + i, t);
    return s;
  };

  // full set, layered for parallax. cam: {x, y, z}. o: {scale (options), window (options), draught (k), board (inner svg;
  //   default: the demo chart), boardShared (false hides the shared-wobble points on the board),
  //   extraWall (svg drawn on the wall, under the puppet), puppet (svg: drawn behind the bench front), extraL2 (svg on top)}
  E.comp.Bench = (t, cam, o = {}) => {
    const par = f => `translate(${((cam.x - 900) * (1 - f)).toFixed(2)},0)`;
    const L0 = wall(t);
    let L1 = shelf(t, 280, 660, 112, 'sh1') + jars(t, 296, 650, 112, 7);
    let L2 = shaft(t);
    L2 += E.props.clock(t) + E.props.window(t, cam, o.window || {}) + E.props.board(t, { inner: o.board ?? (E.chartPlot ? E.chartPlot(t, { shared: o.boardShared }) : '') });
    L2 += E.comp.Legend(t, { x: P.legend.x, y: P.legend.y, s: 1.05 });
    L2 += E.props.rail(t);
    if (o.extraWall) L2 += o.extraWall;
    if (o.puppet) L2 += o.puppet;
    // bench: top plank and the front with drawers
    L2 += E.R('rectangle', [-200, P.benchTop + 4, 2300, 220], { fill: '#B07A4C', sw: 2.2, roughness: 0.6 }, 'benchF', t);
    for (const dx of [140, 520, 980, 1380]) L2 += E.R('rectangle', [dx, P.benchTop + 40, 220, 70], { stroke: C.woodDark, sw: 1.6, roughness: 0.7 }, 'drw' + dx, t) + E.circle(dx + 110, P.benchTop + 75, 5, { fill: C.woodDark });
    L2 += E.R('rectangle', [-220, P.benchTop - 8, 2340, 14], { fill: '#8E5E37', sw: 2, roughness: 0.5 }, 'benchT', t);
    L2 += E.props.scale(t, o.scale || {});
    L2 += E.props.draught(t, { k: o.draught || 0 });
    if (o.extraL2) L2 += o.extraL2;
    return E.g(par(0.3), L0) + E.g(par(0.6), L1) + L2 + E.g(par(1.3), fore(t));
  };
})();

// ---------- the demo's chart: error of the average vs n (real numbers from data/readings.py) ----------
// One definition for every place it appears (the wall board, the frame shot, the screen panel), so the points appear
// at the same narration cues everywhere. o: {x, y, w, h, s, size, shared (bool: draw the shared-wobble trace), dimInd
// (opacity of the independent trace), title}
(() => {
  const T = f => { try { return f(); } catch (e) { return Infinity; } };   // cue of a beat that may not exist in a preview
  E.chartTimes = () => ({
    ind: [T(() => E.B('A2').start - 0.35), T(() => E.cue('A2', 'Four', 0.25)), T(() => E.cue('A2', 'sixteen', 0.2)), T(() => E.cue('A2', '0.06', 0.45))],
    theory: T(() => E.cue('A3', 'one over')),
    sh: [T(() => E.cue('C2', 'Then', 0.1)), T(() => E.cue('C2', 'stalls', -0.1)), T(() => E.cue('C2', 'even', 0.1)), T(() => E.cue('C2', 'sixty', 0.2))],
    floor: T(() => E.cue('C2', 'near', -0.2)),
  });
  E.chartPlot = (t, o = {}) => {
    const ct = E.chartTimes(), f3 = v => E.num(v, 3);
    const traces = [{ key: 'readings.independent', color: E.C.teal, appear: ct.ind, fmt: f3, labelDx: [26, 22, 22, -4], labelDy: [-12, -14, -14, -18], dim: o.dimInd ?? 1 }];
    if (o.shared !== false) traces.push({ key: 'readings.shared', color: E.C.steel, appear: ct.sh, fmt: (v, i) => i ? f3(v) : '',   // n = 1: same as above
      labelDx: [26, 0, 0, -4], labelDy: [-12, -16, -16, -18] });
    return E.comp.Plot(t, {
      x: o.x ?? 36, y: o.y ?? 36, w: o.w ?? 782, h: o.h ?? 374, s: o.s, size: o.size ?? 16, opacity: o.opacity,
      xs: 'readings.ns', xlog: true, ymax: 0.3, yticks: [0, 0.1, 0.2, 0.3], ydec: 1, title: o.title ?? 'Error of the average of n readings (kg, RMSE)',
      xlabel: 'readings averaged (n)', traces,
      guides: [{ key: 'readings.theory', color: E.C.schematic, t0: ct.theory, label: 'σ / √n' }],
      hlines: o.shared !== false ? [{ key: 'readings.shared_floor', color: E.C.steel, t0: ct.floor, labelDy: 18, label: `floor σ·√0.5 = ${E.num(E.D('readings.shared_floor'), 3)}` }] : [],
      footer: `data/readings.py · seed ${E.D('readings.seed')} · ${E.D('readings.sessions').toLocaleString('en-US')} sessions per n`,
    });
  };
})();

// ---------- frame shots: the camera zooms through a 16:9 frame (default E.POS.frame) until it is the screen ----------
(() => {
  const F = r => r || E.POS.frame;
  E.FRAME_Z = r => E.W / F(r).w;
  // camera between `from` (a world cam) and the full-frame cam; p 0..1 (eased by the caller). Zoom moves in log space
  E.frameCam = (from, p, r) => {
    const w = F(r), zf = E.FRAME_Z(r);
    const z = Math.exp(E.lerp(Math.log(from.z), Math.log(zf), p));
    const q = (z - from.z) / (zf - from.z || 1);   // the frame centre reaches the screen centre in step with the zoom
    return { x: E.lerp(from.x, w.x, q), y: E.lerp(from.y, w.y, q), z };
  };
  // standard in/out: returns {cam, k, p}; k is the frame-overlay opacity (1 = fully inside the frame)
  E.frameShot = (t, from, tIn, tOut, to, dIn = 1.1, dOut = 1.4, r) => {
    const pin = E.at(t, tIn, dIn, E.ease.inOut), pout = E.at(t, tOut, dOut, E.ease.inOut);
    if (t < tOut) { const cam = E.frameCam(from, pin, r); return { cam, k: E.clamp((pin - 0.82) / 0.16), p: pin }; }
    const cam = E.frameCam(to || from, 1 - pout, r);
    return { cam, k: E.clamp(1 - pout / 0.18), p: 1 - pout };
  };
  // saffron outline on the frame itself while zooming (world coords)
  E.frameGlow = (t, k, r) => {
    if (k <= 0) return '';
    const w = F(r);
    return E.rect(w.x - w.w / 2 - 2, w.y - w.h / 2 - 2, w.w + 4, w.h + 4, { stroke: E.C.saffron, sw: 3.5, opacity: k, r: 2 }) +
      E.rect(w.x - w.w / 2 - 7, w.y - w.h / 2 - 7, w.w + 14, w.h + 14, { stroke: E.C.saffron, sw: 6, opacity: 0.25 * k, r: 4 });
  };
  // the inside of a frame shot: warm paper filling the screen (screen coords) + the caller's content
  E.frameInside = (t, k, inner) => k <= 0 ? '' : E.g('', E.rect(0, 0, E.W, E.H, { fill: '#FBF4E4' }), { opacity: E.clamp(k * 2.4) }) + E.g('', inner, { opacity: E.clamp((k - 0.35) / 0.65) });
})();
