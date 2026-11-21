# -*- coding: utf-8 -*-
"""Fabrique un fichier .zip par fiche (importable dans Clinicum) : manifest.json + sections mp3 (stockées sans compression)."""
import json, os, re, sys, unicodedata, zipfile
idx = json.load(open("audio/index.json", encoding="utf-8"))
os.makedirs("zips", exist_ok=True)
def slug(s):
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode()
    return re.sub(r"[^A-Za-z0-9]+", "-", s).strip("-")[:60]
n = 0
for k in sorted(idx, key=int):
    v = idx[k]
    if "h2" not in v: continue
    man = {"v": 1, "id": int(k), "name": v["name"], "h2": v["h2"], "v": v.get("v", ""), "sec": v["sec"], "bytes": v["bytes"],
           "chapters": [{"key": c["key"], "title": c["title"], "file": c["file"], "sec": c["sec"], "bytes": c["bytes"]} for c in v["chapters"]]}
    out = f"zips/Clinicum-{int(k):03d}-{slug(v['name'])}.zip"
    with zipfile.ZipFile(out, "w", zipfile.ZIP_STORED) as z:
        z.writestr("manifest.json", json.dumps(man, ensure_ascii=False))
        for c in v["chapters"]:
            z.write(f"audio/{int(k):03d}/{c['file']}", c["file"])
    n += 1
print(n, "zips")
