import textwrap
import os
import re

from datetime import datetime

from enkanetwork.model.character import CharacterInfo
from enkanetwork.model.equipments import EquipmentsType, EquipType, Equipments
from enkanetwork.enum import EquipmentsType, DigitType

from PIL import Image, ImageDraw, ImageEnhance, ImageChops

from prop_reference import (
    ICON_REFERENCE,
    SUBST_ORDER
)

from utils import (
    check_asset,
    format_statistics,
    fade_character_art,
    fade_asset_icon,
    get_active_artifact_sets,
    get_font,
    get_stat_filename,
    open_image,
    scale_image
)

async def generate_image(character: CharacterInfo):
    """ COLORS """
    GREEN = (150, 255, 169)
    WHITE = (255, 255, 255)
    LIGHTER_GREY = (255, 255, 255, 150)
    BEIGE = (245, 222, 179)
    
    """ BACKGROUND SETUP """
    background = open_image("attributes/Assets/default_enka_card.png")
    
    background_rgb = {
        "Pyro": (186, 140, 131),
        "Hydro": (132, 161, 198),
        "Dendro": (45, 142, 52),
        "Electro": (152, 118, 173),
        "Anemo": (82, 176, 177),
        "Cryo": (70, 168, 186),
        "Geo": (187, 159, 75),
    }.get(character.element.name, (255, 255, 255, 50))
    
    background_color = Image.new("RGBA", background.size, background_rgb)
    background = ImageChops.overlay(background_color, background)
    
    
    foreground = Image.new("RGBA", background.size, (0, 0, 0, 0))
    textground = Image.new("RGBA", background.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(textground)
    
    """ FIRST TRIMESTER """   
    character_art = open_image(
        path=f"attributes/Genshin/Gacha/{character.image.banner.filename}.png",
        asset_url=character.image.banner.url
    )
    character_art = scale_image(character_art, fixed_percent=90)
    character_art = character_art.crop((615, 85, character_art.width, character_art.height))
    character_art = await fade_character_art(character_art)
    
    foreground.paste(character_art, (0, 0), character_art)
    
    character_shade = open_image("attributes/Assets/enka_character_shade.png")
    foreground.paste(character_shade, (0, 0), character_shade)
    
    w = int(draw.textlength(f"{character.name}", font=get_font("normal", 30)))
    draw.text(
        (38, 35),
        f"{character.name}",
        font=get_font("normal", 30),
        fill=WHITE,
        anchor="lt"
    )

    draw.polygon(
        [
            (38 + w + 15, 53),
            (38 + w + 15 + 6, 53),
            (38 + w + 15 + 3, 53 - 5),
        ],
        fill=(255, 255, 255, 200)
    )

    draw.text(
        (38 + w + 35, 51),
        f"hatter",
        fill=(255, 255, 255, 200),
        anchor="lm",
        font=get_font("normal", 16),
    )

    info_gap = 220
    
    draw.text(
        (38, info_gap + 325),
        f"UID: 123123123",
        font=get_font("normal", 18),
    )
    
    w = draw.textlength(f"WL7", font=get_font("normal", 18))
    w2 = draw.textlength(f"AR56", font=get_font("normal", 18))
    draw.text(
        (38, info_gap + 350),
        f"WL7",
        font=get_font("normal", 18),
    )
    
    draw.rounded_rectangle(
        (
            38 + w + 8,
            info_gap + 348,
            38 + w + 8 + w2 + 10,
            info_gap + 372
        ),
        fill=(0, 0, 0, 125),
        radius=3
    )
    
    draw.text(
        (38 + w + 8 + 5, info_gap + 350),
        f"AR56",
        font=get_font("normal", 18),
        fill=BEIGE
    )
    
    w = int(draw.textlength(f"Lv. {character.level}/", font=get_font("normal", 23)))
    draw.text((38, 49 + 27), f"Lv. {character.level}/", font=get_font("normal", 23))
    
    draw.text(
        (38 + w, 49 + 27),
        f"{character.max_level}",
        fill=LIGHTER_GREY,
        font=get_font("normal", 23),
    )
    
    friendship_icon = open_image("attributes/UI/COMPANIONSHIP.png")
    friendship_icon = scale_image(friendship_icon, fixed_height=45)
    foreground.paste(friendship_icon, (34, 108), friendship_icon)
    draw.text((80, 130), f"{character.friendship_level}", font=get_font("normal", 23), anchor="lm")

    """ Constellations Section """
    c_overlay = open_image("attributes/Assets/enka_constellation_overlay.png")
    c_overlay = scale_image(c_overlay, fixed_height=75)
    ImageDraw.Draw(c_overlay).ellipse((15, 15, 59, 59), fill=(50, 50, 50, 150), outline=background_rgb, width=2)
    lock = open_image("attributes/UI/LOCKED.png", resize=(20,25))

    constellation_starting_index = 160
    for index, constellation in enumerate(character.constellations):
        foreground.paste(c_overlay, (25, constellation_starting_index + 60*index), c_overlay)
        constellation_icon = open_image(
            path=f"attributes/Genshin/UI/{constellation.icon.filename}.png",
            asset_url=constellation.icon.url
        )
        constellation_icon = scale_image(constellation_icon, fixed_height=45)
        
        if index >= character.constellations_unlocked:
            f = ImageEnhance.Brightness(constellation_icon)
            constellation_icon = f.enhance(0.4)
            constellation_icon.paste(lock, (13, 8), lock)
        else:
            for _ in range(2):
                foreground.paste(
                    constellation_icon, 
                    (int(63 - (constellation_icon.size[0] / 2)), constellation_starting_index + 15 + 60*index), 
                    constellation_icon
                )
                
        foreground.paste(
            constellation_icon, 
            (int(63 - (constellation_icon.size[0] / 2)), constellation_starting_index + 15 + 60*index), 
            constellation_icon
        )


    """ Talents Section """
    talent_overlay = open_image(f"attributes/Assets/enka_talent_overlay.png")
    talent_overlay = scale_image(talent_overlay, fixed_height=80)
    
    for index, skill in enumerate(character.skills):
        for _ in range(4):
            foreground.paste(talent_overlay, (430, 305 + 90 * index), talent_overlay)
        
        sk = open_image(
            path=f"attributes/Genshin/UI/{skill.icon.filename}.png", 
            asset_url=skill.icon.url,
            resize=(50, 50)
        )

        for _ in range(3):
            foreground.paste(sk, (int(471 - (sk.size[0] / 2)), 320 + 90 * index), sk)

        w = int(draw.textlength(str(skill.level), font=get_font("normal", 20)))
        ImageDraw.Draw(foreground, "RGBA").rounded_rectangle(
            (471 - w / 2 - 6, 382 + 90 * index - 15, 471 + w / 2 + 6, 382 + 90 * index + 15),
            radius=15,
            fill=(50, 50, 50, 178) if not skill.is_boosted else (79, 188, 212)
        )

        ImageDraw.Draw(foreground, "RGBA").text(
            (472, 383 + 90 * index),
            f"{skill.level}",
            font=get_font("normal", 20),
            anchor="mm"
        )

    weapon = character.equipments[-1]
    weapon_image = open_image(
        path=f"attributes/Genshin/Weapon/{weapon.detail.icon.filename}.png",
        asset_url=weapon.detail.icon.url
    )
    weapon_image = scale_image(weapon_image, fixed_height=125)
    
    foreground.paste(weapon_image, (555, 25), weapon_image)
    
    rarity_light = scale_image(
        open_image(f"attributes/UI/{ICON_REFERENCE[str(weapon.detail.rarity)]}_WEAPON_LIGHT.png"),
        fixed_height=40
    )
    foreground.paste(rarity_light, (int(625 - (rarity_light.size[0] / 2)), 130), rarity_light)
    
    rarity = scale_image(
        open_image(f"attributes/UI/{ICON_REFERENCE[str(weapon.detail.rarity)]}.png"), 
        fixed_height=25
    )
    
    dark_shadow = ImageEnhance.Brightness(rarity).enhance(0)
    foreground.paste(dark_shadow, (int(625 - (rarity.size[0] / 2)), 135 + 2), dark_shadow)
    foreground.paste(rarity, (int(625 - (rarity.size[0] / 2)), 135), rarity)
    
    weapon_length = int(draw.textlength(f"{weapon.detail.name}", font=get_font("normal", 22)))
    
    async def draw_weapon_information(line_buffer: int = 0):
        # Weapon Main Stat
        mainstat = weapon.detail.mainstats
        w = int(
            draw.textlength(
                f"{mainstat.value}{'%' if mainstat.type == DigitType.PERCENT else ''}",
                font=get_font("normal", 22),
            )
        )

        endpoint = 690 + 20 + 35 + w

        ImageDraw.Draw(foreground, "RGBA").rounded_rectangle(
            (690, 60 + line_buffer, endpoint, 95 + line_buffer), fill=(235, 235, 235, 40), radius=4
        )

        image = open_image(f"attributes/UI/{get_stat_filename(mainstat.prop_id)}.png")
        icon_file = scale_image(image, fixed_height=30)
        icon_file = ImageEnhance.Brightness(icon_file).enhance(2)
        
        for _ in range(3):
            textground.paste(icon_file, (695, 63 + line_buffer), icon_file)

        draw.text(
            (735, 65 + line_buffer),
            f"{mainstat.value}{'%' if mainstat.type == DigitType.PERCENT else ''}",
            font=get_font("normal", 22),
            anchor = "la"
        )
        
        # Weapon Bonus
        substat = weapon.detail.substats
        if substat:
            substat = substat[0]

            w = int(
                draw.textlength(
                    f"{substat.value}{'%' if substat.type == DigitType.PERCENT else ''}",
                    font=get_font("normal", 22),
                )
            )

            ImageDraw.Draw(foreground, "RGBA").rounded_rectangle(
                (endpoint + 10, 60 + line_buffer, endpoint + 10 + 20 + 35 + w, 95 + line_buffer),
                fill=(235, 235, 235, 40),
                radius=4,
            )

            image = open_image(f"attributes/UI/{get_stat_filename(substat.prop_id)}.png")
            icon_file = scale_image(image, fixed_height=30)
            icon_file = ImageEnhance.Brightness(icon_file).enhance(2)
            
            for _ in range(3):
                textground.paste(icon_file, (int(endpoint + 15), 63 + line_buffer), icon_file)

            draw.text(
                (endpoint + 55, 65 + line_buffer),
                f"{substat.value}{'%' if substat.type == DigitType.PERCENT else ''}",
                font=get_font("normal", 22),
                anchor="la"
            )
        
        w = int(
            draw.textlength(
                f"R{weapon.refinement}",
                font=get_font("normal", 22),
            )
        )

        endpoint = 690 + 20 + w

        ImageDraw.Draw(foreground, "RGBA").rounded_rectangle(
            (690, 60 + 45 + line_buffer, endpoint, 95 + 40 + line_buffer), 
            fill=(0, 0, 0, 100), 
            radius=4
        )
        
        draw.text(
            (690 + 10, 60 + 45 + 2 + line_buffer),
            f"R{weapon.refinement}",
            font=get_font("normal", 22),
            fill=(245, 222, 179)
        )
        
        w = int(
            draw.textlength(
                f"Lv. {weapon.level}/{weapon.max_level}",
                font=get_font("normal", 22),
            )
        )
        
        ImageDraw.Draw(foreground, "RGBA").rounded_rectangle(
            (endpoint + 10, 60 + 45 + line_buffer, endpoint + 30 + w, 95 + 40 + line_buffer), 
            fill=(0, 0, 0, 100), 
            radius=4
        )
        
        w = int(
            draw.textlength(
                f"Lv. {weapon.level}/",
                font=get_font("normal", 22),
            )
        )
        
        draw.text(
            (endpoint + 20, 60 + 45 + 2 + line_buffer),
            f"Lv. {weapon.level}/",
            font=get_font("normal", 22),
        )
        
        draw.text(
            (endpoint + 20 + w, 60 + 45 + 2 + line_buffer),
            f"{weapon.max_level}",
            font=get_font("normal", 22),
            fill=(255, 255, 255, 150)
        )
        
        return
    
    if weapon_length < 295:
        draw.text(
            (690, 32),
            f"{weapon.detail.name}",
            font=get_font("normal", 22),
            anchor="lt"
        )
        
        await draw_weapon_information(line_buffer=5)
    else:
        weapon_name = textwrap.wrap(f"{weapon.detail.name}", width=20)
        
        for index, line in enumerate(weapon_name):
            draw.text(
                (690, 32 + (index * 25)),
                line,
                font=get_font("normal", 22),
                anchor="lt"
            )

        await draw_weapon_information(line_buffer=28*index)
            
    all_stats = format_statistics(character)
    statistic_buffer = 365 // len(all_stats)
    for index, item in enumerate(all_stats):
        """Draw Icon for Stat"""
        image = open_image(f"attributes/UI/{ICON_REFERENCE.get(item, item)}.png")
        icon_file = scale_image(image, fixed_height=30)
        icon_file = ImageEnhance.Brightness(icon_file).enhance(2)
        
        for _ in range(3):
            foreground.paste(icon_file, (555, 180 + (index * statistic_buffer)), icon_file)
        
        """ Write Stat Name """
        draw.text(
            (603, 183 + (index * statistic_buffer)), 
            item, 
            font=get_font("normal", 20)
        )

        """ Write Stat Info """
        if item in ["HP", "ATK", "DEF"]:
            pattern = r'([\d,]+)\s*\(([\d,]+)\s*\+\s*([\d,]+)\)'
            match = re.match(pattern, all_stats[item])
            stat_values = [match.group(1), match.group(2), match.group(3)]
            
            draw.text(
                (967, 183 - 10 + (index * statistic_buffer)),
                stat_values[0],
                font=get_font("normal", 20),
                anchor="ra",
            )
            
            w = draw.textlength(f"+{stat_values[2]}", font=get_font("normal", 12))
            draw.text(
                (967, 183 + 12 + (index * statistic_buffer)),
                f"+{stat_values[2]}",
                font=get_font("normal", 12),
                anchor="ra",
                fill=(150, 255, 169, 200)
            )
            
            draw.text(
                (967 - w - 5, 183 + 12 + (index * statistic_buffer)),
                f"{stat_values[1]}",
                font=get_font("normal", 12),
                anchor="ra",
                fill=(255, 255, 255, 200)
            )
        else:
            draw.text(
                (967, 183 + (index * statistic_buffer)),
                str(all_stats[item]),
                font=get_font("normal", 20),
                anchor="ra",
            )
        
    positions = [
        "EQUIP_BRACER",
        "EQUIP_NECKLACE",
        "EQUIP_SHOES",
        "EQUIP_RING",
        "EQUIP_DRESS",
    ]

    artifacts = filter(lambda x: x.type == EquipmentsType.ARTIFACT, character.equipments)
    artifact_spacer = 119
    for artif_index, equipment_type in enumerate(positions):
        artifact: Equipments = next(filter(lambda x: x.detail.artifact_type.value == EquipType(equipment_type), artifacts), None)
        
        ImageDraw.Draw(foreground, "RGBA").rounded_rectangle(
            (
                1009, 
                14 + artifact_spacer*artif_index, 
                1009 + 440, 
                14 + 105 + artifact_spacer*artif_index
            ),
            fill=(0, 0, 0, 60) if artifact else (0, 0, 0, 25),
            radius=5,
        )
        
        if not artifact:
            continue

        artif_icon = await fade_asset_icon(
            open_image(
                path=f"attributes/Genshin/Artifact/{artifact.detail.icon.filename}.png", 
                asset_url=artifact.detail.icon.url,
                resize=(190, 190)),
            "artifact",
        )
        artif_icon = artif_icon.crop((40, 40, 146, 146))
        foreground.paste(artif_icon, (1009, 14 + artifact_spacer*artif_index), artif_icon)

        draw.line(
            (1175, 14 + 10 + artifact_spacer*artif_index, 1175, 14 + 105 - 10 + artifact_spacer*artif_index),
            fill=(255, 255, 255, 25),
            width=2
        )

        image = open_image(f"attributes/UI/{get_stat_filename(artifact.detail.mainstats.prop_id)}.png")
        icon_file = scale_image(image, fixed_height=30)
        icon_file = ImageEnhance.Brightness(icon_file).enhance(2)

        for _ in range(3):
            foreground.paste(icon_file, (1125, 25 + artifact_spacer*artif_index), icon_file)

        mainstat = artifact.detail.mainstats
        draw.text(
            (1150, 60 + artifact_spacer*artif_index),
            f"{('{:,}'.format(mainstat.value))}{'%' if mainstat.type == DigitType.PERCENT else ''}",
            anchor="rt",
            font=get_font("normal", 27),
            fill=WHITE,
        )
        
        w = draw.textlength(f"+{artifact.level}", font=get_font("normal", 12))
        
        ImageDraw.Draw(foreground, "RGBA").rounded_rectangle(
            (1150 - w - 8, 60 + 30 + artifact_spacer*artif_index, 1150, 60 + 31 + 15 + artifact_spacer*artif_index),
            fill=(0, 0, 0, 175),
            radius=3,
        )
        
        draw.text(
            (1150 - 2, 60 + 32 + artifact_spacer*artif_index),
            f"+{artifact.level}",
            anchor="rt",
            font=get_font("normal", 14),
            fill=WHITE
        )
        
        rarity = scale_image(
            open_image(f"attributes/UI/{ICON_REFERENCE[str(artifact.detail.rarity)]}.png"), 
            fixed_height=18
        )
        
        dark_shadow = ImageEnhance.Brightness(rarity).enhance(0)
        textground.paste(dark_shadow, (1035, 90 + artifact_spacer*artif_index), dark_shadow)
        
        textground.paste(rarity, (1035, 88 + artifact_spacer*artif_index), rarity)
        
        """ Artifact Substats """      
        artifact.detail.substats.sort(key=lambda x: SUBST_ORDER.index(x.prop_id))
        for index, subst in enumerate(artifact.detail.substats):
            """Draw Icon for Subtat"""
            
            position = {
                0: [0, 0], 
                1: [1, 0], 
                2: [0, 1], 
                3: [1, 1]
            }.get(index)
            
            image = open_image(f"attributes/UI/{get_stat_filename(subst.prop_id)}.png")
            icon_file = scale_image(image, fixed_height=30)
            icon_file = ImageEnhance.Brightness(icon_file).enhance(2)

            foreground.paste(
                icon_file,
                (
                    1190 + 125*position[1], 
                    30 + artifact_spacer*artif_index + 45*position[0]
                ),
                icon_file,
            )

            """ Draw Substat Value """
            draw.text(
                (
                    1220 + 125*position[1],
                    32 + artifact_spacer*artif_index + 45*position[0]
                ),
                f" +{('{:,}'.format(subst.value))}{'%' if subst.type == DigitType.PERCENT else ''}",
                fill=WHITE,
                font=get_font("normal", 20),
            )
        

    ImageDraw.Draw(foreground, "RGBA").rounded_rectangle(
        (555, 547, 555 + 48, 547 + 48),
        fill=(0, 0, 0, 50),
        radius=5
    )
    
    flower_of_life = open_image("attributes/Assets/flower_of_life_icon.png", resize=(35, 35))
    foreground.paste(flower_of_life, (562, 555), flower_of_life)

    """ Activated Sets Section """
    active_sets = get_active_artifact_sets(character.equipments)
    if len(active_sets) > 1:
        """Two Activated Sets"""
        for set_index, artifact_set in enumerate(active_sets):
            draw.text(
                (770, 560 + 25 * set_index),
                f"{artifact_set.name}",
                fill=GREEN,
                anchor="mm",
                font=get_font("normal", 17),
            )

            ImageDraw.Draw(foreground, "RGBA").rounded_rectangle(
                (935, 548 + 25 * set_index, 935 + 30, 548 + 21 + 25 * set_index),
                fill=(0, 0, 0, 50),
                radius=3,
            )

            draw.text(
                (951, 560 + 25 * set_index),
                f"{artifact_set.count}",
                fill=WHITE,
                anchor="mm",
                font=get_font("normal", 17)
            )

            set_index += 1
    elif len(active_sets) == 1:
        """Single Activated Set"""
        ImageDraw.Draw(foreground, "RGBA").rounded_rectangle(
            (935, 548 + 12, 935 + 30, 548 + 21 + 12),
            fill=(0, 0, 0, 50),
            radius=3,
        )

        draw.text(
            (770, 572),
            [set for set in active_sets][0].name,
            fill=GREEN,
            anchor="mm",
            font=get_font("normal", 17),
        )

        draw.text(
            (951, 571),
            str([set for set in active_sets][0].count),
            fill=WHITE,
            anchor="mm",
            font=get_font("normal", 17),
        )
    else:
        """No Activated Sets"""
        ImageDraw.Draw(foreground, "RGBA").rounded_rectangle(
            (935, 548 + 12, 935 + 30, 548 + 21 + 12),
            fill=(0, 0, 0, 50),
            radius=3,
        )

        draw.text(
            (770, 572),
            "No Activated Bonuses",
            fill=GREEN,
            anchor="mm",
            font=get_font("normal", 17),
        )

        draw.text(
            (951, 571),
            "0",
            fill=WHITE,
            anchor="mm",
            font=get_font("normal", 17),
        )
    
    if not os.path.exists("output"):
        os.makedirs("output")
    
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    filename = f"{character.name}_{timestamp}"
    
    foreground = Image.alpha_composite(foreground, textground)
    Image.alpha_composite(background, foreground).save(
        f"output/{filename}.png", format="png"
    )
    
    return