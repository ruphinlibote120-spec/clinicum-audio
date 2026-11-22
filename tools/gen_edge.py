#!/usr/bin/env python3
"""Audios Clinicum : voix fr-CH-ArianeNeural (français uniquement), débit ralenti, pauses rythmées, volume renforcé, normalisation -14 LUFS.
Lit tools/lot.json (liste d'identifiants de fiches), écrit audio/NNN/KK-clé.mp3 et audio/index.json.
Ne refait que les fiches nouvelles ou modifiées (empreinte 'hash')."""
import asyncio, json, os, re, subprocess, sys, glob
import edge_tts
import edge_tts.communicate as _ec

_VC = json.load(open("tools/voice.json")) if os.path.exists("tools/voice.json") else {}
VOICE = os.environ.get("VOICE") or _VC.get("voice") or "fr-CH-ArianeNeural"
VTAG = os.environ.get("VTAG") or _VC.get("tag") or ""   # étiquette de voix : change quand la voix change (l'application propose alors la mise à jour)
VOL = os.environ.get("VOL", "+25%")
RATE = os.environ.get("RATE") or _VC.get("rate") or "+0%"          # débit : "-12%" = 12 % plus lent
# Pauses (secondes) : le service refuse les balises <break>, donc on allonge les silences après coup avec ffmpeg.
_P = {"seuil": 0.40,   # un silence naturel >= seuil est une fin de phrase ; en dessous : virgule, deux-points...
      "s": 0.90,       # durée totale d'une pause de fin de phrase
      "t": 1.30,       # pause après le titre de la section (première phrase)
      "c": 0.15,       # temps ajouté aux petites pauses (virgule, deux-points, point-virgule)
      "j": 0.50,       # pause entre deux morceaux d'un même chapitre
      "e": 0.60,       # pause à la fin du chapitre
      **_VC.get("pause", {})}
CHUNK = 2800
SEM = asyncio.Semaphore(3)

def _fr(*a, **k):
    text = a[-1]
    if isinstance(text, bytes): text = text.decode("utf-8")
    return ("<speak version='1.0' xmlns='http://www.w3.org/2001/10/synthesis' xml:lang='fr-FR'>"
            f"<voice name='{VOICE}'><prosody pitch='+0Hz' rate='{RATE}' volume='{VOL}'>" + text + "</prosody></voice></speak>")
_ec.mkssml = _fr

def _run(cmd):
    subprocess.check_call(["ffmpeg", "-y", "-loglevel", "error"] + cmd)

def _dur(path):
    return float(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", path]).decode())

def silences(path, noise="-40dB", d=0.18):
    r = subprocess.run(["ffmpeg", "-i", path, "-af", f"silencedetect=noise={noise}:d={d}", "-f", "null", "-"], capture_output=True, text=True).stderr
    return [(float(e) - float(du), float(e)) for e, du in re.findall(r"silence_end: ([\d.]+) \| silence_duration: ([\d.]+)", r)]

def assemble(wavs, out, base):
    """Colle les morceaux, allonge les pauses, normalise et encode en mp3."""
    sil = f"{base}.sil.wav"
    _run(["-f", "lavfi", "-i", "anullsrc=r=24000:cl=mono", "-t", "6", "-c:a", "pcm_s16le", sil])
    joint = f"{base}.all.wav"
    lst = f"{base}.join.txt"
    rows = []
    for k, w in enumerate(wavs):
        if k: rows += [f"file '{os.path.abspath(sil)}'", f"outpoint {_P['j']}"]
        rows.append(f"file '{os.path.abspath(w)}'")
    open(lst, "w").write("\n".join(rows) + "\n")
    _run(["-f", "concat", "-safe", "0", "-i", lst, "-c:a", "pcm_s16le", "-ar", "24000", "-ac", "1", joint])
    rows, cur, premiere = [], 0.0, True
    seg = lambda f, a, b=None: [f"file '{os.path.abspath(f)}'", f"inpoint {a:.3f}"] + ([f"outpoint {b:.3f}"] if b is not None else [])
    for a, b in silences(joint):
        du, mid = b - a, (a + b) / 2
        if du >= _P["seuil"]:
            cible = _P["t"] if (premiere and mid < 12) else _P["s"]
            premiere = False
            extra = max(0.0, cible - du)
        else:
            extra = _P["c"]
        rows += seg(joint, cur, mid); cur = mid
        if extra > 0.01: rows += [f"file '{os.path.abspath(sil)}'", f"outpoint {min(extra, 5.9):.3f}"]
    rows += seg(joint, cur)
    rows += [f"file '{os.path.abspath(sil)}'", f"outpoint {_P['e']}"]
    open(lst, "w").write("\n".join(rows) + "\n")
    fin = f"{base}.fin.wav"
    _run(["-f", "concat", "-safe", "0", "-i", lst, "-c:a", "pcm_s16le", "-ar", "24000", "-ac", "1", fin])
    _run(["-i", fin, "-af", "loudnorm=I=-14:TP=-1.0:LRA=9", "-ar", "24000", "-ac", "1", "-b:a", "40k", out])
    for f in (sil, joint, lst, fin): os.remove(f)

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
    await asyncio.gather(*[synth(p, f"{base}.p{j}.mp3") for j, p in enumerate(parts)])
    wavs = []
    for j in range(len(parts)):
        _run(["-i", f"{base}.p{j}.mp3", "-ar", "24000", "-ac", "1", "-c:a", "pcm_s16le", f"{base}.p{j}.wav"])
        os.remove(f"{base}.p{j}.mp3"); wavs.append(f"{base}.p{j}.wav")
    out = f"{base}.mp3"
    assemble(wavs, out, base)
    for w in wavs: os.remove(w)
    sec = _dur(out)
    return {"key": c["key"], "title": c["title"], "file": os.path.basename(out), "sec": round(sec, 1), "bytes": os.path.getsize(out)}

async def main():
    lot = json.load(open("tools/lot.json"))
    idx_path = "audio/index.json"
    os.makedirs("audio", exist_ok=True)
    idx = json.load(open(idx_path)) if os.path.exists(idx_path) else {}
    for fid in lot:
        r = json.load(open(f"textes/{fid:03d}.json"))
        old = idx.get(str(fid), {})
        if old.get("hash") == r["hash"] and old.get("v", "") == VTAG:
            print("déjà fait", fid, flush=True); continue
        d = f"audio/{fid:03d}"
        os.makedirs(d, exist_ok=True)
        for old in glob.glob(d + "/*.mp3"): os.remove(old)
        info = []
        for i, c in enumerate(r["chapters"]):
            info.append(await chapter(d, i, c))
        idx[str(fid)] = {"name": r["name"], "hash": r["hash"], "h2": json.load(open("tools/h2.json"))[str(fid)]["h2"], **({"v": VTAG} if VTAG else {}), "chapters": info,
                         "sec": round(sum(x["sec"] for x in info), 1), "bytes": sum(x["bytes"] for x in info)}
        json.dump(idx, open(idx_path, "w"), ensure_ascii=False, indent=0)
        print(f"OK {fid:03d} {r['name']} {idx[str(fid)]['sec']} s {idx[str(fid)]['bytes']//1000} Ko", flush=True)
if __name__ == "__main__":
    asyncio.run(main())
