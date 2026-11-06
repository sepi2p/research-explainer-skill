// The handwriting font (Caveat, SIL OFL 1.1: assets/fonts/OFL_caveat.txt), registered once from the local file for every
// scene; the compositions' CSS refers to it as var(--hand). Inter and JetBrains Mono are supplied by HyperFrames itself.
(function () {
  const face = new FontFace("Caveat", "url(assets/fonts/Caveat.ttf)", { weight: "400 700" });
  document.fonts.add(face);
  face.load();
  document.documentElement.style.setProperty("--hand", '"Caveat", cursive');
})();
