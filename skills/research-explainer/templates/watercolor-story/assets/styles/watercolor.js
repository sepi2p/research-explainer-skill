// Everything in watercolor: the AI-painted set (assets/bg_set.jpg) and wash (assets/bg_wash.jpg) behind, and the
// engine's shapes painted on top: lighter washed colours, wobbly bleeding edges, darker wet rims, pigment grain, thin warm ink.
(function () {
  const P = [255, 251, 242];
  const wash = (c, k) => { const n = parseInt(c.slice(1), 16), v = [n >> 16, (n >> 8) & 255, n & 255];
    return "#" + v.map((x, i) => Math.round(x * (1 - k) + P[i] * k).toString(16).padStart(2, "0")).join(""); };
  const DEFS = '<defs><filter id="wcP" x="-12%" y="-12%" width="124%" height="124%" color-interpolation-filters="sRGB">' +
    '<feTurbulence type="fractalNoise" baseFrequency="0.035" numOctaves="3" seed="7" result="n1"/>' +
    '<feDisplacementMap in="SourceGraphic" in2="n1" scale="5" xChannelSelector="R" yChannelSelector="G" result="d"/>' +
    '<feGaussianBlur in="d" stdDeviation="2.4" result="bl"/>' +
    '<feColorMatrix in="d" type="matrix" values="0 0 0 1 0  0 0 0 1 0  0 0 0 1 0  0 0 0 1 0" result="da"/>' +
    '<feColorMatrix in="bl" type="matrix" values="0 0 0 1 0  0 0 0 1 0  0 0 0 1 0  0 0 0 1 0" result="ba"/>' +
    '<feComposite in="da" in2="ba" operator="arithmetic" k1="0" k2="1" k3="-1" k4="0" result="E"/>' +
    '<feComposite in="d" in2="E" operator="arithmetic" k1="0" k2="1" k3="-0.6" k4="0" result="rim"/>' +
    '<feTurbulence type="fractalNoise" baseFrequency="0.75" numOctaves="2" seed="3" result="g"/>' +
    '<feColorMatrix in="g" type="matrix" values="0 0 0 0 0.36  0 0 0 0 0.29  0 0 0 0 0.24  0 0 0 0.34 -0.1" result="g2"/>' +
    '<feComposite in="g2" in2="rim" operator="in" result="g3"/>' +
    '<feTurbulence type="fractalNoise" baseFrequency="0.012" numOctaves="2" seed="21" result="w"/>' +
    '<feColorMatrix in="w" type="matrix" values="0 0 0 0 1  0 0 0 0 1  0 0 0 0 0.97  0 0 0 0.5 -0.18" result="w2"/>' +
    '<feComposite in="w2" in2="rim" operator="in" result="w3"/>' +
    '<feMerge><feMergeNode in="rim"/><feMergeNode in="w3"/><feMergeNode in="g3"/></feMerge></filter></defs>';
  document.documentElement.dataset.look = "watercolor";
  window.PSTYLE = {
    look: "watercolor", room: "assets/bg_set.jpg", tex: 0.18,
    rough: { roughness: 1.6, bowing: 1.3, strokeWidth: 1.15, stroke: "#5B4E46" },
    defs: DEFS,
    post: (o) => o
      .replace(/<path d="([^"]+)" fill="(#[0-9A-Fa-f]{6})"\/>/g, (m, d, c) => '<path d="' + d + '" fill="' + wash(c, 0.2) + '" filter="url(#wcP)"/>')
      .replace(/<path d="([^"]+)" fill="none" stroke="#1F2A44" stroke-width="([0-9.]+)"/g, (m, d, w) => '<path d="' + d + '" fill="none" stroke="#5B4E46" stroke-opacity="0.8" stroke-width="' + w + '"'),
  };
})();
