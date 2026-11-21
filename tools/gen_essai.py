import asyncio, json, glob, os, subprocess, edge_tts
import edge_tts.communicate as _ec
_orig = _ec.mkssml
def _fr(*a, **k):
    x = _orig(*a, **k)
    return x.replace("xml:lang='en-US'", "xml:lang='fr-FR'").replace('xml:lang="en-US"', 'xml:lang="fr-FR"')
_ec.mkssml = _fr
print("SSML exemple :", _fr(*([_ec.TTSConfig("Bonjour.", "fr-FR-VivienneMultilingualNeural")] if hasattr(_ec,"TTSConfig") else ["fr-FR-VivienneMultilingualNeural","+0%","+0%","+0Hz","Bonjour."]), *([ "Bonjour."] if hasattr(_ec,"TTSConfig") else [])) if False else "patch actif")
VOICE = "fr-FR-VivienneMultilingualNeural"
async def one(text, path):
    for k in range(3):
        try:
            await edge_tts.Communicate(text, VOICE).save(path)
            if os.path.getsize(path) > 1000: return
        except Exception as e:
            print("retry", path, e)
    raise SystemExit("echec " + path)
async def main():
    for f in sorted(glob.glob("essai-voix/textes/*.json")):
        r = json.load(open(f)); d = f"essai-voix/audio/{r['id']:03d}"; os.makedirs(d, exist_ok=True)
        files = []; info = []
        for i, c in enumerate(r["chapters"]):
            p = f"{d}/{i:02d}-{c['key']}.mp3"
            await one(c["text"], p); files.append(p)
            dur = float(subprocess.check_output(["ffprobe","-v","error","-show_entries","format=duration","-of","csv=p=0",p]).decode())
            info.append({"key": c["key"], "title": c["title"], "file": os.path.basename(p), "sec": round(dur,1), "bytes": os.path.getsize(p)})
        open(f"{d}/liste.txt","w").write("".join(f"file '{os.path.abspath(p)}'\n" for p in files))
        subprocess.check_call(["ffmpeg","-y","-loglevel","error","-f","concat","-safe","0","-i",f"{d}/liste.txt","-c","copy",f"essai-voix/audio/{r['id']:03d}-fiche-complete.mp3"])
        os.remove(f"{d}/liste.txt")
        json.dump({"id": r["id"], "name": r["name"], "hash": r["hash"], "chapters": info}, open(f"{d}/chapitres.json","w"), ensure_ascii=False, indent=1)
asyncio.run(main())
