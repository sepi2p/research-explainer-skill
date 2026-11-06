"""make_data.py: window.DATA for the page. Every number on graph paper comes from here: each data/<name>.json (written
by the data scripts in data/, e.g. data/readings.py) becomes DATA.<name>, read in scenes with E.D('<name>.<key>...').
    python3 work/make_data.py"""
import json, pathlib
ROOT = pathlib.Path(__file__).resolve().parent.parent
D = {p.stem: json.loads(p.read_text()) for p in sorted((ROOT / "data").glob("*.json"))}
if not D: raise SystemExit("no data/*.json yet: run the data scripts first (e.g. python3 data/readings.py)")
(ROOT / "video/data.js").write_text("window.DATA = " + json.dumps(D, ensure_ascii=False) + ";\n")
for k, v in D.items(): print(f"DATA.{k}: {', '.join(list(v)[:12]) if isinstance(v, dict) else type(v).__name__}")
