"""Download the photos the demo uses from Wikimedia Commons, only if their licence is CC0 or public domain.
Writes sources/images/<name>.jpg (640 px wide thumbnails) and sources/images.json (title, licence, author, url, sha256).
Re-running checks the licence again and re-downloads only missing files.
    python3 experiments/fetch_images.py
"""
import hashlib, json, pathlib, urllib.parse, urllib.request

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "sources" / "images"
OUT.mkdir(parents=True, exist_ok=True)
UA = {"User-Agent": "research-explainer-demo/0.2 (github.com/sepi2p/research-explainer-skill)"}
FILES = {   # name -> Commons file title
    "cat": "File:Young tabby cat keeping watch.jpg",
    "cat2": "File:Tabby Cat at a Cat Cafe (Taipei).jpg",
    "dog": "File:Golden Retriever Chewing A Stick.jpg",
    "dog2": "File:Charlie the Golden Retriever surrounded by daisies.png",
    "fish": "File:Yatomi-Goldfish-1.jpg",
    "fish2": "File:Goldfish in the Cave.jpg",
}
OK = ("CC0", "Public domain", "PD")


def get(url):
    with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=60) as r:
        return r.read()


meta = {}
for name, title in FILES.items():
    q = urllib.parse.urlencode({"action": "query", "format": "json", "titles": title, "prop": "imageinfo",
                                "iiprop": "url|extmetadata", "iiurlwidth": 640,
                                "iiextmetadatafilter": "LicenseShortName|Artist|LicenseUrl"})
    page = next(iter(json.loads(get("https://commons.wikimedia.org/w/api.php?" + q))["query"]["pages"].values()))
    ii = page["imageinfo"][0]
    lic = ii["extmetadata"]["LicenseShortName"]["value"]
    if not lic.startswith(OK):
        raise SystemExit(f"{title}: licence {lic} is not CC0/public domain; pick another file")
    f = OUT / f"{name}.jpg"
    if not f.exists():
        data = get(ii["thumburl"])
        f.write_bytes(data)
    meta[name] = {"title": title, "licence": lic, "author": ii["extmetadata"].get("Artist", {}).get("value", ""),
                  "page": ii["descriptionurl"], "file_url": ii["thumburl"], "sha256": hashlib.sha256(f.read_bytes()).hexdigest()}
    print(name, lic, f.name)
(ROOT / "sources" / "images.json").write_text(json.dumps(meta, indent=1, ensure_ascii=False))
