import asyncio, os, subprocess, edge_tts
import edge_tts.communicate as _ec
VOL = os.environ.get("VOL", "+25%")
def _fr(*a, **k):
    text = a[-1]
    if isinstance(text, bytes): text = text.decode("utf-8")
    return ("<speak version='1.0' xmlns='http://www.w3.org/2001/10/synthesis' xml:lang='fr-FR'>"
            "<voice name='fr-CH-ArianeNeural'>"
            f"<prosody pitch='+0Hz' rate='+0%' volume='{VOL}'>" + text + "</prosody></voice></speak>")
_ec.mkssml = _fr
async def main():
    t = open("essai-voix/extrait.txt", encoding="utf-8").read().strip()
    os.makedirs("essai-voix/extrait", exist_ok=True)
    raw = "essai-voix/extrait/brut.mp3"
    await edge_tts.Communicate(t, "fr-CH-ArianeNeural").save(raw)
    # normalisation du volume : -14 LUFS (niveau vidéo/podcast fort), crête -1 dB
    subprocess.check_call(["ffmpeg","-y","-loglevel","error","-i",raw,"-af","loudnorm=I=-14:TP=-1.0:LRA=9","-ar","24000","-ac","1","-b:a","48k","essai-voix/extrait/Extrait-Ariane-plus-fort.mp3"])
    for f in (raw, "essai-voix/extrait/Extrait-Ariane-plus-fort.mp3"):
        out = subprocess.check_output(["ffmpeg","-i",f,"-af","volumedetect","-f","null","-"], stderr=subprocess.STDOUT).decode()
        print("NIVEAU", f, [l.strip() for l in out.splitlines() if "mean_volume" in l or "max_volume" in l])
    os.remove(raw)
asyncio.run(main())
