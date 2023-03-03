import requests
import os

from collections import Counter
from typing import Literal, List
from pydantic import BaseModel

from enkanetwork.model.character import CharacterInfo
from enkanetwork.model.equipments import EquipmentsType
from enkanetwork.enum import EquipmentsType
from enkanetwork.model import Stats

from PIL import (
    ImageFont,
    Image,
    ImageChops,
    ImageOps,
)

from prop_reference import (
    RELIQUARY_STATS,
    ELEMENT_REFERENCE,
    ELEMENT_REFERENCE,
)


class ActiveSet(BaseModel):
    name: str
    count: int


def check_asset(path: str, asset_url: str) -> None:
    """ Helper function to check if an asset
    exists given a path and reference to the
    asset's source. If the asset does not exist,
    the asset will be downloaded from the source.
    """
    
    if not os.path.exists(path):
        os.makedirs(os.path.dirname(path), exist_ok=True)
        
        try:
            with open(path, "wb") as f:
                f.write(requests.get(asset_url).content)
        except:
            raise Exception("There was an error downloading the asset.")

def open_image(
    path: str, 
    asset_url: str = None,
    mode: str = "RGBA",
    resize: tuple = None,
    resample: int = Image.BICUBIC,
) -> Image:
    if not os.path.exists(path):
        check_asset(path, asset_url)

    image = Image.open(path)
    image = image.convert(mode)
    
    if resize:
        image = image.resize(resize, resample)
    
    return image


def scale_image(
    im: Image,
    fixed_height: int = None,
    fixed_width: int = None,
    fixed_percent: int = None,
) -> Image:
    if fixed_height:
        wpercent = fixed_height / float(im.size[1])
        wsize = int((float(im.size[0]) * float(wpercent)))
        return im.resize((wsize, fixed_height), Image.BICUBIC)
    elif fixed_width:
        hpercent = fixed_width / float(im.size[0])
        hsize = int((float(im.size[1]) * float(hpercent)))
        return im.resize((fixed_width, hsize), Image.BICUBIC)
    elif fixed_percent:
        return im.resize(
            (
                int(im.size[0] * (fixed_percent / 100)),
                int(im.size[1] * (fixed_percent / 100)),
            ),
            Image.BICUBIC,
        )


def get_font(font: Literal["normal"], size: int) -> ImageFont.FreeTypeFont:
    """Helper method to get a font."""
    return {
        "normal": ImageFont.truetype("attributes/Fonts/JA-JP.TTF", size),
        # Insert other fonts you'd like to use here, if any
    }.get(font, ImageFont.truetype("attributes/Fonts/JA-JP.TTF", size))


def fade_character_art(im: Image) -> Image:
    # Load mask from attributes
    mask = Image.open("attributes/Assets/enka_character_mask.png").convert("L")
    mask = mask.resize((im.size[0], im.size[1]), Image.NEAREST)

    # Extract alpha channel from original image
    alpha = im.split()[-1]

    # Apply mask to alpha channel
    new_alpha = ImageOps.invert(mask)
    alpha = ImageChops.multiply(alpha, new_alpha)

    # Composite modified alpha channel back onto original image
    result = im.copy()
    result.putalpha(alpha)

    return result


def fade_asset_icon(im: Image, _type: Literal["artifact"]) -> Image:
    mask_fp = {
        "artifact": "attributes/Assets/artifact_mask.png",
        # Insert other masks you'd like to use here, if any
    }.get(_type)

    mask = Image.open(mask_fp).convert("L")
    mask = mask.resize((im.size[0], im.size[1]), Image.NEAREST)

    overlay = Image.new("RGBA", im.size, (0, 0, 0, 0))
    overlay.paste(im, (0, 0), mask)

    return overlay


def get_active_artifact_sets(equipments: List[EquipmentsType]) -> List[ActiveSet]:
    set_counts = Counter(x.detail.artifact_name_set for x in equipments)
    active_sets = [ActiveSet(name=k, count=v) for k, v in set_counts.items() if v >= 2]
    active_sets.sort(key=lambda x: x.name)
    return active_sets


def get_stat_filename(icon: str) -> str:
    if icon in ELEMENT_REFERENCE:
        return ELEMENT_REFERENCE[icon]

    icon = icon.replace("FIGHT_PROP_BASE_", "")
    icon = icon.replace("FIGHT_PROP_ADD_", "")
    icon = icon.replace("FIGHT_PROP_", "")

    return icon


def format_statistics(char: CharacterInfo) -> dict[str, int]:
    """Format statistics for card, returns a dictionary
    of statistics ({name, value} pairs) with a
    maximum of 8 statistics."""

    stats = char.stats

    max_hp = "{:,}".format(stats.FIGHT_PROP_MAX_HP.to_rounded())
    base_hp = "{:,}".format(stats.BASE_HP.to_rounded())
    bonus_hp = "{:,}".format(round(stats.FIGHT_PROP_MAX_HP.value - stats.BASE_HP.value))

    max_atk = "{:,}".format(stats.FIGHT_PROP_CUR_ATTACK.to_rounded())
    base_atk = "{:,}".format(stats.FIGHT_PROP_BASE_ATTACK.to_rounded())
    bonus_atk = "{:,}".format(round(stats.FIGHT_PROP_CUR_ATTACK.value - stats.FIGHT_PROP_BASE_ATTACK.value))

    max_def = "{:,}".format(stats.FIGHT_PROP_CUR_DEFENSE.to_rounded())
    base_def = "{:,}".format(stats.FIGHT_PROP_BASE_DEFENSE.to_rounded())
    bonus_def = "{:,}".format(round(stats.FIGHT_PROP_CUR_DEFENSE.value - stats.FIGHT_PROP_BASE_DEFENSE.value))
    ret_stats = {
        "HP": f"{max_hp} ({base_hp} + {bonus_hp})",
        "ATK": f"{max_atk} ({base_atk} + {bonus_atk})",
        "DEF": f"{max_def} ({base_def} + {bonus_def})",
    }

    if stats.FIGHT_PROP_ELEMENT_MASTERY.value:
        ret_stats["Elemental Mastery"] = "{:,}".format(
            stats.FIGHT_PROP_ELEMENT_MASTERY.to_rounded()
        )

    for x in RELIQUARY_STATS:
        if getattr(stats, x).value:
            value = getattr(stats, x)
            ret_stats[RELIQUARY_STATS[x]] = (
                value.to_rounded()
                if isinstance(value, Stats)
                else value.to_percentage_symbol()
            )

    if len(ret_stats) > 8:
        # Who cares about these statistics
        ret_stats.pop("Healing Bonus", None)
        ret_stats.pop("Shield Strength", None)

    while len(ret_stats) > 8:
        # Handle damage bonuses if there are more than 8 statistics
        bonuses = []
        for item in ret_stats:
            if "DMG Bonus" in item:
                bonuses.append(float(ret_stats[item].replace("%", "")))

        # If all bonuses are the same, return whatever comes first
        if all(x == bonuses[0] for x in bonuses):
            for item in ret_stats.copy():
                if "DMG Bonus" in item and char.element.name not in item:
                    ret_stats[item] = ret_stats.pop(item)

            return {k: ret_stats[k] for k in list(ret_stats)[:8]}

        # Remove the lowest bonus in statistics
        for bonus in sorted(bonuses):
            if bonus != sorted(bonuses)[-1]:
                for item in ret_stats:
                    if (
                        "DMG Bonus" in item
                        and float(ret_stats[item].replace("%", "")) == bonus
                    ):
                        ret_stats.pop(item)
                        break
            else:
                break

        break

    return ret_stats
