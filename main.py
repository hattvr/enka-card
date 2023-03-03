import asyncio

from generator import generate_image
from enkanetwork import EnkaNetworkAPI

client = EnkaNetworkAPI()

async def main():
    async with client:
        data = await client.fetch_user(843715177)
        for character in data.characters:
            await generate_image(character)
            exit()

asyncio.run(main())