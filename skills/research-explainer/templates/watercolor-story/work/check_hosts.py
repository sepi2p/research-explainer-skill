"""Check that index.html agrees with assets/cues.js HOST (scene starts, film length) and with the captions' END.
Run after every re-timing: python3 work/check_hosts.py (exit 1 on a mismatch)."""
import re, pathlib, sys
H = pathlib.Path(__file__).resolve().parent.parent
idx = (H / "index.html").read_text(); cues = (H / "assets" / "cues.js").read_text()
host = dict((k, float(v)) for k, v in re.findall(r"(\w+): ([\d.]+)", re.search(r"HOST = \{([^}]*)\}", cues).group(1)))
bad = 0
for hid, start, dur in re.findall(r'<div id="(\w+)"[^>]*?data-start="([\d.]+)" data-duration="([\d.]+)"', idx, re.S):
    if hid in host and abs(host[hid] - float(start)) > 1e-6: print("MISMATCH", hid, "index.html", start, "cues.js", host[hid]); bad = 1
    print(f"{hid:9s} {float(start):6.2f} -> {float(start) + float(dur):6.2f}")
main = float(re.search(r'data-composition-id="main" data-start="0" data-duration="([\d.]+)"', idx).group(1))
if abs(main - host["end"]) > 1e-6: print("MISMATCH film length: index.html", main, "cues.js end", host["end"]); bad = 1
cap = re.search(r"END = ([\d.]+)", (H / "compositions" / "captions.html").read_text())
if cap and abs(float(cap.group(1)) - host.get("capEnd", float(cap.group(1)))) > 1e-6:
    print("MISMATCH captions END", cap.group(1), "cues.js capEnd", host["capEnd"]); bad = 1
print("ok" if not bad else "fix the mismatches above"); sys.exit(bad)
