import asyncio, os, subprocess, edge_tts
import edge_tts.communicate as _ec
V = "fr-FR-VivienneMultilingualNeural"
def _fr(*a, **k):
    text = a[-1]
    if isinstance(text, bytes): text = text.decode("utf-8")
    return ("<speak version='1.0' xmlns='http://www.w3.org/2001/10/synthesis' xml:lang='fr-FR'>"
            f"<voice name='{V}'><prosody pitch='+0Hz' rate='+0%' volume='+25%'>" + text + "</prosody></voice></speak>")
_ec.mkssml = _fr
async def main():
    t = open("essai-voix/extrait.txt", encoding="utf-8").read().strip()
    os.makedirs("essai-voix/extrait", exist_ok=True)
    raw = "essai-voix/extrait/brut.mp3"
    await edge_tts.Communicate(t, V).save(raw)
    subprocess.check_call(["ffmpeg","-y","-loglevel","error","-i",raw,"-af","loudnorm=I=-14:TP=-1.0:LRA=9","-ar","24000","-ac","1","-b:a","48k","essai-voix/extrait/Extrait-Vivienne-titres.mp3"])
    os.remove(raw)
asyncio.run(main())
