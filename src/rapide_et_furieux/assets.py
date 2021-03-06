#!/usr/bin/env python3
from pkg_resources import resource_filename

import pygame


TILE_SIZE = (128, 128)
BONUS_SIZE = (34, 34)

BACKGROUND_LAYER = -1
RACE_TRACK_LAYER = 50
WEAPONS_LAYER = 75
RACE_TRACK_MINIATURE_LAYER = 100
ELEMENT_SELECTOR_LAYER = 150
ELEMENT_SELECTOR_ARROWS_LAYER = 160
WEAPON_SELECTOR_LAYER = 150
OSD_LAYER = 250
CONSOLE_LAYER = 300
MOUSE_CURSOR_LAYER = 500


ARROW_UP = ("rapide_et_furieux.gfx.ui", "arrowUp.png")
ARROW_DOWN = ("rapide_et_furieux.gfx.ui", "arrowDown.png")
RED_LINE = ("rapide_et_furieux.gfx.ui", "red_line.png")
GREEN_RECT = ("rapide_et_furieux.gfx.ui", "green_rect.png")
BLUE_DOT = ("rapide_et_furieux.gfx.ui", "blue_dot.png")

UI = {
    ARROW_UP,
    ARROW_DOWN,
    RED_LINE,
    GREEN_RECT,
    BLUE_DOT,
}

MUSICS = {
    ("rapide_et_furieux.music", "398640__jammerboy70__cyber-race.ogg",
     0.1, 126),
    ("rapide_et_furieux.music", "Title Theme.ogg", 0.1, 43),
    ("rapide_et_furieux.music", "Great Boss.ogg", 0.1, 110),
    ("rapide_et_furieux.music", "fight_looped.ogg", 0.1, 24),
    ("rapide_et_furieux.music", "S31-Winning the Race.ogg", 0.1, 139),
}

ENGINE = ("rapide_et_furieux.sounds", "loop_5.ogg", 0.7)
TIRES = ("rapide_et_furieux.sounds", "tires.ogg", 0.3)
SKIDMARKS = {
    ("rapide_et_furieux.gfx.cars", "skidmark_long_%d.png" % idx)
    for idx in range(1, 4)
}
SKIDMARK_OIL = ("rapide_et_furieux.gfx.cars", "skidmark_oil.png")

SOUNDS = {
    'laser': {
        ("rapide_et_furieux.sounds", "laser%d.ogg" % idx, 1.0)
        for idx in range(1, 10)
    },
    'machinegun': {
        ("rapide_et_furieux.sounds",
         "170167__timgormly__8-bit-machine-gun.ogg", 0.3),
    },
    'click': {
        ("rapide_et_furieux.sounds", "click%d.ogg" % idx, 1.0)
        for idx in range(1, 6)
    },
    'powerUp': {
        ("rapide_et_furieux.sounds", "powerUp%d.ogg" % idx, 1.0)
        for idx in range(1, 10)
    },
    'explosion': [
        ("rapide_et_furieux.sounds", "rumble%d.ogg" % idx, 0.3)
        for idx in range(1, 4)
    ] + [
        ("rapide_et_furieux.sounds", "170146__timgormly__8-bit-explosion.ogg",
         0.5),
        ("rapide_et_furieux.sounds",
         "259962__thehorriblejoke__8-bit-explosion.ogg", 0.5),
        ("rapide_et_furieux.sounds",
         "8bit_bomb_explosion.ogg", 0.5),
        ("rapide_et_furieux.sounds",
         "synthetic_explosion_1.ogg", 0.5),
    ],
}

COUNTDOWNS = {
    sex: {
        idx:
        (
            "rapide_et_furieux.sounds.%s" % sex,
            "%d.ogg" % idx if idx > 0 else "go.ogg",
            1.0
        )
        for idx in range(0, 11)
    }
    for sex in ['male', 'female']
}

CAR_SCALE_FACTOR = 0.66
CARS = [
    ("rapide_et_furieux.gfx.cars", "car_%s_%d.png" % (color[0], idx), color[1])
    for idx in range(1, 6)
    for color in [
        ('black', (0, 0, 0)),
        ('blue', (0, 0, 255)),
        ('green', (0, 255, 0)),
        ('red', (255, 0, 0)),
        ('yellow', (255, 255, 0)),
    ]
]

