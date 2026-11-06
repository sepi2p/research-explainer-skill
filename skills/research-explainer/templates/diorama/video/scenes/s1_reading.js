// Scene 1 · One reading. W1: the bag drops on the scale; the true weight is marked; the needle never sits on it.
// W2: the scale prints five real readings onto tickets that hang on the rail; the noise setting appears on graph paper.
// This is the reference scene: it shows the scene contract, beat cues, the camera, the puppet and graph-paper data.
(() => {
  const { C } = E, P = E.POS;
  const W1 = E.B('W1'), W2 = E.B('W2');
  const tDrop = 0.35, tTrue = E.cue('W1', 'two kilos'), tAgree = E.cue('W1', 'never');
  const tQuarter = E.cue('W2', 'quarter', -0.2);
  const N = 5;                                                   // tickets printed in this scene
  const tPrint = i => i === 0 ? tAgree : W2.start + 0.15 + (i - 1) * 0.62;
  const R = i => E.D(`readings.session.readings.${i}`);          // real readings (data/readings.py, seed 0)

  // needle: settles on the newest reading with a springy wobble (on twos, like the puppet)
  const needle = (t) => {
    const tt = E.twos(t);
    let v = 0, from = 0, t0 = tDrop + 0.15;
    const targets = [[tDrop + 0.15, R(0)]];
    for (let i = 1; i < N; i++) targets.push([tPrint(i) - 0.12, R(i)]);
    for (const [ti, vi] of targets) if (tt >= ti) { from = v || 0; v = vi; t0 = ti; }
    if (tt < tDrop + 0.15) return 0;
    const k = E.spring(tt - t0, 140, 9);                      // under-damped: the wobble
    return E.lerp(from, v, k) + 0.02 * Math.sin(t * 9.0);     // a tiny constant tremble
  };
  // one ticket at time t: slides out of the slot, flies to its peg, then sways on the rail
  E.props.s1_ticketAt = (t, i, tp) => {
    if (t < tp) return '';
    const [sx, sy] = E.SLOT(), [px, py] = E.railXY(i);
    const out = E.at(t, tp, 0.22), fly = E.at(t, tp + 0.22, 0.55, E.ease.inOut);
    if (fly <= 0) return E.props.ticket(t, i, sx + 4 + 26 * out, sy - 13, 0);
    const x = E.lerp(sx + 30, px, fly), y = E.lerp(sy - 13, py, fly) - Math.sin(fly * Math.PI) * 40;
    const sway = fly >= 1 ? 6 * Math.exp(-(t - tp - 0.77) * 2.2) * Math.sin((t - tp - 0.77) * 9) : (1 - fly) * -10;
    return E.props.ticket(t, i, x, y, sway) + (fly >= 1 ? E.props.peg(px, py) : '');
  };

  E.scenes.s1_reading = t => {
    const tc = W2.start - 0.35;
    const cam = { x: E.etrack(t, [[0, 722], [tc, 860, 1.5]]), y: E.etrack(t, [[0, 248], [tc, 236, 1.5]]), z: E.etrack(t, [[0, 1.6], [tc, 1.18, 1.5]]) };
    const pip = E.comp.Pip(t, {
      x: P.pip.x, y: P.pip.y, poseKeys: [[0, 'rest'], [tTrue - 0.2, 'pointR'], [tAgree + 0.3, 'rest'], [W2.start + 0.8, 'think']],
      exprKeys: [[0, 'neutral'], [tDrop + 0.2, 'focused'], [tAgree, 'puzzled'], [tQuarter, 'focused']],
      look: t < tAgree + 0.6 ? [1, -0.4] : [1, -0.9], hop: tDrop + 0.18,
    });
    let wall = '';
    // the rail label and the printed tickets
    wall += E.text(P.rail.x0 - 22, P.rail.y - 22, 'readings (kg)', { size: 12, weight: 700, anchor: 'start', fill: C.schematic, opacity: E.fadeIn(t, tAgree, 0.4) });
    for (let i = 0; i < N; i++) wall += E.props.s1_ticketAt(t, i, tPrint(i));
    // the noise setting of the experiment (graph paper: it is read from the data)
    const qk = E.sp(t, tQuarter, 'play');
    if (t > tQuarter) wall += E.g(E.tf(960, 266, qk), E.comp.Slip(t, { x: -72, y: -15, w: 144, h: 30, key: 'readings.sigma', fmt: v => `noise <b>σ = ${E.num(v, 2)} kg</b>`, size: 14, stamp: false, align: 'center', pad: 3, id: 'sig' }));
    const bagY = t < tDrop ? -170 : -170 * (1 - E.sp(t, tDrop, [260, 16]));
    const world = E.comp.Bench(t, cam, {
      puppet: pip, extraWall: wall,
      scale: { value: needle(t), bag: E.fadeIn(t, tDrop - 0.15, 0.1), bagY, trueMark: E.fadeIn(t, tTrue, 0.3), slotGlow: Math.max(...Array.from({ length: N }, (_, i) => E.win(t, tPrint(i) - 0.1, tPrint(i) + 0.3, 0.1))) },
    });
    let screen = '';
    // on "two kilos": the true weight, said once in plain words on torn paper (an illustration, not a measurement)
    const tk = E.win(t, tTrue - 0.1, tAgree + 1.6, 0.3);
    if (tk > 0) screen += E.comp.Torn(t, { x: 300, y: 56, w: 178, h: 48, id: 'truth', html: `true weight: <b>${E.num(E.D('readings.true'))} kg</b>`, size: 17, opacity: tk, rot: -2 });
    // honesty stamp for the first seconds: the bench is invented, the numbers are computed (data/readings.py)
    screen += E.g(E.tf(14, 14), E.rect(0, 0, 226, 26, { fill: C.paper, stroke: C.brick, sw: 1.4, r: 5 }) + E.text(113, 14, E.L.made, { size: 13, weight: 700, fill: C.brick }), { opacity: E.win(t, 0.5, 4.2, 0.4) });
    return { cam, world, screen, hud: { ladder: E.fadeIn(t, W1.end - 0.5, 0.6) } };
  };
})();
