// Cut-paper puppets and the bakery set, drawn with rough.js (MIT). Hand-drawn parts are cached per boil seed (8 per
// second, like the series); faces and the scale's display are crisp SVG so expressions and numbers read. Every function
// is pure: (seed, state) -> SVG string.
(function () {
  const G = rough.generator(), INK = "#1F2A44";
  const cache = new Map();
  const PS = window.PSTYLE || {};
  function P(dr) {
    return G.toPaths(dr).filter((p) => !(PS.noStroke && p.stroke !== "none")).map((p) => p.stroke === "none"
      ? '<path d="' + p.d + '" fill="' + p.fill + '"/>'
      : '<path d="' + p.d + '" fill="none" stroke="' + p.stroke + '" stroke-width="' + p.strokeWidth + '" stroke-linecap="round" stroke-linejoin="round"/>').join("");
  }
  const O = (sd, o) => Object.assign({ seed: sd, roughness: 1.1, bowing: 0.8, strokeWidth: 2, stroke: INK, curveFitting: 0.95, fillStyle: "solid" }, o || {}, PS.rough || {});
  function memo(key, s, fn) { const k = key + "|" + s; let v = cache.get(k); if (v === undefined) { v = fn(s); cache.set(k, v); } return v; }
  // k-th shape of a part gets its own seed, and every boil step re-seeds all of them
  const sd = (s, k) => 1 + s * 997 + k * 31;
  const path = (d, s, k, o) => P(G.path(d, O(sd(s, k), o)));
  const ell = (x, y, w, h, s, k, o) => P(G.ellipse(x, y, w, h, O(sd(s, k), o)));
  const rect = (x, y, w, h, s, k, o) => P(G.rectangle(x, y, w, h, O(sd(s, k), o)));
  const line = (x1, y1, x2, y2, s, k, o) => P(G.line(x1, y1, x2, y2, O(sd(s, k), o)));
  const circ = (x, y, d, s, k, o) => P(G.circle(x, y, d, O(sd(s, k), o)));
  const C = { paper: "#F3E9D2", ink: INK, brick: "#B5533C", saffron: "#E9A23B", teal: "#2A9D8F", steel: "#4F6FA8", wood: "#A87C52",
    woodDark: "#7A5434", cream: "#FBF3E2", wall: "#F2E6D3", tile: "#E3ECE6", tileLine: "#B9C7BE", floor: "#C98B62", block: "#D2A877", kraft: "#E8D3A9", skinA: "#B97A56", skinB: "#EDBE9C" };
  const TXT = (x, y, txt, font, fill, anchor) => '<text x="' + x + '" y="' + y + '"' + (anchor ? ' text-anchor="' + anchor + '"' : "") + ' style="font:' + font + '" fill="' + fill + '">' + txt + "</text>";

  // ---------------- the bakery kitchen (what the image model repaints: no people, no counter, no scale) ----------------
  function kitchenBack(s) {
    return memo("back", s, (s) => {
      let o = '<rect x="0" y="0" width="540" height="960" fill="' + C.wall + '"/>';
      // tiled splashback behind the counter
      o += rect(-10, 392, 560, 170, s, 1, { fill: C.tile, strokeWidth: 1.6 });
      for (let k = 1; k < 6; k++) o += line(-10, 392 + k * 28, 550, 392 + k * 28 + 2, s, 2 + k, { strokeWidth: 1, stroke: C.tileLine });
      for (let k = 0; k < 20; k++) o += line(14 + k * 28 + (k % 2) * 2, 392, 14 + k * 28, 560, s, 10 + k, { strokeWidth: 1, stroke: C.tileLine });
      // terracotta floor tiles
      o += rect(-10, 800, 560, 180, s, 40, { fill: C.floor, strokeWidth: 1.6 });
      for (let k = 0; k < 4; k++) o += line(-10, 836 + k * 40, 550, 838 + k * 40, s, 41 + k, { strokeWidth: 1.2, stroke: "#9A6142" });
      for (let k = 0; k < 9; k++) o += line(30 + k * 64, 800, 22 + k * 66, 960, s, 46 + k, { strokeWidth: 1.2, stroke: "#9A6142" });
      // window with sky, a cloud, curtains and a pot of herbs on the sill
      o += rect(334, 100, 162, 190, s, 60, { fill: "#CFE6F2", strokeWidth: 3 });
      o += ell(392, 150, 62, 26, s, 61, { fill: "#FFFFFF", strokeWidth: 1.4, stroke: "#9FB3C8" }) + ell(420, 143, 42, 22, s, 62, { fill: "#FFFFFF", strokeWidth: 1.4, stroke: "#9FB3C8" });
      o += path("M 334 250 L 372 236 L 404 246 L 440 230 L 496 244 L 496 290 L 334 290 Z", s, 63, { fill: "#B9D3B0", strokeWidth: 1.4 });   // hills
      o += line(415, 100, 415, 290, s, 64, { strokeWidth: 3 }) + line(334, 190, 496, 190, s, 65, { strokeWidth: 3 });
      o += line(316, 90, 514, 90, s, 66, { strokeWidth: 4, stroke: C.woodDark });
      o += path("M 318 92 C 330 150 336 230 346 300 L 324 300 C 318 230 314 150 318 92 Z", s, 67, { fill: C.saffron });
      o += path("M 512 92 C 500 150 494 230 486 300 L 508 300 C 514 230 518 150 512 92 Z", s, 68, { fill: C.saffron });
      o += rect(326, 290, 178, 12, s, 69, { fill: C.wood, strokeWidth: 2 });
      o += path("M 452 290 L 448 266 L 476 266 L 472 290 Z", s, 70, { fill: C.brick }) +
           path("M 462 266 C 456 248 444 244 438 236 C 452 238 462 250 463 264", s, 71, { fill: C.teal }) +
           path("M 462 266 C 466 246 478 240 486 234 C 482 250 472 258 464 266", s, 72, { fill: "#1D6B62" });
      // kitchen clock (hands drawn crisp, outside the cache)
      o += circ(266, 146, 56, s, 80, { fill: "#FFFFFF", strokeWidth: 2.6 });
      // two shelves: jars of flour and sugar, bowls, loaves
      o += rect(18, 212, 236, 10, s, 90, { fill: C.wood, strokeWidth: 2 }) + rect(18, 318, 236, 10, s, 91, { fill: C.wood, strokeWidth: 2 });
      o += path("M 40 222 L 52 240 M 232 222 L 220 240", s, 92, { strokeWidth: 3, stroke: C.woodDark }) + path("M 40 328 L 52 346 M 232 328 L 220 346", s, 93, { strokeWidth: 3, stroke: C.woodDark });
      o += rect(32, 160, 40, 52, s, 94, { fill: "#E9F1F0", strokeWidth: 1.8 }) + rect(34, 182, 36, 28, s, 95, { fill: "#FBF6EC", strokeWidth: 1 }) + rect(30, 152, 44, 10, s, 96, { fill: C.woodDark, strokeWidth: 1.6 });
      o += rect(82, 170, 36, 42, s, 97, { fill: "#E9F1F0", strokeWidth: 1.8 }) + rect(84, 186, 32, 24, s, 98, { fill: "#F2E2C2", strokeWidth: 1 }) + rect(80, 162, 40, 10, s, 99, { fill: C.woodDark, strokeWidth: 1.6 });
      o += path("M 132 186 L 196 186 C 194 204 184 212 164 212 C 144 212 134 204 132 186 Z", s, 100, { fill: "#8FAFC9" }) +
           path("M 138 176 L 190 176 C 188 188 180 192 164 192 C 148 192 140 188 138 176 Z", s, 101, { fill: "#B8CFE0" });
      o += ell(222, 196, 46, 28, s, 102, { fill: "#C98A4B" }) + path("M 210 190 L 216 200 M 222 186 L 228 198 M 234 190 L 238 198", s, 103, { strokeWidth: 1.4, stroke: C.woodDark });
      o += ell(52, 302, 58, 32, s, 104, { fill: "#C98A4B" }) + ell(108, 304, 52, 28, s, 105, { fill: "#B97A3E" }) + path("M 40 296 L 48 306 M 54 292 L 62 304 M 98 298 L 106 308", s, 106, { strokeWidth: 1.4, stroke: C.woodDark });
      o += rect(150, 280, 92, 38, s, 107, { fill: "#D9B98A", strokeWidth: 1.8 }) + path("M 158 280 C 170 262 222 262 234 280", s, 108, { fill: "none", strokeWidth: 2.2, stroke: C.woodDark });
      return o;
    });
  }
  function clockHands(t) {
    const m = (t * 6) % 360, h = 250 + t * 0.5;
    const hx = (a, r) => 266 + r * Math.sin(a * Math.PI / 180), hy = (a, r) => 146 - r * Math.cos(a * Math.PI / 180);
    return '<path d="M 266 146 L ' + hx(h, 13) + " " + hy(h, 13) + " M 266 146 L " + hx(m, 20) + " " + hy(m, 20) + '" stroke="' + INK + '" stroke-width="2.6" stroke-linecap="round"/><circle cx="266" cy="146" r="2.5" fill="' + INK + '"/>';
  }
  // the counter in front of the people, with a rolling pin and a mixing bowl
  function kitchenFront(s) {
    return memo("front", s, (s) => {
      let o = rect(-10, 552, 560, 18, s, 1, { fill: C.block, strokeWidth: 2.4 });
      o += rect(-6, 570, 552, 240, s, 2, { fill: C.wood, strokeWidth: 2.4 });
      for (let k = 0; k < 3; k++) o += rect(16 + k * 176, 596, 156, 186, s, 3 + k, { fill: "#B88A5E", strokeWidth: 1.8 }) + circ(94 + k * 176, 616, 10, s, 6 + k, { fill: C.woodDark, strokeWidth: 1.4 });
      o += path("M 352 538 L 470 538 L 470 550 L 352 550 Z", s, 10, { fill: "#D9B98A" }) + line(338, 544, 352, 544, s, 11, { strokeWidth: 5, stroke: C.woodDark }) + line(470, 544, 486, 544, s, 12, { strokeWidth: 5, stroke: C.woodDark });
      o += path("M 486 514 L 540 514 C 538 538 528 552 513 552 C 498 552 488 538 486 514 Z", s, 13, { fill: "#8FAFC9" });
      return o;
    });
  }
  // a kitchen scale (origin: the middle of its foot on the counter) and its crisp display
  function scale(s) {
    return memo("scale", s, (s) => rect(-60, -52, 120, 52, s, 1, { fill: "#6F8FB4", strokeWidth: 2.2 }) + rect(-12, -58, 24, 8, s, 2, { fill: "#4F5D75", strokeWidth: 1.6 }) +
      rect(-58, -64, 116, 9, s, 3, { fill: "#D3D8DF", strokeWidth: 2 }));
  }
  function scaleDisplay(txt, settled) {
    return '<rect x="-44" y="-42" width="88" height="30" rx="4" fill="#26312B"/>' +
      TXT(28, -20, txt, "700 19px 'JetBrains Mono', monospace", settled ? "#C6F2CF" : "#7FA58A", "end") + TXT(38, -20, "g", "700 12px 'JetBrains Mono', monospace", "#C6F2CF", "middle");
  }
  // a paper bag of flour (origin: the middle of its bottom); the label is crisp
  function bag(s) {
    return memo("bag", s, (s) => path("M -36 0 L -38 -80 L -31 -94 L 31 -94 L 38 -80 L 36 0 Z", s, 1, { fill: C.kraft }) +
      path("M -31 -94 L -26 -104 L 26 -104 L 31 -94 Z", s, 2, { fill: "#D6B987" }) + line(-36, -80, 36, -80, s, 3, { strokeWidth: 1.3 })) +
      '<rect x="-26" y="-66" width="52" height="40" rx="5" fill="#FFFBF2" stroke="#5B4E46" stroke-width="1.2"/>' +
      TXT(0, -48, "FLOUR", "900 13px Inter, sans-serif", "#9C4130", "middle") + TXT(0, -33, "500 g", "700 11px 'JetBrains Mono', monospace", INK, "middle");
  }

  // ---------------- faces (crisp) ----------------
  function eyes(st, y, dx, r, gap) {
    const ex = st.lookX || 0, ey = y + (st.lookY || 0), rr = r + 1.5 * (st.wide || 0);
    if (st.happy) return '<path d="M ' + (-gap - 5) + " " + (y + 1) + " Q " + (-gap) + " " + (y - 5) + " " + (-gap + 5) + " " + (y + 1) + " M " + (gap - 5) + " " + (y + 1) + " Q " + gap + " " + (y - 5) + " " + (gap + 5) + " " + (y + 1) +
      '" fill="none" stroke="' + INK + '" stroke-width="2.6" stroke-linecap="round"/>';
    if (st.blink) return '<path d="M ' + (-gap - 4) + " " + y + " L " + (-gap + 4) + " " + y + " M " + (gap - 4) + " " + y + " L " + (gap + 4) + " " + y + '" stroke="' + INK + '" stroke-width="2.4" stroke-linecap="round"/>';
    return '<circle cx="' + (-gap + ex) + '" cy="' + ey + '" r="' + rr + '" fill="' + INK + '"/><circle cx="' + (gap + ex) + '" cy="' + ey + '" r="' + rr + '" fill="' + INK + '"/>' +
      '<circle cx="' + (-gap + ex + 1) + '" cy="' + (ey - 1.2) + '" r="1" fill="#FFFFFF"/><circle cx="' + (gap + ex + 1) + '" cy="' + (ey - 1.2) + '" r="1" fill="#FFFFFF"/>';
  }
  function brows(st, y, gap, w, col) {
    const b = -(st.brow || 0) - 6 * (st.wide || 0), tilt = st.worry ? 3 : 0;
    return '<path d="M ' + (-gap - w) + " " + (y + b + tilt) + " Q " + (-gap) + " " + (y + b - 5) + " " + (-gap + w) + " " + (y + b - tilt) +
      " M " + (gap - w) + " " + (y + b - tilt) + " Q " + gap + " " + (y + b - 5) + " " + (gap + w) + " " + (y + b + tilt) + '" fill="none" stroke="' + (col || INK) + '" stroke-width="2.8" stroke-linecap="round"/>';
  }
  function mouth(st, y, lip) {
    const m = st.mouth || 0;
    if ((st.laugh || 0) > 0.5) return '<path d="M -10 ' + (y - 1) + " Q 0 " + (y + 13) + " 10 " + (y - 1) + ' Z" fill="#6B2E2E" stroke="' + INK + '" stroke-width="2" stroke-linejoin="round"/>';
    if ((st.oh || 0) > 0.5) return '<ellipse cx="0" cy="' + (y + 3) + '" rx="6" ry="8" fill="#6B2E2E" stroke="' + INK + '" stroke-width="2"/>';
    if (m > 0.08) return '<ellipse cx="0" cy="' + (y + 1) + '" rx="' + (6 + 1.5 * m) + '" ry="' + (1.2 + 5 * m) + '" fill="#6B2E2E" stroke="' + INK + '" stroke-width="2"/>';
    const sm = st.smile || 0;
    return '<path d="M -8 ' + y + " Q 0 " + (y + 3 + 4 * sm) + " 8 " + y + '" fill="none" stroke="' + (lip || INK) + '" stroke-width="2.4" stroke-linecap="round"/>';
  }

  // ---------------- arms: two-link reach (shoulder -> elbow -> hand at a target), drawn from cached parts ----------------
  function reach(sx, sy, tx, ty, a, b, bend) {
    const dx = tx - sx, dy = ty - sy, d = Math.max(Math.abs(a - b) + 1, Math.min(a + b - 0.5, Math.hypot(dx, dy)));
    const th = Math.atan2(dy, dx), al = Math.acos(Math.max(-1, Math.min(1, (a * a + d * d - b * b) / (2 * a * d))));
    const up = th + bend * al, ex = sx + a * Math.cos(up), ey = sy + a * Math.sin(up);
    return { up: up * 180 / Math.PI, fo: Math.atan2(ty - ey, tx - ex) * 180 / Math.PI, ex, ey };
  }
  function arm(s, key, sx, sy, tx, ty, o) {
    // o: { a: upper arm, b: forearm (to the hand's centre), bend: +1/-1 (which way the elbow points), sleeve, fore, skin, hand: svg drawn upright at the hand }
    const k = reach(sx, sy, tx, ty, o.a, o.b, o.bend);
    const up = memo("up-" + key, s, (s) => path("M 0 -12 L " + o.a + " -10 L " + o.a + " 10 L 0 12 Z", s, 1, { fill: o.sleeve }));
    const fo = memo("fo-" + key, s, (s) => path("M -6 -9 L " + (o.b - 6) + " -7 L " + (o.b - 6) + " 7 L -6 9 Z", s, 2, { fill: o.fore || o.sleeve }) + circ(o.b, 0, 18, s, 3, { fill: o.skin }));
    return '<g transform="translate(' + sx + " " + sy + ") rotate(" + k.up + ')">' + up + '</g><g transform="translate(' + k.ex + " " + k.ey + ") rotate(" + k.fo + ')">' + fo +
      (o.hand ? '<g transform="translate(' + o.b + " 0) rotate(" + (-k.fo) + ')">' + o.hand + "</g>" : "") + "</g>";
  }

  // ---------------- the apprentice (origin: neck base) ----------------
  // a young baker: curly hair under a red kerchief, freckles, a blue shirt with rolled sleeves, a cream apron with a pencil
  const SKIN_A = C.skinA, HAIR_A = "#2B1D16", SHIRT_A = "#5B7DB1", APRON = "#F4EBDD";
  function apprentice(s, st) {
    // curly hair: a ring of curls behind the head, so a bumpy dark edge shows round the face and under the kerchief
    const back = memo("app-back", s, (s) => [[-36, -40], [-41, -56], [-38, -73], [-26, -87], [-9, -95], [9, -95], [26, -87], [38, -73], [41, -56], [36, -40]]
      .map(([x, y], k) => circ(x, y, 26, s, 1 + k, { fill: HAIR_A })).join(""));
    const body = memo("app-body", s, (s) =>
      path("M -54 14 C -48 0 -28 -4 -12 -2 L 12 -2 C 28 -4 48 0 54 14 L 60 150 L -60 150 Z", s, 1, { fill: SHIRT_A }) +
      rect(-10, -16, 20, 18, s, 2, { fill: SKIN_A }) + path("M -14 -2 L 0 18 L 14 -2 Z", s, 3, { fill: SKIN_A }) +
      path("M -32 34 L 32 34 L 38 150 L -38 150 Z", s, 4, { fill: APRON }) + line(-30, 34, -14, 0, s, 5, { strokeWidth: 2.4 }) + line(30, 34, 14, 0, s, 6, { strokeWidth: 2.4 }) +
      rect(-15, 78, 30, 24, s, 7, { fill: "#EADFCB", strokeWidth: 1.6 }) + line(-6, 80, -2, 62, s, 8, { strokeWidth: 3.4, stroke: C.saffron }));
    const head = memo("app-head", s, (s) => ell(-32, -52, 11, 17, s, 1, { fill: SKIN_A }) + ell(32, -52, 11, 17, s, 2, { fill: SKIN_A }) + ell(0, -54, 64, 74, s, 3, { fill: SKIN_A }) +
      path("M -34 -70 C -30 -104 30 -104 34 -70 C 20 -80 -20 -80 -34 -70 Z", s, 8, { fill: C.brick }) +
      path("M 30 -78 L 50 -90 L 46 -72 Z", s, 9, { fill: C.brick }) + path("M 30 -76 L 52 -70 L 40 -62 Z", s, 10, { fill: "#9C4130" }));
    const dots = '<g fill="#FFFBF2"><circle cx="-14" cy="-88" r="1.8"/><circle cx="4" cy="-91" r="1.8"/><circle cx="20" cy="-86" r="1.8"/><circle cx="-24" cy="-79" r="1.6"/></g>';
    const freck = '<g fill="#7A4A30"><circle cx="-20" cy="-42" r="1.3"/><circle cx="-15" cy="-39" r="1.3"/><circle cx="-23" cy="-37" r="1.3"/><circle cx="20" cy="-42" r="1.3"/><circle cx="15" cy="-39" r="1.3"/><circle cx="23" cy="-37" r="1.3"/></g>';
    const face = eyes(st, -54, 0, 3, 12) + brows(st, -67, 12, 8) + freck +
      '<path d="M 1 -49 Q -4 -42 2 -40" fill="none" stroke="' + INK + '" stroke-width="1.8" stroke-linecap="round"/>' + mouth(st, -31, "#7A2E2E");
    const opt = { a: 66, b: 60, sleeve: SHIRT_A, fore: SKIN_A, skin: SKIN_A };
    const R = st.handR || [70, 136], L = st.handL || [-44, 136];
    const right = arm(s, "appR", 48, 12, R[0], R[1], Object.assign({ bend: 1 }, opt));
    const left = arm(s, "appL", -48, 12, L[0], L[1], Object.assign({ bend: -1 }, opt));
    return "<g>" + back + body + '<g transform="rotate(' + (st.head || 0) + ' 0 -10)">' + head + dots + face + "</g>" + right + left + "</g>";
  }

  // ---------------- the baker (origin: neck base) ----------------
  // an older baker: tall white hat, grey moustache, rosy cheeks, a saffron shirt, a red neckerchief, a floury white apron
  const SKIN_B = C.skinB, SHIRT_B = "#D9913A", GREY = "#9A948D";
  function baker(s, st) {
    const body = memo("bak-body", s, (s) =>
      path("M -76 16 C -68 0 -40 -4 -20 -2 L 20 -2 C 40 -4 68 0 76 16 L 86 160 L -86 160 Z", s, 1, { fill: SHIRT_B }) +
      rect(-12, -18, 24, 20, s, 2, { fill: SKIN_B }) + path("M -22 -2 L 0 26 L 22 -2 Z", s, 3, { fill: C.brick }) +
      path("M -40 36 L 40 36 L 46 160 L -46 160 Z", s, 4, { fill: "#FBF6EC" }) + line(-38, 36, -20, 2, s, 5, { strokeWidth: 2.4 }) + line(38, 36, 20, 2, s, 6, { strokeWidth: 2.4 }) +
      circ(-18, 96, 16, s, 7, { fill: "#E9E1D3", strokeWidth: 0.8 }) + circ(14, 118, 12, s, 8, { fill: "#E9E1D3", strokeWidth: 0.8 }));
    const head = memo("bak-head", s, (s) => ell(-33, -72, 18, 30, s, 4, { fill: GREY }) + ell(33, -72, 18, 30, s, 5, { fill: GREY }) +
      ell(-38, -56, 12, 18, s, 1, { fill: SKIN_B }) + ell(38, -56, 12, 18, s, 2, { fill: SKIN_B }) + ell(0, -58, 76, 84, s, 3, { fill: SKIN_B }) +
      rect(-36, -108, 72, 24, s, 6, { fill: "#FFFFFF", strokeWidth: 2 }) +
      path("M -38 -106 C -64 -118 -56 -166 -26 -154 C -22 -186 22 -186 26 -154 C 56 -166 64 -118 38 -106 Z", s, 7, { fill: "#FFFFFF" }));
    const cheeks = '<circle cx="-24" cy="-42" r="7" fill="#E58C7A" opacity="0.45"/><circle cx="24" cy="-42" r="7" fill="#E58C7A" opacity="0.45"/>';
    const mous = '<path d="M -26 -38 C -16 -47 -5 -43 0 -39 C 5 -43 16 -47 26 -38 C 18 -31 7 -33 0 -36 C -7 -33 -18 -31 -26 -38 Z" fill="' + GREY + '" stroke="' + INK + '" stroke-width="1.6"/>';
    const face = eyes(st, -62, 0, 3.2, 14) + brows(st, -76, 14, 10, "#6E6862") + cheeks +
      '<path d="M 2 -56 Q -6 -46 3 -43" fill="none" stroke="' + INK + '" stroke-width="2" stroke-linecap="round"/>' + mouth(st, -27) + mous;
    const finger = (st.point || 0) > 0.5 ? memo("bak-finger", s, (s) => rect(-4, -30, 8, 22, s, 1, { fill: SKIN_B, strokeWidth: 1.6 })) : "";
    const opt = { a: 74, b: 66, sleeve: SHIRT_B, fore: SKIN_B, skin: SKIN_B };
    const L = st.handL || [-64, 146], R = st.handR || [60, 146];
    const left = arm(s, "bakL", -70, 14, L[0], L[1], Object.assign({ bend: -1, hand: finger }, opt));
    const right = arm(s, "bakR", 70, 14, R[0], R[1], Object.assign({ bend: 1 }, opt));
    const bob = st.bob || 0;
    return "<g>" + body + '<g transform="translate(0 ' + bob + ") rotate(" + (st.head || 0) + ' 0 -10)">' + head + face + "</g>" + left + right + "</g>";
  }

  // ---------------- a window with curtains that a draught can blow (origin: the middle of the curtain rod) ----------------
  function windowPup(s, st) {
    const frame = memo("win", s, (s) => rect(-58, 8, 116, 132, s, 1, { fill: "#CFE6F2", strokeWidth: 3 }) + ell(-14, 46, 48, 20, s, 2, { fill: "#FFFFFF", strokeWidth: 1.2, stroke: "#9FB3C8" }) +
      line(0, 8, 0, 140, s, 3, { strokeWidth: 3 }) + line(-58, 74, 58, 74, s, 4, { strokeWidth: 3 }) + rect(-68, 138, 136, 10, s, 5, { fill: C.wood, strokeWidth: 2 }) +
      line(-76, 0, 76, 0, s, 6, { strokeWidth: 4, stroke: C.woodDark }));
    const curL = memo("win-cl", s, (s) => path("M -74 2 C -64 50 -60 100 -52 148 L -72 148 C -78 100 -80 50 -74 2 Z", s, 7, { fill: C.saffron }));
    const curR = memo("win-cr", s, (s) => path("M 74 2 C 64 50 60 100 52 148 L 72 148 C 78 100 80 50 74 2 Z", s, 8, { fill: C.saffron }));
    const b = st.blow || 0;   // 0 still, 1 blown inward (to the left of the screen)
    return "<g>" + frame + '<g transform="skewX(' + (-10 * b) + ')">' + curL + '</g><g transform="skewX(' + (-7 * b) + ')">' + curR + "</g></g>";
  }

  window.PUP = { C, kitchenBack, kitchenFront, clockHands, scale, scaleDisplay, bag, apprentice, baker, windowPup, memo, path, rect, line, ell, circ };
})();
