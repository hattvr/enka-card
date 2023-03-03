import asyncio

from generator import generate_image
from enkanetwork import EnkaNetworkAPI

client = EnkaNetworkAPI()
uid = 604905943

async def main():
    async with client:
        data = await client.fetch_user(uid)
        for character in data.characters:
            print(f"[{uid}] Generating enka-card for {character.name}")
            await generate_image(character)

asyncio.run(main())