BARRELS = [
    ("rapide_et_furieux.gfx.weapons",
     "barrel%s_outline.png" % (color[0]), color[1])
    for color in [
        ('Black', (0, 0, 0)),
        ('Blue', (0, 0, 255)),
        ('Green', (0, 255, 0)),
        ('Red', (255, 0, 0)),
        ('Beige', (255, 255, 0)),
    ]
]

BULLET = ("rapide_et_furieux.gfx.weapons", "bulletBeigeSilver_outline.png")
BULLETS = {
    color[1]:
    ("rapide_et_furieux.gfx.weapons",
     "bullet%sSilver_outline.png" % (color[0]), color[1])
    for color in [
        ('Blue', (0, 0, 255)),
        ('Green', (0, 255, 0)),
        ('Red', (255, 0, 0)),
        ('Silver', (128, 128, 128)),
        ('Beige', (100, 100, 100)),
        ('Yellow', (255, 255, 0)),
    ]
}

GUNS = [
    ("rapide_et_furieux.gfx.weapons", "gun%02d.png" % (idx))
    for idx in range(0, 11)
]
GUN_LASER = ("rapide_et_furieux.gfx.weapons", "gun02.png")
GUN_MACHINEGUN = ("rapide_et_furieux.gfx.weapons", "gun05.png")
GUN_MISSILE = ("rapide_et_furieux.gfx.weapons", "gun01.png")
GUN_TANKSHELL = ("rapide_et_furieux.gfx.weapons", "gun06.png")

CROSSAIRS = {
    color[1]:
    ("rapide_et_furieux.gfx.weapons",
     "crossair_%s.png" % (color[0]), color[1])
    for color in [
        ('black', (0, 0, 0)),
        ('blue', (0, 0, 255)),
        ('red', (255, 0, 0)),
        ('white', (255, 255, 255)),
    ]
}

LASERS = {
    (0, 0, 255): ("rapide_et_furieux.gfx.weapons", "laserBlue16.png"),
    (0, 255, 0): ("rapide_et_furieux.gfx.weapons", "laserGreen10.png"),
    (255, 0, 0): ("rapide_et_furieux.gfx.weapons", "laserRed16.png"),
}

MISSILE = ("rapide_et_furieux.gfx.weapons", "spr_missile.png")

SCRATCHS = [
    ("rapide_et_furieux.gfx.weapons", "scratch%d.png" % (idx))
    for idx in range(1, 4)
]

SHIELD = ("rapide_et_furieux.gfx.weapons", "shield3.png")
SHIELDS = [
    ("rapide_et_furieux.gfx.weapons", "shield%d.png" % (idx))
    for idx in range(1, 4)
]

TURRET_BASE = ("rapide_et_furieux.gfx.weapons", "turretBase_small.png")

OIL = ("rapide_et_furieux.gfx.objects", "oil.png")
MINE = ("rapide_et_furieux.gfx.weapons", "ballBlack_07.png")

MOTORCYCLES = [
    ("rapide_et_furieux.gfx.cars", "motorcycle_%s.png" % (color[0]), color[1])
    for color in [
        ('black', (0, 0, 0)),
        ('blue', (0, 0, 255)),
        ('green', (0, 255, 0)),
        ('red', (255, 0, 0)),
        ('yellow', (255, 255, 0)),
    ]
]

EXPLOSIONS = [
    [
        ("rapide_et_furieux.gfx.explosions", "regularExplosion%02d.png" % idx)
        for idx in range(0, 9)
    ],
    [
        ("rapide_et_furieux.gfx.explosions", "simpleExplosion%02d.png" % idx)
        for idx in range(0, 9)
    ],
    [
        ("rapide_et_furieux.gfx.explosions", "sonicExplosion%02d.png" % idx)
        for idx in range(0, 9)
    ],
]

