#!/usr/bin/env python3
"""Génère les audios Clinicum avec Azure AI Speech (voix fr-FR-VivienneMultilingualNeural).
- lit textes/NNN.json, écrit audio/NNN/KK-clé.mp3 + audio/index.json
- ne régénère que les fiches nouvelles ou modifiées (empreinte 'hash')
- s'arrête avant d'atteindre le quota mensuel gratuit (MAX_CHARS, défaut 450000)
Variables : AZURE_SPEECH_KEY, AZURE_SPEECH_REGION, MAX_CHARS, ONLY (ex. "0,5,22"), TEST=1 (1 seul chapitre), DRY=1 (sans appel)
"""
import os, sys, json, glob, time, re, urllib.request, urllib.error
from xml.sax.saxutils import escape

VOICE = "fr-FR-VivienneMultilingualNeural"
FORMAT = "audio-16khz-32kbitrate-mono-mp3"   # 4000 octets/seconde
BPS = 4000
MAX_CHARS = int(os.environ.get("MAX_CHARS", "450000"))
KEY = os.environ.get("AZURE_SPEECH_KEY", "")
REGION = os.environ.get("AZURE_SPEECH_REGION", "")
DRY = os.environ.get("DRY") == "1"
TEST = os.environ.get("TEST") == "1"
ONLY = {int(x) for x in os.environ.get("ONLY", "").split(",") if x.strip()}
CHUNK = 3500  # caractères max par requête (10 min d'audio max côté Azure)

def chunks(text):
    if len(text) <= CHUNK: return [text]
    parts, cur = [], ""
    for s in re.split(r'(?<=[.;:!?]) ', text):
        if len(cur) + len(s) + 1 > CHUNK and cur:
            parts.append(cur); cur = s
        else:
            cur = (cur + " " + s).strip()
    if cur: parts.append(cur)
    return parts

def synth(text):
    if DRY: return b"\0" * (len(text) * 4)
    ssml = ('<speak version="1.0" xml:lang="fr-FR" xmlns="http://www.w3.org/2001/10/synthesis">'
            f'<voice name="{VOICE}">{escape(text)}</voice></speak>').encode("utf-8")
    url = f"https://{REGION}.tts.speech.microsoft.com/cognitiveservices/v1"
    for attempt in range(6):
        req = urllib.request.Request(url, data=ssml, method="POST", headers={
            "Ocp-Apim-Subscription-Key": KEY, "Content-Type": "application/ssml+xml",
            "X-Microsoft-OutputFormat": FORMAT, "User-Agent": "clinicum-audio"})
        try:
            with urllib.request.urlopen(req, timeout=120) as r:
                data = r.read()
            if len(data) > 500: return data
        except urllib.error.HTTPError as e:
            body = e.read()[:200]
            if e.code in (401, 403):
                sys.exit(f"Clé ou région refusée ({e.code}) : vérifiez les secrets. {body}")
            if e.code == 429 or e.code >= 500:
                time.sleep(10 * (attempt + 1)); continue
            sys.exit(f"Erreur Azure {e.code} : {body}")
        except Exception as e:
            time.sleep(10 * (attempt + 1))
    sys.exit("Azure ne répond pas après plusieurs essais")

def main():
    if not DRY and (not KEY or not REGION):
        sys.exit("Secrets AZURE_SPEECH_KEY / AZURE_SPEECH_REGION absents")
    os.makedirs("audio", exist_ok=True)
    idx_path = "audio/index.json"
    idx = json.load(open(idx_path)) if os.path.exists(idx_path) else {}
    used = 0
    todo = []
    for f in sorted(glob.glob("textes/[0-9]*.json")):
        r = json.load(open(f))
        if ONLY and r["id"] not in ONLY: continue
        if idx.get(str(r["id"]), {}).get("hash") == r["hash"]: continue
        todo.append(r)
    print(f"{len(todo)} fiche(s) à produire, budget {MAX_CHARS} caractères")
    for r in todo:
        need = sum(len(c["text"]) for c in r["chapters"])
        if not TEST and used + need > MAX_CHARS:
            print(f"Budget atteint avant la fiche {r['id']} ({r['name']}). Arrêt."); break
        d = f"audio/{r['id']:03d}"; os.makedirs(d, exist_ok=True)
        # nettoyer d'anciens chapitres d'une version précédente
        for old in glob.glob(d + "/*.mp3"): os.remove(old)
        info = []
        for i, c in enumerate(r["chapters"]):
            data = b"".join(synth(p) for p in chunks(c["text"]))
            if not DRY: time.sleep(3.2)  # F0 : ~20 requêtes/minute
            fn = f"{i:02d}-{c['key']}.mp3"
            open(f"{d}/{fn}", "wb").write(data)
            info.append({"key": c["key"], "title": c["title"], "file": fn, "sec": round(len(data) / BPS, 1), "bytes": len(data)})
            used += len(c["text"])
            if TEST: break
        if TEST:
            print("Essai réussi :", info[0]); return
        idx[str(r["id"])] = {"name": r["name"], "hash": r["hash"], "chars": need, "chapters": info}
        json.dump(idx, open(idx_path, "w"), ensure_ascii=False, indent=0)
        print(f"OK {r['id']:03d} {r['name']} ({need} car., total {used})", flush=True)
    done = len(idx)
    print(f"Terminé : {done}/232 fiches ont un audio ; {used} caractères utilisés dans ce lot")

main()
