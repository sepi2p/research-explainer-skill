# tiny OpenAI helper: key read from ~/.config/openai/key, never printed
import json, os, pathlib, urllib.request, time, base64, sys
def key():
    return os.getenv("OPENAI_API_KEY") or pathlib.Path.home().joinpath(".config/openai/key").read_text().strip()
def req(path, body=None, method=None, raw=False):
    data = json.dumps(body).encode() if body is not None else None
    r = urllib.request.Request("https://api.openai.com/v1/" + path, data=data, method=method or ("POST" if data else "GET"),
        headers={"Authorization": "Bearer " + key(), "Content-Type": "application/json"})
    for a in range(6):
        try:
            with urllib.request.urlopen(r, timeout=300) as f:
                b = f.read(); return b if raw else json.loads(b)
        except urllib.error.HTTPError as e:
            msg = e.read().decode()[:400]
            if e.code in (400, 401, 403, 404): raise SystemExit(f"HTTP {e.code}: {msg}")
            time.sleep(3 * 2 ** a)
    raise SystemExit("failed")