OBJECTS = [
    ("rapide_et_furieux.gfx.objects", "arrow_white.png"),
    ("rapide_et_furieux.gfx.objects", "arrow_yellow.png"),
    ("rapide_et_furieux.gfx.objects", "barrel_blue_down.png"),
    ("rapide_et_furieux.gfx.objects", "barrel_blue.png"),
    ("rapide_et_furieux.gfx.objects", "barrel_red_down.png"),
    ("rapide_et_furieux.gfx.objects", "barrier_red.png"),
    ("rapide_et_furieux.gfx.objects", "barrier_red_race.png"),
    ("rapide_et_furieux.gfx.objects", "barrier_white.png"),
    ("rapide_et_furieux.gfx.objects", "barrier_white_race.png"),
    ("rapide_et_furieux.gfx.objects", "cone_down.png"),
    ("rapide_et_furieux.gfx.objects", "cone_straight.png"),
    ("rapide_et_furieux.gfx.objects", "lights.png"),
    OIL,
    ("rapide_et_furieux.gfx.objects", "rock1.png"),
    ("rapide_et_furieux.gfx.objects", "rock2.png"),
    ("rapide_et_furieux.gfx.objects", "rock3.png"),
    ("rapide_et_furieux.gfx.objects", "tent_blue_large.png"),
    ("rapide_et_furieux.gfx.objects", "tent_blue.png"),
    ("rapide_et_furieux.gfx.objects", "tent_red_large.png"),
    ("rapide_et_furieux.gfx.objects", "tent_red.png"),
    ("rapide_et_furieux.gfx.objects", "tires_red_alt.png"),
    ("rapide_et_furieux.gfx.objects", "tires_red.png"),
    ("rapide_et_furieux.gfx.objects", "tires_white_alt.png"),
    ("rapide_et_furieux.gfx.objects", "tires_white.png"),
    ("rapide_et_furieux.gfx.objects", "tree_large.png"),
    ("rapide_et_furieux.gfx.objects", "tree_small.png"),
    ("rapide_et_furieux.gfx.objects", "tribune_empty.png"),
    ("rapide_et_furieux.gfx.objects", "tribune_full.png"),
    ("rapide_et_furieux.gfx.objects", "tribune_overhang_red.png"),
    ("rapide_et_furieux.gfx.objects", "tribune_overhang_striped.png"),
]

BONUSES = {
    color[1]:
    ("rapide_et_furieux.gfx.bonuses", "powerup%s_bolt.png" % color[0], color[1])
    for color in [
        ('Blue', (0, 0, 255)),
        ('Green', (0, 255, 0)),
        ('Red', (255, 0, 0)),
        ('Yellow', (255, 255, 0)),
    ]
}

TILES = [
    ("rapide_et_furieux.gfx.tiles", "dirt.png"),
    ("rapide_et_furieux.gfx.tiles", "grass.png"),
    ("rapide_et_furieux.gfx.tiles", "sand.png"),
]
TILES += [
    ("rapide_et_furieux.gfx.tiles", "road_asphalt%02d.png" % idx)
    for idx in range(1, 91)
]
TILES += [
    ("rapide_et_furieux.gfx.tiles", "road_dirt%02d.png" % idx)
    for idx in range(1, 91)
]
TILES += [
    ("rapide_et_furieux.gfx.tiles", "road_sand%02d.png" % idx)
    for idx in range(1, 91)
]
TILES += [
    ("rapide_et_furieux.gfx.tiles", "land_dirt%02d.png" % idx)
    for idx in range(1, 15)
]
TILES += [
    ("rapide_et_furieux.gfx.tiles", "land_grass%02d.png" % idx)
    for idx in range(1, 15)
]
TILES += [
    ("rapide_et_furieux.gfx.tiles", "land_sand%02d.png" % idx)
    for idx in range(1, 15)
]

SPAWN_TILES = {
    # resource --> angle
    ("rapide_et_furieux.gfx.tiles", "road_asphalt79.png"): 180,
    ("rapide_et_furieux.gfx.tiles", "road_asphalt80.png"): 90,
    ("rapide_et_furieux.gfx.tiles", "road_asphalt81.png"): 0,
    ("rapide_et_furieux.gfx.tiles", "road_asphalt82.png"): 270,
    ("rapide_et_furieux.gfx.tiles", "road_asphalt83.png"): 180,
    ("rapide_et_furieux.gfx.tiles", "road_asphalt84.png"): 90,
    ("rapide_et_furieux.gfx.tiles", "road_asphalt85.png"): 0,
    ("rapide_et_furieux.gfx.tiles", "road_asphalt86.png"): 270,
    ("rapide_et_furieux.gfx.tiles", "road_dirt78.png"): 180,
    ("rapide_et_furieux.gfx.tiles", "road_dirt79.png"): 90,
    ("rapide_et_furieux.gfx.tiles", "road_dirt80.png"): 0,
    ("rapide_et_furieux.gfx.tiles", "road_dirt81.png"): 270,
    ("rapide_et_furieux.gfx.tiles", "road_dirt82.png"): 180,
    ("rapide_et_furieux.gfx.tiles", "road_dirt83.png"): 90,
    ("rapide_et_furieux.gfx.tiles", "road_dirt84.png"): 0,
    ("rapide_et_furieux.gfx.tiles", "road_dirt85.png"): 270,
    ("rapide_et_furieux.gfx.tiles", "road_sand75.png"): 180,
    ("rapide_et_furieux.gfx.tiles", "road_sand76.png"): 90,
    ("rapide_et_furieux.gfx.tiles", "road_sand77.png"): 0,
    ("rapide_et_furieux.gfx.tiles", "road_sand78.png"): 270,
    ("rapide_et_furieux.gfx.tiles", "road_sand79.png"): 180,
    ("rapide_et_furieux.gfx.tiles", "road_sand80.png"): 90,
    ("rapide_et_furieux.gfx.tiles", "road_sand81.png"): 0,
    ("rapide_et_furieux.gfx.tiles", "road_sand82.png"): 270,
}

