#!/usr/bin/env python3
"""Audios Clinicum : voix fr-CH-ArianeNeural (français uniquement), volume renforcé, normalisation -14 LUFS.
Lit tools/lot.json (liste d'identifiants de fiches), écrit audio/NNN/KK-clé.mp3 et audio/index.json.
Ne refait que les fiches nouvelles ou modifiées (empreinte 'hash')."""
import asyncio, json, os, re, subprocess, sys, glob
import edge_tts
import edge_tts.communicate as _ec

VOICE = "fr-CH-ArianeNeural"
VOL = os.environ.get("VOL", "+25%")
CHUNK = 2800
SEM = asyncio.Semaphore(3)

def _fr(*a, **k):
    text = a[-1]
    if isinstance(text, bytes): text = text.decode("utf-8")
    return ("<speak version='1.0' xmlns='http://www.w3.org/2001/10/synthesis' xml:lang='fr-FR'>"
            f"<voice name='{VOICE}'><prosody pitch='+0Hz' rate='+0%' volume='{VOL}'>" + text + "</prosody></voice></speak>")
_ec.mkssml = _fr

def chunks(text):
    if len(text) <= CHUNK: return [text]
    parts, cur = [], ""
    for s in re.split(r'(?<=[.;:!?]) ', text):
        if cur and len(cur) + len(s) + 1 > CHUNK:
            parts.append(cur); cur = s
        else:
            cur = (cur + " " + s).strip()
    if cur: parts.append(cur)
    return parts

async def synth(text, path):
    async with SEM:
        for k in range(5):
            try:
                await edge_tts.Communicate(text, VOICE).save(path)
                if os.path.getsize(path) > 1000: return
            except Exception as e:
                print("retry", path, e, flush=True)
            await asyncio.sleep(5 * (k + 1))
    sys.exit("échec " + path)

async def chapter(d, i, c):
    base = f"{d}/{i:02d}-{c['key']}"
    parts = chunks(c["text"])
    tmp = []
    await asyncio.gather(*[synth(p, f"{base}.p{j}.mp3") for j, p in enumerate(parts)])
    for j in range(len(parts)): tmp.append(f"{base}.p{j}.mp3")
    lst = f"{base}.txt"
    open(lst, "w").write("".join(f"file '{os.path.abspath(t)}'\n" for t in tmp))
    out = f"{base}.mp3"
    subprocess.check_call(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", lst,
                           "-af", "loudnorm=I=-14:TP=-1.0:LRA=9", "-ar", "24000", "-ac", "1", "-b:a", "40k", out])
    for t in tmp: os.remove(t)
    os.remove(lst)
    sec = float(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", out]).decode())
    return {"key": c["key"], "title": c["title"], "file": os.path.basename(out), "sec": round(sec, 1), "bytes": os.path.getsize(out)}

async def main():
    lot = json.load(open("tools/lot.json"))
    idx_path = "audio/index.json"
    os.makedirs("audio", exist_ok=True)
    idx = json.load(open(idx_path)) if os.path.exists(idx_path) else {}
    for fid in lot:
        r = json.load(open(f"textes/{fid:03d}.json"))
        if idx.get(str(fid), {}).get("hash") == r["hash"]:
            print("déjà fait", fid, flush=True); continue
        d = f"audio/{fid:03d}"
        os.makedirs(d, exist_ok=True)
        for old in glob.glob(d + "/*.mp3"): os.remove(old)
        info = []
        for i, c in enumerate(r["chapters"]):
            info.append(await chapter(d, i, c))
        idx[str(fid)] = {"name": r["name"], "hash": r["hash"], "chapters": info,
                         "sec": round(sum(x["sec"] for x in info), 1), "bytes": sum(x["bytes"] for x in info)}
        json.dump(idx, open(idx_path, "w"), ensure_ascii=False, indent=0)
        print(f"OK {fid:03d} {r['name']} {idx[str(fid)]['sec']} s {idx[str(fid)]['bytes']//1000} Ko", flush=True)
asyncio.run(main())
