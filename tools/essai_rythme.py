#!/usr/bin/env python3
"""Essai : compare l'ancien rythme (débit normal, sans pauses) et le nouveau (débit ralenti, pauses) sur un même extrait.
Affiche durée, nombre de silences et silence total. Les mp3 sont déposés dans essai/ pour être écoutés."""
import asyncio, json, os, re, subprocess, sys
sys.path.insert(0, "tools")
import gen_edge as g

def silences(path):
    r = subprocess.run(["ffmpeg", "-i", path, "-af", "silencedetect=noise=-38dB:d=0.3", "-f", "null", "-"], capture_output=True, text=True).stderr
    d = [float(x) for x in re.findall(r"silence_duration: ([\d.]+)", r)]
    return len(d), round(sum(d), 1), round(max(d), 2) if d else 0

async def run(nom, rate, pause, text):
    g.RATE = rate; g._P.update(pause)
    raw = f"essai/{nom}.raw.mp3"
    await g.synth(g.titre(text), raw)
    out = f"essai/{nom}.mp3"
    subprocess.check_call(["ffmpeg", "-y", "-loglevel", "error", "-i", raw, "-af", "loudnorm=I=-14:TP=-1.0:LRA=9", "-ar", "24000", "-ac", "1", "-b:a", "40k", out])
    os.remove(raw)
    sec = float(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", out]).decode())
    n, tot, mx = silences(out)
    print(f"{nom:12s} débit {rate:5s} durée {sec:6.1f} s  silences≥0,3 s : {n:3d}  total {tot:5.1f} s  plus long {mx} s", flush=True)

async def main():
    os.makedirs("essai", exist_ok=True)
    d = json.load(open("textes/000.json"))
    ch = [c for c in d["chapters"] if c["key"] == "pts"][0]
    text = ch["text"][:1500].rsplit(". ", 1)[0] + "."
    print("extrait :", len(text), "caractères")
    z = dict(s=0, c=0, t=0, e=0)
    await run("A-ancien", "+0%", z, text)
    await run("B-pauses", "+0%", dict(s=500, c=250, t=900, e=500), text)
    await run("C-lent12", "-12%", dict(s=500, c=250, t=900, e=500), text)
    await run("D-lent15", "-15%", dict(s=550, c=300, t=1000, e=600), text)
asyncio.run(main())