g_resources = {}


def load_image(rsc):
    img_path = resource_filename(*rsc)
    img = pygame.image.load(img_path)
    if img.get_alpha() is not None:
        img = img.convert_alpha()
    else:
        img = img.convert()
    return img


def load_sound(rsc):
    snd_path = resource_filename(*(rsc[:2]))
    snd = pygame.mixer.Sound(file=snd_path)
    snd.set_volume(rsc[2])
    return snd


def load_music(rsc):
    # simply make sure the file is available and get its path
    return resource_filename(*(rsc[:2]))


def load_resources():
    global g_resources
    rsc = {}

    # images
    rsc.update({ui_rsc: load_image(ui_rsc) for ui_rsc in UI})
    rsc.update({tile_rsc: load_image(tile_rsc) for tile_rsc in TILES})
    rsc.update({obj_rsc: load_image(obj_rsc) for obj_rsc in OBJECTS})
    rsc.update({obj_rsc[:2]: load_image(obj_rsc[:2]) for obj_rsc in CARS})
    rsc.update({obj_rsc[:2]: load_image(obj_rsc[:2])
                for obj_rsc in MOTORCYCLES})
    rsc.update({obj_rsc[:2]: load_image(obj_rsc[:2])
                for obj_rsc in BONUSES.values()})
    rsc.update({
        obj_rsc: load_image(obj_rsc)
        for explosions in EXPLOSIONS
        for obj_rsc in explosions
    })
    rsc.update({obj_rsc[:2]: load_image(obj_rsc[:2]) for obj_rsc in BARRELS})
    rsc.update({obj_rsc[:2]: load_image(obj_rsc[:2])
                for obj_rsc in BULLETS.values()})
    rsc.update({obj_rsc[:2]: load_image(obj_rsc[:2])
                for obj_rsc in CROSSAIRS.values()})
    rsc.update({obj_rsc: load_image(obj_rsc) for obj_rsc in LASERS.values()})
    rsc.update({obj_rsc: load_image(obj_rsc) for obj_rsc in GUNS})
    rsc.update({obj_rsc: load_image(obj_rsc) for obj_rsc in SCRATCHS})
    rsc.update({obj_rsc: load_image(obj_rsc) for obj_rsc in SHIELDS})
    rsc.update({obj_rsc: load_image(obj_rsc) for obj_rsc in SKIDMARKS})
    rsc[TURRET_BASE] = load_image(TURRET_BASE)
    rsc[MINE] = load_image(MINE)
    rsc[MINE] = pygame.transform.scale(
        rsc[MINE],
        (
            int(rsc[MINE].get_size()[0] / 10),
            int(rsc[MINE].get_size()[1] / 10),
        )
    )
    rsc[MISSILE] = load_image(MISSILE)
    rsc[SKIDMARK_OIL] = load_image(SKIDMARK_OIL)

    # sounds
    rsc.update({
        snd_rsc[:2]: load_sound(snd_rsc)
        for snds in SOUNDS.values()
        for snd_rsc in snds
    })
    rsc.update({
        snd_rsc[:2]: load_sound(snd_rsc)
        for snds in COUNTDOWNS.values()
        for snd_rsc in snds.values()
    })
    rsc[ENGINE[:2]] = load_sound(ENGINE)
    rsc[TIRES[:2]] = load_sound(TIRES)

    # musics
    rsc.update({
        music_rsc[:2]: load_music(music_rsc)
        for music_rsc in MUSICS
    })

    g_resources = rsc


def get_resource(rsc):
    rsc = rsc[:2]
    rsc = tuple(rsc)
    return g_resources[rsc]
