# -*- coding: utf-8 -*-
"""Fabrique un fichier .zip par fiche (importable dans Clinicum) : manifest.json + sections mp3 (stockées sans compression)."""
import json, os, re, sys, unicodedata, zipfile
idx = json.load(open("audio/index.json", encoding="utf-8"))
os.makedirs("zips", exist_ok=True)
def slug(s):
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode()
    return re.sub(r"[^A-Za-z0-9]+", "-", s).strip("-")[:60]
n = 0
made = []  # (id, voix, chemin)
for k in sorted(idx, key=int):
    v = idx[k]
    if "h2" not in v: continue
    man = {"v": 1, "id": int(k), "name": v["name"], "h2": v["h2"], "v": v.get("v", ""), "sec": v["sec"], "bytes": v["bytes"],
           "chapters": [{"key": c["key"], "title": c["title"], "file": c["file"], "sec": c["sec"], "bytes": c["bytes"]} for c in v["chapters"]]}
    if not all(os.path.exists(f"audio/{int(k):03d}/{c['file']}") for c in v["chapters"]):
        print("ignoré (fichiers absents) :", k, v["name"]); continue
    out = f"zips/Clinicum-{int(k):03d}-{slug(v['name'])}.zip"
    with zipfile.ZipFile(out, "w", zipfile.ZIP_STORED) as z:
        z.writestr("manifest.json", json.dumps(man, ensure_ascii=False))
        for c in v["chapters"]:
            z.write(f"audio/{int(k):03d}/{c['file']}", c["file"])
    n += 1
    made.append((int(k), v.get("v", ""), out))
print(n, "zips")

# Paquets : un seul fichier à télécharger qui contient plusieurs sujets (Clinicum sait les importer d'un coup).
def pack(name, items):
    if not items: return
    with zipfile.ZipFile(f"zips/{name}", "w", zipfile.ZIP_STORED) as z:
        for _id, _v, path in items:
            z.write(path, os.path.basename(path))
    print("paquet", name, len(items), "sujets", round(os.path.getsize(f"zips/{name}") / 1048576, 1), "Mo")
pack("Clinicum-Pack-Complet.zip", made)
pack("Clinicum-Pack-Ariane.zip", [m for m in made if not m[1] or m[1].startswith("ariane")])
pack("Clinicum-Pack-Vivienne.zip", [m for m in made if m[1].startswith("vivienne")])
