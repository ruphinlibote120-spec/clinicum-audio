import asyncio, edge_tts
async def main():
    vs = await edge_tts.list_voices()
    for v in vs:
        if v["Locale"].startswith("fr-"):
            print("VOIX", v["ShortName"], v["Gender"], v["Locale"], v.get("VoiceTag", {}).get("VoicePersonalities"), v.get("VoiceTag", {}).get("ContentCategories"), sep=" | ")
asyncio.run(main())
