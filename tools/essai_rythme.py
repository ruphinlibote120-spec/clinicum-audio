#!/usr/bin/env python3
"""Essai : compare l'ancien rythme (débit normal, pauses du moteur) et les nouveaux (débit ralenti, pauses allongées) sur un même extrait.
Affiche durée, vitesse de parole et pauses. Les mp3 sont déposés dans essai/ pour être écoutés."""
import asyncio, json, os, re, subprocess, sys
sys.path.insert(0, "tools")
import gen_edge as g

def stats(nom, rate, text, out):
    sec = g._dur(out)
    sil = [b - a for a, b in g.silences(out, d=0.3)]
    parole = sec - sum(sil)
    print(f"{nom:10s} débit {rate:5s} durée {sec:6.1f} s | parole {parole:5.1f} s = {len(text)/parole:4.1f} car/s | pauses≥0,3 s : {len(sil):3d}, total {sum(sil):5.1f} s, moyenne {sum(sil)/max(1,len(sil)):4.2f} s, plus longue {max(sil) if sil else 0:4.2f} s", flush=True)

async def run(nom, rate, pause, text, brut=False):
    g.RATE = rate; g._P.update(pause)
    base = f"essai/{nom}"
    await g.synth(text, base + ".raw.mp3")
    subprocess.check_call(["ffmpeg", "-y", "-loglevel", "error", "-i", base + ".raw.mp3", "-ar", "24000", "-ac", "1", "-c:a", "pcm_s16le", base + ".raw.wav"])
    out = base + ".mp3"
    if brut:   # ancien traitement : aucune pause ajoutée
        subprocess.check_call(["ffmpeg", "-y", "-loglevel", "error", "-i", base + ".raw.wav", "-af", "loudnorm=I=-14:TP=-1.0:LRA=9", "-ar", "24000", "-ac", "1", "-b:a", "40k", out])
        os.remove(base + ".raw.wav")
    else:
        g.assemble([base + ".raw.wav"], out, base); os.remove(base + ".raw.wav")
    os.remove(base + ".raw.mp3")
    stats(nom, rate, text, out)

async def main():
    os.makedirs("essai", exist_ok=True)
    d = json.load(open("textes/000.json"))
    ch = [c for c in d["chapters"] if c["key"] == "pts"][0]
    text = ch["text"][:1500].rsplit(". ", 1)[0] + "."
    print("extrait :", len(text), "caractères")
    await run("A-ancien", "+0%", {}, text, brut=True)
    await run("B-pauses", "+0%", {}, text)
    await run("C-lent12", "-12%", {}, text)
    await run("D-lent15", "-15%", dict(s=1.0, t=1.4, c=0.2), text)
asyncio.run(main())
