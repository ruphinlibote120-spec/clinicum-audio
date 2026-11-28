#!/usr/bin/env python3
"""Essai du style « conté » sur UNE fiche (FICHE=0 par défaut : Paludisme grave).
N'écrit que dans essai/ : les audios publiés dans l'application (audio/) ne sont pas touchés.
Sorties : essai/conte-NNN-<nom>.mp3 (audio complet) et essai/conte-NNN-<nom>.txt (texte lu, à relire)."""
import asyncio, json, os, re, shutil, subprocess, sys, unicodedata
sys.path.insert(0, "tools")
import gen_edge as g
import narration

def slug(t):
    t = unicodedata.normalize("NFD", t.lower()); t = "".join(c for c in t if unicodedata.category(c) != "Mn")
    return re.sub(r"[^a-z0-9]+", "-", t).strip("-")

async def main():
    fid = int(os.environ.get("FICHE", "0"))
    d = json.load(open("tools/sujets.json"))
    rec = narration.narrate(fid, d[fid])
    base = f"essai/conte-{fid:03d}-{slug(rec['name'])}"
    os.makedirs("essai", exist_ok=True); work = base + ".tmp"
    shutil.rmtree(work, ignore_errors=True); os.makedirs(work)
    open(base + ".txt", "w", encoding="utf-8").write(
        rec["name"] + "\n\n" + "\n\n".join(f"[{c['title']}]\n{c['text']}" for c in rec["chapters"]) + "\n")
    info = [await g.chapter(work, i, c) for i, c in enumerate(rec["chapters"])]
    lst = base + ".list"
    open(lst, "w").write("".join(f"file '{os.path.abspath(os.path.join(work, x['file']))}'\n" for x in info))
    subprocess.check_call(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", lst, "-c", "copy", base + ".mp3"])
    os.remove(lst); shutil.rmtree(work)
    sec = sum(x["sec"] for x in info)
    print(f"{base}.mp3 : {sec/60:.1f} min, {os.path.getsize(base + '.mp3')/1e6:.1f} Mo, {len(rec['chapters'])} chapitres")

asyncio.run(main())
