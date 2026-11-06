// Scene 4 · Takeaway. E1: the window closes; two torn-paper notes say what averaging removes and what it cannot;
// the camera settles on Pip and the two-paper legend; the locked top rung pulses (the next question).
(() => {
  const { C } = E, P = E.POS;
  const E1 = E.B('E1');
  const tOwn = E.cue('E1', 'own', -0.3), tShared = E.cue('E1', 'not the shared', -0.1);

  E.scenes.s4_takeaway = t => {
    const tc = E1.start + 1.2;
    const cam = { x: E.etrack(t, [[0, 760], [tc, 380, 2.4]]), y: E.etrack(t, [[0, 214], [tc, 222, 2.4]]), z: E.etrack(t, [[0, 0.74], [tc, 1.3, 2.4]]) };
    const shut = 1 - E.at(t, E1.start - 0.6, 0.5);
    const pip = E.comp.Pip(t, {
      x: P.pip.x, y: P.pip.y, poseKeys: [[0, 'rest'], [tOwn, 'cheer'], [tShared + 0.2, 'shrug'], [E1.end + 0.3, 'wave']],
      exprKeys: [[0, 'neutral'], [tOwn, 'happy'], [tShared + 0.2, 'focused'], [E1.end + 0.3, 'happy']], look: [-0.2, -0.4], hop: tOwn + 0.1,
    });
    let wall = '';
    for (let i = 0; i < 5; i++) { const [px, py] = E.railXY(i); wall += E.props.ticket(t, i, px, py, 2 * Math.sin(t * 2 + i) * shut) + E.props.peg(px, py); }
    const world = E.comp.Bench(t, cam, {
      puppet: pip, extraWall: wall, window: { open: shut, wind: shut }, draught: shut,
      scale: { value: E.D('readings.session.mean64'), avg: E.D('readings.session.mean64'), bag: 1, trueMark: 1 },
    });
    let screen = '';
    const note = (t0, x, col, html, id) => t < t0 ? '' : E.comp.Torn(t, { x, y: 24, w: 270, h: 58, id, s: E.sp(t, t0, 'play'), rot: id === 'own' ? -2 : 1.5, size: 17,
      html: `<span style="border-bottom:3px solid ${col}">${html}</span>` });
    screen += note(tOwn, 40, C.teal, 'own wobble: <b>averages away</b>', 'own');
    screen += note(tShared, 340, C.steel, 'shared push: <b>stays</b>', 'shr');
    return { cam, world, screen, hud: {} };
  };
})();
