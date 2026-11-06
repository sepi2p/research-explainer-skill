// The demo's puppet: Pip, a small cut-paper baker in a saffron jumper and a brick-red knitted hat with a pompom.
// Animated on twos (12 fps) with a seeded ±0.5° jitter, breathing and blinking; no walking and no hand contact.
// Copy this file's pattern for your own cast (cap: 3 animated characters). Origin = bottom centre of the torso, which
// usually sits hidden behind a counter or bench, so the puppet needs no legs.
(() => {
  const { C } = E;
  const D2R = Math.PI / 180;

  // arm angles in degrees, screen space (0 = pointing right, 90 = down): [upper, fore] for the screen-left (L) and
  // screen-right (R) arm
  const POSES = {
    rest: { L: [105, 80], R: [75, 100] },
    pointL: { L: [190, 185], R: [75, 100] },       // points to the screen left
    pointR: { L: [105, 80], R: [-8, -12] },        // points to the screen right
    pointUp: { L: [105, 80], R: [-50, -75] },
    think: { L: [105, 80], R: [115, -110] },       // hand at the chin
    cheer: { L: [-130, -110], R: [-50, -70] },
    shrug: { L: [150, 230], R: [30, -50] },
    hold: { L: [130, 30], R: [50, 150] },          // both hands forward, as if carrying
    write: { L: [120, 40], R: [60, 160] },
    wave: { L: [105, 80], R: [-25, -80] },
  };
  const EXPR = {
    neutral: { brow: 0, browY: 0, smile: 0.3, eye: 1 },
    happy: { brow: -6, browY: -2, smile: 1, eye: 0.75 },
    focused: { brow: 8, browY: 1, smile: 0, eye: 0.85 },
    puzzled: { brow: 12, browY: -1, smile: -0.4, eye: 1.1, browSplit: true },
    surprised: { brow: -10, browY: -4, smile: 0, eye: 1.25, mouthO: 0.8 },
  };
  E.PIP_POSES = POSES; E.PIP_EXPR = EXPR;
  const lerpPose = (a, b, k) => ({ L: [E.lerp(a.L[0], b.L[0], k), E.lerp(a.L[1], b.L[1], k)], R: [E.lerp(a.R[0], b.R[0], k), E.lerp(a.R[1], b.R[1], k)] });
  const lerpExpr = (a, b, k) => { const o = {}; for (const key of ['brow', 'browY', 'smile', 'eye']) o[key] = E.lerp(a[key] ?? 0, b[key] ?? 0, k); o.mouthO = E.lerp(a.mouthO || 0, b.mouthO || 0, k); o.browSplit = k > 0.5 ? b.browSplit : a.browSplit; return o; };
  // keys: [[time, name], ...] -> blended pose / expression (spring blend). Unknown names throw with the valid list.
  const blend = (table, kind, lerpF) => (t, keys) => {
    for (const k of keys) if (!table[k[1]]) throw new Error(`unknown ${kind} ${k[1]} (${kind}s: ${Object.keys(table).join(', ')})`);
    let p = table[keys[0][1]];
    for (let i = 1; i < keys.length; i++) { const k = E.clamp(E.sp(t, keys[i][0], [220, 22])); if (k > 0) p = lerpF(p, table[keys[i][1]], k); }
    return p;
  };
  E.pipPoseAt = blend(POSES, 'pose', lerpPose);
  E.pipExprAt = blend(EXPR, 'expression', lerpExpr);

  // o: {x, y (bottom of the torso), s, poseKeys | pose, exprKeys | expr, look [dx,dy], talk [[t0,t1],...],
  //     hop (time of a little jump), opacity, prop (fn(handR, handL) -> svg drawn over the hands)}
  E.comp.Pip = (t0, o) => {
    const t = E.twos(t0), id = 'pip';
    const pose = o.poseKeys ? E.pipPoseAt(t, o.poseKeys) : POSES[o.pose || 'rest'];
    const ex = o.exprKeys ? E.pipExprAt(t, o.exprKeys) : EXPR[o.expr || 'neutral'];
    const breathe = 1 + 0.02 * Math.sin(2 * Math.PI * 0.25 * t);
    const jit = (E.rng(E.hash('pj' + Math.floor(t * 12)))() - 0.5) * 1.0;
    let hop = 0, sq = 1;
    if (o.hop !== undefined) { const d = t0 - o.hop; if (d >= 0 && d < 0.5) hop = -16 * Math.sin(d / 0.5 * Math.PI); if (d >= 0.45 && d < 0.65) sq = 1 - 0.06 * Math.sin((d - 0.45) / 0.2 * Math.PI); }
    let talkO = 0;
    for (const [a, b] of (o.talk || [])) if (t0 >= a && t0 <= b) talkO = 0.5 + 0.5 * Math.abs(Math.sin(2 * Math.PI * 4.2 * t));
    const shY = -54, sh = { L: [-19, shY], R: [19, shY] };
    const arm = side => {
      const [a1, a2] = pose[side], [sx, sy] = sh[side];
      const ex1 = sx + Math.cos(a1 * D2R) * 23, ey1 = sy + Math.sin(a1 * D2R) * 23;
      const hx = ex1 + Math.cos(a2 * D2R) * 21, hy = ey1 + Math.sin(a2 * D2R) * 21;
      let s = E.R('linearPath', [[[sx, sy], [ex1, ey1], [hx, hy]]], { sw: 10, stroke: C.ink, roughness: 0.4, single: true }, id + 'arm' + side, t);
      s += E.R('linearPath', [[[sx, sy], [ex1, ey1], [hx, hy]]], { sw: 7, stroke: C.saffron, roughness: 0.3, single: true, still: true }, id + 'armc' + side, 0);
      // mitten: an ellipse along the forearm with a thumb
      const ang = a2;
      s += E.g(E.tf(hx, hy, 1, ang), E.R('ellipse', [2, 0, 20, 15], { fill: C.cream, sw: 1.6, roughness: 0.6 }, id + 'mit' + side, t) +
        E.R('ellipse', [-1, side === 'L' ? 6 : -6, 8, 6], { fill: C.cream, sw: 1.3, roughness: 0.5 }, id + 'thumb' + side, t));
      return { s, hand: [hx, hy] };
    };
    const aL = arm('L'), aR = arm('R');
    let s = '';
    // torso: a rounded bean in a saffron jumper with a teal pocket and a pencil
    let torso = E.R('path', ['M-27,0 C-30,-30 -24,-58 -12,-62 L12,-62 C24,-58 30,-30 27,0 Z'], { fill: C.saffron, sw: 2, roughness: 0.8 }, id + 'torso', t);
    torso += E.R('path', ['M-11,-62 L0,-48 L11,-62'], { stroke: C.ink, sw: 1.6, roughness: 0.6 }, id + 'collar', t);
    torso += E.R('rectangle', [5, -36, 14, 13], { fill: C.teal, sw: 1.4, roughness: 0.6 }, id + 'pocket', t);
    torso += E.R('line', [9, -36, 13, -50], { stroke: C.brick, sw: 3 }, id + 'pencil', t);
    for (const y of [-40, -26, -12]) torso += E.circle(-7, y, 1.8, { fill: C.ink, opacity: 0.6 });
    s += E.g(`scale(1,${breathe.toFixed(4)})`, torso);
    // head
    const hy = -88 * breathe;
    let head = E.R('circle', [0, 0, 56], { fill: C.skin, sw: 1.8, roughness: 0.7 }, id + 'head', t);
    // knitted hat with a fold and a pompom
    head += E.R('path', ['M-27,-8 C-27,-34 27,-34 27,-8 Z'], { fill: C.brick, sw: 1.8, roughness: 0.8 }, id + 'hat', t);
    head += E.R('rectangle', [-29, -12, 58, 9], { fill: '#9C4430', sw: 1.6, roughness: 0.6 }, id + 'fold', t);
    for (let i = -20; i <= 20; i += 8) head += E.line(i, -27 + Math.abs(i) * 0.3, i, -14, { stroke: '#8E3B29', sw: 1.2, opacity: 0.7 });
    const pom = Math.sin(t * 2 * Math.PI * 0.5) * 1.5;
    head += E.R('circle', [pom, -33, 13], { fill: C.cream, sw: 1.5, roughness: 1.4 }, id + 'pom', t);
    // eyes: beads that blink, brows, nose, cheeks, mouth
    const lk = o.look || [0, 0], ln = Math.hypot(lk[0], lk[1]) || 1, px = lk[0] / ln * 2.2 * Math.min(1, ln), py = lk[1] / ln * 2.0 * Math.min(1, ln);
    const bp = 2.6 + E.rng(E.hash('pipblink'))() * 2.0, ph = (t % bp) / bp, blink = ph > 0.96;
    for (const sx of [-10, 10]) {
      if (blink) head += E.line(sx - 4, 4, sx + 4, 4, { stroke: C.ink, sw: 2 });
      else head += E.g(E.tf(sx + px, 4 + py, 1, 0, 1, ex.eye), E.circle(0, 0, 3.6, { fill: C.ink }) + E.circle(1, -1.3, 1, { fill: C.white }));
      const ang = (sx < 0 ? 1 : -1) * ex.brow * (ex.browSplit && sx > 0 ? -0.6 : 1);
      head += E.g(E.tf(sx, -5 + ex.browY, 1, ang), E.line(-5, 0, 5, 0, { stroke: C.ink, sw: 2.2 }));
    }
    head += E.circle(0, 11, 3.2, { fill: '#D9937A' });
    head += E.circle(-17, 13, 4.5, { fill: '#E9A08A', opacity: 0.55 }) + E.circle(17, 13, 4.5, { fill: '#E9A08A', opacity: 0.55 });
    const sm = ex.smile, mo = Math.max(talkO, ex.mouthO || 0);
    if (mo > 0.05) head += E.path(`M-5,18 Q0,${(18 + 9 * mo).toFixed(1)} 5,18 Q0,${(16).toFixed(1)} -5,18 Z`, { fill: '#6B2E2A', stroke: C.ink, sw: 1.2 });
    else head += E.path(`M-7,18 Q0,${(18 + sm * 7).toFixed(1)} 7,18`, { stroke: C.ink, sw: 2 });
    s += E.g(E.tf(0, hy), head);
    s += aL.s + aR.s;
    if (o.prop) s += o.prop(aR.hand, aL.hand);
    return E.g(E.tf(o.x, o.y + hop, (o.s ?? 1), jit) + ` scale(${(1 / sq ** 0.5).toFixed(4)},${sq.toFixed(4)})`, s, { opacity: o.opacity });
  };
})();
