// Scene 2 · Average. A1: the scale prints readings 6..64 into a basket; a graph-paper counter shows n and the real
// running average; a saffron pointer on the dial settles near 2 kg. A2: frame shot into the chart board: the measured
// error at n = 1, 4, 16, 64 appears on the cues. A3: the theory curve σ/√n; pull back; the reveal names it (standard
// error) and the card flies to the ladder.
(() => {
  const { C } = E, P = E.POS;
  const A1 = E.B('A1'), A2 = E.B('A2'), A3 = E.B('A3');
  const tStream = A1.start + 0.5, tAvg = E.cue('A1', 'averages', -0.2);
  const tj = j => tStream + 2.3 * Math.pow((j - 5) / 58, 0.62);          // reading j (0-based) prints; 5..63 here
  const nAt = t => { if (t < tStream) return 5; let n = 5; for (let j = 5; j < 64; j++) if (t >= tj(j)) n = j + 1; return n; };
  const tDone = tj(63);
  const CAM0 = { x: 790, y: 238, z: 1.3 }, WIDE = { x: 1200, y: 228, z: 0.95 };
  const tIn = A2.start - 1.6, tOut = E.cue('A3', 'root n', 0.55);
  const tStamp = E.cue('A3', 'standard'), tSticky = tStamp - 2.4;
  const BASKET = { x: 952, y: P.benchTop };
  const R = j => E.D(`readings.session.readings.${j}`);

  E.props.s2_basket = (t, n) => {
    let s = '';
    const fill = E.clamp((n - 5) / 59);
    for (let i = 0; i < Math.round(fill * 22); i++) {        // the pile: blank ticket shapes (no text, so not data)
      const r = E.rng(E.hash('pile' + i)), x = (r() - 0.5) * 70, y = -18 - i * 1.1 - r() * 6;
      s += E.g(E.tf(BASKET.x + x, BASKET.y + y, 1, (r() - 0.5) * 50), E.rect(-10, -5, 20, 10, { fill: C.graph, stroke: C.ink, sw: 0.8 }));
    }
    s += E.R('path', [`M${BASKET.x - 50},${BASKET.y - 30} L${BASKET.x + 50},${BASKET.y - 30} L${BASKET.x + 40},${BASKET.y - 2} L${BASKET.x - 40},${BASKET.y - 2} Z`], { fill: C.wood, sw: 1.8, roughness: 0.8 }, 'bask', t);
    for (let i = -3; i <= 3; i++) s += E.R('line', [BASKET.x + i * 13, BASKET.y - 28, BASKET.x + i * 11, BASKET.y - 4], { stroke: C.woodDark, sw: 1.2 }, 'bsk' + i, t);
    return s;
  };

  E.scenes.s2_average = t => {
    // ---- camera: close on the scale, then a frame shot into the chart board, then the pull-back for the reveal ----
    let cam = { ...CAM0 }, k = 0;
    if (t >= tIn) { const fs = E.frameShot(t, CAM0, tIn, tOut, WIDE, 1.2, 1.3); cam = fs.cam; k = fs.k; }
    const n = nAt(t);
    // needle: the newest reading; once the stream ends it rests on the last one
    const j = n - 1, tj0 = j >= 5 ? tj(j) : -9, prev = j > 0 ? R(j - 1) : R(0);
    const needle = E.lerp(prev, R(j), E.spring(E.twos(t) - tj0, 300, 14)) + 0.02 * Math.sin(t * 9);
    const avgK = E.fadeIn(t, tAvg, 0.3);
    const runMean = E.D('readings.session.running_mean')[n - 1];
    const pip = E.comp.Pip(t, {
      x: P.pip.x, y: P.pip.y,
      poseKeys: [[0, 'think'], [A1.start + 0.2, 'pointR'], [tStream + 0.6, 'write'], [tDone + 0.2, 'cheer'], [tDone + 1.3, 'rest']],
      exprKeys: [[0, 'focused'], [tDone + 0.1, 'happy']], look: [1, -0.5], hop: tDone + 0.15,
    });
    let wall = '';
    for (let i = 0; i < 5; i++) { const [px, py] = E.railXY(i); wall += E.props.ticket(t, i, px, py, 0) + E.props.peg(px, py); }
    let l2 = E.props.s2_basket(t, n);
    // the last few tickets in flight, slot -> basket
    for (let q = Math.max(5, n - 6); q < n; q++) {
      const f = E.at(t, tj(q), 0.45, E.ease.inOut); if (f >= 1) continue;
      const [sx, sy] = E.SLOT(), x = E.lerp(sx + 20, BASKET.x + ((q * 37) % 50) - 25, f), y = E.lerp(sy - 13, BASKET.y - 30, f) - Math.sin(f * Math.PI) * 50;
      l2 += E.g(E.tf(x, y, 1, f * 160 + q * 20), E.rect(-12, -6, 24, 12, { fill: C.graph, stroke: C.ink, sw: 0.9 }));
    }
    // counter: n and the real running average (graph paper: the value is read from the data)
    const ck = E.sp(t, tStream - 0.3, 'play');
    if (t > tStream - 0.3 && t < tIn + 1.3) wall += E.g(E.tf(745, 78, ck), E.comp.Slip(t, { x: -112, y: -18, w: 224, h: 36, opacity: E.fadeOut(t, tIn + 1.2, 0.4), key: 'readings.session.running_mean', id: 'cnt', stamp: false, align: 'center', pad: 3, size: 15,
      fmt: arr => `n = <b>${E.num(n)}</b> · average <b style="color:${t >= tAvg ? C.saffron : C.ink};filter:brightness(0.8)">${E.num(arr[n - 1], 2)} kg</b>` }));
    const world = E.comp.Bench(t, cam, {
      puppet: pip, extraWall: wall, extraL2: l2 + E.frameGlow(t, Math.min(E.at(t, tIn, 0.4), 1 - E.at(t, tOut + 1.0, 0.4))),
      scale: { value: needle, bag: 1, trueMark: 1, avg: runMean, avgK, slotGlow: E.win(t, tStream - 0.1, tDone + 0.2, 0.15) },
    });
    // ---- inside the frame: the chart, full size ----
    let screen = '';
    if (k > 0) screen += E.frameInside(t, k, E.chartPlot(t));
    // ---- the reveal: plain words first, then the name on the spoken word, then the card flies to its rung ----
    screen += E.comp.Reveal(t, {
      t0: tSticky, tStamp, sticky: { x: 610, y: 120, text: 'more readings, smaller error', w: 150, h: 92 },
      card: { title: 'Standard error', sub: 'σ / √n', cite: 'The typical error of an average of n independent readings, each with noise σ.' },
      cardXY: [500, 96], flyTo: [836, 296], tFly: tStamp + 1.75,
    });
    return { cam, world, screen, frame: { k }, hud: {} };
  };
})();
