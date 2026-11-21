import asyncio, json, glob, os, subprocess, edge_tts
import edge_tts.communicate as _ec
def _fr(*a, **k):
    text = a[-1]
    return ("<speak version='1.0' xmlns='http://www.w3.org/2001/10/synthesis' xml:lang='fr-FR'>"
            "<voice name='fr-FR-VivienneMultilingualNeural'><lang xml:lang='fr-FR'>"
            "<prosody pitch='+0Hz' rate='+0%' volume='+0%'>" + text + "</prosody></lang></voice></speak>")
_ec.mkssml = _fr
print("SSML fr-FR :", _fr("x", "Rougeole."))
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
            if os.environ.get('INTRO') == '1' and i > 0: break
            p = f"{d}/{i:02d}-{c['key']}.mp3"
            await one(c["text"], p); files.append(p)
            dur = float(subprocess.check_output(["ffprobe","-v","error","-show_entries","format=duration","-of","csv=p=0",p]).decode())
            info.append({"key": c["key"], "title": c["title"], "file": os.path.basename(p), "sec": round(dur,1), "bytes": os.path.getsize(p)})
        if os.environ.get('INTRO') == '1':
            os.makedirs('essai-voix/intro', exist_ok=True)
            os.replace(files[0], f"essai-voix/intro/{r['id']:03d}-intro.mp3"); continue
        open(f"{d}/liste.txt","w").write("".join(f"file '{os.path.abspath(p)}'\n" for p in files))
        subprocess.check_call(["ffmpeg","-y","-loglevel","error","-f","concat","-safe","0","-i",f"{d}/liste.txt","-c","copy",f"essai-voix/audio/{r['id']:03d}-fiche-complete.mp3"])
        os.remove(f"{d}/liste.txt")
        json.dump({"id": r["id"], "name": r["name"], "hash": r["hash"], "chapters": info}, open(f"{d}/chapitres.json","w"), ensure_ascii=False, indent=1)
asyncio.run(main())
