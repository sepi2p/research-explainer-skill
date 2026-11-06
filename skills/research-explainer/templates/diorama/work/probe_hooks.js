// probe_hooks.js: loaded by work/probe_motion.mjs between the components and the scenes (never in the real page).
// Wraps the paper components whose appearance is a visible motion and records which of them are drawn, visibly, at
// each sampled time, so work/audio.py can put a sound where something appears. A key per drawing:
// "<Component>|<scene>|<id, data key, title or text>", with the exact start time when the component has one (o.t0).
// Not wrapped (no sound of their own): Caption (changes every beat), Legend (pinned on the set), Ladder and Ribbon (HUD;
// ribbon pins come from E.PINS), FrameBorder (the frame shot's camera move has the sound), Reveal (it draws Sticky,
// Stamp and TermCard, which are wrapped), the puppet and the set. Add your own components to COMPS.
(() => {
  const COMPS = ['Slip', 'Torn', 'Sticky', 'Stamp', 'TermCard', 'Chip', 'Bubble', 'Check', 'Cross', 'Plot'];
  const FRESH = 0.25;   // a plot point or line counts while it is appearing; one already there when the plot arrives does not
  const P = window.__probe = { frame: new Map(), rendered: new Set(), cur: '' };
  const str = v => (typeof v === 'string' || typeof v === 'number') ? String(v) : '';
  const ident = o => (str(o.id) || str(o.key) || str(o.title) || str(o.text) || str(o.label) || str(o.term) ||
    str(o.cite) || str(o.html) || '').slice(0, 48);
  const shown = (t, o, out) => !!out && (o.opacity === undefined || o.opacity > 0.05) && (o.s === undefined || o.s > 0.05) &&
    (o.t0 === undefined || t >= o.t0);
  const add = (name, id, t0) => { const k = name + '|' + P.cur + '|' + id; if (!P.frame.has(k)) P.frame.set(k, t0 ?? null); };
  const fresh = (t, t0) => Number.isFinite(t0) && t >= t0 && t - t0 < FRESH;
  for (const name of COMPS) {
    const f = E.comp[name]; if (!f) continue;
    E.comp[name] = (t, o = {}) => {
      const out = f(t, o);
      if (shown(t, o, out)) {
        add(name, ident(o), Number.isFinite(o.t0) ? o.t0 : null);
        if (name === 'Plot') {     // its timed parts: points (traces[].appear), dashed levels and guide curves (t0)
          for (const tr of (o.traces || [])) {
            const ts = Array.isArray(tr.appear) ? tr.appear : (tr.appear !== undefined ? [tr.appear] : []);
            ts.forEach((t0, i) => { if (fresh(t, t0)) add('Point', tr.key + '#' + i, t0); });
          }
          for (const g of [...(o.hlines || []), ...(o.guides || [])]) if (fresh(t, g.t0)) add('Line', g.key, g.t0);
        }
      }
      return out;
    };
  }
})();
