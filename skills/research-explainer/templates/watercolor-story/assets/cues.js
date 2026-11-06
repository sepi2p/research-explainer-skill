// Cue times from the narrator's word times (assets/words.js, written by work/make_captions.py), so a new voice take
// re-times a scene without editing it: write cues as CUES.at("sA", "N2", "average") instead of literal seconds.
// HOST holds each scene host's start in film time and must match index.html (work/check_hosts.py checks it, plus the film
// length and the captions' end). WT(line, word, k) = film time of the k-th occurrence of `word` in `line`;
// at(host, line, word, k) = the same in that scene's own time. (The demo's scenes still use literal times; new scenes
// should use these.)
(function () {
  const HOST = { sA: 0, t1: 13.65, sB1: 13.95, sB2: 17.6, s6: 34.0, end: 40.4, capEnd: 34.0 };
  const norm = (w) => w.toLowerCase().replace(/[^a-z0-9']/g, "");
  function WT(line, word, k) {
    const ws = (window.WORDS || []).filter((w) => w.line === line && norm(w.text) === norm(word));
    const w = ws[k || 0];
    if (!w) throw new Error("cues.js: no word '" + word + "' in line " + line);
    return w.start;
  }
  const at = (host, line, word, k) => WT(line, word, k) - HOST[host];
  window.CUES = { HOST, WT, at };
})();
