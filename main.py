import asyncio

from enkanetwork import EnkaNetworkAPI, Language

from generator import generate_image

client = EnkaNetworkAPI(lang=Language.EN)
uid = 604905943


async def main():
    async with client:
        data = await client.fetch_user(uid)
        for character in data.characters:
            print(f"[{uid}] Generating enka-card for {character.name}")
            generate_image(data, character, client.lang)


asyncio.run(main())
