// Scene 3 · Shared wobble. C1: the window swings open; a draught pushes the needle and every hanging ticket the same
// way; torn paper splits each wobble into its own part and a shared push; the correlation setting on graph paper.
// C2: a graph-paper chart panel slides in: the shared-wobble error (real) stops falling at the floor; the "Average"
// rung cracks (main.js CRACKS).
(() => {
  const { C } = E, P = E.POS;
  const C1 = E.B('C1'), C2 = E.B('C2');
  const tOpen = C1.start + 0.15, tPush = E.cue('C1', 'pushes', -0.1), tSame = E.cue('C1', 'same way'), tShared = E.cue('C1', 'half', -0.1);
  const tPanel = C2.start - 0.45, tStall = E.cue('C2', 'stalls');

  E.scenes.s3_shared = t => {
    const cam = { x: E.etrack(t, [[0, 940], [C1.start + 0.4, 905, 3.5]]), y: 232, z: E.etrack(t, [[0, 0.9], [C1.start + 0.4, 0.98, 3.5]]) };
    const open = E.sp(t, tOpen, [90, 9]), wind = E.clamp(open);
    const push = E.at(t, tPush, 0.5);                     // the shared push (an illustration: torn-paper world, not data)
    const gust = push * (0.75 + 0.25 * E.noise1(t * 1.3, 'gust'));
    const pip = E.comp.Pip(t, {
      x: P.pip.x, y: P.pip.y, poseKeys: [[0, 'rest'], [tOpen + 0.3, 'pointR'], [tShared, 'think'], [tStall, 'shrug']],
      exprKeys: [[0, 'neutral'], [tOpen + 0.2, 'surprised'], [tShared, 'puzzled']], look: t < tShared ? [1, -0.8] : [1, -0.3],
    });
    let wall = '';
    for (let i = 0; i < 5; i++) {                         // every ticket leans the same way in the draught
      const [px, py] = E.railXY(i);
      wall += E.props.ticket(t, i, px, py, 16 * gust + 3 * Math.sin(t * 5 + i)) + E.props.peg(px, py);
    }
    const world = E.comp.Bench(t, cam, {
      puppet: pip, extraWall: wall, window: { open, wind }, draught: E.fadeIn(t, tOpen + 0.3, 0.6),
      scale: { value: 2 + 0.02 * Math.sin(t * 9), lean: 22 * gust, bag: 1, trueMark: 1 },
    });
    let screen = '';
    // torn paper: the idea in words (no numbers: numbers live on graph paper)
    const nk = E.sp(t, tShared, 'play');
    if (t > tShared) {
      screen += E.comp.Torn(t, { x: 16, y: 26, w: 244, h: 72, id: 'split', s: nk, rot: -1.5, size: 16,
        html: `each wobble = <b style="color:${C.teal}">its own part</b><br>+ <b style="color:${C.steel}">a shared push</b>` });
      const rk = E.sp(t, tShared + 0.5, 'play');
      if (t > tShared + 0.5) screen += E.g(E.tf(138, 124, rk), E.comp.Slip(t, { x: -86, y: -16, w: 172, h: 32, key: 'readings.rho', fmt: v => `correlation <b>${E.num(v, 1)}</b>`, size: 15, stamp: false, align: 'center', pad: 3, id: 'rho' }));
    }
    // the chart panel (graph paper; the same chart as the wall board)
    if (t > tPanel) {
      const a = E.sp(t, tPanel, 'obj');
      screen += E.chartPlot(t, { x: E.lerp(870, 272, a), y: 40, w: 474, h: 300, size: 14, dimInd: 0.45, title: 'Error of the average (kg, RMSE)' });
    }
    return { cam, world, screen, hud: {} };
  };
})();
