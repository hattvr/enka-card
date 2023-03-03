#  Enka.Network Card Generation (Python-Based)

<img src="https://cdn.discordapp.com/attachments/1014919079154425917/1081311454407442543/Hu_Tao_2023-03-03_15-25-26.png" width="100%"><br>

## About

A python-based card generation script that allows users to generate Enka.Network cards with ease.

## Project Stack

- [EnkaNetwork.py](https://github.com/mrwan200/EnkaNetwork.py) - Enka.Network API Wrapper
- [Pillow](https://github.com/python-pillow/Pillow) - Python Imaging Library

## Initial Setup

Install the required dependencies:

```shell
pip install -r requirements.txt
```

## Usage
Change the UID in `main.py` to your UID.
```python
import asyncio

from generator import generate_image
from enkanetwork import EnkaNetworkAPI

client = EnkaNetworkAPI()
uid = 604905943 # <- Change this to your UID

async def main():
    async with client:
        data = await client.fetch_user(uid)
        for character in data.characters:
            print(f"[{uid}] Generating enka-card for {character.name}")
            await generate_image(character)

asyncio.run(main())
```

Run the script:
```shell
python main.py
```



Your character cards will be output in the `/output` directory. Happy generating!
