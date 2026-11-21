import asyncio, json, os, edge_tts
import edge_tts.communicate as _ec
CUR = {"v": ""}
def _fr(*a, **k):
    text = a[-1]
    if isinstance(text, bytes): text = text.decode("utf-8")
    return ("<speak version='1.0' xmlns='http://www.w3.org/2001/10/synthesis' xml:lang='fr-FR'>"
            f"<voice name='{CUR['v']}'><prosody pitch='+0Hz' rate='+0%' volume='+0%'>" + text + "</prosody></voice></speak>")
_ec.mkssml = _fr
VOICES = {"Vivienne": "fr-FR-VivienneMultilingualNeural", "Denise": "fr-FR-DeniseNeural", "Eloise": "fr-FR-EloiseNeural", "Henri": "fr-FR-HenriNeural"}
async def main():
    os.makedirs("essai-voix/compare", exist_ok=True)
    for vid in (0, 5, 22):
        r = json.load(open(f"essai-voix/textes/{vid:03d}.json"))
        intro = r["chapters"][0]["text"]
        sect = r["chapters"][1]["text"][:600]
        text = intro + " " + sect
        for nom, v in VOICES.items():
            CUR["v"] = v
            p = f"essai-voix/compare/{nom}-{vid:03d}.mp3"
            for k in range(3):
                try:
                    await edge_tts.Communicate(text, v).save(p)
                    if os.path.getsize(p) > 1000: break
                except Exception as e:
                    print("retry", p, e)
asyncio.run(main())
