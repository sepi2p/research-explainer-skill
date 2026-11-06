// Paper cut-out puppets (no outlines, white cut edge, paper grain, soft shadow) in front of the painted watercolor set.
document.documentElement.dataset.look = "cutout";
window.PSTYLE = {
  look: "cutout", room: "assets/bg_set.jpg", tex: 0.18,
  rough: { roughness: 0.6, bowing: 0.3 }, noStroke: true,
  defs: '<defs><filter id="co" x="-15%" y="-15%" width="135%" height="140%">' +
    '<feMorphology in="SourceAlpha" operator="dilate" radius="1.3" result="dil"/>' +
    '<feFlood flood-color="#FFFDF6"/><feComposite in2="dil" operator="in" result="edge"/>' +
    '<feTurbulence type="fractalNoise" baseFrequency="0.11" numOctaves="2" seed="4" result="n"/>' +
    '<feColorMatrix in="n" type="matrix" values="0 0 0 0 0.3  0 0 0 0 0.24  0 0 0 0 0.18  0 0 0 0.22 -0.06" result="tn"/>' +
    '<feComposite in="tn" in2="SourceAlpha" operator="in" result="tex"/>' +
    '<feMerge result="card"><feMergeNode in="edge"/><feMergeNode in="SourceGraphic"/><feMergeNode in="tex"/></feMerge>' +
    '<feDropShadow in="card" dx="2.4" dy="3.4" stdDeviation="1.8" flood-color="#3A2A1A" flood-opacity="0.42"/></filter></defs>',
  post: (o) => o.replace(/<path d="([^"]+)" fill="(#[0-9A-Fa-f]{6}|rgba[^"]+)"\/>/g, '<path d="$1" fill="$2" filter="url(#co)"/>'),
};
